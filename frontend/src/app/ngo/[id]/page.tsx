'use client';

import React, { useState, useEffect } from 'react';
import { useParams } from 'next/navigation';
import { useAuth } from '@/context/AuthContext';
import { 
  ShieldCheck, 
  Building2, 
  CheckCircle2, 
  FileText, 
  HeartHandshake, 
  TrendingUp, 
  Lock, 
  ArrowLeft, 
  Globe, 
  MapPin, 
  AlertTriangle, 
  Calendar, 
  Target, 
  PieChart, 
  Hash, 
  Award,
  Layers,
  Users
} from 'lucide-react';
import Link from 'next/link';

interface PublicDocument {
  id: number;
  document_type: string;
  file_name: string;
  upload_date: string;
  sha256_hash?: string;
  verification_status: string;
  tamper_risk_level: string;
}

interface PublicProject {
  id: number;
  project_name: string;
  description: string;
  category: string;
  location: string;
  budget: number;
  total_expenses_claimed: number;
  fund_utilization_ratio: number;
  target_beneficiaries: number;
  outcomes?: string;
  status: string;
}

interface PublicNGO {
  id: number;
  org_name: string;
  registration_number: string;
  tax_id: string;
  category: string;
  mission_statement?: string;
  vision?: string;
  website?: string;
  address?: string;
  city?: string;
  state?: string;
  district?: string;
  pin_code?: string;
  organization_type?: string;
  established_date?: string;
  operating_areas?: string;
  doc_completeness_score: number;
  transparency_score: number;
  total_expenses: number;
  total_donations_received: number;
  beneficiary_count: number;
  government_verification_status: string;
  risk_level: string;
  created_at: string;
  documents: PublicDocument[];
}

