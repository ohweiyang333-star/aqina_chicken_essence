"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import {
  subscribeToAuthChanges,
  isAdminUser,
  logout,
} from "@/lib/auth-service";
import {
  getOrders,
  getOrderContactContext,
  sendOrderWhatsAppNotification,
  updateOrderPaymentStatus,
  updateOrderStatus,
  Order,
  OrderContactContext,
  OrderContactTemplate,
  OrderPaymentStatus,
} from "@/lib/order-service";
import {
  Loader2,
  CalendarDays,
  Clock,
  ExternalLink,
  AlertTriangle,
  Truck,
  CheckCircle2,
  XCircle,
  Phone,
  MapPin,
  MessageCircle,
  User as UserIcon,
  ShoppingBag,
  Gift,
} from "lucide-react";
import AdminSidebar from "@/components/admin/AdminSidebar";

type AdminOrderTab = "ALL" | "PENDING" | "SHIPPED" | "COMPLETED";
const ORDER_TABS: AdminOrderTab[] = ["ALL", "PENDING", "SHIPPED", "COMPLETED"];

export default function AdminOrdersPage() {
  const [orders, setOrders] = useState<Order[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isAuthLoading, setIsAuthLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<AdminOrderTab>("ALL");
  const [contactOrderId, setContactOrderId] = useState<string | null>(null);
  const [contactContext, setContactContext] = useState<OrderContactContext | null>(null);
  const [isContactLoading, setIsContactLoading] = useState(false);
  const [isContactSending, setIsContactSending] = useState(false);
  const [expectedShipDate, setExpectedShipDate] = useState("");
  const [contactMessage, setContactMessage] = useState("");
  const [isContactMessageEdited, setIsContactMessageEdited] = useState(false);
  const [selectedTemplateKey, setSelectedTemplateKey] = useState("");
  const [templateVariables, setTemplateVariables] = useState("");
  const [contactStatus, setContactStatus] = useState<string | null>(null);
  const router = useRouter();
  const contactOrder = contactOrderId
    ? orders.find((order) => order.id === contactOrderId) || null
    : null;

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
        fetchOrders();
      })();
    });
    return () => unsubscribe();
  }, [router]);

  useEffect(() => {
    if (!contactOrder || !contactContext) return;

    if (!isContactMessageEdited) {
      setContactMessage(
        buildOrderNotificationMessage(contactOrder, contactContext, expectedShipDate),
      );
    }
    setTemplateVariables(
      buildTemplateVariables(contactOrder, contactContext, expectedShipDate).join("\n"),
    );
  }, [contactOrder, contactContext, expectedShipDate, isContactMessageEdited]);

  const fetchOrders = async () => {
    setIsLoading(true);
    try {
      const data = await getOrders();
      setOrders(data);
    } catch {
      console.error("Failed to fetch orders");
    } finally {
      setIsLoading(false);
    }
  };

  const handleOpenContactPanel = async (
    orderId: string,
    preloadedContext?: OrderContactContext,
  ) => {
    const order = orders.find((item) => item.id === orderId);
    if (!order) return;

    setContactOrderId(orderId);
    setContactContext(null);
    setIsContactLoading(true);
    setExpectedShipDate(order.expectedShipDate || "");
    setContactMessage("");
    setIsContactMessageEdited(false);
    setSelectedTemplateKey("");
    setTemplateVariables("");
    setContactStatus(null);

    try {
      const context = preloadedContext ?? await getOrderContactContext(orderId);
      setContactContext(context);
      const firstTemplate = context.approvedTemplates[0];
      setSelectedTemplateKey(firstTemplate ? templateKey(firstTemplate) : "");
    } catch (error) {
      setContactStatus(
        error instanceof Error ? error.message : "Failed to load contact context",
      );
    } finally {
      setIsContactLoading(false);
    }
  };

  const handleOpenWhatsAppThread = async (orderId: string) => {
    try {
      const context = await getOrderContactContext(orderId);
      if (context.conversationUrl) {
        router.push(context.conversationUrl);
        return;
      }

      await handleOpenContactPanel(orderId, context);
    } catch (error) {
      console.error("Failed to open WhatsApp thread", error);
      await handleOpenContactPanel(orderId);
    }
  };

  const handleCloseContactPanel = () => {
    setContactOrderId(null);
    setContactContext(null);
    setContactStatus(null);
    setIsContactLoading(false);
    setIsContactSending(false);
  };

  const handleStatusUpdate = async (
    orderId: string,
    newStatus: Order["status"],
  ) => {
    try {
      await updateOrderStatus(orderId, newStatus);
      setOrders(
        orders.map((o) => (o.id === orderId ? { ...o, status: newStatus } : o)),
      );
    } catch {
      alert("Failed to update status");
    }
  };

  const handlePaymentStatusUpdate = async (
    orderId: string,
    newStatus: OrderPaymentStatus,
  ) => {
    try {
      await updateOrderPaymentStatus(orderId, newStatus);
      setOrders(
        orders.map((o) =>
          o.id === orderId ? { ...o, paymentStatus: newStatus } : o,
        ),
      );
      if (newStatus === "paid") {
        await handleOpenContactPanel(orderId);
      }
    } catch {
      alert("Failed to update payment status");
    }
  };

  const handleSendNotification = async () => {
    if (!contactOrder?.id || !contactContext || !expectedShipDate || !contactMessage.trim()) {
      return;
    }

    const selectedTemplate =
      contactContext.backendSendMethod === "template"
        ? findTemplateByKey(contactContext.approvedTemplates, selectedTemplateKey)
        : null;

    if (contactContext.backendSendMethod === "template" && !selectedTemplate) {
      setContactStatus("Please select an approved WhatsApp template.");
      return;
    }

    setIsContactSending(true);
    setContactStatus(null);
    try {
      const result = await sendOrderWhatsAppNotification(contactOrder.id, {
        expectedShipDate,
        message: contactMessage.trim(),
        templateName: selectedTemplate?.name,
        languageCode: selectedTemplate?.languageCode,
        bodyVariables:
          contactContext.backendSendMethod === "template"
            ? splitLines(templateVariables)
            : [],
      });
      setOrders((current) =>
        current.map((order) =>
          order.id === contactOrder.id
            ? {
                ...order,
                expectedShipDate: result.expectedShipDate,
                lastCustomerContactMethod: result.method,
                lastCustomerContactAt: new Date(),
              }
            : order,
        ),
      );
      setContactStatus(
        result.method === "template"
          ? "Template sent through WhatsApp Business API."
          : "Message sent through WhatsApp Business API.",
      );
    } catch (error) {
      setContactStatus(
        error instanceof Error
          ? `${error.message} You can still open the WhatsApp draft.`
          : "Send failed. You can still open the WhatsApp draft.",
      );
    } finally {
      setIsContactSending(false);
    }
  };

  const handleLogout = async () => {
    await logout();
    router.push("/admin/login");
  };

  const filteredOrders =
    activeTab === "ALL" ? orders : orders.filter((o) => o.status === activeTab);

  const getStatusColor = (status: Order["status"]) => {
    switch (status) {
      case "PENDING":
        return "bg-amber-100 text-amber-700 border-amber-200";
      case "SHIPPED":
        return "bg-blue-100 text-blue-700 border-blue-200";
      case "COMPLETED":
        return "bg-green-100 text-green-700 border-green-200";
      case "CANCELLED":
        return "bg-red-100 text-red-700 border-red-200";
      default:
        return "bg-gray-100 text-gray-700 border-gray-200";
    }
  };

  const getStatusIcon = (status: Order["status"]) => {
    switch (status) {
      case "PENDING":
        return <Clock size={14} />;
      case "SHIPPED":
        return <Truck size={14} />;
      case "COMPLETED":
        return <CheckCircle2 size={14} />;
      case "CANCELLED":
        return <XCircle size={14} />;
      default:
        return null;
    }
  };

  const getPaymentStatusColor = (status: OrderPaymentStatus) => {
    switch (status) {
      case "paid":
        return "bg-green-100 text-green-700 border-green-200";
      case "payment_submitted":
        return "bg-blue-100 text-blue-700 border-blue-200";
      case "failed":
        return "bg-red-100 text-red-700 border-red-200";
      case "refunded":
        return "bg-gray-100 text-gray-700 border-gray-200";
      default:
        return "bg-amber-100 text-amber-700 border-amber-200";
    }
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
      <AdminSidebar onLogout={handleLogout} />

      {/* Main Content */}
      <main className="flex-1 p-10 overflow-y-auto">
        <header className="flex justify-between items-center mb-10">
          <div>
            <h1 className="text-3xl font-bold text-charcoal tracking-tight">
              Orders Dashboard
            </h1>
            <p className="text-charcoal/50 text-sm">
              Real-time order tracking from your Singapore landing page.
            </p>
          </div>
          <div className="flex bg-white p-1 rounded-xl shadow-sm border border-charcoal/5">
            {ORDER_TABS.map((tab) => (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                className={`px-4 py-2 rounded-lg text-xs font-bold transition-all ${
                  activeTab === tab
                    ? "bg-charcoal text-ivory shadow-md"
                    : "text-charcoal/40 hover:text-charcoal"
                }`}
              >
                {tab}
              </button>
            ))}
          </div>
        </header>

        {isLoading ? (
          <div className="h-64 flex items-center justify-center">
            <Loader2 className="animate-spin text-charcoal/20" size={32} />
          </div>
        ) : filteredOrders.length === 0 ? (
          <div className="bg-white rounded-3xl p-20 text-center border border-dashed border-charcoal/10 space-y-4">
            <div className="w-16 h-16 bg-ivory rounded-full flex items-center justify-center mx-auto text-charcoal/20">
              <ShoppingBag size={32} />
            </div>
            <p className="text-charcoal/40 font-medium">
              No orders found in this category.
            </p>
          </div>
        ) : (
          <div className="space-y-4">
            {filteredOrders.map((order) => {
              const manualDraftHref = buildManualWhatsAppDraftHref(order);
              const apiThreadAvailable = canUseWhatsAppApiForOrder(order);

              return (
              <div
                key={order.id}
                className="bg-white rounded-2xl p-6 shadow-sm border border-charcoal/5 flex flex-col md:flex-row md:items-center justify-between gap-6 hover:shadow-md transition-shadow"
              >
                <div className="flex-1 space-y-4">
                  <div className="flex items-center gap-3">
                    <div
                      className={`px-3 py-1 rounded-full text-[10px] font-bold border flex items-center gap-1.5 uppercase tracking-tighter ${getStatusColor(order.status)}`}
                    >
                      {getStatusIcon(order.status)}
                      {order.status}
                    </div>
                    <div
                      className={`px-3 py-1 rounded-full text-[10px] font-bold border uppercase tracking-tighter ${getPaymentStatusColor(order.paymentStatus)}`}
                    >
                      {order.paymentStatus.replace("_", " ")}
                    </div>
                    <div className="px-3 py-1 rounded-full bg-ivory text-[10px] font-bold uppercase tracking-tighter text-charcoal/50">
                      {sourceLabelForOrder(order)}
                    </div>
                    {(order.marketingContactId || order.checkoutSessionId) && (
                      <div className="px-3 py-1 rounded-full bg-green-50 text-[10px] font-bold uppercase tracking-tighter text-green-700">
                        {orderThreadBadgeLabel(order)}
                      </div>
                    )}
                    <span className="text-xs font-mono text-charcoal/30">
                      #{order.id?.slice(-8)}
                    </span>
                  </div>

                  <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
                    <div className="flex items-start space-x-3">
                      <div className="w-8 h-8 rounded-lg bg-ivory flex items-center justify-center text-charcoal/40">
                        <UserIcon size={16} />
                      </div>
                      <div>
                        <p className="text-[10px] uppercase tracking-widest text-charcoal/40 font-bold mb-1">
                          Customer
                        </p>
                        <p className="text-sm font-bold text-charcoal">
                          {order.customerName}
                        </p>
                      </div>
                    </div>

                    <div className="flex items-start space-x-3">
                      <div className="w-8 h-8 rounded-lg bg-ivory flex items-center justify-center text-green-600/20 text-green-600">
                        <Phone size={16} />
                      </div>
                      <div>
                        <p className="text-[10px] uppercase tracking-widest text-charcoal/40 font-bold mb-1">
                          WhatsApp
                        </p>
                        <p className="text-sm font-bold text-charcoal">
                          {order.customerPhone}
                        </p>
                      </div>
                    </div>

                    <div className="flex items-start space-x-3">
                      <div className="w-8 h-8 rounded-lg bg-ivory flex items-center justify-center text-charcoal/40">
                        <MapPin size={16} />
                      </div>
                      <div>
                        <p className="text-[10px] uppercase tracking-widest text-charcoal/40 font-bold mb-1">
                          Address
                        </p>
                        <p className="text-sm font-medium text-charcoal/70 line-clamp-2">
                          {order.address}
                        </p>
                      </div>
                    </div>

                    {order.giftChoice && (
                      <div className="flex items-start space-x-3">
                        <div className="w-8 h-8 rounded-lg bg-amber-50 flex items-center justify-center text-amber-700">
                          <Gift size={16} />
                        </div>
                        <div>
                          <p className="text-[10px] uppercase tracking-widest text-charcoal/40 font-bold mb-1">
                            Gift Choice
                          </p>
                          <p className="text-sm font-bold text-charcoal">
                            {order.giftChoice.displayName}
                          </p>
                        </div>
                      </div>
                    )}
                  </div>

                  <div className="flex flex-wrap gap-2">
                    {order.paymentReceiptUrl && (
                      <a
                        href={order.paymentReceiptUrl}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="inline-flex w-fit items-center rounded-lg border border-blue-100 bg-blue-50 px-3 py-2 text-xs font-bold text-blue-700 hover:bg-blue-100"
                      >
                        View PayNow receipt
                      </a>
                    )}
                    {manualDraftHref ? (
                      <a
                        id={`order-open-whatsapp-draft-inline-${order.id}`}
                        href={manualDraftHref}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="inline-flex w-fit items-center gap-2 rounded-lg border border-green-100 bg-green-50 px-3 py-2 text-xs font-bold text-green-700 hover:bg-green-100"
                      >
                        <MessageCircle size={14} />
                        Open WhatsApp Draft
                      </a>
                    ) : (
                      <button
                        id={`order-open-whatsapp-draft-inline-${order.id}`}
                        disabled
                        className="inline-flex w-fit items-center gap-2 rounded-lg border border-charcoal/10 bg-charcoal/5 px-3 py-2 text-xs font-bold text-charcoal/30"
                      >
                        <MessageCircle size={14} />
                        Open WhatsApp Draft
                      </button>
                    )}
                    {apiThreadAvailable && (
                      <button
                        id={`order-api-thread-inline-${order.id}`}
                        onClick={() => order.id && void handleOpenWhatsAppThread(order.id)}
                        className="inline-flex w-fit items-center gap-2 rounded-lg border border-charcoal/10 bg-white px-3 py-2 text-xs font-bold text-charcoal/60 hover:text-charcoal"
                      >
                        <ExternalLink size={14} />
                        API Thread
                      </button>
                    )}
                  </div>

                  <PaymentVerificationSummary order={order} />
                </div>

                <div className="flex flex-col items-center md:items-end justify-center min-w-[200px] gap-4 pl-6 md:border-l border-charcoal/5">
                  <div className="text-right">
                    <p className="text-3xl font-black text-secondary tracking-tighter">
                      SGD {order.total.toFixed(2)}
                    </p>
                    <p className="text-[10px] text-charcoal/40 font-bold uppercase tracking-widest mt-1">
                      {order.items[0]?.productName || "Order"}
                    </p>
                    <p className="mt-1 text-[10px] text-charcoal/40">
                      Shipping: SGD {order.shippingFee.toFixed(2)} · {order.boxCount} box
                      {order.boxCount === 1 ? "" : "es"}
                    </p>
                    {order.giftChoice && (
                      <p className="mt-1 text-[10px] font-semibold text-amber-700">
                        Gift: {order.giftChoice.displayName}
                      </p>
                    )}
                    {order.lastCustomerContactMethod && (
                      <p className="mt-1 text-[10px] font-semibold text-green-700">
                        Contacted via {formatContactMethod(order.lastCustomerContactMethod)}
                      </p>
                    )}
                  </div>

                  <div className="flex flex-wrap justify-end gap-2">
                    {manualDraftHref ? (
                      <a
                        id={`order-open-whatsapp-draft-${order.id}`}
                        href={manualDraftHref}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="px-4 py-2 rounded-lg border border-green-200 bg-white text-green-700 text-xs font-bold hover:bg-green-50 transition-all flex items-center gap-2"
                      >
                        <MessageCircle size={14} />
                        Open Draft
                      </a>
                    ) : (
                      <button
                        id={`order-open-whatsapp-draft-${order.id}`}
                        disabled
                        className="px-4 py-2 rounded-lg border border-charcoal/10 bg-charcoal/5 text-charcoal/30 text-xs font-bold transition-all flex items-center gap-2"
                      >
                        <MessageCircle size={14} />
                        Open Draft
                      </button>
                    )}
                    {apiThreadAvailable && (
                      <button
                        id={`order-api-thread-${order.id}`}
                        onClick={() => order.id && void handleOpenWhatsAppThread(order.id)}
                        className="px-4 py-2 rounded-lg border border-charcoal/10 bg-white text-charcoal/60 text-xs font-bold hover:text-charcoal transition-all flex items-center gap-2"
                      >
                        <ExternalLink size={14} />
                        API Thread
                      </button>
                    )}
                    {order.paymentStatus !== "paid" && (
                      <button
                        onClick={() => handlePaymentStatusUpdate(order.id!, "paid")}
                        className="px-4 py-2 rounded-lg bg-blue-600 text-white text-xs font-bold hover:bg-blue-700 transition-all flex items-center gap-2"
                      >
                        <CheckCircle2 size={14} />
                        Mark Paid
                      </button>
                    )}
                    {order.status === "PENDING" && (
                      <button
                        onClick={() => handleStatusUpdate(order.id!, "SHIPPED")}
                        className="px-4 py-2 rounded-lg bg-charcoal text-ivory text-xs font-bold hover:bg-primary transition-all flex items-center gap-2"
                      >
                        <Truck size={14} />
                        Mark Shipped
                      </button>
                    )}
                    {(order.status === "PENDING" ||
                      order.status === "SHIPPED") && (
                      <button
                        onClick={() =>
                          handleStatusUpdate(order.id!, "COMPLETED")
                        }
                        className="px-4 py-2 rounded-lg bg-green-600 text-white text-xs font-bold hover:bg-green-700 transition-all flex items-center gap-2"
                      >
                        <CheckCircle2 size={14} />
                        Complete
                      </button>
                    )}
                  </div>
                </div>
              </div>
              );
            })}
          </div>
        )}
      </main>

      <OrderContactDrawer
        order={contactOrder}
        context={contactContext}
        isLoading={isContactLoading}
        isSending={isContactSending}
        expectedShipDate={expectedShipDate}
        message={contactMessage}
        selectedTemplateKey={selectedTemplateKey}
        templateVariables={templateVariables}
        statusMessage={contactStatus}
        onExpectedShipDateChange={(value) => {
          setExpectedShipDate(value);
          setIsContactMessageEdited(false);
        }}
        onMessageChange={(value) => {
          setContactMessage(value);
          setIsContactMessageEdited(true);
        }}
        onTemplateChange={setSelectedTemplateKey}
        onTemplateVariablesChange={setTemplateVariables}
        onSend={() => void handleSendNotification()}
        onClose={handleCloseContactPanel}
      />
    </div>
  );
}

