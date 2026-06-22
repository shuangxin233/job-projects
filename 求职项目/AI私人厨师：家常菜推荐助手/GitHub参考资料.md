# GitHub 参考资料

本次新增内容参考的是开源项目的方向和技术选型，没有直接复制对方业务代码。

## 1. Ollama Python Library

链接：https://github.com/ollama/ollama-python

参考点：

- Ollama 适合作为本地大模型入口。
- README 中展示了 `stream=True` 的流式聊天用法。
- 本项目没有强依赖 `ollama` Python 包，而是用 HTTP 请求直接访问本地 `/api/chat`，降低依赖复杂度。

## 2. FastAPI StreamingResponse 示例

链接：https://github.com/fastapi/fastapi/blob/master/docs_src/custom_response/tutorial007_py310.py

参考点：

- FastAPI 可以用 `StreamingResponse` 返回生成器内容。
- 本项目把这个思路用于 AI 聊天，后端每生成一段文本就返回给前端。

## 3. Next.js + FastAPI + Ollama 全栈项目

链接：https://github.com/rabbicse/llm

参考点：

- 该项目方向是 Next.js 前端 + FastAPI 后端 + Ollama/DeepSeek，并强调 event streaming。
- 本项目选择相同的大方向，但控制复杂度，只保留初学者能讲清楚的聊天、流式响应和本地模型调用。

## 4. Grocery Assistant Chatbot

链接：https://github.com/Vedantshi/grocery-assistant-chatbot

参考点：

- 食材、购物、菜谱推荐是适合 AI 助手落地的垂直场景。
- 本项目把场景聚焦到“冰箱食材 -> 家常菜推荐”，更适合个人作品集。

## 5. Vercel AI Chatbot

链接：https://github.com/vercel/ai-chatbot

参考点：

- 聊天式产品常见交互包括输入框、消息列表、流式显示、历史会话。
- 本项目没有引入完整模板，只保留最必要的聊天交互，避免初学阶段项目过重。

## 为什么没有直接复制 GitHub 项目

求职项目更重要的是你能讲清楚代码。直接搬大型开源项目会导致：

- 技术点太多，面试解释困难。
- 环境依赖复杂，演示容易失败。
- 项目不像自己做的。

所以这次只参考开源项目的技术方向，然后在你现有项目基础上补充难度适中的功能。
