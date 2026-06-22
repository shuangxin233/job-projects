# 企业知识库智能问答系统 - 后端

## 模块定位

`server` 是项目的 FastAPI 后端，负责文档上传、文本解析、chunk 切割、向量库构建、相似度检索和大模型问答。

## 核心职责

- 接收并校验 PDF 文件
- 解析文档文本
- 使用 `TokenTextSplitter` 进行文本切割
- 调用 Embedding 模型生成向量
- 将向量写入 ChromaDB
- 根据用户问题召回 Top-K 文档片段
- 组织上下文并调用 Groq / Gemini
- 提供健康检查、模型列表、向量库检查等 API

## 安装

```powershell
cd 求职项目\企业知识库智能问答系统\server
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
```

## 配置

创建 `.env`：

```env
GROQ_API_KEY=your-groq-key
GOOGLE_API_KEY=your-google-key
```

## 启动

```powershell
uvicorn main:app --reload
```

默认地址：

```text
http://127.0.0.1:8000
```

## 主要接口

- `POST /upload_and_process_pdfs`：上传并处理 PDF
- `POST /chat`：基于知识库回答问题
- `GET /vector_store/count/{provider}`：查看向量库数量
- `POST /vector_store/search`：直接检索向量库
- `GET /llm`：查看可用模型
- `GET /health`：健康检查
