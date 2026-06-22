import { ApiChatMessage } from "@/types/chat";

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8001";

export async function getOssPresignUrl(
  filename: string
): Promise<{ uploadUrl: string; accessUrl: string; contentType: string }> {
  const response = await fetch(
    `${API_BASE}/api/v1/oss/presign?filename=${encodeURIComponent(filename)}`
  );
  if (!response.ok) {
    throw new Error("获取图片上传地址失败，请先检查 OSS 配置");
  }
  const data = await response.json();
  return {
    uploadUrl: data.uploadUrl.trim().replace(/^["']|["']$/g, ""),
    accessUrl: data.accessUrl.trim().replace(/^["']|["']$/g, ""),
    contentType: data.contentType,
  };
}

export async function uploadImageToOss(file: File): Promise<string> {
  const ext = file.name.split(".").pop() || "jpg";
  const filename = `${Date.now()}.${ext}`;
  const { uploadUrl, accessUrl, contentType } = await getOssPresignUrl(filename);

  const response = await fetch(uploadUrl, {
    method: "PUT",
    body: file,
    headers: { "Content-Type": contentType },
  });

  if (!response.ok) {
    throw new Error(`图片上传失败：${response.status}`);
  }

  return accessUrl;
}

export async function streamChat(
  message: string,
  onChunk: (chunk: string) => void,
  imageUrl?: string,
  onError?: (error: Error) => void,
  onComplete?: () => void,
  threadId?: string
): Promise<void> {
  try {
    const response = await fetch(`${API_BASE}/api/v1/chat/stream`, {
      method: "POST",
      body: JSON.stringify({
        message,
        image_url: imageUrl,
        thread_id: threadId,
      }),
      headers: { "Content-Type": "application/json" },
    });

    if (!response.ok) {
      throw new Error(`请求失败：${response.status}`);
    }

    const reader = response.body?.getReader();
    if (!reader) {
      throw new Error("浏览器无法读取流式响应");
    }

    const decoder = new TextDecoder();
    while (true) {
      const { done, value } = await reader.read();
      if (done) {
        onComplete?.();
        break;
      }
      onChunk(decoder.decode(value, { stream: true }));
    }
  } catch (error) {
    onError?.(error as Error);
  }
}

export async function getChatHistory(threadId: string): Promise<ApiChatMessage[]> {
  const response = await fetch(
    `${API_BASE}/api/v1/chat/messages?thread_id=${encodeURIComponent(threadId)}`
  );
  if (!response.ok) {
    throw new Error("获取历史消息失败");
  }
  const data = await response.json();
  return data.messages;
}

export async function clearChatHistory(threadId: string): Promise<void> {
  const response = await fetch(
    `${API_BASE}/api/v1/chat/messages?thread_id=${encodeURIComponent(threadId)}`,
    { method: "DELETE" }
  );
  if (!response.ok) {
    throw new Error("清空历史消息失败");
  }
}
