import copy
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from urllib.error import HTTPError, URLError

from mini_agent.llm import ChatLLM, LLMError, ParseError, parse_response
from mini_agent.memory import build_context
from mini_agent.runtime import Agent
from mini_agent.storage import SessionBusy, Store, dumps, initial_state
from mini_agent.tools import ToolError, build_registry


def reply(answer="完成", calls=None, reason="任务已完成"):
    msg = {"content": dumps({"reason": reason, "answer": answer})}
    if calls:
        msg["tool_calls"] = calls
    return {"choices": [{"message": msg, "finish_reason": "tool_calls" if calls else "stop"}]}


def call(name, args, call_id="call_1"):
    return {"id": call_id, "type": "function", "function": {
        "name": name, "arguments": dumps(args)}}


class ScriptedLLM:
    """确定性替身只存在于测试，不是产品中的假模型。"""
    def __init__(self, *responses):
        self.responses = list(responses)
        self.requests = []

    def complete(self, messages, tools):
        self.requests.append(copy.deepcopy({"messages": messages, "tools": tools}))
        response = self.responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return response


class AgentTests(unittest.TestCase):
    def setUp(self):
        directory = Path(__file__).resolve().parents[1] / ".runtime" / "tests"
        directory.mkdir(parents=True, exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(dir=directory)
        self.addCleanup(self.temp.cleanup)
        self.store = Store(self.temp.name)

    def test_direct_answer_and_reason(self):
        llm = ScriptedLLM(reply("你好"))
        result = Agent(llm, self.store).chat("A", "w1", "你好")
        self.assertEqual(result["answer"], "你好")
        self.assertEqual(len(llm.requests), 1)
        self.assertFalse(any(row["event"] == "tool" for row in result["trace"]))
        self.assertEqual(result["trace"][2]["reason"], "任务已完成")

    def test_tool_result_is_sent_back_to_model(self):
        llm = ScriptedLLM(reply(calls=[call("calculator", {"expression": "(12+8)*3"})]), reply("60"))
        result = Agent(llm, self.store).chat("A", "w1", "计算 (12+8)*3")
        self.assertEqual(result["status"], "ok")
        tool_message = llm.requests[1]["messages"][-1]
        self.assertEqual(tool_message["tool_call_id"], "call_1")
        self.assertEqual(json.loads(tool_message["content"])["data"]["value"], 60)
        self.assertEqual(len(llm.requests[0]["tools"]), 4)

    def test_multi_step_weather_then_todo(self):
        llm = ScriptedLLM(reply(calls=[call("weather", {"city": "上海"})]),
                          reply(calls=[call("todo", {"action": "add", "text": "明天带伞"})]), reply("已记录"))
        result = Agent(llm, self.store).chat("A", "w1", "查上海模拟天气并记待办")
        self.assertEqual([r["name"] for r in result["trace"] if r["event"] == "tool"], ["weather", "todo"])
        self.assertTrue(self.store.inspect("A", "w1")["state"]["last_tools"]["weather"]["data"]["mock"])

    def test_multiple_calls_have_matching_results(self):
        llm = ScriptedLLM(reply(calls=[call("weather", {"city": "北京"}, "a"),
                                            call("search", {"query": "Agent"}, "b")]), reply())
        Agent(llm, self.store).chat("A", "w1", "天气和资料")
        messages = llm.requests[1]["messages"]
        self.assertEqual([m["tool_call_id"] for m in messages if m["role"] == "tool"], ["a", "b"])

    def test_users_windows_and_restart_are_isolated(self):
        for user, session, item in [("A", "w1", "带伞"), ("A", "w2", "写周报"), ("B", "w1", "买书")]:
            llm = ScriptedLLM(reply(calls=[call("todo", {"action": "add", "text": item})]), reply())
            Agent(llm, self.store).chat(user, session, item)
        restarted = Store(self.temp.name)
        for user, session, expected in [("A", "w1", "带伞"), ("A", "w2", "写周报"), ("B", "w1", "买书")]:
            items = restarted.inspect(user, session)["state"]["todos"]
            self.assertEqual([i["text"] for i in items], [expected])

    def test_plain_followup_keeps_previous_conversation(self):
        Agent(ScriptedLLM(reply("好的，小林")), self.store).chat("A", "w1", "请叫我小林")
        llm = ScriptedLLM(reply("小林"))
        Agent(llm, Store(self.temp.name)).chat("A", "w1", "我叫什么？")
        self.assertIn("请叫我小林", dumps(llm.requests[0]))

    def test_tool_followup_completes_previous_todo(self):
        Agent(ScriptedLLM(reply(calls=[call("todo", {"action": "add", "text": "带伞"})]), reply()),
              self.store).chat("A", "w1", "记待办带伞")
        llm = ScriptedLLM(reply(calls=[call("todo", {"action": "done", "id": 1})]), reply())
        Agent(llm, self.store).chat("A", "w1", "把刚才那条标为完成")
        self.assertIn("带伞", dumps(llm.requests[0]))
        self.assertTrue(self.store.inspect("A", "w1")["state"]["todos"][0]["done"])

    def test_unknown_tool_and_bad_arguments_recover(self):
        malformed = call("calculator", {})
        malformed["function"]["arguments"] = "{broken"
        llm = ScriptedLLM(reply(calls=[call("missing", {})]), reply(calls=[malformed]),
                          reply(calls=[call("calculator", {"expression": "1/0"})]),
                          reply(calls=[call("calculator", {"expression": "2+2"})]), reply("4"))
        result = Agent(llm, self.store).chat("A", "w1", "计算")
        self.assertEqual(result["status"], "ok")
        events = [r["result"]["ok"] for r in result["trace"] if r["event"] == "tool"]
        self.assertEqual(events, [False, False, False, True])

    def test_max_steps_stops_and_next_turn_stays_valid(self):
        response = reply(calls=[call("calculator", {"expression": "1+1"})])
        llm = ScriptedLLM(response, response)
        result = Agent(llm, self.store, max_steps=2).chat("A", "w1", "继续算")
        self.assertEqual(result["status"], "max_steps")
        self.assertEqual(len(llm.requests), 2)
        followup = ScriptedLLM(reply("2"))
        Agent(followup, self.store).chat("A", "w1", "上次算出多少")
        self.assertEqual(followup.requests[0]["messages"][-2]["role"], "assistant")

    def test_parse_error_can_recover(self):
        llm = ScriptedLLM({"choices": []}, reply("恢复成功"))
        self.assertEqual(Agent(llm, self.store).chat("A", "w1", "你好")["status"], "ok")
        self.assertIn("上次响应格式无效", dumps(llm.requests[1]))

    def test_api_failure_keeps_completed_todo(self):
        llm = ScriptedLLM(reply(calls=[call("todo", {"action": "add", "text": "写周报"})]), LLMError("模拟超时"))
        result = Agent(llm, self.store).chat("A", "w1", "记周报")
        self.assertEqual(result["status"], "llm_error")
        self.assertEqual(self.store.inspect("A", "w1")["state"]["todos"][0]["text"], "写周报")

    def test_compression_retains_structured_state_and_pairing(self):
        Agent(ScriptedLLM(reply(calls=[call("todo", {"action": "add", "text": "写周报"})]), reply()),
              self.store).chat("A", "w1", "记录待办")
        for i in range(8):
            Agent(ScriptedLLM(reply("收到")), self.store).chat("A", "w1", f"第{i}次聊天")
        llm = ScriptedLLM(reply("写周报"))
        Agent(llm, self.store).chat("A", "w1", "待办是什么")
        state = self.store.inspect("A", "w1")["state"]
        self.assertTrue(state["summary"])
        self.assertLessEqual(len(state["turns"]), 5)  # 4 个历史轮次 + 刚完成的轮次。
        self.assertIn("写周报", llm.requests[0]["messages"][1]["content"])
        self.assertFalse(any(m["role"] == "tool" for m in llm.requests[0]["messages"]))

    def test_context_budget_stops_before_api(self):
        llm = ScriptedLLM()
        result = Agent(llm, self.store, context_budget=20).chat("A", "w1", "你好")
        self.assertEqual(result["status"], "context_limit")
        self.assertEqual(llm.requests, [])

    def test_context_budget_includes_tool_schema(self):
        schemas = build_registry().schemas()
        context = build_context(initial_state(), [{"role": "user", "content": "你好"}], schemas)
        self.assertLessEqual(len(dumps({"messages": context, "tools": schemas})), 24000)

    def test_same_session_busy_other_session_available(self):
        with self.store.edit("A", "w1"):
            with self.assertRaises(SessionBusy):
                self.store.inspect("A", "w1")
            self.assertEqual(self.store.inspect("A", "w2")["state"]["todos"], [])

    def test_trace_persisted_without_credentials(self):
        result = Agent(ScriptedLLM(reply(calls=[call("search", {"query": "Agent"})]), reply()),
                       self.store).chat("A", "w1", "搜索 Agent")
        trace = self.store.inspect("A", "w1")["trace"]
        self.assertEqual(trace[-1]["run_id"], result["run_id"])
        tool = next(row for row in trace if row["event"] == "tool")
        self.assertIn("duration_ms", tool)
        self.assertNotIn("Authorization", dumps(trace))

    def test_invalid_input_rejected_without_calling_model(self):
        for value in ("", "x" * 2001):
            with self.assertRaises(ValueError):
                Agent(ScriptedLLM(), self.store).chat("A", "w1", value)

    def test_live_smoke_stops_after_api_failure_and_marks_skipped(self):
        from scripts import live_smoke
        llm = ScriptedLLM(LLMError("LLM HTTP 402: insufficient balance"))
        llm.model, llm.url = "test-model", "https://example.invalid/v1/chat/completions"
        with patch.object(live_smoke, "ROOT", Path(self.temp.name)), \
                patch.object(live_smoke.ChatLLM, "from_env", return_value=llm), \
                patch("sys.argv", ["live_smoke.py"]), patch("sys.stdout", new_callable=io.StringIO):
            self.assertEqual(live_smoke.main(), 1)
        path = next(Path(self.temp.name).glob(".runtime/live/*/report.json"))
        report = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(report["executed_cases"], 1)
        self.assertEqual(report["skipped_cases"], 7)
        self.assertFalse(report["passed"])
        self.assertEqual(len(llm.requests), 1)


class ToolAndParserTests(unittest.TestCase):
    def setUp(self):
        self.tools, self.state = build_registry(), initial_state()

    def test_schema_validation(self):
        for args in ({}, {"action": "delete"}, {"action": "done", "id": True},
                     {"action": "add", "text": ""}, {"action": "list", "user": "B"}, []):
            with self.subTest(args=args), self.assertRaises(ToolError):
                self.tools.execute("todo", args, self.state)

    def test_calculator_blocks_code_and_expensive_expressions(self):
        for expression in ("__import__('os').getcwd()", "2**999999", "True+1", "[1][0]", "1e999"):
            with self.subTest(expression=expression), self.assertRaises(ToolError):
                self.tools.execute("calculator", {"expression": expression}, self.state)

    def test_negative_decimal_math(self):
        value = self.tools.execute("calculator", {"expression": "-2.5*(4+2)"}, self.state)
        self.assertEqual(value["value"], -15)

    def test_todo_duplicate_and_conditional_requirements(self):
        args = {"action": "add", "text": "带伞"}
        self.tools.execute("todo", args, self.state)
        self.tools.execute("todo", args, self.state)
        self.assertEqual(len(self.state["todos"]), 1)
        for args in ({"action": "add"}, {"action": "done"}, {"action": "done", "id": 999}):
            with self.assertRaises(ToolError):
                self.tools.execute("todo", args, self.state)

    def test_search_no_hit_and_weather_limit(self):
        result = self.tools.execute("search", {"query": "不存在的词xyz"}, self.state)
        self.assertTrue(result["mock"])
        self.assertEqual(result["results"], [])
        with self.assertRaises(ToolError):
            self.tools.execute("weather", {"city": "不存在"}, self.state)

    def test_duplicate_registration_rejected(self):
        with self.assertRaises(ValueError):
            self.tools.register("todo", "duplicate", {}, [], lambda a, s: None)

    def test_parser_plain_text_and_brief_reason(self):
        self.assertEqual(parse_response({"choices": [{"message": {"content": "你好"}}]})["answer"], "你好")
        self.assertEqual(parse_response(reply(reason="需要计算"))["reason"], "需要计算")

    def test_parser_rejects_empty_truncated_duplicate_calls(self):
        bad = [None, [], {}, {"choices": []}, {"choices": [{"message": None}]},
               {"choices": [{"message": {"content": ""}}]},
               {"choices": [{"message": {"content": "半截答案"}, "finish_reason": "length"}]},
               reply(calls=[call("todo", {}), call("todo", {})])]
        for payload in bad:
            with self.subTest(payload=payload), self.assertRaises(ParseError):
                parse_response(payload)


class HTTPTests(unittest.TestCase):
    def client(self):
        return ChatLLM("test-key-not-real", "https://example.invalid/v1", "test-model")

    def test_default_provider_is_groq(self):
        with patch.dict("os.environ", {"LLM_API_KEY": "test-key-not-real"}, clear=True):
            client = ChatLLM.from_env()
        self.assertEqual(client.url, "https://api.groq.com/openai/v1/chat/completions")
        self.assertEqual(client.model, "qwen/qwen3.8-27b")

    def test_groq_qwen_limits_output_and_disables_reasoning(self):
        client = ChatLLM("test-key-not-real", "https://api.groq.com/openai/v1", "qwen/qwen3.8-27b")
        with patch.object(client.opener, "open", return_value=io.BytesIO(json.dumps(reply()).encode())) as mocked:
            client.complete([], [])
        body = json.loads(mocked.call_args.args[0].data)
        self.assertEqual(body["max_completion_tokens"], 1024)
        self.assertEqual(body["reasoning_effort"], "none")
        self.assertNotIn("thinking", body)

    @patch("mini_agent.llm.time.sleep")
    def test_rate_limit_honors_retry_after(self, sleep):
        client = self.client()
        err = HTTPError(client.url, 429, "limited", {"retry-after": "12"}, None)
        with patch.object(client.opener, "open", side_effect=[err, io.BytesIO(json.dumps(reply()).encode())]):
            client.complete([], [])
        sleep.assert_called_once_with(12)

    @patch("mini_agent.llm.time.sleep")
    def test_long_rate_limit_wait_stops_without_retry_or_provider_switch(self, sleep):
        client = self.client()
        err = HTTPError(client.url, 429, "limited", {"retry-after": "90"}, None)
        with patch.object(client.opener, "open", side_effect=err) as mocked:
            with self.assertRaises(LLMError):
                client.complete([], [])
        self.assertEqual(mocked.call_count, 1)
        sleep.assert_not_called()

    def test_http_request_contains_tools_and_auto_choice(self):
        client = self.client()
        with patch.object(client.opener, "open", return_value=io.BytesIO(json.dumps(reply()).encode())) as mocked:
            client.complete([{"role": "user", "content": "hello"}], build_registry().schemas())
        request = mocked.call_args.args[0]
        body = json.loads(request.data)
        self.assertEqual(request.full_url, "https://example.invalid/v1/chat/completions")
        self.assertEqual(body["tool_choice"], "auto")
        self.assertEqual(len(body["tools"]), 4)

    @patch("mini_agent.llm.time.sleep")
    def test_429_retries_once(self, sleep):
        client = self.client()
        err = HTTPError(client.url, 429, "limited", {}, None)
        with patch.object(client.opener, "open", side_effect=[err, io.BytesIO(json.dumps(reply()).encode())]) as mocked:
            client.complete([], [])
        self.assertEqual(mocked.call_count, 2)

    def test_deepseek_disables_thinking_but_other_providers_do_not_receive_extension(self):
        for url, expected in [("https://api.deepseek.com", True), ("https://api.openai.com/v1", False)]:
            client = ChatLLM("test-key-not-real", url, "test-model")
            with patch.object(client.opener, "open", return_value=io.BytesIO(json.dumps(reply()).encode())) as mocked:
                client.complete([], [])
            body = json.loads(mocked.call_args.args[0].data)
            self.assertEqual("thinking" in body, expected)
            if expected:
                self.assertEqual(body["thinking"], {"type": "disabled"})

    def test_401_has_no_retry_or_sensitive_error_body(self):
        client = self.client()
        err = HTTPError(client.url, 401, "test-key-not-real", {}, None)
        with patch.object(client.opener, "open", side_effect=err) as mocked:
            with self.assertRaises(LLMError) as raised:
                client.complete([], [])
        self.assertEqual(mocked.call_count, 1)
        self.assertNotIn("test-key-not-real", str(raised.exception))

    def test_402_explains_balance_problem_without_retry(self):
        client = self.client()
        err = HTTPError(client.url, 402, "private provider response", {}, None)
        with patch.object(client.opener, "open", side_effect=err) as mocked:
            with self.assertRaises(LLMError) as raised:
                client.complete([], [])
        self.assertEqual(mocked.call_count, 1)
        self.assertIn("余额不足", str(raised.exception))
        self.assertNotIn("private provider response", str(raised.exception))

    @patch("mini_agent.llm.time.sleep")
    def test_timeout_and_malformed_http_body(self, sleep):
        client = self.client()
        with patch.object(client.opener, "open", side_effect=URLError("timeout")) as mocked:
            with self.assertRaises(LLMError):
                client.complete([], [])
            self.assertEqual(mocked.call_count, 2)
        with patch.object(client.opener, "open", return_value=io.BytesIO(b"not json")):
            with self.assertRaises(LLMError):
                client.complete([], [])


if __name__ == "__main__":
    unittest.main()
