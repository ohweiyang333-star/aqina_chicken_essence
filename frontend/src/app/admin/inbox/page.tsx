"use client";

import type { ReactNode } from "react";
import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import {
  Inbox,
  Loader2,
  MessageCircle,
  PauseCircle,
  PlayCircle,
  RefreshCw,
  Send,
  Smartphone,
} from "lucide-react";

import AdminSidebar from "@/components/admin/AdminSidebar";
import { isAdminUser, logout, subscribeToAuthChanges } from "@/lib/auth-service";
import {
  MarketingConversationDetail,
  MarketingConversationSummary,
  MarketingInboxFilter,
  MarketingTag,
  getMarketingConversation,
  listMarketingConversations,
  sendMarketingConversationText,
  updateMarketingContactTag,
  updateMarketingConversationAutomation,
} from "@/lib/backend-conversation-service";

const FILTERS: Array<{ value: MarketingInboxFilter; label: string }> = [
  { value: "all", label: "All" },
  { value: "messenger", label: "Messenger" },
  { value: "whatsapp", label: "WhatsApp" },
];

const TAG_OPTIONS: Array<{ value: MarketingTag; label: string }> = [
  { value: "lead_cold", label: "Cold Lead" },
  { value: "qualified_warm", label: "Warm Lead" },
  { value: "cart_hot", label: "Cart Hot" },
  { value: "handoff_pending", label: "Handoff" },
];

