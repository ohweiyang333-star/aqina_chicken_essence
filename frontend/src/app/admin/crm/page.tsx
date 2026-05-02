"use client";

import type { ReactNode } from "react";
import { useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import {
  Bot,
  Brain,
  Loader2,
  MessageCircle,
  Package2,
  QrCode,
  RefreshCw,
  Save,
  ShieldAlert,
  Sparkles,
} from "lucide-react";

import AdminSidebar from "@/components/admin/AdminSidebar";
import { isAdminUser, logout, subscribeToAuthChanges } from "@/lib/auth-service";
import {
  ChatbotSettings,
  getChatbotSettings,
  updateChatbotSettings,
} from "@/lib/backend-chatbot-service";
import {
  EscalationRecord,
  FacebookCommentEvent,
  acknowledgeEscalation,
  listFacebookCommentEvents,
  listEscalations,
  resolveEscalation,
} from "@/lib/backend-marketing-service";

const RULE_FIELDS = [
  ["comment_hook", "public_reply", "贴文公开回复"],
  ["comment_hook", "private_opening", "Messenger / WhatsApp 破冰私信"],
  ["t15m", "lead_cold", "15 分钟 - 冷线"],
  ["t15m", "qualified_warm", "15 分钟 - 暖线"],
  ["t3h", "default", "3 小时 - 感官唤醒"],
  ["t12h", "cart_hot", "12 小时 - 逼单付款"],
  ["t23h", "default", "23 小时 - YES 留存"],
] as const;

export default function AdminCRMPage() {
  const router = useRouter();
  const [isAuthLoading, setIsAuthLoading] = useState(true);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [settings, setSettings] = useState<ChatbotSettings | null>(null);
  const [escalations, setEscalations] = useState<EscalationRecord[]>([]);
  const [commentEvents, setCommentEvents] = useState<FacebookCommentEvent[]>([]);

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
        void loadData();
      })();
    });
    return () => unsubscribe();
  }, [router]);

  const escalationStats = useMemo(
    () => ({
      open: escalations.filter((item) => item.status === "open").length,
      acknowledged: escalations.filter((item) => item.status === "acknowledged").length,
      resolved: escalations.filter((item) => item.status === "resolved").length,
    }),
    [escalations],
  );

  async function loadData() {
    setIsLoading(true);
    try {
      const [fetchedSettings, escalationRows] = await Promise.all([
        getChatbotSettings(),
        listEscalations(),
      ]);
      const facebookRows = await listFacebookCommentEvents();
      setSettings(fetchedSettings);
      setEscalations(escalationRows);
      setCommentEvents(facebookRows);
    } catch (error) {
      console.error("Failed to load CRM settings", error);
    } finally {
      setIsLoading(false);
    }
  }

  async function handleSave() {
    if (!settings) return;
    setIsSaving(true);
    try {
      const updated = await updateChatbotSettings(settings);
      setSettings(updated);
      alert("CRM 设置已保存。");
    } catch (error) {
      console.error("Failed to save CRM settings", error);
      alert("保存失败，请稍后再试。");
    } finally {
      setIsSaving(false);
    }
  }

  async function handleAcknowledge(escalationId: string) {
    await acknowledgeEscalation(escalationId);
    await loadData();
  }

  async function handleResolve(escalationId: string) {
    await resolveEscalation(escalationId);
    await loadData();
  }

  function updateRule(stage: string, key: string, instruction: string) {
    setSettings((current) => {
      if (!current) return current;
      return {
        ...current,
        crm_follow_up_rules: {
          ...current.crm_follow_up_rules,
          [stage]: {
            ...(current.crm_follow_up_rules[stage] || {}),
            [key]: { instruction },
          },
        },
      };
    });
  }

  function updatePackage(
    packageCode: string,
    field: keyof ChatbotSettings["packages"][string],
    value: string | number | boolean,
  ) {
    setSettings((current) => {
      if (!current) return current;
      return {
        ...current,
        packages: {
          ...current.packages,
          [packageCode]: {
            ...current.packages[packageCode],
            [field]: value,
          },
        },
      };
    });
  }

  function updateFacebookAutomation(
    field: keyof ChatbotSettings["facebook_comment_automation"],
    value: boolean | string[],
  ) {
    setSettings((current) => {
      if (!current) return current;
      return {
        ...current,
        facebook_comment_automation: {
          ...current.facebook_comment_automation,
          [field]: value,
        },
      };
    });
  }

  if (isAuthLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-[#f4f1eb]">
        <Loader2 className="animate-spin text-[#8e5d34]" size={42} />
      </div>
    );
  }

  return (
    <div className="flex min-h-screen bg-[radial-gradient(circle_at_top,_rgba(187,140,81,0.18),_transparent_32%),linear-gradient(180deg,_#f7f2ea_0%,_#efe7d8_100%)]">
      <AdminSidebar
        onLogout={async () => {
          await logout();
          router.push("/admin/login");
        }}
      />

      <main className="flex-1 overflow-y-auto p-8 lg:p-10">
        <div className="mx-auto max-w-7xl space-y-8">
          <header className="rounded-[28px] border border-white/60 bg-white/70 p-7 shadow-[0_20px_60px_rgba(75,48,24,0.08)] backdrop-blur">
            <div className="flex flex-col gap-5 lg:flex-row lg:items-end lg:justify-between">
              <div className="space-y-2">
                <div className="inline-flex items-center gap-2 rounded-full border border-[#d8c0a0] bg-[#fff8ee] px-4 py-2 text-xs font-semibold uppercase tracking-[0.24em] text-[#8e5d34]">
                  <Sparkles size={14} />
                  Aqina Marketing OS
                </div>
                <h1 className="text-3xl font-black tracking-tight text-[#2b2018]">
                  CRM、Chatbot 与人工升级控制台
                </h1>
                <p className="max-w-3xl text-sm leading-6 text-[#6c5849]">
                  这里统一管理 Aqina 的正式 Prompt、套餐知识库、24 小时追单规则、PayNow 收款资料，以及需要人工接管的顾客队列。
                </p>
              </div>

              <div className="flex flex-wrap gap-3">
                <button
                  id="crm-refresh-button"
                  onClick={() => void loadData()}
                  className="inline-flex items-center gap-2 rounded-full border border-[#d6c2ab] bg-white px-5 py-3 text-sm font-semibold text-[#6c5849] transition hover:border-[#8e5d34] hover:text-[#8e5d34]"
                >
                  <RefreshCw size={16} />
                  刷新数据
                </button>
                <button
                  id="crm-save-button"
                  onClick={() => void handleSave()}
                  disabled={isSaving || !settings}
                  className="inline-flex items-center gap-2 rounded-full bg-[#2b2018] px-5 py-3 text-sm font-semibold text-[#f7f2ea] shadow-lg transition hover:bg-[#8e5d34] disabled:cursor-wait disabled:opacity-60"
                >
                  {isSaving ? <Loader2 className="animate-spin" size={16} /> : <Save size={16} />}
                  保存全部设置
                </button>
              </div>
            </div>
          </header>

          {isLoading || !settings ? (
            <div className="flex h-72 items-center justify-center rounded-[28px] border border-white/60 bg-white/70 shadow-[0_20px_60px_rgba(75,48,24,0.08)]">
              <Loader2 className="animate-spin text-[#8e5d34]" size={32} />
            </div>
          ) : (
            <div className="space-y-8">
              <section className="grid gap-4 md:grid-cols-4">
                <StatCard
                  icon={<ShieldAlert size={18} />}
                  title="待人工处理"
                  value={String(escalationStats.open)}
                  caption="Open escalations"
                  accent="from-[#402415] to-[#8f4f2b]"
                />
                <StatCard
                  icon={<Brain size={18} />}
                  title="Prompt 与规则"
                  value={`${RULE_FIELDS.length} 项`}
                  caption="Live CRM triggers"
                  accent="from-[#7a531f] to-[#b88c51]"
                />
                <StatCard
                  icon={<MessageCircle size={18} />}
                  title="FB 留言私讯"
                  value={settings.facebook_comment_automation.enabled ? "ON" : "OFF"}
                  caption={`${commentEvents.length} recent events`}
                  accent="from-[#33534a] to-[#5f927f]"
                />
                <StatCard
                  icon={<QrCode size={18} />}
                  title="PayNow 状态"
                  value={settings.payment.paynow.enabled ? "启用中" : "已关闭"}
                  caption={settings.payment.paynow.payment_reference_prefix || "AQINA"}
                  accent="from-[#36574b] to-[#60a28a]"
                />
              </section>

              <SectionShell
                icon={<Bot size={18} />}
                title="品牌人格与主 Prompt"
                subtitle="正式系统提示词、客服转人工安抚话术，都从这里统一下发。"
              >
                <div className="grid gap-6 lg:grid-cols-[1.35fr_0.65fr]">
                  <FieldBlock label="System Prompt">
                    <textarea
                      id="crm-system-prompt"
                      value={settings.system_prompt}
                      onChange={(event) =>
                        setSettings((current) =>
                          current ? { ...current, system_prompt: event.target.value } : current,
                        )
                      }
                      className={textareaClassName}
                      rows={22}
                    />
                  </FieldBlock>

                  <div className="space-y-6">
                    <FieldBlock label="Handoff Message">
                      <textarea
                        id="crm-handoff-message"
                        value={settings.handoff_message}
                        onChange={(event) =>
                          setSettings((current) =>
                            current ? { ...current, handoff_message: event.target.value } : current,
                          )
                        }
                        className={textareaClassName}
                        rows={6}
                      />
                    </FieldBlock>

                    <FieldBlock label="Legacy FAQ Keywords">
                      <div className="space-y-3">
                        {settings.faq.map((item, index) => (
                          <div key={`${item.keywords.join("-")}-${index}`} className="rounded-2xl border border-[#e8dccd] bg-[#fffaf4] p-4">
                            <input
                              value={item.keywords.join(", ")}
                              onChange={(event) => {
                                const keywords = event.target.value
                                  .split(",")
                                  .map((value) => value.trim())
                                  .filter(Boolean);
                                setSettings((current) => {
                                  if (!current) return current;
                                  const faq = [...current.faq];
                                  faq[index] = { ...faq[index], keywords };
                                  return { ...current, faq };
                                });
                              }}
                              className={inputClassName}
                              placeholder="delivery, shipping, 现货"
                            />
                            <textarea
                              value={item.response_zh}
                              onChange={(event) =>
                                setSettings((current) => {
                                  if (!current) return current;
                                  const faq = [...current.faq];
                                  faq[index] = { ...faq[index], response_zh: event.target.value };
                                  return { ...current, faq };
                                })
                              }
                              className={`${textareaClassName} mt-3`}
                              rows={3}
                            />
                          </div>
                        ))}
                      </div>
                    </FieldBlock>
                  </div>
                </div>
              </SectionShell>

              <SectionShell
                icon={<Package2 size={18} />}
                title="套餐与知识库"
                subtitle="固定四个配套，编辑文案与价格；知识库则提供 USP、FAQ 与医疗免责。"
              >
                <div className="space-y-8">
                  <div className="grid gap-4 xl:grid-cols-2">
                    {Object.values(settings.packages).map((pkg) => (
                      <div key={pkg.code} className="rounded-[24px] border border-[#e6d6c3] bg-[#fffaf4] p-5 shadow-sm">
                        <div className="mb-4 flex items-start justify-between gap-3">
                          <div>
                            <p className="text-xs font-semibold uppercase tracking-[0.22em] text-[#9f7b52]">
                              {pkg.code}
                            </p>
                            <h3 className="text-lg font-bold text-[#2b2018]">{pkg.name_zh}</h3>
                          </div>
                          <div className="rounded-full bg-[#2b2018] px-3 py-1 text-xs font-semibold text-[#f7f2ea]">
                            SGD {pkg.price_sgd.toFixed(2)}
                          </div>
                        </div>

                        <div className="grid gap-3 md:grid-cols-2">
                          <LabeledInput
                            label="中文名称"
                            value={pkg.name_zh}
                            onChange={(value) => updatePackage(pkg.code, "name_zh", value)}
                          />
                          <LabeledInput
                            label="英文名称"
                            value={pkg.name_en}
                            onChange={(value) => updatePackage(pkg.code, "name_en", value)}
                          />
                          <LabeledInput
                            label="价格 SGD"
                            type="number"
                            value={String(pkg.price_sgd)}
                            onChange={(value) => updatePackage(pkg.code, "price_sgd", Number(value))}
                          />
                          <LabeledInput
                            label="包数"
                            type="number"
                            value={String(pkg.pack_count)}
                            onChange={(value) => updatePackage(pkg.code, "pack_count", Number(value))}
                          />
                        </div>

                        <div className="mt-3 grid gap-3">
                          <LabeledTextarea
                            label="中文描述"
                            value={pkg.description_zh}
                            onChange={(value) => updatePackage(pkg.code, "description_zh", value)}
                          />
                          <LabeledTextarea
                            label="英文描述"
                            value={pkg.description_en}
                            onChange={(value) => updatePackage(pkg.code, "description_en", value)}
                          />
                        </div>

                        <div className="mt-4 flex flex-wrap gap-3 text-sm text-[#6c5849]">
                          <ToggleChip
                            active={pkg.hero}
                            label="主推配套"
                            onClick={() => updatePackage(pkg.code, "hero", !pkg.hero)}
                          />
                          <ToggleChip
                            active={pkg.free_shipping_eligible}
                            label="满足免邮"
                            onClick={() =>
                              updatePackage(pkg.code, "free_shipping_eligible", !pkg.free_shipping_eligible)
                            }
                          />
                        </div>
                      </div>
                    ))}
                  </div>

                  <div className="grid gap-6 lg:grid-cols-2">
                    <FieldBlock label="USPs（每行一条）">
                      <textarea
                        value={settings.knowledge_base.usps.join("\n")}
                        onChange={(event) =>
                          setSettings((current) =>
                            current
                              ? {
                                  ...current,
                                  knowledge_base: {
                                    ...current.knowledge_base,
                                    usps: event.target.value.split("\n").map((line) => line.trim()).filter(Boolean),
                                  },
                                }
                              : current,
                          )
                        }
                        className={textareaClassName}
                        rows={8}
                      />
                    </FieldBlock>
                    <FieldBlock label="FAQ（每行：问题 | 回答）">
                      <textarea
                        value={settings.knowledge_base.faq.map((item) => `${item.question} | ${item.answer}`).join("\n")}
                        onChange={(event) =>
                          setSettings((current) =>
                            current
                              ? {
                                  ...current,
                                  knowledge_base: {
                                    ...current.knowledge_base,
                                    faq: event.target.value
                                      .split("\n")
                                      .map((line) => line.trim())
                                      .filter(Boolean)
                                      .map((line) => {
                                        const [question, ...answerParts] = line.split("|");
                                        return {
                                          question: question?.trim() || "",
                                          answer: answerParts.join("|").trim(),
                                        };
                                      }),
                                  },
                                }
                              : current,
                          )
                        }
                        className={textareaClassName}
                        rows={8}
                      />
                    </FieldBlock>
                  </div>

                  <div className="grid gap-6 lg:grid-cols-3">
                    <LabeledTextarea
                      label="医疗免责"
                      value={settings.knowledge_base.medical_disclaimer}
                      onChange={(value) =>
                        setSettings((current) =>
                          current
                            ? {
                                ...current,
                                knowledge_base: { ...current.knowledge_base, medical_disclaimer: value },
                              }
                            : current,
                        )
                      }
                    />
                    <LabeledTextarea
                      label="物流说明"
                      value={settings.knowledge_base.logistics}
                      onChange={(value) =>
                        setSettings((current) =>
                          current
                            ? { ...current, knowledge_base: { ...current.knowledge_base, logistics: value } }
                            : current,
                        )
                      }
                    />
                    <LabeledTextarea
                      label="饮用建议与对比"
                      value={`${settings.knowledge_base.consumption}\n\n${settings.knowledge_base.comparisons}`}
                      onChange={(value) => {
                        const [consumption = "", ...rest] = value.split("\n\n");
                        setSettings((current) =>
                          current
                            ? {
                                ...current,
                                knowledge_base: {
                                  ...current.knowledge_base,
                                  consumption,
                                  comparisons: rest.join("\n\n"),
                                },
                              }
                            : current,
                        );
                      }}
                    />
                  </div>
                </div>
              </SectionShell>

              <SectionShell
                icon={<MessageCircle size={18} />}
                title="Facebook 留言转 Messenger"
                subtitle="只针对购买意图关键词评论发送一次 Messenger 破冰私讯；顾客回复后才进入 AI 销售流程。"
              >
                <div className="grid gap-6 xl:grid-cols-[0.9fr_1.1fr]">
                  <div className="space-y-4">
                    <ToggleRow
                      label="启用 Comment-to-Messenger"
                      value={settings.facebook_comment_automation.enabled}
                      onToggle={() =>
                        updateFacebookAutomation(
                          "enabled",
                          !settings.facebook_comment_automation.enabled,
                        )
                      }
                    />
                    <ToggleRow
                      label="发送公开回复"
                      value={settings.facebook_comment_automation.public_reply_enabled}
                      onToggle={() =>
                        updateFacebookAutomation(
                          "public_reply_enabled",
                          !settings.facebook_comment_automation.public_reply_enabled,
                        )
                      }
                    />
                    <ToggleRow
                      label="发送 Messenger 私讯"
                      value={settings.facebook_comment_automation.private_reply_enabled}
                      onToggle={() =>
                        updateFacebookAutomation(
                          "private_reply_enabled",
                          !settings.facebook_comment_automation.private_reply_enabled,
                        )
                      }
                    />
                    <ToggleRow
                      label="忽略 Page 自己留言"
                      value={settings.facebook_comment_automation.ignore_page_self_comments}
                      onToggle={() =>
                        updateFacebookAutomation(
                          "ignore_page_self_comments",
                          !settings.facebook_comment_automation.ignore_page_self_comments,
                        )
                      }
                    />
                    <FieldBlock label="触发关键词（逗号或换行分隔）">
                      <textarea
                        id="crm-facebook-comment-keywords"
                        value={settings.facebook_comment_automation.keywords.join(", ")}
                        onChange={(event) =>
                          updateFacebookAutomation(
                            "keywords",
                            splitKeywords(event.target.value),
                          )
                        }
                        className={textareaClassName}
                        rows={6}
                      />
                    </FieldBlock>
                  </div>

                  <div className="space-y-4">
                    <div className="grid gap-4 lg:grid-cols-2">
                      <FieldBlock label="公开回复文案">
                        <textarea
                          id="crm-facebook-public-reply"
                          value={settings.crm_follow_up_rules?.comment_hook?.public_reply?.instruction || ""}
                          onChange={(event) =>
                            updateRule("comment_hook", "public_reply", event.target.value)
                          }
                          className={textareaClassName}
                          rows={6}
                        />
                      </FieldBlock>
                      <FieldBlock label="Messenger 破冰私讯">
                        <textarea
                          id="crm-facebook-private-reply"
                          value={settings.crm_follow_up_rules?.comment_hook?.private_opening?.instruction || ""}
                          onChange={(event) =>
                            updateRule("comment_hook", "private_opening", event.target.value)
                          }
                          className={textareaClassName}
                          rows={6}
                        />
                      </FieldBlock>
                    </div>

                    <div className="rounded-[24px] border border-[#e7d8c7] bg-[#fffaf4] p-5">
                      <div className="mb-4 flex items-center justify-between gap-3">
                        <div>
                          <p className="text-xs font-semibold uppercase tracking-[0.24em] text-[#a07b56]">
                            Recent delivery
                          </p>
                          <h3 className="text-lg font-bold text-[#2b2018]">最近 FB 留言发送状态</h3>
                        </div>
                        <button
                          type="button"
                          onClick={() => void loadData()}
                          className="inline-flex items-center gap-2 rounded-full border border-[#d6c2ab] bg-white px-4 py-2 text-sm font-semibold text-[#6c5849] transition hover:border-[#8e5d34] hover:text-[#8e5d34]"
                        >
                          <RefreshCw size={14} />
                          刷新
                        </button>
                      </div>

                      {commentEvents.length === 0 ? (
                        <div className="rounded-2xl border border-dashed border-[#d9c5ad] bg-white p-5 text-sm text-[#6c5849]">
                          还没有 Facebook 评论自动化记录。
                        </div>
                      ) : (
                        <div className="space-y-3">
                          {commentEvents.slice(0, 6).map((item) => (
                            <div key={item.event_id} className="rounded-2xl border border-[#eadccd] bg-white p-4">
                              <div className="mb-2 flex flex-wrap items-center gap-2">
                                <StatusPill value={item.status} />
                                <StatusPill value={`Public: ${item.public_reply_status}`} muted />
                                <StatusPill value={`DM: ${item.private_reply_status}`} muted />
                              </div>
                              <p className="line-clamp-2 text-sm leading-6 text-[#2b2018]">
                                {item.comment_text || "无评论内容"}
                              </p>
                              <p className="mt-2 text-xs text-[#8a6c52]">
                                {item.from_name || "Facebook 用户"} · keyword: {item.matched_keyword || "-"}
                              </p>
                              {Object.keys(item.reply_errors || {}).length > 0 ? (
                                <p className="mt-2 line-clamp-2 text-xs text-[#9a3412]">
                                  {Object.entries(item.reply_errors)
                                    .map(([key, value]) => `${key}: ${value}`)
                                    .join(" | ")}
                                </p>
                              ) : null}
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              </SectionShell>

              <SectionShell
                icon={<Brain size={18} />}
                title="CRM 跟进规则矩阵"
                subtitle="每个触发节点都是独立文案入口，后端会把这些规则与对话上下文一起喂给 Gemini。"
              >
                <div className="grid gap-4 lg:grid-cols-2">
                  {RULE_FIELDS.map(([stage, key, label]) => (
                    <div key={`${stage}-${key}`} className="rounded-[24px] border border-[#e7d8c7] bg-[#fffaf4] p-5">
                      <p className="mb-2 text-xs font-semibold uppercase tracking-[0.24em] text-[#a07b56]">
                        {stage}
                      </p>
                      <h3 className="mb-3 text-lg font-bold text-[#2b2018]">{label}</h3>
                      <textarea
                        value={settings.crm_follow_up_rules?.[stage]?.[key]?.instruction || ""}
                        onChange={(event) => updateRule(stage, key, event.target.value)}
                        className={textareaClassName}
                        rows={6}
                      />
                    </div>
                  ))}
                </div>
              </SectionShell>

              <div className="grid gap-8 xl:grid-cols-[0.95fr_1.05fr]">
                <SectionShell
                  icon={<QrCode size={18} />}
                  title="PayNow 收款配置"
                  subtitle="全站已切到 PayNow-only；这里控制 QR、参考前缀和付款备注。"
                >
                  <div className="grid gap-4">
                    <ToggleRow
                      label="启用 PayNow"
                      value={settings.payment.paynow.enabled}
                      onToggle={() =>
                        setSettings((current) =>
                          current
                            ? {
                                ...current,
                                payment: {
                                  paynow: {
                                    ...current.payment.paynow,
                                    enabled: !current.payment.paynow.enabled,
                                  },
                                },
                              }
                            : current,
                        )
                      }
                    />
                    <LabeledInput
                      label="PayNow 户名"
                      value={settings.payment.paynow.account_name}
                      onChange={(value) =>
                        setSettings((current) =>
                          current
                            ? {
                                ...current,
                                payment: {
                                  paynow: { ...current.payment.paynow, account_name: value },
                                },
                              }
                            : current,
                        )
                      }
                    />
                    <LabeledInput
                      label="QR 图片 URL"
                      value={settings.payment.paynow.payment_qr_image}
                      onChange={(value) =>
                        setSettings((current) =>
                          current
                            ? {
                                ...current,
                                payment: {
                                  paynow: { ...current.payment.paynow, payment_qr_image: value },
                                },
                              }
                            : current,
                        )
                      }
                    />
                    <LabeledInput
                      label="QR Alt"
                      value={settings.payment.paynow.payment_qr_alt}
                      onChange={(value) =>
                        setSettings((current) =>
                          current
                            ? {
                                ...current,
                                payment: {
                                  paynow: { ...current.payment.paynow, payment_qr_alt: value },
                                },
                              }
                            : current,
                        )
                      }
                    />
                    <div className="grid gap-4 md:grid-cols-2">
                      <LabeledInput
                        label="Reference Prefix"
                        value={settings.payment.paynow.payment_reference_prefix}
                        onChange={(value) =>
                          setSettings((current) =>
                            current
                              ? {
                                  ...current,
                                  payment: {
                                    paynow: {
                                      ...current.payment.paynow,
                                      payment_reference_prefix: value,
                                    },
                                  },
                                }
                              : current,
                          )
                        }
                      />
                      <LabeledInput
                        label="付款备注"
                        value={settings.payment.paynow.payment_note}
                        onChange={(value) =>
                          setSettings((current) =>
                            current
                              ? {
                                  ...current,
                                  payment: {
                                    paynow: { ...current.payment.paynow, payment_note: value },
                                  },
                                }
                              : current,
                          )
                        }
                      />
                    </div>
                  </div>
                </SectionShell>

                <SectionShell
                  icon={<ShieldAlert size={18} />}
                  title="Escalation 与人工接管队列"
                  subtitle="当顾客投诉、退款或要求人工时，系统会暂停自动化并发 WhatsApp 模板给你的私人号码。"
                >
                  <div className="grid gap-4">
                    <ToggleRow
                      label="启用人工升级"
                      value={settings.escalation.enabled}
                      onToggle={() =>
                        setSettings((current) =>
                          current
                            ? {
                                ...current,
                                escalation: {
                                  ...current.escalation,
                                  enabled: !current.escalation.enabled,
                                },
                              }
                            : current,
                        )
                      }
                    />
                    <LabeledInput
                      label="私人 WhatsApp 号码"
                      value={settings.escalation.private_whatsapp_number}
                      onChange={(value) =>
                        setSettings((current) =>
                          current
                            ? {
                                ...current,
                                escalation: {
                                  ...current.escalation,
                                  private_whatsapp_number: value,
                                },
                              }
                            : current,
                        )
                      }
                    />
                    <LabeledInput
                      label="模板名称"
                      value={settings.escalation.whatsapp_template_name}
                      onChange={(value) =>
                        setSettings((current) =>
                          current
                            ? {
                                ...current,
                                escalation: {
                                  ...current.escalation,
                                  whatsapp_template_name: value,
                                },
                              }
                            : current,
                        )
                      }
                    />
                    <ToggleRow
                      label="转人工后暂停自动化"
                      value={settings.escalation.pause_automation_on_handoff}
                      onToggle={() =>
                        setSettings((current) =>
                          current
                            ? {
                                ...current,
                                escalation: {
                                  ...current.escalation,
                                  pause_automation_on_handoff:
                                    !current.escalation.pause_automation_on_handoff,
                                },
                              }
                            : current,
                        )
                      }
                    />
                  </div>

                  <div className="mt-6 space-y-3">
                    {escalations.length === 0 ? (
                      <div className="rounded-2xl border border-dashed border-[#d9c5ad] bg-[#fffaf4] p-6 text-sm text-[#6c5849]">
                        目前没有待处理的 escalation。
                      </div>
                    ) : (
                      escalations.map((item) => (
                        <div key={item.escalation_id} className="rounded-[24px] border border-[#e6d7c7] bg-[#fffaf4] p-5">
                          <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
                            <div className="space-y-2">
                              <div className="inline-flex rounded-full bg-[#2b2018] px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.2em] text-[#f7f2ea]">
                                {item.status}
                              </div>
                              <h3 className="text-base font-bold text-[#2b2018]">{item.reason}</h3>
                              <p className="text-sm leading-6 text-[#6c5849]">{item.latest_customer_message || "无附加留言"}</p>
                              <p className="text-xs uppercase tracking-[0.2em] text-[#9a7a57]">
                                {item.private_whatsapp_number || "未配置私人号码"}
                              </p>
                            </div>

                            <div className="flex flex-wrap gap-3">
                              {item.status !== "acknowledged" && item.status !== "resolved" && (
                                <button
                                  onClick={() => void handleAcknowledge(item.escalation_id)}
                                  className="rounded-full border border-[#d7c3ab] bg-white px-4 py-2 text-sm font-semibold text-[#6c5849] transition hover:border-[#8e5d34] hover:text-[#8e5d34]"
                                >
                                  Acknowledge
                                </button>
                              )}
                              {item.status !== "resolved" && (
                                <button
                                  onClick={() => void handleResolve(item.escalation_id)}
                                  className="rounded-full bg-[#2b2018] px-4 py-2 text-sm font-semibold text-[#f7f2ea] transition hover:bg-[#8e5d34]"
                                >
                                  Resolve & Resume
                                </button>
                              )}
                            </div>
                          </div>
                        </div>
                      ))
                    )}
                  </div>
                </SectionShell>
              </div>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}

function StatCard({
  icon,
  title,
  value,
  caption,
  accent,
}: {
  icon: ReactNode;
  title: string;
  value: string;
  caption: string;
  accent: string;
}) {
  return (
    <div className="rounded-[26px] border border-white/70 bg-white/75 p-5 shadow-[0_18px_45px_rgba(75,48,24,0.08)] backdrop-blur">
      <div className={`mb-4 inline-flex rounded-2xl bg-gradient-to-br ${accent} p-3 text-white shadow-lg`}>
        {icon}
      </div>
      <p className="text-sm font-semibold uppercase tracking-[0.24em] text-[#9a7a57]">{title}</p>
      <p className="mt-2 text-3xl font-black tracking-tight text-[#2b2018]">{value}</p>
      <p className="mt-1 text-sm text-[#6c5849]">{caption}</p>
    </div>
  );
}

function SectionShell({
  icon,
  title,
  subtitle,
  children,
}: {
  icon: ReactNode;
  title: string;
  subtitle: string;
  children: ReactNode;
}) {
  return (
    <section className="rounded-[30px] border border-white/70 bg-white/75 p-7 shadow-[0_24px_70px_rgba(75,48,24,0.08)] backdrop-blur">
      <div className="mb-6 flex items-start gap-4">
        <div className="rounded-2xl bg-[#2b2018] p-3 text-[#f7f2ea] shadow-lg">{icon}</div>
        <div>
          <h2 className="text-2xl font-black tracking-tight text-[#2b2018]">{title}</h2>
          <p className="mt-1 max-w-3xl text-sm leading-6 text-[#6c5849]">{subtitle}</p>
        </div>
      </div>
      {children}
    </section>
  );
}

function FieldBlock({
  label,
  children,
}: {
  label: string;
  children: ReactNode;
}) {
  return (
    <div>
      <p className="mb-3 text-xs font-semibold uppercase tracking-[0.24em] text-[#9d7c58]">{label}</p>
      {children}
    </div>
  );
}

function LabeledInput({
  label,
  value,
  onChange,
  type = "text",
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
  type?: string;
}) {
  return (
    <label className="block">
      <span className="mb-2 block text-xs font-semibold uppercase tracking-[0.2em] text-[#9d7c58]">{label}</span>
      <input type={type} value={value} onChange={(event) => onChange(event.target.value)} className={inputClassName} />
    </label>
  );
}

function LabeledTextarea({
  label,
  value,
  onChange,
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
}) {
  return (
    <label className="block">
      <span className="mb-2 block text-xs font-semibold uppercase tracking-[0.2em] text-[#9d7c58]">{label}</span>
      <textarea value={value} onChange={(event) => onChange(event.target.value)} className={textareaClassName} rows={6} />
    </label>
  );
}

function ToggleRow({
  label,
  value,
  onToggle,
}: {
  label: string;
  value: boolean;
  onToggle: () => void;
}) {
  return (
    <button
      type="button"
      onClick={onToggle}
      className="flex items-center justify-between rounded-2xl border border-[#e6d6c4] bg-[#fffaf4] px-4 py-4 text-left transition hover:border-[#8e5d34]"
    >
      <span className="text-sm font-semibold text-[#2b2018]">{label}</span>
      <span
        className={`inline-flex rounded-full px-3 py-1 text-xs font-semibold uppercase tracking-[0.2em] ${
          value ? "bg-[#2b2018] text-[#f7f2ea]" : "bg-[#eadfd1] text-[#7a614d]"
        }`}
      >
        {value ? "ON" : "OFF"}
      </span>
    </button>
  );
}

function ToggleChip({
  active,
  label,
  onClick,
}: {
  active: boolean;
  label: string;
  onClick: () => void;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={`rounded-full px-3 py-2 text-xs font-semibold uppercase tracking-[0.18em] transition ${
        active ? "bg-[#2b2018] text-[#f7f2ea]" : "bg-[#f0e4d5] text-[#7a614d]"
      }`}
    >
      {label}
    </button>
  );
}

function StatusPill({ value, muted = false }: { value: string; muted?: boolean }) {
  return (
    <span
      className={`inline-flex rounded-full px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.16em] ${
        muted ? "bg-[#eadfd1] text-[#7a614d]" : "bg-[#2b2018] text-[#f7f2ea]"
      }`}
    >
      {value || "pending"}
    </span>
  );
}

function splitKeywords(value: string): string[] {
  return value
    .split(/[\n,]/)
    .map((item) => item.trim())
    .filter(Boolean);
}

const inputClassName =
  "w-full rounded-2xl border border-[#e4d4c2] bg-white px-4 py-3 text-sm text-[#2b2018] outline-none transition focus:border-[#8e5d34] focus:ring-4 focus:ring-[#b88c51]/15";

const textareaClassName =
  "w-full rounded-2xl border border-[#e4d4c2] bg-white px-4 py-3 text-sm leading-6 text-[#2b2018] outline-none transition focus:border-[#8e5d34] focus:ring-4 focus:ring-[#b88c51]/15";
