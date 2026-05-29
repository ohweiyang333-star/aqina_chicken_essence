import { redirect } from "next/navigation";

type PageProps = {
  searchParams?: Promise<{
    conversation?: string;
    tab?: string;
  }>;
};

export default async function AdminWhatsAppRedirectPage({ searchParams }: PageProps) {
  const params = await searchParams;
  const query = new URLSearchParams();

  if (params?.conversation) {
    query.set("conversation", params.conversation);
    redirect(`/admin/inbox?${query.toString()}`);
  }

  if (params?.tab === "templates") {
    query.set("tab", "templates");
    redirect(`/admin/inbox?${query.toString()}`);
  }

  query.set("tab", params?.tab === "inbox" ? "conversations" : "campaigns");
  redirect(`/admin/inbox?${query.toString()}`);
}
