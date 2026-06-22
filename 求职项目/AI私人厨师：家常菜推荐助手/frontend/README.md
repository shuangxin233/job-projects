# AI私人厨师前端

## 模块定位

这是 AI 私人厨师项目的 Next.js 前端，负责聊天式交互、用户输入、推荐结果展示和后端接口调用。

## 核心功能

- 输入食材、口味和做饭需求
- 调用 FastAPI 后端获取菜谱推荐
- 展示流式回复内容
- 展示菜谱卡片和聊天记录
- 支持配置后端 API 地址

## 启动方式

```powershell
npm install
npm run dev
```

默认访问：

```text
http://localhost:3000
```

## 后端地址配置

默认后端地址：

```text
http://localhost:8001
```

如需修改，在 `.env.local` 中配置：

```text
NEXT_PUBLIC_API_BASE_URL=http://localhost:8001
```

## 关键文件

- `app/page.tsx`：聊天页面主流程
- `components/ChatInput.tsx`：输入框和图片选择
- `components/ChatMessage.tsx`：消息展示和 Markdown 渲染
- `components/RecipeCard.tsx`：菜谱卡片
- `lib/api.ts`：后端接口调用
- `types/chat.ts`：聊天相关类型
