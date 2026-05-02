'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { loginWithGoogle, subscribeToAuthChanges, isAdminUser, logout } from '@/lib/auth-service';
import { LogIn, ShieldCheck, Loader2 } from 'lucide-react';

export default function AdminLoginPage() {
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState('');
  const router = useRouter();

  useEffect(() => {
    const unsubscribe = subscribeToAuthChanges((user) => {
      void (async () => {
        if (!user) {
          setIsLoading(false);
          return;
        }

        const isAdmin = await isAdminUser(user);
        if (isAdmin) {
          router.push('/admin');
          return;
        }

        await logout();
        setIsLoading(false);
      })();
    });
    return () => unsubscribe();
  }, [router]);

  const handleLogin = async () => {
    setError('');
    setIsLoading(true);
    try {
      await loginWithGoogle();
      router.push('/admin');
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Login failed');
      setIsLoading(false);
    }
  };

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-ivory">
        <Loader2 className="animate-spin text-primary" size={48} />
      </div>
    );
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-ivory p-6">
      <div className="max-w-md w-full bg-white rounded-3xl shadow-2xl p-10 space-y-8 text-center border border-charcoal/5">
        <div className="space-y-4">
          <div className="w-20 h-20 gradient-gold rounded-3xl flex items-center justify-center mx-auto text-white shadow-xl rotate-3">
            <ShieldCheck size={40} />
          </div>
          <h1 className="text-3xl font-bold text-charcoal">Admin Portal</h1>
          <p className="text-charcoal/60">Aqina Singapore Management Dashboard</p>
        </div>

        {error && (
          <div className="p-4 bg-red-50 text-red-600 rounded-xl text-sm font-medium border border-red-100 italic">
            {error}
          </div>
        )}

        <button
          onClick={handleLogin}
          className="w-full py-5 rounded-2xl bg-charcoal text-ivory font-bold hover:bg-primary transition-all flex items-center justify-center space-x-3 shadow-xl hover:shadow-charcoal/20 group"
        >
          <LogIn size={20} className="group-hover:-translate-x-1 transition-transform" />
          <span>Sign in with Google</span>
        </button>

        <p className="text-[10px] uppercase tracking-widest text-charcoal/30 font-bold">
          Restricted Access — Authorized Personnel Only
        </p>
      </div>
    </div>
  );
}
