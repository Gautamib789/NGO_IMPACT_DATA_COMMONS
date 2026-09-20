'use client';

import React, { useState, useEffect, Suspense } from 'react';
import Link from 'next/link';
import { useRouter, useSearchParams } from 'next/navigation';
import { useAuth, UserRole } from '@/context/AuthContext';
import { ShieldCheck, LogIn, Lock, Mail, Sparkles, CheckCircle2, ArrowRight } from 'lucide-react';

function LoginContent() {
  const searchParams = useSearchParams();
  const initRole = searchParams.get('role') as UserRole || 'DONOR';

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [role, setRole] = useState<UserRole>(initRole);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const { login, apiFetch } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (searchParams.get('role')) {
      setRole(searchParams.get('role') as UserRole);
    }
  }, [searchParams]);

  const handleLogin = async (e?: React.FormEvent, customEmail?: string, customPassword?: string) => {
    if (e) e.preventDefault();
    setError('');
    setLoading(true);

    const loginEmail = customEmail || email;
    const loginPassword = customPassword || password;

    try {
      const data = await apiFetch('/api/auth/login', {
        method: 'POST',
        body: JSON.stringify({ email: loginEmail, password: loginPassword }),
      });

      if (data.requires_otp) {
        // NGO / Admin: OTP required — do NOT store partial pre-auth token.
        // The full authenticated token is only issued after OTP verification.
        // Store email in sessionStorage as a fallback for verify-otp page.
        if (typeof window !== 'undefined') {
          sessionStorage.setItem('otp_pending_email', data.email);
        }
        router.push(`/verify-otp?email=${encodeURIComponent(data.email)}`);
      } else {
        // Donor: no OTP step — issue final token immediately.
        login(data.access_token, {
          id: data.user_id,
          email: data.email,
          full_name: data.full_name,
          role: data.role,
        });
        router.push('/choose-role');
      }
    } catch (err: any) {
      setError(err.message || 'Invalid credentials');
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
            <ShieldCheck className="h-6 w-6" />
          </div>
          <h2 className="text-2xl font-bold text-slate-900 tracking-tight">Sign in to NGO Impact</h2>
          <p className="text-xs text-slate-500 max-w-xs mx-auto">Access role-restricted features & SHA-256 ledger tools.</p>
        </div>

        {/* Main Form Card */}
        <div className="bg-white rounded-2xl border border-slate-200/90 p-7 shadow-card space-y-5">
          
          <form onSubmit={handleLogin} className="space-y-4">
            
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

            <div>
              <div className="flex items-center justify-between mb-1">
                <label className="block text-xs font-semibold text-slate-700">Password</label>
                <Link href="/forgot-password" className="text-xs text-blue-600 font-semibold hover:underline">
                  Forgot Password?
                </Link>
              </div>
              <div className="relative">
                <Lock className="absolute left-3.5 top-3 h-4 w-4 text-slate-400" />
                <input
                  type="password"
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••"
                  className="w-full rounded-xl border border-slate-300 bg-slate-50 pl-10 pr-4 py-2.5 text-xs text-slate-900 placeholder-slate-400 focus:border-blue-600 focus:bg-white focus:outline-none transition-all shadow-2xs"
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full flex items-center justify-center space-x-2 rounded-xl bg-blue-600 hover:bg-blue-700 py-3 text-xs font-bold text-white shadow-md shadow-blue-500/20 disabled:opacity-50 transition-all hover:scale-[1.01] cursor-pointer"
            >
              <LogIn className="h-4 w-4" />
              <span>{loading ? 'Authenticating...' : 'Sign In'}</span>
            </button>

          </form>

          {/* Quick Demo Login Credentials Preset */}
          <div className="pt-2 border-t border-slate-100 space-y-2">
            <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block text-center">Quick Demo Profiles</span>
            <div className="grid grid-cols-3 gap-2">
              <button
                type="button"
                onClick={() => handleLogin(undefined, 'donor@example.com', 'DonorPassword123!')}
                className="py-1.5 px-2 rounded-lg border border-slate-200 bg-slate-50 hover:bg-emerald-50 hover:border-emerald-200 hover:text-emerald-700 text-[10px] font-semibold text-slate-600 transition-all text-center"
              >
                Donor Demo
              </button>
              <button
                type="button"
                onClick={() => handleLogin(undefined, 'contact@hopefoundation.org', 'NgoPassword123!')}
                className="py-1.5 px-2 rounded-lg border border-slate-200 bg-slate-50 hover:bg-blue-50 hover:border-blue-200 hover:text-blue-700 text-[10px] font-semibold text-slate-600 transition-all text-center"
              >
                NGO Demo
              </button>
              <button
                type="button"
                onClick={() => handleLogin(undefined, 'admin@ngoimpact.org', 'AdminPassword123!')}
                className="py-1.5 px-2 rounded-lg border border-slate-200 bg-slate-50 hover:bg-amber-50 hover:border-amber-200 hover:text-amber-700 text-[10px] font-semibold text-slate-600 transition-all text-center"
              >
                Admin Demo
              </button>
            </div>
          </div>

          <div className="pt-3 border-t border-slate-100 text-center">
            <p className="text-xs text-slate-500">
              Don't have an account?{' '}
              <Link href="/register" className="text-blue-600 font-bold hover:underline">
                Register here
              </Link>
            </p>
          </div>

        </div>

        {/* Security Badge */}
        <div className="flex items-center justify-center space-x-2 text-slate-400 text-xs">
          <CheckCircle2 className="h-4 w-4 text-emerald-500" />
          <span>256-bit Encrypted Session & SHA-256 Ledger Audit</span>
        </div>

      </div>
    </div>
  );
}

export default function LoginPage() {
  return (
    <Suspense fallback={<div className="flex min-h-screen items-center justify-center text-slate-500">Loading sign-in form...</div>}>
      <LoginContent />
    </Suspense>
  );
}
