import { NextRequest, NextResponse } from 'next/server';

// Chatbot settings interface
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

// Default settings
const defaultSettings: ChatbotSettings = {
  faq: [
    {
      keywords: ['price', 'pricing', 'how much', '价钱', '价格'],
      response_en: 'Our chicken essence starts from SGD 75 per box. We offer bundle discounts for larger orders!',
      response_zh: '我们的滴鸡精从每盒 SGD 75 起。大订单有折扣优惠！',
    },
    {
      keywords: ['shipping', 'delivery', '运费', '配送'],
      response_en: 'We offer free shipping across Singapore. Delivery typically takes 2-3 business days.',
      response_zh: '我们提供全新加坡免运费服务。通常需要 2-3 个工作日送达。',
    },
    {
      keywords: ['halal', '清真'],
      response_en: 'Yes, all our products are Halal certified by JAKIM Malaysia.',
      response_zh: '是的，我们所有产品都获得马来西亚 JAKIM 清真认证。',
    },
  ],
  abandoned_cart_message: {
    template: 'Hi [Name]! Your Aqina chicken essence order is almost ready. Use code [DISCOUNT_CODE] to enjoy your offer.',
    discountCode: 'HEALTHY10',
    delayMinutes: 15,
  },
  replenishment_reminder: {
    enabled: true,
    template_en: 'Hi [Name]! Your Aqina chicken essence is running low. Stock up now for continued wellness!',
    template_zh: 'Hi [Name]! 您的滴鸡精库存快用完啦。现在订购，持续健康！',
    triggerDays: [12, 25],
  },
};

// GET - Fetch chatbot settings
export async function GET() {
  try {
    // In a real app, fetch from Firestore 'chatbotSettings' collection
    // For now, return default settings
    return NextResponse.json(defaultSettings);
  } catch (error) {
    console.error('Error fetching chatbot settings:', error);
    return NextResponse.json(
      { error: 'Failed to fetch settings' },
      { status: 500 }
    );
  }
}

// PUT - Update chatbot settings
export async function PUT(request: NextRequest) {
  try {
    const settings: ChatbotSettings = await request.json();

    // Validate settings
    if (!settings.faq || !Array.isArray(settings.faq)) {
      return NextResponse.json(
        { error: 'Invalid FAQ data' },
        { status: 400 }
      );
    }

    // In a real app, save to Firestore 'chatbotSettings' collection
    // await admin.firestore().collection('chatbotSettings').doc('default').set(settings);

    console.log('Chatbot settings updated:', settings);

    return NextResponse.json({ success: true, settings });
  } catch (error) {
    console.error('Error updating chatbot settings:', error);
    return NextResponse.json(
      { error: 'Failed to update settings' },
      { status: 500 }
    );
  }
}
