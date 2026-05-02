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
  updateOrderPaymentStatus,
  updateOrderStatus,
  Order,
  OrderPaymentStatus,
} from "@/lib/order-service";
import {
  Loader2,
  Clock,
  Truck,
  CheckCircle2,
  XCircle,
  Phone,
  MapPin,
  User as UserIcon,
  ShoppingBag,
} from "lucide-react";
import AdminSidebar from "@/components/admin/AdminSidebar";

type AdminOrderTab = "ALL" | "PENDING" | "SHIPPED" | "COMPLETED";
const ORDER_TABS: AdminOrderTab[] = ["ALL", "PENDING", "SHIPPED", "COMPLETED"];

export default function AdminOrdersPage() {
  const [orders, setOrders] = useState<Order[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isAuthLoading, setIsAuthLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<AdminOrderTab>("ALL");
  const router = useRouter();

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
    } catch {
      alert("Failed to update payment status");
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
            {filteredOrders.map((order) => (
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
                      {order.source === "marketing_chatbot" ? "Chatbot" : "Landing"}
                    </div>
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
                  </div>

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
                  </div>

                  <div className="flex gap-2">
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
            ))}
          </div>
        )}
      </main>
    </div>
  );
}