export default function NGOPublicDetailPage() {
  const params = useParams();
  const ngoId = params.id;
  const { user, apiFetch } = useAuth();
  const [ngo, setNgo] = useState<PublicNGO | null>(null);
  const [projects, setProjects] = useState<PublicProject[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Donation modal state
  const [showDonateModal, setShowDonateModal] = useState(false);
  const [donationAmount, setDonationAmount] = useState<number>(1000);
  const [customAmount, setCustomAmount] = useState<string>('');
  const [donorMsg, setDonorMsg] = useState<string>('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [donationSuccess, setDonationSuccess] = useState<any>(null);

  useEffect(() => {
    const fetchPublicData = async () => {
      try {
        setLoading(true);
        setError(null);
        const [ngoData, projData] = await Promise.allSettled([
          apiFetch(`/api/public/ngos/${ngoId}`),
          apiFetch(`/api/public/ngos/${ngoId}/projects`),
        ]);

        if (ngoData.status === 'fulfilled') {
          setNgo(ngoData.value);
        } else {
          setError('Public NGO profile not found or unavailable.');
        }

        if (projData.status === 'fulfilled') {
          setProjects(projData.value);
        }
      } catch (err: any) {
        console.error('Failed to load public NGO profile', err);
        setError('Error loading NGO profile dossier.');
      } finally {
        setLoading(false);
      }
    };
    if (ngoId) fetchPublicData();
  }, [ngoId]);

  const handleDonateSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!ngo) return;
    if (!user) {
      alert('Please log in or register to complete a verified donation.');
      return;
    }

    const finalAmount = customAmount ? parseFloat(customAmount) : donationAmount;
    if (!finalAmount || finalAmount <= 0) return;

    try {
      setIsSubmitting(true);
      const res = await apiFetch('/api/donations/create', {
        method: 'POST',
        body: JSON.stringify({
          ngo_id: ngo.id,
          amount: finalAmount,
          currency: 'INR',
          donor_name: user.full_name,
          message: donorMsg,
        }),
      });

      setDonationSuccess(res);
    } catch (err: any) {
      alert(err.message || 'Donation submission failed');
    } finally {
      setIsSubmitting(false);
    }
  };

  if (loading) {
    return (
      <div className="text-center py-24 text-slate-400 bg-slate-50 min-h-screen flex flex-col items-center justify-center">
        <div className="inline-block h-10 w-10 animate-spin rounded-full border-4 border-blue-600 border-t-transparent mb-4"></div>
        <p className="text-xs font-semibold text-slate-600">Retrieving Public Transparency Dossier...</p>
      </div>
    );
  }

  if (error || !ngo) {
    return (
      <div className="mx-auto max-w-4xl px-4 py-20 text-center text-slate-500 space-y-4 bg-slate-50 min-h-screen flex flex-col items-center justify-center">
        <Building2 className="h-16 w-16 text-slate-300" />
        <h2 className="text-2xl font-extrabold text-slate-900">NGO Profile Not Found</h2>
        <p className="text-xs text-slate-500 max-w-md">The requested NGO profile may be unapproved, inactive, or invalid under public transparency standards.</p>
        <Link href="/explore" className="inline-flex items-center space-x-2 rounded-xl bg-blue-600 px-5 py-2.5 text-xs font-bold text-white hover:bg-blue-700 shadow-sm transition-all">
          <ArrowLeft className="h-4 w-4" />
          <span>Return to NGO Directory</span>
        </Link>
      </div>
    );
  }

  const govStatus = ngo.government_verification_status || 'NOT_VERIFIED';

  return (
    <div className="min-h-screen bg-slate-50/70 pb-24 pt-6">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 space-y-8">
        
        {/* Navigation Breadcrumb */}
        <div className="flex items-center justify-between">
          <Link href="/explore" className="inline-flex items-center space-x-1.5 text-xs font-bold text-slate-500 hover:text-blue-600 transition-colors">
            <ArrowLeft className="h-4 w-4" />
            <span>Return to Public Directory</span>
          </Link>

          <span className="text-[11px] font-mono text-slate-400">
            PUBLIC AUDIT ID: #NGO-{ngo.id.toString().padStart(4, '0')}
          </span>
        </div>

        {/* SIMULATED DEMO GOVERNMENT REGISTRY MANDATORY DISCLAIMER BANNER */}
        <div className="rounded-2xl border-2 border-amber-300 bg-gradient-to-r from-amber-50 to-orange-50 p-5 shadow-xs space-y-2">
          <div className="flex items-start space-x-3">
            <AlertTriangle className="h-6 w-6 text-amber-600 flex-shrink-0 mt-0.5" />
            <div className="space-y-1">
              <h3 className="text-xs font-extrabold tracking-wider uppercase text-amber-900">
                SIMULATED DEMO GOVERNMENT REGISTRY FOR ACADEMIC / PROJECT DEMONSTRATION ONLY
              </h3>
              <p className="text-xs text-amber-800 leading-relaxed">
                This public transparency profile displays regulatory verification status generated by cross-matching credentials against a simulated, pre-seeded demo registry database (FCRA, 80G, and MCA NGO Darpan records). It is designed for academic demonstration and system evaluation purposes and does not represent an active connection to official government servers.
              </p>
            </div>
          </div>
        </div>

        {/* Header Profile Banner */}
        <div className="rounded-3xl border border-slate-200/80 bg-white p-6 md:p-8 shadow-card space-y-6">
          <div className="flex flex-col md:flex-row md:items-start md:justify-between gap-6">
            
            <div className="space-y-3 max-w-3xl">
              <div className="flex flex-wrap items-center gap-2">
                {/* Government Verification Badge */}
                <span className={`inline-flex items-center gap-1.5 rounded-full px-3 py-1 text-xs font-extrabold border ${
                  govStatus === 'VERIFIED'
                    ? 'bg-emerald-50 text-emerald-700 border-emerald-300'
                    : govStatus === 'PARTIAL_MATCH'
                    ? 'bg-amber-50 text-amber-700 border-amber-300'
                    : 'bg-slate-100 text-slate-700 border-slate-300'
                }`}>
                  <ShieldCheck className="h-3.5 w-3.5" />
                  {govStatus === 'VERIFIED'
                    ? 'VERIFIED DEMO REGISTRY STATUS'
                    : govStatus === 'PARTIAL_MATCH'
                    ? 'PARTIAL DEMO REGISTRY MATCH'
                    : 'REGISTRY UNVERIFIED (DEMO)'}
                </span>

                {/* Organization Type */}
                <span className="inline-flex items-center gap-1 rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold text-slate-700">
                  <Building2 className="h-3 w-3 text-slate-500" />
                  {ngo.organization_type || 'Trust'}
                </span>

                {/* Established Date */}
                {ngo.established_date && (
                  <span className="inline-flex items-center gap-1 rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold text-slate-700">
                    <Calendar className="h-3 w-3 text-slate-500" />
                    Est. {new Date(ngo.established_date).getFullYear()}
                  </span>
                )}
              </div>

              <div>
                <h1 className="text-3xl font-extrabold text-slate-900 sm:text-4xl tracking-tight">{ngo.org_name}</h1>
                <p className="mt-2 text-xs text-slate-600 flex flex-wrap items-center gap-x-3 gap-y-1">
                  <span className="font-semibold text-blue-700 bg-blue-50 px-2.5 py-0.5 rounded-md border border-blue-100">{ngo.category}</span>
                  <span>•</span>
                  <span className="font-mono text-slate-700">Reg #: {ngo.registration_number}</span>
                  <span>•</span>
                  <span className="font-mono text-slate-700">Tax ID: {ngo.tax_id}</span>
                </p>
              </div>

              {(ngo.city || ngo.state || ngo.address) && (
                <p className="text-xs text-slate-500 flex items-center gap-1.5">
                  <MapPin className="h-3.5 w-3.5 text-slate-400 flex-shrink-0" />
                  <span>
                    {[ngo.city, ngo.state, ngo.address].filter(Boolean).join(', ')}
                  </span>
                </p>
              )}
            </div>

            <div className="flex flex-row md:flex-col items-center md:items-end justify-between gap-4 border-t md:border-t-0 border-slate-100 pt-4 md:pt-0">
              <div className="bg-gradient-to-b from-slate-50 to-emerald-50/50 p-4 rounded-2xl border border-slate-200 text-center min-w-[140px]">
                <span className="block text-[10px] text-slate-500 uppercase font-bold tracking-wider">Transparency Index</span>
                <span className="text-3xl font-extrabold text-emerald-600">{ngo.transparency_score}%</span>
                <span className="block text-[9px] text-slate-400 mt-0.5 font-mono">Verified Score</span>
              </div>

              <button
                onClick={() => setShowDonateModal(true)}
                className="flex items-center space-x-2 rounded-2xl bg-blue-600 hover:bg-blue-700 px-6 py-3.5 text-xs font-bold text-white shadow-md shadow-blue-600/20 transition-all cursor-pointer"
              >
                <HeartHandshake className="h-4 w-4" />
                <span>Support via Verified Donation</span>
              </button>
            </div>

          </div>
        </div>

        {/* Main 2-Column Content Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          
          {/* Left Column (2 Cols): Mission, Active Projects, Public Documents */}
          <div className="lg:col-span-2 space-y-8">
            
            {/* Mission & Vision Card */}
            <div className="bg-white rounded-3xl border border-slate-200/80 p-6 md:p-8 shadow-card space-y-4">
              <h2 className="text-base font-bold text-slate-900 flex items-center gap-2 border-b border-slate-100 pb-3">
                <Building2 className="h-5 w-5 text-blue-600" />
                Organizational Mission & Scope
              </h2>

              <div className="space-y-3 text-xs text-slate-600 leading-relaxed">
                <div>
                  <h3 className="font-bold text-slate-900 mb-1">Mission Statement</h3>
                  <p className="bg-slate-50 p-4 rounded-xl border border-slate-200/80 text-slate-700">
                    {ngo.mission_statement || 'No mission description published.'}
                  </p>
                </div>

                {ngo.vision && (
                  <div>
                    <h3 className="font-bold text-slate-900 mb-1">Vision</h3>
                    <p className="bg-slate-50 p-4 rounded-xl border border-slate-200/80 text-slate-700">
                      {ngo.vision}
                    </p>
                  </div>
                )}

                {ngo.operating_areas && (
                  <div>
                    <h3 className="font-bold text-slate-900 mb-1">Operating Areas</h3>
                    <p className="text-slate-700">{ngo.operating_areas}</p>
                  </div>
                )}

                {ngo.website && (
                  <div className="pt-2">
                    <a
                      href={ngo.website}
                      target="_blank"
                      rel="noreferrer"
                      className="inline-flex items-center gap-1.5 text-xs text-blue-600 hover:underline font-bold"
                    >
                      <Globe className="h-4 w-4" />
                      <span>Official Website: {ngo.website} ↗</span>
                    </a>
                  </div>
                )}
              </div>
            </div>

            {/* Public Transparency Projects Card */}
            <div className="bg-white rounded-3xl border border-slate-200/80 p-6 md:p-8 shadow-card space-y-6">
              <div className="flex items-center justify-between border-b border-slate-100 pb-4">
                <div>
                  <h2 className="text-base font-bold text-slate-900 flex items-center gap-2">
                    <Target className="h-5 w-5 text-blue-600" />
                    Public Transparency Projects ({projects.length})
                  </h2>
                  <p className="text-xs text-slate-500">Active community initiatives with verified fund utilization tracking.</p>
                </div>
              </div>

              {projects.length === 0 ? (
                <div className="text-center py-8 text-slate-400 bg-slate-50 rounded-2xl border border-slate-200/80">
                  <Layers className="mx-auto h-8 w-8 text-slate-300 mb-2" />
                  <p className="text-xs font-semibold">No active public projects listed for this organization.</p>
                </div>
              ) : (
                <div className="space-y-4">
                  {projects.map((proj) => (
                    <div key={proj.id} className="bg-slate-50/80 rounded-2xl border border-slate-200 p-5 space-y-3">
                      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-200/60 pb-3">
                        <div>
                          <span className="text-[10px] font-bold text-blue-600 uppercase tracking-wider">{proj.category}</span>
                          <h3 className="text-sm font-bold text-slate-900">{proj.project_name}</h3>
                        </div>
                        <span className="inline-flex items-center px-3 py-1 rounded-full text-[10px] font-bold uppercase bg-emerald-50 text-emerald-700 border border-emerald-200">
                          {proj.status}
                        </span>
                      </div>

                      <p className="text-xs text-slate-600 leading-relaxed">{proj.description}</p>

                      {proj.location && (
                        <p className="text-xs text-slate-500 flex items-center gap-1">
                          <MapPin className="h-3 w-3 text-slate-400" /> Location: {proj.location}
                        </p>
                      )}

                      {/* Budget vs Expenses Bar */}
                      <div className="space-y-1.5 pt-1">
                        <div className="flex justify-between text-[11px] font-mono">
                          <span className="text-slate-500 font-sans">Budget vs Claimed Expenses:</span>
                          <span className="font-bold text-slate-900">
                            ₹{proj.total_expenses_claimed.toLocaleString('en-IN')} / ₹{proj.budget.toLocaleString('en-IN')} ({proj.fund_utilization_ratio}%)
                          </span>
                        </div>
                        <div className="h-2 w-full bg-slate-200 rounded-full overflow-hidden">
                          <div
                            className="h-full bg-gradient-to-r from-blue-500 to-emerald-500 rounded-full"
                            style={{ width: `${Math.min(100, proj.fund_utilization_ratio)}%` }}
                          />
                        </div>
                      </div>

                      {/* Beneficiaries & Outcomes */}
                      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-2 text-xs">
                        <div className="bg-white p-3 rounded-xl border border-slate-200/80 flex items-center space-x-2">
                          <Users className="h-4 w-4 text-blue-600 flex-shrink-0" />
                          <div>
                            <span className="text-[10px] text-slate-400 block font-sans">Target Beneficiaries</span>
                            <span className="font-bold text-slate-900">{proj.target_beneficiaries.toLocaleString()} Assisted</span>
                          </div>
                        </div>

                        {proj.outcomes && (
                          <div className="bg-white p-3 rounded-xl border border-slate-200/80">
                            <span className="text-[10px] text-slate-400 block font-sans">Reported Outcomes</span>
                            <span className="font-semibold text-slate-800 text-[11px] truncate block">{proj.outcomes}</span>
                          </div>
                        )}
                      </div>

                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Public Compliance & Verified Audit Documents */}
            <div className="bg-white rounded-3xl border border-slate-200/80 p-6 md:p-8 shadow-card space-y-4">
              <div className="border-b border-slate-100 pb-3">
                <h2 className="text-base font-bold text-slate-900 flex items-center gap-2">
                  <FileText className="h-5 w-5 text-blue-600" />
                  Verified Compliance Documents ({ngo.documents.length})
                </h2>
                <p className="text-xs text-slate-500">Cryptographically verified document status without exposing private files or identities.</p>
              </div>

              {ngo.documents.length === 0 ? (
                <p className="text-xs text-slate-400 italic bg-slate-50 p-4 rounded-xl border border-slate-200 text-center">
                  No public compliance documents listed for this NGO.
                </p>
              ) : (
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  {ngo.documents.map((doc) => (
                    <div key={doc.id} className="bg-slate-50 p-4 rounded-2xl border border-slate-200 space-y-2 text-xs">
                      <div className="flex items-center justify-between">
                        <span className="font-bold text-slate-900">{doc.document_type}</span>
                        <span className="inline-flex items-center text-[10px] font-bold text-emerald-700 bg-emerald-50 px-2.5 py-0.5 rounded-full border border-emerald-200">
                          <CheckCircle2 className="h-3 w-3 mr-1" /> {doc.verification_status}
                        </span>
                      </div>

                      <p className="text-[10px] font-mono text-slate-500 truncate">{doc.file_name}</p>

                      {doc.sha256_hash && (
                        <div className="bg-white p-2 rounded-lg border border-slate-200/80 font-mono text-[9px] text-slate-600 break-all">
                          <span className="text-slate-400 block text-[8px] font-sans">SHA-256 HASH GUARANTEE</span>
                          {doc.sha256_hash.substring(0, 24)}...
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>

          </div>

          {/* Right Column (1 Col): Transparency Index Breakdown, Financial Summary & Ledger Notice */}
          <div className="space-y-6">
            
            {/* Transparency Score Breakdown Matrix */}
            <div className="bg-white rounded-3xl border border-slate-200/80 p-6 shadow-card space-y-4">
              <h2 className="text-sm font-extrabold text-slate-900 uppercase tracking-wider flex items-center gap-2 border-b border-slate-100 pb-3">
                <Award className="h-4 w-4 text-emerald-600" />
                Transparency & Compliance Matrix
              </h2>

              <div className="space-y-3 text-xs">
                <div className="bg-slate-50 p-3.5 rounded-2xl border border-slate-200 flex justify-between items-center">
                  <div>
                    <span className="font-bold text-slate-900 block">Overall Transparency Index</span>
                    <span className="text-[10px] text-slate-500">System Calculated Score</span>
                  </div>
                  <span className="text-xl font-extrabold text-emerald-600 font-mono">{ngo.transparency_score}%</span>
                </div>

                <div className="bg-slate-50 p-3.5 rounded-2xl border border-slate-200 flex justify-between items-center">
                  <div>
                    <span className="font-bold text-slate-900 block">Document Completeness</span>
                    <span className="text-[10px] text-slate-500">Required Dossiers Verified</span>
                  </div>
                  <span className="text-sm font-bold text-slate-800 font-mono">{ngo.doc_completeness_score}%</span>
                </div>

                <div className="bg-slate-50 p-3.5 rounded-2xl border border-slate-200 flex justify-between items-center">
                  <div>
                    <span className="font-bold text-slate-900 block">Demo Registry Status</span>
                    <span className="text-[10px] text-slate-500">Pre-seeded Govt Database</span>
                  </div>
                  <span className={`text-xs font-bold ${govStatus === 'VERIFIED' ? 'text-emerald-700' : 'text-amber-700'}`}>
                    {govStatus}
                  </span>
                </div>

                <div className="bg-slate-50 p-3.5 rounded-2xl border border-slate-200 flex justify-between items-center">
                  <div>
                    <span className="font-bold text-slate-900 block">Risk Assessment</span>
                    <span className="text-[10px] text-slate-500">AI Tamper Risk Evaluation</span>
                  </div>
                  <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-[10px] font-bold uppercase bg-emerald-50 text-emerald-700 border border-emerald-200">
                    {ngo.risk_level} RISK
                  </span>
                </div>
              </div>
            </div>

            {/* Aggregated Financial & Impact Metrics */}
            <div className="bg-white rounded-3xl border border-slate-200/80 p-6 shadow-card space-y-4">
              <h2 className="text-sm font-extrabold text-slate-900 uppercase tracking-wider flex items-center gap-2 border-b border-slate-100 pb-3">
                <TrendingUp className="h-4 w-4 text-emerald-600" />
                Aggregated Financial & Impact Dossier
              </h2>

              <div className="space-y-3 font-mono text-xs">
                <div className="bg-slate-50 p-4 rounded-2xl border border-slate-200 flex justify-between items-center">
                  <span className="text-slate-500 font-sans text-xs">Total Funds Raised</span>
                  <span className="font-bold text-emerald-700 text-sm">₹{ngo.total_donations_received.toLocaleString('en-IN')}</span>
                </div>

                <div className="bg-slate-50 p-4 rounded-2xl border border-slate-200 flex justify-between items-center">
                  <span className="text-slate-500 font-sans text-xs">Reported Expenses</span>
                  <span className="font-bold text-slate-900 text-sm">₹{ngo.total_expenses.toLocaleString('en-IN')}</span>
                </div>

                <div className="bg-slate-50 p-4 rounded-2xl border border-slate-200 flex justify-between items-center">
                  <span className="text-slate-500 font-sans text-xs">Beneficiaries Impacted</span>
                  <span className="font-bold text-slate-900 text-sm">{ngo.beneficiary_count.toLocaleString()}</span>
                </div>
              </div>

              {/* SHA-256 Blockchain Ledger Guarantee Notice */}
              <div className="p-4 bg-blue-50 border border-blue-200 rounded-2xl text-xs text-blue-900 space-y-2">
                <div className="flex items-center space-x-2 font-bold text-blue-900">
                  <Lock className="h-4 w-4 text-blue-600 flex-shrink-0" />
                  <span>SHA-256 Blockchain Ledger Guarantee</span>
                </div>
                <p className="text-[11px] leading-relaxed text-blue-800">
                  All donations processed for {ngo.org_name} automatically generate tamper-evident SHA-256 block hashes linked in immutable sequence.
                </p>
                <div className="pt-1">
                  <Link href="/ledger" className="inline-flex items-center space-x-1 text-[11px] font-bold text-blue-700 hover:underline">
                    <span>Inspect Public Blockchain Ledger ↗</span>
                  </Link>
                </div>
              </div>
            </div>

          </div>

        </div>

        {/* Verified Donation Modal */}
        {showDonateModal && (
          <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/60 backdrop-blur-sm p-4">
            <div className="w-full max-w-md rounded-3xl border border-slate-100 bg-white p-6 shadow-2xl space-y-4 text-slate-900">
              
              {donationSuccess ? (
                <div className="text-center space-y-4 py-3">
                  <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-full bg-emerald-100 text-emerald-600 border border-emerald-200">
                    <CheckCircle2 className="h-8 w-8" />
                  </div>
                  <h3 className="text-lg font-bold text-slate-900">Donation Recorded & Blocked</h3>
                  <p className="text-xs text-slate-600">
                    Your contribution of <span className="font-bold text-emerald-700">₹{donationSuccess.amount?.toLocaleString('en-IN')} {donationSuccess.currency}</span> has been logged on the SHA-256 ledger.
                  </p>

                  <div className="bg-slate-50 p-3.5 rounded-2xl border border-slate-200 text-left font-mono text-[10px] space-y-1">
                    <p className="text-slate-500 font-sans">Cryptographic Tx Hash:</p>
                    <p className="text-blue-600 break-all">{donationSuccess.transaction_hash}</p>
                  </div>

                  <button
                    onClick={() => {
                      setShowDonateModal(false);
                      setDonationSuccess(null);
                    }}
                    className="w-full rounded-xl bg-blue-600 py-3 text-xs font-bold text-white hover:bg-blue-700 shadow-sm shadow-blue-600/20"
                  >
                    Done
                  </button>
                </div>
              ) : (
                <form onSubmit={handleDonateSubmit} className="space-y-4">
                  <div className="flex justify-between items-start border-b border-slate-100 pb-3">
                    <div>
                      <span className="text-[10px] font-bold text-blue-600 uppercase tracking-wider">Verified NGO Donation</span>
                      <h3 className="text-base font-bold text-slate-900">{ngo.org_name}</h3>
                    </div>
                    <button
                      type="button"
                      onClick={() => setShowDonateModal(false)}
                      className="text-slate-400 hover:text-slate-700 text-lg font-bold"
                    >
                      ✕
                    </button>
                  </div>

                  <div>
                    <label className="block text-xs font-bold text-slate-700 mb-2">Select Donation Amount (INR)</label>
                    <div className="grid grid-cols-4 gap-2">
                      {[500, 1000, 2500, 5000].map((amt) => (
                        <button
                          key={amt}
                          type="button"
                          onClick={() => {
                            setDonationAmount(amt);
                            setCustomAmount('');
                          }}
                          className={`rounded-xl py-2 text-xs font-bold transition-all ${
                            donationAmount === amt && !customAmount
                              ? 'bg-blue-600 text-white shadow-xs'
                              : 'border border-slate-200 bg-slate-50 text-slate-700 hover:bg-slate-100'
                          }`}
                        >
                          ₹{amt.toLocaleString('en-IN')}
                        </button>
                      ))}
                    </div>

                    <input
                      type="number"
                      placeholder="Or enter custom amount (₹)..."
                      value={customAmount}
                      onChange={(e) => setCustomAmount(e.target.value)}
                      className="mt-2.5 w-full rounded-xl border border-slate-200 bg-slate-50 px-3.5 py-2.5 text-xs text-slate-900 placeholder-slate-400 focus:border-blue-500 focus:bg-white focus:outline-none"
                    />
                  </div>

                  <div>
                    <label className="block text-xs font-bold text-slate-700 mb-1">Impact Message (Optional)</label>
                    <textarea
                      rows={2}
                      value={donorMsg}
                      onChange={(e) => setDonorMsg(e.target.value)}
                      placeholder="Write a message of encouragement..."
                      className="w-full rounded-xl border border-slate-200 bg-slate-50 px-3.5 py-2.5 text-xs text-slate-900 placeholder-slate-400 focus:border-blue-500 focus:bg-white focus:outline-none"
                    />
                  </div>

                  <div className="flex space-x-2 pt-1">
                    <button
                      type="button"
                      onClick={() => setShowDonateModal(false)}
                      className="w-1/3 rounded-xl border border-slate-200 py-3 text-xs font-semibold text-slate-600 hover:bg-slate-50"
                    >
                      Cancel
                    </button>
                    <button
                      type="submit"
                      disabled={isSubmitting}
                      className="w-2/3 rounded-xl bg-blue-600 py-3 text-xs font-bold text-white hover:bg-blue-700 disabled:opacity-50 shadow-sm shadow-blue-600/20"
                    >
                      {isSubmitting ? 'Recording on Ledger...' : 'Confirm Donation'}
                    </button>
                  </div>
                </form>
              )}

            </div>
          </div>
        )}

      </div>
    </div>
  );
}
