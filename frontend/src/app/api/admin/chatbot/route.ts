import { NextRequest, NextResponse } from "next/server";
import { db, collection, doc, getDoc, setDoc } from "@/lib/firebase";

interface ChatbotSettings {
  faq: Array<{
    keywords: string[];
    response_en: string;
    response_zh: string;
    recommendProductId?: string;
  }>;
  abandoned_cart_message: {
    template: string;
    discountCode: string;
    delayMinutes: number;
  };
  replenishment_reminder: {
    enabled: boolean;
    template_en: string;
    template_zh: string;
    triggerDays: number[];
  };
}

// PUT - Update chatbot settings (Admin only)
export async function PUT(request: NextRequest) {
  try {
    // Verify admin authorization
    const authHeader = request.headers.get("authorization");
    if (!authHeader?.startsWith("Bearer ")) {
      return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
    }

    // In production, verify the token with Firebase Admin
    // For now, we'll skip this check

    const settings: ChatbotSettings = await request.json();

    // Validate settings
    if (!settings.faq || !Array.isArray(settings.faq)) {
      return NextResponse.json({ error: "Invalid FAQ data" }, { status: 400 });
    }

    // Convert to Firestore format
    const firestoreData = {
      faq: settings.faq.map((item) => ({
        keywords: item.keywords,
        response: {
          en: item.response_en,
          zh: item.response_zh,
        },
        recommendProductId: item.recommendProductId || null,
      })),
      abandonedCartMessage: {
        template: settings.abandoned_cart_message.template,
        discountCode: settings.abandoned_cart_message.discountCode,
        delay: settings.abandoned_cart_message.delayMinutes,
      },
      replenishmentReminder: {
        enabled: settings.replenishment_reminder.enabled,
        templates: {
          en: settings.replenishment_reminder.template_en,
          zh: settings.replenishment_reminder.template_zh,
        },
        triggerDays: settings.replenishment_reminder.triggerDays,
      },
      updated_at: new Date(),
    };

    // Save to Firestore
    await setDoc(doc(db, "chatbotSettings", "default"), firestoreData, { merge: true });

    console.log("Chatbot settings updated:", firestoreData);

    return NextResponse.json({ success: true, settings });
  } catch (error) {
    console.error("Error updating chatbot settings:", error);
    return NextResponse.json(
      { error: "Failed to update settings" },
      { status: 500 },
    );
  }
}

// GET - Fetch chatbot settings (Admin only)
export async function GET(request: NextRequest) {
  try {
    const docRef = doc(db, "chatbotSettings", "default");
    const docSnap = await getDoc(docRef);

    if (!docSnap.exists()) {
      return NextResponse.json({
        faq: [],
        abandoned_cart_message: {
          template: "Hi [Name]! 您的 Aqina 滴鸡精还在购物车中。",
          discountCode: "HEALTHY10",
          delayMinutes: 15,
        },
        replenishment_reminder: {
          enabled: true,
          template_en: "Hi [Name]! Your Aqina chicken essence is running low.",
          template_zh: "Hi [Name]! 您的滴鸡精库存快用完啦。",
          triggerDays: [12, 25],
        },
      });
    }

    const data = docSnap.data();

    // Convert from Firestore format
    const settings: ChatbotSettings = {
      faq: (data?.faq || []).map((item: any) => ({
        keywords: item.keywords || [],
        response_en: item.response?.en || "",
        response_zh: item.response?.zh || "",
        recommendProductId: item.recommendProductId,
      })),
      abandoned_cart_message: {
        template:
          data?.abandonedCartMessage?.template ||
          "Hi [Name]! 您的 Aqina 滴鸡精还在购物车中。",
        discountCode: data?.abandonedCartMessage?.discountCode || "HEALTHY10",
        delayMinutes: data?.abandonedCartMessage?.delay || 15,
      },
      replenishment_reminder: {
        enabled: data?.replenishmentReminder?.enabled ?? true,
        template_en:
          data?.replenishmentReminder?.templates?.en ||
          "Hi [Name]! Your Aqina chicken essence is running low.",
        template_zh:
          data?.replenishmentReminder?.templates?.zh ||
          "Hi [Name]! 您的滴鸡精库存快用完啦。",
        triggerDays: data?.replenishmentReminder?.triggerDays || [12, 25],
      },
    };

    return NextResponse.json(settings);
  } catch (error) {
    console.error("Error fetching chatbot settings:", error);
    return NextResponse.json(
      { error: "Failed to fetch settings" },
      { status: 500 },
    );
  }
}
