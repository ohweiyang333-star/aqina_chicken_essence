import type { ReactNode } from "react";
import "../globals.css";

export default function PayNowLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en" className="h-full antialiased">
      <body className="min-h-full font-body">{children}</body>
    </html>
  );
}
