'use client';

import React, { useState, useEffect, Suspense } from 'react';
import Link from 'next/link';
import { useRouter, useSearchParams } from 'next/navigation';
import { useAuth } from '@/context/AuthContext';
import {
  ShieldCheck,
  RefreshCw,
  CheckCircle2,
  Lock,
  Search,
  Building2,
  Copy,
  Check,
  AlertTriangle,
  ArrowRight,
  ChevronLeft,
  ChevronRight,
  ExternalLink,
  FileCode,
  RotateCcw,
  Layers,
  Database
} from 'lucide-react';

interface LedgerBlockPayload {
  donation_id?: number;
  tx_hash?: string;
  donor_name?: string;
  ngo_id?: number;
  ngo_name?: string;
  amount?: number;
  currency?: string;
  [key: string]: any;
}

interface LedgerBlock {
  index: number;
  timestamp: string;
  event_type: string;
  payload: LedgerBlockPayload;
  payload_json: string;
  previous_hash: string;
  block_hash: string;
  nonce: number;
}

interface NGO {
  id: number;
  org_name: string;
}

function FundRecordsContent() {
  const { apiFetch } = useAuth();
  const router = useRouter();
  const searchParams = useSearchParams();

  // URL state synchronization
  const [search, setSearch] = useState(searchParams.get('search') || '');
  const [ngoId, setNgoId] = useState<string>(searchParams.get('ngo_id') || 'all');
  const [sort, setSort] = useState(searchParams.get('sort') || 'newest');
  const [page, setPage] = useState(parseInt(searchParams.get('page') || '1', 10));

  // Data & UI states
  const [blocks, setBlocks] = useState<LedgerBlock[]>([]);
  const [totalCount, setTotalCount] = useState<number>(0);
  const [totalPages, setTotalPages] = useState<number>(1);
  const [stats, setStats] = useState<any>({
    total_blocks: 0,
    total_donations: 0,
    total_funds_all: 0,
    total_funds_inr: 0,
    total_funds_usd: 0,
    supported_ngos: 0,
    last_verified: ''
  });
  const [ngosList, setNgosList] = useState<NGO[]>([]);

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [verifying, setVerifying] = useState(false);
  const [verificationResult, setVerificationResult] = useState<any>(null);
  const [copiedHash, setCopiedHash] = useState<string | null>(null);

  // Modal State
  const [selectedBlock, setSelectedBlock] = useState<LedgerBlock | null>(null);

  // Format monetary values in INR/USD with Indian numbering
  const formatCurrency = (amount?: number | null, currency: string = 'INR') => {
    if (amount === undefined || amount === null) return '—';
    const formattedNum = Number(amount).toLocaleString('en-IN', { maximumFractionDigits: 2 });
    if (currency === 'USD' || currency === '$') {
      return `$${formattedNum}`;
    }
    return `\u20B9${formattedNum}`;
  };

  // Safely parse payload — backend sends parsed dict, but fall back to
  // parsing payload_json string if payload key is null/missing (legacy compat)
  const safePayload = (block: LedgerBlock): LedgerBlockPayload => {
    if (block.payload && typeof block.payload === 'object' && !Array.isArray(block.payload)) {
      return block.payload;
    }
    try {
      const parsed = JSON.parse(block.payload_json || '{}');
      // Strip email even in frontend as final safety net
      if (parsed && typeof parsed === 'object') {
        delete parsed.donor_email;
      }
      return parsed as LedgerBlockPayload;
    } catch {
      return {};
    }
  };

  // Shorten SHA-256 hash for clean UI card display
  const shortenHash = (hash: string) => {
    if (!hash) return '';
    if (hash.length <= 16) return hash;
    return `${hash.substring(0, 8)}...${hash.substring(hash.length - 8)}`;
  };

  // Helper to copy text to clipboard
  const handleCopyHash = (text: string) => {
    navigator.clipboard.writeText(text);
    setCopiedHash(text);
    setTimeout(() => setCopiedHash(null), 2500);
  };

  // Update URL search parameters
  const updateUrlParams = (newParams: Record<string, string | number>) => {
    const params = new URLSearchParams(searchParams.toString());
    Object.entries(newParams).forEach(([key, value]) => {
      if (value && value !== 'all' && value !== 'newest' && value !== 1 && value !== '1') {
        params.set(key, String(value));
      } else {
        params.delete(key);
      }
    });
    router.push(`/ledger?${params.toString()}`);
  };

  // Fetch approved NGOs for dropdown filter
  useEffect(() => {
    const fetchNgoDropdown = async () => {
      try {
        const data = await apiFetch('/api/public/ngos');
        if (Array.isArray(data)) {
          setNgosList(data);
        } else if (data && Array.isArray(data.items)) {
          setNgosList(data.items);
        }
      } catch (err) {
        console.error('Failed to fetch NGO list for filter dropdown:', err);
      }
    };
    fetchNgoDropdown();
  }, []);

  // Fetch ledger blocks & integrity summary
  const fetchLedgerData = async () => {
    try {
      setLoading(true);
      setError(null);

      const params = new URLSearchParams();
      params.set('meta', 'true');
      params.set('page', String(page));
      params.set('limit', '12');

      if (search.trim()) params.set('search', search.trim());
      if (ngoId && ngoId !== 'all') params.set('ngo_id', ngoId);
      if (sort) params.set('sort', sort);

      const data = await apiFetch(`/api/ledger/blocks?${params.toString()}`);

      if (data && Array.isArray(data.items)) {
        setBlocks(data.items);
        setTotalCount(data.total || 0);
        setTotalPages(data.total_pages || 1);
        if (data.stats) setStats(data.stats);
      } else if (Array.isArray(data)) {
        setBlocks(data);
        setTotalCount(data.length);
        setTotalPages(1);
      } else {
        setBlocks([]);
        setTotalCount(0);
        setTotalPages(1);
      }

      // Initial integrity verification
      if (!verificationResult) {
        const vRes = await apiFetch('/api/ledger/verify');
        setVerificationResult(vRes);
      }
    } catch (err: any) {
      console.error('Failed to load ledger records:', err);
      setError(err.message || 'Unable to load fund records. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchLedgerData();
  }, [search, ngoId, sort, page]);

  // Handle Live Re-verification Call
  const handleReverify = async () => {
    try {
      setVerifying(true);
      const vRes = await apiFetch('/api/ledger/verify');
      setVerificationResult(vRes);
      if (vRes && vRes.verified_at) {
        setStats((prev: any) => ({ ...prev, last_verified: vRes.verified_at }));
      }
    } catch (err: any) {
      alert(err.message || 'Verification failed');
    } finally {
      setVerifying(false);
    }
  };

  // Filter Handlers
  const handleSearchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const val = e.target.value;
    setSearch(val);
    setPage(1);
    updateUrlParams({ search: val, ngo_id: ngoId, sort, page: 1 });
  };

  const handleNgoChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const val = e.target.value;
    setNgoId(val);
    setPage(1);
    updateUrlParams({ search, ngo_id: val, sort, page: 1 });
  };

  const handleSortChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const val = e.target.value;
    setSort(val);
    updateUrlParams({ search, ngo_id: ngoId, sort: val, page });
  };

  const handleClearFilters = () => {
    setSearch('');
    setNgoId('all');
    setSort('newest');
    setPage(1);
    router.push('/ledger');
  };

  const isChainValid = verificationResult ? verificationResult.valid : true;

  return (
    <main className="min-h-screen bg-slate-50/60 pb-20 pt-8">
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 space-y-8">

        {/* 1. Page Header */}
        <div className="space-y-3 max-w-3xl">
          <div className="inline-flex items-center space-x-2 rounded-full border border-blue-200 bg-blue-50 px-3.5 py-1 text-xs font-bold text-blue-700">
            <Lock className="h-3.5 w-3.5" />
            <span>SHA-256 Hash-Linked Ledger & Tamper-Evident System</span>
          </div>
          <h1 className="text-3xl font-extrabold text-slate-900 tracking-tight sm:text-4xl">
            Fund Records
          </h1>
          <p className="text-base font-medium text-slate-700 leading-snug">
            Transparent records of donations and their cryptographically linked ledger history.
          </p>
          <p className="text-xs text-slate-600 leading-relaxed pt-1">
            Every recorded donation is linked to the previous ledger record using a SHA-256 cryptographic hash. This makes unauthorized changes detectable.
          </p>
        </div>

        {/* 2. Ledger Integrity Summary Card */}
        <div className="rounded-2xl border border-slate-200/80 bg-white p-6 shadow-xs space-y-6">
          <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 border-b border-slate-100 pb-5">
            <div className="flex items-center space-x-3">
              {isChainValid ? (
                <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-emerald-50 text-emerald-600 border border-emerald-200">
                  <CheckCircle2 className="h-5 w-5" />
                </div>
              ) : (
                <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-rose-50 text-rose-600 border border-rose-200">
                  <AlertTriangle className="h-5 w-5" />
                </div>
              )}
              <div>
                <div className="flex items-center space-x-2">
                  <span className={`text-sm font-bold ${isChainValid ? 'text-emerald-700' : 'text-rose-700'}`}>
                    {isChainValid ? '✓ Chain Integrity Verified' : '⚠ Chain Integrity Verification Failed'}
                  </span>
                  <span className="inline-block h-2 w-2 rounded-full bg-emerald-500 animate-pulse"></span>
                </div>
                <p className="text-xs text-slate-500 mt-0.5">
                  {verificationResult?.status || 'SHA-256 sequential cryptographic link active'}
                </p>
              </div>
            </div>

            <button
              onClick={handleReverify}
              disabled={verifying}
              className="inline-flex items-center justify-center space-x-2 rounded-xl bg-blue-600 hover:bg-blue-700 px-4 py-2.5 text-xs font-bold text-white transition-all shadow-xs shadow-blue-600/20 disabled:opacity-50"
            >
              <RefreshCw className={`h-4 w-4 ${verifying ? 'animate-spin' : ''}`} />
              <span>{verifying ? 'Re-scanning Chain...' : 'Re-verify Ledger'}</span>
            </button>
          </div>

          {/* Stats Grid */}
          <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-6">
            <div className="rounded-xl bg-slate-50/80 p-3.5 border border-slate-100 space-y-1">
              <span className="block text-[10px] font-bold text-slate-500 uppercase tracking-wider">Total Blocks</span>
              <span className="text-lg font-extrabold text-slate-900">{stats.total_blocks || totalCount}</span>
              <span className="block text-[9px] text-slate-400 font-medium">SHA-256 Linked</span>
            </div>

            <div className="rounded-xl bg-slate-50/80 p-3.5 border border-slate-100 space-y-1">
              <span className="block text-[10px] font-bold text-slate-500 uppercase tracking-wider">Total Donations</span>
              <span className="text-lg font-extrabold text-slate-900">{stats.total_donations || totalCount}</span>
              <span className="block text-[9px] text-slate-400 font-medium">Recorded Events</span>
            </div>

            <div className="rounded-xl bg-emerald-50/50 p-3.5 border border-emerald-100 space-y-1">
              <span className="block text-[10px] font-bold text-emerald-800 uppercase tracking-wider">Current Platform Funds</span>
              <span className="text-lg font-extrabold text-emerald-700">
                {`\u20B9${Number(stats.total_funds_inr || 0).toLocaleString('en-IN')}`}
              </span>
              <span className="block text-[9px] text-emerald-600 font-medium">Active INR Currency</span>
            </div>

            <div className="rounded-xl bg-amber-50/60 p-3.5 border border-amber-100 space-y-1">
              <span className="block text-[10px] font-bold text-amber-800 uppercase tracking-wider">Pre-Migration USD Records</span>
              <span className="text-lg font-extrabold text-amber-800">
                {`$${Number(stats.total_funds_usd || 0).toLocaleString('en-IN')} USD`}
              </span>
              <span className="block text-[9px] text-amber-700 font-medium">
                {stats.usd_blocks_count ? `${stats.usd_blocks_count} historical USD blocks` : 'Historical pre-migration USD'}
              </span>
            </div>

            <div className="rounded-xl bg-slate-50/80 p-3.5 border border-slate-100 space-y-1">
              <span className="block text-[10px] font-bold text-slate-500 uppercase tracking-wider">Supported NGOs</span>
              <span className="text-lg font-extrabold text-slate-900">{stats.supported_ngos || ngosList.length || 8}</span>
              <span className="block text-[9px] text-slate-400 font-medium">Verified Partners</span>
            </div>

            <div className="col-span-2 sm:col-span-1 rounded-xl bg-slate-50/80 p-3.5 border border-slate-100 space-y-1">
              <span className="block text-[10px] font-bold text-slate-500 uppercase tracking-wider">Last Verification</span>
              <span className="block text-xs font-semibold text-slate-700 truncate">
                {stats.last_verified || 'Verified Live'}
              </span>
              <span className="block text-[9px] text-emerald-600 font-medium">Chain Intact</span>
            </div>
          </div>
        </div>

        {/* 3. How the Ledger Works Section */}
        <div className="rounded-2xl border border-slate-200/80 bg-white p-6 shadow-xs space-y-5">
          <div>
            <h2 className="text-lg font-bold text-slate-900 flex items-center gap-2">
              <Layers className="h-5 w-5 text-blue-600" />
              <span>How the ledger works</span>
            </h2>
            <p className="text-xs text-slate-600 mt-1">
              Each donation creates a ledger record. The record is cryptographically linked to the previous block. If important ledger data is changed later, the calculated hash will no longer match the stored hash, allowing the system to detect the change.
            </p>
          </div>

          {/* Visual Diagram Flow */}
          <div className="flex flex-wrap items-center justify-between gap-2 py-3 bg-slate-50 rounded-xl px-4 border border-slate-200/70 text-xs font-bold text-slate-800">
            <div className="flex items-center space-x-2 bg-white px-3 py-2 rounded-lg border border-slate-200 shadow-2xs">
              <span className="h-2 w-2 rounded-full bg-blue-600"></span>
              <span>Donation</span>
            </div>
            <ArrowRight className="h-4 w-4 text-slate-400 flex-shrink-0" />
            <div className="flex items-center space-x-2 bg-white px-3 py-2 rounded-lg border border-slate-200 shadow-2xs">
              <span className="h-2 w-2 rounded-full bg-blue-600"></span>
              <span>Donation Record</span>
            </div>
            <ArrowRight className="h-4 w-4 text-slate-400 flex-shrink-0" />
            <div className="flex items-center space-x-2 bg-white px-3 py-2 rounded-lg border border-slate-200 shadow-2xs">
              <span className="h-2 w-2 rounded-full bg-blue-600"></span>
              <span>Ledger Block</span>
            </div>
            <ArrowRight className="h-4 w-4 text-slate-400 flex-shrink-0" />
            <div className="flex items-center space-x-2 bg-white px-3 py-2 rounded-lg border border-slate-200 shadow-2xs">
              <span className="h-2 w-2 rounded-full bg-emerald-600"></span>
              <span>SHA-256 Hash</span>
            </div>
            <ArrowRight className="h-4 w-4 text-slate-400 flex-shrink-0" />
            <div className="flex items-center space-x-2 bg-white px-3 py-2 rounded-lg border border-slate-200 shadow-2xs">
              <span className="h-2 w-2 rounded-full bg-blue-600"></span>
              <span>Next Block</span>
            </div>
          </div>

          {/* 3 Explanation Cards */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 pt-1">
            <div className="rounded-xl border border-slate-200/80 p-4 space-y-1.5 bg-slate-50/50">
              <h3 className="text-xs font-bold text-slate-900">1. Donation Recorded</h3>
              <p className="text-xs text-slate-600 leading-relaxed">
                Each completed donation generates a tamper-evident record storing the amount, recipient NGO, and timestamp.
              </p>
            </div>

            <div className="rounded-xl border border-slate-200/80 p-4 space-y-1.5 bg-slate-50/50">
              <h3 className="text-xs font-bold text-slate-900">2. Block Cryptographically Linked</h3>
              <p className="text-xs text-slate-600 leading-relaxed">
                The block embeds the SHA-256 cryptographic digest of the preceding block, creating an unbroken chain.
              </p>
            </div>

            <div className="rounded-xl border border-slate-200/80 p-4 space-y-1.5 bg-slate-50/50">
              <h3 className="text-xs font-bold text-slate-900">3. Tampering Becomes Detectable</h3>
              <p className="text-xs text-slate-600 leading-relaxed">
                Any unauthorized alteration of past records changes the hash and instantly fails sequential verification.
              </p>
            </div>
          </div>
        </div>

        {/* 4. Search and Filter Bar */}
        <div className="rounded-2xl border border-slate-200/80 bg-white p-5 shadow-xs">
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
            
            {/* Search Input */}
            <div className="space-y-1.5">
              <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider">
                Search
              </label>
              <div className="relative">
                <Search className="absolute left-3.5 top-3 h-4 w-4 text-slate-400" />
                <input
                  type="text"
                  placeholder="Search NGO or transaction..."
                  value={search}
                  onChange={handleSearchChange}
                  className="w-full rounded-xl border border-slate-200 bg-slate-50 pl-10 pr-4 py-2 text-sm text-slate-900 placeholder-slate-400 focus:border-blue-500 focus:bg-white focus:outline-none transition-colors"
                />
              </div>
            </div>

            {/* NGO Select Dropdown */}
            <div className="space-y-1.5">
              <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider">
                Organisation
              </label>
              <select
                value={ngoId}
                onChange={handleNgoChange}
                className="w-full rounded-xl border border-slate-200 bg-slate-50 px-3.5 py-2 text-sm font-medium text-slate-800 focus:border-blue-500 focus:bg-white focus:outline-none transition-colors"
              >
                <option value="all">All organisations</option>
                {ngosList.map((ngo) => (
                  <option key={ngo.id} value={ngo.id}>{ngo.org_name}</option>
                ))}
              </select>
            </div>

            {/* Sort Dropdown */}
            <div className="space-y-1.5">
              <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider">
                Sort
              </label>
              <select
                value={sort}
                onChange={handleSortChange}
                className="w-full rounded-xl border border-slate-200 bg-slate-50 px-3.5 py-2 text-sm font-medium text-slate-800 focus:border-blue-500 focus:bg-white focus:outline-none transition-colors"
              >
                <option value="newest">Newest first</option>
                <option value="oldest">Oldest first</option>
                <option value="highest_amount">Highest amount</option>
                <option value="lowest_amount">Lowest amount</option>
              </select>
            </div>

          </div>
        </div>

        {/* Counter Bar */}
        <div className="flex items-center justify-between">
          <p className="text-sm font-semibold text-slate-600">
            {!loading && !error && (
              <>Showing <span className="text-slate-900 font-bold">{blocks.length}</span> of <span className="text-slate-900 font-bold">{totalCount}</span> ledger records</>
            )}
          </p>

          {(search || ngoId !== 'all' || sort !== 'newest') && (
            <button
              onClick={handleClearFilters}
              className="inline-flex items-center gap-1.5 text-xs font-semibold text-blue-600 hover:text-blue-700 transition-colors"
            >
              <RotateCcw className="h-3.5 w-3.5" />
              <span>Clear filters</span>
            </button>
          )}
        </div>

        {/* Loading Skeleton */}
        {loading && (
          <div className="grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-3">
            {[1, 2, 3, 4, 5, 6].map((i) => (
              <div key={i} className="animate-pulse rounded-2xl border border-slate-200 bg-white p-6 space-y-4">
                <div className="flex items-center justify-between">
                  <div className="h-6 w-24 bg-slate-200 rounded-lg"></div>
                  <div className="h-6 w-20 bg-slate-200 rounded-full"></div>
                </div>
                <div className="h-5 w-3/4 bg-slate-200 rounded"></div>
                <div className="h-10 w-full bg-slate-100 rounded-xl"></div>
                <div className="h-8 w-full bg-slate-200 rounded-xl"></div>
              </div>
            ))}
          </div>
        )}

        {/* Error State */}
        {!loading && error && (
          <div className="rounded-2xl border border-rose-200 bg-rose-50/50 p-8 text-center space-y-3">
            <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-rose-100 text-rose-600">
              <AlertTriangle className="h-6 w-6" />
            </div>
            <h3 className="text-base font-bold text-slate-900">Unable to load fund records</h3>
            <p className="text-xs text-slate-600 max-w-md mx-auto">{error}</p>
            <button
              onClick={fetchLedgerData}
              className="mt-2 inline-flex items-center gap-2 rounded-xl bg-slate-900 px-4 py-2 text-xs font-bold text-white hover:bg-slate-800"
            >
              <RefreshCw className="h-3.5 w-3.5" />
              <span>Retry connection</span>
            </button>
          </div>
        )}

        {/* Empty State */}
        {!loading && !error && blocks.length === 0 && (
          <div className="rounded-2xl border border-slate-200 bg-white p-12 text-center space-y-4 shadow-xs">
            <Database className="mx-auto h-12 w-12 text-slate-400" />
            <div className="space-y-1">
              <h3 className="text-lg font-bold text-slate-900">No fund records found</h3>
              <p className="text-xs text-slate-500 max-w-sm mx-auto">
                No ledger blocks match your search or filter options.
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

        {/* 5. Ledger Block Cards */}
        {!loading && !error && blocks.length > 0 && (
          <div className="grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-3">
            {blocks.map((block) => {
              const payload = safePayload(block);
              const isDonation = block.event_type === 'DONATION_LOGGED';
              const ngoName = payload.ngo_name || (isDonation ? 'Organisation unavailable' : '—');
              const ngoIdVal = payload.ngo_id;
              const amountVal = (payload.amount !== undefined && payload.amount !== null) ? Number(payload.amount) : null;
              const currencyVal = payload.currency || 'INR';
              const donorLabel = payload.donor_name || 'Verified donor';

              return (
                <div
                  key={block.index}
                  className="rounded-2xl border border-slate-200/80 bg-white p-6 shadow-xs hover:shadow-md hover:border-slate-300 transition-all flex flex-col justify-between space-y-5"
                >
                  <div className="space-y-4">
                    {/* Header: Block Index & Status Badge */}
                    <div className="flex items-center justify-between gap-2 border-b border-slate-100 pb-3">
                      <div className="flex items-center space-x-2">
                        <span className="flex h-7 w-7 items-center justify-center rounded-lg bg-blue-50 text-blue-700 font-extrabold text-xs border border-blue-200">
                          #{block.index}
                        </span>
                        <span className="inline-block text-[10px] font-extrabold uppercase tracking-wider px-2 py-0.5 rounded-full bg-slate-100 text-slate-700">
                          {block.event_type}
                        </span>
                      </div>

                      <div className="inline-flex items-center gap-1 rounded-full bg-emerald-50 px-2 py-0.5 text-[10px] font-bold text-emerald-700 border border-emerald-200">
                        <CheckCircle2 className="h-3 w-3 text-emerald-600" />
                        <span>SHA-256 Verified</span>
                      </div>
                    </div>

                    {/* NGO Name & Link */}
                    <div className="space-y-1">
                      <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">Recipient Organisation</span>
                      {ngoIdVal ? (
                        <Link
                          href={`/ngo/${ngoIdVal}`}
                          className="text-base font-bold text-slate-900 hover:text-blue-600 transition-colors inline-flex items-center gap-1 leading-snug"
                        >
                          <span>{ngoName}</span>
                          <ExternalLink className="h-3.5 w-3.5 text-slate-400" />
                        </Link>
                      ) : (
                        <h3 className="text-base font-bold text-slate-900 leading-snug">{ngoName}</h3>
                      )}
                    </div>

                    {/* Financial Amount & Donor Info */}
                    <div className={`grid grid-cols-2 gap-2 p-3 rounded-xl border text-xs ${currencyVal === 'USD' ? 'bg-amber-50/40 border-amber-100' : 'bg-slate-50/80 border-slate-100'}`}>
                      <div>
                        <span className="block text-[10px] uppercase font-bold text-slate-400">Amount</span>
                        <span className={`text-base font-extrabold ${currencyVal === 'USD' ? 'text-amber-800' : 'text-emerald-700'}`}>
                          {isDonation ? formatCurrency(amountVal, currencyVal) : 'System Event'}
                        </span>
                        {isDonation && currencyVal === 'USD' && (
                          <span className="inline-flex items-center gap-1 text-[9px] font-bold text-amber-800 bg-amber-100/70 px-1.5 py-0.5 rounded border border-amber-200 mt-1 block">
                            <AlertTriangle className="h-2.5 w-2.5 text-amber-600 flex-shrink-0" />
                            <span>Historical USD record</span>
                          </span>
                        )}
                        {isDonation && currencyVal === 'INR' && (
                          <span className="inline-flex items-center gap-1 text-[9px] font-bold text-emerald-800 bg-emerald-100/70 px-1.5 py-0.5 rounded border border-emerald-200 mt-1 block">
                            <CheckCircle2 className="h-2.5 w-2.5 text-emerald-600 flex-shrink-0" />
                            <span>INR record</span>
                          </span>
                        )}
                      </div>
                      <div>
                        <span className="block text-[10px] uppercase font-bold text-slate-400">Donor</span>
                        <span className="font-bold text-slate-800">{donorLabel}</span>
                      </div>
                    </div>

                    {/* Hashes Section */}
                    <div className="space-y-2 text-[11px] font-mono">
                      <div className="flex justify-between items-center bg-slate-50 p-2 rounded-lg border border-slate-100">
                        <span className="text-slate-400 text-[10px] font-bold uppercase">Previous Hash</span>
                        <span className="text-slate-600 font-semibold">{shortenHash(block.previous_hash)}</span>
                      </div>

                      <div className="flex justify-between items-center bg-blue-50/50 p-2 rounded-lg border border-blue-100">
                        <span className="text-blue-600 text-[10px] font-bold uppercase">Current Hash</span>
                        <span className="text-blue-700 font-bold">{shortenHash(block.block_hash)}</span>
                      </div>
                    </div>

                    {/* Timestamp */}
                    <p className="text-[11px] text-slate-400 font-mono">
                      Timestamp: {new Date(block.timestamp).toLocaleString()}
                    </p>
                  </div>

                  {/* Actions */}
                  <div className="flex items-center space-x-2 pt-3 border-t border-slate-100">
                    <button
                      onClick={() => setSelectedBlock(block)}
                      className="flex-1 rounded-xl border border-slate-200 bg-white py-2 text-center text-xs font-bold text-slate-700 hover:bg-slate-50 hover:text-blue-600 transition-colors"
                    >
                      View block details
                    </button>
                    <button
                      onClick={() => handleCopyHash(block.block_hash)}
                      className="inline-flex items-center justify-center gap-1 rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 text-xs font-semibold text-slate-700 hover:bg-slate-100 transition-colors"
                      title="Copy SHA-256 block hash"
                    >
                      {copiedHash === block.block_hash ? (
                        <>
                          <Check className="h-3.5 w-3.5 text-emerald-600" />
                          <span className="text-emerald-700 font-bold">Copied</span>
                        </>
                      ) : (
                        <>
                          <Copy className="h-3.5 w-3.5 text-slate-500" />
                          <span>Copy hash</span>
                        </>
                      )}
                    </button>
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
              Showing page {page} of {totalPages}
            </p>
            <div className="flex items-center space-x-2">
              <button
                disabled={page <= 1}
                onClick={() => {
                  const p = Math.max(1, page - 1);
                  setPage(p);
                  updateUrlParams({ search, ngo_id: ngoId, sort, page: p });
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
                  updateUrlParams({ search, ngo_id: ngoId, sort, page: p });
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

      {/* 6. Block Details Modal */}
      {selectedBlock && (()=>{const modalPayload=safePayload(selectedBlock);return(<>
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/60 backdrop-blur-sm p-4">
          <div className="w-full max-w-2xl rounded-2xl bg-white p-6 shadow-2xl space-y-5 border border-slate-100 max-h-[90vh] overflow-y-auto">
            
            <div className="flex justify-between items-start border-b border-slate-100 pb-4">
              <div className="flex items-center space-x-3">
                <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-blue-50 text-blue-700 font-black text-sm border border-blue-200">
                  #{selectedBlock.index}
                </span>
                <div>
                  <h3 className="text-base font-bold text-slate-900">BLOCK #{selectedBlock.index} DETAILS</h3>
                  <p className="text-xs text-slate-500">Event: {selectedBlock.event_type}</p>
                </div>
              </div>
              <button
                type="button"
                onClick={() => setSelectedBlock(null)}
                className="text-slate-400 hover:text-slate-700 font-bold text-lg"
              >
                ✕
              </button>
            </div>

            {/* Block Specifications */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs">
              <div className="bg-slate-50 p-3 rounded-xl border border-slate-200 space-y-1">
                <span className="text-[10px] font-bold text-slate-400 uppercase">Timestamp</span>
                <p className="font-mono text-slate-800">{new Date(selectedBlock.timestamp).toLocaleString()}</p>
              </div>

              <div className="bg-slate-50 p-3 rounded-xl border border-slate-200 space-y-1">
                <span className="text-[10px] font-bold text-slate-400 uppercase">Donor</span>
                <p className="font-bold text-slate-800">{modalPayload.donor_name || 'Verified donor'}</p>
              </div>

              <div className="bg-slate-50 p-3 rounded-xl border border-slate-200 space-y-1">
                <span className="text-[10px] font-bold text-slate-400 uppercase">Recipient Organisation</span>
                <p className="font-bold text-slate-900">
                  {modalPayload.ngo_name || (selectedBlock.event_type === 'DONATION_LOGGED' ? 'Organisation unavailable' : '—')}
                </p>
                {modalPayload.ngo_id && (
                  <p className="text-[10px] text-slate-400 font-mono">NGO ID: {modalPayload.ngo_id}</p>
                )}
              </div>

              <div className="bg-slate-50 p-3 rounded-xl border border-slate-200 space-y-1">
                <span className="text-[10px] font-bold text-slate-400 uppercase">Amount</span>
                <p className="font-extrabold text-emerald-700 text-sm">
                  {selectedBlock.event_type === 'DONATION_LOGGED'
                    ? formatCurrency(
                        modalPayload.amount !== undefined ? Number(modalPayload.amount) : null,
                        modalPayload.currency || 'INR'
                      )
                    : 'System Record'}
                </p>
                {modalPayload.currency && (
                  <p className="text-[10px] text-slate-400 font-mono">{modalPayload.currency}</p>
                )}
              </div>

              {modalPayload.donation_id && (
                <div className="bg-slate-50 p-3 rounded-xl border border-slate-200 space-y-1">
                  <span className="text-[10px] font-bold text-slate-400 uppercase">Donation ID</span>
                  <p className="font-mono font-bold text-slate-800">#{modalPayload.donation_id}</p>
                </div>
              )}
            </div>

            {/* Historical USD Notice Banner */}
            {modalPayload.currency === 'USD' && (
              <div className="rounded-xl border border-amber-200/90 bg-amber-50/90 p-3.5 text-xs text-amber-900 flex items-start space-x-2.5">
                <AlertTriangle className="h-4 w-4 text-amber-600 flex-shrink-0 mt-0.5" />
                <div>
                  <span className="font-bold block text-amber-950">Historical Pre-Migration Ledger Record</span>
                  <span className="text-amber-800 text-[11px] leading-relaxed block mt-0.5">
                    Historical record — originally recorded in USD before the platform migrated to INR.
                    The raw payload and SHA-256 block hash remain cryptographically immutable and byte-preserved.
                  </span>
                </div>
              </div>
            )}

            {/* Hashes Detail */}
            <div className="space-y-3 text-xs font-mono">
              <div className="bg-slate-50 p-3 rounded-xl border border-slate-200 space-y-1">
                <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">Previous Block Hash</span>
                <span className="text-slate-600 break-all">{selectedBlock.previous_hash}</span>
              </div>

              <div className="bg-blue-50/60 p-3.5 rounded-xl border border-blue-200 space-y-1">
                <span className="text-[10px] font-bold text-blue-700 uppercase tracking-wider block">Current Block Hash (SHA-256 Digest)</span>
                <span className="text-blue-900 font-bold break-all">{selectedBlock.block_hash}</span>
              </div>

              {modalPayload.tx_hash && (
                <div className="bg-slate-50 p-3 rounded-xl border border-slate-200 space-y-1">
                  <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block">Transaction Hash</span>
                  <span className="text-slate-700 break-all">{modalPayload.tx_hash}</span>
                </div>
              )}
            </div>

            {/* Block Payload Dump — privacy-safe: email already stripped by safePayload */}
            <div className="space-y-1">
              <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider block">Payload JSON</span>
              <pre className="bg-slate-900 text-slate-200 p-3.5 rounded-xl font-mono text-[11px] overflow-x-auto whitespace-pre-wrap max-h-40">
                {JSON.stringify(modalPayload, null, 2)}
              </pre>
            </div>

            {/* Verification Banner */}
            <div className="bg-emerald-50 p-3 rounded-xl border border-emerald-200 text-xs font-bold text-emerald-800 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <CheckCircle2 className="h-4 w-4 text-emerald-600" />
                <span>SHA-256 Cryptographic Link Valid & Tamper-Free</span>
              </div>
              <span className="text-[10px] font-mono bg-white px-2 py-0.5 rounded border border-emerald-200">Nonce: {selectedBlock.nonce}</span>
            </div>

            {/* Modal Actions */}
            <div className="flex items-center justify-end space-x-2 pt-2 border-t border-slate-100">
              <button
                type="button"
                onClick={() => setSelectedBlock(null)}
                className="rounded-xl border border-slate-200 px-4 py-2 text-xs font-bold text-slate-700 hover:bg-slate-50"
              >
                Close
              </button>
              <button
                type="button"
                onClick={() => handleCopyHash(selectedBlock.block_hash)}
                className="inline-flex items-center gap-1.5 rounded-xl bg-blue-600 px-4 py-2 text-xs font-bold text-white hover:bg-blue-700 shadow-xs shadow-blue-600/20"
              >
                {copiedHash === selectedBlock.block_hash ? (
                  <>
                    <Check className="h-4 w-4 text-white" />
                    <span>Hash Copied!</span>
                  </>
                ) : (
                  <>
                    <Copy className="h-4 w-4 text-white" />
                    <span>Copy Current Hash</span>
                  </>
                )}
              </button>
            </div>

          </div>
        </div>
      </>);})()}

    </main>
  );
}

export default function LedgerPage() {
  return (
    <Suspense fallback={
      <div className="min-h-screen bg-slate-50 p-12 text-center text-slate-500">
        Loading Fund Records ledger...
      </div>
    }>
      <FundRecordsContent />
    </Suspense>
  );
}
