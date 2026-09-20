'use client';

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/context/AuthContext';
import { FolderPlus, MapPin, Edit3, Trash2, CheckCircle2, TrendingUp, Users, DollarSign, PlusCircle, AlertCircle, Eye, ShieldCheck, ShieldAlert, ShieldX } from 'lucide-react';
import { Project, mapProjectResponse } from './types';

import { getApiErrorMessage } from '@/utils/errorUtils';

interface ProjectsTabProps {
  onRefresh: () => void;
  onSelectProject?: (projectId: number) => void;
}

export default function ProjectsTab({ onRefresh, onSelectProject }: ProjectsTabProps) {
  const router = useRouter();
  const { apiFetch } = useAuth();
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  // Form State for Create / Edit
  const [showModal, setShowModal] = useState(false);
  const [editingProject, setEditingProject] = useState<Project | null>(null);
  const [name, setName] = useState('');
  const [category, setCategory] = useState('Healthcare');
  const [description, setDescription] = useState('');
  const [budget, setBudget] = useState<number>(50000);
  const [location, setLocation] = useState('');
  const [latitude, setLatitude] = useState<string>('');
  const [longitude, setLongitude] = useState<string>('');
  const [startDate, setStartDate] = useState<string>('');
  const [endDate, setEndDate] = useState<string>('');
  const [targetBeneficiaries, setTargetBeneficiaries] = useState<number>(500);
  const [outcomes, setOutcomes] = useState('');
  const [status, setStatus] = useState<'ACTIVE' | 'COMPLETED' | 'SUSPENDED'>('ACTIVE');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const fetchProjects = async () => {
    try {
      setLoading(true);
      setErrorMsg(null);
      const data = await apiFetch('/api/ngo/projects');
      const mappedProjects = (data || []).map(mapProjectResponse);
      setProjects(mappedProjects);
    } catch (err: any) {
      setErrorMsg(getApiErrorMessage(err));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchProjects();
  }, []);

  const openCreateModal = () => {
    setEditingProject(null);
    setName('');
    setCategory('Healthcare');
    setDescription('');
    setBudget(50000);
    setLocation('Bengaluru, Karnataka');
    setLatitude('12.9716');
    setLongitude('77.5946');
    setStartDate('2026-01-01');
    setEndDate('2026-12-31');
    setTargetBeneficiaries(500);
    setOutcomes('');
    setStatus('ACTIVE');
    setShowModal(true);
  };

  const openEditModal = (p: Project) => {
    setEditingProject(p);
    setName(p.project_name);
    setCategory(p.category);
    setDescription(p.description || '');
    setBudget(p.budget ?? p.total_budget ?? 0);
    setLocation(p.location || '');
    setLatitude(p.latitude ? String(p.latitude) : '');
    setLongitude(p.longitude ? String(p.longitude) : '');
    setStartDate(p.start_date ? p.start_date.split('T')[0] : '');
    setEndDate(p.end_date ? p.end_date.split('T')[0] : '');
    setTargetBeneficiaries(p.target_beneficiaries ? Number(p.target_beneficiaries) : p.beneficiary_count || 0);
    setOutcomes(p.outcomes || '');
    setStatus((p.status as any) === 'COMPLETED' ? 'COMPLETED' : (p.status as any) === 'SUSPENDED' ? 'SUSPENDED' : 'ACTIVE');
    setShowModal(true);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim()) {
      setErrorMsg('Project name is required.');
      return;
    }
    if (budget <= 0) {
      setErrorMsg('Project budget must be greater than zero.');
      return;
    }
    if (startDate && endDate && new Date(endDate) < new Date(startDate)) {
      setErrorMsg('End date cannot be before start date.');
      return;
    }

    try {
      setIsSubmitting(true);
      setErrorMsg(null);
      setSuccessMsg(null);

      const payload = {
        project_name: name,
        category,
        description,
        budget: Number(budget),
        total_budget: Number(budget),
        location,
        latitude: latitude ? parseFloat(latitude) : undefined,
        longitude: longitude ? parseFloat(longitude) : undefined,
        start_date: startDate || undefined,
        end_date: endDate || undefined,
        target_beneficiaries: Number(targetBeneficiaries),
        number_of_beneficiaries: Number(targetBeneficiaries),
        outcomes,
        status,
      };

      if (editingProject) {
        await apiFetch(`/api/ngo/projects/${editingProject.id}`, {
          method: 'PUT',
          body: JSON.stringify(payload),
        });
        setSuccessMsg(`Project '${name}' updated successfully.`);
      } else {
        await apiFetch('/api/ngo/projects', {
          method: 'POST',
          body: JSON.stringify(payload),
        });
        setSuccessMsg(`New project '${name}' created successfully.`);
      }

      setShowModal(false);
      fetchProjects();
      onRefresh();
    } catch (err: any) {
      setErrorMsg(getApiErrorMessage(err));
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleDelete = async (id: number, pName: string) => {
    if (!confirm(`Are you sure you want to delete project '${pName}'? This action is irreversible.`)) return;

    try {
      setErrorMsg(null);
      setSuccessMsg(null);
      await apiFetch(`/api/ngo/projects/${id}`, { method: 'DELETE' });
      setSuccessMsg(`Project '${pName}' deleted successfully.`);
      fetchProjects();
      onRefresh();
    } catch (err: any) {
      setErrorMsg(getApiErrorMessage(err));
    }
  };

  if (loading) {
    return (
      <div className="py-12 text-center text-slate-500 bg-white rounded-3xl border border-slate-200">
        <div className="inline-block h-8 w-8 animate-spin rounded-full border-4 border-blue-600 border-t-transparent mb-3"></div>
        <p className="text-xs font-semibold">Loading projects registry...</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      
      {/* Top Action Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 bg-white p-6 rounded-3xl border border-slate-200 shadow-card">
        <div>
          <h2 className="text-xl font-bold text-slate-900">Project Management Portfolio ({projects.length})</h2>
          <p className="text-xs text-slate-500">Track active field projects, budgets, GPS locations, and fund utilization.</p>
        </div>

        <button
          onClick={openCreateModal}
          className="inline-flex items-center space-x-2 rounded-xl bg-blue-600 px-5 py-2.5 text-xs font-bold text-white hover:bg-blue-700 transition-all shadow-xs shadow-blue-600/20 cursor-pointer"
        >
          <PlusCircle className="h-4 w-4" />
          <span>Create New Project</span>
        </button>
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

      {/* Projects Grid */}
      {projects.length === 0 ? (
        <div className="py-16 text-center text-slate-400 bg-white rounded-3xl border border-slate-200">
          <FolderPlus className="mx-auto h-12 w-12 text-slate-300 mb-3" />
          <p className="text-sm font-bold text-slate-700">No Projects Found</p>
          <p className="text-xs text-slate-500 mt-1 mb-4">Create your first field project to begin tracking beneficiaries and expenses.</p>
          <button
            onClick={openCreateModal}
            className="inline-flex items-center space-x-2 rounded-xl bg-blue-600 px-4 py-2 text-xs font-bold text-white hover:bg-blue-700 cursor-pointer"
          >
            <PlusCircle className="h-4 w-4" />
            <span>Add Project</span>
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {projects.map((p) => (
            <div key={p.id} className="bg-white rounded-3xl border border-slate-200 p-6 shadow-card space-y-5 flex flex-col justify-between">
              
              <div className="space-y-3">
                <div className="flex items-start justify-between gap-2">
                  <div>
                    <span className="text-[10px] font-bold uppercase tracking-wider text-blue-600 bg-blue-50 px-2.5 py-0.5 rounded-full border border-blue-200">
                      {p.category}
                    </span>
                    <h3 className="text-lg font-bold text-slate-900 mt-1">{p.project_name}</h3>
                  </div>

                  <span className={`px-2.5 py-1 rounded-full text-[10px] font-bold uppercase border ${
                    p.status === 'ACTIVE' ? 'bg-emerald-50 text-emerald-700 border-emerald-200' :
                    p.status === 'COMPLETED' ? 'bg-blue-50 text-blue-700 border-blue-200' :
                    'bg-rose-50 text-rose-700 border-rose-200'
                  }`}>
                    {p.status}
                  </span>
                </div>

                <p className="text-xs text-slate-600 line-clamp-2">{p.description || 'No description provided.'}</p>

                {p.location && (
                  <div className="flex items-center space-x-1.5 text-xs text-slate-500">
                    <MapPin className="h-3.5 w-3.5 text-slate-400" />
                    <span>{p.location}</span>
                    {p.latitude && p.longitude && (
                      <span className="text-[10px] font-mono text-slate-400">({p.latitude.toFixed(4)}, {p.longitude.toFixed(4)})</span>
                    )}
                  </div>
                )}
              </div>

              {/* Fund Metrics & Utilization */}
              <div className="bg-slate-50 p-4 rounded-2xl border border-slate-200/80 space-y-3">
                <div className="grid grid-cols-3 gap-2 text-center text-xs">
                  <div>
                    <span className="text-[10px] text-slate-400 uppercase font-bold block">Budget</span>
                    <span className="font-extrabold text-slate-900">
                      {(p.budget ?? p.total_budget) !== undefined ? `₹${(p.budget ?? p.total_budget)!.toLocaleString('en-IN')}` : 'Unavailable'}
                    </span>
                  </div>
                  <div>
                    <span className="text-[10px] text-slate-400 uppercase font-bold block">Claimed</span>
                    <span className="font-extrabold text-blue-700">
                      ₹{(p.total_expenses_claimed ?? p.amount_spent ?? 0).toLocaleString('en-IN')}
                    </span>
                  </div>
                  <div>
                    <span className="text-[10px] text-slate-400 uppercase font-bold block">Utilization</span>
                    <span className="font-extrabold text-emerald-600">{(p.fund_utilization_ratio ?? 0)}%</span>
                  </div>
                </div>

                {/* Progress bar */}
                <div className="w-full bg-slate-200 rounded-full h-2 overflow-hidden">
                  <div
                    className="bg-emerald-500 h-2 rounded-full transition-all duration-500"
                    style={{ width: `${Math.min(100, p.fund_utilization_ratio ?? 0)}%` }}
                  ></div>
                </div>
              </div>

              {/* Card Footer Actions */}
              <div className="flex items-center justify-between pt-3 border-t border-slate-100 text-xs">
                <div className="flex items-center space-x-4 text-slate-500 font-medium">
                  <span className="flex items-center gap-1"><Users className="h-3.5 w-3.5 text-slate-400" /> {p.beneficiary_count} Beneficiaries</span>
                </div>

                <div className="flex items-center space-x-2">
                  <button
                    onClick={() => onSelectProject ? onSelectProject(p.id) : router.push(`/ngo/projects/${p.id}`)}
                    className="inline-flex items-center space-x-1.5 rounded-xl bg-blue-600 text-white px-3.5 py-1.5 text-xs font-bold hover:bg-blue-700 transition-all cursor-pointer shadow-xs shadow-blue-600/20"
                    title="View Project Details, Evidence & Forensic Analysis"
                  >
                    <Eye className="h-3.5 w-3.5" />
                    <span>View Details</span>
                  </button>

                  <button
                    onClick={() => openEditModal(p)}
                    className="p-2 text-slate-500 hover:text-blue-600 hover:bg-slate-100 rounded-xl transition-colors cursor-pointer"
                    title="Edit Project"
                  >
                    <Edit3 className="h-4 w-4" />
                  </button>
                  <button
                    onClick={() => handleDelete(p.id, p.project_name)}
                    className="p-2 text-slate-500 hover:text-rose-600 hover:bg-slate-100 rounded-xl transition-colors cursor-pointer"
                    title="Delete Project"
                  >
                    <Trash2 className="h-4 w-4" />
                  </button>
                </div>
              </div>

            </div>
          ))}
        </div>
      )}

      {/* Modal Form for Create / Edit */}
      {showModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/60 backdrop-blur-sm p-4 overflow-y-auto">
          <div className="w-full max-w-xl rounded-3xl border border-slate-100 bg-white p-6 sm:p-8 shadow-2xl space-y-6 my-8">
            <div className="flex justify-between items-center border-b border-slate-100 pb-4">
              <h3 className="text-lg font-bold text-slate-900">
                {editingProject ? 'Edit Project Details' : 'Create New Field Project'}
              </h3>
              <button onClick={() => setShowModal(false)} className="text-slate-400 hover:text-slate-700 font-bold text-lg cursor-pointer">✕</button>
            </div>

            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <label className="block text-xs font-bold text-slate-700 mb-1">Project Name</label>
                <input
                  type="text"
                  required
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="e.g. Rural Mobile Health Clinic Initiative"
                  className="w-full rounded-xl border border-slate-200 bg-slate-50 px-3.5 py-2 text-xs text-slate-900 focus:border-blue-500 focus:bg-white focus:outline-none"
                />
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-bold text-slate-700 mb-1">Category</label>
                  <select
                    value={category}
                    onChange={(e) => setCategory(e.target.value)}
                    className="w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 text-xs font-medium text-slate-800 focus:border-blue-500 focus:outline-none"
                  >
                    <option value="Healthcare">Healthcare & Medical</option>
                    <option value="Education">Education & Literacy</option>
                    <option value="Environment">Environment & Sanitation</option>
                    <option value="Clean Water">Clean Water & Wells</option>
                    <option value="Livelihood">Livelihood & Women Empowerment</option>
                  </select>
                </div>

                <div>
                  <label className="block text-xs font-bold text-slate-700 mb-1">Project Budget (₹)</label>
                  <input
                    type="number"
                    required
                    min="1"
                    value={budget}
                    onChange={(e) => setBudget(parseFloat(e.target.value) || 0)}
                    className="w-full rounded-xl border border-slate-200 bg-slate-50 px-3.5 py-2 text-xs font-bold text-slate-900 focus:border-blue-500 focus:outline-none"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-700 mb-1">Description & Scope</label>
                <textarea
                  rows={2}
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  placeholder="Outline key project objectives and implementation strategy..."
                  className="w-full rounded-xl border border-slate-200 bg-slate-50 px-3.5 py-2 text-xs text-slate-900 focus:border-blue-500 focus:outline-none"
                />
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                <div>
                  <label className="block text-xs font-bold text-slate-700 mb-1">Location / District</label>
                  <input
                    type="text"
                    value={location}
                    onChange={(e) => setLocation(e.target.value)}
                    placeholder="e.g. Mysuru, Karnataka"
                    className="w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 text-xs text-slate-900 focus:border-blue-500 focus:outline-none"
                  />
                </div>
                <div>
                  <label className="block text-xs font-bold text-slate-700 mb-1">Latitude (GPS)</label>
                  <input
                    type="number"
                    step="any"
                    value={latitude}
                    onChange={(e) => setLatitude(e.target.value)}
                    placeholder="e.g. 12.2958"
                    className="w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 text-xs text-slate-900 focus:border-blue-500 focus:outline-none font-mono"
                  />
                </div>
                <div>
                  <label className="block text-xs font-bold text-slate-700 mb-1">Longitude (GPS)</label>
                  <input
                    type="number"
                    step="any"
                    value={longitude}
                    onChange={(e) => setLongitude(e.target.value)}
                    placeholder="e.g. 76.6394"
                    className="w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 text-xs text-slate-900 focus:border-blue-500 focus:outline-none font-mono"
                  />
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-bold text-slate-700 mb-1">Start Date</label>
                  <input
                    type="date"
                    value={startDate}
                    onChange={(e) => setStartDate(e.target.value)}
                    className="w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 text-xs text-slate-900 focus:border-blue-500 focus:outline-none"
                  />
                </div>
                <div>
                  <label className="block text-xs font-bold text-slate-700 mb-1">End Date</label>
                  <input
                    type="date"
                    value={endDate}
                    onChange={(e) => setEndDate(e.target.value)}
                    className="w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 text-xs text-slate-900 focus:border-blue-500 focus:outline-none"
                  />
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-bold text-slate-700 mb-1">Target Beneficiaries</label>
                  <input
                    type="number"
                    value={targetBeneficiaries}
                    onChange={(e) => setTargetBeneficiaries(parseInt(e.target.value) || 0)}
                    className="w-full rounded-xl border border-slate-200 bg-slate-50 px-3.5 py-2 text-xs text-slate-900 focus:border-blue-500 focus:outline-none"
                  />
                </div>

                <div>
                  <label className="block text-xs font-bold text-slate-700 mb-1">Status</label>
                  <select
                    value={status}
                    onChange={(e: any) => setStatus(e.target.value)}
                    className="w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 text-xs font-medium text-slate-800 focus:border-blue-500 focus:outline-none"
                  >
                    <option value="ACTIVE">ACTIVE</option>
                    <option value="COMPLETED">COMPLETED</option>
                    <option value="SUSPENDED">SUSPENDED</option>
                  </select>
                </div>
              </div>

              <div className="flex space-x-3 pt-4">
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
                  {isSubmitting ? 'Saving Project...' : editingProject ? 'Update Project' : 'Create Project'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

    </div>
  );
}
