'use client';

import React, { useState, Suspense } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { useAuth } from '@/context/AuthContext';
import { KeyRound, Lock, CheckCircle2, AlertTriangle } from 'lucide-react';

function ResetPasswordContent() {
  const searchParams = useSearchParams();
  const email = searchParams.get('email') || '';
  const isDevMode = searchParams.get('dev_mode') === 'true';
  
  const [otp, setOtp] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);
  
  const { apiFetch } = useAuth();
  const router = useRouter();

  const handleReset = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    if (newPassword !== confirmPassword) {
      setError('Passwords do not match');
      return;
    }
    
    if (newPassword.length < 8) {
      setError('Password must be at least 8 characters long');
      return;
    }

    setLoading(true);

    try {
      await apiFetch('/api/auth/reset-password', {
        method: 'POST',
        body: JSON.stringify({ email, otp, new_password: newPassword }),
      });
      setSuccess(true);
      setTimeout(() => {
        router.push('/choose-role');
      }, 3000);
    } catch (err: any) {
      setError(err.message || 'Invalid or expired OTP');
    } finally {
      setLoading(false);
    }
  };

  if (success) {
    return (
      <div className="flex min-h-[85vh] items-center justify-center p-4 bg-slate-50">
        <div className="bg-white rounded-2xl border border-slate-200 p-8 text-center space-y-4 shadow-card max-w-sm">
          <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-full bg-emerald-100 text-emerald-600">
            <CheckCircle2 className="h-8 w-8" />
          </div>
          <h2 className="text-xl font-bold text-slate-900">Password Reset Successful</h2>
          <p className="text-slate-500 text-xs">You will be redirected to the login page shortly.</p>
        </div>
      </div>
    );
  }

  if (!email) {
    return (
      <div className="flex min-h-[85vh] items-center justify-center p-4 bg-slate-50">
        <div className="bg-white rounded-2xl border border-slate-200 p-8 text-center text-slate-600 shadow-card">
          <p>Missing email parameter.</p>
          <button onClick={() => router.push('/forgot-password')} className="mt-4 text-blue-600 font-bold hover:underline">
            Go back
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
          <h2 className="text-2xl font-bold text-slate-900 tracking-tight">Set New Password</h2>
          <p className="text-xs text-slate-500 max-w-xs mx-auto">
            Enter the 6-digit code sent to <span className="font-semibold text-slate-800">{email}</span> and your new password.
          </p>
        </div>

        {/* Main Form Card */}
        <div className="bg-white rounded-2xl border border-slate-200/90 p-7 shadow-card space-y-5">
          <form onSubmit={handleReset} className="space-y-4">
            
            {isDevMode && (
              <div className="rounded-xl border border-amber-300 bg-amber-50 p-3 text-xs text-amber-900 space-y-1">
                <div className="font-bold flex items-center space-x-1">
                  <AlertTriangle className="h-4 w-4 text-amber-600 shrink-0 inline mr-1" />
                  <span>Development Mode Active</span>
                </div>
                <p className="text-amber-800 text-[11px] leading-relaxed">
                  The 6-digit code was logged to <code className="bg-amber-100 px-1 py-0.5 rounded font-mono text-amber-950">backend/mock_email.txt</code> and server terminal logs.
                </p>
              </div>
            )}

            {error && (
              <div className="rounded-xl border border-rose-200 bg-rose-50 p-3 text-xs text-rose-700 font-medium flex items-center gap-2 animate-in fade-in">
                <span className="h-2 w-2 rounded-full bg-rose-500 shrink-0"></span>
                <span>{error}</span>
              </div>
            )}

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Verification Code</label>
              <div className="relative">
                <KeyRound className="absolute left-3.5 top-3 h-4 w-4 text-slate-400" />
                <input
                  type="text"
                  required
                  maxLength={6}
                  value={otp}
                  onChange={(e) => setOtp(e.target.value.replace(/\D/g, ''))}
                  placeholder="000000"
                  className="w-full tracking-widest text-center rounded-xl border border-slate-300 bg-slate-50 pl-10 pr-4 py-2.5 text-sm font-mono text-slate-900 placeholder-slate-400 focus:border-blue-600 focus:bg-white focus:outline-none transition-all shadow-2xs"
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">New Password</label>
              <div className="relative">
                <Lock className="absolute left-3.5 top-3 h-4 w-4 text-slate-400" />
                <input
                  type="password"
                  required
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                  placeholder="••••••••"
                  className="w-full rounded-xl border border-slate-300 bg-slate-50 pl-10 pr-4 py-2.5 text-xs text-slate-900 placeholder-slate-400 focus:border-blue-600 focus:bg-white focus:outline-none transition-all shadow-2xs"
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Confirm New Password</label>
              <div className="relative">
                <Lock className="absolute left-3.5 top-3 h-4 w-4 text-slate-400" />
                <input
                  type="password"
                  required
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  placeholder="••••••••"
                  className="w-full rounded-xl border border-slate-300 bg-slate-50 pl-10 pr-4 py-2.5 text-xs text-slate-900 placeholder-slate-400 focus:border-blue-600 focus:bg-white focus:outline-none transition-all shadow-2xs"
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={loading || otp.length < 6 || !newPassword}
              className="w-full flex items-center justify-center rounded-xl bg-blue-600 hover:bg-blue-700 py-3 text-xs font-bold text-white shadow-md shadow-blue-500/20 disabled:opacity-50 transition-all hover:scale-[1.01] cursor-pointer"
            >
              <span>{loading ? 'Resetting...' : 'Confirm Reset'}</span>
            </button>
          </form>
        </div>

      </div>
    </div>
  );
}

export default function ResetPasswordPage() {
  return (
    <Suspense fallback={<div className="flex min-h-screen items-center justify-center text-slate-500">Loading form...</div>}>
      <ResetPasswordContent />
    </Suspense>
  );
}
