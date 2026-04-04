'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import {
  LayoutDashboard,
  BrainCircuit,
  Users,
  LogOut,
  ShoppingBag
} from 'lucide-react';

interface NavItem {
  label: string;
  href: string;
  icon: React.ElementType;
}

const navItems: NavItem[] = [
  { label: 'Orders', href: '/admin/orders', icon: ShoppingBag },
  { label: 'CRM & AI', href: '/admin/crm', icon: BrainCircuit },
  { label: 'Customers', href: '/admin/customers', icon: Users },
];

interface AdminSidebarProps {
  onLogout: () => void;
}

export default function AdminSidebar({ onLogout }: AdminSidebarProps) {
  const pathname = usePathname();

  const isActive = (href: string) => pathname === href || pathname?.startsWith(href + '/');

  return (
    <aside className="w-64 bg-charcoal text-ivory flex flex-col h-screen sticky top-0">
      {/* Logo */}
      <div className="p-6 border-b border-white/10">
        <div className="flex items-center space-x-3">
          <div className="w-10 h-10 gradient-gold rounded-xl flex items-center justify-center shadow-lg">
            <ShoppingBag size={24} className="text-white" />
          </div>
          <div>
            <span className="text-xl font-bold tracking-tight">Aqina Admin</span>
            <p className="text-xs text-ivory/50">Management Console</p>
          </div>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 p-4 space-y-2">
        {navItems.map((item) => {
          const Icon = item.icon;
          const active = isActive(item.href);
          return (
            <Link
              key={item.href}
              href={item.href}
              className={`
                w-full flex items-center space-x-3 px-4 py-3 rounded-xl
                transition-all font-medium
                ${active
                  ? 'bg-primary/20 text-primary border border-primary/30'
                  : 'text-ivory/50 hover:bg-white/5 hover:text-ivory'
                }
              `}
            >
              <Icon size={20} className={active ? 'text-primary' : ''} />
              <span>{item.label}</span>
              {active && <div className="ml-auto w-2 h-2 rounded-full bg-primary" />}
            </Link>
          );
        })}
      </nav>

      {/* Logout */}
      <div className="p-4 border-t border-white/10">
        <button
          onClick={onLogout}
          className="w-full flex items-center space-x-3 px-4 py-3 rounded-xl
                     hover:bg-red-500/10 hover:text-red-400 text-ivory/50
                     font-medium transition-all group"
        >
          <LogOut size={20} className="group-hover:-translate-x-1 transition-transform" />
          <span>Logout</span>
        </button>
      </div>
    </aside>
  );
}
