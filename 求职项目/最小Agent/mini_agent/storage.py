"""每个 (user, session) 一个 SQLite 文件，既持久化也提供跨进程互斥。"""
import hashlib
import json
import sqlite3
from contextlib import contextmanager
from pathlib import Path


def dumps(value):
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


def initial_state():
    return {"summary": "", "turns": [], "todos": [], "next_todo_id": 1, "last_tools": {}}


class SessionBusy(Exception):
    pass


class Store:
    def __init__(self, directory):
        self.directory = Path(directory)
        self.directory.mkdir(parents=True, exist_ok=True)

    def path(self, user, session):
        if not user.strip() or not session.strip() or max(len(user), len(session)) > 100:
            raise ValueError("用户和会话名必须为 1～100 个字符")
        key = hashlib.sha256(dumps([user, session]).encode("utf-8")).hexdigest()
        return self.directory / (key + ".db")

    @contextmanager
    def edit(self, user, session):
        db = sqlite3.connect(self.path(user, session), timeout=1)
        try:
            db.execute("CREATE TABLE IF NOT EXISTS state (id INTEGER PRIMARY KEY, data TEXT)")
            db.execute("CREATE TABLE IF NOT EXISTS turns (id INTEGER PRIMARY KEY, data TEXT)")
            db.execute("CREATE TABLE IF NOT EXISTS traces (id INTEGER PRIMARY KEY, data TEXT)")
            db.commit()
            db.execute("BEGIN IMMEDIATE")
            row = db.execute("SELECT data FROM state WHERE id=1").fetchone()
            state = json.loads(row[0]) if row else initial_state()
            yield state, db
            db.execute("INSERT OR REPLACE INTO state VALUES (1, ?)", (dumps(state),))
            db.commit()
        except sqlite3.OperationalError as exc:
            db.rollback()
            if "locked" in str(exc):
                raise SessionBusy("这个会话正在处理另一条消息，请稍后重试。") from None
            raise
        finally:
            db.close()

    def inspect(self, user, session):
        with self.edit(user, session) as (state, db):
            traces = [json.loads(row[0]) for row in db.execute(
                "SELECT data FROM traces ORDER BY id DESC LIMIT 30")]
            return {"state": state, "trace": list(reversed(traces))}
