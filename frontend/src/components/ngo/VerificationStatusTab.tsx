'use client';

import React from 'react';
import { ShieldCheck, FileCheck, CheckCircle2, AlertTriangle, XCircle, Landmark, Award } from 'lucide-react';
import { NGOProfile, GovernmentVerification } from './types';

interface VerificationStatusTabProps {
  profile: NGOProfile | null;
  govVerification: GovernmentVerification | null;
}

export default function VerificationStatusTab({ profile, govVerification }: VerificationStatusTabProps) {
  const govStatus = govVerification?.verification_status || 'NOT_VERIFIED';
  const adminStatus = profile?.status || 'PENDING';
  const docScore = profile?.doc_completeness_score || 0;
  const transScore = profile?.transparency_score || 0;

  return (
    <div className="space-y-6">
      
      {/* Overview Status Banner */}
      <div className="bg-white rounded-3xl border border-slate-200 p-6 md:p-8 shadow-card space-y-6">
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-6 border-b border-slate-100 pb-6">
          <div className="space-y-2">
            <div className="flex items-center space-x-2">
              <Award className="h-6 w-6 text-blue-600" />
              <h2 className="text-xl font-bold text-slate-900">NGO Verification & Compliance Matrix</h2>
            </div>
            <p className="text-xs text-slate-500">Comprehensive compliance rating computed from automated government registry cross-checks, document completeness, and AI fraud audits.</p>
          </div>

          <div className="flex items-center space-x-4">
            <div className="bg-slate-50 p-4 rounded-2xl border border-slate-200 text-center min-w-[140px]">
              <span className="block text-[10px] text-slate-400 uppercase font-bold tracking-wider">Overall Status</span>
              <span className={`text-sm font-extrabold uppercase mt-1 block ${
                adminStatus === 'APPROVED' ? 'text-emerald-600' :
                adminStatus === 'PENDING' ? 'text-amber-600' : 'text-rose-600'
              }`}>
                {adminStatus}
              </span>
            </div>

            <div className="bg-slate-50 p-4 rounded-2xl border border-slate-200 text-center min-w-[140px]">
              <span className="block text-[10px] text-slate-400 uppercase font-bold tracking-wider">Transparency Score</span>
              <span className="text-2xl font-extrabold text-emerald-600">{transScore}%</span>
            </div>
          </div>
        </div>

        {/* 4 Pillars of Verification */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          
          {/* Pillar 1: Government Registry */}
          <div className="bg-slate-50 p-6 rounded-2xl border border-slate-200 space-y-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <Landmark className="h-5 w-5 text-blue-600" />
                <h3 className="font-bold text-slate-900 text-sm">1. Government Registry Audit</h3>
              </div>
              <span className={`px-2.5 py-0.5 rounded-full text-[10px] font-bold uppercase border ${
                govStatus === 'VERIFIED' ? 'bg-emerald-50 text-emerald-700 border-emerald-300' :
                govStatus === 'PARTIAL_MATCH' ? 'bg-amber-50 text-amber-700 border-amber-300' :
                'bg-rose-50 text-rose-700 border-rose-300'
              }`}>
                {govStatus}
              </span>
            </div>
            <p className="text-xs text-slate-600 leading-relaxed">
              Automated cross-matching against simulated FCRA, Section 80G tax exemption, and registration records.
            </p>
          </div>

          {/* Pillar 2: Document Completeness */}
          <div className="bg-slate-50 p-6 rounded-2xl border border-slate-200 space-y-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <FileCheck className="h-5 w-5 text-blue-600" />
                <h3 className="font-bold text-slate-900 text-sm">2. Document Audit Completeness</h3>
              </div>
              <span className="text-sm font-extrabold text-slate-900 font-mono">{docScore}%</span>
            </div>
            <p className="text-xs text-slate-600 leading-relaxed">
              Measures percentage of required compliance documents (80G, PAN, Audit Reports, Bylaws) uploaded with valid SHA-256 hashes.
            </p>
            <div className="w-full bg-slate-200 rounded-full h-2 overflow-hidden">
              <div className="bg-blue-600 h-2 rounded-full" style={{ width: `${docScore}%` }}></div>
            </div>
          </div>

          {/* Pillar 3: Admin Review */}
          <div className="bg-slate-50 p-6 rounded-2xl border border-slate-200 space-y-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <ShieldCheck className="h-5 w-5 text-blue-600" />
                <h3 className="font-bold text-slate-900 text-sm">3. Platform Admin Inspection</h3>
              </div>
              <span className={`px-2.5 py-0.5 rounded-full text-[10px] font-bold uppercase border ${
                adminStatus === 'APPROVED' ? 'bg-emerald-50 text-emerald-700 border-emerald-300' :
                adminStatus === 'PENDING' ? 'bg-amber-50 text-amber-700 border-amber-300' :
                'bg-rose-50 text-rose-700 border-rose-300'
              }`}>
                {adminStatus}
              </span>
            </div>
            <p className="text-xs text-slate-600 leading-relaxed">
              Manual inspection and decision by chief platform auditors following automated tamper-risk checks.
            </p>
          </div>

          {/* Pillar 4: Transparency Rating */}
          <div className="bg-slate-50 p-6 rounded-2xl border border-slate-200 space-y-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-2">
                <CheckCircle2 className="h-5 w-5 text-emerald-600" />
                <h3 className="font-bold text-slate-900 text-sm">4. AI Fraud Engine Rating</h3>
              </div>
              <span className="text-sm font-extrabold text-emerald-600 font-mono">{transScore}%</span>
            </div>
            <p className="text-xs text-slate-600 leading-relaxed">
              Dynamic score evaluating financial ratios, expense claims, beneficiary reporting consistency, and document hash integrity.
            </p>
          </div>

        </div>
      </div>

    </div>
  );
}
