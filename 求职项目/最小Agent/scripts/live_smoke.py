"""需要真实 API Key，验证模型自主选择工具及多轮会话；没有 Key 就失败。"""
import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from mini_agent.llm import ChatLLM, LLMError, load_env
from mini_agent.runtime import Agent
from mini_agent.storage import Store


def main():
    parser = argparse.ArgumentParser(description="真实 LLM API 冒烟测试")
    parser.add_argument("--env-file", default=str(ROOT / ".env"))
    parser.add_argument("--resume-report", help="服务恢复后，从本项目 .runtime/live 下的报告继续未通过用例")
    args = parser.parse_args()
    load_env(args.env_file)
    llm = ChatLLM.from_env()
    run = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    output = ROOT / ".runtime" / "live" / run
    report = {"kind": "real_llm_api", "model": llm.model, "endpoint": llm.url,
              "time_utc": run, "cases": [], "attempts": []}
    if args.resume_report:
        source = Path(args.resume_report).resolve()
        if not source.is_relative_to((ROOT / ".runtime/live").resolve()):
            raise LLMError("只能续测本项目 .runtime/live 下的报告。")
        report = json.loads(source.read_text(encoding="utf-8"))
        if report.get("model") != llm.model or report.get("endpoint") != llm.url:
            raise LLMError("续测的模型和接口必须与原报告一致。")
        output = source.parent
        report.setdefault("attempts", list(report["cases"]))
        report["resume_count"] = report.get("resume_count", 0) + 1
        report["last_resumed_utc"] = run
        report.pop("aborted_reason", None)
    agent = Agent(llm, Store(output / "sessions"))
    checks = [
        ("w1", "你好，请叫我小林。", []),
        ("w1", "请用计算器计算 (12+8)*3。", ["calculator"]),
        ("w1", "用计算器把刚才的计算结果除以4。", ["calculator"]),
        ("w1", "查上海的模拟天气，再添加一条待办：明天带伞。", ["weather", "todo"]),
        ("w2", "先搜索周报写法；再添加待办：周五写周报；确认待办已保存后，最后给我三行周报模板。", ["search", "todo"]),
        ("w1", "把刚才带伞的待办标记完成，再调用工具列出所有待办，包括已完成的项目。", ["todo"]),
        ("w1", "我之前让你叫我什么？请只回答称呼。", []),
        ("w2", "列出我的待办。", ["todo"]),
    ]
    for index, (session, text, expected) in enumerate(checks):
        if index < len(report["cases"]) and report["cases"][index]["passed"]:
            print("KEEP " + text, flush=True)
            continue
        result = agent.chat("smoke", session, text)
        names = [row["name"] for row in result["trace"] if row["event"] == "tool" and row["result"]["ok"]]
        passed = result["status"] == "ok" and set(expected) <= set(names)
        if not expected:
            passed = passed and not names
        if "(12+8)*3" in text:
            values = [r["result"].get("data", {}).get("value") for r in result["trace"] if r["event"] == "tool"]
            passed = passed and 60 in values
        if "请只回答称呼" in text:
            passed = passed and result["answer"].strip().strip("。！!\"' ") == "小林"
        if "包括已完成的项目" in text:
            actions = {r["args"].get("action") for r in result["trace"]
                       if r["event"] == "tool" and r["name"] == "todo" and r["result"]["ok"]}
            passed = passed and {"done", "list"} <= actions and "明天带伞" in result["answer"]
        if expected == ["calculator"] or expected == ["todo"]:
            passed = passed and "模拟数据" not in result["answer"]
        if "除以4" in text:
            values = [r["result"].get("data", {}).get("value") for r in result["trace"] if r["event"] == "tool"]
            passed = passed and 15 in values
        case = {"session": session, "input": text, "passed": passed, **result}
        report["attempts"].append(case)
        if index < len(report["cases"]):
            report["cases"][index] = case
        else:
            report["cases"].append(case)
        print(("PASS" if passed else "FAIL") + " " + text, flush=True)
        (output / "report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        if result["status"] == "llm_error":
            report["aborted_reason"] = result["answer"]
            print("API 请求失败，停止后续用例；请处理配置、余额或网络问题后重试。", flush=True)
            break
    w1 = agent.store.inspect("smoke", "w1")["state"]["todos"]
    w2 = agent.store.inspect("smoke", "w2")["state"]["todos"]
    isolated = (len(w1) == 1 and w1[0]["text"] == "明天带伞" and w1[0]["done"]
                and len(w2) == 1 and w2[0]["text"] == "周五写周报" and not w2[0]["done"])
    report["isolation_passed"] = isolated
    report["planned_cases"] = len(checks)
    report["executed_cases"] = len(report["cases"])
    report["skipped_cases"] = len(checks) - len(report["cases"])
    report["passed"] = (isolated and not report["skipped_cases"]
                        and all(case["passed"] for case in report["cases"]))
    (output / "report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print("Report: " + str(output / "report.json"))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except LLMError as exc:
        print("真实 API 测试未完成：" + str(exc))
        raise SystemExit(1)