function OrderContactDrawer({
  order,
  context,
  isLoading,
  isSending,
  expectedShipDate,
  message,
  selectedTemplateKey,
  templateVariables,
  statusMessage,
  onExpectedShipDateChange,
  onMessageChange,
  onTemplateChange,
  onTemplateVariablesChange,
  onSend,
  onClose,
}: {
  order: Order | null;
  context: OrderContactContext | null;
  isLoading: boolean;
  isSending: boolean;
  expectedShipDate: string;
  message: string;
  selectedTemplateKey: string;
  templateVariables: string;
  statusMessage: string | null;
  onExpectedShipDateChange: (value: string) => void;
  onMessageChange: (value: string) => void;
  onTemplateChange: (value: string) => void;
  onTemplateVariablesChange: (value: string) => void;
  onSend: () => void;
  onClose: () => void;
}) {
  if (!order) return null;

  const draftHref =
    context?.normalizedWhatsApp && message.trim()
      ? buildCustomerWhatsAppHref(context.normalizedWhatsApp, message.trim())
      : undefined;
  const canOpenDraft = Boolean(draftHref);
  const canSendViaBackend = Boolean(
    context?.backendSendMethod &&
      expectedShipDate &&
      message.trim() &&
      (context.backendSendMethod !== "template" || selectedTemplateKey),
  );
  const linkedConversationHref = context?.conversationUrl || undefined;

  return (
    <div className="fixed inset-0 z-50 flex justify-end bg-charcoal/30 backdrop-blur-sm">
      <button
        aria-label="Close contact panel"
        className="absolute inset-0 cursor-default"
        onClick={onClose}
      />
      <aside className="relative flex h-full w-full max-w-[560px] flex-col overflow-y-auto bg-[#f8f9fa] shadow-2xl">
        <header className="border-b border-charcoal/10 bg-white px-6 py-5">
          <div className="flex items-start justify-between gap-4">
            <div>
              <p className="text-[11px] font-bold uppercase tracking-[0.24em] text-green-700">
                Customer contact
              </p>
              <h2 className="mt-2 text-2xl font-black tracking-tight text-charcoal">
                {order.customerName || "Customer"}
              </h2>
              <p className="mt-1 text-xs text-charcoal/50">
                #{order.id?.slice(-8)} · {context?.sourceLabel || sourceLabelForOrder(order)}
              </p>
            </div>
            <button
              id="order-contact-close"
              onClick={onClose}
              className="rounded-lg border border-charcoal/10 bg-white px-3 py-2 text-xs font-bold text-charcoal/60 hover:text-charcoal"
            >
              Close
            </button>
          </div>
        </header>

        <div className="space-y-4 p-6">
          {isLoading ? (
            <div className="flex h-52 items-center justify-center rounded-xl border border-charcoal/10 bg-white">
              <Loader2 className="animate-spin text-charcoal/30" size={32} />
            </div>
          ) : (
            <>
              <section className="rounded-xl border border-charcoal/10 bg-white p-4">
                <div className="grid gap-3 sm:grid-cols-2">
                  <InfoTile label="WhatsApp" value={context?.normalizedWhatsApp || order.customerPhone || "-"} />
                  {order.giftChoice && (
                    <InfoTile label="Gift choice" value={order.giftChoice.displayName} tone="amber" />
                  )}
                  <InfoTile
                    label="Backend send"
                    value={backendSendLabel(context)}
                    tone={context?.backendSendMethod ? "green" : "amber"}
                  />
                </div>
                {linkedConversationHref && (
                  <a
                    id="order-contact-open-thread"
                    href={linkedConversationHref}
                    className="mt-3 inline-flex items-center gap-2 text-xs font-bold text-green-700 hover:text-green-800"
                  >
                    <ExternalLink size={14} />
                    Open WhatsApp API thread
                  </a>
                )}
              </section>

              <section className="rounded-xl border border-charcoal/10 bg-white p-4">
                <label className="text-[11px] font-bold uppercase tracking-[0.22em] text-charcoal/40">
                  Expected ship date
                </label>
                <div className="mt-2 flex items-center gap-3 rounded-lg border border-charcoal/10 px-3 py-2">
                  <CalendarDays size={16} className="text-charcoal/40" />
                  <input
                    id="order-contact-ship-date"
                    type="date"
                    value={expectedShipDate}
                    min={todayInputValue()}
                    onChange={(event) => onExpectedShipDateChange(event.target.value)}
                    className="w-full bg-transparent text-sm font-semibold text-charcoal outline-none"
                  />
                </div>
              </section>

              <section className="rounded-xl border border-charcoal/10 bg-white p-4">
                <label className="text-[11px] font-bold uppercase tracking-[0.22em] text-charcoal/40">
                  WhatsApp message
                </label>
                <textarea
                  id="order-contact-message"
                  value={message}
                  onChange={(event) => onMessageChange(event.target.value)}
                  rows={7}
                  className="mt-2 w-full resize-none rounded-lg border border-charcoal/10 bg-[#fbfbfa] p-3 text-sm leading-6 text-charcoal outline-none focus:border-green-600"
                  placeholder="Message will be generated from the order status."
                />
              </section>

              {context?.backendSendMethod === "template" && (
                <section className="rounded-xl border border-charcoal/10 bg-white p-4">
                  <label className="text-[11px] font-bold uppercase tracking-[0.22em] text-charcoal/40">
                    Approved template
                  </label>
                  <select
                    id="order-contact-template"
                    value={selectedTemplateKey}
                    onChange={(event) => onTemplateChange(event.target.value)}
                    className="mt-2 w-full rounded-lg border border-charcoal/10 bg-white px-3 py-2 text-sm font-semibold text-charcoal outline-none focus:border-green-600"
                  >
                    {context.approvedTemplates.map((template) => (
                      <option key={templateKey(template)} value={templateKey(template)}>
                        {template.name} · {template.languageCode}
                      </option>
                    ))}
                  </select>
                  <textarea
                    id="order-contact-template-variables"
                    value={templateVariables}
                    onChange={(event) => onTemplateVariablesChange(event.target.value)}
                    rows={4}
                    className="mt-3 w-full resize-none rounded-lg border border-charcoal/10 bg-[#fbfbfa] p-3 text-sm leading-6 text-charcoal outline-none focus:border-green-600"
                    placeholder="Template variables, one per line"
                  />
                </section>
              )}

              {statusMessage && (
                <div className="rounded-xl border border-amber-200 bg-amber-50 p-3 text-sm font-semibold text-amber-800">
                  {statusMessage}
                </div>
              )}
            </>
          )}
        </div>

        <footer className="mt-auto border-t border-charcoal/10 bg-white p-5">
          <div className="flex flex-col gap-3 sm:flex-row">
            {canOpenDraft && draftHref ? (
              <a
                id="order-contact-open-draft"
                href={draftHref}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex flex-1 items-center justify-center gap-2 rounded-lg border border-green-200 bg-green-50 px-4 py-3 text-sm font-bold text-green-700 hover:bg-green-100"
              >
                <ExternalLink size={16} />
                Open WhatsApp Draft
              </a>
            ) : (
              <button
                id="order-contact-open-draft-disabled"
                disabled
                className="inline-flex flex-1 items-center justify-center gap-2 rounded-lg border border-charcoal/10 bg-charcoal/5 px-4 py-3 text-sm font-bold text-charcoal/30"
              >
                <ExternalLink size={16} />
                Open WhatsApp Draft
              </button>
            )}
            <button
              id="order-contact-send-backend"
              onClick={onSend}
              disabled={isSending || !canSendViaBackend}
              className="inline-flex flex-1 items-center justify-center gap-2 rounded-lg bg-charcoal px-4 py-3 text-sm font-bold text-ivory hover:bg-primary disabled:cursor-not-allowed disabled:opacity-40"
            >
              {isSending ? <Loader2 className="animate-spin" size={16} /> : <MessageCircle size={16} />}
              Send from Backend
            </button>
          </div>
        </footer>
      </aside>
    </div>
  );
}

