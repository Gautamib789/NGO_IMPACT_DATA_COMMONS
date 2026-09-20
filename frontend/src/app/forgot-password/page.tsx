'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/context/AuthContext';
import { Mail, HelpCircle, ArrowRight } from 'lucide-react';

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  
  const { apiFetch } = useAuth();
  const router = useRouter();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const res = await apiFetch('/api/auth/forgot-password', {
        method: 'POST',
        body: JSON.stringify({ email }),
      });

      const devParam = res?.dev_mode ? '&dev_mode=true' : '';
      router.push(`/reset-password?email=${encodeURIComponent(email)}${devParam}`);
    } catch (err: any) {
      setError(err.message || 'Unable to send verification email. Please try again later.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex min-h-[85vh] items-center justify-center px-4 py-12 bg-slate-50">
      <div className="w-full max-w-md space-y-6">
        
        {/* Header */}
        <div className="text-center space-y-2">
          <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-2xl bg-blue-600/10 text-blue-600 border border-blue-200 shadow-sm">
            <HelpCircle className="h-6 w-6" />
          </div>
          <h2 className="text-2xl font-bold text-slate-900 tracking-tight">Reset Account Password</h2>
          <p className="text-xs text-slate-500 max-w-xs mx-auto">
            Enter your email to receive a verification code.
          </p>
        </div>

        {/* Main Form Card */}
        <div className="bg-white rounded-2xl border border-slate-200/90 p-7 shadow-card space-y-5">
          <form onSubmit={handleSubmit} className="space-y-4">
            
            {error && (
              <div className="rounded-xl border border-rose-200 bg-rose-50 p-3 text-xs text-rose-700 font-medium flex items-center gap-2 animate-in fade-in">
                <span className="h-2 w-2 rounded-full bg-rose-500 shrink-0"></span>
                <span>{error}</span>
              </div>
            )}

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Email Address</label>
              <div className="relative">
                <Mail className="absolute left-3.5 top-3 h-4 w-4 text-slate-400" />
                <input
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="name@example.com"
                  className="w-full rounded-xl border border-slate-300 bg-slate-50 pl-10 pr-4 py-2.5 text-xs text-slate-900 placeholder-slate-400 focus:border-blue-600 focus:bg-white focus:outline-none transition-all shadow-2xs"
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={loading || !email}
              className="w-full flex items-center justify-center space-x-2 rounded-xl bg-blue-600 hover:bg-blue-700 py-3 text-xs font-bold text-white shadow-md shadow-blue-500/20 disabled:opacity-50 transition-all hover:scale-[1.01] cursor-pointer"
            >
              <span>{loading ? 'Sending Request...' : 'Send Reset Code'}</span>
              <ArrowRight className="h-4 w-4" />
            </button>

            <div className="pt-2 text-center text-xs">
              <Link href="/login" className="text-slate-500 hover:text-blue-600 font-semibold transition-colors">
                Return to Sign In
              </Link>
            </div>
          </form>
        </div>

      </div>
    </div>
  );
}
