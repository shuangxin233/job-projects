# 测试报告

验证日期：2026-09-07。环境：Windows、Python 3.10.13。

## 自动化测试：37 / 37 通过

执行命令：

```powershell
python -m unittest discover -v
```

最后一次功能验证输出：`Ran 37 tests in 2.386s`、`OK`。本报告不会把测试替身当作真实模型。

| 范围 | 已通过的行为 |
| --- | --- |
| 基本循环 | 直接回答、工具结果回填、连续多工具任务、单次多个 call_id 对应结果 |
| Session | A/w1、A/w2、B/w1 隔离；重建 Store 后恢复；同会话互斥、不同会话独立 |
| 追问 | 纯对话历史进入下一次 context；工具追问可完成之前的待办 |
| Memory | 完整轮次压缩、有界摘要、待办保留、工具消息不孤立、Schema 计入预算 |
| 终止与恢复 | 最大轮次停止、context 超限停止、无效模型输出修复、API 失败后保存已完成操作 |
| 工具 | 未知工具、非法参数 JSON、Schema 校验、除零恢复、AST 安全计算、待办去重与条件参数校验 |
| 输出解析 | 普通文本、reason 摘要、空结果、截断结果、重复调用 ID、message=null |
| HTTP | tools + auto 请求格式、429 有界重试、401 不重试、不泄露错误正文、超时与非法 JSON |
| DeepSeek 配置 | 官方地址显式关闭 thinking，其他服务不发送此专有参数 |
| Trace | 工具参数、结果、耗时、run_id 正常记录和持久化 |
| 余额不足 | 402 返回明确充值提示且不重试；真实冒烟脚本停止后续请求，记录未执行用例 |
| 免费 API 配置 | 智谱默认参数、可选 Groq、Qwen 非思考参数、1,024 tokens 输出上限、遵守 Retry-After、较长限流停止 |

单元测试通过说明程序能按给定模型输出正确处理流程。真实模型的工具选择与回答质量需要下面的独立验证。

## 当前方案：智谱免费 API，待用户配置新密钥

用户反馈 Groq 登录页显示 Forbidden。现已默认改用智谱免费 glm-4.7-flash，并新增请求参数测试，共 37 项测试通过。本机访问智谱官网返回 HTTP 200，未认证访问 API 地址返回 HTTP 401。**尚无用户的智谱 Key，未完成智谱真实模型功能验证。** 网络入口检查不等于模型调用成功。

## 历史尝试：Groq 免费 API

用户随后要求使用免费 API。已核对官方资料，将默认配置切换到 Groq Free 套餐的 `qwen/qwen3.8-27b`。本机配置已经准备好，旧 DeepSeek 密钥只做本地备份，没有转发到 Groq。免费方案的申请与额度说明见 [FREE_API_SETUP.md](FREE_API_SETUP.md)。

当前尚无用户的 Groq Key，因此**尚未完成 Groq 真实模型功能验证**。36 项测试包含模拟 HTTP 响应的协议验证，不能替代真实免费模型调用。随后用户反馈 Groq 登录页 Forbidden，因此已改用智谱方案。

本机还尝试了不携带密钥的 Groq 模型列表请求，收到 HTTP 403。该结果不能证明携带有效密钥后一定可用，账号权限和当前网络访问仍需在配置密钥后验证。尚未发送用户对话或旧平台密钥到 Groq。

## 历史验证：DeepSeek 请求因账户余额不足未通过

2026-09-07 已使用本地配置的真实 DeepSeek API 密钥发起请求。接口为 `https://api.deepseek.com/chat/completions`，模型参数为 `deepseek-v4-flash`。本次 8 个用例均收到 HTTP 402，没有拿到模型回答，也没有执行成功的工具调用。

```text
LLM HTTP 402：检查密钥、模型、余额或服务状态。 已完成的操作会保留。
```

上面是当时实际输出；随后已把 402 提示改为明确的“API 账户余额不足，请在服务商开放平台充值后重试”。按 [DeepSeek 官方错误码](https://api-docs.deepseek.com/zh-cn/quick_start/error_codes/)查询，402 对应余额不足。另调用只读余额接口返回 HTTP 200 且 `is_available=false`，确认当前账户没有可供 API 调用的余额。

结果摘要见 [evidence/live_api_attempt.json](evidence/live_api_attempt.json)。本地完整 trace 留在 `.runtime/live/20260907T091002Z/report.json`，未上传本地配置或账户余额明细。

因此这次历史测试没有通过真实 LLM 功能联调。它验证了接口能返回实际服务商错误，不能证明真实模型已经正确执行工具循环。现在请配置默认方案的智谱 Key 后运行：

```powershell
python scripts/live_smoke.py
```

或者使用本机集中配置文件：

```powershell
python scripts/live_smoke.py --env-file "$HOME\Desktop\项目制作过程\最小Agent-API配置.env"
```

预设 8 个真实模型用例：直接聊天、计算出 60、追问算出 15、模拟天气与待办、周报搜索与待办、完成之前待办、称呼追问、另一个窗口列待办。脚本检查实际工具 trace、数值和最终待办隔离，保存 `report.json`。本次问题暴露后已增加遇到 API 错误就停止的逻辑，报告区分执行数和跳过数；避免配置或余额问题导致无意义的后续请求。所有用例与隔离检查都通过后才将真实联调标记为通过。

## 额外检查

- `python -m mini_agent --help` 正常显示参数。
- 未配置密钥时，CLI 明确提示配置问题，不伪造模型回答。
- Windows PowerShell 启动脚本已实际执行；中文配置路径正常，缺少密钥时返回退出码 1。
- 最初 29 项测试曾发现 `message=null` 类型检查遗漏；修复后全部通过。加入 DeepSeek 请求参数验证后共有 30 项。
- 搜索与天气为 mock 数据；calculator 和 todo 的测试实际运行 Python 工具函数。

提交前最后一步：配置自己的智谱 Key，使用免费 glm-4.7-flash，执行真实 API 测试并更新本报告。不要将 .env 或自己的聊天数据库上传。
