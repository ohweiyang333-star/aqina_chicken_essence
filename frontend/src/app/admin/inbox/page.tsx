"use client";

import type { ReactNode } from "react";
import { useState, useEffect, useMemo } from "react";
import Image from "next/image";
import { useRouter } from "next/navigation";
import {
  AlertTriangle,
  CheckCircle2,
  Clock,
  ImageIcon,
  Loader2,
  MessageCircle,
  PauseCircle,
  PlayCircle,
  RefreshCw,
  Save,
  Send,
  ShieldCheck,
  Smartphone,
  Users,
  X,
  XCircle,
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
  sendMarketingConversationImage,
  sendMarketingConversationText,
  updateMarketingContactTag,
  updateMarketingConversationAutomation,
} from "@/lib/backend-conversation-service";
import {
  WhatsAppCampaign,
  WhatsAppCampaignDetail,
  WhatsAppCampaignPreview,
  WhatsAppHealth,
  WhatsAppTemplate,
  cancelWhatsAppCampaign,
  createWhatsAppCampaign,
  getWhatsAppCampaign,
  getWhatsAppHealth,
  launchWhatsAppCampaign,
  listWhatsAppCampaigns,
  listWhatsAppTemplates,
  pauseWhatsAppCampaign,
  previewWhatsAppCampaign,
  saveWhatsAppTemplate,
  sendWhatsAppTemplate,
  syncWhatsAppTemplates,
} from "@/lib/backend-whatsapp-service";

type AdminInboxTab = "conversations" | "campaigns" | "templates";

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

