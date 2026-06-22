import { Message } from "@/types/chat";
import { ChefHat, Loader2, User } from "lucide-react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";

interface ChatMessageProps {
  message: Message;
}

export function ChatMessage({ message }: ChatMessageProps) {
  const isUser = message.role === "user";

  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"}`}>
      <div className={`flex max-w-[86%] gap-3 ${isUser ? "flex-row-reverse" : ""}`}>
        <div
          className={`grid h-9 w-9 shrink-0 place-items-center rounded-full ${
            isUser ? "bg-slate-700 text-white" : "bg-orange-600 text-white"
          }`}
        >
          {message.streaming || message.loading ? (
            <Loader2 size={16} className="animate-spin" />
          ) : isUser ? (
            <User size={16} />
          ) : (
            <ChefHat size={16} />
          )}
        </div>

        <div
          className={`rounded-xl px-4 py-3 text-sm leading-6 shadow-sm ${
            isUser
              ? "bg-slate-700 text-white"
              : "border border-stone-200 bg-white text-stone-800"
          }`}
        >
          {message.imageUrl && (
            <img
              src={message.imageUrl}
              alt="上传的食材图片"
              className="mb-2 max-h-48 w-full max-w-64 rounded-lg object-cover"
            />
          )}
          {isUser ? (
            <p className="whitespace-pre-wrap">{message.content}</p>
          ) : (
            <div className="prose prose-sm max-w-none prose-stone">
              <ReactMarkdown
                remarkPlugins={[remarkGfm]}
                components={{
                  a: ({ href, children }) => (
                    <a href={href} target="_blank" rel="noopener noreferrer">
                      {children}
                    </a>
                  ),
                  code: ({ children }) => (
                    <code className="rounded bg-stone-100 px-1.5 py-0.5 text-xs">
                      {children}
                    </code>
                  ),
                }}
              >
                {message.content || (message.streaming ? "正在生成..." : "")}
              </ReactMarkdown>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
