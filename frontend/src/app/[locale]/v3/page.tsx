import { redirect } from "next/navigation";

type LegacyV3PageProps = {
  params: Promise<{ locale: string }>;
};

export default async function LegacyV3RedirectPage({
  params,
}: LegacyV3PageProps) {
  const { locale } = await params;
  redirect(locale === "zh" ? "/v3/zh" : "/v3/en");
}