function InfoTile({
  label,
  value,
  tone = "default",
}: {
  label: string;
  value: string;
  tone?: "default" | "green" | "amber";
}) {
  const toneClass =
    tone === "green"
      ? "text-green-700"
      : tone === "amber"
        ? "text-amber-700"
        : "text-charcoal";
  return (
    <div className="rounded-lg bg-ivory p-3">
      <p className="text-[10px] font-bold uppercase tracking-widest text-charcoal/40">
        {label}
      </p>
      <p className={`mt-1 text-sm font-bold ${toneClass}`}>{value}</p>
    </div>
  );
}

function sourceLabelForOrder(order: Order) {
  const sourceChannel = normalizeSourceChannel(order.sourceChannel);
  if (order.source === "marketing_chatbot" && sourceChannel === "whatsapp") {
    return "WhatsApp Chatbot";
  }
  if (order.source === "marketing_chatbot" && sourceChannel === "messenger") {
    return "Messenger Chatbot";
  }
  if (order.source === "marketing_chatbot") return "Chatbot";
  if (order.source === "landing_page") return "Landing Checkout";
  return order.source || "Landing Checkout";
}

function orderThreadBadgeLabel(order: Order) {
  const sourceChannel = normalizeSourceChannel(order.sourceChannel);
  if (sourceChannel === "whatsapp") return "WhatsApp thread";
  if (sourceChannel === "messenger") return "Messenger thread";
  return "Thread linked";
}

