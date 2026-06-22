# AI私人厨师：家常菜推荐助手

## 项目定位

基于 Next.js + FastAPI + Ollama 的家常菜推荐助手。用户输入食材或做饭需求后，前端以聊天方式调用后端接口，后端优先使用本地 Ollama 模型流式返回菜谱建议；如果 Ollama 不可用，则使用规则菜谱兜底，保证演示稳定。

## 跨设备运行结论

可以在其他设备运行，但需要安装 Python 和 Node.js。Ollama 是可选依赖：不安装或未启动时，项目仍会返回规则兜底菜谱。

## 后端启动

```powershell
cd AI私人厨师：家常菜推荐助手
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
cd AI私人厨师：家常菜推荐助手\frontend
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

```powershell
ollama pull qwen2.5:3b
```

后端默认请求：

```text
http://localhost:11434/api/chat
```

## GitHub 上传说明

已排除 `OllamaSetup.exe`、`.next`、`node_modules`、聊天历史和 `.env`。新设备运行时重新安装依赖即可。

