# 企业知识库智能问答系统

## 项目定位

这是一个面向企业文档问答场景的 RAG 系统。用户上传 PDF 文档后，系统完成文本解析、切割、向量化、ChromaDB 存储、Top-K 检索和大模型问答，前端提供聊天、文件上传、检索检查和历史导出能力。

项目重点展示完整 RAG 流程和前后端分离架构，而不是单纯调用大模型回答问题。

## 核心流程

```text
用户上传 PDF
-> FastAPI 接收文件
-> 文档解析并抽取文本
-> TokenTextSplitter 切割文本
-> Embedding 模型向量化 chunk
-> 写入 ChromaDB 向量库
-> 用户提出问题
-> 系统执行相似度检索并召回 Top-K chunk
-> 将检索证据传入 LLM
-> 返回带上下文依据的答案
-> Streamlit 前端展示问答和检索信息
```

## 技术栈

- 前端：Streamlit
- 后端：FastAPI
- 文档处理：PyPDF
- 文本切割：TokenTextSplitter
- 向量库：ChromaDB
- Embedding：HuggingFace / Google GenAI
- LLM：Groq / Gemini
- 编排：LangChain

## 目录结构

```text
企业知识库智能问答系统/
├── client/              # Streamlit 前端
├── server/              # FastAPI 后端
├── assets/              # 架构图和演示图
├── UPGRADE_NOTES.md     # 改进记录
├── 部署说明.md          # 跨设备运行说明
└── README.md
```

## 安装依赖

后端：

```powershell
cd 求职项目\企业知识库智能问答系统\server
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
```

前端：

```powershell
cd 求职项目\企业知识库智能问答系统\client
pip install -r requirements.txt
```

## 环境变量

在 `server` 目录下创建 `.env`，填写本地 API Key：

```env
GROQ_API_KEY=your-groq-key
GOOGLE_API_KEY=your-google-key
```

## 启动方式

启动后端：

```powershell
cd 求职项目\企业知识库智能问答系统\server
uvicorn main:app --reload
```

启动前端：

```powershell
cd 求职项目\企业知识库智能问答系统\client
streamlit run app.py
```

## 主要功能

- 多 PDF 上传与解析
- 文本切割和 chunk 管理
- Embedding 向量化
- ChromaDB 本地向量库
- Top-K 相似度检索
- Groq / Gemini 模型切换
- 检索结果检查
- 聊天历史导出

## 面试讲解重点

- 这是标准 RAG 流程：切割、向量化、入库、召回、生成。
- 用户问题不会直接交给大模型，而是先从企业文档中找证据。
- 前端只负责交互，后端集中处理文档、向量库和 LLM 调用。
- 检索检查功能可以帮助解释模型回答来自哪些文档片段。
- 新设备运行时需要重新上传文档生成向量库，真实密钥不会上传到 GitHub。
