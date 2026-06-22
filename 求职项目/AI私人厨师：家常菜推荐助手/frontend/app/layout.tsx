import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "AI 私人厨师",
  description: "根据家庭食材生成家常菜建议的 AI 应用",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="zh-CN">
      <body>{children}</body>
    </html>
  );
}
