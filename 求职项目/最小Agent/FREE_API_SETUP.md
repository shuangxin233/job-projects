# 使用免费的真实 API

题目只要求真实 LLM API，没有指定服务商或要求付费。兼容 OpenAI 格式只是请求协议，不代表必须购买 OpenAI API。

## 当前方案：智谱 GLM-4-Flash-250414

智谱在[官方模型概览](https://docs.bigmodel.cn/cn/guide/start/model-overview)中将 glm-4-flash-250414 列为免费模型，[模型文档](https://docs.bigmodel.cn/cn/guide/models/free/glm-4-flash-250414)确认支持 Function Calling。核对日期：2026-09-07。模型名完整使用 glm-4-flash-250414，程序不会自动切换付费模型。

本机已配置智谱 Key 并完成 8 项真实 API 测试，全部通过。换到其他电脑需申请自己的密钥，详见 TEST_REPORT.md。

## 申请和配置

1. 打开[智谱开放平台](https://bigmodel.cn)，按页面提供的方式注册或登录。
2. 进入控制台的 API 密钥管理页面创建密钥。若平台提示实名认证，按平台要求自行完成。使用免费 glm-4-flash-250414，无需购买 Coding Plan。
3. 用记事本打开桌面 `项目制作过程/最小Agent-API配置.env`，只把智谱密钥填在 LLM_API_KEY= 后，保存。不要发到聊天或 GitHub，也不要使用其他平台密钥。

```dotenv
LLM_API_KEY=你自己的智谱密钥
LLM_BASE_URL=https://open.bigmodel.cn/api/paas/v4
LLM_MODEL=glm-4-flash-250414
```

模型名称、地址已准备好。换到其他电脑时，从 .env.example 复制出 .env，填写自己的密钥。

## 运行验证

在项目目录运行：

```powershell
python scripts/live_smoke.py --env-file "$HOME\Desktop\项目制作过程\最小Agent-API配置.env"
```

一次问题可能触发多次模型请求。免费模型仍受平台限流和容量约束，以控制台显示为准。本项目单次输出最多 1,024 tokens，工具循环最多六次，重试等待最多 30 秒。出现限流请等待恢复；不会自动改用付费服务。

客户端默认将相邻请求开始时间间隔设为 10 秒，可通过 `.env` 中 `LLM_MIN_INTERVAL_SECONDS` 调整（0～30）。完整 8 项测试通常需要数分钟；两个窗口同时运行时也共享平台账号额度，程序只对单个进程限速。API HTTP 429 可能对应不同原因，本项目提取数字业务码，避免把余额问题当作短期限流。

智谱业务码 1305 表示模型访问量过大，客户端等待 30 秒后重试一次；如果仍未恢复，测试停止。稍后使用 `--resume-report .runtime/live/<原时间>/report.json` 继续未通过用例，原会话和失败尝试都会保留。

主循环和工具仍由本地 Python 实现，没有用平台内置 Agent 代替。真实测试状态见 TEST_REPORT.md，不能把模拟 HTTP 测试当成模型已调用成功。

## 为什么更换 Groq

用户的 Groq 密钥页面显示 Forbidden，本机未认证请求也返回 403。仅凭错误不能确定具体是网络、权限还是地域原因。为继续免费方案，改用本机能访问官网的智谱；旧平台密钥没有转发到新平台。
