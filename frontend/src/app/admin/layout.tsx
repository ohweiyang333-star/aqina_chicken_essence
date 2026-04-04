import type { Metadata } from "next";
import { Outfit, Inter } from "next/font/google";
import { ReactNode } from "react";
import "../globals.css";

const outfit = Outfit({
  subsets: ["latin"],
  variable: "--font-outfit",
  display: "swap",
});

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-inter",
  display: "swap",
});

export const metadata: Metadata = {
  title: "Admin Dashboard | Aqina",
  description: "Admin dashboard for Aqina Chicken Essence",
};

export default function AdminLayout({
  children,
}: {
  children: ReactNode;
}) {
  return (
    <html className={`${outfit.variable} ${inter.variable} h-full antialiased`}>
      <body className="min-h-full font-sans">
        {children}
      </body>
    </html>
  );
}
