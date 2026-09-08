# 面试作业｜shuangxin233

本次提交包含“从零实现最小可用 Agent”和“架构题回答”两部分。

| 材料 | 在线查看 | 下载与运行 |
| --- | --- | --- |
| 最小可用 Agent | [项目 README、设计与 memory 说明](求职项目/最小Agent/README.md) | [解压运行指南](求职项目/最小Agent/QUICKSTART.md) |
| 架构题回答 | [五道架构问答在线阅读](求职项目/架构题回答/README.md) | [下载 Word 原文件](求职项目/架构题回答/架构题回答.docx?raw=true) |

## 题目要求与提交材料对照

| 提交要求 | 本项目提供的内容 | 查看位置 |
| --- | --- | --- |
| 使用真实 LLM API | 真实 HTTP 客户端接入智谱 glm-4-flash-250414；8 项真实场景通过，附原始问答及工具 trace | [API 客户端](求职项目/最小Agent/mini_agent/llm.py)、[测试报告](求职项目/最小Agent/TEST_REPORT.md)、[真实调用证据](求职项目/最小Agent/evidence/live_api_success.json) |
| 代码链接 | 手写 Runtime、工具注册与 Schema、会话、memory、测试和启动入口全部公开 | [完整项目目录](求职项目/最小Agent) |
| README：运行方式、系统设计、memory 召回时机与放置方式 | 第 1 节介绍运行；第 3 节介绍系统设计；第 4 节说明召回时机、消息角色、上下文顺序及压缩策略 | [README](求职项目/最小Agent/README.md)、[解压运行指南](求职项目/最小Agent/QUICKSTART.md) |
| AI Prompt 与问题解决记录 | 开发约束、当前实际 System Prompt 原文、修复 Prompt、最终测试输入，以及失败、定位、修正与验证记录 | [AI_PROMPTS.md](求职项目/最小Agent/AI_PROMPTS.md)、[PROBLEM_SOLVING.md](求职项目/最小Agent/PROBLEM_SOLVING.md) |

Memory 每次用户发言先按用户和会话 ID 读取；每次调用模型前重新组装。固定 system 规则之后放近期历史，再将摘要、待办和最近工具结果作为独立 user 数据消息放到当前问题前；本轮工具返回结果随后追加。完整机制和边界见 README 第 4 节。

“真实 LLM API”是已经实际调用模型，不要求把个人 API 密钥公开提交。运行者自行配置自己的密钥；确定性单元测试与真实 API 验证分开记录。

## 一次下载两份作业

**[下载面试作业提交包 ZIP](面试提交/面试作业-提交包.zip?raw=true)**

该压缩包仅包含本次提交的 Agent 完整源码、运行指南、测试与证据、AI Prompt、问题解决记录、架构题 Word 原件和提交说明；不包含其他历史项目、真实 API 密钥或运行缓存。完整解压后先阅读 `答案文件/提交说明.txt`。

Agent 使用 Python 3.10+ 标准库，无需第三方 Python 依赖。运行真实聊天需要运行者自己的 API Key 和可访问 API 的网络。搜索、天气是模拟数据；计算器与待办为真实本地执行。

## 验证记录

- 2026-09-07：8 项真实 API 场景通过，包括会话隔离和追问。见 [测试报告](求职项目/最小Agent/TEST_REPORT.md)。
- 2026-09-08：实际压缩、解压到独立环境，44 项自动化测试通过，并完成单条真实 API 计算器调用。见 [交付验证报告](求职项目/最小Agent/DELIVERY_CHECK.md)。
- 架构题为书面设计回答，在线版保留 Word 原文。

其他求职展示项目见 [项目目录](求职项目/README.md)。
