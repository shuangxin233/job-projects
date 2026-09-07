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
    args = parser.parse_args()
    load_env(args.env_file)
    llm = ChatLLM.from_env()
    run = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    output = ROOT / ".runtime" / "live" / run
    agent = Agent(llm, Store(output / "sessions"))
    checks = [
        ("w1", "你好，请叫我小林。", []),
        ("w1", "请用计算器计算 (12+8)*3。", ["calculator"]),
        ("w1", "用计算器把刚才的计算结果除以4。", ["calculator"]),
        ("w1", "查上海的模拟天气，再添加一条待办：明天带伞。", ["weather", "todo"]),
        ("w2", "搜索周报写法，给我三行周报模板，再添加待办：周五写周报。", ["search", "todo"]),
        ("w1", "把刚才带伞的待办标记完成，再列出我的待办。", ["todo"]),
        ("w1", "我请你怎么称呼我？", []),
        ("w2", "列出我的待办。", ["todo"]),
    ]
    report = {"kind": "real_llm_api", "model": llm.model, "endpoint": llm.url,
              "time_utc": run, "cases": []}
    for session, text, expected in checks:
        result = agent.chat("smoke", session, text)
        names = [row["name"] for row in result["trace"] if row["event"] == "tool" and row["result"]["ok"]]
        passed = result["status"] == "ok" and set(expected) <= set(names)
        if not expected:
            passed = passed and not names
        if "(12+8)*3" in text:
            values = [r["result"].get("data", {}).get("value") for r in result["trace"] if r["event"] == "tool"]
            passed = passed and 60 in values
        if text == "我请你怎么称呼我？":
            passed = passed and "小林" in result["answer"]
        if "除以4" in text:
            values = [r["result"].get("data", {}).get("value") for r in result["trace"] if r["event"] == "tool"]
            passed = passed and 15 in values
        report["cases"].append({"session": session, "input": text, "passed": passed, **result})
        print(("PASS" if passed else "FAIL") + " " + text, flush=True)
        (output / "report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    w1 = agent.store.inspect("smoke", "w1")["state"]["todos"]
    w2 = agent.store.inspect("smoke", "w2")["state"]["todos"]
    isolated = (len(w1) == 1 and w1[0]["text"] == "明天带伞" and w1[0]["done"]
                and len(w2) == 1 and w2[0]["text"] == "周五写周报" and not w2[0]["done"])
    report["isolation_passed"] = isolated
    report["passed"] = isolated and all(case["passed"] for case in report["cases"])
    (output / "report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print("Report: " + str(output / "report.json"))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except LLMError as exc:
        print("真实 API 测试未完成：" + str(exc))
        raise SystemExit(1)