function canUseWhatsAppApiForOrder(order: Order) {
  return Boolean(
    order.source === "marketing_chatbot" &&
      normalizeSourceChannel(order.sourceChannel) === "whatsapp" &&
      (order.marketingContactId || order.checkoutSessionId),
  );
}

function normalizeSourceChannel(value: string | undefined) {
  return String(value || "").trim().toLowerCase();
}

function formatContactMethod(method: string) {
  if (method === "free_text") return "WhatsApp text";
  if (method === "template") return "WhatsApp template";
  return method;
}

function backendSendLabel(context: OrderContactContext | null) {
  if (!context?.conversationId) return "Manual draft only";
  if (context.backendSendMethod === "free_text") return "API text ready";
  if (context.backendSendMethod === "template") return "Template required";
  return "No template saved";
}

function templateKey(template: OrderContactTemplate) {
  return `${template.name}::${template.languageCode}`;
}

function findTemplateByKey(templates: OrderContactTemplate[], key: string) {
  return templates.find((template) => templateKey(template) === key) || null;
}

function splitLines(value: string) {
  return value
    .split("\n")
    .map((line) => line.trim())
    .filter(Boolean);
}

function PaymentVerificationSummary({ order }: { order: Order }) {
  const verification = order.paymentVerification;
  if (!verification) return null;

  const isDuplicate =
    verification.duplicateDetected ||
    order.riskFlags.includes("duplicate_payment_reference");
  const isWarning = verification.status === "warning" || isDuplicate;
  const statusLabel =
    verification.status === "ok"
      ? "AI amount match"
      : verification.status === "unavailable"
        ? "AI check unavailable"
        : "AI check warning";

  return (
    <div
      className={`w-full rounded-lg border px-3 py-3 text-xs ${
        isDuplicate
          ? "border-red-200 bg-red-50 text-red-900"
          : isWarning
            ? "border-amber-200 bg-amber-50 text-amber-900"
            : "border-emerald-200 bg-emerald-50 text-emerald-900"
      }`}
    >
      <div className="flex flex-wrap items-center gap-2 font-bold">
        {isDuplicate && <AlertTriangle size={14} />}
        <span>{isDuplicate ? "Duplicate payment reference / Possible scam risk" : statusLabel}</span>
        {typeof verification.confidence === "number" && (
          <span className="font-mono opacity-70">
            Confidence {(verification.confidence * 100).toFixed(0)}%
          </span>
        )}
      </div>
      <div className="mt-2 grid gap-1 sm:grid-cols-3">
        <span>Expected: {formatSgd(verification.expectedAmount ?? order.total)}</span>
        <span>
          Receipt:{" "}
          {typeof verification.extractedAmount === "number"
            ? formatSgd(verification.extractedAmount)
            : "Not read"}
        </span>
        <span>Reference: {verification.referenceNumber || order.transactionId || "Not read"}</span>
      </div>
      {verification.duplicateOrderIds.length > 0 && (
        <p className="mt-2 font-semibold">
          Related orders: {verification.duplicateOrderIds.map((id) => `#${id.slice(-8)}`).join(", ")}
        </p>
      )}
      {verification.warnings.length > 0 && (
        <p className="mt-2 leading-5">{verification.warnings.join(" · ")}</p>
      )}
    </div>
  );
}

