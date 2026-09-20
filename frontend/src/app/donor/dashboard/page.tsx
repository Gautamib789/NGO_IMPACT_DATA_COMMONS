'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { useAuth } from '@/context/AuthContext';
import { HeartHandshake, ShieldCheck, Database, Calendar, ExternalLink, ArrowRight, Wallet, Award, CheckCircle2 } from 'lucide-react';
import { formatCurrency } from '@/utils/formatCurrency';

interface Donation {
  id: number;
  ngo_id: number;
  amount: number;
  currency: string;
  donor_name: string;
  message: string;
  transaction_hash: string;
  status: string;
  created_at: string;
  ngo_name: string;
}

export default function DonorDashboard() {
  const { user, apiFetch } = useAuth();
  const [donations, setDonations] = useState<Donation[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchMyDonations = async () => {
    try {
      setLoading(true);
      const data = await apiFetch('/api/donations/my-donations');
      setDonations(data);
    } catch (err) {
      console.error('Failed to load donor history', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchMyDonations();
  }, []);

  const totalDonated = donations.reduce((sum, d) => sum + d.amount, 0);

  return (
    <div className="min-h-screen bg-slate-50/60 pb-20 pt-8">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 space-y-8">
        
        {/* Donor Banner */}
        <div className="rounded-3xl border border-slate-200 bg-white p-8 shadow-card space-y-6">
          <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-6">
            <div className="space-y-2">
              <div className="inline-flex items-center space-x-2 rounded-full border border-blue-200 bg-blue-50 px-3.5 py-1 text-xs font-semibold text-blue-700">
                <HeartHandshake className="h-3.5 w-3.5" />
                <span>Verified Philanthropist Portal</span>
              </div>
              <h1 className="text-3xl font-extrabold text-slate-900">
                Welcome back, <span className="text-blue-600">{user?.full_name}</span>
              </h1>
              <p className="text-xs text-slate-500">Track your contributions sealed on the cryptographic hash-chain ledger.</p>
            </div>

            <div className="flex items-center space-x-4 bg-slate-50 p-4.5 rounded-2xl border border-slate-200 min-w-[220px]">
              <div className="flex h-12 w-12 items-center justify-center rounded-xl bg-blue-600/10 text-blue-600 border border-blue-200">
                <Wallet className="h-6 w-6" />
              </div>
              <div>
                <span className="text-[10px] text-slate-400 uppercase font-bold tracking-wider block">Total Impact Contributed</span>
                <p className="text-2xl font-extrabold text-slate-900">{formatCurrency(totalDonated, 'INR')}</p>
              </div>
            </div>
          </div>
        </div>

        {/* Donation History Table */}
        <div className="bg-white rounded-2xl border border-slate-200/80 p-6 shadow-card space-y-4">
          <div className="flex items-center justify-between border-b border-slate-100 pb-4">
            <h2 className="text-lg font-bold text-slate-900 flex items-center gap-2">
              <Database className="h-5 w-5 text-blue-600" />
              Cryptographic Donation Receipts
            </h2>
            <Link
              href="/explore"
              className="flex items-center space-x-1 text-xs font-bold text-blue-600 hover:underline"
            >
              <span>Explore More NGOs</span>
              <ArrowRight className="h-3.5 w-3.5" />
            </Link>
          </div>

          {loading ? (
            <div className="text-center py-12 text-slate-400">
              <div className="inline-block h-6 w-6 animate-spin rounded-full border-2 border-blue-600 border-t-transparent mb-2"></div>
              <p className="text-xs font-semibold">Fetching verified receipts...</p>
            </div>
          ) : donations.length === 0 ? (
            <div className="text-center py-12 text-slate-500 space-y-3">
              <HeartHandshake className="mx-auto h-10 w-10 text-slate-400" />
              <p className="text-sm font-semibold text-slate-900">You haven't logged any donations yet.</p>
              <p className="text-xs text-slate-500 max-w-md mx-auto">Browse approved NGOs on our public directory to make your first verified impact contribution.</p>
              <Link
                href="/explore"
                className="inline-flex items-center space-x-2 rounded-xl bg-blue-600 px-5 py-2.5 text-xs font-bold text-white hover:bg-blue-700 shadow-sm shadow-blue-600/20 mt-2"
              >
                <span>Explore Verified Directory</span>
              </Link>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="border-b border-slate-200 bg-slate-50 text-slate-500 font-bold uppercase text-[10px]">
                  <tr>
                    <th className="p-3.5">Date</th>
                    <th className="p-3.5">Recipient NGO</th>
                    <th className="p-3.5">Amount</th>
                    <th className="p-3.5">Transaction Hash</th>
                    <th className="p-3.5">Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {donations.map((don) => (
                    <tr key={don.id} className="hover:bg-slate-50/80 transition-colors">
                      <td className="p-3.5 text-slate-600 font-medium whitespace-nowrap">
                        {new Date(don.created_at).toLocaleDateString()}
                      </td>
                      <td className="p-3.5 font-bold text-slate-900">
                        {don.ngo_name}
                      </td>
                      <td className="p-3.5 font-bold text-emerald-700 whitespace-nowrap">
                        {formatCurrency(don.amount, don.currency || 'INR')}
                      </td>
                      <td className="p-3.5 font-mono text-[11px] text-slate-500">
                        <span className="bg-slate-50 px-2.5 py-1 rounded-lg border border-slate-200 text-blue-600 break-all block max-w-xs truncate font-semibold">
                          {don.transaction_hash}
                        </span>
                      </td>
                      <td className="p-3.5">
                        <span className="inline-flex items-center space-x-1 rounded-full bg-emerald-50 px-2.5 py-1 text-[10px] font-bold text-emerald-700 border border-emerald-200">
                          <CheckCircle2 className="h-3 w-3 text-emerald-600" />
                          <span>Sealed</span>
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

      </div>
    </div>
  );
}
