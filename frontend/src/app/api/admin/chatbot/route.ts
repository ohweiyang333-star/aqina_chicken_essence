import { NextRequest, NextResponse } from "next/server";

function getBackendUrl(path: string) {
  const baseUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
  return `${baseUrl.replace(/\/$/, "")}${path}`;
}

async function proxy(request: NextRequest, method: "GET" | "PUT") {
  const authorization = request.headers.get("authorization");
  const response = await fetch(getBackendUrl("/api/v1/chatbot/settings"), {
    method,
    headers: {
      "Content-Type": "application/json",
      ...(authorization ? { Authorization: authorization } : {}),
    },
    body: method === "PUT" ? await request.text() : undefined,
    cache: "no-store",
  });

  const text = await response.text();
  return new NextResponse(text, {
    status: response.status,
    headers: { "Content-Type": response.headers.get("content-type") || "application/json" },
  });
}

export async function GET(request: NextRequest) {
  return proxy(request, "GET");
}

export async function PUT(request: NextRequest) {
  return proxy(request, "PUT");
}
