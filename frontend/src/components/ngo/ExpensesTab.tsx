'use client';

import React, { useState, useEffect } from 'react';
import { useAuth } from '@/context/AuthContext';
import { DollarSign, PlusCircle, Upload, FileText, Hash, CheckCircle2, AlertTriangle, Filter, Trash2, ShieldCheck, Info } from 'lucide-react';
import { Expense, Project } from './types';

interface ExpensesTabProps {
  projects: Project[];
  onRefresh: () => void;
}

export default function ExpensesTab({ projects, onRefresh }: ExpensesTabProps) {
  const { apiFetch } = useAuth();
  const [expenses, setExpenses] = useState<Expense[]>([]);
  const [selectedProjectId, setSelectedProjectId] = useState<string>('ALL');
  const [loading, setLoading] = useState(true);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  // Add Expense Modal
  const [showAddModal, setShowAddModal] = useState(false);
  const [projectId, setProjectId] = useState<string>('');
  const [category, setCategory] = useState('Medical Supplies');
  const [description, setDescription] = useState('');
  const [amount, setAmount] = useState<number>(10000);
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Upload Receipt Modal
  const [uploadExpenseId, setUploadExpenseId] = useState<number | null>(null);
  const [receiptFile, setReceiptFile] = useState<File | null>(null);
  const [isUploading, setIsUploading] = useState(false);

  const fetchExpenses = async () => {
    try {
      setLoading(true);
      setErrorMsg(null);
      let url = '/api/ngo/expenses';
      if (selectedProjectId !== 'ALL') {
        url += `?project_id=${selectedProjectId}`;
      }
      const data = await apiFetch(url);
      setExpenses(data);
    } catch (err: any) {
      setErrorMsg(err.message || 'Failed to load expenses.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchExpenses();
  }, [selectedProjectId]);

  const handleAddExpense = async (e: React.FormEvent) => {
    e.preventDefault();
    if (amount <= 0) {
      setErrorMsg('Expense amount must be greater than zero.');
      return;
    }

    try {
      setIsSubmitting(true);
      setErrorMsg(null);
      setSuccessMsg(null);

      const payload = {
        project_id: projectId ? parseInt(projectId) : undefined,
        category,
        description,
        amount: Number(amount),
      };

      await apiFetch('/api/ngo/expenses', {
        method: 'POST',
        body: JSON.stringify(payload),
      });

      setSuccessMsg(`Expense claim for ₹${amount.toLocaleString('en-IN')} submitted successfully.`);
      setShowAddModal(false);
      fetchExpenses();
      onRefresh();
    } catch (err: any) {
      setErrorMsg(err.message || 'Failed to submit expense claim.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleUploadReceipt = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!uploadExpenseId || !receiptFile) return;

    try {
      setIsUploading(true);
      setErrorMsg(null);
      setSuccessMsg(null);

      const formData = new FormData();
      formData.append('file', receiptFile);

      const res = await apiFetch(`/api/ngo/expenses/${uploadExpenseId}/upload-receipt`, {
        method: 'POST',
        body: formData,
      });

      setSuccessMsg(`Receipt uploaded successfully! Cryptographic SHA-256 hash calculated (${res.receipt_sha256.substring(0, 16)}...).`);
      setUploadExpenseId(null);
      setReceiptFile(null);
      fetchExpenses();
      onRefresh();
    } catch (err: any) {
      setErrorMsg(err.message || 'Failed to upload receipt file.');
    } finally {
      setIsUploading(false);
    }
  };

  const handleDeleteExpense = async (id: number) => {
    if (!confirm('Are you sure you want to delete this expense record?')) return;

    try {
      setErrorMsg(null);
      setSuccessMsg(null);
      await apiFetch(`/api/ngo/expenses/${id}`, { method: 'DELETE' });
      setSuccessMsg('Expense record deleted successfully.');
      fetchExpenses();
      onRefresh();
    } catch (err: any) {
      setErrorMsg(err.message || 'Failed to delete expense.');
    }
  };

  return (
    <div className="space-y-6">
      
      {/* Receipt Status Notice Banner */}
      <div className="rounded-2xl border border-amber-200 bg-amber-50/70 p-5 text-xs text-amber-900 space-y-1 shadow-xs">
        <div className="flex items-start space-x-2.5">
          <Info className="h-5 w-5 text-amber-600 flex-shrink-0 mt-0.5" />
          <div className="space-y-1">
            <h4 className="font-extrabold text-amber-950">Expense Receipt Cryptographic Verification Notice</h4>
            <p className="leading-relaxed text-amber-800">
              When a receipt image or invoice PDF is uploaded, a <strong>SHA-256 cryptographic hash</strong> is calculated and recorded to verify file integrity. A status of <strong>VERIFIED</strong> confirms that the file was securely hashed and stored without corruption; it does not constitute absolute fiscal verification or proof of commercial authenticity.
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

      {/* Top Action & Filter Bar */}
      <div className="bg-white p-6 rounded-3xl border border-slate-200 shadow-card flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div className="flex items-center space-x-3">
          <Filter className="h-4 w-4 text-slate-400" />
          <span className="text-xs font-bold text-slate-700">Filter Project:</span>
          <select
            value={selectedProjectId}
            onChange={(e) => setSelectedProjectId(e.target.value)}
            className="rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 text-xs font-semibold text-slate-800 focus:border-blue-500 focus:outline-none"
          >
            <option value="ALL">All Projects ({projects.length})</option>
            {projects.map((p) => (
              <option key={p.id} value={p.id}>{p.project_name}</option>
            ))}
          </select>
        </div>

        <button
          onClick={() => {
            setAmount(10000);
            setDescription('');
            setCategory('Medical Supplies');
            setProjectId(projects.length > 0 ? String(projects[0].id) : '');
            setShowAddModal(true);
          }}
          className="inline-flex items-center space-x-2 rounded-xl bg-blue-600 px-5 py-2.5 text-xs font-bold text-white hover:bg-blue-700 transition-all shadow-xs shadow-blue-600/20 cursor-pointer"
        >
          <PlusCircle className="h-4 w-4" />
          <span>Add Expense Claim</span>
        </button>
      </div>

      {/* Expenses Table / Cards */}
      <div className="bg-white rounded-3xl border border-slate-200 p-6 md:p-8 shadow-card space-y-6">
        <div className="border-b border-slate-100 pb-4">
          <h3 className="text-base font-bold text-slate-900">Claimed Field Expenses ({expenses.length})</h3>
          <p className="text-xs text-slate-500">Expense records, receipt proof files, and SHA-256 cryptographic hashes.</p>
        </div>

        {loading ? (
          <div className="py-12 text-center text-slate-500">
            <div className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-blue-600 border-t-transparent mb-3"></div>
            <p className="text-xs font-semibold">Loading expense log...</p>
          </div>
        ) : expenses.length === 0 ? (
          <div className="py-12 text-center text-slate-400">
            <DollarSign className="mx-auto h-10 w-10 text-slate-300 mb-2" />
            <p className="text-xs font-semibold">No expense records found for this selection.</p>
          </div>
        ) : (
          <div className="space-y-4">
            {expenses.map((exp) => (
              <div key={exp.id} className="bg-slate-50 p-5 rounded-2xl border border-slate-200 space-y-4">
                <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-3 border-b border-slate-200/80 pb-3">
                  <div>
                    <span className="text-[10px] font-bold uppercase tracking-wider text-blue-600 bg-blue-50 px-2 py-0.5 rounded-full border border-blue-200">
                      {exp.category}
                    </span>
                    <h4 className="font-bold text-slate-900 text-base mt-1">₹{exp.amount.toLocaleString('en-IN')}</h4>
                    {exp.project_name && <p className="text-xs text-slate-500">Project: {exp.project_name}</p>}
                  </div>

                  <div className="flex items-center space-x-3">
                    <span className={`px-3 py-1 rounded-full text-xs font-bold uppercase border ${
                      exp.verification_status === 'VERIFIED' ? 'bg-emerald-50 text-emerald-700 border-emerald-300' :
                      exp.verification_status === 'PENDING' ? 'bg-amber-50 text-amber-700 border-amber-300' :
                      'bg-rose-50 text-rose-700 border-rose-300'
                    }`}>
                      {exp.verification_status === 'VERIFIED' ? '✓ RECEIPT HASH VERIFIED' : exp.verification_status}
                    </span>

                    <button
                      onClick={() => handleDeleteExpense(exp.id)}
                      className="p-1.5 text-slate-400 hover:text-rose-600 transition-colors cursor-pointer"
                      title="Delete Expense"
                    >
                      <Trash2 className="h-4 w-4" />
                    </button>
                  </div>
                </div>

                {exp.description && (
                  <p className="text-xs text-slate-600 leading-relaxed">{exp.description}</p>
                )}

                {/* Receipt Details or Upload Button */}
                <div className="pt-1">
                  {exp.receipt_sha256 ? (
                    <div className="bg-white p-3 rounded-xl border border-slate-200 text-xs font-mono space-y-1">
                      <div className="flex items-center justify-between text-[10px] text-slate-500 font-sans">
                        <span className="font-bold text-slate-700 flex items-center gap-1">
                          <FileText className="h-3 w-3 text-blue-600" /> Receipt File: {exp.receipt_file_name}
                        </span>
                        <span>SHA-256 Cryptographic Hash</span>
                      </div>
                      <p className="text-blue-600 break-all text-[10px]">{exp.receipt_sha256}</p>
                    </div>
                  ) : (
                    <div className="flex items-center justify-between bg-amber-50/60 p-3 rounded-xl border border-amber-200 text-xs">
                      <span className="text-amber-900 font-medium flex items-center gap-1.5">
                        <AlertTriangle className="h-4 w-4 text-amber-600 flex-shrink-0" />
                        No receipt proof file uploaded for this expense claim yet.
                      </span>
                      <button
                        onClick={() => {
                          setUploadExpenseId(exp.id);
                          setReceiptFile(null);
                        }}
                        className="inline-flex items-center space-x-1 font-bold text-blue-600 bg-white px-3 py-1.5 rounded-lg border border-blue-200 hover:bg-blue-50 transition-colors cursor-pointer"
                      >
                        <Upload className="h-3.5 w-3.5" />
                        <span>Upload Receipt</span>
                      </button>
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Add Expense Modal */}
      {showAddModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/60 backdrop-blur-sm p-4">
          <div className="w-full max-w-md rounded-3xl border border-slate-100 bg-white p-6 shadow-2xl space-y-6">
            <div className="flex justify-between items-center border-b border-slate-100 pb-3">
              <h3 className="text-base font-bold text-slate-900">Submit Field Expense Claim</h3>
              <button onClick={() => setShowAddModal(false)} className="text-slate-400 hover:text-slate-700 font-bold text-lg cursor-pointer">✕</button>
            </div>

            <form onSubmit={handleAddExpense} className="space-y-4">
              <div>
                <label className="block text-xs font-bold text-slate-700 mb-1">Expense Amount (₹)</label>
                <input
                  type="number"
                  required
                  min="1"
                  step="0.01"
                  value={amount}
                  onChange={(e) => setAmount(parseFloat(e.target.value) || 0)}
                  className="w-full rounded-xl border border-slate-200 bg-slate-50 px-3.5 py-2 text-xs font-bold text-slate-900 focus:border-blue-500 focus:outline-none"
                />
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-700 mb-1">Assigned Field Project</label>
                <select
                  value={projectId}
                  onChange={(e) => setProjectId(e.target.value)}
                  className="w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 text-xs font-medium text-slate-800 focus:border-blue-500 focus:outline-none"
                >
                  <option value="">General NGO Expenses (Unallocated)</option>
                  {projects.map((p) => (
                    <option key={p.id} value={p.id}>{p.project_name}</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-700 mb-1">Category</label>
                <select
                  value={category}
                  onChange={(e) => setCategory(e.target.value)}
                  className="w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 text-xs font-medium text-slate-800 focus:border-blue-500 focus:outline-none"
                >
                  <option value="Medical Supplies">Medical Supplies & Equipment</option>
                  <option value="Food & Nutrition">Food Rations & Meals</option>
                  <option value="Education Books">Educational Materials & Books</option>
                  <option value="Water Infrastructure">Water Drilling & Filtration</option>
                  <option value="Logistics & Fuel">Logistics & Field Transportation</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-700 mb-1">Description / Itemized Invoice Details</label>
                <textarea
                  rows={2}
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  placeholder="Describe purchased goods, supplier invoice details..."
                  className="w-full rounded-xl border border-slate-200 bg-slate-50 px-3.5 py-2 text-xs text-slate-900 focus:border-blue-500 focus:outline-none"
                />
              </div>

              <div className="flex space-x-3 pt-2">
                <button
                  type="button"
                  onClick={() => setShowAddModal(false)}
                  className="w-1/3 rounded-xl border border-slate-200 py-2.5 text-xs font-semibold text-slate-600 hover:bg-slate-50 cursor-pointer"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="w-2/3 rounded-xl bg-blue-600 py-2.5 text-xs font-bold text-white hover:bg-blue-700 disabled:opacity-50 transition-all cursor-pointer shadow-xs shadow-blue-600/20"
                >
                  {isSubmitting ? 'Submitting Claim...' : 'Submit Expense'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Upload Receipt Modal */}
      {uploadExpenseId && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/60 backdrop-blur-sm p-4">
          <div className="w-full max-w-md rounded-3xl border border-slate-100 bg-white p-6 shadow-2xl space-y-6">
            <div className="flex justify-between items-center border-b border-slate-100 pb-3">
              <h3 className="text-base font-bold text-slate-900">Upload Expense Receipt / Invoice File</h3>
              <button onClick={() => setUploadExpenseId(null)} className="text-slate-400 hover:text-slate-700 font-bold text-lg cursor-pointer">✕</button>
            </div>

            <form onSubmit={handleUploadReceipt} className="space-y-4">
              <div>
                <label className="block text-xs font-bold text-slate-700 mb-1.5">Select Receipt File (PDF / Image)</label>
                <input
                  type="file"
                  required
                  accept=".pdf,.png,.jpg,.jpeg"
                  onChange={(e) => setReceiptFile(e.target.files ? e.target.files[0] : null)}
                  className="w-full text-xs text-slate-600 file:mr-4 file:py-2 file:px-4 file:rounded-xl file:border-0 file:text-xs file:font-bold file:bg-blue-600 file:text-white hover:file:bg-blue-700 cursor-pointer"
                />
              </div>

              <div className="flex space-x-3 pt-2">
                <button
                  type="button"
                  onClick={() => setUploadExpenseId(null)}
                  className="w-1/3 rounded-xl border border-slate-200 py-2.5 text-xs font-semibold text-slate-600 hover:bg-slate-50 cursor-pointer"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isUploading || !receiptFile}
                  className="w-2/3 rounded-xl bg-blue-600 py-2.5 text-xs font-bold text-white hover:bg-blue-700 disabled:opacity-50 transition-all cursor-pointer shadow-xs shadow-blue-600/20"
                >
                  {isUploading ? 'Hashing with SHA-256...' : 'Upload & Compute Hash'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

    </div>
  );
}
