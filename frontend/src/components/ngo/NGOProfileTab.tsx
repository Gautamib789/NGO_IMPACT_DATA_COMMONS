'use client';

import React, { useState, useEffect } from 'react';
import { useAuth } from '@/context/AuthContext';
import { Building2, Save, Globe, MapPin, CheckCircle2, Shield } from 'lucide-react';
import { NGOProfile } from './types';

interface NGOProfileTabProps {
  profile: NGOProfile | null;
  onRefresh: () => void;
}

export default function NGOProfileTab({ profile, onRefresh }: NGOProfileTabProps) {
  const { apiFetch } = useAuth();
  const [orgName, setOrgName] = useState(profile?.org_name || '');
  const [registrationNumber, setRegistrationNumber] = useState(profile?.registration_number || '');
  const [taxId, setTaxId] = useState(profile?.tax_id || '');
  const [category, setCategory] = useState(profile?.category || 'Healthcare');
  const [missionStatement, setMissionStatement] = useState(profile?.mission_statement || '');
  const [website, setWebsite] = useState(profile?.website || '');
  const [address, setAddress] = useState(profile?.address || '');

  const [isSaving, setIsSaving] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  useEffect(() => {
    if (profile) {
      if (profile.org_name) setOrgName(profile.org_name);
      if (profile.registration_number) setRegistrationNumber(profile.registration_number);
      if (profile.tax_id) setTaxId(profile.tax_id);
      if (profile.category) setCategory(profile.category);
      if (profile.mission_statement) setMissionStatement(profile.mission_statement);
      if (profile.website) setWebsite(profile.website);
      if (profile.address) setAddress(profile.address);
    }
  }, [profile]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      setIsSaving(true);
      setErrorMsg(null);
      setSuccessMsg(null);

      const payload = {
        org_name: orgName,
        registration_number: registrationNumber,
        tax_id: taxId,
        category,
        mission_statement: missionStatement,
        website,
        address,
      };

      await apiFetch('/api/ngos/profile', {
        method: 'PUT',
        body: JSON.stringify(payload),
      });

      setSuccessMsg('NGO organization profile updated successfully.');
      onRefresh();
    } catch (err: any) {
      setErrorMsg(err.message || 'Failed to update NGO profile.');
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div className="space-y-6">

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

      <div className="bg-white rounded-3xl border border-slate-200 p-6 md:p-8 shadow-card space-y-6">
        <div className="border-b border-slate-100 pb-4">
          <h2 className="text-xl font-bold text-slate-900 flex items-center gap-2">
            <Building2 className="h-5 w-5 text-blue-600" />
            Official Organization Dossier
          </h2>
          <p className="text-xs text-slate-500">Update official registration numbers, mission details, and legal address.</p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-5">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-bold text-slate-700 mb-1">Organization Name</label>
              <input
                type="text"
                required
                value={orgName}
                onChange={(e) => setOrgName(e.target.value)}
                className="w-full rounded-xl border border-slate-200 bg-slate-50 px-3.5 py-2.5 text-xs text-slate-900 focus:border-blue-500 focus:bg-white focus:outline-none"
              />
            </div>

            <div>
              <label className="block text-xs font-bold text-slate-700 mb-1">Category / Sector</label>
              <select
                value={category}
                onChange={(e) => setCategory(e.target.value)}
                className="w-full rounded-xl border border-slate-200 bg-slate-50 px-3 py-2.5 text-xs font-medium text-slate-800 focus:border-blue-500 focus:outline-none"
              >
                <option value="Healthcare">Healthcare & Medical Relief</option>
                <option value="Education">Education & Rural Literacy</option>
                <option value="Environment">Environmental Sustainability</option>
                <option value="Clean Water">Clean Water & Well Infrastructure</option>
                <option value="Livelihood">Livelihood & Economic Development</option>
              </select>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-bold text-slate-700 mb-1">Government Registration Number</label>
              <input
                type="text"
                required
                value={registrationNumber}
                onChange={(e) => setRegistrationNumber(e.target.value)}
                className="w-full rounded-xl border border-slate-200 bg-slate-50 px-3.5 py-2.5 text-xs font-mono text-slate-900 focus:border-blue-500 focus:bg-white focus:outline-none"
              />
            </div>

            <div>
              <label className="block text-xs font-bold text-slate-700 mb-1">Tax ID / PAN Number</label>
              <input
                type="text"
                required
                value={taxId}
                onChange={(e) => setTaxId(e.target.value)}
                className="w-full rounded-xl border border-slate-200 bg-slate-50 px-3.5 py-2.5 text-xs font-mono text-slate-900 focus:border-blue-500 focus:bg-white focus:outline-none"
              />
            </div>
          </div>

          <div>
            <label className="block text-xs font-bold text-slate-700 mb-1">Official Mission Statement</label>
            <textarea
              rows={3}
              value={missionStatement}
              onChange={(e) => setMissionStatement(e.target.value)}
              placeholder="Describe your organization's core charter and public impact goals..."
              className="w-full rounded-xl border border-slate-200 bg-slate-50 px-3.5 py-2.5 text-xs text-slate-900 focus:border-blue-500 focus:bg-white focus:outline-none"
            />
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-bold text-slate-700 mb-1">Official Website URL</label>
              <input
                type="url"
                value={website}
                onChange={(e) => setWebsite(e.target.value)}
                placeholder="https://example.org"
                className="w-full rounded-xl border border-slate-200 bg-slate-50 px-3.5 py-2.5 text-xs text-slate-900 focus:border-blue-500 focus:bg-white focus:outline-none"
              />
            </div>

            <div>
              <label className="block text-xs font-bold text-slate-700 mb-1">Physical Registered Address</label>
              <input
                type="text"
                value={address}
                onChange={(e) => setAddress(e.target.value)}
                placeholder="e.g. 100 Civic Centre, Mysuru, Karnataka"
                className="w-full rounded-xl border border-slate-200 bg-slate-50 px-3.5 py-2.5 text-xs text-slate-900 focus:border-blue-500 focus:bg-white focus:outline-none"
              />
            </div>
          </div>

          <div className="pt-3">
            <button
              type="submit"
              disabled={isSaving}
              className="inline-flex items-center space-x-2 rounded-xl bg-blue-600 px-6 py-3 text-xs font-bold text-white hover:bg-blue-700 disabled:opacity-50 transition-all cursor-pointer shadow-xs shadow-blue-600/20"
            >
              <Save className="h-4 w-4" />
              <span>{isSaving ? 'Saving Changes...' : 'Save Organization Profile'}</span>
            </button>
          </div>
        </form>
      </div>

    </div>
  );
}
