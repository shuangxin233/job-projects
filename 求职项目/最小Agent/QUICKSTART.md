# 面试官：解压后如何运行

本项目为 Python 命令行程序，全部源码已包含。需要 **Python 3.10+**，只使用标准库，不需要 pip、Node.js、Docker、Git 或数据库服务。Python 可从 [官网](https://www.python.org/downloads/) 安装。本项目实测环境为 Windows、Python 3.10.13。

真实聊天还需要：能访问 API 的网络和运行者自己的有效 **API Key**。提交目录不含作者密钥，仅解压不能直接调用真实模型；没有密钥仍可运行全部自动化测试并阅读真实测试证据。

## Windows：按顺序执行

完整解压压缩包，进入含 README.md、mini_agent、tests 的“最小Agent”目录，在此处打开 PowerShell。不要在 ZIP 预览窗口中运行。

1. 执行 `python --version`，确认至少为 3.10。若找不到 python，尝试 `py -3 --version`，后续命令中的 python 也统一替换为 py -3。两者都不存在时先安装 Python，启用安装器提供的命令行访问选项，然后重新打开终端。
2. 先运行无需网络和密钥的测试：

```powershell
python -m unittest discover -v
```

预期 `Ran 44 tests`、`OK`。这些是确定性测试，真实 API 验证另行执行。

3. 首次配置时复制示例；已有 `.env` 时直接编辑，避免覆盖：

```powershell
Copy-Item .env.example .env
notepad .env
```

在 [智谱开放平台](https://bigmodel.cn) 控制台创建自己的 API Key，填入 `.env`：

```dotenv
LLM_API_KEY=填入运行者自己的智谱密钥
LLM_BASE_URL=https://open.bigmodel.cn/api/paas/v4
LLM_MODEL=glm-4-flash-250414
LLM_MIN_INTERVAL_SECONDS=10
```

注意文件名必须是 `.env`，不是 `.env.txt`；密钥不是登录密码。模型在 2026-09-07 按官方免费模型资料核对并完成验证，后续限额和可用性以平台为准。

4. 启动聊天：

```powershell
$env:PYTHONUTF8="1"
python -m mini_agent --user A --session window1 --trace
```

或者使用会检查 Python 版本的启动脚本：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\run_windows.ps1 -Session window1
```

脚本默认使用解压目录中的 `.env` 和 `.runtime`，不依赖作者桌面。解压目录需要可写。另开一个终端，把 window1 改为 window2，即可演示独立会话。`/state` 查看状态，`/exit` 退出；相同 user 和 session 可重启续聊。

## macOS / Linux

使用标准库命令行入口；本次未在这两种系统上实测，Windows 启动脚本不适用于它们。

```sh
cd /你解压的路径/答案文件/最小Agent
python3 --version
python3 -c "import sqlite3, ssl"
python3 -m unittest discover -v
# 仅首次配置时复制，随后用文本编辑器填写 .env 中自己的密钥
cp .env.example .env
PYTHONUTF8=1 python3 -m mini_agent --user A --session window1 --trace
```

需要 Python 3.10+ 及其标准库 sqlite3、ssl；使用精简系统 Python 时应先补全系统 Python 组件。

## 真实 API 测试

配置 `.env` 后，在项目目录执行；macOS/Linux 将 python 换成 python3：

```sh
python -m mini_agent --user demo --session calculation --message "请用计算器计算 (12+8)*3。" --trace
python scripts/live_smoke.py
```

完整 API 测试需要数分钟，报告位于 `.runtime/live/<时间>/report.json`。历史 8 项真实场景通过的问答与日志在 `evidence/live_api_success.json`。搜索、天气是模拟数据；计算、待办和 LLM 请求是真实执行。

## 常见问题

| 现象 | 处理方式 |
| --- | --- |
| No module named mini_agent / 发现 0 项测试 | 进入含 README.md、mini_agent、tests 的“最小Agent”目录再执行 |
| 提示缺少 API Key | 检查 `.env` 文件名和非空密钥，不能填写登录密码 |
| 修改配置不生效 | 系统已有的 LLM_API_KEY、LLM_MODEL、LLM_BASE_URL 环境变量优先；清除当前终端中的旧变量或换新终端 |
| HTTP 401 / 403 | 检查密钥所属平台、账号权限及网络访问 |
| HTTP 429 / 业务码 1305 | 服务繁忙或限流，稍后重试；已有有界重试，不会自动切换付费模型 |
| HTTP 402 / 业务码 1113 | 检查账号状态和所选模型；不同平台密钥不能混用 |
| 网络超时 / TLS 错误 | 检查网络、代理、系统时间和证书，不要关闭证书验证 |
| 六轮上限停止 | 查看 trace，将任务表达得更明确或拆成多条输入 |

无法获得密钥时，可先运行自动化测试并查看历史真实 API 证据，这不等于在该电脑上重新通过真实 API 测试。模型可能回答错误，程序可运行不代表任意请求都保证成功。
