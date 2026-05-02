"use client";

import type { ReactNode } from "react";
import { useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import {
  AlertTriangle,
  CheckCircle2,
  Clock,
  Loader2,
  MessageCircle,
  PauseCircle,
  PlayCircle,
  RefreshCw,
  Save,
  Send,
  ShieldCheck,
  Users,
  XCircle,
} from "lucide-react";

import AdminSidebar from "@/components/admin/AdminSidebar";
import { isUserAdmin, logout, subscribeToAuthChanges } from "@/lib/auth-service";
import {
  WhatsAppCampaign,
  WhatsAppCampaignDetail,
  WhatsAppCampaignPreview,
  WhatsAppConversationDetail,
  WhatsAppConversationSummary,
  WhatsAppHealth,
  WhatsAppTemplate,
  cancelWhatsAppCampaign,
  createWhatsAppCampaign,
  getWhatsAppCampaign,
  getWhatsAppConversation,
  getWhatsAppHealth,
  launchWhatsAppCampaign,
  listWhatsAppCampaigns,
  listWhatsAppConversations,
  listWhatsAppTemplates,
  pauseWhatsAppCampaign,
  previewWhatsAppCampaign,
  saveWhatsAppTemplate,
  sendWhatsAppTemplate,
  sendWhatsAppText,
  syncWhatsAppTemplates,
  updateWhatsAppAutomation,
} from "@/lib/backend-whatsapp-service";

type AdminWhatsAppTab = "inbox" | "campaigns" | "templates";

const emptyCampaign = {
  name: "",
  template_name: "",
  language_code: "en_US",
  body_variables: [] as string[],
  audience_tags: [] as string[],
};

export default function AdminWhatsAppPage() {
  const router = useRouter();
  const [isAuthLoading, setIsAuthLoading] = useState(true);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [activeTab, setActiveTab] = useState<AdminWhatsAppTab>("inbox");
  const [health, setHealth] = useState<WhatsAppHealth | null>(null);
  const [conversations, setConversations] = useState<WhatsAppConversationSummary[]>([]);
  const [selectedConversationId, setSelectedConversationId] = useState<string | null>(null);
  const [conversationDetail, setConversationDetail] = useState<WhatsAppConversationDetail | null>(null);
  const [templates, setTemplates] = useState<WhatsAppTemplate[]>([]);
  const [campaigns, setCampaigns] = useState<WhatsAppCampaign[]>([]);
  const [campaignDetail, setCampaignDetail] = useState<WhatsAppCampaignDetail | null>(null);
  const [replyText, setReplyText] = useState("");
  const [templateName, setTemplateName] = useState("");
  const [templateVariables, setTemplateVariables] = useState("");
  const [campaignForm, setCampaignForm] = useState(emptyCampaign);
  const [campaignPreview, setCampaignPreview] = useState<WhatsAppCampaignPreview | null>(null);
  const [localTemplate, setLocalTemplate] = useState({
    name: "",
    language_code: "en_US",
    category: "MARKETING",
    status: "APPROVED",
  });

  useEffect(() => {
    const unsubscribe = subscribeToAuthChanges((user) => {
      if (!user || !isUserAdmin(user)) {
        router.push("/admin/login");
        return;
      }
      setIsAuthLoading(false);
      void loadData();
    });
    return () => unsubscribe();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [router]);

  const approvedTemplates = useMemo(
    () => templates.filter((item) => item.status.toUpperCase() === "APPROVED"),
    [templates],
  );

  async function loadData() {
    setIsLoading(true);
    try {
      const [healthPayload, conversationRows, templateRows, campaignRows] = await Promise.all([
        getWhatsAppHealth(),
        listWhatsAppConversations(),
        listWhatsAppTemplates(),
        listWhatsAppCampaigns(),
      ]);
      setHealth(healthPayload);
      setConversations(conversationRows);
      setTemplates(templateRows);
      setCampaigns(campaignRows);
      const nextConversationId = selectedConversationId || conversationRows[0]?.conversation_id || null;
      setSelectedConversationId(nextConversationId);
      if (nextConversationId) {
        await loadConversation(nextConversationId);
      } else {
        setConversationDetail(null);
      }
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
    } catch (error) {
      console.error("Failed to load WhatsApp console", error);
    } finally {
      setIsLoading(false);
    }
  }

  async function loadConversation(conversationId: string) {
    const detail = await getWhatsAppConversation(conversationId);
    setConversationDetail(detail);
    setSelectedConversationId(conversationId);
  }

  async function handleSendText() {
    if (!selectedConversationId || !replyText.trim()) return;
    setIsSaving(true);
    try {
      await sendWhatsAppText(selectedConversationId, replyText.trim());
      setReplyText("");
      await loadConversation(selectedConversationId);
      await loadListOnly();
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
      await loadListOnly();
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
      await updateWhatsAppAutomation(
        conversationDetail.conversation.conversation_id,
        paused,
        paused ? "manual_whatsapp_console" : undefined,
      );
      await loadConversation(conversationDetail.conversation.conversation_id);
      await loadListOnly();
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
      const preview = await previewWhatsAppCampaign({
        ...campaignForm,
        body_variables: campaignForm.body_variables,
      });
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
      const rows = await listWhatsAppCampaigns();
      setCampaigns(rows);
      const detail = await getWhatsAppCampaign(created.campaign_id);
      setCampaignDetail(detail);
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

  async function loadListOnly() {
    setConversations(await listWhatsAppConversations());
  }

  async function handleLogout() {
    await logout();
    router.push("/admin/login");
  }

  if (isAuthLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-[#f6f4ee]">
        <Loader2 className="animate-spin text-[#0d3b2e]" size={42} />
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
              <div className="mb-2 inline-flex items-center gap-2 rounded-md border border-[#cdd9d2] bg-white px-3 py-2 text-xs font-semibold text-[#236b50]">
                <MessageCircle size={14} />
                WhatsApp Business API
              </div>
              <h1 className="text-3xl font-bold text-[#10251d]">WhatsApp 操作台</h1>
              <p className="mt-1 max-w-3xl text-sm text-[#617069]">
                统一处理顾客对话、人工接管、Template、投递状态与合规批量广播。
              </p>
            </div>

            <div className="flex flex-wrap gap-2">
              <button
                id="whatsapp-refresh-button"
                onClick={() => void loadData()}
                className="inline-flex items-center gap-2 rounded-md border border-[#cfd8d2] bg-white px-4 py-2 text-sm font-semibold text-[#294239] hover:border-[#236b50]"
              >
                <RefreshCw size={16} />
                刷新
              </button>
              <HealthPill health={health} />
            </div>
          </header>

          <div className="flex flex-wrap gap-2">
            {(["inbox", "campaigns", "templates"] as AdminWhatsAppTab[]).map((tab) => (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                className={`rounded-md px-4 py-2 text-sm font-semibold ${
                  activeTab === tab
                    ? "bg-[#10251d] text-white"
                    : "border border-[#d7d0c5] bg-white text-[#5d6a64] hover:text-[#10251d]"
                }`}
              >
                {tab === "inbox" ? "Inbox" : tab === "campaigns" ? "Campaigns" : "Templates"}
              </button>
            ))}
          </div>

          {isLoading ? (
            <div className="flex h-80 items-center justify-center rounded-md border border-[#ded8ce] bg-white">
              <Loader2 className="animate-spin text-[#236b50]" size={32} />
            </div>
          ) : (
            <>
              {activeTab === "inbox" && (
                <InboxPanel
                  conversations={conversations}
                  conversationDetail={conversationDetail}
                  selectedConversationId={selectedConversationId}
                  templates={approvedTemplates}
                  replyText={replyText}
                  templateName={templateName}
                  templateVariables={templateVariables}
                  isSaving={isSaving}
                  onSelectConversation={(id) => void loadConversation(id)}
                  onReplyTextChange={setReplyText}
                  onTemplateNameChange={setTemplateName}
                  onTemplateVariablesChange={setTemplateVariables}
                  onSendText={() => void handleSendText()}
                  onSendTemplate={() => void handleSendTemplate()}
                  onAutomationToggle={() => void handleAutomationToggle()}
                />
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
            </>
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
  templates,
  replyText,
  templateName,
  templateVariables,
  isSaving,
  onSelectConversation,
  onReplyTextChange,
  onTemplateNameChange,
  onTemplateVariablesChange,
  onSendText,
  onSendTemplate,
  onAutomationToggle,
}: {
  conversations: WhatsAppConversationSummary[];
  conversationDetail: WhatsAppConversationDetail | null;
  selectedConversationId: string | null;
  templates: WhatsAppTemplate[];
  replyText: string;
  templateName: string;
  templateVariables: string;
  isSaving: boolean;
  onSelectConversation: (id: string) => void;
  onReplyTextChange: (value: string) => void;
  onTemplateNameChange: (value: string) => void;
  onTemplateVariablesChange: (value: string) => void;
  onSendText: () => void;
  onSendTemplate: () => void;
  onAutomationToggle: () => void;
}) {
  const windowOpen = conversationDetail?.window.is_open;
  return (
    <section className="grid min-h-[720px] gap-4 xl:grid-cols-[320px_minmax(0,1fr)_340px]">
      <div className="overflow-hidden rounded-md border border-[#ddd5ca] bg-white">
        <div className="border-b border-[#ebe5dc] p-4">
          <h2 className="text-base font-bold">对话列表</h2>
          <p className="text-xs text-[#6b746f]">{conversations.length} 个 WhatsApp thread</p>
        </div>
        <div className="max-h-[660px] overflow-y-auto">
          {conversations.map((item) => (
            <button
              key={item.conversation_id}
              onClick={() => onSelectConversation(item.conversation_id)}
              className={`block w-full border-b border-[#f0ebe4] p-4 text-left hover:bg-[#f7faf8] ${
                selectedConversationId === item.conversation_id ? "bg-[#edf7f2]" : ""
              }`}
            >
              <div className="flex items-start justify-between gap-3">
                <div className="min-w-0">
                  <p className="truncate text-sm font-bold text-[#14231d]">
                    {item.customer_name || item.wa_id}
                  </p>
                  <p className="mt-1 truncate text-xs text-[#69746e]">{item.latest_message?.text || "No messages yet"}</p>
                </div>
                <WindowBadge isOpen={item.window.is_open} />
              </div>
              <div className="mt-3 flex flex-wrap gap-2 text-[11px] text-[#6b746f]">
                <span className="rounded bg-[#f2eee7] px-2 py-1">{item.current_tag || "untagged"}</span>
                <span className="rounded bg-[#f2eee7] px-2 py-1">{item.marketing_status || "unknown"}</span>
              </div>
            </button>
          ))}
        </div>
      </div>

      <div className="flex min-h-[720px] flex-col rounded-md border border-[#ddd5ca] bg-white">
        <div className="flex items-start justify-between gap-4 border-b border-[#ebe5dc] p-4">
          <div>
            <h2 className="text-lg font-bold">
              {conversationDetail?.conversation.customer_name || conversationDetail?.conversation.wa_id || "选择一个对话"}
            </h2>
            {conversationDetail && (
              <p className="mt-1 text-xs text-[#6b746f]">
                {conversationDetail.conversation.wa_id} · {conversationDetail.conversation.current_tag}
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
              id="whatsapp-reply-textarea"
              value={replyText}
              onChange={(event) => onReplyTextChange(event.target.value)}
              rows={3}
              disabled={!conversationDetail || !windowOpen}
              className="min-h-24 resize-none rounded-md border border-[#d8d1c7] bg-white p-3 text-sm text-[#14231d] outline-none focus:border-[#236b50] disabled:bg-[#f2eee7]"
              placeholder={windowOpen ? "输入人工回复..." : "24 小时窗口已关闭，请使用 template"}
            />
            <button
              id="whatsapp-send-text-button"
              onClick={onSendText}
              disabled={isSaving || !conversationDetail || !windowOpen || !replyText.trim()}
              className="inline-flex h-12 items-center justify-center gap-2 rounded-md bg-[#123d2f] px-5 text-sm font-bold text-white disabled:cursor-not-allowed disabled:opacity-50"
            >
              {isSaving ? <Loader2 className="animate-spin" size={16} /> : <Send size={16} />}
              发送
            </button>
          </div>

          <div className="mt-3 grid gap-3 lg:grid-cols-[220px_1fr_auto]">
            <select
              id="whatsapp-template-select"
              value={templateName}
              onChange={(event) => onTemplateNameChange(event.target.value)}
              className="rounded-md border border-[#d8d1c7] bg-white px-3 py-2 text-sm text-[#14231d]"
            >
              {templates.map((item) => (
                <option key={`${item.name}-${item.language_code}`} value={item.name}>
                  {item.name} · {item.language_code}
                </option>
              ))}
            </select>
            <input
              id="whatsapp-template-variables"
              value={templateVariables}
              onChange={(event) => onTemplateVariablesChange(event.target.value)}
              className="rounded-md border border-[#d8d1c7] bg-white px-3 py-2 text-sm text-[#14231d]"
              placeholder="Template 变量，每行一个"
            />
            <button
              id="whatsapp-template-send-button"
              onClick={onSendTemplate}
              disabled={isSaving || !conversationDetail || !templateName}
              className="inline-flex items-center justify-center gap-2 rounded-md border border-[#236b50] bg-white px-4 py-2 text-sm font-bold text-[#236b50] disabled:cursor-not-allowed disabled:opacity-50"
            >
              <ShieldCheck size={16} />
              发 Template
            </button>
          </div>
        </div>
      </div>

      <aside className="space-y-4">
        <Panel title="顾客与自动化">
          {conversationDetail ? (
            <div className="space-y-4 text-sm">
              <InfoRow label="WhatsApp" value={conversationDetail.conversation.wa_id} />
              <InfoRow label="Lead Tag" value={conversationDetail.conversation.current_tag || "-"} />
              <InfoRow label="Marketing" value={conversationDetail.conversation.marketing_status || "-"} />
              <InfoRow label="窗口" value={conversationDetail.window.is_open ? "可自由回复" : "只可 Template"} />
              <button
                id="whatsapp-automation-toggle-button"
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
    <section className="grid gap-4 xl:grid-cols-[minmax(0,1fr)_420px]">
      <div className="space-y-4">
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
                  <div key={item.contact_id} className="flex items-center justify-between border-b border-[#f0ebe4] p-3 text-sm">
                    <div>
                      <p className="font-semibold">{item.customer_name || item.wa_id}</p>
                      <p className="text-xs text-[#6b746f]">{item.current_tag || "untagged"} · {item.wa_id}</p>
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

      <div className="space-y-4">
        <Panel title="Campaigns">
          <div className="space-y-3">
            {campaigns.map((campaign) => (
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
            ))}
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
                    {recipient.error_message && <p className="mt-1 text-xs text-[#a84133]">{recipient.error_message}</p>}
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
    <section className="grid gap-4 xl:grid-cols-[380px_minmax(0,1fr)]">
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
        <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
          {templates.map((template) => (
            <div key={template.template_id} className="rounded-md border border-[#e5ddd1] bg-[#faf8f3] p-4">
              <div className="flex items-start justify-between gap-3">
                <div className="min-w-0">
                  <p className="break-words text-sm font-bold">{template.name}</p>
                  <p className="mt-1 text-xs text-[#6b746f]">{template.language_code} · {template.category}</p>
                </div>
                <StatusPill status={template.status} />
              </div>
            </div>
          ))}
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

function Panel({ title, children }: { title: string; children: ReactNode }) {
  return (
    <div className="rounded-md border border-[#ddd5ca] bg-white p-4">
      <h2 className="mb-4 text-base font-bold text-[#10251d]">{title}</h2>
      {children}
    </div>
  );
}

function InfoRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex items-start justify-between gap-4 border-b border-[#eee8df] py-2">
      <span className="text-xs font-semibold text-[#6b746f]">{label}</span>
      <span className="break-words text-right text-sm font-bold text-[#14231d]">{value}</span>
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

function WindowBadge({ isOpen }: { isOpen: boolean }) {
  return (
    <span
      className={`inline-flex shrink-0 items-center gap-1 rounded px-2 py-1 text-[11px] font-bold ${
        isOpen ? "bg-[#e8f8ef] text-[#236b50]" : "bg-[#fff0e8] text-[#a84133]"
      }`}
    >
      <Clock size={12} />
      {isOpen ? "Open" : "Template"}
    </span>
  );
}

function StatusPill({ status }: { status: string }) {
  const normalized = status.toLowerCase();
  const className = normalized.includes("fail") || normalized.includes("reject")
    ? "bg-[#fff0e8] text-[#a84133]"
    : normalized.includes("approve") || normalized.includes("sent") || normalized.includes("read") || normalized.includes("delivered")
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
      <input
        id={id}
        value={value}
        onChange={(event) => onChange(event.target.value)}
        className={inputClassName}
      />
    </label>
  );
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

function formatTime(value: string | undefined) {
  if (!value) return "";
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) return String(value);
  return parsed.toLocaleString("en-SG", {
    month: "short",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  });
}
