"""真实 HTTP 接口与输出解析；单元测试可注入替身，不改变 Runtime。"""
import json
import os
import time
from pathlib import Path
from urllib import error, request
from urllib.parse import urlparse


class LLMError(Exception):
    pass


class ParseError(Exception):
    pass


def load_env(path):
    """够用的 .env 读取器：支持 KEY=value、引号和整行注释。"""
    if Path(path).exists():
        for line in Path(path).read_text(encoding="utf-8-sig").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, value = line.split("=", 1)
                os.environ.setdefault(key.strip(), value.strip().strip("\"'"))


class NoRedirect(request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None  # 避免带着 Authorization 跳转到其他主机。


class ChatLLM:
    def __init__(self, key, base_url, model, timeout=30):
        if not key or not model:
            raise LLMError("请在本地 .env 填写 LLM_API_KEY 和 LLM_MODEL。")
        parsed = urlparse(base_url)
        if parsed.scheme != "https" or not parsed.netloc or parsed.username or parsed.query:
            raise LLMError("LLM_BASE_URL 必须是无用户名、无查询参数的 HTTPS 地址。")
        self.key, self.model, self.timeout = key, model, timeout
        self.is_deepseek = parsed.hostname == "api.deepseek.com"
        self.is_groq = parsed.hostname == "api.groq.com"
        self.is_bigmodel = parsed.hostname == "open.bigmodel.cn"
        self.url = base_url.rstrip("/") + "/chat/completions"
        self.opener = request.build_opener(NoRedirect())

    @classmethod
    def from_env(cls):
        return cls(os.getenv("LLM_API_KEY", ""),
                   os.getenv("LLM_BASE_URL", "https://open.bigmodel.cn/api/paas/v4"),
                   os.getenv("LLM_MODEL", "glm-4.7-flash"))

    def complete(self, messages, tools):
        payload = {"model": self.model, "messages": messages,
                   "tools": tools, "tool_choice": "auto"}
        if self.is_deepseek:
            payload["thinking"] = {"type": "disabled"}
        if self.is_bigmodel and self.model == "glm-4.7-flash":
            payload["thinking"] = {"type": "disabled"}
            payload["max_tokens"] = 1024
        if self.is_groq:
            payload["max_completion_tokens"] = 1024
            if self.model.startswith("qwen/"):
                payload["reasoning_effort"] = "none"
        body = json.dumps(payload).encode("utf-8")
        req = request.Request(self.url, data=body, headers={
            "Authorization": "Bearer " + self.key, "Content-Type": "application/json"})
        # 只重试一次 HTTP 请求；不重放已经执行的工具。
        for attempt in range(2):
            try:
                with self.opener.open(req, timeout=self.timeout) as response:
                    raw = response.read(1_000_001)
                if len(raw) > 1_000_000:
                    raise LLMError("LLM 响应过大。")
                return json.loads(raw)
            except error.HTTPError as exc:
                if exc.code in (429, 500, 502, 503, 504) and attempt == 0:
                    try:
                        delay = float(exc.headers.get("retry-after", "1"))
                    except (ValueError, TypeError):
                        delay = 1
                    if not 0 <= delay <= 30:
                        raise LLMError("API 要求较长等待，请稍后重试；不会自动升级或切换付费服务。") from None
                    time.sleep(delay)
                    continue
                # 不输出服务商原始响应，避免把密钥或请求内容带入日志。
                if exc.code == 402:
                    raise LLMError("LLM HTTP 402：API 账户余额不足，请在服务商开放平台充值后重试。") from None
                if exc.code == 429:
                    raise LLMError("LLM HTTP 429：调用频率或额度达到上限，请等待额度恢复后重试。") from None
                raise LLMError(f"LLM HTTP {exc.code}：检查密钥、模型、余额或服务状态。") from None
            except (error.URLError, TimeoutError, OSError):
                if attempt == 0:
                    time.sleep(1)
                    continue
                raise LLMError("LLM 网络连接失败或超时。") from None
            except (ValueError, UnicodeError):
                raise LLMError("LLM 返回的 HTTP 正文不是合法 JSON。") from None


def parse_response(payload):
    """提取简短决策说明、原生 tool_calls 和最终答案。"""
    try:
        choice = payload["choices"][0]
        msg = choice["message"]
        if not isinstance(msg, dict):
            raise ValueError("message 必须是对象")
        if choice.get("finish_reason") in ("length", "content_filter"):
            raise ValueError("响应被截断或过滤")
        content = msg.get("content") or ""
        if not isinstance(content, str):
            raise ValueError("content 必须是字符串")
        calls = msg.get("tool_calls") or []
        if not isinstance(calls, list) or len(calls) > 4:
            raise ValueError("一次最多四个工具调用")
        ids = set()
        for call in calls:
            fn = call["function"]
            if (call.get("type") != "function" or not isinstance(call["id"], str)
                    or not call["id"] or call["id"] in ids
                    or not isinstance(fn["name"], str)
                    or not isinstance(fn["arguments"], str)):
                raise ValueError("工具调用结构不合法")
            ids.add(call["id"])
        reason, answer = "", content
        try:
            envelope = json.loads(content)
            if isinstance(envelope, dict):
                reason = envelope.get("reason", "")
                answer = envelope.get("answer", "")
                if not isinstance(reason, str) or not isinstance(answer, str):
                    raise ValueError("reason 和 answer 必须是文本")
        except json.JSONDecodeError:
            pass  # 兼容普通文本回答；不把解析失败伪装成工具调用。
        if not calls and not answer.strip():
            raise ValueError("响应既没有工具调用，也没有最终答案")
        # 不保存厂商隐藏推理字段；reason 只是可展示的一句话动作说明。
        clean = {"role": "assistant", "content": content or None}
        if calls:
            clean["tool_calls"] = calls
        return {"message": clean, "calls": calls, "reason": reason[:300], "answer": answer}
    except (KeyError, IndexError, TypeError, ValueError) as exc:
        raise ParseError("LLM 输出结构不合法：" + str(exc)[:150]) from None
