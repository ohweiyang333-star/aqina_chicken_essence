import type { Metadata } from "next";
import { ReactNode } from "react";
import "./globals.css";

export const metadata: Metadata = {
  title: "Aqina 滴鸡精｜零负担吸收的纯粹能量｜黄梨酵素滴鸡精",
  description:
    "给身体最纯粹的能量，从零负担吸收开始。Aqina 黄梨酵素滴鸡精，聚焦好吸收、轻负担与每日可持续的温热补养。",
  icons: {
    icon: [
      { url: "/icon.png", type: "image/png", sizes: "512x512" },
      { url: "/favicon.ico", type: "image/x-icon" },
    ],
    shortcut: ["/favicon.ico"],
    apple: ["/apple-icon.png"],
  },
  keywords: [
    "Aqina Singapore",
    "鸡精",
    "滴鸡精",
    "Halal Certified",
    "Free Shipping Singapore",
    "2-3 days delivery",
    "Customer Reviews",
  ],
};

export default function RootLayout({
  children,
}: {
  children: ReactNode;
}) {
  return (
    <html className="h-full antialiased">
      <body className="min-h-full font-sans">{children}</body>
    </html>
  );
}
