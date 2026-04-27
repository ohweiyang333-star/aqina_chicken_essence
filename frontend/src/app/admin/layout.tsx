import type { Metadata } from "next";
import { ReactNode } from "react";

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
    <div className="min-h-full font-sans">{children}</div>
  );
}
