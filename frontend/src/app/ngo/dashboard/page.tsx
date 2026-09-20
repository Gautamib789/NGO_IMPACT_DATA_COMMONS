'use client';

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/context/AuthContext';
import {
  LayoutDashboard,
  Building2,
  Landmark,
  FileText,
  FolderPlus,
  Users,
  DollarSign,
  PieChart,
  Award,
  LogOut,
  RefreshCw,
  AlertCircle
} from 'lucide-react';

import { NGOProfile, GovernmentVerification, Project } from '@/components/ngo/types';
import OverviewTab from '@/components/ngo/OverviewTab';
import NGOProfileTab from '@/components/ngo/NGOProfileTab';
import GovernmentVerificationTab from '@/components/ngo/GovernmentVerificationTab';
import DocumentsTab from '@/components/ngo/DocumentsTab';
import ProjectsTab from '@/components/ngo/ProjectsTab';
import BeneficiariesTab from '@/components/ngo/BeneficiariesTab';
import ExpensesTab from '@/components/ngo/ExpensesTab';
import FundUtilizationTab from '@/components/ngo/FundUtilizationTab';
import VerificationStatusTab from '@/components/ngo/VerificationStatusTab';

type TabType =
  | 'overview'
  | 'profile'
  | 'government'
  | 'documents'
  | 'projects'
  | 'beneficiaries'
  | 'expenses'
  | 'fund-utilization'
  | 'verification-status';

