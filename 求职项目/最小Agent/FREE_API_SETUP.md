# 使用免费的真实 API

面试题只要求“需要使用真实的 LLM API”，没有指定 DeepSeek、OpenAI 或付费服务。免费套餐下调用真实模型同样符合这一要求。项目里说的“兼容 OpenAI 格式”只是请求协议，不代表一定调用 OpenAI 的付费服务。

## 当前默认方案：Groq Free + Qwen

截至 2026-09-07，[Groq 官方免费限额页](https://console.groq.com/docs/rate-limits)列出 `qwen/qwen3.8-27b` 的 Free 配额：每分钟 30 次请求、每天 1,000 次请求、每分钟 8,000 tokens、每天 200,000 tokens。具体以你的账号 Limits 页面为准，平台可能调整。

[模型文档](https://console.groq.com/docs/model/qwen/qwen3.8-27b)确认支持 Tool Use，适合让本项目把工具 Schema 交给模型，工具本身仍由本地 Python 执行。这个模型目前标记为 Preview，后续可用性可能变化。

这里使用普通模型 API，不使用 Groq Compound 或平台内置 Agent 来代替主循环。

## 你要做的操作

1. 打开 [Groq API Keys 页面](https://console.groq.com/keys)，按页面提供的方式注册或登录。
2. 保持 **Free** 套餐，创建一个 API Key；不要升级 Developer 付费套餐。官方说明升级付费套餐需要提供支付方式，见[计费说明](https://console.groq.com/docs/billing-faqs)。
3. 用记事本打开本地 `.env`，或已为你准备好的桌面 `项目制作过程/最小Agent-API配置.env`。
4. 只填写 `LLM_API_KEY=` 后的 Groq 密钥，保存。不要使用 DeepSeek 的密钥，不要发到聊天或 GitHub。

```dotenv
LLM_API_KEY=你自己的Groq密钥
LLM_BASE_URL=https://api.groq.com/openai/v1
LLM_MODEL=qwen/qwen3.8-27b
```

如果网页登录、地区可用性或验证码遇到问题，请说明具体提示。当前没有你的 Groq 密钥，因此尚不能确认这个账号和网络能成功调用该模型。

## 运行验证

在项目目录执行：

```powershell
python scripts/live_smoke.py --env-file "$HOME\Desktop\项目制作过程\最小Agent-API配置.env"
```

一次用户问题可能需要多次 API 请求，8 个测试用例也可能消耗十几次或更多调用。免费套餐的每分钟 token 限额比单纯的请求次数更容易触发；出现 429 时等额度恢复，再使用新的测试会话重跑。

客户端只使用你配置的服务，不会自动调用付费后备模型。每次输出最多 1,024 tokens；遇到重试等待超过 30 秒的情况会停止并提示。免费不是不限量，也不保证一直有空闲容量。

在其他电脑上需要自己申请密钥。完整测试执行状态以 `TEST_REPORT.md` 为准，不把 HTTP 替身测试说成免费模型已经调用成功。
