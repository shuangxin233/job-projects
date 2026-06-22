# 企业知识库智能问答系统 - 前端

## 模块定位

`client` 是项目的 Streamlit 前端，负责文件上传、模型选择、聊天交互、检索检查和聊天记录导出。

## 核心功能

- 上传一个或多个 PDF 文件
- 选择 Groq 或 Gemini 模型
- 向后端提交文档处理任务
- 基于已处理文档进行问答
- 查看向量库检索结果
- 导出聊天历史

## 安装

```powershell
cd 求职项目\企业知识库智能问答系统\client
pip install -r requirements.txt
```

## 启动

```powershell
streamlit run app.py
```

## 配置

如后端地址变化，修改：

```python
API_URL = "http://127.0.0.1:8000"
```

位置：

```text
client/utils/config.py
```

## 使用流程

1. 先启动 FastAPI 后端。
2. 启动 Streamlit 前端。
3. 选择模型提供商和模型。
4. 上传 PDF 并提交处理。
5. 在聊天框中提问。
6. 如需排查效果，打开检索检查面板查看召回片段。
