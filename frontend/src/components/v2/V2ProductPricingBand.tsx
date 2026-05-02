"use client";

import type { ReactNode } from "react";
import { useTranslations } from "next-intl";
import { Reveal } from "./V2Motion";

interface V2ProductPricingBandProps {
  children: ReactNode;
}

export default function V2ProductPricingBand({
  children,
}: V2ProductPricingBandProps) {
  const t = useTranslations("Index.v2.pricingBand");

  return (
    <section
      aria-label={t("ariaLabel")}
      className="bg-[#07170f] text-text-light shadow-[inset_0_1px_0_rgba(255,255,255,0.06)]"
    >
      <Reveal y={28} scale={0.98}>
        {children}
      </Reveal>
    </section>
  );
}
