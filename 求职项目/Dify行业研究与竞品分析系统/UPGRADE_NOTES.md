# Dify行业研究与竞品分析系统 - 改进记录

## 改进范围

本项目围绕行业研究和竞品分析场景，对工作流调用、本地知识库检索、报告生成、证据管理和质量评估进行了工程化整理。

## 主要改进

1. 引用和证据管理
   - 将不同来源的资料统一整理为证据列表。
   - 为每条证据分配 `[S1]`、`[S2]` 等引用编号。
   - 报告生成时要求引用这些编号，方便追溯答案来源。

2. 本地知识库 RAG
   - 支持添加纯文本，也支持上传 `.txt`、`.md`、`.pdf`、`.docx` 文件。
   - 文档会被切分为带重叠的 chunk。
   - chunk 会被向量化并写入本地向量存储。
   - 后端支持 Top-K 相似度检索。
   - 研究任务优先搜索本地知识库；本地证据不足时，再使用请求中提供的外部资料。
   - 默认使用 JSON 向量存储，设置 `VECTOR_STORE_BACKEND=chroma` 后可切换到 ChromaDB。

3. 证据清洗
   - 对本地知识库和外部资料进行清洗、去重和截断。
   - 把“证据准备”和“报告写作”拆开，减少无关内容进入最终报告。

4. 研究计划和质量控制
   - 后端会生成研究计划。
   - 报告生成前会检查信息缺口。
   - 报告生成后会检查章节覆盖、证据数量和引用使用情况。

5. FastAPI 后端
   - `backend/` 提供研究任务提交、知识库管理、任务历史、Markdown 导出和本地草稿生成接口。

6. 评估脚本
   - `evaluation/topics.json` 定义固定测试主题和必需章节。
   - `evaluation/evaluate_reports.py` 检查报告章节覆盖和引用情况。

## 推荐演示流程

1. 在 Dify 中导入 `Deep Researcher On Dify .yml`。
2. 按 `DIFY_WORKFLOW_UPGRADE_CHECKLIST.md` 检查工作流配置。
3. 启动后端：

```powershell
cd backend
uvicorn app.main:app --reload --port 8010
```

4. 通过 `/knowledge/documents` 或 `/knowledge/files` 添加本地知识。
5. 通过 `/knowledge/search` 验证 Top-K 检索。
6. 通过 `/research` 提交研究任务。
7. 通过 `/reports/{task_id}.md` 导出 Markdown 报告。
8. 运行 `python evaluation/evaluate_reports.py` 检查报告质量。