function formatSgd(value: number) {
  return `SGD ${value.toFixed(2)}`;
}

function buildOrderNotificationMessage(
  order: Order,
  context: OrderContactContext,
  expectedShipDate: string,
) {
  return buildManualOrderMessage({
    ...order,
    customerName: context.customerName || order.customerName,
    expectedShipDate: expectedShipDate || undefined,
  });
}

function buildManualWhatsAppDraftHref(order: Order) {
  const phone = normalizeCustomerWhatsAppForLink(order.customerPhone);
  if (!phone) return undefined;
  return buildCustomerWhatsAppHref(phone, buildManualOrderMessage(order));
}

function buildManualOrderMessage(order: Order) {
  const customerName = order.customerName || "there";
  const orderRef = order.id ? `#${order.id.slice(-8)}` : "your order";
  const giftLine = order.giftChoice
    ? `Gift choice: ${order.giftChoice.displayName}.`
    : "";

  if (order.expectedShipDate) {
    return [
      `Hi ${customerName}, Aqina SG here.`,
      `Your order ${orderRef} is arranged for shipment on ${formatShipDate(order.expectedShipDate)}.`,
      giftLine,
      "We will update you again if there are any delivery changes. Thank you.",
    ].filter(Boolean).join("\n");
  }

  if (order.status === "SHIPPED") {
    return [
      `Hi ${customerName}, Aqina SG here.`,
      `Your order ${orderRef} has been arranged for shipment.`,
      giftLine,
      "Thank you for your patience.",
    ].filter(Boolean).join("\n");
  }

  if (order.paymentStatus === "paid") {
    return [
      `Hi ${customerName}, Aqina SG has verified your PayNow payment for order ${orderRef}.`,
      giftLine,
      "We are arranging your shipment and will update you once delivery is ready. Thank you.",
    ].filter(Boolean).join("\n");
  }

  return [
    `Hi ${customerName}, Aqina SG has received your order ${orderRef} and PayNow receipt.`,
    giftLine,
    "We are checking the payment and will update you about delivery soon. Thank you.",
  ].filter(Boolean).join("\n");
}

