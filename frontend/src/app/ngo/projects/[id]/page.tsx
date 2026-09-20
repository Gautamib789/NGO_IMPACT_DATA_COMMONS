'use client';

import React, { useState, useEffect } from 'react';
import { useParams, useRouter } from 'next/navigation';
import { useAuth } from '@/context/AuthContext';
import {
  ArrowLeft,
  FolderPlus,
  MapPin,
  Calendar,
  Users,
  DollarSign,
  PieChart,
  ShieldCheck,
  ShieldAlert,
  ShieldX,
  FileText,
  Upload,
  Image as ImageIcon,
  PlusCircle,
  Eye,
  AlertTriangle,
  CheckCircle2,
  XCircle,
  RefreshCw,
  Clock,
  Layers,
  FileCheck
} from 'lucide-react';
import {
  ProjectDetailData,
  ProjectEvidence,
  ProjectExpense,
  ProjectFinding,
  ProjectIntegrityAnalysisData,
  mapProjectResponse
} from '@/components/ngo/types';
import { getApiErrorMessage } from '@/utils/errorUtils';

export default function ProjectDetailsPage() {
  const params = useParams();
  const router = useRouter();
  const projectId = params?.id ? String(params.id) : '';

  const { token, user, isLoading: authLoading, apiFetch } = useAuth();

  const [data, setData] = useState<ProjectDetailData | null>(null);
  const [integrityAnalysis, setIntegrityAnalysis] = useState<ProjectIntegrityAnalysisData | null>(null);
  const [loading, setLoading] = useState(true);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  // Evidence Filter
  const [evidenceCategory, setEvidenceCategory] = useState<string>('ALL');

  // Lightbox State
  const [previewImage, setPreviewImage] = useState<{ url: string; title: string; meta: any } | null>(null);

  // Modals
  const [showUploadModal, setShowUploadModal] = useState(false);
  const [uploadFile, setUploadFile] = useState<File | null>(null);
  const [uploadCategory, setUploadCategory] = useState<string>('BEFORE_PHOTO');
  const [isUploading, setIsUploading] = useState(false);

  const [showExpenseModal, setShowExpenseModal] = useState(false);
  const [expenseInvoice, setExpenseInvoice] = useState('');
  const [expenseVendor, setExpenseVendor] = useState('');
  const [expenseAmount, setExpenseAmount] = useState<number>(1000);
  const [expenseDate, setExpenseDate] = useState<string>(new Date().toISOString().split('T')[0]);
  const [expenseDesc, setExpenseDesc] = useState('');
  const [expenseEvidenceId, setExpenseEvidenceId] = useState<number | undefined>(undefined);
  const [isSubmittingExpense, setIsSubmittingExpense] = useState(false);

  // Safe formatting helpers
  const formatCurrency = (val?: number | null): string => {
    if (val === undefined || val === null || isNaN(val)) {
      return 'Budget information unavailable';
    }
    return `₹${val.toLocaleString('en-IN')}`;
  };

  const formatNumber = (val?: number | null, fallback: string = 'N/A'): string => {
    if (val === undefined || val === null || isNaN(val)) return fallback;
    return val.toLocaleString('en-IN');
  };

  const formatFloat = (val?: number | null, digits: number = 1, fallback: string = '0.0'): string => {
    if (val === undefined || val === null || isNaN(val)) return fallback;
    return val.toFixed(digits);
  };

  // Auth guard
  useEffect(() => {
    if (!authLoading && (!token || !user || user.role !== 'NGO')) {
      router.push('/login');
    }
  }, [user, token, authLoading, router]);

  const fetchProjectData = async () => {
    if (!projectId || !token) return;
    try {
      setLoading(true);
      setErrorMsg(null);

      const [detailRes, integrityRes] = await Promise.all([
        apiFetch(`/api/ngo/projects/${projectId}`),
        apiFetch(`/api/ngo/projects/${projectId}/integrity-analysis`).catch(() => null)
      ]);

      if (detailRes && detailRes.project) {
        const mappedProject = mapProjectResponse(detailRes.project);
        setData({
          ...detailRes,
          project: mappedProject
        });
      } else {
        setData(detailRes);
      }

      if (integrityRes) {
        setIntegrityAnalysis(integrityRes);
      }
    } catch (err: any) {
      setErrorMsg(getApiErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (projectId && token) {
      fetchProjectData();
    }
  }, [projectId, token]);

  const handleUploadEvidence = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!uploadFile) {
      setErrorMsg('Please select a file to upload.');
      return;
    }

    try {
      setIsUploading(true);
      setErrorMsg(null);
      setSuccessMsg(null);

      const formData = new FormData();
      formData.append('file', uploadFile);
      formData.append('evidence_type', uploadCategory);

      // Call API directly with token
      const res = await fetch(`http://localhost:8000/api/ngo/projects/${projectId}/evidence`, {
        method: 'POST',
        headers: {
          Authorization: `Bearer ${token}`
        },
        body: formData
      });

      const responseData = await res.json();
      if (!res.ok) {
        throw responseData;
      }

      setSuccessMsg(`Evidence '${uploadFile.name}' uploaded & forensic analysis completed successfully.`);
      setShowUploadModal(false);
      setUploadFile(null);
      fetchProjectData();
    } catch (err: any) {
      setErrorMsg(getApiErrorMessage(err));
    } finally {
      setIsUploading(false);
    }
  };

  const handleAddExpense = async (e: React.FormEvent) => {
    e.preventDefault();
    if (expenseAmount <= 0) {
      setErrorMsg('Expense amount must be greater than zero.');
      return;
    }

    try {
      setIsSubmittingExpense(true);
      setErrorMsg(null);
      setSuccessMsg(null);

      const payload = {
        invoice_number: expenseInvoice,
        vendor_name: expenseVendor,
        amount: Number(expenseAmount),
        expense_date: expenseDate,
        description: expenseDesc,
        evidence_id: expenseEvidenceId ? Number(expenseEvidenceId) : undefined
      };

      await apiFetch(`/api/ngo/projects/${projectId}/expenses`, {
        method: 'POST',
        body: JSON.stringify(payload)
      });

      setSuccessMsg('Project expense recorded & financial integrity re-evaluated successfully.');
      setShowExpenseModal(false);
      setExpenseInvoice('');
      setExpenseVendor('');
      setExpenseAmount(1000);
      setExpenseDesc('');
      fetchProjectData();
    } catch (err: any) {
      setErrorMsg(getApiErrorMessage(err));
    } finally {
      setIsSubmittingExpense(false);
    }
  };

  if (authLoading || loading) {
    return (
      <div className="min-h-screen bg-slate-50 flex items-center justify-center p-4">
        <div className="text-center space-y-3">
          <div className="inline-block h-10 w-10 animate-spin rounded-full border-4 border-blue-600 border-t-transparent"></div>
          <p className="text-sm font-bold text-slate-700">Loading Project Evidence & Integrity Analysis...</p>
        </div>
      </div>
    );
  }

  if (errorMsg && !data) {
    return (
      <div className="min-h-screen bg-slate-50 p-6 flex flex-col items-center justify-center">
        <div className="bg-white p-8 rounded-3xl border border-slate-200 max-w-lg w-full text-center space-y-4 shadow-card">
          <AlertTriangle className="mx-auto h-12 w-12 text-rose-500" />
          <h2 className="text-lg font-bold text-slate-900">Project Not Accessible</h2>
          <p className="text-xs text-rose-700 bg-rose-50 p-3 rounded-xl border border-rose-200">{errorMsg}</p>
          <button
            onClick={() => router.push('/ngo/dashboard')}
            className="inline-flex items-center space-x-2 rounded-xl bg-blue-600 px-5 py-2.5 text-xs font-bold text-white hover:bg-blue-700"
          >
            <ArrowLeft className="h-4 w-4" />
            <span>Back to NGO Dashboard</span>
          </button>
        </div>
      </div>
    );
  }

  if (!data) return null;

  const { project, evidence_files, expenses, findings, risk_analysis } = data;

  const currentStatus = risk_analysis?.status || project.integrity_status || 'VERIFIED';
  const currentRiskScore = risk_analysis?.risk_score ?? project.risk_score ?? 0.0;
  const currentRiskLevel = risk_analysis?.risk_level || project.risk_level || 'LOW';

  // Evidence Filter Logic
  const filteredEvidence = evidence_files.filter((ev) => {
    if (evidenceCategory === 'ALL') return true;
    if (evidenceCategory === 'PHOTOS') return ['BEFORE_PHOTO', 'DURING_PHOTO', 'AFTER_PHOTO', 'SITE_PHOTO'].includes(ev.evidence_type);
    if (evidenceCategory === 'BEFORE_PHOTO') return ev.evidence_type === 'BEFORE_PHOTO';
    if (evidenceCategory === 'DURING_PHOTO') return ev.evidence_type === 'DURING_PHOTO';
    if (evidenceCategory === 'AFTER_PHOTO') return ev.evidence_type === 'AFTER_PHOTO';
    if (evidenceCategory === 'DOCUMENTS') return ['CERTIFICATE', 'DOCUMENT'].includes(ev.evidence_type);
    if (evidenceCategory === 'BILLS') return ['INVOICE', 'RECEIPT'].includes(ev.evidence_type);
    if (evidenceCategory === 'OTHER') return ev.evidence_type === 'OTHER_PROOF';
    return true;
  });

  const beforePhotos = evidence_files.filter(e => e.evidence_type === 'BEFORE_PHOTO');
  const duringPhotos = evidence_files.filter(e => e.evidence_type === 'DURING_PHOTO' || e.evidence_type === 'SITE_PHOTO');
  const afterPhotos = evidence_files.filter(e => e.evidence_type === 'AFTER_PHOTO');

  const getImageUrl = (path: string) => {
    if (!path) return '';
    if (path.startsWith('http')) return path;
    return `http://localhost:8000/${path.replace(/\\/g, '/')}`;
  };

  return (
    <div className="min-h-screen bg-slate-50/80 pb-24">
      {/* Sticky Header */}
      <header className="sticky top-0 z-30 bg-white/90 backdrop-blur-md border-b border-slate-200/80 shadow-xs">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 py-3.5 flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <button
              onClick={() => router.push('/ngo/dashboard')}
              className="p-2 rounded-xl text-slate-500 hover:text-blue-600 hover:bg-slate-100 transition-colors cursor-pointer"
              title="Return to Dashboard"
            >
              <ArrowLeft className="h-5 w-5" />
            </button>
            <div>
              <div className="flex items-center space-x-2">
                <span className="text-[10px] font-bold uppercase tracking-wider text-blue-600 bg-blue-50 px-2 py-0.5 rounded-full border border-blue-200">
                  {project.category}
                </span>
                <span className={`px-2 py-0.5 rounded-full text-[10px] font-bold uppercase border ${
                  project.status === 'ACTIVE' ? 'bg-emerald-50 text-emerald-700 border-emerald-200' : 'bg-slate-100 text-slate-700 border-slate-200'
                }`}>
                  {project.status}
                </span>
              </div>
              <h1 className="text-lg font-extrabold text-slate-900 leading-tight mt-0.5">{project.project_name}</h1>
            </div>
          </div>

          <div className="flex items-center space-x-3">
            <button
              onClick={fetchProjectData}
              className="inline-flex items-center space-x-1.5 p-2 rounded-xl text-slate-500 hover:text-blue-600 hover:bg-slate-100 transition-colors cursor-pointer"
              title="Refresh Integrity Analysis"
            >
              <RefreshCw className="h-4 w-4" />
            </button>
            <button
              onClick={() => setShowUploadModal(true)}
              className="inline-flex items-center space-x-2 rounded-xl bg-blue-600 px-4 py-2 text-xs font-bold text-white hover:bg-blue-700 shadow-xs shadow-blue-600/20 cursor-pointer"
            >
              <Upload className="h-4 w-4" />
              <span>Upload Evidence</span>
            </button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 py-6 space-y-6">

        {/* Global Notifications */}
        {errorMsg && (
          <div className="rounded-2xl border border-rose-200 bg-rose-50 p-4 text-xs text-rose-800 flex items-center justify-between shadow-xs">
            <div className="flex items-center space-x-2">
              <AlertTriangle className="h-4 w-4 text-rose-600 flex-shrink-0" />
              <span>{errorMsg}</span>
            </div>
            <button onClick={() => setErrorMsg(null)} className="text-xs font-bold underline cursor-pointer">Dismiss</button>
          </div>
        )}

        {successMsg && (
          <div className="rounded-2xl border border-emerald-200 bg-emerald-50 p-4 text-xs text-emerald-800 flex items-center justify-between shadow-xs">
            <div className="flex items-center space-x-2">
              <CheckCircle2 className="h-4 w-4 text-emerald-600 flex-shrink-0" />
              <span>{successMsg}</span>
            </div>
            <button onClick={() => setSuccessMsg(null)} className="text-xs font-bold underline cursor-pointer">Dismiss</button>
          </div>
        )}

        {/* ================================================== */}
        {/* 1. PROJECT INTEGRITY ANALYSIS DASHBOARD */}
        {/* ================================================== */}
        <div className="bg-white rounded-3xl border border-slate-200/90 p-6 sm:p-8 shadow-card space-y-6">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-100 pb-6">
            <div>
              <div className="flex items-center space-x-2 text-xs font-extrabold uppercase tracking-widest text-blue-600 mb-1">
                <ShieldCheck className="h-4 w-4 text-blue-600" />
                <span>PROJECT INTEGRITY & AI FORENSIC ANALYSIS</span>
              </div>
              <h2 className="text-2xl font-black text-slate-900">Project Verification Overview</h2>
              <p className="text-xs text-slate-500 mt-1">
                Real-time automated evaluation combining photo forensics, SHA-256 / pHash duplicate checks, financial OCR, and identity cross-validation.
              </p>
            </div>

            {/* Overall Risk Badge */}
            <div className="flex items-center space-x-3 bg-slate-50 p-4 rounded-2xl border border-slate-200">
              <div className="text-right">
                <span className="text-[10px] uppercase font-bold text-slate-400 block">Overall Risk Score</span>
                <span className="text-2xl font-black text-slate-900">{currentRiskScore.toFixed(1)}%</span>
              </div>
              <div className={`px-4 py-2 rounded-xl text-xs font-black uppercase border flex items-center space-x-1.5 ${
                currentStatus === 'VERIFIED' ? 'bg-emerald-50 text-emerald-800 border-emerald-300' :
                currentStatus === 'NEEDS_ADMIN_REVIEW' ? 'bg-amber-50 text-amber-800 border-amber-300' :
                'bg-rose-50 text-rose-800 border-rose-300'
              }`}>
                {currentStatus === 'VERIFIED' && <ShieldCheck className="h-4 w-4 text-emerald-600" />}
                {currentStatus === 'NEEDS_ADMIN_REVIEW' && <ShieldAlert className="h-4 w-4 text-amber-600" />}
                {currentStatus === 'REJECTED' && <ShieldX className="h-4 w-4 text-rose-600" />}
                <span>{currentStatus.replace(/_/g, ' ')}</span>
              </div>
            </div>
          </div>

          {/* AI Recommendation Message */}
          {risk_analysis?.recommendation && (
            <div className="rounded-2xl bg-blue-50/70 border border-blue-200/80 p-4 text-xs text-slate-800 flex items-start space-x-3">
              <FileCheck className="h-5 w-5 text-blue-600 flex-shrink-0 mt-0.5" />
              <div>
                <span className="font-bold text-blue-900 block mb-0.5">Automated Risk Analysis Summary</span>
                <span>{risk_analysis.recommendation}</span>
              </div>
            </div>
          )}

          {/* Breakdown Grid */}
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {/* 1. Document Identity */}
            <div className="bg-slate-50/80 p-4 rounded-2xl border border-slate-200/80 space-y-2">
              <div className="flex items-center justify-between text-xs">
                <span className="font-bold text-slate-600">Document Identity</span>
                <span className="font-extrabold text-slate-900">{(risk_analysis?.document_identity_risk ?? 0).toFixed(1)}%</span>
              </div>
              <div className="w-full bg-slate-200 rounded-full h-2 overflow-hidden">
                <div className="bg-blue-600 h-2 rounded-full" style={{ width: `${Math.min(100, risk_analysis?.document_identity_risk || 0)}%` }}></div>
              </div>
              <span className="text-[10px] font-bold text-slate-500 uppercase block text-right">
                {(risk_analysis?.document_identity_risk ?? 0) === 0 ? 'MATCH' : 'HIGH RISK'}
              </span>
            </div>

            {/* 2. Photo Integrity */}
            <div className="bg-slate-50/80 p-4 rounded-2xl border border-slate-200/80 space-y-2">
              <div className="flex items-center justify-between text-xs">
                <span className="font-bold text-slate-600">Photo Integrity</span>
                <span className="font-extrabold text-slate-900">{(risk_analysis?.photo_integrity_risk ?? 0).toFixed(1)}%</span>
              </div>
              <div className="w-full bg-slate-200 rounded-full h-2 overflow-hidden">
                <div className="bg-emerald-600 h-2 rounded-full" style={{ width: `${Math.min(100, risk_analysis?.photo_integrity_risk || 0)}%` }}></div>
              </div>
              <span className="text-[10px] font-bold text-slate-500 uppercase block text-right">
                {(risk_analysis?.photo_integrity_risk ?? 0) < 15 ? 'LOW RISK' : 'RISK DETECTED'}
              </span>
            </div>

            {/* 3. Financial Integrity */}
            <div className="bg-slate-50/80 p-4 rounded-2xl border border-slate-200/80 space-y-2">
              <div className="flex items-center justify-between text-xs">
                <span className="font-bold text-slate-600">Financial Integrity</span>
                <span className="font-extrabold text-slate-900">{(risk_analysis?.financial_integrity_risk ?? 0).toFixed(1)}%</span>
              </div>
              <div className="w-full bg-slate-200 rounded-full h-2 overflow-hidden">
                <div className="bg-indigo-600 h-2 rounded-full" style={{ width: `${Math.min(100, risk_analysis?.financial_integrity_risk || 0)}%` }}></div>
              </div>
              <span className="text-[10px] font-bold text-slate-500 uppercase block text-right">
                {(risk_analysis?.financial_integrity_risk ?? 0) === 0 ? 'CLEAN' : 'INCONSISTENCY'}
              </span>
            </div>

            {/* 4. Evidence Consistency */}
            <div className="bg-slate-50/80 p-4 rounded-2xl border border-slate-200/80 space-y-2">
              <div className="flex items-center justify-between text-xs">
                <span className="font-bold text-slate-600">Evidence Consistency</span>
                <span className="font-extrabold text-slate-900">{(risk_analysis?.evidence_consistency_risk ?? 0).toFixed(1)}%</span>
              </div>
              <div className="w-full bg-slate-200 rounded-full h-2 overflow-hidden">
                <div className="bg-purple-600 h-2 rounded-full" style={{ width: `${Math.min(100, risk_analysis?.evidence_consistency_risk || 0)}%` }}></div>
              </div>
              <span className="text-[10px] font-bold text-slate-500 uppercase block text-right">
                {(risk_analysis?.evidence_consistency_risk ?? 0) === 0 ? 'CONSISTENT' : 'DUPLICATE CHECK'}
              </span>
            </div>
          </div>

          {/* Admin Review Required Banner */}
          {currentStatus !== 'VERIFIED' && (
            <div className="rounded-2xl border border-amber-200 bg-amber-50/90 p-5 space-y-3">
              <div className="flex items-center space-x-2 text-amber-900 font-extrabold text-xs uppercase tracking-wide">
                <AlertTriangle className="h-4 w-4 text-amber-600 flex-shrink-0" />
                <span>ADMINISTRATOR REVIEW REQUIRED</span>
              </div>
              <p className="text-xs text-amber-800">
                Automated risk analysis flagged evidence or financial records requiring administrator review before complete verification.
              </p>
              {findings && findings.length > 0 && (
                <ul className="space-y-1.5 pl-4 list-disc text-xs text-amber-900 font-medium">
                  {findings.map((f, idx) => (
                    <li key={idx}>
                      <span className="font-bold">{f.category.replace(/_/g, ' ')}:</span> {f.message}
                    </li>
                  ))}
                </ul>
              )}
            </div>
          )}
        </div>

        {/* ================================================== */}
        {/* 2. PROJECT OVERVIEW & METRICS */}
        {/* ================================================== */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 bg-white rounded-3xl border border-slate-200/90 p-6 shadow-card space-y-4">
            <h3 className="text-sm font-extrabold text-slate-900 uppercase tracking-wider flex items-center gap-2">
              <FolderPlus className="h-4 w-4 text-blue-600" />
              Project Scope & Details
            </h3>
            <p className="text-xs text-slate-600 leading-relaxed">
              {project.description || 'No detailed description provided for this field initiative.'}
            </p>

            {project.objective && (
              <div className="bg-slate-50 p-4 rounded-2xl border border-slate-200 text-xs space-y-1">
                <span className="font-bold text-slate-700 block">Project Objective & Outcomes</span>
                <p className="text-slate-600">{project.objective}</p>
              </div>
            )}

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-2 border-t border-slate-100 text-xs">
              {project.location && (
                <div className="flex items-center space-x-2">
                  <MapPin className="h-4 w-4 text-rose-500 flex-shrink-0" />
                  <div>
                    <span className="text-[10px] font-bold text-slate-400 block uppercase">Location</span>
                    <span className="font-bold text-slate-800">{project.location}</span>
                    {project.latitude !== undefined && project.latitude !== null && project.longitude !== undefined && project.longitude !== null && (
                      <span className="text-[10px] font-mono text-slate-400 block">GPS: {project.latitude.toFixed(4)}, {project.longitude.toFixed(4)}</span>
                    )}
                  </div>
                </div>
              )}

              <div className="flex items-center space-x-2">
                <Calendar className="h-4 w-4 text-blue-500 flex-shrink-0" />
                <div>
                  <span className="text-[10px] font-bold text-slate-400 block uppercase">Timeline</span>
                  <span className="font-bold text-slate-800">
                    {project.start_date ? new Date(project.start_date).toLocaleDateString() : 'N/A'} — {project.end_date ? new Date(project.end_date).toLocaleDateString() : 'N/A'}
                  </span>
                </div>
              </div>
            </div>
          </div>

          {/* Budget & Utilization Card */}
          <div className="bg-white rounded-3xl border border-slate-200/90 p-6 shadow-card space-y-4 flex flex-col justify-between">
            <h3 className="text-sm font-extrabold text-slate-900 uppercase tracking-wider flex items-center gap-2">
              <DollarSign className="h-4 w-4 text-emerald-600" />
              Financial Utilization
            </h3>

            <div className="space-y-3">
              <div className="flex justify-between items-center text-xs pb-2 border-b border-slate-100">
                <span className="text-slate-500 font-medium">Total Project Budget</span>
                <span className="font-extrabold text-slate-900">{formatCurrency(project.budget ?? project.total_budget)}</span>
              </div>
              <div className="flex justify-between items-center text-xs pb-2 border-b border-slate-100">
                <span className="text-slate-500 font-medium">Total Expenses Claimed</span>
                <span className="font-extrabold text-blue-700">{formatCurrency(project.total_expenses_claimed ?? project.amount_spent ?? 0)}</span>
              </div>
              <div className="flex justify-between items-center text-xs pb-2 border-b border-slate-100">
                <span className="text-slate-500 font-medium">Remaining Funds</span>
                <span className="font-extrabold text-emerald-700">
                  {(project.budget ?? project.total_budget) !== undefined
                    ? `₹${Math.max(0, (project.budget ?? project.total_budget)! - (project.total_expenses_claimed ?? project.amount_spent ?? 0)).toLocaleString('en-IN')}`
                    : 'Budget information unavailable'}
                </span>
              </div>
              <div className="flex justify-between items-center text-xs">
                <span className="text-slate-500 font-medium">Target Beneficiaries</span>
                <span className="font-extrabold text-slate-900">{formatNumber(project.beneficiary_count ?? project.number_of_beneficiaries ?? 0)} People</span>
              </div>
            </div>

            <div className="space-y-1.5 pt-2">
              <div className="flex justify-between text-xs">
                <span className="font-bold text-slate-600">Utilization Ratio</span>
                <span className="font-black text-emerald-600">{formatFloat(project.fund_utilization_ratio, 1)}%</span>
              </div>
              <div className="w-full bg-slate-100 rounded-full h-3 overflow-hidden border border-slate-200">
                <div
                  className="bg-emerald-500 h-3 rounded-full transition-all duration-500"
                  style={{ width: `${Math.min(100, project.fund_utilization_ratio ?? 0)}%` }}
                ></div>
              </div>
            </div>
          </div>
        </div>

        {/* ================================================== */}
        {/* 3. PROGRESS EVIDENCE TIMELINE (BEFORE / DURING / AFTER) */}
        {/* ================================================== */}
        <div className="bg-white rounded-3xl border border-slate-200/90 p-6 sm:p-8 shadow-card space-y-6">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-base font-extrabold text-slate-900 flex items-center gap-2">
                <Layers className="h-5 w-5 text-blue-600" />
                PROJECT PROGRESS EVIDENCE TIMELINE
              </h3>
              <p className="text-xs text-slate-500">Visual progress verification across project lifecycle phases.</p>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {/* BEFORE */}
            <div className="bg-slate-50 p-4 rounded-2xl border border-slate-200 space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-xs font-black uppercase text-amber-700 bg-amber-100/80 px-2.5 py-0.5 rounded-full">
                  BEFORE PHASE ({beforePhotos.length})
                </span>
              </div>
              {beforePhotos.length === 0 ? (
                <p className="text-xs text-slate-400 py-6 text-center italic">No Before photos uploaded</p>
              ) : (
                <div className="grid grid-cols-2 gap-2">
                  {beforePhotos.map((img) => (
                    <div
                      key={img.id}
                      onClick={() => setPreviewImage({ url: getImageUrl(img.file_path), title: img.file_name, meta: img })}
                      className="group relative h-24 rounded-xl overflow-hidden border border-slate-200 cursor-pointer bg-slate-900"
                    >
                      <img src={getImageUrl(img.file_path)} alt={img.file_name} className="h-full w-full object-cover group-hover:scale-105 transition-transform" />
                      <div className="absolute inset-0 bg-slate-950/40 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center text-white text-xs font-bold">
                        Inspect
                      </div>
                      <span className="absolute bottom-1 right-1 bg-slate-950/80 text-[9px] font-bold text-white px-1.5 py-0.5 rounded">
                        {img.tamper_risk_score}% Risk
                      </span>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* DURING */}
            <div className="bg-slate-50 p-4 rounded-2xl border border-slate-200 space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-xs font-black uppercase text-blue-700 bg-blue-100/80 px-2.5 py-0.5 rounded-full">
                  DURING PHASE ({duringPhotos.length})
                </span>
              </div>
              {duringPhotos.length === 0 ? (
                <p className="text-xs text-slate-400 py-6 text-center italic">No During photos uploaded</p>
              ) : (
                <div className="grid grid-cols-2 gap-2">
                  {duringPhotos.map((img) => (
                    <div
                      key={img.id}
                      onClick={() => setPreviewImage({ url: getImageUrl(img.file_path), title: img.file_name, meta: img })}
                      className="group relative h-24 rounded-xl overflow-hidden border border-slate-200 cursor-pointer bg-slate-900"
                    >
                      <img src={getImageUrl(img.file_path)} alt={img.file_name} className="h-full w-full object-cover group-hover:scale-105 transition-transform" />
                      <div className="absolute inset-0 bg-slate-950/40 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center text-white text-xs font-bold">
                        Inspect
                      </div>
                      <span className="absolute bottom-1 right-1 bg-slate-950/80 text-[9px] font-bold text-white px-1.5 py-0.5 rounded">
                        {img.tamper_risk_score}% Risk
                      </span>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* AFTER */}
            <div className="bg-slate-50 p-4 rounded-2xl border border-slate-200 space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-xs font-black uppercase text-emerald-700 bg-emerald-100/80 px-2.5 py-0.5 rounded-full">
                  AFTER PHASE ({afterPhotos.length})
                </span>
              </div>
              {afterPhotos.length === 0 ? (
                <p className="text-xs text-slate-400 py-6 text-center italic">No After photos uploaded</p>
              ) : (
                <div className="grid grid-cols-2 gap-2">
                  {afterPhotos.map((img) => (
                    <div
                      key={img.id}
                      onClick={() => setPreviewImage({ url: getImageUrl(img.file_path), title: img.file_name, meta: img })}
                      className="group relative h-24 rounded-xl overflow-hidden border border-slate-200 cursor-pointer bg-slate-900"
                    >
                      <img src={getImageUrl(img.file_path)} alt={img.file_name} className="h-full w-full object-cover group-hover:scale-105 transition-transform" />
                      <div className="absolute inset-0 bg-slate-950/40 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center text-white text-xs font-bold">
                        Inspect
                      </div>
                      <span className="absolute bottom-1 right-1 bg-slate-950/80 text-[9px] font-bold text-white px-1.5 py-0.5 rounded">
                        {img.tamper_risk_score}% Risk
                      </span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>

        {/* ================================================== */}
        {/* 4. PROJECT EVIDENCE MANAGEMENT */}
        {/* ================================================== */}
        <div className="bg-white rounded-3xl border border-slate-200/90 p-6 sm:p-8 shadow-card space-y-6">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-100 pb-4">
            <div>
              <h3 className="text-lg font-black text-slate-900 flex items-center gap-2">
                <ImageIcon className="h-5 w-5 text-blue-600" />
                Project Evidence Repository ({evidence_files.length})
              </h3>
              <p className="text-xs text-slate-500">Forensic tamper inspection, pHash duplicate detection, and SHA-256 verification.</p>
            </div>

            <button
              onClick={() => setShowUploadModal(true)}
              className="inline-flex items-center space-x-2 rounded-xl bg-blue-600 px-4 py-2 text-xs font-bold text-white hover:bg-blue-700 cursor-pointer shadow-xs"
            >
              <Upload className="h-4 w-4" />
              <span>Upload Project Evidence</span>
            </button>
          </div>

          {/* Evidence Category Filter */}
          <div className="flex space-x-1 border-b border-slate-100 pb-2 overflow-x-auto">
            {[
              { id: 'ALL', label: 'All Evidence' },
              { id: 'PHOTOS', label: 'All Photos' },
              { id: 'BEFORE_PHOTO', label: 'Before' },
              { id: 'DURING_PHOTO', label: 'During' },
              { id: 'AFTER_PHOTO', label: 'After' },
              { id: 'DOCUMENTS', label: 'Certificates' },
              { id: 'BILLS', label: 'Bills & Invoices' },
              { id: 'OTHER', label: 'Other Proof' }
            ].map((cat) => (
              <button
                key={cat.id}
                onClick={() => setEvidenceCategory(cat.id)}
                className={`px-3 py-1.5 rounded-xl text-xs font-bold transition-all cursor-pointer whitespace-nowrap ${
                  evidenceCategory === cat.id
                    ? 'bg-blue-600 text-white shadow-xs'
                    : 'text-slate-600 hover:bg-slate-100'
                }`}
              >
                {cat.label}
              </button>
            ))}
          </div>

          {/* Evidence List */}
          {filteredEvidence.length === 0 ? (
            <div className="py-12 text-center text-slate-400 bg-slate-50 rounded-2xl border border-slate-200">
              <ImageIcon className="mx-auto h-10 w-10 text-slate-300 mb-2" />
              <p className="text-xs font-bold text-slate-700">No project evidence uploaded yet.</p>
              <button
                onClick={() => setShowUploadModal(true)}
                className="mt-3 inline-flex items-center space-x-1.5 text-xs font-bold text-blue-600 hover:underline"
              >
                <PlusCircle className="h-3.5 w-3.5" />
                <span>Upload First Evidence File</span>
              </button>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {filteredEvidence.map((ev) => (
                <div key={ev.id} className="bg-slate-50 p-4 rounded-2xl border border-slate-200 space-y-3 flex flex-col justify-between">
                  <div className="flex items-start space-x-3">
                    {/* Thumbnail / Icon */}
                    {['BEFORE_PHOTO', 'DURING_PHOTO', 'AFTER_PHOTO', 'SITE_PHOTO'].includes(ev.evidence_type) ? (
                      <div
                        onClick={() => setPreviewImage({ url: getImageUrl(ev.file_path), title: ev.file_name, meta: ev })}
                        className="h-16 w-16 rounded-xl overflow-hidden border border-slate-300 flex-shrink-0 cursor-pointer bg-slate-900 group relative"
                      >
                        <img src={getImageUrl(ev.file_path)} alt={ev.file_name} className="h-full w-full object-cover group-hover:scale-105 transition-transform" />
                        <div className="absolute inset-0 bg-slate-950/40 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center text-white text-[10px] font-bold">
                          View
                        </div>
                      </div>
                    ) : (
                      <div className="h-16 w-16 rounded-xl bg-blue-100 border border-blue-200 flex items-center justify-center flex-shrink-0 text-blue-600 font-bold text-xs">
                        <FileText className="h-8 w-8" />
                      </div>
                    )}

                    <div className="space-y-1 min-w-0 flex-1">
                      <div className="flex items-center justify-between gap-1">
                        <span className="text-[9px] font-black uppercase text-blue-700 bg-blue-100/80 px-2 py-0.5 rounded-md">
                          {ev.evidence_type.replace(/_/g, ' ')}
                        </span>
                        <span className={`px-2 py-0.5 rounded-full text-[9px] font-black uppercase border ${
                          ev.verification_status === 'VERIFIED' ? 'bg-emerald-50 text-emerald-700 border-emerald-200' :
                          ev.verification_status === 'NEEDS_ADMIN_REVIEW' ? 'bg-amber-50 text-amber-700 border-amber-200' :
                          'bg-rose-50 text-rose-700 border-rose-200'
                        }`}>
                          {ev.verification_status.replace(/_/g, ' ')}
                        </span>
                      </div>

                      <h4 className="text-xs font-bold text-slate-900 truncate" title={ev.file_name}>{ev.file_name}</h4>
                      <p className="text-[10px] text-slate-400">Uploaded {new Date(ev.upload_timestamp).toLocaleString()}</p>
                    </div>
                  </div>

                  {/* Forensic Breakdown */}
                  <div className="bg-white p-3 rounded-xl border border-slate-200/80 space-y-2 text-[11px]">
                    <div className="flex justify-between items-center text-slate-600 font-medium">
                      <span>Forensic Tamper Score:</span>
                      <span className="font-bold text-slate-900">{ev.tamper_risk_score}% ({ev.tamper_risk_level})</span>
                    </div>

                    {ev.sha256_hash && (
                      <div className="text-[10px] font-mono text-slate-500 truncate" title={ev.sha256_hash}>
                        SHA-256: {ev.sha256_hash.substring(0, 16)}...
                      </div>
                    )}

                    {ev.p_hash && (
                      <div className="text-[10px] font-mono text-slate-500 truncate">
                        pHash: {ev.p_hash}
                      </div>
                    )}

                    {ev.ocr_text && (
                      <div className="bg-slate-50 p-2 rounded border border-slate-100 text-[10px] text-slate-600 line-clamp-2 italic">
                        OCR Text: "{ev.ocr_text}"
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* ================================================== */}
        {/* 5. EXPENSES & FINANCIAL EVIDENCE */}
        {/* ================================================== */}
        <div className="bg-white rounded-3xl border border-slate-200/90 p-6 sm:p-8 shadow-card space-y-6">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-100 pb-4">
            <div>
              <h3 className="text-lg font-black text-slate-900 flex items-center gap-2">
                <DollarSign className="h-5 w-5 text-emerald-600" />
                Project Expenses & Invoice Audit ({expenses.length})
              </h3>
              <p className="text-xs text-slate-500">Cross-reference recorded expenses against uploaded receipts with automated OCR amount checks.</p>
            </div>

            <button
              onClick={() => setShowExpenseModal(true)}
              className="inline-flex items-center space-x-2 rounded-xl bg-emerald-600 px-4 py-2 text-xs font-bold text-white hover:bg-emerald-700 cursor-pointer shadow-xs"
            >
              <PlusCircle className="h-4 w-4" />
              <span>Add Expense Entry</span>
            </button>
          </div>

          {expenses.length === 0 ? (
            <div className="py-12 text-center text-slate-400 bg-slate-50 rounded-2xl border border-slate-200">
              <DollarSign className="mx-auto h-10 w-10 text-slate-300 mb-2" />
              <p className="text-xs font-bold text-slate-700">No project expenses recorded yet.</p>
              <button
                onClick={() => setShowExpenseModal(true)}
                className="mt-3 inline-flex items-center space-x-1.5 text-xs font-bold text-emerald-600 hover:underline"
              >
                <PlusCircle className="h-3.5 w-3.5" />
                <span>Log First Expense</span>
              </button>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs border-collapse">
                <thead>
                  <tr className="border-b border-slate-200 text-[10px] font-bold uppercase text-slate-400">
                    <th className="py-3 px-3">Date</th>
                    <th className="py-3 px-3">Invoice # / Vendor</th>
                    <th className="py-3 px-3">Entered Amount</th>
                    <th className="py-3 px-3">OCR Extracted</th>
                    <th className="py-3 px-3">Comparison Result</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 text-slate-700 font-medium">
                  {expenses.map((exp) => (
                    <tr key={exp.id} className="hover:bg-slate-50">
                      <td className="py-3 px-3 text-slate-500">{new Date(exp.expense_date).toLocaleDateString()}</td>
                      <td className="py-3 px-3">
                        <span className="font-bold text-slate-900 block">{exp.invoice_number || 'Receipt'}</span>
                        <span className="text-[10px] text-slate-400">{exp.vendor_name || 'Generic Vendor'}</span>
                      </td>
                      <td className="py-3 px-3 font-extrabold text-slate-900">₹{exp.amount.toLocaleString('en-IN')}</td>
                      <td className="py-3 px-3 font-bold text-slate-600">
                        {exp.ocr_amount ? `₹${exp.ocr_amount.toLocaleString('en-IN')}` : 'N/A'}
                      </td>
                      <td className="py-3 px-3">
                        {exp.is_ocr_matched === true ? (
                          <span className="inline-flex items-center space-x-1 px-2.5 py-0.5 rounded-full text-[10px] font-black bg-emerald-50 text-emerald-700 border border-emerald-200">
                            <CheckCircle2 className="h-3 w-3" />
                            <span>VERIFIED MATCH</span>
                          </span>
                        ) : exp.is_ocr_matched === false ? (
                          <span className="inline-flex items-center space-x-1 px-2.5 py-0.5 rounded-full text-[10px] font-black bg-rose-50 text-rose-700 border border-rose-200">
                            <XCircle className="h-3 w-3" />
                            <span>MISMATCH DETECTED</span>
                          </span>
                        ) : (
                          <span className="text-[10px] text-slate-400">PENDING OCR</span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </main>

      {/* ================================================== */}
      {/* LIGHTBOX PREVIEW MODAL */}
      {/* ================================================== */}
      {previewImage && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/80 backdrop-blur-md p-4">
          <div className="relative max-w-4xl w-full bg-slate-900 rounded-3xl overflow-hidden border border-slate-800 shadow-2xl flex flex-col md:flex-row">
            <div className="flex-1 bg-black flex items-center justify-center p-4 min-h-[300px]">
              <img src={previewImage.url} alt={previewImage.title} className="max-h-[70vh] object-contain" />
            </div>

            <div className="w-full md:w-80 p-6 bg-slate-900 text-white space-y-4 flex flex-col justify-between">
              <div className="space-y-3">
                <div className="flex justify-between items-start">
                  <h3 className="text-sm font-bold text-slate-100 truncate">{previewImage.title}</h3>
                  <button onClick={() => setPreviewImage(null)} className="text-slate-400 hover:text-white font-black text-lg cursor-pointer">✕</button>
                </div>

                <div className="space-y-2 text-xs">
                  <div className="flex justify-between text-slate-400">
                    <span>Evidence Type:</span>
                    <span className="font-bold text-blue-400">{previewImage.meta.evidence_type}</span>
                  </div>
                  <div className="flex justify-between text-slate-400">
                    <span>Tamper Risk:</span>
                    <span className="font-bold text-amber-400">{previewImage.meta.tamper_risk_score}% ({previewImage.meta.tamper_risk_level})</span>
                  </div>
                  <div className="flex justify-between text-slate-400">
                    <span>Verification:</span>
                    <span className="font-bold text-emerald-400">{previewImage.meta.verification_status}</span>
                  </div>
                </div>

                {previewImage.meta.sha256_hash && (
                  <div className="bg-slate-950 p-2.5 rounded-xl border border-slate-800 text-[10px] font-mono text-slate-400 space-y-1 break-all">
                    <span className="text-slate-500 font-bold block">SHA-256 Hash:</span>
                    <span>{previewImage.meta.sha256_hash}</span>
                  </div>
                )}
              </div>

              <button
                onClick={() => setPreviewImage(null)}
                className="w-full rounded-xl bg-slate-800 py-2.5 text-xs font-bold text-slate-200 hover:bg-slate-700 cursor-pointer"
              >
                Close Inspector
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ================================================== */}
      {/* UPLOAD EVIDENCE MODAL */}
      {/* ================================================== */}
      {showUploadModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/60 backdrop-blur-sm p-4">
          <div className="w-full max-w-lg rounded-3xl bg-white p-6 sm:p-8 border border-slate-100 shadow-2xl space-y-6">
            <div className="flex justify-between items-center border-b border-slate-100 pb-3">
              <h3 className="text-base font-bold text-slate-900">Upload Project Evidence</h3>
              <button onClick={() => setShowUploadModal(false)} className="text-slate-400 hover:text-slate-700 font-bold text-lg cursor-pointer">✕</button>
            </div>

            <form onSubmit={handleUploadEvidence} className="space-y-4">
              <div>
                <label className="block text-xs font-bold text-slate-700 mb-1">Evidence Category</label>
                <select
                  value={uploadCategory}
                  onChange={(e) => setUploadCategory(e.target.value)}
                  className="w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 text-xs font-medium text-slate-900 focus:border-blue-500 focus:outline-none"
                >
                  <option value="BEFORE_PHOTO">Before Photo (Pre-project phase)</option>
                  <option value="DURING_PHOTO">During Photo (In-progress work)</option>
                  <option value="AFTER_PHOTO">After Photo (Completed milestone)</option>
                  <option value="CERTIFICATE">Certificate / Formal Document</option>
                  <option value="INVOICE">Invoice / Bill / Receipt</option>
                  <option value="OTHER_PROOF">Other Supporting Evidence</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-700 mb-1">Select Evidence File (JPG, PNG, PDF)</label>
                <input
                  type="file"
                  required
                  accept="image/*,application/pdf"
                  onChange={(e) => setUploadFile(e.target.files?.[0] || null)}
                  className="w-full text-xs text-slate-700 file:mr-4 file:py-2 file:px-4 file:rounded-xl file:border-0 file:text-xs file:font-bold file:bg-blue-50 file:text-blue-700 hover:file:bg-blue-100 cursor-pointer"
                />
              </div>

              <div className="bg-slate-50 p-3 rounded-xl border border-slate-200 text-[10px] text-slate-500 space-y-1">
                <span className="font-bold text-slate-700 block">Automated Processing Pipeline:</span>
                <p>• Calculates SHA-256 fingerprint & pHash perceptual hash.</p>
                <p>• Runs forensic tamper analysis & EXIF inspection.</p>
                <p>• Executes OCR text extraction & NGO identity validation.</p>
              </div>

              <div className="flex space-x-3 pt-2">
                <button
                  type="button"
                  onClick={() => setShowUploadModal(false)}
                  className="w-1/3 rounded-xl border border-slate-200 py-2.5 text-xs font-semibold text-slate-600 hover:bg-slate-50 cursor-pointer"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isUploading}
                  className="w-2/3 rounded-xl bg-blue-600 py-2.5 text-xs font-bold text-white hover:bg-blue-700 disabled:opacity-50 cursor-pointer shadow-xs"
                >
                  {isUploading ? 'Analyzing & Uploading...' : 'Upload & Run Forensics'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* ================================================== */}
      {/* ADD EXPENSE MODAL */}
      {/* ================================================== */}
      {showExpenseModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/60 backdrop-blur-sm p-4">
          <div className="w-full max-w-lg rounded-3xl bg-white p-6 sm:p-8 border border-slate-100 shadow-2xl space-y-6">
            <div className="flex justify-between items-center border-b border-slate-100 pb-3">
              <h3 className="text-base font-bold text-slate-900">Record Project Expense</h3>
              <button onClick={() => setShowExpenseModal(false)} className="text-slate-400 hover:text-slate-700 font-bold text-lg cursor-pointer">✕</button>
            </div>

            <form onSubmit={handleAddExpense} className="space-y-4">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-bold text-slate-700 mb-1">Invoice / Receipt #</label>
                  <input
                    type="text"
                    required
                    value={expenseInvoice}
                    onChange={(e) => setExpenseInvoice(e.target.value)}
                    placeholder="e.g. INV-2026-88"
                    className="w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 text-xs font-bold text-slate-900 focus:border-blue-500 focus:outline-none"
                  />
                </div>
                <div>
                  <label className="block text-xs font-bold text-slate-700 mb-1">Vendor / Supplier</label>
                  <input
                    type="text"
                    required
                    value={expenseVendor}
                    onChange={(e) => setExpenseVendor(e.target.value)}
                    placeholder="e.g. Apex Health Supplies"
                    className="w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 text-xs font-medium text-slate-900 focus:border-blue-500 focus:outline-none"
                  />
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-bold text-slate-700 mb-1">Amount (₹)</label>
                  <input
                    type="number"
                    required
                    min="1"
                    value={expenseAmount}
                    onChange={(e) => setExpenseAmount(parseFloat(e.target.value) || 0)}
                    className="w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 text-xs font-extrabold text-slate-900 focus:border-blue-500 focus:outline-none"
                  />
                </div>
                <div>
                  <label className="block text-xs font-bold text-slate-700 mb-1">Expense Date</label>
                  <input
                    type="date"
                    required
                    value={expenseDate}
                    onChange={(e) => setExpenseDate(e.target.value)}
                    className="w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 text-xs text-slate-900 focus:border-blue-500 focus:outline-none"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-700 mb-1">Description / Category</label>
                <input
                  type="text"
                  value={expenseDesc}
                  onChange={(e) => setExpenseDesc(e.target.value)}
                  placeholder="e.g. Purchase of 500 medical emergency kits"
                  className="w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 text-xs text-slate-900 focus:border-blue-500 focus:outline-none"
                />
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-700 mb-1">Link to Uploaded Invoice Document (Optional)</label>
                <select
                  value={expenseEvidenceId || ''}
                  onChange={(e) => setExpenseEvidenceId(e.target.value ? Number(e.target.value) : undefined)}
                  className="w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 text-xs font-medium text-slate-800 focus:border-blue-500 focus:outline-none"
                >
                  <option value="">No document linked</option>
                  {evidence_files.map((ev) => (
                    <option key={ev.id} value={ev.id}>
                      {ev.file_name} ({ev.evidence_type})
                    </option>
                  ))}
                </select>
              </div>

              <div className="flex space-x-3 pt-2">
                <button
                  type="button"
                  onClick={() => setShowExpenseModal(false)}
                  className="w-1/3 rounded-xl border border-slate-200 py-2.5 text-xs font-semibold text-slate-600 hover:bg-slate-50 cursor-pointer"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isSubmittingExpense}
                  className="w-2/3 rounded-xl bg-emerald-600 py-2.5 text-xs font-bold text-white hover:bg-emerald-700 disabled:opacity-50 cursor-pointer shadow-xs"
                >
                  {isSubmittingExpense ? 'Saving Expense...' : 'Save Expense & Run Audit'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
