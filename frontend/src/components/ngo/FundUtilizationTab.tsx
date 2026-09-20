'use client';

import React from 'react';
import { PieChart, TrendingUp, DollarSign, CheckCircle2, AlertTriangle, Layers } from 'lucide-react';
import { Project, NGOProfile } from './types';

interface FundUtilizationTabProps {
  profile: NGOProfile | null;
  projects: Project[];
}

export default function FundUtilizationTab({ profile, projects }: FundUtilizationTabProps) {
  const totalBudget = projects.reduce((acc, p) => acc + (p.budget ?? p.total_budget ?? 0), 0);
  const totalClaimed = projects.reduce((acc, p) => acc + (p.total_expenses_claimed ?? p.amount_spent ?? 0), 0);
  const overallUtilization = totalBudget > 0 ? round((totalClaimed / totalBudget) * 100, 2) : 0;

  function round(val: number, decimals: number) {
    return Number(Math.round(Number(val + 'e' + decimals)) + 'e-' + decimals);
  }

  return (
    <div className="space-y-6">
      
      {/* Top Fund Overview Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        
        <div className="bg-white p-6 rounded-3xl border border-slate-200 shadow-card space-y-2">
          <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Total Approved Budget</span>
          <div className="flex items-baseline justify-between">
            <span className="text-2xl font-extrabold text-slate-900">₹{totalBudget.toLocaleString('en-IN')}</span>
            <DollarSign className="h-5 w-5 text-blue-600" />
          </div>
          <p className="text-[11px] text-slate-500">Across {projects.length} field projects</p>
        </div>

        <div className="bg-white p-6 rounded-3xl border border-slate-200 shadow-card space-y-2">
          <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Claimed Field Expenses</span>
          <div className="flex items-baseline justify-between">
            <span className="text-2xl font-extrabold text-blue-700">₹{totalClaimed.toLocaleString('en-IN')}</span>
            <TrendingUp className="h-5 w-5 text-emerald-600" />
          </div>
          <p className="text-[11px] text-slate-500">Verified receipt hashes logged</p>
        </div>

        <div className="bg-white p-6 rounded-3xl border border-slate-200 shadow-card space-y-2">
          <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Overall Fund Utilization</span>
          <div className="flex items-baseline justify-between">
            <span className="text-2xl font-extrabold text-emerald-600">{overallUtilization}%</span>
            <PieChart className="h-5 w-5 text-emerald-600" />
          </div>
          <p className="text-[11px] text-slate-500">Capital deployment ratio</p>
        </div>

        <div className="bg-white p-6 rounded-3xl border border-slate-200 shadow-card space-y-2">
          <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400">Public Transparency Score</span>
          <div className="flex items-baseline justify-between">
            <span className="text-2xl font-extrabold text-slate-900">{profile?.transparency_score || 0}%</span>
            <CheckCircle2 className="h-5 w-5 text-emerald-600" />
          </div>
          <p className="text-[11px] text-slate-500">AI Fraud Engine composite rating</p>
        </div>

      </div>

      {/* Project-by-Project Fund Allocation Table */}
      <div className="bg-white rounded-3xl border border-slate-200 p-6 md:p-8 shadow-card space-y-6">
        <div className="border-b border-slate-100 pb-4">
          <h3 className="text-base font-bold text-slate-900 flex items-center gap-2">
            <Layers className="h-5 w-5 text-blue-600" />
            Project Fund Utilization Breakdown
          </h3>
          <p className="text-xs text-slate-500">Compare allocated capital vs claimed field expenses for every project.</p>
        </div>

        {projects.length === 0 ? (
          <div className="py-12 text-center text-slate-400">
            <p className="text-xs font-semibold">No project fund utilization data available.</p>
          </div>
        ) : (
          <div className="space-y-6">
            {projects.map((p) => (
              <div key={p.id} className="bg-slate-50 p-5 rounded-2xl border border-slate-200 space-y-3">
                <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
                  <div>
                    <span className="text-[10px] font-bold uppercase text-blue-600 bg-blue-50 px-2 py-0.5 rounded-md border border-blue-200">
                      {p.category}
                    </span>
                    <h4 className="font-bold text-slate-900 text-sm mt-1">{p.project_name}</h4>
                  </div>

                  <div className="text-right sm:text-right font-mono text-xs">
                    <span className="text-slate-500 font-sans block text-[10px]">UTILIZATION RATIO</span>
                    <span className="font-extrabold text-emerald-700 text-base">{p.fund_utilization_ratio}%</span>
                  </div>
                </div>

                {/* Progress bar */}
                <div className="w-full bg-slate-200 rounded-full h-3 overflow-hidden">
                  <div
                    className="bg-emerald-500 h-3 rounded-full transition-all duration-500"
                    style={{ width: `${Math.min(100, p.fund_utilization_ratio ?? 0)}%` }}
                  ></div>
                </div>

                <div className="flex justify-between items-center text-xs font-mono pt-1 text-slate-600">
                  <span>Expenses Claimed: <strong className="text-slate-900 font-bold">₹{(p.total_expenses_claimed ?? p.amount_spent ?? 0).toLocaleString('en-IN')}</strong></span>
                  <span>Approved Budget: <strong className="text-slate-900 font-bold">₹{(p.budget ?? p.total_budget ?? 0).toLocaleString('en-IN')}</strong></span>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

    </div>
  );
}