export default function NGODashboardPage() {
  const router = useRouter();
  const { user, token, isLoading, logout, apiFetch } = useAuth();

  const [activeTab, setActiveTab] = useState<TabType>('overview');
  const [profile, setProfile] = useState<NGOProfile | null>(null);
  const [govVerification, setGovVerification] = useState<GovernmentVerification | null>(null);
  const [projects, setProjects] = useState<Project[]>([]);
  const [loadingData, setLoadingData] = useState(true);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  // Authentication check
  useEffect(() => {
    if (!isLoading && (!token || !user || user.role !== 'NGO')) {
      router.push('/login');
    }
  }, [user, token, isLoading, router]);

  const loadAllData = async (showLoadingSpinner = true) => {
    if (!token || user?.role !== 'NGO') return;
    try {
      if (showLoadingSpinner) {
        setLoadingData(true);
      }
      setErrorMsg(null);

      const [profData, govData, projData] = await Promise.allSettled([
        apiFetch('/api/ngos/profile'),
        apiFetch('/api/ngos/government-verification'),
        apiFetch('/api/ngo/projects'),
      ]);

      if (profData.status === 'fulfilled') {
        setProfile(profData.value);
      } else {
        console.error('Failed to load NGO profile', profData.reason);
      }

      if (govData.status === 'fulfilled') {
        setGovVerification(govData.value);
      }

      if (projData.status === 'fulfilled') {
        setProjects(projData.value);
      }
    } finally {
      setLoadingData(false);
    }
  };

  useEffect(() => {
    if (token && user?.role === 'NGO') {
      loadAllData();
    }
  }, [token, user]);

  if (isLoading || loadingData) {
    return (
      <div className="min-h-screen bg-slate-50 flex items-center justify-center p-4">
        <div className="text-center space-y-3">
          <div className="inline-block h-10 w-10 animate-spin rounded-full border-4 border-blue-600 border-t-transparent"></div>
          <p className="text-sm font-bold text-slate-700">Loading NGO Portal Dashboard...</p>
          <p className="text-xs text-slate-400">Fetching live API compliance records</p>
        </div>
      </div>
    );
  }

  if (!user || user.role !== 'NGO') {
    return null;
  }

  const tabs = [
    { id: 'overview', label: 'Overview', icon: LayoutDashboard },
    { id: 'profile', label: 'NGO Profile', icon: Building2 },
    { id: 'government', label: 'Government Verification', icon: Landmark },
    { id: 'documents', label: 'Documents', icon: FileText, badge: profile?.documents?.length },
    { id: 'projects', label: 'Projects', icon: FolderPlus, badge: projects.length },
    { id: 'beneficiaries', label: 'Beneficiaries', icon: Users },
    { id: 'expenses', label: 'Expenses', icon: DollarSign },
    { id: 'fund-utilization', label: 'Fund Utilization', icon: PieChart },
    { id: 'verification-status', label: 'Verification Status', icon: Award },
  ];

  return (
    <div className="min-h-screen bg-slate-50/70 pb-20">

      {/* Top NGO Header */}
      <header className="sticky top-0 z-30 bg-white/90 backdrop-blur-md border-b border-slate-200/80 shadow-xs">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 py-3.5 flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="h-9 w-9 rounded-xl bg-blue-600 flex items-center justify-center text-white font-black text-base shadow-xs">
              N
            </div>
            <div>
              <h1 className="text-sm font-bold text-slate-900 leading-none">{profile?.org_name || 'NGO Dashboard'}</h1>
              <p className="text-[10px] text-slate-500 font-mono mt-0.5">{user.email} • NGO Portal</p>
            </div>
          </div>

          <div className="flex items-center space-x-3">
            <button
              onClick={() => loadAllData()}
              className="p-2 rounded-xl text-slate-500 hover:text-blue-600 hover:bg-slate-100 transition-colors cursor-pointer"
              title="Refresh Dashboard Data"
            >
              <RefreshCw className="h-4 w-4" />
            </button>
            <button
              onClick={logout}
              className="inline-flex items-center space-x-1.5 rounded-xl border border-slate-200 bg-slate-50 px-3 py-1.5 text-xs font-semibold text-slate-700 hover:bg-slate-100 transition-colors cursor-pointer"
            >
              <LogOut className="h-3.5 w-3.5" />
              <span>Logout</span>
            </button>
          </div>
        </div>
      </header>

      {/* Main Content Area with Navigation Tabs */}
      <main className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 py-6 space-y-6">

        {errorMsg && (
          <div className="rounded-xl border border-rose-200 bg-rose-50 p-4 text-xs text-rose-800 flex items-center justify-between shadow-xs">
            <div className="flex items-center space-x-2">
              <AlertCircle className="h-4 w-4 text-rose-600 flex-shrink-0" />
              <span>{errorMsg}</span>
            </div>
            <button onClick={() => loadAllData()} className="text-xs font-bold underline cursor-pointer">Retry Loading</button>
          </div>
        )}

        {/* Tab Navigation Menu */}
        <div className="bg-white rounded-2xl border border-slate-200/80 p-1.5 shadow-xs overflow-x-auto">
          <nav className="flex space-x-1 min-w-max">
            {tabs.map((tab) => {
              const Icon = tab.icon;
              const isActive = activeTab === tab.id;
              return (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id as TabType)}
                  className={`flex items-center space-x-2 rounded-xl px-4 py-2.5 text-xs font-bold transition-all cursor-pointer ${isActive
                      ? 'bg-blue-600 text-white shadow-xs'
                      : 'text-slate-600 hover:text-slate-900 hover:bg-slate-100'
                    }`}
                >
                  <Icon className={`h-4 w-4 ${isActive ? 'text-white' : 'text-slate-400'}`} />
                  <span>{tab.label}</span>
                  {tab.badge !== undefined && (
                    <span className={`px-1.5 py-0.5 rounded-full text-[10px] ${isActive ? 'bg-white/20 text-white' : 'bg-slate-100 text-slate-700'
                      }`}>
                      {tab.badge}
                    </span>
                  )}
                </button>
              );
            })}
          </nav>
        </div>

        {/* Tab Content Display */}
        <div className="pt-2">
          {activeTab === 'overview' && (
            <OverviewTab
              profile={profile}
              govVerification={govVerification}
              projects={projects}
              onNavigateTab={(tabKey) => setActiveTab(tabKey as TabType)}
            />
          )}

          {activeTab === 'profile' && (
            <NGOProfileTab
              profile={profile}
              onRefresh={() => loadAllData(false)}
            />
          )}

          {activeTab === 'government' && (
            <GovernmentVerificationTab />
          )}

          {activeTab === 'documents' && (
            <DocumentsTab
              documents={profile?.documents || []}
              onRefresh={loadAllData}
            />
          )}

          {activeTab === 'projects' && (
            <ProjectsTab
              onRefresh={loadAllData}
            />
          )}

          {activeTab === 'beneficiaries' && (
            <BeneficiariesTab
              projects={projects}
              onRefresh={loadAllData}
            />
          )}

          {activeTab === 'expenses' && (
            <ExpensesTab
              projects={projects}
              onRefresh={loadAllData}
            />
          )}

          {activeTab === 'fund-utilization' && (
            <FundUtilizationTab
              profile={profile}
              projects={projects}
            />
          )}

          {activeTab === 'verification-status' && (
            <VerificationStatusTab
              profile={profile}
              govVerification={govVerification}
            />
          )}
        </div>

      </main>
    </div>
  );
}
