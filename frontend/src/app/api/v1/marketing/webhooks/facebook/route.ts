import { NextRequest } from "next/server";
import {
  headMetaWebhook,
  receiveMetaWebhook,
  verifyMetaWebhook,
} from "../_meta-webhook-proxy";

export const dynamic = "force-dynamic";

export async function GET(request: NextRequest) {
  return verifyMetaWebhook(request, "facebook");
}

export async function HEAD(request: NextRequest) {
  return headMetaWebhook(request, "facebook");
}

export async function POST(request: NextRequest) {
  return receiveMetaWebhook(request, "facebook");
}
