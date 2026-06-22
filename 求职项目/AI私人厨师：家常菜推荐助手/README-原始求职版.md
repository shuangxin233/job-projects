# AI 私人厨师项目说明

## 项目定位

这是一个面向家庭做饭场景的 AI 应用。用户输入冰箱里的食材，或者上传食材图片，系统通过前端聊天界面调用后端接口，返回家常菜推荐、步骤、调味建议和食品安全提醒。

这个项目适合初学者求职展示，因为它不只是静态页面，而是包含了前后端联调、流式响应、本地大模型调用、会话历史和接口文档。

## 本次新增内容

1. 后端聊天接口 `/api/v1/chat/stream`：支持流式返回。
2. 本地 Ollama 调用：优先调用本地大模型生成菜谱。
3. 兜底菜谱逻辑：Ollama 没启动时，仍然能返回可演示的菜谱结果。
4. 会话历史保存：按 `thread_id` 存储用户和 AI 消息。
5. 前端中文乱码修复：聊天页面、输入框、消息展示、接口错误提示已经整理。
6. OSS 上传容错：OSS 没配置时，后端可以正常启动，文字聊天不受影响。
7. 求职资料：新增学习手册、简历话术、GitHub 参考资料和接口测试文件。

## 技术栈

- 前端：Next.js、React、TypeScript、Tailwind CSS
- 后端：FastAPI、Pydantic、StreamingResponse
- AI：Ollama 本地模型接口
- 存储：本地 JSON 文件保存会话历史
- 图片上传：阿里云 OSS 预签名 URL，可选配置

## 项目结构

```text
项目资料/
  app/                         后端 FastAPI 项目
    api/v1/chat.py             聊天、历史、清空接口
    api/v1/oss.py              图片上传预签名接口
    services/ollama_client.py  本地 Ollama 流式调用
    services/recipe_engine.py  私厨提示词和兜底菜谱
    services/chat_store.py     本地会话历史存储
  私厨-前端源码/                Next.js 前端
  README-求职版.md             本文件
  学习手册-从零到面试.md        逐步学习说明
  简历和面试话术.md             简历写法和面试回答
  GitHub参考资料.md             本次参考的开源项目
  接口测试.http                接口测试示例
```

## 启动后端

在 `C:\Users\shuangxin\Desktop\项目资料` 目录打开终端：

```powershell
pip install -r requirements.txt
python -m app.main
```

如果要启用图片上传到阿里云 OSS，再额外安装：

```powershell
pip install -r requirements-oss.txt
```

后端默认地址：

```text
http://127.0.0.1:8001
```

接口文档地址：

```text
http://127.0.0.1:8001/docs
```

## 启动 Ollama

如果你已经安装了 Ollama，先拉取一个适合中文的模型：

```powershell
ollama pull qwen2.5:3b
```

然后保持 Ollama 运行。后端会自动请求：

```text
http://localhost:11434/api/chat
```

如果 Ollama 没启动，项目会自动使用兜底菜谱逻辑，方便你演示项目。

## 启动前端

进入前端目录：

```powershell
cd C:\Users\shuangxin\Desktop\项目资料\私厨-前端源码
npm install
npm run dev
```

浏览器访问：

```text
http://localhost:3000
```

## 推荐演示话术

可以这样介绍：

> 这是一个 AI 私人厨师应用。用户输入现有食材后，前端通过 fetch 调用 FastAPI 后端，后端使用 StreamingResponse 实时返回 AI 生成内容。后端优先调用本地 Ollama 模型，如果模型服务不可用，就用规则菜谱兜底，保证演示稳定。每轮对话会按 thread_id 存到本地 JSON，刷新页面后还能恢复历史。

## 后续可扩展方向

- 把 JSON 历史存储替换成 SQLite。
- 增加用户登录和多会话列表。
- 接入真正的图片识别模型，把食材图片转成食材名称。
- 增加收藏菜谱、购物清单、营养估算。
- 给后端增加 pytest 自动化测试。

## 上传 GitHub 前注意

根目录已经新增 `.gitignore`。上传 GitHub 时不要提交 `OllamaSetup.exe`、`.env`、`node_modules`、`.next`、`app/data/chat_history.json` 这些本地文件。
