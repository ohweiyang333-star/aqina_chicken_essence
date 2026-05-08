"use client";

import { useTranslations } from "next-intl";
import { BadgeCheck, ShieldCheck, Truck } from "lucide-react";
import { MotionItem, StaggerGroup } from "./V2Motion";

const icons = [ShieldCheck, BadgeCheck, Truck] as const;

export default function V2QuickTrustStrip() {
  const t = useTranslations("Index.v2.quickTrust");
  const items = t.raw("items") as Array<{
    title: string;
    body: string;
  }>;

  return (
    <section id="v2-quick-trust" className="bg-[#f8ecd5] py-8 text-[#23170d]">
      <div className="section-shell">
        <StaggerGroup className="grid gap-3 md:grid-cols-3" staggerChildren={0.08}>
          {items.map((item, index) => {
            const Icon = icons[index % icons.length];

            return (
              <MotionItem
                as="article"
                key={item.title}
                className="rounded-lg border border-[#dcc08c] bg-white/78 px-5 py-5 shadow-[0_12px_30px_rgba(91,57,24,0.07)]"
                y={16}
              >
                <div className="flex items-center gap-3">
                  <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-[#f2dba8] text-[#7c531c]">
                    <Icon size={19} />
                  </span>
                  <div>
                    <h2 className="text-sm font-bold text-[#23170d]">{item.title}</h2>
                    <p className="mt-1 text-sm leading-6 text-[#6f5a43]">{item.body}</p>
                  </div>
                </div>
              </MotionItem>
            );
          })}
        </StaggerGroup>
      </div>
    </section>
  );
}