export default function AdminInboxPage() {
  const router = useRouter();
  const [isAuthLoading, setIsAuthLoading] = useState(true);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [activeFilter, setActiveFilter] = useState<MarketingInboxFilter>("all");
  const [conversations, setConversations] = useState<MarketingConversationSummary[]>([]);
  const [stats, setStats] = useState({ all: 0, messenger: 0, whatsapp: 0 });
  const [selectedConversationId, setSelectedConversationId] = useState<string | null>(null);
  const [conversationDetail, setConversationDetail] = useState<MarketingConversationDetail | null>(null);
  const [replyText, setReplyText] = useState("");

  useEffect(() => {
    const unsubscribe = subscribeToAuthChanges((user) => {
      void (async () => {
        if (!user) {
          router.push("/admin/login");
          return;
        }

        const isAdmin = await isAdminUser(user);
        if (!isAdmin) {
          await logout();
          router.push("/admin/login");
          return;
        }

        setIsAuthLoading(false);
        void loadData("all");
      })();
    });
    return () => unsubscribe();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [router]);

  async function loadData(channel: MarketingInboxFilter = activeFilter) {
    setIsLoading(true);
    try {
      const rows = await listMarketingConversations(channel);
      const allRows = channel === "all" ? rows : await listMarketingConversations("all");
      setStats({
        all: allRows.length,
        messenger: allRows.filter((item) => item.channel === "messenger").length,
        whatsapp: allRows.filter((item) => item.channel === "whatsapp").length,
      });
      setConversations(rows);
      const requestedConversationId =
        typeof window === "undefined"
          ? null
          : new URLSearchParams(window.location.search).get("conversation");
      const selectedStillVisible = rows.some((item) => item.conversation_id === selectedConversationId);
      const nextConversationId =
        (selectedStillVisible ? selectedConversationId : null) ||
        requestedConversationId ||
        rows[0]?.conversation_id ||
        null;

      setSelectedConversationId(nextConversationId);
      if (nextConversationId) {
        await loadConversation(nextConversationId);
      } else {
        setConversationDetail(null);
      }
    } catch (error) {
      console.error("Failed to load unified inbox", error);
    } finally {
      setIsLoading(false);
    }
  }

  async function loadConversation(conversationId: string) {
    const detail = await getMarketingConversation(conversationId);
    setConversationDetail(detail);
    setSelectedConversationId(conversationId);
  }

  async function handleFilterChange(nextFilter: MarketingInboxFilter) {
    setActiveFilter(nextFilter);
    setSelectedConversationId(null);
    setConversationDetail(null);
    await loadData(nextFilter);
  }

  async function handleSendText() {
    if (!selectedConversationId || !replyText.trim()) return;
    setIsSaving(true);
    try {
      await sendMarketingConversationText(selectedConversationId, replyText.trim());
      setReplyText("");
      await loadConversation(selectedConversationId);
      setConversations(await listMarketingConversations(activeFilter));
    } catch (error) {
      alert(error instanceof Error ? error.message : "发送失败");
    } finally {
      setIsSaving(false);
    }
  }

  async function handleAutomationToggle() {
    if (!conversationDetail) return;
    const paused = !conversationDetail.conversation.automation_paused;
    setIsSaving(true);
    try {
      await updateMarketingConversationAutomation(
        conversationDetail.conversation.conversation_id,
        paused,
        paused ? "admin_unified_inbox" : undefined,
      );
      await loadConversation(conversationDetail.conversation.conversation_id);
      setConversations(await listMarketingConversations(activeFilter));
    } finally {
      setIsSaving(false);
    }
  }

  async function handleTagChange(nextTag: MarketingTag) {
    if (!conversationDetail) return;
    setIsSaving(true);
    try {
      await updateMarketingContactTag(conversationDetail.conversation.contact_id, nextTag);
      await loadConversation(conversationDetail.conversation.conversation_id);
      setConversations(await listMarketingConversations(activeFilter));
    } finally {
      setIsSaving(false);
    }
  }

  async function handleLogout() {
    await logout();
    router.push("/admin/login");
  }

  if (isAuthLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-[#f6f4ee]">
        <Loader2 className="animate-spin text-[#10251d]" size={42} />
      </div>
    );
  }

  return (
    <div className="flex min-h-screen bg-[#f6f4ee] text-[#14231d]">
      <AdminSidebar onLogout={handleLogout} />

      <main className="flex-1 overflow-y-auto p-6 lg:p-8">
        <div className="mx-auto max-w-[1500px] space-y-5">
          <header className="flex flex-col gap-4 border-b border-[#d9d2c4] pb-5 xl:flex-row xl:items-end xl:justify-between">
            <div>
              <div className="mb-2 inline-flex items-center gap-2 rounded-md border border-[#d6d0c5] bg-white px-3 py-2 text-xs font-semibold text-[#79552d]">
                <Inbox size={14} />
                Unified Admin Inbox
              </div>
              <h1 className="text-3xl font-bold text-[#10251d]">Messenger / WhatsApp 对话后台</h1>
              <p className="mt-1 max-w-3xl text-sm text-[#617069]">
                同一个后台查看广告进来的 Messenger 与 WhatsApp 对话、lead tag、来源和人工接管状态。
              </p>
            </div>

            <div className="flex flex-wrap gap-2">
              <MetricPill label="All" value={stats.all} />
              <MetricPill label="Messenger" value={stats.messenger} />
              <MetricPill label="WhatsApp" value={stats.whatsapp} />
              <button
                id="inbox-refresh-button"
                onClick={() => void loadData(activeFilter)}
                className="inline-flex items-center gap-2 rounded-md border border-[#cfd8d2] bg-white px-4 py-2 text-sm font-semibold text-[#294239] hover:border-[#236b50]"
              >
                <RefreshCw size={16} />
                刷新
              </button>
            </div>
          </header>

          <div className="flex flex-wrap gap-2">
            {FILTERS.map((filter) => (
              <button
                key={filter.value}
                id={`inbox-filter-${filter.value}`}
                onClick={() => void handleFilterChange(filter.value)}
                className={`rounded-md px-4 py-2 text-sm font-semibold ${
                  activeFilter === filter.value
                    ? "bg-[#10251d] text-white"
                    : "border border-[#d7d0c5] bg-white text-[#5d6a64] hover:text-[#10251d]"
                }`}
              >
                {filter.label}
              </button>
            ))}
          </div>

          {isLoading ? (
            <div className="flex h-80 items-center justify-center rounded-md border border-[#ded8ce] bg-white">
              <Loader2 className="animate-spin text-[#236b50]" size={32} />
            </div>
          ) : (
            <InboxPanel
              conversations={conversations}
              conversationDetail={conversationDetail}
              selectedConversationId={selectedConversationId}
              replyText={replyText}
              isSaving={isSaving}
              onSelectConversation={(id) => void loadConversation(id)}
              onReplyTextChange={setReplyText}
              onSendText={() => void handleSendText()}
              onAutomationToggle={() => void handleAutomationToggle()}
              onTagChange={(tag) => void handleTagChange(tag)}
            />
          )}
        </div>
      </main>
    </div>
  );
}

function InboxPanel({
  conversations,
  conversationDetail,
  selectedConversationId,
  replyText,
  isSaving,
  onSelectConversation,
  onReplyTextChange,
  onSendText,
  onAutomationToggle,
  onTagChange,
}: {
  conversations: MarketingConversationSummary[];
  conversationDetail: MarketingConversationDetail | null;
  selectedConversationId: string | null;
  replyText: string;
  isSaving: boolean;
  onSelectConversation: (id: string) => void;
  onReplyTextChange: (value: string) => void;
  onSendText: () => void;
  onAutomationToggle: () => void;
  onTagChange: (tag: MarketingTag) => void;
}) {
  const windowOpen = conversationDetail?.window.is_open;
  return (
    <section className="grid min-h-[720px] gap-4 xl:grid-cols-[330px_minmax(0,1fr)_340px]">
      <div className="overflow-hidden rounded-md border border-[#ddd5ca] bg-white">
        <div className="border-b border-[#ebe5dc] p-4">
          <h2 className="text-base font-bold">对话列表</h2>
          <p className="text-xs text-[#6b746f]">{conversations.length} 个 thread</p>
        </div>
        <div className="max-h-[660px] overflow-y-auto">
          {conversations.length === 0 ? (
            <p className="p-4 text-sm text-[#6b746f]">暂无对话。</p>
          ) : (
            conversations.map((item) => (
              <button
                key={item.conversation_id}
                id={`inbox-conversation-${item.conversation_id}`}
                onClick={() => onSelectConversation(item.conversation_id)}
                className={`block w-full border-b border-[#f0ebe4] p-4 text-left hover:bg-[#f7faf8] ${
                  selectedConversationId === item.conversation_id ? "bg-[#edf7f2]" : ""
                }`}
              >
                <div className="flex items-start justify-between gap-3">
                  <div className="min-w-0">
                    <div className="flex items-center gap-2">
                      <ChannelIcon channel={item.channel} />
                      <p className="truncate text-sm font-bold text-[#14231d]">
                        {item.customer_name || maskPlatformId(item.platform_id)}
                      </p>
                    </div>
                    <p className="mt-1 truncate text-xs text-[#69746e]">
                      {item.latest_message?.text || "No messages yet"}
                    </p>
                  </div>
                  <WindowBadge isOpen={item.window.is_open} />
                </div>
                <div className="mt-3 flex flex-wrap gap-2 text-[11px] text-[#6b746f]">
                  <span className="rounded bg-[#f2eee7] px-2 py-1">{channelLabel(item.channel)}</span>
                  <span className="rounded bg-[#f2eee7] px-2 py-1">{item.current_tag || "untagged"}</span>
                  <span className="rounded bg-[#f2eee7] px-2 py-1">{item.acquisition.source}</span>
                </div>
              </button>
            ))
          )}
        </div>
      </div>

      <div className="flex min-h-[720px] flex-col rounded-md border border-[#ddd5ca] bg-white">
        <div className="flex items-start justify-between gap-4 border-b border-[#ebe5dc] p-4">
          <div>
            <h2 className="text-lg font-bold">
              {conversationDetail?.conversation.customer_name || "选择一个对话"}
            </h2>
            {conversationDetail && (
              <p className="mt-1 text-xs text-[#6b746f]">
                {channelLabel(conversationDetail.conversation.channel)} · {maskPlatformId(conversationDetail.conversation.platform_id)}
              </p>
            )}
          </div>
          {conversationDetail && <WindowBadge isOpen={conversationDetail.window.is_open} />}
        </div>

        <div className="flex-1 space-y-3 overflow-y-auto bg-[#faf8f3] p-4">
          {conversationDetail?.messages.map((message) => (
            <div
              key={message.message_id}
              className={`flex ${message.direction === "outbound" ? "justify-end" : "justify-start"}`}
            >
              <div
                className={`max-w-[74%] rounded-md px-4 py-3 text-sm leading-6 ${
                  message.direction === "outbound"
                    ? "bg-[#123d2f] text-white"
                    : "border border-[#e0d8cd] bg-white text-[#14231d]"
                }`}
              >
                <p className="whitespace-pre-wrap break-words">{message.text}</p>
                <div className="mt-2 flex flex-wrap gap-2 text-[11px] opacity-70">
                  <span>{formatTime(message.created_at)}</span>
                  {message.role && <span>{message.role}</span>}
                  {message.delivery_status && <span>{message.delivery_status}</span>}
                  {message.message_type && <span>{message.message_type}</span>}
                </div>
                {message.error_message && <p className="mt-2 text-xs text-[#ffb4a8]">{message.error_message}</p>}
              </div>
            </div>
          ))}
        </div>

        <div className="border-t border-[#ebe5dc] p-4">
          <div className="grid gap-3 lg:grid-cols-[1fr_auto]">
            <textarea
              id="inbox-reply-textarea"
              value={replyText}
              onChange={(event) => onReplyTextChange(event.target.value)}
              rows={3}
              disabled={!conversationDetail || !windowOpen}
              className="min-h-24 resize-none rounded-md border border-[#d8d1c7] bg-white p-3 text-sm text-[#14231d] outline-none focus:border-[#236b50] disabled:bg-[#f2eee7]"
              placeholder={windowOpen ? "输入人工回复..." : "窗口已关闭，无法自由回复"}
            />
            <button
              id="inbox-send-text-button"
              onClick={onSendText}
              disabled={isSaving || !conversationDetail || !windowOpen || !replyText.trim()}
              className="inline-flex h-12 items-center justify-center gap-2 rounded-md bg-[#123d2f] px-5 text-sm font-bold text-white disabled:cursor-not-allowed disabled:opacity-50"
            >
              {isSaving ? <Loader2 className="animate-spin" size={16} /> : <Send size={16} />}
              发送
            </button>
          </div>
        </div>
      </div>

      <aside className="space-y-4">
        <Panel title="顾客与分类">
          {conversationDetail ? (
            <div className="space-y-4 text-sm">
              <InfoRow label="Channel" value={channelLabel(conversationDetail.conversation.channel)} />
              <InfoRow label="Platform ID" value={maskPlatformId(conversationDetail.conversation.platform_id)} />
              <InfoRow label="Marketing" value={conversationDetail.conversation.marketing_status || "-"} />
              <InfoRow label="窗口" value={conversationDetail.window.is_open ? "可自由回复" : "已关闭"} />
              <label className="grid gap-1 text-xs font-semibold text-[#6b746f]">
                Lead Tag
                <select
                  id="inbox-tag-select"
                  value={conversationDetail.conversation.current_tag || "lead_cold"}
                  onChange={(event) => onTagChange(event.target.value as MarketingTag)}
                  disabled={isSaving}
                  className="rounded-md border border-[#d8d1c7] bg-white px-3 py-2 text-sm font-bold text-[#14231d]"
                >
                  {TAG_OPTIONS.map((tag) => (
                    <option key={tag.value} value={tag.value}>
                      {tag.label}
                    </option>
                  ))}
                </select>
              </label>
              <button
                id="inbox-automation-toggle-button"
                onClick={onAutomationToggle}
                disabled={isSaving}
                className="inline-flex w-full items-center justify-center gap-2 rounded-md bg-[#10251d] px-4 py-3 text-sm font-bold text-white disabled:opacity-50"
              >
                {conversationDetail.conversation.automation_paused ? <PlayCircle size={16} /> : <PauseCircle size={16} />}
                {conversationDetail.conversation.automation_paused ? "恢复 Bot" : "暂停 Bot"}
              </button>
            </div>
          ) : (
            <p className="text-sm text-[#6b746f]">请选择一个对话。</p>
          )}
        </Panel>

        <Panel title="来源">
          {conversationDetail ? (
            <div className="space-y-2 text-sm">
              <InfoRow label="Source" value={conversationDetail.conversation.acquisition.source || "unknown/direct"} />
              <InfoRow label="Ref" value={conversationDetail.conversation.acquisition.ref || "-"} />
              <InfoRow label="Ad ID" value={conversationDetail.conversation.acquisition.ad_id || "-"} />
              <InfoRow label="Post ID" value={conversationDetail.conversation.acquisition.post_id || "-"} />
            </div>
          ) : (
            <p className="text-sm text-[#6b746f]">暂无来源资料。</p>
          )}
        </Panel>

        <Panel title="关联订单">
          <div className="space-y-3">
            {conversationDetail?.orders.length ? (
              conversationDetail.orders.map((order) => (
                <div key={order.order_id} className="rounded-md border border-[#e5ddd1] bg-[#faf8f3] p-3 text-sm">
                  <div className="flex items-center justify-between gap-3">
                    <span className="font-semibold">#{order.order_id.slice(-8)}</span>
                    <span className="text-xs text-[#6b746f]">{order.order_status || "pending"}</span>
                  </div>
                  <p className="mt-1 text-xs text-[#6b746f]">
                    {order.payment_status || "payment pending"} · SGD {Number(order.total_amount || 0).toFixed(2)}
                  </p>
                </div>
              ))
            ) : (
              <p className="text-sm text-[#6b746f]">暂无关联订单。</p>
            )}
          </div>
        </Panel>
      </aside>
    </section>
  );
}

function MetricPill({ label, value }: { label: string; value: number }) {
  return (
    <div className="inline-flex items-center gap-2 rounded-md border border-[#d7d0c5] bg-white px-4 py-2 text-sm font-semibold text-[#294239]">
      <span className="text-[#6b746f]">{label}</span>
      <span>{value}</span>
    </div>
  );
}

function Panel({ title, children }: { title: string; children: ReactNode }) {
  return (
    <div className="rounded-md border border-[#ddd5ca] bg-white p-4">
      <h2 className="mb-4 text-base font-bold text-[#10251d]">{title}</h2>
      {children}
    </div>
  );
}

function InfoRow({ label, value }: { label: string; value: ReactNode }) {
  return (
    <div className="flex items-start justify-between gap-4 border-b border-[#eee8df] py-2">
      <span className="text-xs font-semibold text-[#6b746f]">{label}</span>
      <span className="break-words text-right text-sm font-bold text-[#14231d]">{value}</span>
    </div>
  );
}

function WindowBadge({ isOpen }: { isOpen: boolean }) {
  return (
    <span
      className={`inline-flex items-center gap-1 rounded-md px-2 py-1 text-[11px] font-bold ${
        isOpen ? "bg-[#ecf8f1] text-[#236b50]" : "bg-[#fff0e8] text-[#9a5a22]"
      }`}
    >
      {isOpen ? "Open" : "Closed"}
    </span>
  );
}

function ChannelIcon({ channel }: { channel: MarketingConversationSummary["channel"] }) {
  if (channel === "messenger") return <MessageCircle size={14} className="shrink-0 text-[#2c65c8]" />;
  return <Smartphone size={14} className="shrink-0 text-[#236b50]" />;
}

function channelLabel(channel: MarketingConversationSummary["channel"]) {
  return channel === "messenger" ? "Messenger" : "WhatsApp";
}

function maskPlatformId(value: string) {
  if (!value) return "Unknown contact";
  if (value.length <= 8) return value;
  return `${value.slice(0, 4)}...${value.slice(-4)}`;
}

function formatTime(value?: string) {
  if (!value) return "-";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleString("en-SG", {
    month: "short",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  });
}
