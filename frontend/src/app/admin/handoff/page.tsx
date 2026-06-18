"use client";

import { useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import {
  Archive,
  CheckCircle2,
  ExternalLink,
  Loader2,
  MessageSquareText,
  RefreshCw,
  ShieldAlert,
} from "lucide-react";

import AdminSidebar from "@/components/admin/AdminSidebar";
import { isAdminUser, logout, subscribeToAuthChanges } from "@/lib/auth-service";
import {
  EscalationRecord,
  acknowledgeEscalation,
  archiveEscalation,
  listEscalations,
  remarkEscalation,
  resolveEscalation,
} from "@/lib/backend-marketing-service";

export default function AdminHandoffPage() {
  const router = useRouter();
  const [isAuthLoading, setIsAuthLoading] = useState(true);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [escalations, setEscalations] = useState<EscalationRecord[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [remarkDraft, setRemarkDraft] = useState("");

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

  const selected = useMemo(
    () => escalations.find((item) => item.escalation_id === selectedId) || escalations[0] || null,
    [escalations, selectedId],
  );

  const stats = useMemo(
    () => ({
      open: escalations.filter((item) => item.status === "open").length,
      acknowledged: escalations.filter((item) => item.status === "acknowledged").length,
      resolved: escalations.filter((item) => item.status === "resolved").length,
    }),
    [escalations],
  );

  useEffect(() => {
    setRemarkDraft(selected?.remark || "");
  }, [selected?.escalation_id, selected?.remark]);

  async function loadData() {
    setIsLoading(true);
    try {
      const rows = await listEscalations();
      setEscalations(rows);
      setSelectedId((current) =>
        current && rows.some((item) => item.escalation_id === current)
          ? current
          : rows[0]?.escalation_id || null,
      );
    } finally {
      setIsLoading(false);
    }
  }

  async function handleAcknowledge(escalationId: string) {
    setIsSaving(true);
    try {
      await acknowledgeEscalation(escalationId);
      await loadData();
    } finally {
      setIsSaving(false);
    }
  }

  async function handleResolve(escalationId: string) {
    setIsSaving(true);
    try {
      await resolveEscalation(escalationId);
      await loadData();
    } finally {
      setIsSaving(false);
    }
  }

  async function handleRemark(escalationId: string) {
    if (!remarkDraft.trim()) return;
    setIsSaving(true);
    try {
      await remarkEscalation(escalationId, remarkDraft.trim());
      await loadData();
    } finally {
      setIsSaving(false);
    }
  }

  async function handleArchive(escalationId: string) {
    setIsSaving(true);
    try {
      await archiveEscalation(escalationId, remarkDraft.trim() || undefined);
      await loadData();
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
        <header className="flex shrink-0 flex-col gap-4 border-b border-[#d9d2c4] pb-5 xl:flex-row xl:items-end xl:justify-between">
          <div>
            <h1 className="text-3xl font-bold text-[#10251d]">Handoff Queue</h1>
          </div>
          <div className="flex flex-wrap gap-2">
            <MetricPill label="Open" value={stats.open} />
            <MetricPill label="Acknowledged" value={stats.acknowledged} />
            <MetricPill label="Resolved" value={stats.resolved} />
            <button
              id="handoff-refresh-button"
              onClick={() => void loadData()}
              className="inline-flex items-center gap-2 rounded-md border border-[#cfd8d2] bg-white px-4 py-2 text-sm font-semibold text-[#294239] hover:border-[#236b50]"
            >
              <RefreshCw size={16} />
              刷新
            </button>
          </div>
        </header>

        {isLoading ? (
          <div className="flex flex-1 items-center justify-center">
            <Loader2 className="animate-spin text-[#236b50]" size={32} />
          </div>
        ) : (
          <section className="grid min-h-0 flex-1 gap-4 pt-5 xl:grid-cols-[420px_minmax(0,1fr)]">
            <div className="flex min-h-0 flex-col overflow-hidden rounded-md border border-[#ddd5ca] bg-white">
              <div className="flex shrink-0 items-center justify-between border-b border-[#ebe5dc] p-4">
                <h2 className="text-base font-bold">人工接管</h2>
                <span className="text-xs font-semibold text-[#6b746f]">{escalations.length} active</span>
              </div>
              <div className="min-h-0 flex-1 overflow-y-auto">
                {escalations.length === 0 ? (
                  <p className="p-4 text-sm text-[#6b746f]">目前没有待处理的 handoff。</p>
                ) : (
                  escalations.map((item) => (
                    <button
                      key={item.escalation_id}
                      id={`handoff-row-${item.escalation_id}`}
                      onClick={() => setSelectedId(item.escalation_id)}
                      className={`block w-full border-b border-[#f0ebe4] p-4 text-left hover:bg-[#f7faf8] ${
                        selected?.escalation_id === item.escalation_id ? "bg-[#edf7f2]" : ""
                      }`}
                    >
                      <div className="flex items-start justify-between gap-3">
                        <div className="min-w-0">
                          <p className="truncate text-sm font-bold text-[#14231d]">{item.reason}</p>
                          <p className="mt-1 line-clamp-2 text-xs leading-5 text-[#69746e]">
                            {item.latest_customer_message || "No customer message"}
                          </p>
                        </div>
                        <StatusPill status={item.status} />
                      </div>
                      {item.remark && (
                        <p className="mt-3 rounded bg-[#f2eee7] px-2 py-1 text-xs text-[#5d6a64]">
                          {item.remark}
                        </p>
                      )}
                    </button>
                  ))
                )}
              </div>
            </div>

            <div className="min-h-0 overflow-hidden rounded-md border border-[#ddd5ca] bg-white">
              {selected ? (
                <div className="flex h-full min-h-0 flex-col">
                  <div className="flex shrink-0 items-start justify-between gap-4 border-b border-[#ebe5dc] p-4">
                    <div>
                      <div className="mb-2 inline-flex items-center gap-2 rounded-md bg-[#fff0e8] px-2 py-1 text-xs font-bold text-[#9b321c]">
                        <ShieldAlert size={14} />
                        {selected.status}
                      </div>
                      <h2 className="text-xl font-bold text-[#10251d]">{selected.reason}</h2>
                      <p className="mt-1 text-xs text-[#6b746f]">{selected.escalation_id}</p>
                    </div>
                    {selected.conversation_id && (
                      <button
                        id="handoff-open-inbox-button"
                        onClick={() => router.push(`/admin/inbox?conversation=${selected.conversation_id}`)}
                        className="inline-flex items-center gap-2 rounded-md border border-[#cfd8d2] bg-white px-4 py-2 text-sm font-semibold text-[#294239] hover:border-[#236b50]"
                      >
                        <ExternalLink size={16} />
                        Open Inbox
                      </button>
                    )}
                  </div>

                  <div className="min-h-0 flex-1 overflow-y-auto p-4">
                    <div className="grid gap-3 md:grid-cols-2">
                      <InfoRow label="Contact ID" value={selected.contact_id} />
                      <InfoRow label="Conversation" value={selected.conversation_id || "-"} />
                      <InfoRow
                        label="Alert numbers"
                        value={
                          selected.private_whatsapp_numbers?.length
                            ? selected.private_whatsapp_numbers.join(", ")
                            : selected.private_whatsapp_number || "-"
                        }
                      />
                      <InfoRow label="Template" value={selected.template_name || "-"} />
                      <InfoRow label="Notified" value={formatTime(selected.notified_at)} />
                      <InfoRow label="Resolved" value={formatTime(selected.resolved_at || undefined)} />
                    </div>

                    <div className="mt-4 rounded-md border border-[#e5ddd1] bg-[#faf8f3] p-4">
                      <h3 className="mb-2 text-sm font-bold text-[#10251d]">Customer message</h3>
                      <p className="whitespace-pre-wrap text-sm leading-6 text-[#35473f]">
                        {selected.latest_customer_message || "No customer message"}
                      </p>
                    </div>

                    <label className="mt-4 grid gap-2 text-sm font-semibold text-[#10251d]">
                      Remark
                      <textarea
                        id="handoff-remark-textarea"
                        value={remarkDraft}
                        onChange={(event) => setRemarkDraft(event.target.value)}
                        rows={5}
                        className="resize-none rounded-md border border-[#d8d1c7] bg-white p-3 text-sm text-[#14231d] outline-none focus:border-[#236b50]"
                        placeholder="记录人工处理备注..."
                      />
                    </label>
                  </div>

                  <div className="flex shrink-0 flex-wrap gap-2 border-t border-[#ebe5dc] p-4">
                    {selected.status === "open" && (
                      <button
                        id="handoff-acknowledge-button"
                        onClick={() => void handleAcknowledge(selected.escalation_id)}
                        disabled={isSaving}
                        className="inline-flex items-center gap-2 rounded-md border border-[#cfd8d2] bg-white px-4 py-2 text-sm font-bold text-[#294239] disabled:opacity-50"
                      >
                        <MessageSquareText size={16} />
                        Acknowledge
                      </button>
                    )}
                    <button
                      id="handoff-save-remark-button"
                      onClick={() => void handleRemark(selected.escalation_id)}
                      disabled={isSaving || !remarkDraft.trim()}
                      className="inline-flex items-center gap-2 rounded-md border border-[#236b50] bg-white px-4 py-2 text-sm font-bold text-[#236b50] disabled:opacity-50"
                    >
                      Save Remark
                    </button>
                    {selected.status !== "resolved" && (
                      <button
                        id="handoff-resolve-button"
                        onClick={() => void handleResolve(selected.escalation_id)}
                        disabled={isSaving}
                        className="inline-flex items-center gap-2 rounded-md bg-[#123d2f] px-4 py-2 text-sm font-bold text-white disabled:opacity-50"
                      >
                        <CheckCircle2 size={16} />
                        Resolve & Resume
                      </button>
                    )}
                    <button
                      id="handoff-archive-button"
                      onClick={() => void handleArchive(selected.escalation_id)}
                      disabled={isSaving}
                      className="inline-flex items-center gap-2 rounded-md border border-[#c95b4a] bg-white px-4 py-2 text-sm font-bold text-[#a84133] disabled:opacity-50"
                    >
                      <Archive size={16} />
                      Archive
                    </button>
                  </div>
                </div>
              ) : (
                <div className="flex h-full items-center justify-center p-8 text-sm text-[#6b746f]">
                  Select a handoff case.
                </div>
              )}
            </div>
          </section>
        )}
      </main>
    </div>
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

function InfoRow({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-md border border-[#e5ddd1] bg-white p-3">
      <p className="text-xs font-semibold text-[#6b746f]">{label}</p>
      <p className="mt-1 break-words text-sm font-bold text-[#14231d]">{value}</p>
    </div>
  );
}

function StatusPill({ status }: { status: EscalationRecord["status"] }) {
  const className =
    status === "open"
      ? "bg-[#fff0e8] text-[#a84133]"
      : status === "acknowledged"
        ? "bg-[#f2eee7] text-[#6b746f]"
        : "bg-[#e8f8ef] text-[#236b50]";
  return <span className={`rounded px-2 py-1 text-[11px] font-bold ${className}`}>{status}</span>;
}

function formatTime(value?: string) {
  if (!value) return "-";
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) return String(value);
  return parsed.toLocaleString("en-SG", {
    month: "short",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  });
}
