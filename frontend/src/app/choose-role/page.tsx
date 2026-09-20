'use client';

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth, UserRole } from '@/context/AuthContext';
import { ShieldCheck, HeartHandshake, LayoutDashboard, ShieldAlert, Globe, ArrowRight } from 'lucide-react';

export default function ChooseRolePage() {
  const { user, apiFetch } = useAuth();
  const router = useRouter();
  const [loading, setLoading] = useState<string | null>(null);
  const [error, setError] = useState('');

  // Protect the route
  React.useEffect(() => {
    if (!user) {
      router.push('/');
    }
  }, [user, router]);

  const handleRoleSelection = async (targetRole: 'PUBLIC' | UserRole) => {
    setError('');
    setLoading(targetRole);

    try {
      if (targetRole === 'PUBLIC') {
        router.push('/explore');
        return;
      }

      if (targetRole === 'DONOR') {
        router.push('/donor/dashboard');
        return;
      }

      if (targetRole === 'NGO' || targetRole === 'ADMIN') {
        // Enforce OTP Generation
        await apiFetch('/api/auth/generate-role-otp', {
          method: 'POST',
        });
        
        router.push('/verify-otp');
      }
    } catch (err: any) {
      setError(err.message || 'Authorization failed for selected role.');
      setLoading(null);
    }
  };

  const roles = [
    {
      id: 'PUBLIC',
      title: 'Public Viewer',
      description: 'Explore active NGOs, audit impact statistics, and view our SHA-256 transparent ledger.',
      icon: Globe,
      color: 'bg-white hover:bg-slate-50 border-slate-200 text-slate-700 hover:border-slate-300'
    },
    {
      id: 'DONOR',
      title: 'Donor Account',
      description: 'Donate directly to compliance-approved NGOs and track certified contribution records.',
      icon: HeartHandshake,
      color: 'bg-white hover:bg-emerald-50/50 border-emerald-200/80 text-emerald-900 hover:border-emerald-400'
    },
    {
      id: 'NGO',
      title: 'NGO Partner Portal',
      description: 'Manage your organization profile, track incoming donations, and submit project evidence.',
      icon: LayoutDashboard,
      color: 'bg-white hover:bg-blue-50/50 border-blue-200/80 text-blue-900 hover:border-blue-400'
    },
    {
      id: 'ADMIN',
      title: 'Platform Administrator',
      description: 'Review NGO verification audits, evaluate AI fraud alerts, and oversee platform integrity.',
      icon: ShieldAlert,
      color: 'bg-white hover:bg-amber-50/50 border-amber-200/80 text-amber-900 hover:border-amber-400'
    }
  ];

  if (!user) {
    return <div className="min-h-screen text-slate-500 flex items-center justify-center bg-slate-50">Authenticating user session...</div>;
  }

  return (
    <div className="flex min-h-[85vh] items-center justify-center bg-slate-50 p-6">
      <div className="w-full max-w-4xl">
        <div className="text-center mb-10 space-y-2">
          <div className="flex justify-center mb-3">
            <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-blue-600/10 text-blue-600 border border-blue-200 shadow-sm">
              <ShieldCheck className="h-8 w-8" />
            </div>
          </div>
          <h1 className="text-3xl font-bold tracking-tight text-slate-900">Select Access Portal</h1>
          <p className="text-sm text-slate-500 max-w-xl mx-auto">
            Choose your interaction role to proceed with session-authenticated platform capabilities.
          </p>
          
          {error && (
            <div className="mt-4 max-w-md mx-auto rounded-xl border border-rose-200 bg-rose-50 p-3 text-xs text-rose-700 font-medium">
              {error}
            </div>
          )}
        </div>

        <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-2">
          {roles.map((role) => {
            const Icon = role.icon;
            const isClicking = loading === role.id;
            return (
              <button
                key={role.id}
                onClick={() => handleRoleSelection(role.id as any)}
                disabled={!!loading}
                className={`group relative text-left rounded-2xl border p-6 shadow-card hover:shadow-card-hover transition-all hover:-translate-y-0.5 cursor-pointer ${role.color} ${loading && !isClicking ? 'opacity-50 grayscale' : ''}`}
              >
                <div className="flex items-center justify-between gap-4 mb-3">
                  <div className="flex items-center gap-3">
                    <div className="p-3 rounded-xl bg-slate-100/80 group-hover:bg-white transition-colors">
                      {isClicking ? (
                        <div className="h-6 w-6 animate-spin rounded-full border-2 border-blue-600 border-t-transparent"></div>
                      ) : (
                        <Icon className="h-6 w-6 text-slate-700 group-hover:text-blue-600 transition-colors" />
                      )}
                    </div>
                    <h3 className="text-lg font-bold text-slate-900">{role.title}</h3>
                  </div>
                  <ArrowRight className="h-4 w-4 text-slate-300 group-hover:text-blue-600 group-hover:translate-x-1 transition-all" />
                </div>
                <p className="text-xs text-slate-500 leading-relaxed pl-1">
                  {role.description}
                </p>
              </button>
            )
          })}
        </div>
      </div>
    </div>
  );
}
