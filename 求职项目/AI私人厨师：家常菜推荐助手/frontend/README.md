# AI 私人厨师前端

这是 AI 私人厨师项目的 Next.js 前端。页面提供聊天式交互，调用后端 FastAPI 接口获取流式菜谱推荐。

## 启动

```powershell
npm install
npm run dev
```

默认访问：

```text
http://localhost:3000
```

## 后端地址

默认后端地址是：

```text
http://localhost:8001
```

如果后端部署到其他地址，可以在 `.env.local` 中配置：

```text
NEXT_PUBLIC_API_BASE_URL=http://localhost:8001
```

## 关键文件

- `app/page.tsx`：聊天页面主流程
- `components/ChatInput.tsx`：输入框和图片选择
- `components/ChatMessage.tsx`：消息展示和 Markdown 渲染
- `lib/api.ts`：后端接口封装
- `types/chat.ts`：聊天相关类型
