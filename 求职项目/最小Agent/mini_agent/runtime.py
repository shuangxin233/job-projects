"""主循环：用户 → LLM → 解析 → 工具 → LLM → 最终答案。"""
import json
import time
import uuid
from datetime import datetime, timezone

from .llm import LLMError, ParseError, parse_response
from .memory import ContextLimit, build_context
from .storage import dumps
from .tools import ToolError, build_registry


class Agent:
    def __init__(self, llm, store, max_steps=6, context_budget=24000, registry=None):
        if not 1 <= max_steps <= 20:
            raise ValueError("max_steps 必须为 1～20")
        self.llm, self.store = llm, store
        self.max_steps, self.context_budget = max_steps, context_budget
        self.registry = registry or build_registry()

    def chat(self, user, session, text):
        if not isinstance(text, str) or not text.strip() or len(text) > 2000:
            raise ValueError("输入必须是 1～2000 字符")
        run_id, trace = uuid.uuid4().hex, []
        last_successful_call = None
        current = [{"role": "user", "content": text}]
        status, answer = "max_steps", "已达到最大循环次数，请缩小任务或继续追问。已完成的操作会保留。"

        def log(event, step, **fields):
            trace.append({"time": datetime.now(timezone.utc).isoformat(), "run_id": run_id,
                          "user": user, "session": session, "step": step, "event": event, **fields})

        with self.store.edit(user, session) as (state, db):
            log("start", 0)
            # 一次用户输入最多调用 max_steps 次模型。多工具也有单次上限。
            for step in range(1, self.max_steps + 1):
                try:
                    messages = build_context(state, current, self.registry.schemas(), self.context_budget)
                    log("llm_request", step, context_chars=len(dumps(messages)))
                    decision = parse_response(self.llm.complete(messages, self.registry.schemas()))
                except ParseError as exc:
                    log("parse_error", step, error=str(exc))
                    current.append({"role": "user", "content": "上次响应格式无效。请输出合法工具调用或非空答案。"})
                    continue
                except (LLMError, ContextLimit) as exc:
                    status = "llm_error" if isinstance(exc, LLMError) else "context_limit"
                    answer = str(exc) + " 已完成的操作会保留。"
                    log(status, step, error=str(exc))
                    break

                log("decision", step, reason=decision["reason"],
                    tools=[call["function"]["name"] for call in decision["calls"]])
                if not decision["calls"]:
                    status, answer = "ok", decision["answer"]
                    break

                # 必须先保存 assistant 工具调用，再给每个 call_id 配一条 tool 结果。
                current.append(decision["message"])
                for call in decision["calls"]:
                    fn, started = call["function"], time.monotonic()
                    args = None
                    try:
                        args = json.loads(fn["arguments"])
                        signature = (fn["name"], json.dumps(args, sort_keys=True))
                        if signature == last_successful_call:
                            raise ToolError("相同工具和参数已经成功执行，不再重复。请根据上一条成功结果回答，或使用不同工具/参数完成剩余任务。")
                        value = self.registry.execute(fn["name"], args, state)
                        result = {"ok": True, "data": value}
                        last_successful_call = signature
                    except (json.JSONDecodeError, ToolError) as exc:
                        result = {"ok": False, "error": str(exc)[:300]}
                    except Exception as exc:
                        result = {"ok": False, "error": "工具执行异常：" + type(exc).__name__}
                    output = dumps(result)
                    if len(output) > 3500:
                        result = {"ok": result["ok"], "truncated": True, "preview": output[:2800]}
                        output = dumps(result)
                    current.append({"role": "tool", "tool_call_id": call["id"], "content": output})
                    if result["ok"] and fn["name"] != "todo":
                        state["last_tools"][fn["name"]] = result
                    log("tool", step, call_id=call["id"], name=fn["name"], args=args,
                        result=result, duration_ms=round((time.monotonic() - started) * 1000, 2))

            current.append({"role": "assistant", "content": answer})
            state["turns"].append(current)
            log("finish", step, status=status)
            # 归档保存完整轮次和 trace；下次模型只读取压缩后的活动记忆。
            db.execute("INSERT INTO turns(data) VALUES (?)", (dumps(current),))
            for row in trace:
                db.execute("INSERT INTO traces(data) VALUES (?)", (dumps(row),))
        return {"answer": answer, "status": status, "run_id": run_id, "trace": trace}
