'use client';

import React, { useState, useEffect } from 'react';
import { useAuth } from '@/context/AuthContext';
import { ShieldAlert, CheckCircle2, XCircle, AlertOctagon, Building2, Users, TrendingUp, Database, FileText, Sparkles } from 'lucide-react';

interface NGO {
  id: number;
  org_name: string;
  registration_number: string;
  tax_id: string;
  category: string;
  mission_statement: string;
  website: string;
  address: string;
  status: 'PENDING' | 'APPROVED' | 'REJECTED';
  doc_completeness_score: number;
  transparency_score: number;
  total_expenses: number;
  total_donations_received: number;
  beneficiary_count: number;
  created_at: string;
  documents: { id: number; document_type: string; file_name: string; file_path: string }[];
}

interface FraudFlag {
  id: number;
  ngo_id: number;
  ngo_name: string;
  severity: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  rule_code: string;
  description: string;
  status: 'OPEN' | 'RESOLVED';
  created_at: string;
}

export default function AdminDashboard() {
  const { apiFetch } = useAuth();
  const [stats, setStats] = useState<any>(null);
  const [pendingNgos, setPendingNgos] = useState<NGO[]>([]);
  const [allNgos, setAllNgos] = useState<NGO[]>([]);
  const [fraudFlags, setFraudFlags] = useState<FraudFlag[]>([]);
  const [activeTab, setActiveTab] = useState<'pending' | 'all' | 'fraud'>('pending');
  const [loading, setLoading] = useState(true);

  // Rejection modal
  const [rejectingNgoId, setRejectingNgoId] = useState<number | null>(null);
  const [rejectReason, setRejectReason] = useState('');

  const fetchAdminData = async () => {
    try {
      setLoading(true);
      const [sData, pData, aData, fData] = await Promise.all([
        apiFetch('/api/admin/stats'),
        apiFetch('/api/admin/ngos/pending'),
        apiFetch('/api/admin/ngos/all'),
        apiFetch('/api/fraud/flags'),
      ]);

      setStats(sData);
      setPendingNgos(pData);
      setAllNgos(aData);
      setFraudFlags(fData);
    } catch (err) {
      console.error('Failed to load admin data', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAdminData();
  }, []);

  const handleApprove = async (ngoId: number) => {
    try {
      await apiFetch(`/api/admin/ngos/${ngoId}/approve`, { method: 'POST' });
      fetchAdminData();
    } catch (err: any) {
      alert(err.message || 'Approval failed');
    }
  };

  const handleRejectSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!rejectingNgoId) return;

    try {
      await apiFetch(`/api/admin/ngos/${rejectingNgoId}/reject`, {
        method: 'POST',
        body: JSON.stringify({ reason: rejectReason }),
      });
      setRejectingNgoId(null);
      setRejectReason('');
      fetchAdminData();
    } catch (err: any) {
      alert(err.message || 'Rejection failed');
    }
  };

  const handleResolveFlag = async (flagId: number) => {
    try {
      await apiFetch(`/api/fraud/resolve/${flagId}`, { method: 'POST' });
      fetchAdminData();
    } catch (err: any) {
      alert(err.message || 'Flag resolution failed');
    }
  };

  return (
    <div className="min-h-screen bg-slate-50/60 pb-20 pt-8">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 space-y-8">
        
        {/* Admin Banner */}
        <div className="rounded-3xl border border-slate-200 bg-white p-8 shadow-card space-y-6">
          <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-6">
            <div className="space-y-2">
              <div className="inline-flex items-center space-x-2 rounded-full border border-amber-200 bg-amber-50 px-3.5 py-1 text-xs font-semibold text-amber-800">
                <ShieldAlert className="h-3.5 w-3.5 text-amber-600" />
                <span>Platform Chief Administrator & Compliance Officer</span>
              </div>
              <h1 className="text-3xl font-extrabold text-slate-900">
                Admin Governance <span className="text-blue-600">Control Panel</span>
              </h1>
              <p className="text-xs text-slate-500">Review NGO verification applications, audit AI fraud alerts, and enforce RBAC compliance.</p>
            </div>

            <div className="grid grid-cols-3 gap-3">
              <div className="bg-slate-50 p-3.5 rounded-2xl border border-slate-200 text-center min-w-[100px]">
                <span className="block text-[10px] text-slate-400 uppercase font-bold tracking-wider">Pending</span>
                <span className="text-xl font-extrabold text-amber-600">{stats?.pending_ngos || 0}</span>
              </div>
              <div className="bg-slate-50 p-3.5 rounded-2xl border border-slate-200 text-center min-w-[100px]">
                <span className="block text-[10px] text-slate-400 uppercase font-bold tracking-wider">Approved</span>
                <span className="text-xl font-extrabold text-emerald-600">{stats?.approved_ngos || 0}</span>
              </div>
              <div className="bg-slate-50 p-3.5 rounded-2xl border border-slate-200 text-center min-w-[100px]">
                <span className="block text-[10px] text-slate-400 uppercase font-bold tracking-wider">Risk Flags</span>
                <span className="text-xl font-extrabold text-rose-600">{stats?.open_fraud_flags || 0}</span>
              </div>
            </div>
          </div>
        </div>

        {/* Tab Navigation */}
        <div className="flex space-x-3 border-b border-slate-200/80 pb-3">
          <button
            onClick={() => setActiveTab('pending')}
            className={`flex items-center space-x-2 rounded-xl px-4 py-2.5 text-xs font-bold transition-all cursor-pointer ${
              activeTab === 'pending'
                ? 'bg-blue-600 text-white shadow-md shadow-blue-600/20'
                : 'border border-slate-200 bg-white text-slate-600 hover:text-slate-900 hover:bg-slate-50'
            }`}
          >
            <Building2 className="h-4 w-4" />
            <span>Pending Approvals ({pendingNgos.length})</span>
          </button>

          <button
            onClick={() => setActiveTab('all')}
            className={`flex items-center space-x-2 rounded-xl px-4 py-2.5 text-xs font-bold transition-all cursor-pointer ${
              activeTab === 'all'
                ? 'bg-blue-600 text-white shadow-md shadow-blue-600/20'
                : 'border border-slate-200 bg-white text-slate-600 hover:text-slate-900 hover:bg-slate-50'
            }`}
          >
            <CheckCircle2 className="h-4 w-4" />
            <span>All Registered NGOs ({allNgos.length})</span>
          </button>

          <button
            onClick={() => setActiveTab('fraud')}
            className={`flex items-center space-x-2 rounded-xl px-4 py-2.5 text-xs font-bold transition-all cursor-pointer ${
              activeTab === 'fraud'
                ? 'bg-blue-600 text-white shadow-md shadow-blue-600/20'
                : 'border border-slate-200 bg-white text-slate-600 hover:text-slate-900 hover:bg-slate-50'
            }`}
          >
            <AlertOctagon className="h-4 w-4" />
            <span>AI Fraud & Risk Flags ({fraudFlags.filter(f => f.status === 'OPEN').length})</span>
          </button>
        </div>

        {/* Tab Content */}
        {loading ? (
          <div className="text-center py-16 text-slate-400">
            <div className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-blue-600 border-t-transparent mb-3"></div>
            <p className="text-xs font-semibold">Loading compliance records...</p>
          </div>
        ) : activeTab === 'pending' ? (
          <div className="space-y-4">
            {pendingNgos.length === 0 ? (
              <div className="bg-white rounded-2xl border border-slate-200/80 p-12 text-center text-slate-500 shadow-card">
                <CheckCircle2 className="mx-auto h-10 w-10 text-emerald-600 mb-2" />
                <p className="text-base font-bold text-slate-900">No pending NGO approval requests.</p>
                <p className="text-xs text-slate-500 mt-1">All submitted applications have been audited.</p>
              </div>
            ) : (
              pendingNgos.map((ngo) => (
                <div key={ngo.id} className="bg-white rounded-2xl border border-slate-200/80 p-6 space-y-4 shadow-card border-l-4 border-l-amber-500">
                  <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2 border-b border-slate-100 pb-3">
                    <div>
                      <span className="text-[10px] font-bold text-amber-700 uppercase tracking-wider bg-amber-50 px-2 py-0.5 rounded border border-amber-200">Pending Review</span>
                      <h3 className="text-lg font-bold text-slate-900 mt-1">{ngo.org_name}</h3>
                      <p className="text-xs text-slate-500 font-mono">Reg #: {ngo.registration_number} • Tax ID: {ngo.tax_id}</p>
                    </div>

                    <div className="flex items-center space-x-2">
                      <button
                        onClick={() => handleApprove(ngo.id)}
                        className="flex items-center space-x-1.5 rounded-xl bg-emerald-600 hover:bg-emerald-700 px-4 py-2 text-xs font-bold text-white shadow-xs shadow-emerald-600/20 cursor-pointer"
                      >
                        <CheckCircle2 className="h-4 w-4" />
                        <span>Approve NGO</span>
                      </button>
                      <button
                        onClick={() => setRejectingNgoId(ngo.id)}
                        className="flex items-center space-x-1.5 rounded-xl border border-rose-200 bg-rose-50 hover:bg-rose-100 px-4 py-2 text-xs font-bold text-rose-700 cursor-pointer"
                      >
                        <XCircle className="h-4 w-4" />
                        <span>Reject</span>
                      </button>
                    </div>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
                    <div>
                      <span className="block font-bold text-slate-700 mb-1">Mission & Domain:</span>
                      <p className="text-slate-600 bg-slate-50 p-3 rounded-xl border border-slate-200/80">{ngo.mission_statement || 'N/A'}</p>
                    </div>

                    <div>
                      <span className="block font-bold text-slate-700 mb-1">Uploaded Audit Documents ({ngo.documents.length}):</span>
                      {ngo.documents.length === 0 ? (
                        <p className="text-slate-400 italic">No files uploaded yet.</p>
                      ) : (
                        <div className="space-y-1.5">
                          {ngo.documents.map((doc) => (
                            <div key={doc.id} className="flex items-center space-x-2 bg-slate-50 p-2 rounded-lg border border-slate-200/80 text-[11px] text-slate-700 font-medium">
                              <FileText className="h-3.5 w-3.5 text-blue-600" />
                              <span>{doc.document_type}: {doc.file_name}</span>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        ) : activeTab === 'all' ? (
          <div className="bg-white rounded-2xl border border-slate-200/80 p-6 shadow-card">
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="border-b border-slate-200 bg-slate-50 text-slate-500 font-bold uppercase text-[10px]">
                  <tr>
                    <th className="p-3.5">Organization Name</th>
                    <th className="p-3.5">Registration #</th>
                    <th className="p-3.5">Category</th>
                    <th className="p-3.5">Transparency Score</th>
                    <th className="p-3.5">Status</th>
                    <th className="p-3.5">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {allNgos.map((ngo) => (
                    <tr key={ngo.id} className="hover:bg-slate-50/80 transition-colors">
                      <td className="p-3.5 font-bold text-slate-900">{ngo.org_name}</td>
                      <td className="p-3.5 font-mono text-slate-500">{ngo.registration_number}</td>
                      <td className="p-3.5 text-slate-600 font-medium">{ngo.category}</td>
                      <td className="p-3.5 font-bold text-emerald-700">{ngo.transparency_score}%</td>
                      <td className="p-3.5">
                        <span className={`px-2.5 py-0.5 rounded-full text-[10px] font-bold uppercase border ${
                          ngo.status === 'APPROVED' ? 'bg-emerald-50 text-emerald-700 border-emerald-200' :
                          ngo.status === 'PENDING' ? 'bg-amber-50 text-amber-700 border-amber-200' :
                          'bg-rose-50 text-rose-700 border-rose-200'
                        }`}>
                          {ngo.status}
                        </span>
                      </td>
                      <td className="p-3.5 space-x-2">
                        {ngo.status !== 'APPROVED' && (
                          <button
                            onClick={() => handleApprove(ngo.id)}
                            className="rounded-lg bg-emerald-600 px-3 py-1 text-[11px] font-bold text-white hover:bg-emerald-700 cursor-pointer"
                          >
                            Approve
                          </button>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        ) : (
          /* AI Fraud Flags Tab */
          <div className="space-y-4">
            {fraudFlags.length === 0 ? (
              <div className="bg-white rounded-2xl border border-slate-200/80 p-12 text-center text-slate-500 shadow-card">
                <CheckCircle2 className="mx-auto h-10 w-10 text-emerald-600 mb-2" />
                <p className="text-base font-bold text-slate-900">No AI Fraud alerts generated.</p>
                <p className="text-xs text-slate-500 mt-1">All financial ratios and registration details comply with rules.</p>
              </div>
            ) : (
              fraudFlags.map((flag) => (
                <div key={flag.id} className={`bg-white rounded-2xl border border-slate-200/80 p-5 space-y-3 shadow-card border-l-4 ${
                  flag.severity === 'CRITICAL' ? 'border-l-rose-500' :
                  flag.severity === 'HIGH' ? 'border-l-orange-500' : 'border-l-amber-500'
                }`}>
                  <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
                    <div className="flex items-center space-x-2">
                      <span className={`px-2.5 py-0.5 rounded-full text-[10px] font-bold uppercase ${
                        flag.severity === 'CRITICAL' ? 'bg-rose-50 text-rose-700 border border-rose-200' :
                        flag.severity === 'HIGH' ? 'bg-orange-50 text-orange-700 border border-orange-200' :
                        'bg-amber-50 text-amber-700 border border-amber-200'
                      }`}>
                        {flag.severity} RISK
                      </span>
                      <span className="font-bold text-slate-900 text-sm">{flag.ngo_name}</span>
                      <span className="text-xs text-slate-500 font-mono">[{flag.rule_code}]</span>
                    </div>

                    {flag.status === 'OPEN' ? (
                      <button
                        onClick={() => handleResolveFlag(flag.id)}
                        className="rounded-xl border border-slate-200 bg-slate-50 hover:bg-slate-100 px-3 py-1.5 text-xs font-bold text-slate-700 cursor-pointer"
                      >
                        Resolve & Recalculate Score
                      </button>
                    ) : (
                      <span className="text-xs font-bold text-emerald-600 bg-emerald-50 px-2.5 py-1 rounded-full border border-emerald-200">RESOLVED</span>
                    )}
                  </div>

                  <p className="text-xs text-slate-600 bg-slate-50 p-3 rounded-xl border border-slate-200/80">
                    {flag.description}
                  </p>
                </div>
              ))
            )}
          </div>
        )}

        {/* Reject Reason Modal */}
        {rejectingNgoId && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/60 backdrop-blur-sm p-4">
            <form onSubmit={handleRejectSubmit} className="w-full max-w-md rounded-2xl border border-slate-100 bg-white p-6 space-y-4 shadow-2xl">
              <h3 className="text-lg font-bold text-slate-900">Specify Rejection Reason</h3>
              <textarea
                rows={3}
                required
                value={rejectReason}
                onChange={(e) => setRejectReason(e.target.value)}
                placeholder="State why this NGO registration is rejected..."
                className="w-full rounded-xl border border-slate-200 bg-slate-50 p-3 text-xs text-slate-900 placeholder-slate-400 focus:border-rose-500 focus:bg-white focus:outline-none"
              />
              <div className="flex space-x-2">
                <button
                  type="button"
                  onClick={() => setRejectingNgoId(null)}
                  className="w-1/2 rounded-xl border border-slate-200 bg-slate-50 py-2.5 text-xs font-semibold text-slate-600 hover:bg-slate-100"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="w-1/2 rounded-xl bg-rose-600 py-2.5 text-xs font-bold text-white hover:bg-rose-700 shadow-sm shadow-rose-600/20"
                >
                  Confirm Rejection
                </button>
              </div>
            </form>
          </div>
        )}

      </div>
    </div>
  );
}
