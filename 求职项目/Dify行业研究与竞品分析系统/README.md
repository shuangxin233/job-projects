# Dify行业研究与竞品分析系统

## 项目定位

这是一个面向行业研究、竞品分析和主题调研的报告生成系统。项目使用 Dify 负责多步骤工作流编排，同时补充 FastAPI 后端，用于任务提交、本地知识库检索、证据清洗、报告保存、导出和评估。

项目重点展示从“用户提出研究主题”到“生成结构化 Markdown 报告”的完整流程。

## 核心流程

```text
用户输入研究主题
-> 明确研究目标和约束
-> 生成研究计划
-> 优先检索本地知识库
-> 本地证据不足时补充外部资料
-> 清洗、去重并编号证据
-> 检查信息缺口
-> 按章节生成研究报告
-> 检查引用和结构完整性
-> 导出 Markdown 报告
```

## 技术栈

- Dify Workflow
- FastAPI
- Pydantic
- 本地 JSON 向量库
- 可选 ChromaDB
- Markdown 报告生成
- 规则化报告评估脚本

## 主要文件

- `Deep Researcher On Dify .yml`：Dify 工作流配置文件
- `backend/`：FastAPI 后端
- `evaluation/`：报告质量评估脚本和测试主题
- `DIFY_WORKFLOW_UPGRADE_CHECKLIST.md`：Dify 工作流配置检查表
- `UPGRADE_NOTES.md`：项目改进记录

## 后端启动

```powershell
cd 求职项目\Dify行业研究与竞品分析系统\backend
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8010
```

可选 `.env`：

```env
DIFY_API_KEY=app-xxx
DIFY_WORKFLOW_URL=http://127.0.0.1/v1/workflows/run
DIFY_TIMEOUT_SECONDS=180
```

如果没有配置 Dify，后端仍会使用本地证据和报告质量控制流程生成草稿，方便演示主流程。

## 本地知识库 RAG

后端支持本地知识库优先检索：

```text
上传本地文件 / 添加文本
-> 抽取文本
-> 切分为 chunk
-> 生成 embedding
-> 存入 JSON 向量库或 ChromaDB
-> 检索 Top-K 相似 chunk
-> 作为报告证据
-> 证据不足时再补充外部资料
```

默认使用轻量 JSON 向量库。需要 ChromaDB 时可设置：

```env
VECTOR_STORE_BACKEND=chroma
```

## 评估脚本

```powershell
python evaluation/evaluate_reports.py
```

评估内容包括：

- 报告必需章节是否完整
- 引用标记数量是否足够
- 每个测试主题是否通过质量检查

## 面试讲解重点

- 使用 Dify 编排多步骤 AI 工作流。
- 后端把工作流能力产品化，提供任务提交、报告保存和导出。
- 本地知识库优先，减少直接依赖联网搜索。
- 支持 chunking、embedding、向量存储和 Top-K 检索。
- 生成报告前会做证据清洗、去重和信息缺口检查。
- 评估脚本可以量化报告结构和引用质量。

## 许可证

项目包含开源组件和个人扩展代码，使用时请遵守仓库中保留的许可证文件。
