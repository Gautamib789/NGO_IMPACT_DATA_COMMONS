'use client';

import React from 'react';
import { Building2, CheckCircle2, FileText, FolderPlus, Users, DollarSign, TrendingUp, ShieldCheck, Landmark, AlertTriangle, ArrowRight } from 'lucide-react';
import { NGOProfile, GovernmentVerification, Project } from './types';

interface OverviewTabProps {
  profile: NGOProfile | null;
  govVerification: GovernmentVerification | null;
  projects: Project[];
  onNavigateTab: (tab: string) => void;
}

export default function OverviewTab({ profile, govVerification, projects, onNavigateTab }: OverviewTabProps) {
  const totalBudget = projects.reduce((acc, p) => acc + (p.budget ?? p.total_budget ?? 0), 0);
  const totalClaimed = projects.reduce((acc, p) => acc + (p.total_expenses_claimed ?? p.amount_spent ?? 0), 0);
  const totalBeneficiaries = profile?.beneficiary_count || 0;
  const govStatus = govVerification?.verification_status || 'NOT_VERIFIED';

  return (
    <div className="space-y-6">
      
      {/* Top Banner Card */}
      <div className="rounded-3xl border border-slate-200 bg-gradient-to-r from-blue-900 via-slate-900 to-indigo-950 p-8 text-white shadow-xl relative overflow-hidden">
        <div className="relative z-10 flex flex-col md:flex-row md:items-center md:justify-between gap-6">
          <div className="space-y-2">
            <div className="flex items-center space-x-2">
              <span className="inline-flex items-center gap-1 rounded-full bg-emerald-500/20 px-3 py-1 text-xs font-bold text-emerald-300 border border-emerald-500/30">
                <CheckCircle2 className="h-3.5 w-3.5" />
                NGO PORTAL DASHBOARD
              </span>
              <span className="text-xs text-slate-300 font-mono">Reg #: {profile?.registration_number || 'N/A'}</span>
            </div>

            <h1 className="text-3xl font-extrabold tracking-tight sm:text-4xl text-white">{profile?.org_name || 'Organization Account'}</h1>
            <p className="text-xs text-slate-300 flex flex-wrap items-center gap-3">
              <span className="font-semibold">{profile?.category || 'General NGO'}</span>
              <span>•</span>
              <span>Tax ID: {profile?.tax_id || 'N/A'}</span>
              <span>•</span>
              <span>Status: <strong className="text-emerald-400">{profile?.status}</strong></span>
            </p>
          </div>

          <div className="flex items-center space-x-4">
            <div className="bg-white/10 backdrop-blur-md p-4 rounded-2xl border border-white/10 text-center min-w-[120px]">
              <span className="block text-[10px] text-slate-300 uppercase font-bold tracking-wider">Transparency Score</span>
              <span className="text-3xl font-extrabold text-emerald-400">{profile?.transparency_score || 0}%</span>
            </div>

            <div className="bg-white/10 backdrop-blur-md p-4 rounded-2xl border border-white/10 text-center min-w-[120px]">
              <span className="block text-[10px] text-slate-300 uppercase font-bold tracking-wider">Doc Completeness</span>
              <span className="text-3xl font-extrabold text-blue-400">{profile?.doc_completeness_score || 0}%</span>
            </div>
          </div>
        </div>
      </div>

      {/* Metrics Row */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        
        <div className="bg-white p-6 rounded-3xl border border-slate-200 shadow-card space-y-2">
          <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Active Field Projects</span>
          <div className="flex items-baseline justify-between">
            <span className="text-3xl font-extrabold text-slate-900">{projects.length}</span>
            <FolderPlus className="h-6 w-6 text-blue-600" />
          </div>
          <button onClick={() => onNavigateTab('projects')} className="text-xs text-blue-600 hover:underline font-bold flex items-center gap-1 cursor-pointer">
            Manage Projects <ArrowRight className="h-3 w-3" />
          </button>
        </div>

        <div className="bg-white p-6 rounded-3xl border border-slate-200 shadow-card space-y-2">
          <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Total Beneficiaries Reached</span>
          <div className="flex items-baseline justify-between">
            <span className="text-3xl font-extrabold text-slate-900">{totalBeneficiaries.toLocaleString()}</span>
            <Users className="h-6 w-6 text-emerald-600" />
          </div>
          <button onClick={() => onNavigateTab('beneficiaries')} className="text-xs text-blue-600 hover:underline font-bold flex items-center gap-1 cursor-pointer">
            View Beneficiaries <ArrowRight className="h-3 w-3" />
          </button>
        </div>

        <div className="bg-white p-6 rounded-3xl border border-slate-200 shadow-card space-y-2">
          <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Claimed Field Expenses</span>
          <div className="flex items-baseline justify-between">
            <span className="text-3xl font-extrabold text-blue-700">₹{totalClaimed.toLocaleString('en-IN')}</span>
            <DollarSign className="h-6 w-6 text-blue-600" />
          </div>
          <button onClick={() => onNavigateTab('expenses')} className="text-xs text-blue-600 hover:underline font-bold flex items-center gap-1 cursor-pointer">
            Expense Claims <ArrowRight className="h-3 w-3" />
          </button>
        </div>

        <div className="bg-white p-6 rounded-3xl border border-slate-200 shadow-card space-y-2">
          <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Government Registry Status</span>
          <div className="flex items-baseline justify-between">
            <span className={`text-base font-extrabold uppercase ${
              govStatus === 'VERIFIED' ? 'text-emerald-600' : 'text-amber-600'
            }`}>
              {govStatus}
            </span>
            <Landmark className="h-6 w-6 text-amber-600" />
          </div>
          <button onClick={() => onNavigateTab('government')} className="text-xs text-blue-600 hover:underline font-bold flex items-center gap-1 cursor-pointer">
            Verify Status <ArrowRight className="h-3 w-3" />
          </button>
        </div>

      </div>

      {/* Quick Action Shortcuts */}
      <div className="bg-white rounded-3xl border border-slate-200 p-6 md:p-8 shadow-card space-y-4">
        <h3 className="text-base font-bold text-slate-900">Quick Dashboard Actions</h3>
        
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <button
            onClick={() => onNavigateTab('projects')}
            className="p-5 rounded-2xl bg-slate-50 hover:bg-blue-50 border border-slate-200 hover:border-blue-300 text-left space-y-2 transition-all group cursor-pointer"
          >
            <FolderPlus className="h-6 w-6 text-blue-600 group-hover:scale-110 transition-transform" />
            <h4 className="font-bold text-slate-900 text-sm">Add New Field Project</h4>
            <p className="text-xs text-slate-500">Define budget, location, GPS, and beneficiary targets.</p>
          </button>

          <button
            onClick={() => onNavigateTab('documents')}
            className="p-5 rounded-2xl bg-slate-50 hover:bg-blue-50 border border-slate-200 hover:border-blue-300 text-left space-y-2 transition-all group cursor-pointer"
          >
            <FileText className="h-6 w-6 text-blue-600 group-hover:scale-110 transition-transform" />
            <h4 className="font-bold text-slate-900 text-sm">Upload Compliance Document</h4>
            <p className="text-xs text-slate-500">Compute SHA-256 cryptographic hash and tamper score.</p>
          </button>

          <button
            onClick={() => onNavigateTab('beneficiaries')}
            className="p-5 rounded-2xl bg-slate-50 hover:bg-blue-50 border border-slate-200 hover:border-blue-300 text-left space-y-2 transition-all group cursor-pointer"
          >
            <Users className="h-6 w-6 text-blue-600 group-hover:scale-110 transition-transform" />
            <h4 className="font-bold text-slate-900 text-sm">Register Masked Beneficiary</h4>
            <p className="text-xs text-slate-500">Assign privacy-safe code to community beneficiaries.</p>
          </button>
        </div>
      </div>

    </div>
  );
}