const ALLOWED_REPLY_IMAGE_TYPES = new Set(["image/jpeg", "image/png", "image/webp"]);
const MAX_REPLY_IMAGE_BYTES = 8 * 1024 * 1024;
const emptyCampaign = {
  name: "",
  template_name: "",
  language_code: "en_US",
  body_variables: [] as string[],
  audience_tags: [] as string[],
};

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
  const [selectedImageFile, setSelectedImageFile] = useState<File | null>(null);
  const [selectedImagePreview, setSelectedImagePreview] = useState<string | null>(null);
  const [templateName, setTemplateName] = useState("");
  const [templateVariables, setTemplateVariables] = useState("");
  const [activeTab, setActiveTab] = useState<AdminInboxTab>("conversations");
  const [whatsappHealth, setWhatsAppHealth] = useState<WhatsAppHealth | null>(null);
  const [templates, setTemplates] = useState<WhatsAppTemplate[]>([]);
  const [campaigns, setCampaigns] = useState<WhatsAppCampaign[]>([]);
  const [campaignDetail, setCampaignDetail] = useState<WhatsAppCampaignDetail | null>(null);
  const [campaignForm, setCampaignForm] = useState(emptyCampaign);
  const [campaignPreview, setCampaignPreview] = useState<WhatsAppCampaignPreview | null>(null);
  const [localTemplate, setLocalTemplate] = useState({
    name: "",
    language_code: "en_US",
    category: "MARKETING",
    status: "APPROVED",
  });

  const approvedTemplates = useMemo(
    () => templates.filter((item) => item.status.toUpperCase() === "APPROVED"),
    [templates],
  );

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
        const params = typeof window === "undefined" ? null : new URLSearchParams(window.location.search);
        const requestedTab = params?.get("tab");
        if (requestedTab === "conversations" || requestedTab === "campaigns" || requestedTab === "templates") {
          setActiveTab(requestedTab);
        }
        void loadData("all");
      })();
    });
    return () => unsubscribe();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [router]);

  useEffect(() => {
    return () => {
      if (selectedImagePreview) {
        URL.revokeObjectURL(selectedImagePreview);
      }
    };
  }, [selectedImagePreview]);

  async function loadData(channel: MarketingInboxFilter = activeFilter) {
    setIsLoading(true);
    try {
      const rows = await listMarketingConversations(channel);
      const [allRows, whatsappTools] = await Promise.all([
        channel === "all" ? Promise.resolve(rows) : listMarketingConversations("all"),
        loadWhatsAppTools(),
      ]);
      setStats({
        all: allRows.length,
        messenger: allRows.filter((item) => item.channel === "messenger").length,
        whatsapp: allRows.filter((item) => item.channel === "whatsapp").length,
      });
      setWhatsAppHealth(whatsappTools.health);
      setTemplates(whatsappTools.templates);
      setCampaigns(whatsappTools.campaigns);
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

  async function loadWhatsAppTools() {
    const [health, templateRows, campaignRows] = await Promise.all([
      getWhatsAppHealth(),
      listWhatsAppTemplates(),
      listWhatsAppCampaigns(),
    ]);
    if (!campaignForm.template_name && templateRows[0]) {
      setCampaignForm((current) => ({
        ...current,
        template_name: templateRows[0].name,
        language_code: templateRows[0].language_code,
      }));
    }
    if (!templateName && templateRows[0]) {
      setTemplateName(templateRows[0].name);
    }
    return { health, templates: templateRows, campaigns: campaignRows };
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
    setReplyText("");
    handleClearImage();
    await loadData(nextFilter);
  }

  function handleSelectConversation(conversationId: string) {
    setReplyText("");
    setTemplateVariables("");
    handleClearImage();
    void loadConversation(conversationId);
  }

  function handleSelectImage(file: File) {
    if (!ALLOWED_REPLY_IMAGE_TYPES.has(file.type)) {
      alert("请上传 JPG、PNG 或 WebP 图片。");
      return;
    }
    if (file.size > MAX_REPLY_IMAGE_BYTES) {
      alert("图片不能超过 8MB。");
      return;
    }
    setSelectedImageFile(file);
    const nextPreview = URL.createObjectURL(file);
    setSelectedImagePreview((current) => {
      if (current) {
        URL.revokeObjectURL(current);
      }
      return nextPreview;
    });
  }

  function handleClearImage() {
    setSelectedImageFile(null);
    setSelectedImagePreview((current) => {
      if (current) {
        URL.revokeObjectURL(current);
      }
      return null;
    });
  }

  async function handleSendReply() {
    if (!selectedConversationId || (!replyText.trim() && !selectedImageFile)) return;
    setIsSaving(true);
    try {
      if (selectedImageFile) {
        await sendMarketingConversationImage(selectedConversationId, selectedImageFile, replyText.trim());
      } else {
        await sendMarketingConversationText(selectedConversationId, replyText.trim());
      }
      setReplyText("");
      handleClearImage();
      await loadConversation(selectedConversationId);
      setConversations(await listMarketingConversations(activeFilter));
    } catch (error) {
      alert(error instanceof Error ? error.message : "发送失败");
    } finally {
      setIsSaving(false);
    }
  }

  async function handleSendTemplate() {
    if (!selectedConversationId || !templateName) return;
    const selected = templates.find((item) => item.name === templateName);
    setIsSaving(true);
    try {
      await sendWhatsAppTemplate(
        selectedConversationId,
        templateName,
        selected?.language_code || "en_US",
        splitLines(templateVariables),
      );
      setTemplateVariables("");
      await loadConversation(selectedConversationId);
      setConversations(await listMarketingConversations(activeFilter));
    } catch (error) {
      alert(error instanceof Error ? error.message : "模板发送失败");
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

  async function handleSyncTemplates() {
    setIsSaving(true);
    try {
      await syncWhatsAppTemplates();
      setTemplates(await listWhatsAppTemplates());
    } catch (error) {
      alert(error instanceof Error ? error.message : "Template sync failed");
    } finally {
      setIsSaving(false);
    }
  }

  async function handleSaveLocalTemplate() {
    if (!localTemplate.name.trim()) return;
    setIsSaving(true);
    try {
      await saveWhatsAppTemplate({
        ...localTemplate,
        name: localTemplate.name.trim(),
        components: [],
      });
      setLocalTemplate({ name: "", language_code: "en_US", category: "MARKETING", status: "APPROVED" });
      setTemplates(await listWhatsAppTemplates());
    } finally {
      setIsSaving(false);
    }
  }

  async function handlePreviewCampaign() {
    setIsSaving(true);
    try {
      const preview = await previewWhatsAppCampaign(campaignForm);
      setCampaignPreview(preview);
    } catch (error) {
      alert(error instanceof Error ? error.message : "Campaign preview failed");
    } finally {
      setIsSaving(false);
    }
  }

  async function handleCreateCampaign() {
    setIsSaving(true);
    try {
      const created = await createWhatsAppCampaign(campaignForm);
      setCampaignPreview(created.preview);
      setCampaigns(await listWhatsAppCampaigns());
      setCampaignDetail(await getWhatsAppCampaign(created.campaign_id));
    } catch (error) {
      alert(error instanceof Error ? error.message : "Campaign create failed");
    } finally {
      setIsSaving(false);
    }
  }

  async function handleCampaignAction(campaignId: string, action: "launch" | "pause" | "cancel") {
    setIsSaving(true);
    try {
      if (action === "launch") await launchWhatsAppCampaign(campaignId);
      if (action === "pause") await pauseWhatsAppCampaign(campaignId);
      if (action === "cancel") await cancelWhatsAppCampaign(campaignId);
      setCampaigns(await listWhatsAppCampaigns());
      setCampaignDetail(await getWhatsAppCampaign(campaignId));
    } catch (error) {
      alert(error instanceof Error ? error.message : "Campaign action failed");
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
    <div className="flex h-screen overflow-hidden bg-[#f6f4ee] text-[#14231d]">
      <AdminSidebar onLogout={handleLogout} />

      <main className="flex min-w-0 flex-1 flex-col overflow-hidden p-6 lg:p-8">
        <div className="mx-auto flex h-full w-full max-w-[1500px] flex-col overflow-hidden">
          <header className="flex shrink-0 flex-col gap-4 border-b border-[#d9d2c4] pb-5 xl:flex-row xl:items-end xl:justify-between">
            <div>
              <h1 className="text-3xl font-bold text-[#10251d]">Messenger / WhatsApp 对话后台</h1>
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
              <HealthPill health={whatsappHealth} />
            </div>
          </header>

          <div className="flex shrink-0 flex-wrap gap-2 pt-5">
            {([
              ["conversations", "Conversations"],
              ["campaigns", "Campaigns (WhatsApp)"],
              ["templates", "Templates (WhatsApp)"],
            ] as Array<[AdminInboxTab, string]>).map(([tab, label]) => (
              <button
                key={tab}
                id={`inbox-tab-${tab}`}
                onClick={() => setActiveTab(tab)}
                className={`rounded-md px-4 py-2 text-sm font-semibold ${
                  activeTab === tab
                    ? "bg-[#10251d] text-white"
                    : "border border-[#d7d0c5] bg-white text-[#5d6a64] hover:text-[#10251d]"
                }`}
              >
                {label}
              </button>
            ))}
          </div>

          {isLoading ? (
            <div className="mt-5 flex min-h-0 flex-1 items-center justify-center rounded-md border border-[#ded8ce] bg-white">
              <Loader2 className="animate-spin text-[#236b50]" size={32} />
            </div>
          ) : (
            <div className="min-h-0 flex-1 pt-5">
              {activeTab === "conversations" && (
                <div className="flex h-full min-h-0 flex-col gap-4">
                  <div className="flex shrink-0 flex-wrap gap-2">
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
                  <InboxPanel
                    conversations={conversations}
                    conversationDetail={conversationDetail}
                    selectedConversationId={selectedConversationId}
                    replyText={replyText}
                    selectedImageFile={selectedImageFile}
                    selectedImagePreview={selectedImagePreview}
                    templates={approvedTemplates}
                    templateName={templateName}
                    templateVariables={templateVariables}
                    isSaving={isSaving}
                    onSelectConversation={handleSelectConversation}
                    onReplyTextChange={setReplyText}
                    onSelectImage={handleSelectImage}
                    onClearImage={handleClearImage}
                    onSendReply={() => void handleSendReply()}
                    onTemplateNameChange={setTemplateName}
                    onTemplateVariablesChange={setTemplateVariables}
                    onSendTemplate={() => void handleSendTemplate()}
                    onAutomationToggle={() => void handleAutomationToggle()}
                    onTagChange={(tag) => void handleTagChange(tag)}
                  />
                </div>
              )}

              {activeTab === "campaigns" && (
                <CampaignPanel
                  templates={approvedTemplates}
                  campaigns={campaigns}
                  campaignDetail={campaignDetail}
                  campaignForm={campaignForm}
                  campaignPreview={campaignPreview}
                  isSaving={isSaving}
                  onFormChange={setCampaignForm}
                  onPreview={() => void handlePreviewCampaign()}
                  onCreate={() => void handleCreateCampaign()}
                  onSelectCampaign={(id) => void getWhatsAppCampaign(id).then(setCampaignDetail)}
                  onAction={(id, action) => void handleCampaignAction(id, action)}
                />
              )}

              {activeTab === "templates" && (
                <TemplatePanel
                  templates={templates}
                  localTemplate={localTemplate}
                  isSaving={isSaving}
                  onLocalTemplateChange={setLocalTemplate}
                  onSync={() => void handleSyncTemplates()}
                  onSave={() => void handleSaveLocalTemplate()}
                />
              )}
            </div>
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
  selectedImageFile,
  selectedImagePreview,
  templates,
  templateName,
  templateVariables,
  isSaving,
  onSelectConversation,
  onReplyTextChange,
  onSelectImage,
  onClearImage,
  onSendReply,
  onTemplateNameChange,
  onTemplateVariablesChange,
  onSendTemplate,
  onAutomationToggle,
  onTagChange,
}: {
  conversations: MarketingConversationSummary[];
  conversationDetail: MarketingConversationDetail | null;
  selectedConversationId: string | null;
  replyText: string;
  selectedImageFile: File | null;
  selectedImagePreview: string | null;
  templates: WhatsAppTemplate[];
  templateName: string;
  templateVariables: string;
  isSaving: boolean;
  onSelectConversation: (id: string) => void;
  onReplyTextChange: (value: string) => void;
  onSelectImage: (file: File) => void;
  onClearImage: () => void;
  onSendReply: () => void;
  onTemplateNameChange: (value: string) => void;
  onTemplateVariablesChange: (value: string) => void;
  onSendTemplate: () => void;
  onAutomationToggle: () => void;
  onTagChange: (tag: MarketingTag) => void;
}) {
  const windowOpen = conversationDetail?.window.is_open;
  const canReply = Boolean(conversationDetail && windowOpen);
  const canSendTemplate = Boolean(conversationDetail?.conversation.channel === "whatsapp" && templateName);
  const [activeInspector, setActiveInspector] = useState<"customer" | "source" | "orders">("customer");
  return (
    <section className="grid min-h-0 flex-1 gap-4 xl:grid-cols-[330px_minmax(0,1fr)_340px]">
      <div className="min-h-0 overflow-hidden rounded-md border border-[#ddd5ca] bg-white">
        <div className="border-b border-[#ebe5dc] p-4">
          <h2 className="text-base font-bold">对话列表</h2>
          <p className="text-xs text-[#6b746f]">{conversations.length} 个 thread</p>
        </div>
        <div className="h-[calc(100%-73px)] overflow-y-auto">
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
                        {item.customer_name || item.platform_id || "Unknown contact"}
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
                  <TagBadge tag={item.current_tag} />
                  {item.handoff_recommended && <HandoffBadge />}
                  <span className="rounded bg-[#f2eee7] px-2 py-1">{item.acquisition.source}</span>
                </div>
                <BlockerPills blockers={item.latest_blockers || []} compact />
              </button>
            ))
          )}
        </div>
      </div>

      <div className="flex min-h-0 flex-col overflow-hidden rounded-md border border-[#ddd5ca] bg-white">
        <div className="flex items-start justify-between gap-4 border-b border-[#ebe5dc] p-4">
          <div>
            <h2 className="text-lg font-bold">
              {conversationDetail?.conversation.customer_name || "选择一个对话"}
            </h2>
            {conversationDetail && (
              <p className="mt-1 text-xs text-[#6b746f]">
                {channelLabel(conversationDetail.conversation.channel)} ·{" "}
                {conversationDetail.conversation.platform_id || "Unknown contact"}
              </p>
            )}
          </div>
          {conversationDetail && <WindowBadge isOpen={conversationDetail.window.is_open} />}
        </div>

        <div className="min-h-0 flex-1 space-y-3 overflow-y-auto bg-[#faf8f3] p-4">
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
                {message.message_type === "image" && message.media_url ? (
                  <div className="space-y-2">
                    <Image
                      id={`inbox-message-image-${message.message_id}`}
                      src={message.media_url}
                      alt={message.text || "Sent image"}
                      width={640}
                      height={420}
                      unoptimized
                      className="max-h-80 w-full rounded-md object-cover"
                    />
                    {message.text && message.text !== "Manual image sent" && (
                      <p className="whitespace-pre-wrap break-words">{message.text}</p>
                    )}
                  </div>
                ) : (
                  <p className="whitespace-pre-wrap break-words">{message.text}</p>
                )}
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
          {selectedImagePreview && selectedImageFile && (
            <div className="mb-3 flex items-center gap-3 rounded-md border border-[#d8d1c7] bg-[#fbfaf6] p-2">
              <div
                id="inbox-selected-image-preview"
                role="img"
                aria-label={selectedImageFile.name}
                style={{ backgroundImage: `url(${selectedImagePreview})` }}
                className="h-16 w-16 rounded-md bg-cover bg-center bg-no-repeat"
              />
              <div className="min-w-0 flex-1">
                <p className="truncate text-sm font-semibold text-[#14231d]">{selectedImageFile.name}</p>
                <p className="text-xs text-[#6b746f]">{formatFileSize(selectedImageFile.size)}</p>
              </div>
              <button
                id="inbox-clear-image-button"
                type="button"
                onClick={onClearImage}
                disabled={isSaving}
                className="inline-flex h-9 w-9 items-center justify-center rounded-md border border-[#d8d1c7] bg-white text-[#5d6a64] hover:text-[#10251d] disabled:opacity-50"
                aria-label="清除已选图片"
              >
                <X size={16} />
              </button>
            </div>
          )}
          <div className="grid gap-3 lg:grid-cols-[1fr_auto]">
            <div className="grid gap-2">
              <textarea
                id="inbox-reply-textarea"
                value={replyText}
                onChange={(event) => onReplyTextChange(event.target.value)}
                rows={3}
                disabled={!canReply}
                className="min-h-24 resize-none rounded-md border border-[#d8d1c7] bg-white p-3 text-sm text-[#14231d] outline-none focus:border-[#236b50] disabled:bg-[#f2eee7]"
                placeholder={windowOpen ? "输入人工回复；选择图片后这里会作为图片说明..." : "窗口已关闭，无法自由回复"}
              />
              <div>
                <input
                  id="inbox-image-input"
                  type="file"
                  accept="image/jpeg,image/png,image/webp"
                  className="sr-only"
                  disabled={!canReply || isSaving}
                  onChange={(event) => {
                    const file = event.currentTarget.files?.[0];
                    if (file) {
                      onSelectImage(file);
                    }
                    event.currentTarget.value = "";
                  }}
                />
                <label
                  id="inbox-attach-image-button"
                  htmlFor="inbox-image-input"
                  className={`inline-flex items-center gap-2 rounded-md border border-[#cfd8d2] bg-white px-3 py-2 text-sm font-semibold text-[#294239] ${
                    canReply && !isSaving ? "cursor-pointer hover:border-[#236b50]" : "cursor-not-allowed opacity-50"
                  }`}
                >
                  <ImageIcon size={16} />
                  图片
                </label>
              </div>
            </div>
            <button
              id="inbox-send-text-button"
              onClick={onSendReply}
              disabled={isSaving || !canReply || (!replyText.trim() && !selectedImageFile)}
              className="inline-flex h-12 items-center justify-center gap-2 rounded-md bg-[#123d2f] px-5 text-sm font-bold text-white disabled:cursor-not-allowed disabled:opacity-50"
            >
              {isSaving ? <Loader2 className="animate-spin" size={16} /> : <Send size={16} />}
              发送
            </button>
          </div>
          {conversationDetail?.conversation.channel === "whatsapp" && (
            <div className="mt-4 rounded-md border border-[#e5ddd1] bg-[#fbfaf6] p-3">
              <div className="grid gap-3 lg:grid-cols-[220px_minmax(0,1fr)_auto]">
                <label className="grid gap-1 text-xs font-semibold text-[#6b746f]">
                  Template
                  <select
                    id="inbox-whatsapp-template-select"
                    value={templateName}
                    onChange={(event) => onTemplateNameChange(event.target.value)}
                    disabled={isSaving || templates.length === 0}
                    className="rounded-md border border-[#d8d1c7] bg-white px-3 py-2 text-sm font-bold text-[#14231d]"
                  >
                    <option value="">选择 template</option>
                    {templates.map((template) => (
                      <option key={`${template.name}-${template.language_code}`} value={template.name}>
                        {template.name} · {template.language_code}
                      </option>
                    ))}
                  </select>
                </label>
                <label className="grid gap-1 text-xs font-semibold text-[#6b746f]">
                  Variables
                  <textarea
                    id="inbox-whatsapp-template-variables"
                    value={templateVariables}
                    onChange={(event) => onTemplateVariablesChange(event.target.value)}
                    rows={2}
                    disabled={isSaving}
                    className="min-h-16 resize-none rounded-md border border-[#d8d1c7] bg-white p-2 text-sm text-[#14231d]"
                  />
                </label>
                <button
                  id="inbox-send-template-button"
                  onClick={onSendTemplate}
                  disabled={isSaving || !canSendTemplate}
                  className="inline-flex h-10 self-end items-center justify-center gap-2 rounded-md border border-[#236b50] bg-white px-4 text-sm font-bold text-[#236b50] disabled:cursor-not-allowed disabled:opacity-50"
                >
                  <ShieldCheck size={16} />
                  Template
                </button>
              </div>
            </div>
          )}
        </div>
      </div>

      <aside className="flex min-h-0 flex-col overflow-hidden rounded-md border border-[#ddd5ca] bg-white">
        <div className="grid shrink-0 grid-cols-3 border-b border-[#ebe5dc] p-2">
          {([
            ["customer", "顾客与分类"],
            ["source", "来源"],
            ["orders", "关联订单"],
          ] as Array<[typeof activeInspector, string]>).map(([tab, label]) => (
            <button
              key={tab}
              id={`inbox-inspector-${tab}`}
              onClick={() => setActiveInspector(tab)}
              className={`rounded-md px-2 py-2 text-xs font-bold ${
                activeInspector === tab
                  ? "bg-[#10251d] text-white"
                  : "text-[#5d6a64] hover:bg-[#f7faf8] hover:text-[#10251d]"
              }`}
            >
              {label}
            </button>
          ))}
        </div>
        <div className="min-h-0 flex-1 overflow-y-auto p-4">
          {activeInspector === "customer" && (
            conversationDetail ? (
              <div className="space-y-4 text-sm">
                <InfoRow label="Channel" value={channelLabel(conversationDetail.conversation.channel)} />
                <InfoRow label="Platform ID" value={conversationDetail.conversation.platform_id || "Unknown contact"} />
                <InfoRow label="Marketing" value={conversationDetail.conversation.marketing_status || "-"} />
                <InfoRow label="窗口" value={conversationDetail.window.is_open ? "可自由回复" : "已关闭"} />
                <InfoRow
                  label="Handoff"
                  value={conversationDetail.conversation.handoff_recommended ? "Needs human follow-up" : "No"}
                />
                {conversationDetail.conversation.handoff_reason && (
                  <InfoRow label="Reason" value={conversationDetail.conversation.handoff_reason} />
                )}
                <div className="grid gap-2">
                  <span className="text-xs font-semibold text-[#6b746f]">Blockers</span>
                  <BlockerPills blockers={conversationDetail.conversation.latest_blockers || []} />
                </div>
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
            )
          )}

          {activeInspector === "source" && (
            conversationDetail ? (
              <div className="space-y-2 text-sm">
                <InfoRow label="Source" value={conversationDetail.conversation.acquisition.source || "unknown/direct"} />
                <InfoRow label="Ref" value={conversationDetail.conversation.acquisition.ref || "-"} />
                <InfoRow label="Ad ID" value={conversationDetail.conversation.acquisition.ad_id || "-"} />
                <InfoRow label="Post ID" value={conversationDetail.conversation.acquisition.post_id || "-"} />
              </div>
            ) : (
              <p className="text-sm text-[#6b746f]">暂无来源资料。</p>
            )
          )}

          {activeInspector === "orders" && (
            <div className="space-y-3">
              {conversationDetail && (
                <div className="grid grid-cols-3 gap-2 text-center text-xs">
                  <div className="rounded-md bg-[#f2eee7] p-2">
                    <p className="font-bold text-[#10251d]">{conversationDetail.conversation.matched_order_count || 0}</p>
                    <p className="text-[#6b746f]">Matched</p>
                  </div>
                  <div className="rounded-md bg-[#f2eee7] p-2">
                    <p className="truncate font-bold text-[#10251d]">
                      {conversationDetail.conversation.latest_order_status || "-"}
                    </p>
                    <p className="text-[#6b746f]">Order</p>
                  </div>
                  <div className="rounded-md bg-[#f2eee7] p-2">
                    <p className="truncate font-bold text-[#10251d]">
                      {conversationDetail.conversation.latest_payment_status || "-"}
                    </p>
                    <p className="text-[#6b746f]">Payment</p>
                  </div>
                </div>
              )}
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
          )}
        </div>
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

function CampaignPanel({
  templates,
  campaigns,
  campaignDetail,
  campaignForm,
  campaignPreview,
  isSaving,
  onFormChange,
  onPreview,
  onCreate,
  onSelectCampaign,
  onAction,
}: {
  templates: WhatsAppTemplate[];
  campaigns: WhatsAppCampaign[];
  campaignDetail: WhatsAppCampaignDetail | null;
  campaignForm: typeof emptyCampaign;
  campaignPreview: WhatsAppCampaignPreview | null;
  isSaving: boolean;
  onFormChange: (value: typeof emptyCampaign) => void;
  onPreview: () => void;
  onCreate: () => void;
  onSelectCampaign: (id: string) => void;
  onAction: (id: string, action: "launch" | "pause" | "cancel") => void;
}) {
  return (
    <section className="grid h-full min-h-0 gap-4 xl:grid-cols-[minmax(0,1fr)_420px]">
      <div className="min-h-0 space-y-4 overflow-y-auto pr-1">
        <Panel title="Campaign Builder">
          <div className="grid gap-3 lg:grid-cols-2">
            <LabeledInput
              id="whatsapp-campaign-name"
              label="Campaign 名称"
              value={campaignForm.name}
              onChange={(value) => onFormChange({ ...campaignForm, name: value })}
            />
            <label className="grid gap-1 text-sm font-semibold">
              Template
              <select
                id="whatsapp-campaign-template"
                value={campaignForm.template_name}
                onChange={(event) => {
                  const template = templates.find((item) => item.name === event.target.value);
                  onFormChange({
                    ...campaignForm,
                    template_name: event.target.value,
                    language_code: template?.language_code || campaignForm.language_code,
                  });
                }}
                className={inputClassName}
              >
                <option value="">选择 approved template</option>
                {templates.map((item) => (
                  <option key={`${item.name}-${item.language_code}`} value={item.name}>
                    {item.name} · {item.language_code}
                  </option>
                ))}
              </select>
            </label>
            <LabeledInput
              id="whatsapp-campaign-language"
              label="语言"
              value={campaignForm.language_code}
              onChange={(value) => onFormChange({ ...campaignForm, language_code: value })}
            />
            <LabeledInput
              id="whatsapp-campaign-tags"
              label="受众标签，逗号分隔"
              value={campaignForm.audience_tags.join(", ")}
              onChange={(value) =>
                onFormChange({
                  ...campaignForm,
                  audience_tags: splitComma(value),
                })
              }
            />
          </div>
          <label className="mt-3 grid gap-1 text-sm font-semibold">
            Template 变量，每行一个
            <textarea
              id="whatsapp-campaign-variables"
              value={campaignForm.body_variables.join("\n")}
              onChange={(event) =>
                onFormChange({
                  ...campaignForm,
                  body_variables: splitLines(event.target.value),
                })
              }
              rows={4}
              className="rounded-md border border-[#d8d1c7] bg-white p-3 text-sm text-[#14231d]"
            />
          </label>
          <div className="mt-4 flex flex-wrap gap-2">
            <button
              id="whatsapp-campaign-preview-button"
              onClick={onPreview}
              disabled={isSaving || !campaignForm.template_name || !campaignForm.name}
              className="inline-flex items-center gap-2 rounded-md border border-[#236b50] bg-white px-4 py-2 text-sm font-bold text-[#236b50] disabled:opacity-50"
            >
              <Users size={16} />
              Preview
            </button>
            <button
              id="whatsapp-campaign-create-button"
              onClick={onCreate}
              disabled={isSaving || !campaignPreview || !campaignForm.template_name || !campaignForm.name}
              className="inline-flex items-center gap-2 rounded-md bg-[#10251d] px-4 py-2 text-sm font-bold text-white disabled:opacity-50"
            >
              <Save size={16} />
              Save Draft
            </button>
          </div>
        </Panel>

        <Panel title="Audience Preview">
          {campaignPreview ? (
            <div className="space-y-4">
              <div className="grid gap-3 md:grid-cols-4">
                <Metric label="可发送" value={campaignPreview.eligible_count} />
                <Metric label="已退订/未 opt-in" value={campaignPreview.skipped_opt_out_count} />
                <Metric label="窗口外" value={campaignPreview.window_closed_count} />
                <Metric label="缺变量" value={campaignPreview.missing_variable_count} />
              </div>
              <div className="max-h-72 overflow-y-auto rounded-md border border-[#e5ddd1]">
                {campaignPreview.recipients.map((item) => (
                  <div
                    key={item.contact_id}
                    className="flex items-center justify-between border-b border-[#f0ebe4] p-3 text-sm"
                  >
                    <div>
                      <p className="font-semibold">{item.customer_name || item.wa_id}</p>
                      <p className="text-xs text-[#6b746f]">
                        {item.current_tag || "untagged"} · {item.wa_id}
                      </p>
                    </div>
                    <WindowBadge isOpen={item.window_open} />
                  </div>
                ))}
              </div>
            </div>
          ) : (
            <p className="text-sm text-[#6b746f]">先 preview，确认 opt-in 受众后才可保存和启动。</p>
          )}
        </Panel>
      </div>

      <div className="min-h-0 space-y-4 overflow-y-auto pr-1">
        <Panel title="Campaigns">
          <div className="space-y-3">
            {campaigns.length ? (
              campaigns.map((campaign) => (
                <button
                  key={campaign.campaign_id}
                  onClick={() => onSelectCampaign(campaign.campaign_id)}
                  className="block w-full rounded-md border border-[#e5ddd1] bg-[#faf8f3] p-3 text-left text-sm hover:border-[#236b50]"
                >
                  <div className="flex items-center justify-between gap-3">
                    <p className="font-bold">{campaign.name}</p>
                    <StatusPill status={campaign.status} />
                  </div>
                  <p className="mt-1 text-xs text-[#6b746f]">
                    {campaign.template_name} · sent {campaign.sent_count || 0} · failed {campaign.failed_count || 0}
                  </p>
                </button>
              ))
            ) : (
              <p className="text-sm text-[#6b746f]">No campaigns.</p>
            )}
          </div>
        </Panel>

        <Panel title="Launch Control">
          {campaignDetail ? (
            <div className="space-y-4">
              <InfoRow label="Campaign" value={campaignDetail.campaign.name} />
              <InfoRow label="Template" value={campaignDetail.campaign.template_name} />
              <InfoRow label="Status" value={campaignDetail.campaign.status} />
              <div className="grid grid-cols-2 gap-2">
                <Metric label="Queued" value={campaignDetail.campaign.queued_count || 0} />
                <Metric label="Sent" value={campaignDetail.campaign.sent_count || 0} />
                <Metric label="Delivered" value={campaignDetail.campaign.delivered_count || 0} />
                <Metric label="Failed" value={campaignDetail.campaign.failed_count || 0} />
              </div>
              <div className="flex flex-wrap gap-2">
                <button
                  id="whatsapp-campaign-launch-button"
                  onClick={() => onAction(campaignDetail.campaign.campaign_id, "launch")}
                  disabled={isSaving || !["draft", "paused"].includes(campaignDetail.campaign.status)}
                  className="inline-flex items-center gap-2 rounded-md bg-[#123d2f] px-3 py-2 text-sm font-bold text-white disabled:opacity-50"
                >
                  <PlayCircle size={16} />
                  Launch
                </button>
                <button
                  id="whatsapp-campaign-pause-button"
                  onClick={() => onAction(campaignDetail.campaign.campaign_id, "pause")}
                  disabled={isSaving || !["queued", "sending"].includes(campaignDetail.campaign.status)}
                  className="inline-flex items-center gap-2 rounded-md border border-[#d4aa3b] bg-white px-3 py-2 text-sm font-bold text-[#8a6413] disabled:opacity-50"
                >
                  <PauseCircle size={16} />
                  Pause
                </button>
                <button
                  id="whatsapp-campaign-cancel-button"
                  onClick={() => onAction(campaignDetail.campaign.campaign_id, "cancel")}
                  disabled={isSaving || campaignDetail.campaign.status === "cancelled"}
                  className="inline-flex items-center gap-2 rounded-md border border-[#c95b4a] bg-white px-3 py-2 text-sm font-bold text-[#a84133] disabled:opacity-50"
                >
                  <XCircle size={16} />
                  Cancel
                </button>
              </div>
              <div className="max-h-80 overflow-y-auto rounded-md border border-[#e5ddd1]">
                {campaignDetail.recipients.map((recipient) => (
                  <div key={recipient.recipient_id} className="border-b border-[#f0ebe4] p-3 text-sm">
                    <div className="flex items-center justify-between gap-3">
                      <p className="font-semibold">{recipient.customer_name || recipient.wa_id}</p>
                      <StatusPill status={recipient.status} />
                    </div>
                    {recipient.error_message && (
                      <p className="mt-1 text-xs text-[#a84133]">{recipient.error_message}</p>
                    )}
                  </div>
                ))}
              </div>
            </div>
          ) : (
            <p className="text-sm text-[#6b746f]">选择一个 campaign 查看详情。</p>
          )}
        </Panel>
      </div>
    </section>
  );
}

function TemplatePanel({
  templates,
  localTemplate,
  isSaving,
  onLocalTemplateChange,
  onSync,
  onSave,
}: {
  templates: WhatsAppTemplate[];
  localTemplate: { name: string; language_code: string; category: string; status: string };
  isSaving: boolean;
  onLocalTemplateChange: (value: { name: string; language_code: string; category: string; status: string }) => void;
  onSync: () => void;
  onSave: () => void;
}) {
  return (
    <section className="grid h-full min-h-0 gap-4 xl:grid-cols-[380px_minmax(0,1fr)]">
      <Panel title="Template Controls">
        <div className="space-y-3">
          <button
            id="whatsapp-template-sync-button"
            onClick={onSync}
            disabled={isSaving}
            className="inline-flex w-full items-center justify-center gap-2 rounded-md bg-[#10251d] px-4 py-3 text-sm font-bold text-white disabled:opacity-50"
          >
            <RefreshCw size={16} />
            Sync from Meta
          </button>
          <LabeledInput
            id="whatsapp-local-template-name"
            label="Template name"
            value={localTemplate.name}
            onChange={(value) => onLocalTemplateChange({ ...localTemplate, name: value })}
          />
          <LabeledInput
            id="whatsapp-local-template-language"
            label="Language"
            value={localTemplate.language_code}
            onChange={(value) => onLocalTemplateChange({ ...localTemplate, language_code: value })}
          />
          <div className="grid grid-cols-2 gap-3">
            <LabeledInput
              id="whatsapp-local-template-category"
              label="Category"
              value={localTemplate.category}
              onChange={(value) => onLocalTemplateChange({ ...localTemplate, category: value })}
            />
            <LabeledInput
              id="whatsapp-local-template-status"
              label="Status"
              value={localTemplate.status}
              onChange={(value) => onLocalTemplateChange({ ...localTemplate, status: value })}
            />
          </div>
          <button
            id="whatsapp-template-save-button"
            onClick={onSave}
            disabled={isSaving || !localTemplate.name.trim()}
            className="inline-flex w-full items-center justify-center gap-2 rounded-md border border-[#236b50] bg-white px-4 py-3 text-sm font-bold text-[#236b50] disabled:opacity-50"
          >
            <Save size={16} />
            Save Local Mirror
          </button>
        </div>
      </Panel>

      <Panel title="Templates">
        <div className="min-h-0 overflow-y-auto">
          {templates.length ? (
            <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
              {templates.map((template) => (
                <div key={template.template_id} className="rounded-md border border-[#e5ddd1] bg-[#faf8f3] p-4">
                  <div className="flex items-start justify-between gap-3">
                    <div className="min-w-0">
                      <p className="break-words text-sm font-bold">{template.name}</p>
                      <p className="mt-1 text-xs text-[#6b746f]">
                        {template.language_code} · {template.category}
                      </p>
                    </div>
                    <StatusPill status={template.status} />
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-sm text-[#6b746f]">No templates.</p>
          )}
        </div>
      </Panel>
    </section>
  );
}

function HealthPill({ health }: { health: WhatsAppHealth | null }) {
  if (!health) return null;
  return (
    <div
      className={`inline-flex items-center gap-2 rounded-md px-4 py-2 text-sm font-semibold ${
        health.ready
          ? "border border-[#b8d8c7] bg-[#ecf8f1] text-[#236b50]"
          : "border border-[#efcfb7] bg-[#fff6ec] text-[#9a5a22]"
      }`}
    >
      {health.ready ? <CheckCircle2 size={16} /> : <AlertTriangle size={16} />}
      {health.ready ? "Cloud API Ready" : "Config Incomplete"}
    </div>
  );
}

function Metric({ label, value }: { label: string; value: number }) {
  return (
    <div className="rounded-md border border-[#e5ddd1] bg-[#faf8f3] p-3">
      <p className="text-xs font-semibold text-[#6b746f]">{label}</p>
      <p className="mt-1 text-2xl font-bold text-[#10251d]">{value}</p>
    </div>
  );
}

function StatusPill({ status }: { status: string }) {
  const normalized = status.toLowerCase();
  const className =
    normalized.includes("fail") || normalized.includes("reject")
      ? "bg-[#fff0e8] text-[#a84133]"
      : normalized.includes("approve") ||
          normalized.includes("sent") ||
          normalized.includes("read") ||
          normalized.includes("delivered")
        ? "bg-[#e8f8ef] text-[#236b50]"
        : "bg-[#f2eee7] text-[#6b746f]";
  return <span className={`rounded px-2 py-1 text-[11px] font-bold ${className}`}>{status}</span>;
}

function LabeledInput({
  id,
  label,
  value,
  onChange,
}: {
  id: string;
  label: string;
  value: string;
  onChange: (value: string) => void;
}) {
  return (
    <label className="grid gap-1 text-sm font-semibold">
      {label}
      <input id={id} value={value} onChange={(event) => onChange(event.target.value)} className={inputClassName} />
    </label>
  );
}

function TagBadge({ tag }: { tag: MarketingConversationSummary["current_tag"] }) {
  const isHot = tag === "cart_hot";
  return (
    <span
      className={`rounded px-2 py-1 ${
        isHot ? "bg-[#fff2d8] font-bold text-[#8a4a00]" : "bg-[#f2eee7] text-[#6b746f]"
      }`}
    >
      {tag || "untagged"}
    </span>
  );
}

function HandoffBadge() {
  return (
    <span className="rounded bg-[#ffe8e2] px-2 py-1 font-bold text-[#9b321c]">
      Needs human follow-up
    </span>
  );
}

function BlockerPills({ blockers, compact = false }: { blockers: string[]; compact?: boolean }) {
  if (!blockers.length) {
    return compact ? null : <p className="text-xs text-[#8a938e]">No active blocker</p>;
  }
  return (
    <div className={`flex flex-wrap gap-1.5 ${compact ? "mt-2" : ""}`}>
      {blockers.map((blocker) => (
        <span
          key={blocker}
          className="rounded border border-[#e0c9ae] bg-[#fffaf0] px-2 py-1 text-[11px] font-bold text-[#7a5128]"
        >
          {blockerLabel(blocker)}
        </span>
      ))}
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
      <Clock size={12} />
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

function blockerLabel(value: string) {
  const labels: Record<string, string> = {
    price_or_package: "Price/package",
    delivery: "Delivery",
    payment: "Payment",
  };
  return labels[value] || value;
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

function formatFileSize(value: number) {
  if (value < 1024) return `${value} B`;
  if (value < 1024 * 1024) return `${(value / 1024).toFixed(1)} KB`;
  return `${(value / 1024 / 1024).toFixed(1)} MB`;
}

const inputClassName = "rounded-md border border-[#d8d1c7] bg-white px-3 py-2 text-sm text-[#14231d]";

function splitLines(value: string) {
  return value
    .split("\n")
    .map((item) => item.trim())
    .filter(Boolean);
}

function splitComma(value: string) {
  return value
    .split(",")
    .map((item) => item.trim())
    .filter(Boolean);
}
