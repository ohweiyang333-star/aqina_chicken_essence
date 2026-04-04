"use client";

import { useTranslations } from "next-intl";
import { useState, useEffect, useRef } from "react";
import { ChevronDown, ChevronUp } from "lucide-react";
import { prepare, layout, type PreparedText } from "@chenglou/pretext";

interface FAQ {
  question: string;
  answer: string;
}

export default function FAQSection() {
  const t = useTranslations("FAQ");

  const [openIndex, setOpenIndex] = useState<number | null>(null);
  const [faqData, setFaqData] = useState<FAQ[]>([]);
  const [preparedAnswers, setPreparedAnswers] = useState<PreparedText[]>([]);
  const [answerHeights, setAnswerHeights] = useState<number[]>([]);
  const containerRef = useRef<HTMLDivElement>(null);

  // 初始化 FAQ 数据
  useEffect(() => {
    const faqs: FAQ[] = [
      {
        question: t("q1.question") || "How to consume for best results?",
        answer:
          t("q1.answer") ||
          "Recommend one pack daily, best taken on an empty stomach in the morning for optimal absorption. Tear open and drink directly, tastes even better when warmed.",
      },
      {
        question: t("q2.question") || "Who is this suitable for?",
        answer:
          t("q2.answer") ||
          "Office workers, night owls, pregnant and postpartum mothers, post-surgery recovery individuals, and students.",
      },
      {
        question: t("q3.question") || "What is the return policy?",
        answer:
          t("q3.answer") ||
          "We support returns within 7 days after signing (limited to quality issues such as off-flavor, leakage, shipping errors, unused condition).",
      },
    ];
    setFaqData(faqs);
  }, [t]);

  // 使用 Pretext 预计算所有答案的高度（一次性，较慢）
  useEffect(() => {
    if (faqData.length === 0) return;

    // 获取容器宽度和字体设置
    const containerWidth = containerRef.current?.offsetWidth || 800;
    const maxWidth = containerWidth - 64; // 减去 padding (px-8 = 32px * 2)
    const font = "16px Inter";
    const lineHeight = 28;

    // 准备所有答案文本
    const prepared = faqData.map((faq) =>
      prepare(faq.answer, font, { whiteSpace: "normal" }),
    );
    setPreparedAnswers(prepared);

    // 计算所有答案的高度
    const heights = prepared.map((p) => layout(p, maxWidth, lineHeight).height);
    setAnswerHeights(heights);
  }, [faqData]);

  const toggleFAQ = (index: number) => {
    setOpenIndex(openIndex === index ? null : index);
  };

  return (
    <section className="w-full py-24 px-6 sm:px-12 bg-white" id="faq">
      <div className="max-w-4xl mx-auto">
        {/* Section Header */}
        <div className="text-center mb-16 space-y-4">
          <span className="text-secondary font-bold tracking-widest text-sm uppercase">
            {t("subtitle") || "Frequently Asked Questions"}
          </span>
          <h2 className="text-4xl md:text-5xl font-bold text-charcoal">
            {t("title") || "Common Questions"}
          </h2>
          <p className="text-charcoal/60 max-w-2xl mx-auto">
            {t("description") ||
              "Quick answers to help you understand Aqina better."}
          </p>
        </div>

        {/* FAQ Accordion */}
        <div ref={containerRef} className="space-y-4">
          {faqData.map((faq, index) => {
            const isOpen = openIndex === index;
            const answerHeight = answerHeights[index] || 0;

            return (
              <div
                key={index}
                className="bg-ivory rounded-2xl border border-charcoal/5 overflow-hidden"
              >
                <button
                  onClick={() => toggleFAQ(index)}
                  className="w-full px-8 py-6 flex items-center justify-between text-left hover:bg-charcoal/5 transition-all"
                >
                  <span className="font-semibold text-charcoal pr-8">
                    {faq.question}
                  </span>
                  <span className="text-primary flex-shrink-0">
                    {isOpen ? (
                      <ChevronUp size={24} />
                    ) : (
                      <ChevronDown size={24} />
                    )}
                  </span>
                </button>

                {/* 使用预计算的高度实现平滑动画 */}
                <div
                  className="px-8 overflow-hidden transition-all duration-300 ease-in-out"
                  style={{
                    height: isOpen ? `${answerHeight}px` : "0px",
                    opacity: isOpen ? 1 : 0,
                  }}
                >
                  <div className="pt-2 pb-6">
                    <p className="text-charcoal/70 leading-relaxed pl-4 border-l-4 border-primary">
                      {faq.answer}
                    </p>
                  </div>
                </div>
              </div>
            );
          })}
        </div>

        {/* Additional Help CTA */}
        <div className="mt-12 text-center">
          <p className="text-charcoal/60 mb-4">
            {t("moreHelp") || "Still have questions? We're here to help!"}
          </p>
          <a
            href="https://wa.me/650000000"
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-2 px-8 py-4 rounded-xl bg-charcoal text-ivory font-bold hover:bg-primary transition-all"
          >
            {t("contactWhatsApp") || "Contact WhatsApp Support"}
          </a>
        </div>
      </div>
    </section>
  );
}
