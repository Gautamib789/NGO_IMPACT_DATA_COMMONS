'use client';

import React, { useState, useEffect, Suspense } from 'react';
import Link from 'next/link';
import { useRouter, useSearchParams } from 'next/navigation';
import { useAuth } from '@/context/AuthContext';
import { 
  Search, 
  CheckCircle2, 
  Building2, 
  HeartHandshake, 
  FileCheck, 
  ShieldCheck, 
  MapPin, 
  Filter, 
  RotateCcw,
  ArrowRight,
  Lock,
  ChevronLeft,
  ChevronRight
} from 'lucide-react';

interface NGO {
  id: number;
  org_name: string;
  registration_number: string;
  tax_id: string;
  category: string;
  mission_statement: string;
  website: string;
  address: string;
  status: string;
  doc_completeness_score: number;
  transparency_score: number;
  total_expenses: number;
  total_donations_received: number;
  beneficiary_count: number;
}

function ExploreDirectoryContent() {
  const { user, apiFetch } = useAuth();
  const router = useRouter();
  const searchParams = useSearchParams();

  // URL state synchronization
  const [search, setSearch] = useState(searchParams.get('search') || '');
  const [cause, setCause] = useState(searchParams.get('cause') || 'All causes');
  const [stateFilter, setStateFilter] = useState(searchParams.get('state') || 'All states');
  const [sort, setSort] = useState(searchParams.get('sort') || 'Recently registered');
  const [page, setPage] = useState(parseInt(searchParams.get('page') || '1', 10));

  // Data & UI states
  const [ngos, setNgos] = useState<NGO[]>([]);
  const [totalCount, setTotalCount] = useState<number>(0);
  const [totalPages, setTotalPages] = useState<number>(1);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Donation Modal State
  const [selectedNgo, setSelectedNgo] = useState<NGO | null>(null);
  const [donationAmount, setDonationAmount] = useState<number>(50);
  const [customAmount, setCustomAmount] = useState<string>('');
  const [donorMsg, setDonorMsg] = useState<string>('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [donationSuccess, setDonationSuccess] = useState<any>(null);

  const causesList = [
    'All causes',
    'Medical Support',
    'Free Education',
    'Environment & Conservation',
    'Clean Water & Sanitation',
    'Child Welfare',
    'Women Empowerment',
    'Old Age Support',
    'Disaster Relief',
    'Community Development',
    'Healthcare & Relief',
    'Other'
  ];

  const statesList = [
    'All states',
    'Karnataka',
    'Delhi',
    'Maharashtra',
    'Tamil Nadu',
    'California',
    'Texas',
    'Uttar Pradesh',
    'Telangana',
    'West Bengal'
  ];

  const sortOptions = [
    { label: 'Recently registered', value: 'recent' },
    { label: 'Name A-Z', value: 'name_asc' },
    { label: 'Name Z-A', value: 'name_desc' },
    { label: 'Highest transparency score', value: 'transparency_high' },
    { label: 'Lowest transparency score', value: 'transparency_low' }
  ];

  // Helper to extract clean initials from organization name
  const getInitials = (name: string) => {
    if (!name) return 'NGO';
    const words = name.trim().split(/\s+/);
    if (words.length >= 2) {
      return (words[0][0] + words[1][0]).toUpperCase();
    }
    return name.slice(0, 2).toUpperCase();
  };

  // Sync state changes to URL
  const updateUrlParams = (newParams: Record<string, string | number>) => {
    const params = new URLSearchParams(searchParams.toString());
    Object.entries(newParams).forEach(([key, value]) => {
      if (value && value !== 'All causes' && value !== 'All states' && value !== 'Recently registered' && value !== 'recent' && value !== 1 && value !== '1') {
        params.set(key, String(value));
      } else {
        params.delete(key);
      }
    });
    router.push(`/explore?${params.toString()}`);
  };

  // Fetch NGO dataset from FastAPI database backend
  const fetchNgos = async () => {
    try {
      setLoading(true);
      setError(null);

      const params = new URLSearchParams();
      params.set('meta', 'true');
      params.set('page', String(page));
      params.set('limit', '9');

      if (search.trim()) params.set('search', search.trim());
      if (cause && cause !== 'All causes') params.set('cause', cause);
      if (stateFilter && stateFilter !== 'All states') params.set('state', stateFilter);
      if (sort) params.set('sort', sort);

      const data = await apiFetch(`/api/public/ngos?${params.toString()}`);

      if (data && Array.isArray(data.items)) {
        setNgos(data.items);
        setTotalCount(data.total || 0);
        setTotalPages(data.total_pages || 1);
      } else if (Array.isArray(data)) {
        setNgos(data);
        setTotalCount(data.length);
        setTotalPages(1);
      } else {
        setNgos([]);
        setTotalCount(0);
        setTotalPages(1);
      }
    } catch (err: any) {
      console.error('Failed to load NGOs from database backend:', err);
      setError(err.message || 'Unable to connect to the backend server.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchNgos();
  }, [search, cause, stateFilter, sort, page]);

  // Handle Search Input Change
  const handleSearchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const val = e.target.value;
    setSearch(val);
    setPage(1);
    updateUrlParams({ search: val, cause, state: stateFilter, sort, page: 1 });
  };

  // Handle Cause Filter Change
  const handleCauseChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const val = e.target.value;
    setCause(val);
    setPage(1);
    updateUrlParams({ search, cause: val, state: stateFilter, sort, page: 1 });
  };

  // Handle State Filter Change
  const handleStateChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const val = e.target.value;
    setStateFilter(val);
    setPage(1);
    updateUrlParams({ search, cause, state: val, sort, page: 1 });
  };

  // Handle Sort Change
  const handleSortChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const val = e.target.value;
    setSort(val);
    updateUrlParams({ search, cause, state: stateFilter, sort: val, page });
  };

  // Reset Filters
  const handleClearFilters = () => {
    setSearch('');
    setCause('All causes');
    setStateFilter('All states');
    setSort('Recently registered');
    setPage(1);
    router.push('/explore');
  };

  // Handle Donation Submit
  const handleDonateSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedNgo) return;
    if (!user) {
      alert('Please sign in to make a verified donation.');
      router.push('/login');
      return;
    }

    const finalAmount = customAmount ? parseFloat(customAmount) : donationAmount;
    if (!finalAmount || finalAmount <= 0) {
      alert('Please enter a valid donation amount.');
      return;
    }

    try {
      setIsSubmitting(true);
      const res = await apiFetch('/api/donations/create', {
        method: 'POST',
        body: JSON.stringify({
          ngo_id: selectedNgo.id,
          amount: finalAmount,
          currency: 'INR',
          donor_name: user.full_name,
          message: donorMsg,
        }),
      });

      setDonationSuccess(res);
      fetchNgos();
    } catch (err: any) {
      alert(err.message || 'Donation submission failed');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <main className="min-h-screen bg-slate-50/60 pb-20 pt-8">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        
        {/* Page Title Header */}
        <div className="mb-8 space-y-2">
          <h1 className="text-3xl font-extrabold text-slate-900 tracking-tight sm:text-4xl">
            Find an organisation
          </h1>
          <p className="text-base text-slate-600 max-w-3xl">
            Every organisation here has had its documents reviewed and approved by an admin.
          </p>
        </div>

        {/* Filter & Search Controls Card */}
        <div className="mb-8 rounded-2xl border border-slate-200/80 bg-white p-5 shadow-xs">
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
            
            {/* Search Input */}
            <div className="space-y-1.5">
              <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider">
                Search
              </label>
              <div className="relative">
                <Search className="absolute left-3.5 top-3 h-4 w-4 text-slate-400" />
                <input
                  type="text"
                  placeholder="Name or city"
                  value={search}
                  onChange={handleSearchChange}
                  className="w-full rounded-xl border border-slate-200 bg-slate-50 pl-10 pr-4 py-2.5 text-sm text-slate-900 placeholder-slate-400 focus:border-blue-500 focus:bg-white focus:outline-none transition-colors"
                />
              </div>
            </div>

            {/* Cause Dropdown */}
            <div className="space-y-1.5">
              <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider">
                Cause
              </label>
              <select
                value={cause}
                onChange={handleCauseChange}
                className="w-full rounded-xl border border-slate-200 bg-slate-50 px-3.5 py-2.5 text-sm font-medium text-slate-800 focus:border-blue-500 focus:bg-white focus:outline-none transition-colors"
              >
                {causesList.map((c) => (
                  <option key={c} value={c}>{c}</option>
                ))}
              </select>
            </div>

            {/* State Dropdown */}
            <div className="space-y-1.5">
              <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider">
                State
              </label>
              <select
                value={stateFilter}
                onChange={handleStateChange}
                className="w-full rounded-xl border border-slate-200 bg-slate-50 px-3.5 py-2.5 text-sm font-medium text-slate-800 focus:border-blue-500 focus:bg-white focus:outline-none transition-colors"
              >
                {statesList.map((s) => (
                  <option key={s} value={s}>{s}</option>
                ))}
              </select>
            </div>

            {/* Sort Dropdown */}
            <div className="space-y-1.5">
              <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider">
                Sort by
              </label>
              <select
                value={sort}
                onChange={handleSortChange}
                className="w-full rounded-xl border border-slate-200 bg-slate-50 px-3.5 py-2.5 text-sm font-medium text-slate-800 focus:border-blue-500 focus:bg-white focus:outline-none transition-colors"
              >
                {sortOptions.map((opt) => (
                  <option key={opt.value} value={opt.value}>{opt.label}</option>
                ))}
              </select>
            </div>

          </div>
        </div>

        {/* Results Counter Bar */}
        <div className="mb-6 flex items-center justify-between">
          <p className="text-sm font-semibold text-slate-600">
            {!loading && !error && (
              <>Showing <span className="text-slate-900 font-bold">{ngos.length}</span> of <span className="text-slate-900 font-bold">{totalCount}</span> verified organisations</>
            )}
          </p>

          {(search || cause !== 'All causes' || stateFilter !== 'All states' || sort !== 'Recently registered') && (
            <button
              onClick={handleClearFilters}
              className="inline-flex items-center gap-1.5 text-xs font-semibold text-blue-600 hover:text-blue-700 transition-colors"
            >
              <RotateCcw className="h-3.5 w-3.5" />
              <span>Clear filters</span>
            </button>
          )}
        </div>

        {/* Loading Skeleton State */}
        {loading && (
          <div className="grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-3">
            {[1, 2, 3, 4, 5, 6].map((i) => (
              <div key={i} className="animate-pulse rounded-2xl border border-slate-200 bg-white p-6 space-y-4">
                <div className="flex items-center justify-between">
                  <div className="h-10 w-10 rounded-xl bg-slate-200"></div>
                  <div className="h-6 w-20 rounded-full bg-slate-200"></div>
                </div>
                <div className="h-5 w-3/4 rounded bg-slate-200"></div>
                <div className="h-4 w-1/2 rounded bg-slate-200"></div>
                <div className="h-12 w-full rounded bg-slate-100"></div>
                <div className="flex gap-2 pt-2">
                  <div className="h-9 flex-1 rounded-xl bg-slate-200"></div>
                  <div className="h-9 flex-1 rounded-xl bg-slate-200"></div>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Error State */}
        {!loading && error && (
          <div className="rounded-2xl border border-rose-200 bg-rose-50/50 p-8 text-center space-y-3">
            <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-rose-100 text-rose-600">
              ⚠️
            </div>
            <h3 className="text-base font-bold text-slate-900">Backend Connection Error</h3>
            <p className="text-xs text-slate-600 max-w-md mx-auto">{error}</p>
            <button
              onClick={fetchNgos}
              className="mt-2 inline-flex items-center gap-2 rounded-xl bg-slate-900 px-4 py-2 text-xs font-bold text-white hover:bg-slate-800"
            >
              <RotateCcw className="h-3.5 w-3.5" />
              <span>Retry connection</span>
            </button>
          </div>
        )}

        {/* Empty State */}
        {!loading && !error && ngos.length === 0 && (
          <div className="rounded-2xl border border-slate-200 bg-white p-12 text-center space-y-4 shadow-xs">
            <Building2 className="mx-auto h-12 w-12 text-slate-400" />
            <div className="space-y-1">
              <h3 className="text-lg font-bold text-slate-900">No organisations found</h3>
              <p className="text-xs text-slate-500 max-w-sm mx-auto">
                No verified organisations match your current search and filter criteria.
              </p>
            </div>
            <button
              onClick={handleClearFilters}
              className="inline-flex items-center gap-2 rounded-xl bg-blue-600 px-5 py-2.5 text-xs font-bold text-white hover:bg-blue-700 shadow-sm shadow-blue-600/20"
            >
              <RotateCcw className="h-4 w-4" />
              <span>Clear filters</span>
            </button>
          </div>
        )}

        {/* NGO Cards Grid */}
        {!loading && !error && ngos.length > 0 && (
          <div className="grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-3">
            {ngos.map((ngo) => {
              const isVerified = ngo.status === 'APPROVED';
              const initials = getInitials(ngo.org_name);

              return (
                <div 
                  key={ngo.id}
                  className="group rounded-2xl border border-slate-200/80 bg-white p-6 shadow-xs hover:shadow-md hover:border-slate-300 transition-all flex flex-col justify-between space-y-5"
                >
                  
                  <div className="space-y-4">
                    {/* Header: Logo Initials & Verified Badge */}
                    <div className="flex items-start justify-between gap-3">
                      <div className="flex h-11 w-11 flex-shrink-0 items-center justify-center rounded-xl bg-blue-50 text-blue-700 font-black text-sm border border-blue-100 shadow-xs">
                        {initials}
                      </div>

                      {isVerified && (
                        <div className="inline-flex items-center gap-1 rounded-full bg-emerald-50 px-2.5 py-1 text-[11px] font-bold text-emerald-700 border border-emerald-200/80 flex-shrink-0">
                          <CheckCircle2 className="h-3.5 w-3.5 text-emerald-600" />
                          <span>Verified</span>
                        </div>
                      )}
                    </div>

                    {/* NGO Name & Location */}
                    <div className="space-y-1">
                      <h3 className="text-lg font-bold text-slate-900 group-hover:text-blue-600 transition-colors leading-snug">
                        {ngo.org_name}
                      </h3>
                      <div className="flex items-center gap-1.5 text-xs font-medium text-slate-500">
                        <MapPin className="h-3.5 w-3.5 text-slate-400 flex-shrink-0" />
                        <span>{ngo.address || 'Location Verified'}</span>
                      </div>
                    </div>

                    {/* Mission / Description */}
                    <p className="text-xs text-slate-600 line-clamp-3 leading-relaxed">
                      {ngo.mission_statement || 'Dedicated to verified philanthropic operations and transparent community impact.'}
                    </p>

                    {/* Category Tag */}
                    <div className="pt-1">
                      <span className="inline-block rounded-lg bg-slate-100 px-2.5 py-1 text-[11px] font-semibold text-slate-700">
                        {ngo.category || 'General Social Good'}
                      </span>
                    </div>
                  </div>

                  {/* Footer Metrics & Actions */}
                  <div className="space-y-4 pt-4 border-t border-slate-100">
                    
                    {/* Scores & Financials */}
                    <div className="grid grid-cols-2 gap-2 text-xs bg-slate-50/80 p-2.5 rounded-xl border border-slate-100">
                      <div>
                        <span className="block text-[10px] uppercase font-bold text-slate-400">Transparency</span>
                        <span className="font-bold text-emerald-700">{ngo.transparency_score}%</span>
                      </div>
                      <div>
                        <span className="block text-[10px] uppercase font-bold text-slate-400">Impact Reached</span>
                        <span className="font-bold text-slate-900">{ngo.beneficiary_count ? ngo.beneficiary_count.toLocaleString() : '1,000+'}</span>
                      </div>
                    </div>

                    {/* Action Buttons */}
                    <div className="flex items-center space-x-2 pt-1">
                      <Link
                        href={`/ngo/${ngo.id}`}
                        className="flex-1 rounded-xl border border-slate-200 bg-white py-2.5 text-center text-xs font-semibold text-slate-700 hover:bg-slate-50 hover:text-blue-600 transition-colors"
                      >
                        View impact
                      </Link>
                      <button
                        onClick={() => setSelectedNgo(ngo)}
                        className="flex-1 rounded-xl bg-blue-600 py-2.5 text-xs font-bold text-white hover:bg-blue-700 transition-colors shadow-xs shadow-blue-600/20"
                      >
                        Donate
                      </button>
                    </div>

                  </div>

                </div>
              );
            })}
          </div>
        )}

        {/* Pagination Bar */}
        {!loading && !error && totalPages > 1 && (
          <div className="mt-10 flex items-center justify-between border-t border-slate-200 pt-6">
            <p className="text-xs font-semibold text-slate-500">
              Page {page} of {totalPages}
            </p>
            <div className="flex items-center space-x-2">
              <button
                disabled={page <= 1}
                onClick={() => {
                  const p = Math.max(1, page - 1);
                  setPage(p);
                  updateUrlParams({ search, cause, state: stateFilter, sort, page: p });
                }}
                className="inline-flex items-center gap-1 rounded-xl border border-slate-200 bg-white px-3.5 py-2 text-xs font-semibold text-slate-700 hover:bg-slate-50 disabled:opacity-40"
              >
                <ChevronLeft className="h-4 w-4" />
                <span>Previous</span>
              </button>
              <button
                disabled={page >= totalPages}
                onClick={() => {
                  const p = Math.min(totalPages, page + 1);
                  setPage(p);
                  updateUrlParams({ search, cause, state: stateFilter, sort, page: p });
                }}
                className="inline-flex items-center gap-1 rounded-xl border border-slate-200 bg-white px-3.5 py-2 text-xs font-semibold text-slate-700 hover:bg-slate-50 disabled:opacity-40"
              >
                <span>Next</span>
                <ChevronRight className="h-4 w-4" />
              </button>
            </div>
          </div>
        )}

      </div>

      {/* Verified Donation Modal */}
      {selectedNgo && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/60 backdrop-blur-sm p-4">
          <div className="w-full max-w-md rounded-2xl bg-white p-6 shadow-2xl space-y-4 border border-slate-100">
            
            {donationSuccess ? (
              <div className="text-center space-y-4 py-3">
                <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-emerald-100 text-emerald-600 font-bold">
                  ✓
                </div>
                <h3 className="text-lg font-bold text-slate-900">Donation Confirmed & Ledger Blocked</h3>
                <p className="text-xs text-slate-600">
                  Thank you! Your donation of <span className="font-bold text-emerald-700">₹{donationSuccess.amount?.toLocaleString('en-IN')} {donationSuccess.currency}</span> to <span className="font-bold text-slate-900">{donationSuccess.ngo_name}</span> has been logged on the SHA-256 blockchain ledger.
                </p>

                <div className="bg-slate-50 p-3 rounded-xl border border-slate-200 text-left font-mono text-[10px] space-y-1">
                  <p className="text-slate-500">Cryptographic Tx Hash:</p>
                  <p className="text-blue-600 break-all">{donationSuccess.transaction_hash}</p>
                </div>

                <button
                  onClick={() => {
                    setSelectedNgo(null);
                    setDonationSuccess(null);
                  }}
                  className="w-full rounded-xl bg-blue-600 py-2.5 text-xs font-bold text-white hover:bg-blue-700 shadow-sm shadow-blue-600/20"
                >
                  Close
                </button>
              </div>
            ) : (
              <form onSubmit={handleDonateSubmit} className="space-y-4">
                <div className="flex justify-between items-start border-b border-slate-100 pb-3">
                  <div>
                    <span className="text-[10px] font-bold text-blue-600 uppercase tracking-wider">Verified NGO Donation</span>
                    <h3 className="text-base font-bold text-slate-900">{selectedNgo.org_name}</h3>
                  </div>
                  <button
                    type="button"
                    onClick={() => setSelectedNgo(null)}
                    className="text-slate-400 hover:text-slate-700 font-bold text-base"
                  >
                    ✕
                  </button>
                </div>

                {/* Amount presets */}
                <div>
                  <label className="block text-xs font-bold text-slate-700 mb-2">Select Amount (INR)</label>
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
                    className="mt-2.5 w-full rounded-xl border border-slate-200 bg-slate-50 px-3.5 py-2 text-xs text-slate-900 placeholder-slate-400 focus:border-blue-500 focus:bg-white focus:outline-none"
                  />
                </div>

                {/* Note */}
                <div>
                  <label className="block text-xs font-bold text-slate-700 mb-1">Impact Message (Optional)</label>
                  <textarea
                    rows={2}
                    value={donorMsg}
                    onChange={(e) => setDonorMsg(e.target.value)}
                    placeholder="Write a message of encouragement..."
                    className="w-full rounded-xl border border-slate-200 bg-slate-50 px-3.5 py-2 text-xs text-slate-900 placeholder-slate-400 focus:border-blue-500 focus:bg-white focus:outline-none"
                  />
                </div>

                <div className="bg-slate-50 p-3 rounded-xl border border-slate-200 text-[11px] text-slate-600 flex items-center gap-2">
                  <Lock className="h-4 w-4 text-blue-600 flex-shrink-0" />
                  <span>Transaction will generate an immutable SHA-256 block hash.</span>
                </div>

                <div className="flex space-x-2 pt-1">
                  <button
                    type="button"
                    onClick={() => setSelectedNgo(null)}
                    className="w-1/3 rounded-xl border border-slate-200 py-2.5 text-xs font-semibold text-slate-600 hover:bg-slate-50"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={isSubmitting}
                    className="w-2/3 rounded-xl bg-blue-600 py-2.5 text-xs font-bold text-white hover:bg-blue-700 disabled:opacity-50 shadow-sm shadow-blue-600/20"
                  >
                    {isSubmitting ? 'Recording on Ledger...' : 'Confirm Donation'}
                  </button>
                </div>
              </form>
            )}

          </div>
        </div>
      )}

    </main>
  );
}

export default function ExplorePage() {
  return (
    <Suspense fallback={
      <div className="min-h-screen bg-slate-50 p-12 text-center text-slate-500">
        Loading Find an organisation portal...
      </div>
    }>
      <ExploreDirectoryContent />
    </Suspense>
  );
}
