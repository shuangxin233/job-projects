import argparse
import os
import sqlite3
from pathlib import Path

from .llm import ChatLLM, LLMError, load_env
from .runtime import Agent
from .storage import SessionBusy, Store, dumps


PROJECT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser(description="手写最小 Agent：真实 LLM + 四个工具 + 独立会话")
    parser.add_argument("--user", default="A", help="用户标识，默认 A")
    parser.add_argument("--session", default="window1", help="会话标识，两个窗口使用不同名称")
    parser.add_argument("--message", help="单次提问；不传则交互聊天")
    parser.add_argument("--trace", action="store_true", help="显示简短执行日志")
    parser.add_argument("--inspect", action="store_true", help="查看本会话状态，不调用 LLM")
    parser.add_argument("--env-file", default=str(PROJECT / ".env"))
    parser.add_argument("--data-dir", default=os.getenv("AGENT_DATA_DIR", str(PROJECT / ".runtime")))
    args = parser.parse_args()
    try:
        store = Store(args.data_dir)
        if args.inspect:
            print(dumps(store.inspect(args.user, args.session)))
            return 0
        load_env(args.env_file)
        agent = Agent(ChatLLM.from_env(), store)
        print(f"用户={args.user} | 会话={args.session} | /exit 退出 | /state 查看状态")
        while True:
            text = args.message if args.message is not None else input("你：").strip()
            if text == "/exit":
                return 0
            if text == "/state":
                print(dumps(store.inspect(args.user, args.session)["state"]))
                if args.message is not None:
                    return 0
                continue
            if not text and args.message is None:
                continue
            result = agent.chat(args.user, args.session, text)
            print("Agent：" + result["answer"])
            if args.trace:
                for row in result["trace"]:
                    if row["event"] in ("decision", "tool", "finish", "parse_error", "llm_error", "context_limit"):
                        print("  TRACE " + dumps(row))
            if args.message is not None:
                return 0 if result["status"] == "ok" else 1
    except (LLMError, SessionBusy, ValueError, sqlite3.Error, OSError) as exc:
        print("无法完成：" + str(exc))
        return 1
    except (KeyboardInterrupt, EOFError):
        print("\n已退出；当前未完成轮次回滚，之前会话仍保留。")
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