function buildTemplateVariables(
  order: Order,
  context: OrderContactContext,
  expectedShipDate: string,
) {
  return [
    context.customerName || order.customerName,
    expectedShipDate ? formatShipDate(expectedShipDate) : "",
    order.id || "",
  ].filter(Boolean);
}

function buildCustomerWhatsAppHref(phone: string, message: string) {
  return `https://wa.me/${phone}?text=${encodeURIComponent(message)}`;
}

function normalizeCustomerWhatsAppForLink(value: string | undefined) {
  const digits = String(value || "").replace(/\D/g, "");
  if (!digits) return undefined;

  const normalized =
    digits.length === 8
      ? `65${digits}`
      : digits.startsWith("0065") && digits.length > 4
        ? digits.slice(2)
        : digits;

  if (normalized.length < 8 || normalized.length > 20) return undefined;
  return normalized;
}

function formatShipDate(value: string) {
  const [year, month, day] = value.split("-").map(Number);
  if (!year || !month || !day) return value;
  return new Date(year, month - 1, day).toLocaleDateString("en-SG", {
    day: "numeric",
    month: "short",
    year: "numeric",
  });
}

function todayInputValue() {
  const now = new Date();
  const month = String(now.getMonth() + 1).padStart(2, "0");
  const day = String(now.getDate()).padStart(2, "0");
  return `${now.getFullYear()}-${month}-${day}`;
}
