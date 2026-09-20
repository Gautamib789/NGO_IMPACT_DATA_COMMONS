'use client';

import React, { useState, useEffect } from 'react';
import { useAuth } from '@/context/AuthContext';
import { ShieldCheck, AlertTriangle, CheckCircle2, XCircle, RefreshCw, Landmark, FileCheck } from 'lucide-react';
import { GovernmentVerification } from './types';

export default function GovernmentVerificationTab() {
  const { apiFetch } = useAuth();
  const [data, setData] = useState<GovernmentVerification | null>(null);
  const [loading, setLoading] = useState(true);
  const [verifying, setVerifying] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const fetchVerificationStatus = async () => {
    try {
      setLoading(true);
      setErrorMsg(null);
      const res = await apiFetch('/api/ngos/government-verification');
      setData(res);
    } catch (err: any) {
      setErrorMsg(err.message || 'Failed to retrieve government verification data.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchVerificationStatus();
  }, []);

  const handleRunVerification = async () => {
    try {
      setVerifying(true);
      setErrorMsg(null);
      const res = await apiFetch('/api/ngos/government-verification', { method: 'POST' });
      setData(res);
    } catch (err: any) {
      setErrorMsg(err.message || 'Government verification check failed.');
    } finally {
      setVerifying(false);
    }
  };

  if (loading) {
    return (
      <div className="py-12 text-center text-slate-500 bg-white rounded-3xl border border-slate-200">
        <div className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-blue-600 border-t-transparent mb-3"></div>
        <p className="text-xs font-semibold">Checking Demo Government Registry status...</p>
      </div>
    );
  }

  const matches = data?.field_matches;
  const status = data?.verification_status || 'NOT_VERIFIED';

  return (
    <div className="space-y-6">
      
      {/* SIMULATED DEMO GOVERNMENT REGISTRY MANDATORY DISCLAIMER BANNER */}
      <div className="rounded-2xl border-2 border-amber-300 bg-gradient-to-r from-amber-50 to-orange-50 p-5 shadow-sm space-y-2">
        <div className="flex items-start space-x-3">
          <AlertTriangle className="h-6 w-6 text-amber-600 flex-shrink-0 mt-0.5" />
          <div className="space-y-1">
            <h3 className="text-sm font-extrabold tracking-wide uppercase text-amber-900">
              SIMULATED DEMO GOVERNMENT REGISTRY FOR ACADEMIC / PROJECT DEMONSTRATION ONLY
            </h3>
            <p className="text-xs text-amber-800 leading-relaxed">
              This automated verification checks your organization credentials against a simulated, pre-seeded government registry database (FCRA, 80G, and MCA NGO Darpan records). It provides illustrative regulatory compliance verification for project evaluation purposes and does not represent an actual connection to official government servers.
            </p>
          </div>
        </div>
      </div>

      {errorMsg && (
        <div className="rounded-xl border border-rose-200 bg-rose-50 p-4 text-xs text-rose-800 flex items-center justify-between">
          <span>{errorMsg}</span>
          <button onClick={fetchVerificationStatus} className="text-xs font-bold underline cursor-pointer">Retry</button>
        </div>
      )}

      {/* Main Verification Status Card */}
      <div className="bg-white rounded-3xl border border-slate-200 p-6 md:p-8 shadow-card space-y-6">
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 border-b border-slate-100 pb-6">
          <div className="space-y-1">
            <div className="flex items-center space-x-2">
              <Landmark className="h-5 w-5 text-blue-600" />
              <h2 className="text-xl font-bold text-slate-900">Government Registry Verification Dossier</h2>
            </div>
            <p className="text-xs text-slate-500">Automated cross-matching against simulated central government registration records.</p>
          </div>

          <div className="flex items-center space-x-3">
            <span className={`px-4 py-1.5 rounded-full text-xs font-extrabold uppercase border ${
              status === 'VERIFIED' ? 'bg-emerald-50 text-emerald-700 border-emerald-300' :
              status === 'PARTIAL_MATCH' ? 'bg-amber-50 text-amber-700 border-amber-300' :
              status === 'FAILED' ? 'bg-rose-50 text-rose-700 border-rose-300' :
              'bg-slate-100 text-slate-700 border-slate-300'
            }`}>
              {status === 'VERIFIED' ? '✓ FULLY REGISTRY VERIFIED' :
               status === 'PARTIAL_MATCH' ? '⚠ PARTIAL REGISTRY MATCH' :
               status === 'FAILED' ? '✕ REGISTRY MATCH FAILED' : 'NOT VERIFIED'}
            </span>

            <button
              onClick={handleRunVerification}
              disabled={verifying}
              className="inline-flex items-center space-x-1.5 rounded-xl bg-blue-600 px-4 py-2 text-xs font-bold text-white hover:bg-blue-700 disabled:opacity-50 transition-all cursor-pointer shadow-xs shadow-blue-600/20"
            >
              <RefreshCw className={`h-3.5 w-3.5 ${verifying ? 'animate-spin' : ''}`} />
              <span>{verifying ? 'Verifying...' : 'Re-Run Verification'}</span>
            </button>
          </div>
        </div>

        {/* Verification Message */}
        {data?.details && (
          <div className="bg-slate-50 p-4 rounded-xl border border-slate-200 text-xs text-slate-700 leading-relaxed font-mono">
            <span className="font-bold text-slate-900 font-sans block mb-1">Audit Details:</span>
            {data.details}
          </div>
        )}

        {/* Field Matches Grid */}
        <div className="space-y-3">
          <h3 className="text-xs font-bold text-slate-700 uppercase tracking-wider">Field-by-Field Government Record Matching</h3>
          
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            
            <div className="bg-slate-50 p-4 rounded-2xl border border-slate-200/80 flex items-center justify-between">
              <div>
                <p className="text-xs font-bold text-slate-900">Registration Number</p>
                <p className="text-[10px] text-slate-500">Government Registry ID</p>
              </div>
              {matches?.registration_number_matched ? (
                <span className="inline-flex items-center text-xs font-bold text-emerald-600 bg-emerald-50 px-2.5 py-1 rounded-full border border-emerald-200">
                  <CheckCircle2 className="h-3.5 w-3.5 mr-1" /> Matched
                </span>
              ) : (
                <span className="inline-flex items-center text-xs font-bold text-rose-600 bg-rose-50 px-2.5 py-1 rounded-full border border-rose-200">
                  <XCircle className="h-3.5 w-3.5 mr-1" /> Mismatch
                </span>
              )}
            </div>

            <div className="bg-slate-50 p-4 rounded-2xl border border-slate-200/80 flex items-center justify-between">
              <div>
                <p className="text-xs font-bold text-slate-900">Organization Name</p>
                <p className="text-[10px] text-slate-500">Official Title Match</p>
              </div>
              {matches?.org_name_matched ? (
                <span className="inline-flex items-center text-xs font-bold text-emerald-600 bg-emerald-50 px-2.5 py-1 rounded-full border border-emerald-200">
                  <CheckCircle2 className="h-3.5 w-3.5 mr-1" /> Matched
                </span>
              ) : (
                <span className="inline-flex items-center text-xs font-bold text-rose-600 bg-rose-50 px-2.5 py-1 rounded-full border border-rose-200">
                  <XCircle className="h-3.5 w-3.5 mr-1" /> Mismatch
                </span>
              )}
            </div>

            <div className="bg-slate-50 p-4 rounded-2xl border border-slate-200/80 flex items-center justify-between">
              <div>
                <p className="text-xs font-bold text-slate-900">Tax ID / PAN Exemption</p>
                <p className="text-[10px] text-slate-500">Tax Exemption Record</p>
              </div>
              {matches?.tax_id_matched ? (
                <span className="inline-flex items-center text-xs font-bold text-emerald-600 bg-emerald-50 px-2.5 py-1 rounded-full border border-emerald-200">
                  <CheckCircle2 className="h-3.5 w-3.5 mr-1" /> Matched
                </span>
              ) : (
                <span className="inline-flex items-center text-xs font-bold text-rose-600 bg-rose-50 px-2.5 py-1 rounded-full border border-rose-200">
                  <XCircle className="h-3.5 w-3.5 mr-1" /> Mismatch
                </span>
              )}
            </div>

            <div className="bg-slate-50 p-4 rounded-2xl border border-slate-200/80 flex items-center justify-between">
              <div>
                <p className="text-xs font-bold text-slate-900">Section 80G Tax Exemption</p>
                <p className="text-[10px] text-slate-500">Donor Tax Rebate Status</p>
              </div>
              {matches?.section_80g_registered ? (
                <span className="inline-flex items-center text-xs font-bold text-emerald-600 bg-emerald-50 px-2.5 py-1 rounded-full border border-emerald-200">
                  <CheckCircle2 className="h-3.5 w-3.5 mr-1" /> Active
                </span>
              ) : (
                <span className="inline-flex items-center text-xs font-bold text-amber-600 bg-amber-50 px-2.5 py-1 rounded-full border border-amber-200">
                  <AlertTriangle className="h-3.5 w-3.5 mr-1" /> Pending
                </span>
              )}
            </div>

            <div className="bg-slate-50 p-4 rounded-2xl border border-slate-200/80 flex items-center justify-between">
              <div>
                <p className="text-xs font-bold text-slate-900">FCRA Registration</p>
                <p className="text-[10px] text-slate-500">Foreign Contribution Clearance</p>
              </div>
              {matches?.fcra_registered ? (
                <span className="inline-flex items-center text-xs font-bold text-emerald-600 bg-emerald-50 px-2.5 py-1 rounded-full border border-emerald-200">
                  <CheckCircle2 className="h-3.5 w-3.5 mr-1" /> Cleared
                </span>
              ) : (
                <span className="inline-flex items-center text-xs font-bold text-slate-600 bg-slate-100 px-2.5 py-1 rounded-full border border-slate-200">
                  Not Cleared
                </span>
              )}
            </div>

          </div>
        </div>

        {/* Matched Registry Record */}
        {data?.matched_registry_record && (
          <div className="bg-blue-50/50 p-5 rounded-2xl border border-blue-200 space-y-3">
            <h3 className="text-xs font-bold text-blue-900 flex items-center gap-1.5">
              <FileCheck className="h-4 w-4 text-blue-600" />
              Simulated Government Registry Entry Found
            </h3>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 text-xs">
              <div>
                <span className="text-[10px] text-slate-500 block font-mono">REGISTRY ID</span>
                <span className="font-bold text-slate-900 font-mono">{data.matched_registry_record.registry_id}</span>
              </div>
              <div>
                <span className="text-[10px] text-slate-500 block">RECORDED TITLE</span>
                <span className="font-bold text-slate-900">{data.matched_registry_record.official_name}</span>
              </div>
              <div>
                <span className="text-[10px] text-slate-500 block">JURISDICTION</span>
                <span className="font-bold text-slate-900">{data.matched_registry_record.state}</span>
              </div>
              <div>
                <span className="text-[10px] text-slate-500 block">VALID UNTIL</span>
                <span className="font-bold text-emerald-700">{data.matched_registry_record.valid_until}</span>
              </div>
            </div>
          </div>
        )}

      </div>
    </div>
  );
}
