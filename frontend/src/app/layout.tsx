import type { Metadata } from "next";
import { ReactNode } from "react";
import "./globals.css";

export const metadata: Metadata = {
  title: "Aqina Premium Chicken Essence Singapore | Pineapple Enzyme Chicken Essence",
  description:
    "Aqina pineapple enzyme chicken essence is made for clean absorption, gentle daily recovery, and easy warm nourishment for Singapore families.",
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
    "premium chicken essence",
    "pineapple enzyme chicken essence",
    "Halal Certified",
    "Free Shipping Singapore",
    "2-3 days delivery",
    "Customer Reviews",
    "鸡精",
    "滴鸡精",
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
