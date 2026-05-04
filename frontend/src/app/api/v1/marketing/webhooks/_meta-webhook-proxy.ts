import { NextRequest, NextResponse } from "next/server";

type MetaWebhookChannel = "facebook" | "whatsapp";

function getBackendWebhookUrl(request: NextRequest, channel: MetaWebhookChannel) {
  const frontendUrl = new URL(request.url);
  const baseUrl = (process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000").replace(/\/$/, "");
  const backendUrl = new URL(`/api/v1/marketing/webhooks/${channel}`, baseUrl);
  backendUrl.search = frontendUrl.search;
  return backendUrl;
}

async function toNextResponse(response: Response) {
  const headers = new Headers();
  const contentType = response.headers.get("content-type");
  if (contentType) {
    headers.set("content-type", contentType);
  }

  return new NextResponse(await response.text(), {
    status: response.status,
    headers,
  });
}

export async function verifyMetaWebhook(request: NextRequest, channel: MetaWebhookChannel) {
  const response = await fetch(getBackendWebhookUrl(request, channel), {
    method: "GET",
    cache: "no-store",
  });

  return toNextResponse(response);
}

export async function headMetaWebhook(request: NextRequest, channel: MetaWebhookChannel) {
  const response = await fetch(getBackendWebhookUrl(request, channel), {
    method: "HEAD",
    cache: "no-store",
  });

  return new NextResponse(null, {
    status: response.status,
  });
}

export async function receiveMetaWebhook(request: NextRequest, channel: MetaWebhookChannel) {
  const headers = new Headers();
  const contentType = request.headers.get("content-type");
  const signature = request.headers.get("x-hub-signature");
  const signature256 = request.headers.get("x-hub-signature-256");

  if (contentType) {
    headers.set("content-type", contentType);
  }
  if (signature) {
    headers.set("x-hub-signature", signature);
  }
  if (signature256) {
    headers.set("x-hub-signature-256", signature256);
  }

  const response = await fetch(getBackendWebhookUrl(request, channel), {
    method: "POST",
    headers,
    body: await request.text(),
    cache: "no-store",
  });

  return toNextResponse(response);
}
