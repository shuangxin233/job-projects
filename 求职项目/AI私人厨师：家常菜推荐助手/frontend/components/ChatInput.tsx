import { ChangeEvent, KeyboardEvent, useEffect, useRef, useState } from "react";
import { Image, Send, X } from "lucide-react";

interface ChatInputProps {
  onSend: (text: string, file?: File) => void;
  disabled?: boolean;
}

export function ChatInput({ onSend, disabled }: ChatInputProps) {
  const [text, setText] = useState("");
  const [file, setFile] = useState<File>();
  const [previewUrl, setPreviewUrl] = useState<string>();
  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (!file) {
      setPreviewUrl(undefined);
      return;
    }
    const url = URL.createObjectURL(file);
    setPreviewUrl(url);
    return () => URL.revokeObjectURL(url);
  }, [file]);

  const handleSend = () => {
    if (!text.trim() && !file) return;
    onSend(text.trim(), file);
    setText("");
    setFile(undefined);
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  };

  const handleKeyDown = (event: KeyboardEvent<HTMLTextAreaElement>) => {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      handleSend();
    }
  };

  const handleFileChange = (event: ChangeEvent<HTMLInputElement>) => {
    const selectedFile = event.target.files?.[0];
    if (selectedFile?.type.startsWith("image/")) {
      setFile(selectedFile);
    }
  };

  return (
    <div className="border-t border-stone-200 bg-white p-4">
      {previewUrl && (
        <div className="mb-3 flex items-center gap-2">
          <div className="relative h-20 w-20 overflow-hidden rounded-lg border border-stone-200">
            <img src={previewUrl} alt="食材预览" className="h-full w-full object-cover" />
            <button
              type="button"
              aria-label="移除图片"
              onClick={() => setFile(undefined)}
              className="absolute right-1 top-1 rounded-full bg-stone-900/75 p-1 text-white hover:bg-stone-900"
            >
              <X size={12} />
            </button>
          </div>
          <span className="text-sm text-stone-500">{file?.name}</span>
        </div>
      )}

      <div className="flex items-end gap-2">
        <button
          type="button"
          aria-label="上传食材图片"
          onClick={() => fileInputRef.current?.click()}
          className="grid h-11 w-11 shrink-0 place-items-center rounded-lg border border-stone-200 text-stone-600 hover:bg-stone-50 disabled:cursor-not-allowed disabled:opacity-50"
          disabled={disabled}
        >
          <Image size={20} />
        </button>
        <input
          type="file"
          ref={fileInputRef}
          onChange={handleFileChange}
          accept="image/*"
          className="hidden"
          disabled={disabled}
        />
        <textarea
          value={text}
          onChange={(event) => setText(event.target.value)}
          onKeyDown={handleKeyDown}
          placeholder="输入食材或需求，例如：鸡蛋、番茄、土豆，想做晚饭"
          className="min-h-11 flex-1 resize-none rounded-lg border border-stone-200 bg-stone-50 px-4 py-3 text-sm leading-5 text-stone-900 outline-none transition focus:border-orange-300 focus:bg-white focus:ring-2 focus:ring-orange-100"
          rows={1}
          disabled={disabled}
        />
        <button
          type="button"
          aria-label="发送"
          onClick={handleSend}
          disabled={disabled || (!text.trim() && !file)}
          className="grid h-11 w-11 shrink-0 place-items-center rounded-lg bg-orange-600 text-white shadow-sm transition hover:bg-orange-700 disabled:cursor-not-allowed disabled:bg-stone-300"
        >
          <Send size={20} />
        </button>
      </div>
    </div>
  );
}
