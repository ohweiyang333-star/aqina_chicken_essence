"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import {
  subscribeToAuthChanges,
  isUserAdmin,
  logout,
} from "@/lib/auth-service";
import {
  Loader2,
  MessageSquare,
  Clock,
  Users,
  TrendingUp,
  Sparkles,
  Save,
  Plus,
  Trash2,
} from "lucide-react";
import AdminSidebar from "@/components/admin/AdminSidebar";

interface FAQItem {
  keywords: string[];
  response_en: string;
  response_zh: string;
  recommendProductId?: string;
}

interface ChatbotSettings {
  faq: FAQItem[];
  abandoned_cart_message: {
    template: string;
    discountCode: string;
    delayMinutes: number;
  };
  replenishment_reminder: {
    enabled: boolean;
    template_en: string;
    template_zh: string;
    triggerDays: number[];
  };
}

export default function AdminCRMPage() {
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [isAuthLoading, setIsAuthLoading] = useState(true);
  const [settings, setSettings] = useState<ChatbotSettings>({
    faq: [],
    abandoned_cart_message: {
      template: "Hi [Name]! 您的 Aqina 滴鸡精还在购物车中。",
      discountCode: "HEALTHY10",
      delayMinutes: 15,
    },
    replenishment_reminder: {
      enabled: true,
      template_en: "Hi [Name]! Your Aqina chicken essence is running low.",
      template_zh: "Hi [Name]! 您的滴鸡精库存快用完啦。",
      triggerDays: [12, 25],
    },
  });
  const [newFaq, setNewFaq] = useState<FAQItem>({
    keywords: [],
    response_en: "",
    response_zh: "",
  });
  const router = useRouter();

  useEffect(() => {
    const unsubscribe = subscribeToAuthChanges((user) => {
      if (!user || !isUserAdmin(user)) {
        router.push("/admin/login");
      } else {
        setIsAuthLoading(false);
        fetchSettings();
      }
    });
    return () => unsubscribe();
  }, [router]);

  const fetchSettings = async () => {
    setIsLoading(true);
    try {
      const response = await fetch("/api/admin/chatbot");
      if (response.ok) {
        const data = await response.json();
        setSettings(data);
      }
    } catch (error) {
      console.error("Failed to fetch chatbot settings");
    } finally {
      setIsLoading(false);
    }
  };

  const handleSave = async () => {
    setIsSaving(true);
    try {
      const response = await fetch("/api/admin/chatbot", {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(settings),
      });
      if (response.ok) {
        alert("Settings saved successfully!");
      }
    } catch (error) {
      alert("Failed to save settings");
    } finally {
      setIsSaving(false);
    }
  };

  const handleAddFaq = () => {
    if (
      newFaq.keywords.length > 0 &&
      newFaq.response_en &&
      newFaq.response_zh
    ) {
      setSettings({
        ...settings,
        faq: [...settings.faq, newFaq],
      });
      setNewFaq({ keywords: [], response_en: "", response_zh: "" });
    }
  };

  const handleDeleteFaq = (index: number) => {
    setSettings({
      ...settings,
      faq: settings.faq.filter((_, i) => i !== index),
    });
  };

  if (isAuthLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[#F8F9FA]">
        <Loader2 className="animate-spin text-primary" size={48} />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#F8F9FA] flex">
      <AdminSidebar
        onLogout={async () => {
          await logout();
          router.push("/admin/login");
        }}
      />

      {/* Main Content */}
      <main className="flex-1 p-10 overflow-y-auto">
        {/* Header */}
        <header className="mb-10">
          <div className="flex items-center gap-3 mb-2">
            <div className="w-12 h-12 rounded-xl gradient-gold flex items-center justify-center shadow-lg">
              <Sparkles size={24} className="text-white" />
            </div>
            <div>
              <h1 className="text-3xl font-bold text-charcoal tracking-tight">
                CRM & AI Intelligence
              </h1>
              <p className="text-charcoal/50 text-sm">
                Manage customer engagement and automated recovery
              </p>
            </div>
          </div>
        </header>

        {isLoading ? (
          <div className="h-64 flex items-center justify-center">
            <Loader2 className="animate-spin text-charcoal/20" size={32} />
          </div>
        ) : (
          <div className="space-y-8">
            {/* Stats Cards */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div className="bg-white rounded-2xl p-6 shadow-sm border border-charcoal/5">
                <div className="flex items-center justify-between mb-4">
                  <div className="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center">
                    <TrendingUp className="text-primary" size={20} />
                  </div>
                  <span className="text-xs font-bold text-green-600 bg-green-50 px-2 py-1 rounded-full">
                    +12%
                  </span>
                </div>
                <p className="text-2xl font-bold text-charcoal">SGD 1,200</p>
                <p className="text-xs text-charcoal/50 mt-1">
                  AI Recovery Revenue
                </p>
              </div>

              <div className="bg-white rounded-2xl p-6 shadow-sm border border-charcoal/5">
                <div className="flex items-center justify-between mb-4">
                  <div className="w-10 h-10 rounded-lg bg-blue-50 flex items-center justify-center">
                    <MessageSquare className="text-blue-600" size={20} />
                  </div>
                </div>
                <p className="text-2xl font-bold text-charcoal">
                  {settings.faq.length}
                </p>
                <p className="text-xs text-charcoal/50 mt-1">
                  Active FAQ Responses
                </p>
              </div>

              <div className="bg-white rounded-2xl p-6 shadow-sm border border-charcoal/5">
                <div className="flex items-center justify-between mb-4">
                  <div className="w-10 h-10 rounded-lg bg-purple-50 flex items-center justify-center">
                    <Clock className="text-purple-600" size={20} />
                  </div>
                </div>
                <p className="text-2xl font-bold text-charcoal">
                  {settings.abandoned_cart_message.delayMinutes}m
                </p>
                <p className="text-xs text-charcoal/50 mt-1">
                  Cart Abandonment Delay
                </p>
              </div>
            </div>

            {/* AI Recovery Settings */}
            <section className="bg-white rounded-2xl p-6 shadow-sm border border-charcoal/5">
              <div className="flex items-center gap-3 mb-6">
                <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-primary to-accent flex items-center justify-center">
                  <MessageSquare size={20} className="text-white" />
                </div>
                <div>
                  <h2 className="text-xl font-bold text-charcoal">
                    AI Recovery Engine
                  </h2>
                  <p className="text-sm text-charcoal/50">
                    WhatsApp cart abandonment & replenishment automation
                  </p>
                </div>
              </div>

              <div className="space-y-6">
                {/* Cart Abandonment */}
                <div className="p-4 rounded-xl bg-ivory border border-charcoal/10">
                  <h3 className="font-bold text-charcoal mb-4">
                    Cart Abandonment Recovery
                  </h3>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <label className="block text-xs font-bold text-charcoal/50 uppercase tracking-wider mb-2">
                        Message Template
                      </label>
                      <textarea
                        value={settings.abandoned_cart_message.template}
                        onChange={(e) =>
                          setSettings({
                            ...settings,
                            abandoned_cart_message: {
                              ...settings.abandoned_cart_message,
                              template: e.target.value,
                            },
                          })
                        }
                        className="w-full p-3 rounded-lg border border-charcoal/20 text-sm"
                        rows={3}
                      />
                    </div>

                    <div className="space-y-4">
                      <div>
                        <label className="block text-xs font-bold text-charcoal/50 uppercase tracking-wider mb-2">
                          Discount Code
                        </label>
                        <input
                          type="text"
                          value={settings.abandoned_cart_message.discountCode}
                          onChange={(e) =>
                            setSettings({
                              ...settings,
                              abandoned_cart_message: {
                                ...settings.abandoned_cart_message,
                                discountCode: e.target.value,
                              },
                            })
                          }
                          className="w-full p-3 rounded-lg border border-charcoal/20 text-sm"
                        />
                      </div>

                      <div>
                        <label className="block text-xs font-bold text-charcoal/50 uppercase tracking-wider mb-2">
                          Delay (minutes)
                        </label>
                        <select
                          value={settings.abandoned_cart_message.delayMinutes}
                          onChange={(e) =>
                            setSettings({
                              ...settings,
                              abandoned_cart_message: {
                                ...settings.abandoned_cart_message,
                                delayMinutes: parseInt(e.target.value),
                              },
                            })
                          }
                          className="w-full p-3 rounded-lg border border-charcoal/20 text-sm"
                        >
                          <option value={15}>15 minutes</option>
                          <option value={30}>30 minutes</option>
                          <option value={60}>1 hour</option>
                          <option value={1440}>24 hours</option>
                        </select>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Replenishment Reminder */}
                <div className="p-4 rounded-xl bg-ivory border border-charcoal/10">
                  <div className="flex items-center justify-between mb-4">
                    <h3 className="font-bold text-charcoal">
                      Replenishment Reminder
                    </h3>
                    <button
                      onClick={() =>
                        setSettings({
                          ...settings,
                          replenishment_reminder: {
                            ...settings.replenishment_reminder,
                            enabled: !settings.replenishment_reminder.enabled,
                          },
                        })
                      }
                      className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                        settings.replenishment_reminder.enabled
                          ? "bg-primary"
                          : "bg-gray-300"
                      }`}
                    >
                      <span
                        className={`inline-block h-5 w-5 transform rounded-full bg-white transition ${
                          settings.replenishment_reminder.enabled
                            ? "translate-x-6"
                            : "translate-x-1"
                        }`}
                      />
                    </button>
                  </div>

                  {settings.replenishment_reminder.enabled && (
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div>
                        <label className="block text-xs font-bold text-charcoal/50 uppercase tracking-wider mb-2">
                          English Template
                        </label>
                        <textarea
                          value={settings.replenishment_reminder.template_en}
                          onChange={(e) =>
                            setSettings({
                              ...settings,
                              replenishment_reminder: {
                                ...settings.replenishment_reminder,
                                template_en: e.target.value,
                              },
                            })
                          }
                          className="w-full p-3 rounded-lg border border-charcoal/20 text-sm"
                          rows={2}
                        />
                      </div>

                      <div>
                        <label className="block text-xs font-bold text-charcoal/50 uppercase tracking-wider mb-2">
                          Chinese Template
                        </label>
                        <textarea
                          value={settings.replenishment_reminder.template_zh}
                          onChange={(e) =>
                            setSettings({
                              ...settings,
                              replenishment_reminder: {
                                ...settings.replenishment_reminder,
                                template_zh: e.target.value,
                              },
                            })
                          }
                          className="w-full p-3 rounded-lg border border-charcoal/20 text-sm"
                          rows={2}
                        />
                      </div>
                    </div>
                  )}
                </div>
              </div>
            </section>

            {/* FAQ Management */}
            <section className="bg-white rounded-2xl p-6 shadow-sm border border-charcoal/5">
              <div className="flex items-center justify-between mb-6">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-lg bg-blue-50 flex items-center justify-center">
                    <MessageSquare size={20} className="text-blue-600" />
                  </div>
                  <div>
                    <h2 className="text-xl font-bold text-charcoal">
                      FAQ Management
                    </h2>
                    <p className="text-sm text-charcoal/50">
                      Manage automated chatbot responses
                    </p>
                  </div>
                </div>
              </div>

              {/* Existing FAQs */}
              <div className="space-y-3 mb-6">
                {settings.faq.map((faq, index) => (
                  <div
                    key={index}
                    className="p-4 rounded-lg border border-charcoal/10 bg-ivory/50"
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex flex-wrap gap-2 mb-2">
                          {faq.keywords.map((keyword, i) => (
                            <span
                              key={i}
                              className="text-xs bg-primary/10 text-primary px-2 py-1 rounded-full"
                            >
                              {keyword}
                            </span>
                          ))}
                        </div>
                        <p className="text-sm text-charcoal/70">
                          {faq.response_en}
                        </p>
                      </div>
                      <button
                        onClick={() => handleDeleteFaq(index)}
                        className="text-red-500 hover:text-red-700 ml-4"
                      >
                        <Trash2 size={16} />
                      </button>
                    </div>
                  </div>
                ))}
              </div>

              {/* Add New FAQ */}
              <div className="p-4 rounded-lg border-2 border-dashed border-charcoal/20">
                <h4 className="font-bold text-charcoal mb-4">
                  Add New FAQ Response
                </h4>

                <div className="space-y-4">
                  <div>
                    <label className="block text-xs font-bold text-charcoal/50 uppercase tracking-wider mb-2">
                      Keywords (comma separated)
                    </label>
                    <input
                      type="text"
                      placeholder="e.g., price, shipping, discount"
                      value={newFaq.keywords.join(", ")}
                      onChange={(e) =>
                        setNewFaq({
                          ...newFaq,
                          keywords: e.target.value
                            .split(",")
                            .map((k) => k.trim())
                            .filter(Boolean),
                        })
                      }
                      className="w-full p-3 rounded-lg border border-charcoal/20 text-sm"
                    />
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <label className="block text-xs font-bold text-charcoal/50 uppercase tracking-wider mb-2">
                        English Response
                      </label>
                      <textarea
                        value={newFaq.response_en}
                        onChange={(e) =>
                          setNewFaq({ ...newFaq, response_en: e.target.value })
                        }
                        className="w-full p-3 rounded-lg border border-charcoal/20 text-sm"
                        rows={3}
                        placeholder="Enter response in English..."
                      />
                    </div>

                    <div>
                      <label className="block text-xs font-bold text-charcoal/50 uppercase tracking-wider mb-2">
                        Chinese Response
                      </label>
                      <textarea
                        value={newFaq.response_zh}
                        onChange={(e) =>
                          setNewFaq({ ...newFaq, response_zh: e.target.value })
                        }
                        className="w-full p-3 rounded-lg border border-charcoal/20 text-sm"
                        rows={3}
                        placeholder="输入中文回复..."
                      />
                    </div>
                  </div>

                  <button
                    onClick={handleAddFaq}
                    className="flex items-center gap-2 px-4 py-2 rounded-lg bg-primary text-white font-bold hover:bg-primary/80 transition-all"
                  >
                    <Plus size={16} />
                    Add FAQ
                  </button>
                </div>
              </div>
            </section>

            {/* Save Button */}
            <div className="flex justify-end">
              <button
                onClick={handleSave}
                disabled={isSaving}
                className="flex items-center gap-2 px-6 py-3 rounded-xl bg-charcoal text-ivory font-bold hover:bg-primary transition-all disabled:opacity-50"
              >
                {isSaving ? (
                  <Loader2 size={20} className="animate-spin" />
                ) : (
                  <Save size={20} />
                )}
                {isSaving ? "Saving..." : "Save All Settings"}
              </button>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
