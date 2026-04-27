"use client";

import Image from "next/image";
import { useTranslations } from "next-intl";
import { CheckCircle2, Droplet, XCircle } from "lucide-react";
import V2SectionHeading from "./V2SectionHeading";

interface ComparisonItem {
  label: string;
  ordinary: string;
  aqina: string;
}

interface ComparisonBullet {
  text: string;
}

export default function V2ComparisonSection() {
  const t = useTranslations("Index.v2.comparison");
  const items = t.raw("items") as ComparisonItem[];
  const ordinaryBullets = t.raw("ordinaryBullets") as ComparisonBullet[];
  const aqinaBullets = t.raw("aqinaBullets") as ComparisonBullet[];

  return (
    <section
      id="v2-comparison"
      className="relative overflow-hidden bg-[#fff7e8] py-16 md:py-24"
    >
      <div className="absolute inset-x-0 top-0 h-px bg-[#e2c894]" />
      <div className="section-shell space-y-10">
        <V2SectionHeading
          eyebrow={t("eyebrow")}
          title={t("title")}
          body={t("body")}
          align="center"
        />

        <div className="relative rounded-lg border border-[#e2c894] bg-[linear-gradient(110deg,#fffaf1_0%,#fff7e8_44%,#f7e8c9_100%)] px-4 py-6 shadow-[0_24px_70px_rgba(91,57,24,0.12)] md:px-8 md:py-9">
          <div className="mb-6 text-center">
            <p className="text-xs font-bold uppercase tracking-[0.28em] text-[#9b6b1f]">
              {t("visualTitle")}
            </p>
          </div>

          <div className="grid gap-5 lg:grid-cols-[1fr_auto_1fr_0.78fr] lg:items-center">
            <article className="relative overflow-hidden rounded-lg border border-[#c8c1b7] bg-[#f3f0ec] p-4 text-[#4d4740] shadow-[0_14px_32px_rgba(55,46,38,0.08)]">
              <div className="absolute inset-0 bg-[radial-gradient(circle_at_80%_18%,rgba(255,255,255,0.9),transparent_32%)]" />
              <div className="relative grid gap-4 sm:grid-cols-[0.82fr_1fr] sm:items-center">
                <div>
                  <p className="border-b border-[#bdb4a8] pb-2 text-sm font-bold text-[#2f2a25]">
                    {t("ordinaryTitle")}
                  </p>
                  <ul className="mt-4 space-y-3">
                    {ordinaryBullets.map((bullet) => (
                      <li
                        key={bullet.text}
                        className="flex items-start gap-2 text-sm leading-6"
                      >
                        <XCircle
                          size={17}
                          className="mt-1 shrink-0 text-[#7f766d]"
                        />
                        <span>{bullet.text}</span>
                      </li>
                    ))}
                  </ul>
                </div>
                <div className="relative min-h-44 overflow-hidden rounded-md bg-[#ded8cf]">
                  <Image
                    src="/v2/aqina-v2-golden-essence.webp"
                    alt={t("ordinaryImageAlt")}
                    fill
                    sizes="(max-width: 1024px) 88vw, 22vw"
                    className="scale-110 object-cover opacity-70 grayscale"
                  />
                  <div className="absolute inset-0 bg-[#e8e2d8]/45" />
                </div>
              </div>
            </article>

            <div className="relative mx-auto flex h-24 w-24 items-center justify-center lg:h-32 lg:w-28">
              <div className="absolute h-20 w-20 rotate-[-14deg] rounded-[55%_45%_52%_48%] bg-[linear-gradient(135deg,#d58a1f,#f2c15f)] opacity-90 blur-[1px]" />
              <span className="relative -rotate-12 font-heading text-5xl font-bold italic leading-none text-white drop-shadow-[0_8px_14px_rgba(91,57,24,0.28)] lg:text-6xl">
                VS
              </span>
            </div>

            <article className="relative overflow-hidden rounded-lg border border-[#e0b35e] bg-[#fffaf1] p-4 text-[#4d351f] shadow-[0_18px_42px_rgba(155,107,31,0.14)]">
              <div className="absolute inset-0 bg-[radial-gradient(circle_at_78%_32%,rgba(233,195,113,0.32),transparent_34%)]" />
              <div className="relative grid gap-4 sm:grid-cols-[0.86fr_1fr] sm:items-center">
                <div>
                  <p className="border-b border-[#e2c894] pb-2 text-sm font-bold text-[#8d6221]">
                    {t("aqinaTitle")}
                  </p>
                  <ul className="mt-4 space-y-3">
                    {aqinaBullets.map((bullet) => (
                      <li
                        key={bullet.text}
                        className="flex items-start gap-2 text-sm font-semibold leading-6"
                      >
                        <CheckCircle2
                          size={17}
                          className="mt-1 shrink-0 text-[#b98220]"
                        />
                        <span>{bullet.text}</span>
                      </li>
                    ))}
                  </ul>
                </div>
                <div className="relative min-h-44 overflow-hidden rounded-md bg-[#fff2d1]">
                  <Image
                    src="/v2/aqina-v2-golden-essence.webp"
                    alt={t("aqinaImageAlt")}
                    fill
                    sizes="(max-width: 1024px) 88vw, 22vw"
                    className="scale-110 object-cover"
                  />
                </div>
              </div>
            </article>

            <aside className="rounded-lg border border-[#e2c894] bg-white/74 p-5 text-[#4d351f] shadow-[0_14px_34px_rgba(91,57,24,0.08)] backdrop-blur">
              <Droplet size={42} className="mb-4 text-[#b98220]" />
              <h3 className="text-xl font-bold leading-tight text-[#23170d]">
                {t("dailyTitle")}
              </h3>
              <p className="mt-3 text-sm leading-7 text-[#6f5a43]">
                {t("dailyBody")}
              </p>
            </aside>
          </div>
        </div>

        <div className="grid gap-3 md:grid-cols-4">
          {items.map((item) => (
            <article
              key={item.label}
              className="rounded-lg border border-[#ead3a7] bg-white/72 px-4 py-4 shadow-[0_10px_26px_rgba(91,57,24,0.06)]"
            >
              <p className="text-sm font-bold text-[#23170d]">{item.label}</p>
              <p className="mt-2 text-xs leading-6 text-[#6f5a43]">
                {item.aqina}
              </p>
            </article>
          ))}
        </div>
      </div>
    </section>
  );
}
