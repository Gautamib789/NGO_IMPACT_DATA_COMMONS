'use client';

import React, { useState } from 'react';
import { useAuth } from '@/context/AuthContext';
import { Upload, FileText, ShieldAlert, CheckCircle2, AlertTriangle, XCircle, Info, Hash, ScanText } from 'lucide-react';
import { NGODocument } from './types';

interface DocumentsTabProps {
  documents: NGODocument[];
  onRefresh: () => void;
}

export default function DocumentsTab({ documents, onRefresh }: DocumentsTabProps) {
  const { apiFetch } = useAuth();
  const [docType, setDocType] = useState('80G_CERTIFICATE');
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [isUploading, setIsUploading] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  const handleDocUpload = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedFile) {
      setErrorMsg('Please select a document file to upload.');
      return;
    }

    try {
      setIsUploading(true);
      setErrorMsg(null);
      setSuccessMsg(null);

      const formData = new FormData();
      formData.append('document_type', docType);
      formData.append('file', selectedFile);

      await apiFetch('/api/ngos/upload-document', {
        method: 'POST',
        body: formData,
      });

      setSuccessMsg('Document successfully uploaded, hashed with SHA-256, and submitted for automated integrity analysis.');
      setSelectedFile(null);
      onRefresh();
    } catch (err: any) {
      setErrorMsg(err.message || 'Document upload failed.');
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <div className="space-y-6">
      
      {/* Risk-Based Language Mandatory Notice Banner */}
      <div className="rounded-2xl border border-blue-200 bg-blue-50/70 p-5 text-xs text-blue-900 space-y-1 shadow-xs">
        <div className="flex items-start space-x-2.5">
          <Info className="h-5 w-5 text-blue-600 flex-shrink-0 mt-0.5" />
          <div className="space-y-1">
            <h4 className="font-extrabold text-blue-950">Document Tamper Detection & Verification Notice</h4>
            <p className="leading-relaxed text-blue-800">
              Automated document analysis provides heuristic risk indicators (SHA-256 cryptographic hashing, PDF metadata editing software scans, and magic byte validation). A <strong>LOW tamper risk score</strong> indicates no structural anomalies were detected by automated scanners, but does not constitute absolute proof of authenticity or fiscal truth. Final verification decisions are audited by platform administrators.
            </p>
          </div>
        </div>
      </div>

      {errorMsg && (
        <div className="rounded-xl border border-rose-200 bg-rose-50 p-4 text-xs text-rose-800 flex items-center justify-between">
          <span>{errorMsg}</span>
          <button onClick={() => setErrorMsg(null)} className="text-xs font-bold underline cursor-pointer">Dismiss</button>
        </div>
      )}

      {successMsg && (
        <div className="rounded-xl border border-emerald-200 bg-emerald-50 p-4 text-xs text-emerald-800 flex items-center justify-between">
          <span>{successMsg}</span>
          <button onClick={() => setSuccessMsg(null)} className="text-xs font-bold underline cursor-pointer">Dismiss</button>
        </div>
      )}

      {/* Upload Form Card */}
      <div className="bg-white rounded-3xl border border-slate-200 p-6 md:p-8 shadow-card space-y-6">
        <div className="border-b border-slate-100 pb-4">
          <h2 className="text-xl font-bold text-slate-900 flex items-center gap-2">
            <Upload className="h-5 w-5 text-blue-600" />
            Upload Organization Compliance Document
          </h2>
          <p className="text-xs text-slate-500">Files are hashed with SHA-256 immediately upon upload to ensure non-repudiation.</p>
        </div>

        <form onSubmit={handleDocUpload} className="space-y-4 bg-slate-50 p-5 rounded-2xl border border-slate-200/80">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-bold text-slate-700 mb-1.5">Document Type</label>
              <select
                value={docType}
                onChange={(e) => setDocType(e.target.value)}
                className="w-full rounded-xl border border-slate-200 bg-white px-3.5 py-2.5 text-xs font-medium text-slate-800 focus:border-blue-500 focus:outline-none"
              >
                <option value="80G_CERTIFICATE">80G Tax Exemption Certificate</option>
                <option value="12A_REGISTRATION">12A Registration Certificate</option>
                <option value="FCRA_CERTIFICATE">FCRA International Certificate</option>
                <option value="PAN_CARD">NGO PAN Card Copy</option>
                <option value="AUDIT_REPORT">Annual Financial Audit Report</option>
                <option value="TRUST_DEED">Trust Deed / NGO Registration Bylaws</option>
              </select>
            </div>

            <div>
              <label className="block text-xs font-bold text-slate-700 mb-1.5">Select File (PDF, PNG, JPG)</label>
              <input
                type="file"
                required
                accept=".pdf,.png,.jpg,.jpeg"
                onChange={(e) => setSelectedFile(e.target.files ? e.target.files[0] : null)}
                className="w-full text-xs text-slate-600 file:mr-4 file:py-2 file:px-4 file:rounded-xl file:border-0 file:text-xs file:font-bold file:bg-blue-600 file:text-white hover:file:bg-blue-700 cursor-pointer"
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={isUploading || !selectedFile}
            className="w-full rounded-xl bg-blue-600 py-3 text-xs font-bold text-white hover:bg-blue-700 disabled:opacity-50 transition-all shadow-xs shadow-blue-600/20 cursor-pointer"
          >
            {isUploading ? 'Hashing with SHA-256 & Scanning...' : 'Upload Document for Integrity Scan'}
          </button>
        </form>
      </div>

      {/* Uploaded Documents Table */}
      <div className="bg-white rounded-3xl border border-slate-200 p-6 md:p-8 shadow-card space-y-6">
        <div className="border-b border-slate-100 pb-4">
          <h3 className="text-base font-bold text-slate-900">Uploaded Compliance Documents ({documents.length})</h3>
          <p className="text-xs text-slate-500">Cryptographic audit dossier and admin verification status.</p>
        </div>

        {documents.length === 0 ? (
          <div className="py-12 text-center text-slate-400">
            <FileText className="mx-auto h-10 w-10 text-slate-300 mb-2" />
            <p className="text-xs font-semibold">No compliance documents uploaded yet.</p>
          </div>
        ) : (
          <div className="space-y-4">
            {documents.map((doc) => (
              <div key={doc.id} className="bg-slate-50 p-5 rounded-2xl border border-slate-200 space-y-4">
                <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-3 border-b border-slate-200/80 pb-3">
                  <div className="flex items-center space-x-3">
                    <FileText className="h-5 w-5 text-blue-600 flex-shrink-0" />
                    <div>
                      <p className="font-bold text-slate-900 text-sm">{doc.document_type}</p>
                      <p className="text-xs text-slate-500 font-mono">{doc.file_name}</p>
                    </div>
                  </div>

                  <div className="flex items-center space-x-2">
                    <span className={`px-3 py-1 rounded-full text-xs font-bold uppercase border ${
                      doc.verification_status === 'VERIFIED' ? 'bg-emerald-50 text-emerald-700 border-emerald-300' :
                      doc.verification_status === 'NEEDS_ADMIN_REVIEW' ? 'bg-amber-50 text-amber-700 border-amber-300' :
                      doc.verification_status === 'REQUEST_CLARIFICATION' ? 'bg-blue-50 text-blue-700 border-blue-300' :
                      doc.verification_status === 'REJECTED' ? 'bg-rose-50 text-rose-700 border-rose-300' :
                      'bg-slate-100 text-slate-700 border-slate-300'
                    }`}>
                      {doc.verification_status}
                    </span>

                    {doc.tamper_risk_level && (
                      <span className={`px-2.5 py-1 rounded-full text-[10px] font-extrabold uppercase border ${
                        doc.tamper_risk_level === 'LOW' ? 'bg-emerald-100 text-emerald-800 border-emerald-200' :
                        doc.tamper_risk_level === 'MEDIUM' ? 'bg-amber-100 text-amber-800 border-amber-200' :
                        'bg-rose-100 text-rose-800 border-rose-200'
                      }`}>
                        RISK: {doc.tamper_risk_level} ({doc.tamper_risk_score || 0}%)
                      </span>
                    )}
                  </div>
                </div>

                {/* Technical Hash & Details */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs font-mono">
                  {doc.sha256_hash && (
                    <div className="bg-white p-3 rounded-xl border border-slate-200 space-y-0.5">
                      <span className="text-[10px] text-slate-400 font-sans uppercase font-bold flex items-center gap-1">
                        <Hash className="h-3 w-3 text-slate-400" /> Cryptographic SHA-256 Hash
                      </span>
                      <p className="text-blue-600 break-all text-[10px]">{doc.sha256_hash}</p>
                    </div>
                  )}

                  <div className="bg-white p-3 rounded-xl border border-slate-200 space-y-0.5 font-sans">
                    <span className="text-[10px] text-slate-400 uppercase font-bold flex items-center gap-1">
                      <ScanText className="h-3 w-3 text-slate-400" /> Real OCR Extraction Status
                    </span>
                    <p className="text-slate-800 text-xs font-medium">
                      {doc.ocr_text ? `Extracted (${doc.ocr_text.length} chars)` : 'No text extracted'}
                    </p>
                  </div>
                </div>

                {/* Document Integrity Risk Analysis Card */}
                {(() => {
                  let meta: any = null;
                  if (doc.exif_metadata) {
                    try {
                      meta = JSON.parse(doc.exif_metadata);
                    } catch (e) {
                      meta = { summary: doc.exif_metadata };
                    }
                  }

                  const orgCheck = meta?.identity_checks?.organization_name || {
                    detected_value: meta?.detected_org_name || null,
                    expected_value: meta?.expected_org_name || null,
                    validation_state: meta?.org_mismatch ? 'DETECTED_MISMATCH' : (meta?.detected_org_name ? 'DETECTED_MATCH' : (meta?.expected_org_name ? 'NOT_DETECTED' : 'NOT_APPLICABLE')),
                    confidence: meta?.detected_org_name ? 98.0 : 0.0
                  };

                  const regCheck = meta?.identity_checks?.registration_number || {
                    detected_value: meta?.detected_reg_number || null,
                    expected_value: meta?.expected_reg_number || null,
                    validation_state: meta?.reg_mismatch ? 'DETECTED_MISMATCH' : (meta?.detected_reg_number ? 'DETECTED_MATCH' : (meta?.expected_reg_number ? 'NOT_DETECTED' : 'NOT_APPLICABLE')),
                    confidence: meta?.detected_reg_number ? 98.0 : 0.0
                  };

                  const panCheck = meta?.identity_checks?.pan || {
                    detected_value: meta?.detected_pan || null,
                    expected_value: meta?.expected_pan || null,
                    validation_state: meta?.pan_mismatch ? 'DETECTED_MISMATCH' : (meta?.detected_pan ? 'DETECTED_MATCH' : (meta?.expected_pan ? 'NOT_DETECTED' : 'NOT_APPLICABLE')),
                    confidence: meta?.detected_pan ? 99.0 : 0.0
                  };

                  const hasIdentityChecks = (orgCheck && orgCheck.validation_state !== 'NOT_APPLICABLE') || (regCheck && regCheck.validation_state !== 'NOT_APPLICABLE') || (panCheck && panCheck.validation_state !== 'NOT_APPLICABLE');
                  const hasRiskDetails = doc.verification_status !== 'VERIFIED' || (doc.tamper_risk_score && doc.tamper_risk_score > 0) || hasIdentityChecks;

                  if (!hasRiskDetails && !doc.verification_message) return null;

                  const renderFieldBadge = (check: any, label: string) => {
                    if (!check || check.validation_state === 'NOT_APPLICABLE') return null;
                    const state = check.validation_state;
                    const isMatch = state === 'DETECTED_MATCH';
                    const isMismatch = state === 'DETECTED_MISMATCH';
                    const isNotDetected = state === 'NOT_DETECTED';

                    return (
                      <div className={`p-3.5 rounded-xl border space-y-2 ${
                        isMatch ? 'bg-emerald-50/70 border-emerald-200' :
                        isMismatch ? 'bg-rose-50/80 border-rose-200' :
                        'bg-amber-50/70 border-amber-200'
                      }`}>
                        <div className="flex justify-between items-center">
                          <span className="font-extrabold text-[10px] uppercase tracking-wider text-slate-700">{label}</span>
                          <span className={`font-extrabold px-2.5 py-0.5 rounded text-[10px] uppercase border ${
                            isMatch ? 'bg-emerald-100 text-emerald-800 border-emerald-300' :
                            isMismatch ? 'bg-rose-100 text-rose-800 border-rose-300' :
                            'bg-amber-100 text-amber-800 border-amber-300'
                          }`}>
                            {isMatch ? 'VERIFIED MATCH' : isMismatch ? 'MISMATCH DETECTED' : 'NOT DETECTED'}
                          </span>
                        </div>

                        <div className="grid grid-cols-2 gap-2 text-xs font-mono pt-0.5">
                          <div>
                            <span className="text-[10px] font-sans text-slate-500 block">Detected:</span>
                            <strong className="text-slate-900 font-bold break-words">{check.detected_value || 'None'}</strong>
                          </div>
                          <div>
                            <span className="text-[10px] font-sans text-slate-500 block">Expected:</span>
                            <strong className="text-slate-900 font-bold break-words">{check.expected_value || 'None'}</strong>
                          </div>
                        </div>

                        <div className="flex items-center justify-between text-[10px] font-sans text-slate-500 border-t border-black/5 pt-1 mt-1">
                          <span>Evidence Confidence:</span>
                          <span className="font-bold font-mono text-slate-700">{check.confidence}%</span>
                        </div>
                      </div>
                    );
                  };

                  return (
                    <div className={`p-4 rounded-2xl border space-y-3 font-sans text-xs ${
                      doc.verification_status === 'VERIFIED'
                        ? 'bg-emerald-50/60 border-emerald-200 text-emerald-950'
                        : doc.verification_status === 'REJECTED'
                        ? 'bg-rose-50/80 border-rose-200 text-rose-950'
                        : 'bg-amber-50/80 border-amber-200 text-amber-950'
                    }`}>
                      <div className="flex items-center justify-between border-b border-black/5 pb-2">
                        <div className="flex items-center gap-1.5 font-extrabold uppercase tracking-wider text-[11px]">
                          <ShieldAlert className={`h-4 w-4 ${doc.verification_status === 'VERIFIED' ? 'text-emerald-600' : doc.verification_status === 'REJECTED' ? 'text-rose-600' : 'text-amber-600'}`} />
                          Document Integrity & Ownership Risk Analysis
                        </div>
                        <span className={`font-extrabold text-[10px] px-2 py-0.5 rounded border ${
                          doc.verification_status === 'VERIFIED' ? 'bg-emerald-100 text-emerald-800 border-emerald-200' :
                          doc.verification_status === 'REJECTED' ? 'bg-rose-100 text-rose-800 border-rose-200' :
                          'bg-amber-100 text-amber-800 border-amber-200'
                        }`}>
                          Status: {doc.verification_status}
                        </span>
                      </div>

                      {/* Field Cross-Validation Cards */}
                      {hasIdentityChecks && (
                        <div className="grid grid-cols-1 md:grid-cols-3 gap-3 bg-white/90 p-3.5 rounded-xl border border-black/5 shadow-xs">
                          {renderFieldBadge(orgCheck, 'Organization Name Comparison')}
                          {renderFieldBadge(regCheck, 'Registration Number Comparison')}
                          {renderFieldBadge(panCheck, 'PAN / Tax ID Comparison')}
                        </div>
                      )}

                      {/* Evidence Findings & Reasons */}
                      {doc.verification_message && (
                        <div className="space-y-1 pt-1">
                          <span className="font-extrabold text-[10px] uppercase text-slate-600 block">Verification Evidence & Analysis Findings:</span>
                          <p className="text-xs leading-relaxed text-slate-800 font-medium">{doc.verification_message}</p>
                        </div>
                      )}
                    </div>
                  );
                })()}

                {/* Review Notes if any */}
                {doc.review_notes && (
                  <div className="bg-amber-50/80 p-3 rounded-xl border border-amber-200 text-xs text-amber-900 space-y-0.5">
                    <span className="font-bold text-amber-950 block">Admin Auditor Notes ({doc.reviewed_by_email || 'Admin'}):</span>
                    <p>{doc.review_notes}</p>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>

    </div>
  );
}
