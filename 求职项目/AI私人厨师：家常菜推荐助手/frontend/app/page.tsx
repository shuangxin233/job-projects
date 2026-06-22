"use client";

import { useEffect, useRef, useState } from "react";
import { ChefHat, Plus, Sparkles, UtensilsCrossed } from "lucide-react";

import { ChatInput } from "@/components/ChatInput";
import { ChatMessage } from "@/components/ChatMessage";
import { clearChatHistory, getChatHistory, streamChat, uploadImageToOss } from "@/lib/api";
import { generateUUID } from "@/lib/utils";
import { ApiChatMessage, Message } from "@/types/chat";

const samplePrompts = [
  "我有鸡蛋、番茄和米饭，帮我安排一顿晚饭",
  "只有土豆和鸡胸肉，想做低脂一点",
  "给我推荐一道 20 分钟内能完成的家常菜",
];

export default function Home() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [processing, setProcessing] = useState(false);
  const [threadId, setThreadId] = useState("");
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const messageIdCounter = useRef(0);

  const toMessage = (item: ApiChatMessage, index: number): Message => ({
    id: `history_${index}_${item.created_at || Date.now()}`,
    role: item.role,
    content: item.content,
    imageUrl: item.image_url || undefined,
    timestamp: item.created_at ? new Date(item.created_at).getTime() : Date.now(),
  });

  const loadHistory = async (id: string) => {
    try {
      const history = await getChatHistory(id);
      const loadedMessages = history.map(toMessage);
      setMessages(loadedMessages);
      messageIdCounter.current = loadedMessages.length;
    } catch (error) {
      console.error("加载历史消息失败", error);
    }
  };

  useEffect(() => {
    let storedThreadId = localStorage.getItem("personal_chef_thread_id");
    if (!storedThreadId) {
      storedThreadId = generateUUID();
      localStorage.setItem("personal_chef_thread_id", storedThreadId);
    }
    setThreadId(storedThreadId);
    loadHistory(storedThreadId);
  }, []);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const addMessage = (message: Omit<Message, "id" | "timestamp">) => {
    messageIdCounter.current += 1;
    const newMessage: Message = {
      ...message,
      id: `msg_${messageIdCounter.current}_${Date.now()}`,
      timestamp: Date.now(),
    };
    setMessages((current) => [...current, newMessage]);
    return newMessage;
  };

  const handleNewChat = async () => {
    if (threadId) {
      try {
        await clearChatHistory(threadId);
      } catch (error) {
        console.error("清空历史失败", error);
      }
    }

    const newThreadId = generateUUID();
    localStorage.setItem("personal_chef_thread_id", newThreadId);
    setThreadId(newThreadId);
    setMessages([]);
    messageIdCounter.current = 0;
  };

  const handleSend = async (text: string, file?: File) => {
    if (processing) return;

    let activeThreadId = threadId;
    if (!activeThreadId) {
      activeThreadId = generateUUID();
      localStorage.setItem("personal_chef_thread_id", activeThreadId);
      setThreadId(activeThreadId);
    }

    let imageUrl: string | undefined;
    if (file) {
      try {
        imageUrl = await uploadImageToOss(file);
      } catch (error) {
        console.error("图片上传失败", error);
        addMessage({
          role: "assistant",
          content: "图片上传失败。你可以先直接输入食材名称，文字聊天功能仍然可用。",
        });
        return;
      }
    }

    const userText = text || "我上传了一张食材图片，请帮我推荐菜谱";
    addMessage({ role: "user", content: userText, imageUrl });
    setProcessing(true);

    const assistantMessageId = addMessage({
      role: "assistant",
      content: "",
      streaming: true,
    }).id;

    try {
      await streamChat(
        userText,
        (chunk) => {
          setMessages((current) =>
            current.map((message) =>
              message.id === assistantMessageId
                ? { ...message, content: message.content + chunk }
                : message
            )
          );
        },
        imageUrl,
        (error) => {
          setMessages((current) =>
            current.map((message) =>
              message.id === assistantMessageId
                ? {
                    ...message,
                    content: message.content + `\n\n[错误] ${error.message}`,
                    streaming: false,
                  }
                : message
            )
          );
        },
        () => {
          setMessages((current) =>
            current.map((message) =>
              message.id === assistantMessageId ? { ...message, streaming: false } : message
            )
          );
        },
        activeThreadId
      );
    } finally {
      setProcessing(false);
    }
  };

  return (
    <main className="min-h-screen bg-[#f8f5ef] text-stone-900">
      <header className="border-b border-stone-200 bg-white">
        <div className="mx-auto flex max-w-5xl items-center justify-between px-4 py-4">
          <div className="flex items-center gap-3">
            <div className="grid h-11 w-11 place-items-center rounded-lg bg-orange-600 text-white">
              <ChefHat size={24} />
            </div>
            <div>
              <h1 className="text-lg font-semibold">AI 私人厨师</h1>
              <p className="text-sm text-stone-500">根据食材生成家常菜建议</p>
            </div>
          </div>
          <button
            type="button"
            onClick={handleNewChat}
            className="flex items-center gap-2 rounded-lg border border-stone-200 bg-white px-3 py-2 text-sm text-stone-700 hover:bg-stone-50"
          >
            <Plus size={18} />
            新会话
          </button>
        </div>
      </header>

      <section className="mx-auto grid min-h-[calc(100vh-81px)] max-w-5xl grid-rows-[1fr_auto] px-4 py-6">
        <div className="overflow-hidden rounded-lg border border-stone-200 bg-white shadow-sm">
          <div className="flex h-[calc(100vh-185px)] min-h-[420px] flex-col">
            <div className="flex-1 overflow-y-auto p-4">
              {messages.length === 0 ? (
                <div className="flex h-full flex-col items-center justify-center text-center">
                  <div className="mb-4 grid h-16 w-16 place-items-center rounded-full bg-orange-50 text-orange-600">
                    <UtensilsCrossed size={32} />
                  </div>
                  <h2 className="text-xl font-semibold">从食材开始</h2>
                  <p className="mt-2 max-w-md text-sm leading-6 text-stone-500">
                    输入冰箱里的食材，系统会生成适合新手执行的菜谱建议。
                  </p>
                  <div className="mt-5 flex max-w-xl flex-wrap justify-center gap-2">
                    {samplePrompts.map((prompt) => (
                      <button
                        key={prompt}
                        type="button"
                        onClick={() => handleSend(prompt)}
                        className="inline-flex items-center gap-2 rounded-lg border border-stone-200 px-3 py-2 text-left text-sm text-stone-600 hover:border-orange-200 hover:bg-orange-50"
                      >
                        <Sparkles size={15} />
                        {prompt}
                      </button>
                    ))}
                  </div>
                </div>
              ) : (
                <div className="space-y-4">
                  {messages.map((message) => (
                    <ChatMessage key={message.id} message={message} />
                  ))}
                  <div ref={messagesEndRef} />
                </div>
              )}
            </div>
            <ChatInput onSend={handleSend} disabled={processing} />
          </div>
        </div>
      </section>
    </main>
  );
}
