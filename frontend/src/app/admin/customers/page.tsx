'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { subscribeToAuthChanges, isAdminUser, logout } from '@/lib/auth-service';
import {
  Loader2,
  Users,
  Search,
  Mail,
  Phone,
  MapPin,
  TrendingUp,
  Crown,
  Star
} from 'lucide-react';
import AdminSidebar from '@/components/admin/AdminSidebar';

interface Customer {
  customer_id: string;
  name: string;
  email: string;
  whatsapp: string;
  address?: string;
  total_spent: number;
  purchase_count: number;
  customer_level: 'new' | 'standard' | 'vip';
  last_purchase_date?: Date;
  created_at: Date;
}

type CustomerLevelFilter = 'ALL' | Customer['customer_level'];
const CUSTOMER_LEVEL_FILTERS: CustomerLevelFilter[] = ['ALL', 'new', 'standard', 'vip'];

export default function AdminCustomersPage() {
  const [customers, setCustomers] = useState<Customer[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isAuthLoading, setIsAuthLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [levelFilter, setLevelFilter] = useState<CustomerLevelFilter>('ALL');
  const router = useRouter();

  useEffect(() => {
    const unsubscribe = subscribeToAuthChanges((user) => {
      void (async () => {
        if (!user) {
          router.push('/admin/login');
          return;
        }

        const isAdmin = await isAdminUser(user);
        if (!isAdmin) {
          await logout();
          router.push('/admin/login');
          return;
        }

        setIsAuthLoading(false);
        fetchCustomers();
      })();
    });
    return () => unsubscribe();
  }, [router]);

  const fetchCustomers = async () => {
    setIsLoading(true);
    try {
      const response = await fetch('/api/customers');
      if (response.ok) {
        const data = await response.json();
        setCustomers(data.customers || []);
      }
    } catch {
      console.error('Failed to fetch customers');
    } finally {
      setIsLoading(false);
    }
  };

  const getLevelColor = (level: Customer['customer_level']) => {
    switch (level) {
      case 'vip': return 'bg-gradient-to-r from-primary to-accent text-white';
      case 'standard': return 'bg-blue-100 text-blue-700';
      case 'new': return 'bg-gray-100 text-gray-600';
      default: return 'bg-gray-100 text-gray-600';
    }
  };

  const getLevelIcon = (level: Customer['customer_level']) => {
    switch (level) {
      case 'vip': return <Crown size={12} />;
      case 'standard': return <Star size={12} />;
      case 'new': return <Users size={12} />;
      default: return null;
    }
  };

  const filteredCustomers = customers.filter(customer => {
    const matchesSearch = searchQuery === '' ||
      customer.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      customer.email.toLowerCase().includes(searchQuery.toLowerCase()) ||
      customer.whatsapp.includes(searchQuery);

    const matchesLevel = levelFilter === 'ALL' || customer.customer_level === levelFilter;

    return matchesSearch && matchesLevel;
  });

  // Calculate stats
  const totalRevenue = customers.reduce((sum, c) => sum + c.total_spent, 0);
  const vipCount = customers.filter(c => c.customer_level === 'vip').length;
  const avgLtv = customers.length > 0 ? totalRevenue / customers.length : 0;

  if (isAuthLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[#F8F9FA]">
        <Loader2 className="animate-spin text-primary" size={48} />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#F8F9FA] flex">
      <AdminSidebar onLogout={async () => { await logout(); router.push('/admin/login'); }} />

      {/* Main Content */}
      <main className="flex-1 p-10 overflow-y-auto">
        {/* Header */}
        <header className="mb-10">
          <div className="flex items-center gap-3 mb-2">
            <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-blue-500 to-blue-600 flex items-center justify-center shadow-lg">
              <Users size={24} className="text-white" />
            </div>
            <div>
              <h1 className="text-3xl font-bold text-charcoal tracking-tight">Customers</h1>
              <p className="text-charcoal/50 text-sm">Manage customer relationships and insights</p>
            </div>
          </div>
        </header>

        {/* Stats */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          <div className="bg-white rounded-2xl p-6 shadow-sm border border-charcoal/5">
            <div className="flex items-center justify-between mb-2">
              <Users className="text-charcoal/40" size={20} />
              <span className="text-xs font-bold text-blue-600 bg-blue-50 px-2 py-1 rounded-full">
                Total
              </span>
            </div>
            <p className="text-2xl font-bold text-charcoal">{customers.length}</p>
            <p className="text-xs text-charcoal/50 mt-1">Total Customers</p>
          </div>

          <div className="bg-white rounded-2xl p-6 shadow-sm border border-charcoal/5">
            <div className="flex items-center justify-between mb-2">
              <TrendingUp className="text-green-600" size={20} />
              <span className="text-xs font-bold text-green-600 bg-green-50 px-2 py-1 rounded-full">
                Revenue
              </span>
            </div>
            <p className="text-2xl font-bold text-charcoal">SGD {totalRevenue.toFixed(0)}</p>
            <p className="text-xs text-charcoal/50 mt-1">Total Revenue</p>
          </div>

          <div className="bg-white rounded-2xl p-6 shadow-sm border border-charcoal/5">
            <div className="flex items-center justify-between mb-2">
              <Crown className="text-primary" size={20} />
              <span className="text-xs font-bold text-primary bg-primary/10 px-2 py-1 rounded-full">
                VIPs
              </span>
            </div>
            <p className="text-2xl font-bold text-charcoal">{vipCount}</p>
            <p className="text-xs text-charcoal/50 mt-1">VIP Customers</p>
          </div>

          <div className="bg-white rounded-2xl p-6 shadow-sm border border-charcoal/5">
            <div className="flex items-center justify-between mb-2">
              <Star className="text-accent" size={20} />
              <span className="text-xs font-bold text-accent bg-accent/10 px-2 py-1 rounded-full">
                Avg LTV
              </span>
            </div>
            <p className="text-2xl font-bold text-charcoal">SGD {avgLtv.toFixed(0)}</p>
            <p className="text-xs text-charcoal/50 mt-1">Avg Lifetime Value</p>
          </div>
        </div>

        {/* Search and Filter */}
        <div className="bg-white rounded-2xl p-4 shadow-sm border border-charcoal/5 mb-6">
          <div className="flex flex-col md:flex-row gap-4">
            <div className="flex-1 relative">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-charcoal/40" size={20} />
              <input
                type="text"
                placeholder="Search by name, email, or phone..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-10 pr-4 py-3 rounded-xl border border-charcoal/10 bg-ivory/50 focus:outline-none focus:ring-2 focus:ring-primary/50"
              />
            </div>

            <div className="flex gap-2">
              {CUSTOMER_LEVEL_FILTERS.map((level) => (
                <button
                  key={level}
                  onClick={() => setLevelFilter(level)}
                  className={`px-4 py-2 rounded-lg text-sm font-bold transition-all ${
                    levelFilter === level
                      ? 'bg-charcoal text-white'
                      : 'bg-ivory text-charcoal/60 hover:bg-charcoal/10'
                  }`}
                >
                  {level.charAt(0).toUpperCase() + level.slice(1)}
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Customers List */}
        {isLoading ? (
          <div className="h-64 flex items-center justify-center">
            <Loader2 className="animate-spin text-charcoal/20" size={32} />
          </div>
        ) : filteredCustomers.length === 0 ? (
          <div className="bg-white rounded-2xl p-20 text-center border border-dashed border-charcoal/10">
            <Users size={48} className="mx-auto text-charcoal/20 mb-4" />
            <p className="text-charcoal/40 font-medium">No customers found</p>
          </div>
        ) : (
          <div className="bg-white rounded-2xl shadow-sm border border-charcoal/5 overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead className="bg-ivory/50 border-b border-charcoal/10">
                  <tr>
                    <th className="px-6 py-4 text-left text-xs font-bold text-charcoal/50 uppercase tracking-wider">
                      Customer
                    </th>
                    <th className="px-6 py-4 text-left text-xs font-bold text-charcoal/50 uppercase tracking-wider">
                      Contact
                    </th>
                    <th className="px-6 py-4 text-left text-xs font-bold text-charcoal/50 uppercase tracking-wider">
                      Level
                    </th>
                    <th className="px-6 py-4 text-right text-xs font-bold text-charcoal/50 uppercase tracking-wider">
                      Orders
                    </th>
                    <th className="px-6 py-4 text-right text-xs font-bold text-charcoal/50 uppercase tracking-wider">
                      Total Spent
                    </th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-charcoal/5">
                  {filteredCustomers.map((customer) => (
                    <tr key={customer.customer_id} className="hover:bg-ivory/30 transition-colors">
                      <td className="px-6 py-4">
                        <div className="flex items-center gap-3">
                          <div className={`w-10 h-10 rounded-full flex items-center justify-center text-sm font-bold ${getLevelColor(customer.customer_level)}`}>
                            {getLevelIcon(customer.customer_level)}
                            {customer.name.charAt(0).toUpperCase()}
                          </div>
                          <div>
                            <p className="font-bold text-charcoal">{customer.name}</p>
                            <p className="text-xs text-charcoal/50">ID: {customer.customer_id.slice(-8)}</p>
                          </div>
                        </div>
                      </td>

                      <td className="px-6 py-4">
                        <div className="space-y-1">
                          <div className="flex items-center gap-2 text-sm text-charcoal/70">
                            <Mail size={14} />
                            {customer.email}
                          </div>
                          <div className="flex items-center gap-2 text-sm text-charcoal/70">
                            <Phone size={14} />
                            {customer.whatsapp}
                          </div>
                          {customer.address && (
                            <div className="flex items-center gap-2 text-sm text-charcoal/50">
                              <MapPin size={14} />
                              <span className="line-clamp-1">{customer.address}</span>
                            </div>
                          )}
                        </div>
                      </td>

                      <td className="px-6 py-4">
                        <span className={`inline-flex items-center gap-1 px-3 py-1 rounded-full text-xs font-bold uppercase ${getLevelColor(customer.customer_level)}`}>
                          {getLevelIcon(customer.customer_level)}
                          {customer.customer_level}
                        </span>
                      </td>

                      <td className="px-6 py-4 text-right">
                        <p className="font-bold text-charcoal">{customer.purchase_count}</p>
                      </td>

                      <td className="px-6 py-4 text-right">
                        <p className="font-bold text-lg text-primary">SGD {customer.total_spent.toFixed(2)}</p>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
