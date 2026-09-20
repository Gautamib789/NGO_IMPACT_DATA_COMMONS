'use client';

import React, { useState, useEffect, Suspense } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { useAuth } from '@/context/AuthContext';
import { ShieldCheck, KeyRound, RefreshCw, CheckCircle2 } from 'lucide-react';

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://127.0.0.1:8000';

async function unauthFetch(endpoint: string, body: object) {
  const response = await fetch(`${API_BASE}${endpoint}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  const data = await response.json();
  if (!response.ok) {
    const msg =
      typeof data.detail === 'string'
        ? data.detail
        : Array.isArray(data.detail)
        ? data.detail.map((d: any) => d?.msg || String(d)).join('; ')
        : data.message || `HTTP ${response.status}`;
    throw new Error(msg);
  }
  return data;
}

function VerifyOTPContent() {
  const searchParams = useSearchParams();
  const { login } = useAuth();
  const router = useRouter();

  // Email: prefer URL param, then sessionStorage fallback
  const [email, setEmail] = useState('');
  const [otp, setOtp] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [message, setMessage] = useState('');
  const [resendLoading, setResendLoading] = useState(false);

  useEffect(() => {
    const urlEmail = searchParams.get('email');
    if (urlEmail) {
      setEmail(decodeURIComponent(urlEmail));
    } else if (typeof window !== 'undefined') {
      const stored = sessionStorage.getItem('otp_pending_email');
      if (stored) setEmail(stored);
    }
  }, [searchParams]);

  const handleVerify = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setMessage('');
    setLoading(true);

    try {
      // No Bearer token needed — email + OTP is the credential
      const data = await unauthFetch('/api/auth/verify-login-otp', { email, otp });

      // Clear pending OTP state
      if (typeof window !== 'undefined') {
        sessionStorage.removeItem('otp_pending_email');
      }

      // Store the final verified token + user
      login(data.access_token, {
        id: data.user_id,
        email: data.email,
        full_name: data.full_name,
        role: data.role,
      });

      if (data.role === 'ADMIN') router.push('/admin/dashboard');
      else if (data.role === 'NGO') router.push('/ngo/dashboard');
      else router.push('/');

    } catch (err: any) {
      setError(err.message || 'Incorrect verification code. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleResend = async () => {
    setError('');
    setMessage('');
    setResendLoading(true);

    try {
      // No Bearer token needed
      const data = await unauthFetch('/api/auth/resend-login-otp', { email });
      setMessage(data.message || 'Verification code resent successfully.');
      if (data.dev_note) {
        setMessage(`${data.message || 'Code resent.'} ${data.dev_note}`);
      }
    } catch (err: any) {
      setError(err.message || 'Failed to resend verification code.');
    } finally {
      setResendLoading(false);
    }
  };

  if (!email) {
    return (
      <div className="flex min-h-[85vh] items-center justify-center p-4 bg-slate-50">
        <div className="bg-white rounded-2xl border border-slate-200 p-8 text-center text-slate-600 shadow-card">
          <p>Verification session not found.</p>
          <button onClick={() => router.push('/login')} className="mt-4 text-blue-600 font-bold hover:underline">
            Return to Login
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="flex min-h-[85vh] items-center justify-center px-4 py-12 bg-slate-50">
      <div className="w-full max-w-md space-y-6">
        
        {/* Header */}
        <div className="text-center space-y-2">
          <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-2xl bg-blue-600/10 text-blue-600 border border-blue-200 shadow-sm">
            <ShieldCheck className="h-6 w-6" />
          </div>
          <h2 className="text-2xl font-bold text-slate-900 tracking-tight">Two-Factor Authentication</h2>
          <p className="text-xs text-slate-500 max-w-xs mx-auto">
            We've sent a 6-digit code to <span className="font-semibold text-slate-800">{email}</span>
          </p>
        </div>

        {/* Main Form Card */}
        <div className="bg-white rounded-2xl border border-slate-200/90 p-7 shadow-card space-y-5">
          <form onSubmit={handleVerify} className="space-y-4">
            
            {error && (
              <div className="rounded-xl border border-rose-200 bg-rose-50 p-3 text-xs text-rose-700 font-medium flex items-center gap-2 animate-in fade-in">
                <span className="h-2 w-2 rounded-full bg-rose-500 shrink-0"></span>
                <span>{error}</span>
              </div>
            )}

            {message && (
              <div className="flex items-center space-x-2 rounded-xl border border-emerald-200 bg-emerald-50 p-3 text-xs text-emerald-700 font-medium animate-in fade-in">
                <CheckCircle2 className="h-4 w-4 shrink-0" />
                <span>{message}</span>
              </div>
            )}

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Verification Code</label>
              <div className="relative">
                <KeyRound className="absolute left-3.5 top-3.5 h-4 w-4 text-slate-400" />
                <input
                  type="text"
                  required
                  maxLength={6}
                  value={otp}
                  onChange={(e) => setOtp(e.target.value.replace(/\D/g, ''))}
                  placeholder="000000"
                  className="w-full tracking-widest text-center rounded-xl border border-slate-300 bg-slate-50 pl-10 pr-4 py-3 text-lg font-mono font-bold text-slate-900 placeholder-slate-400 focus:border-blue-600 focus:bg-white focus:outline-none transition-all shadow-2xs"
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={loading || otp.length < 6}
              className="w-full flex items-center justify-center space-x-2 rounded-xl bg-blue-600 hover:bg-blue-700 py-3 text-xs font-bold text-white shadow-md shadow-blue-500/20 disabled:opacity-50 transition-all hover:scale-[1.01] cursor-pointer"
            >
              <span>{loading ? 'Verifying Code...' : 'Verify & Continue'}</span>
            </button>

            <div className="pt-2 text-center">
              <button
                type="button"
                onClick={handleResend}
                disabled={resendLoading}
                className="inline-flex items-center space-x-1.5 text-xs text-slate-500 hover:text-blue-600 disabled:opacity-50 transition-colors font-semibold cursor-pointer"
              >
                <RefreshCw className={`h-3 w-3 ${resendLoading ? 'animate-spin' : ''}`} />
                <span>{resendLoading ? 'Sending...' : 'Resend Verification Code'}</span>
              </button>
            </div>

            <div className="pt-1 text-center">
              <button
                type="button"
                onClick={() => router.push('/login')}
                className="text-xs text-slate-400 hover:text-slate-600 font-medium cursor-pointer"
              >
                ← Back to Login
              </button>
            </div>
          </form>
        </div>

      </div>
    </div>
  );
}

export default function VerifyOTPPage() {
  return (
    <Suspense fallback={<div className="flex min-h-screen items-center justify-center text-slate-500">Loading verification form...</div>}>
      <VerifyOTPContent />
    </Suspense>
  );
}
