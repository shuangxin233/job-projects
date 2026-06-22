# AI私人厨师：家常菜推荐助手

## 项目定位

这是一个基于 FastAPI + Next.js 的家常菜推荐助手。用户可以输入已有食材、口味偏好或做饭需求，系统通过后端推荐逻辑生成菜谱建议，并在前端以聊天式界面展示结果。

项目适合作为求职展示中的完整 Web 应用案例：包含前后端分离、接口设计、流式回复、可选本地大模型调用和兜底推荐逻辑。

## 核心流程

```text
用户输入做饭需求
-> 前端发送请求到 FastAPI
-> 后端解析食材、口味和场景
-> 优先调用本地 Ollama 模型生成建议
-> 如果模型不可用，使用规则推荐兜底
-> 返回菜名、食材、步骤和提示
-> 前端展示为聊天记录和菜谱卡片
```

## 技术栈

- 后端：Python、FastAPI、Pydantic
- 前端：Next.js、React、TypeScript
- 模型：Ollama 本地模型，可选
- 其他：REST API、聊天记录管理、规则兜底推荐

## 后端启动

```powershell
cd 求职项目\AI私人厨师：家常菜推荐助手
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
python -m backend.main
```

默认地址：

```text
http://127.0.0.1:8001
```

接口文档：

```text
http://127.0.0.1:8001/docs
```

## 前端启动

```powershell
cd 求职项目\AI私人厨师：家常菜推荐助手\frontend
npm install
npm run dev
```

默认地址：

```text
http://localhost:3000
```

如后端地址变化，可在 `frontend/.env.local` 中配置：

```text
NEXT_PUBLIC_API_BASE_URL=http://localhost:8001
```

## Ollama 可选配置

不安装 Ollama 时，项目仍可通过规则兜底返回菜谱建议。需要本地大模型效果时可执行：

```powershell
ollama pull qwen2.5:3b
```

后端默认请求：

```text
http://localhost:11434/api/chat
```

## 面试讲解重点

- 前后端分离：Next.js 负责交互，FastAPI 负责业务逻辑。
- 模型可用性处理：Ollama 不可用时，系统仍能稳定返回结果。
- 接口清晰：推荐、聊天和文件相关能力拆分到不同模块。
- 可扩展：后续可接入用户画像、历史偏好、营养分析和食材库存管理。
