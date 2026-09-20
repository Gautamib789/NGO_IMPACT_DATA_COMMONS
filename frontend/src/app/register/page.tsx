'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useAuth, UserRole } from '@/context/AuthContext';
import { ShieldCheck, UserPlus, User, Mail, Lock, Building2, HeartHandshake, ShieldAlert, CheckCircle2 } from 'lucide-react';

export default function RegisterPage() {
  const [fullName, setFullName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [role, setRole] = useState<UserRole>('DONOR');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const { login, apiFetch } = useAuth();
  const router = useRouter();

  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      const data = await apiFetch('/api/auth/register', {
        method: 'POST',
        body: JSON.stringify({
          full_name: fullName,
          email,
          password,
          role,
        }),
      });

      login(data.access_token, {
        id: data.user_id,
        email: data.email,
        full_name: data.full_name,
        role: data.role,
      });

      if (data.role === 'NGO') router.push('/ngo/dashboard');
      else if (data.role === 'ADMIN') router.push('/admin/dashboard');
      else router.push('/donor/dashboard');

    } catch (err: any) {
      setError(err.message || 'Registration failed');
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
          <h2 className="text-2xl font-bold text-slate-900 tracking-tight">Create Platform Account</h2>
          <p className="text-xs text-slate-500 max-w-xs mx-auto">Join as a Donor, NGO Representative, or Platform Administrator.</p>
        </div>

        {/* Card */}
        <div className="bg-white rounded-2xl border border-slate-200/90 p-7 shadow-card space-y-5">
          
          <form onSubmit={handleRegister} className="space-y-4">
            
            {error && (
              <div className="rounded-xl border border-rose-200 bg-rose-50 p-3 text-xs text-rose-700 font-medium flex items-center gap-2 animate-in fade-in">
                <span className="h-2 w-2 rounded-full bg-rose-500 shrink-0"></span>
                <span>{error}</span>
              </div>
            )}

            {/* Role Selection Tabs */}
            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-2">Select Account Role</label>
              <div className="grid grid-cols-3 gap-2">
                <button
                  type="button"
                  onClick={() => setRole('DONOR')}
                  className={`flex flex-col items-center justify-center rounded-xl p-3 border text-xs font-bold transition-all cursor-pointer ${
                    role === 'DONOR'
                      ? 'border-blue-600 bg-blue-50 text-blue-700 shadow-2xs'
                      : 'border-slate-200 bg-slate-50 text-slate-600 hover:bg-slate-100'
                  }`}
                >
                  <HeartHandshake className="h-4 w-4 mb-1" />
                  <span>Donor</span>
                </button>

                <button
                  type="button"
                  onClick={() => setRole('NGO')}
                  className={`flex flex-col items-center justify-center rounded-xl p-3 border text-xs font-bold transition-all cursor-pointer ${
                    role === 'NGO'
                      ? 'border-blue-600 bg-blue-50 text-blue-700 shadow-2xs'
                      : 'border-slate-200 bg-slate-50 text-slate-600 hover:bg-slate-100'
                  }`}
                >
                  <Building2 className="h-4 w-4 mb-1" />
                  <span>NGO Org</span>
                </button>

                <button
                  type="button"
                  onClick={() => setRole('ADMIN')}
                  className={`flex flex-col items-center justify-center rounded-xl p-3 border text-xs font-bold transition-all cursor-pointer ${
                    role === 'ADMIN'
                      ? 'border-amber-500 bg-amber-50 text-amber-800 shadow-2xs'
                      : 'border-slate-200 bg-slate-50 text-slate-600 hover:bg-slate-100'
                  }`}
                >
                  <ShieldAlert className="h-4 w-4 mb-1" />
                  <span>Admin</span>
                </button>
              </div>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Full Name / Org Representative</label>
              <div className="relative">
                <User className="absolute left-3.5 top-3 h-4 w-4 text-slate-400" />
                <input
                  type="text"
                  required
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  placeholder="Jane Doe"
                  className="w-full rounded-xl border border-slate-300 bg-slate-50 pl-10 pr-4 py-2.5 text-xs text-slate-900 placeholder-slate-400 focus:border-blue-600 focus:bg-white focus:outline-none transition-all shadow-2xs"
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Email Address</label>
              <div className="relative">
                <Mail className="absolute left-3.5 top-3 h-4 w-4 text-slate-400" />
                <input
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="jane@example.com"
                  className="w-full rounded-xl border border-slate-300 bg-slate-50 pl-10 pr-4 py-2.5 text-xs text-slate-900 placeholder-slate-400 focus:border-blue-600 focus:bg-white focus:outline-none transition-all shadow-2xs"
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 mb-1">Password</label>
              <div className="relative">
                <Lock className="absolute left-3.5 top-3 h-4 w-4 text-slate-400" />
                <input
                  type="password"
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="At least 6 characters"
                  className="w-full rounded-xl border border-slate-300 bg-slate-50 pl-10 pr-4 py-2.5 text-xs text-slate-900 placeholder-slate-400 focus:border-blue-600 focus:bg-white focus:outline-none transition-all shadow-2xs"
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full flex items-center justify-center space-x-2 rounded-xl bg-blue-600 hover:bg-blue-700 py-3 text-xs font-bold text-white shadow-md shadow-blue-500/20 disabled:opacity-50 transition-all hover:scale-[1.01] cursor-pointer"
            >
              <UserPlus className="h-4 w-4" />
              <span>{loading ? 'Creating Account...' : 'Complete Registration'}</span>
            </button>

            <div className="pt-3 border-t border-slate-100 text-center">
              <p className="text-xs text-slate-500">
                Already registered?{' '}
                <Link href="/login" className="text-blue-600 font-bold hover:underline">
                  Log in here
                </Link>
              </p>
            </div>

          </form>

        </div>

        {/* Security Badge */}
        <div className="flex items-center justify-center space-x-2 text-slate-400 text-xs">
          <CheckCircle2 className="h-4 w-4 text-emerald-500" />
          <span>Encrypted Password Hashing & Role-Based Access Control</span>
        </div>

      </div>
    </div>
  );
}
