import type { Metadata } from "next";
import { ReactNode } from "react";
import { Fraunces, Plus_Jakarta_Sans } from "next/font/google";
import MarketingAnalytics from "@/components/MarketingAnalytics";
import "./globals.css";

// Latin display + figures. Fraunces carries warmth and optical sizing, which suits a food
// brand and gives the price numerals real character — they are the hero content on this page.
// Chinese text deliberately falls through to the platform's own face (PingFang / Yahei):
// self-hosting a CJK webfont would cost megabytes for a worse result than the native one.
const display = Fraunces({
  subsets: ["latin"],
  variable: "--font-display",
  display: "swap",
});

const bodyFont = Plus_Jakarta_Sans({
  subsets: ["latin"],
  variable: "--font-body-latin",
  display: "swap",
});

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
    "纯鸡精",
  ],
};

export default function RootLayout({
  children,
}: {
  children: ReactNode;
}) {
  return (
    <html
      className={`h-full antialiased ${display.variable} ${bodyFont.variable}`}
      data-scroll-behavior="smooth"
    >
      <body className="min-h-full font-sans">
        {children}
        <MarketingAnalytics />
      </body>
    </html>
  );
}
