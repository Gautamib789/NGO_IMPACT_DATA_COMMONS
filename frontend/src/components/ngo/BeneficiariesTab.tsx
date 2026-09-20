'use client';

import React, { useState, useEffect } from 'react';
import { useAuth } from '@/context/AuthContext';
import { Users, UserPlus, Shield, Trash2, Filter, Lock, Tag, MapPin } from 'lucide-react';
import { Beneficiary, Project } from './types';

interface BeneficiariesTabProps {
  projects: Project[];
  onRefresh: () => void;
}

export default function BeneficiariesTab({ projects, onRefresh }: BeneficiariesTabProps) {
  const { apiFetch } = useAuth();
  const [beneficiaries, setBeneficiaries] = useState<Beneficiary[]>([]);
  const [selectedProjectId, setSelectedProjectId] = useState<string>('ALL');
  const [loading, setLoading] = useState(true);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  // Add Beneficiary state
  const [showModal, setShowModal] = useState(false);
  const [alias, setAlias] = useState('');
  const [projectId, setProjectId] = useState<string>('');
  const [ageGroup, setAgeGroup] = useState('Adults');
  const [gender, setGender] = useState('Female');
  const [location, setLocation] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const fetchBeneficiaries = async () => {
    try {
      setLoading(true);
      setErrorMsg(null);
      let url = '/api/ngo/beneficiaries';
      if (selectedProjectId !== 'ALL') {
        url += `?project_id=${selectedProjectId}`;
      }
      const data = await apiFetch(url);
      setBeneficiaries(data);
    } catch (err: any) {
      setErrorMsg(err.message || 'Failed to load beneficiaries.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchBeneficiaries();
  }, [selectedProjectId]);

  const handleAddBeneficiary = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      setIsSubmitting(true);
      setErrorMsg(null);
      setSuccessMsg(null);

      const payload = {
        name_or_alias: alias,
        project_id: projectId ? parseInt(projectId) : undefined,
        age_group: ageGroup,
        gender,
        location,
      };

      const newB = await apiFetch('/api/ngo/beneficiaries', {
        method: 'POST',
        body: JSON.stringify(payload),
      });

      setSuccessMsg(`Beneficiary registered with masked code ${newB.beneficiary_code}.`);
      setAlias('');
      setShowModal(false);
      fetchBeneficiaries();
      onRefresh();
    } catch (err: any) {
      setErrorMsg(err.message || 'Failed to register beneficiary.');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleDelete = async (id: number, code: string) => {
    if (!confirm(`Are you sure you want to remove beneficiary record '${code}'?`)) return;

    try {
      setErrorMsg(null);
      setSuccessMsg(null);
      await apiFetch(`/api/ngo/beneficiaries/${id}`, { method: 'DELETE' });
      setSuccessMsg(`Beneficiary record '${code}' removed successfully.`);
      fetchBeneficiaries();
      onRefresh();
    } catch (err: any) {
      setErrorMsg(err.message || 'Failed to delete beneficiary.');
    }
  };

  return (
    <div className="space-y-6">
      
      {/* Privacy Protection Mandatory Banner */}
      <div className="rounded-2xl border border-indigo-200 bg-indigo-50/70 p-5 text-xs text-indigo-900 space-y-1 shadow-xs">
        <div className="flex items-start space-x-2.5">
          <Shield className="h-5 w-5 text-indigo-600 flex-shrink-0 mt-0.5" />
          <div className="space-y-1">
            <h4 className="font-extrabold text-indigo-950">Beneficiary Data Privacy & Masking Safeguards</h4>
            <p className="leading-relaxed text-indigo-800">
              To protect beneficiary dignity and comply with data privacy regulations, national identity numbers (such as Aadhaar or SSN) are <strong>never collected or stored</strong>. Every beneficiary is assigned an auto-generated masked cryptographic code (e.g. <code>BEN-2026-X100</code>). Pseudonyms or community alias labels are used across all public transparency feeds.
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

      {/* Top Controls & Filter Bar */}
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
            setAlias('');
            setProjectId(projects.length > 0 ? String(projects[0].id) : '');
            setLocation('');
            setShowModal(true);
          }}
          className="inline-flex items-center space-x-2 rounded-xl bg-blue-600 px-5 py-2.5 text-xs font-bold text-white hover:bg-blue-700 transition-all shadow-xs shadow-blue-600/20 cursor-pointer"
        >
          <UserPlus className="h-4 w-4" />
          <span>Register Beneficiary</span>
        </button>
      </div>

      {/* Beneficiary List */}
      <div className="bg-white rounded-3xl border border-slate-200 p-6 md:p-8 shadow-card space-y-6">
        <div className="border-b border-slate-100 pb-4 flex justify-between items-center">
          <div>
            <h3 className="text-base font-bold text-slate-900">Registered Beneficiaries ({beneficiaries.length})</h3>
            <p className="text-xs text-slate-500">Masked records with privacy protection.</p>
          </div>
        </div>

        {loading ? (
          <div className="py-12 text-center text-slate-500">
            <div className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-blue-600 border-t-transparent mb-3"></div>
            <p className="text-xs font-semibold">Loading beneficiary directory...</p>
          </div>
        ) : beneficiaries.length === 0 ? (
          <div className="py-12 text-center text-slate-400">
            <Users className="mx-auto h-10 w-10 text-slate-300 mb-2" />
            <p className="text-xs font-semibold">No beneficiaries registered for this selection.</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {beneficiaries.map((b) => (
              <div key={b.id} className="bg-slate-50 p-4 rounded-2xl border border-slate-200/80 space-y-3 flex flex-col justify-between">
                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="font-mono text-xs font-extrabold text-blue-700 bg-blue-50 px-2.5 py-0.5 rounded-full border border-blue-200">
                      {b.beneficiary_code}
                    </span>
                    <button
                      onClick={() => handleDelete(b.id, b.beneficiary_code)}
                      className="text-slate-400 hover:text-rose-600 p-1 transition-colors cursor-pointer"
                      title="Remove Beneficiary"
                    >
                      <Trash2 className="h-3.5 w-3.5" />
                    </button>
                  </div>

                  <h4 className="font-bold text-slate-900 text-sm">{b.name_or_alias}</h4>
                  
                  {b.project_name && (
                    <p className="text-[11px] text-slate-500 flex items-center gap-1 font-medium">
                      <Tag className="h-3 w-3 text-slate-400" /> {b.project_name}
                    </p>
                  )}

                  <div className="flex flex-wrap gap-2 text-[10px] text-slate-600 pt-1">
                    {b.age_group && <span className="bg-white px-2 py-0.5 rounded-md border border-slate-200">{b.age_group}</span>}
                    {b.gender && <span className="bg-white px-2 py-0.5 rounded-md border border-slate-200">{b.gender}</span>}
                    {b.location && <span className="bg-white px-2 py-0.5 rounded-md border border-slate-200 flex items-center gap-0.5"><MapPin className="h-2.5 w-2.5 text-slate-400" /> {b.location}</span>}
                  </div>
                </div>

                <div className="text-[10px] text-slate-400 font-mono pt-2 border-t border-slate-200/60">
                  Registered: {new Date(b.created_at).toLocaleDateString()}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Add Beneficiary Modal */}
      {showModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/60 backdrop-blur-sm p-4">
          <div className="w-full max-w-md rounded-3xl border border-slate-100 bg-white p-6 shadow-2xl space-y-6">
            <div className="flex justify-between items-center border-b border-slate-100 pb-3">
              <h3 className="text-base font-bold text-slate-900">Register Beneficiary Record</h3>
              <button onClick={() => setShowModal(false)} className="text-slate-400 hover:text-slate-700 font-bold text-lg cursor-pointer">✕</button>
            </div>

            <form onSubmit={handleAddBeneficiary} className="space-y-4">
              <div>
                <label className="block text-xs font-bold text-slate-700 mb-1">Beneficiary Name or Alias Pseudonym</label>
                <input
                  type="text"
                  required
                  value={alias}
                  onChange={(e) => setAlias(e.target.value)}
                  placeholder="e.g. Village Cooperative Beneficiary #12"
                  className="w-full rounded-xl border border-slate-200 bg-slate-50 px-3.5 py-2 text-xs text-slate-900 focus:border-blue-500 focus:outline-none"
                />
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-700 mb-1">Assigned Field Project</label>
                <select
                  value={projectId}
                  onChange={(e) => setProjectId(e.target.value)}
                  className="w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 text-xs font-medium text-slate-800 focus:border-blue-500 focus:outline-none"
                >
                  <option value="">General NGO Community (No Project)</option>
                  {projects.map((p) => (
                    <option key={p.id} value={p.id}>{p.project_name}</option>
                  ))}
                </select>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-bold text-slate-700 mb-1">Age Group</label>
                  <select
                    value={ageGroup}
                    onChange={(e) => setAgeGroup(e.target.value)}
                    className="w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 text-xs font-medium text-slate-800 focus:border-blue-500 focus:outline-none"
                  >
                    <option value="Children">Children (&lt; 18 yrs)</option>
                    <option value="Youth">Youth (18 - 25 yrs)</option>
                    <option value="Adults">Adults (26 - 60 yrs)</option>
                    <option value="Seniors">Seniors (&gt; 60 yrs)</option>
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-bold text-slate-700 mb-1">Gender</label>
                  <select
                    value={gender}
                    onChange={(e) => setGender(e.target.value)}
                    className="w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 text-xs font-medium text-slate-800 focus:border-blue-500 focus:outline-none"
                  >
                    <option value="Female">Female</option>
                    <option value="Male">Male</option>
                    <option value="Other">Other / Non-Binary</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-700 mb-1">Location / Village</label>
                <input
                  type="text"
                  value={location}
                  onChange={(e) => setLocation(e.target.value)}
                  placeholder="e.g. Mandya District, Karnataka"
                  className="w-full rounded-xl border border-slate-200 bg-slate-50 px-3.5 py-2 text-xs text-slate-900 focus:border-blue-500 focus:outline-none"
                />
              </div>

              <div className="flex space-x-3 pt-2">
                <button
                  type="button"
                  onClick={() => setShowModal(false)}
                  className="w-1/3 rounded-xl border border-slate-200 py-2.5 text-xs font-semibold text-slate-600 hover:bg-slate-50 cursor-pointer"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isSubmitting}
                  className="w-2/3 rounded-xl bg-blue-600 py-2.5 text-xs font-bold text-white hover:bg-blue-700 disabled:opacity-50 transition-all cursor-pointer shadow-xs shadow-blue-600/20"
                >
                  {isSubmitting ? 'Registering...' : 'Register Beneficiary'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

    </div>
  );
}
