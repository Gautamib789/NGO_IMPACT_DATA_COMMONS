'use client';

import React, { useState, useEffect, Suspense } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/context/AuthContext';
import { 
  ShieldCheck, 
  HeartHandshake, 
  Database, 
  CheckCircle2, 
  FileText, 
  Lock, 
  Building2, 
  TrendingUp, 
  ArrowRight, 
  Sparkles, 
  Users, 
  ChevronRight, 
  GraduationCap, 
  Utensils, 
  HeartPulse, 
  Baby, 
  UserCheck, 
  HelpingHand, 
  Flame, 
  Globe
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
  doc_completeness_score: number;
  transparency_score: number;
  total_expenses: number;
  total_donations_received: number;
  beneficiary_count: number;
}

interface Stats {
  approved_ngos_count: number;
  total_funds_raised: number;
  total_donations_count: number;
  total_beneficiaries_impacted: number;
  blockchain_ledger_blocks: number;
}

function LandingContent() {
  const { user, apiFetch } = useAuth();
  const router = useRouter();

  const [ngos, setNgos] = useState<NGO[]>([]);
  const [stats, setStats] = useState<Stats | null>(null);
  const [loading, setLoading] = useState(true);
  const [selectedCategory, setSelectedCategory] = useState<string>('All');

  // Donation Modal State
  const [selectedNgo, setSelectedNgo] = useState<NGO | null>(null);
  const [donationAmount, setDonationAmount] = useState<number>(50);
  const [customAmount, setCustomAmount] = useState<string>('');
  const [donorMsg, setDonorMsg] = useState<string>('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [donationSuccess, setDonationSuccess] = useState<any>(null);

  const causes = [
    { name: 'Free Education', icon: GraduationCap, category: 'Education & Youth' },
    { name: 'Free Food', icon: Utensils, category: 'Clean Water & Sanitation' },
    { name: 'Medical Support', icon: HeartPulse, category: 'Healthcare & Relief' },
    { name: 'Child Welfare', icon: Baby, category: 'Education & Youth' },
    { name: 'Women Empowerment', icon: UserCheck, category: 'Community Development' },
    { name: 'Old Age Support', icon: HelpingHand, category: 'Healthcare & Relief' },
    { name: 'Disaster Relief', icon: Flame, category: 'Healthcare & Relief' },
    { name: 'Community Development', icon: Globe, category: 'Environment & Conservation' },
    { name: 'Other', icon: Sparkles, category: 'All' },
  ];

  const recentImpactWork = [
    {
      id: 1,
      title: 'Free Food Distribution for 150 Families',
      category: 'Free Food',
      ngoName: 'Hope Foundation India',
      date: '26 Aug 2026',
      description: 'Distributed 150 essential grain and nutrient packages to vulnerable families facing drought.',
      accentColor: 'from-amber-500 to-orange-500',
      icon: Utensils
    },
    {
      id: 2,
      title: 'Clean Drinking Water Well Installation',
      category: 'Clean Water & Sanitation',
      ngoName: 'CleanWater Global Initiative',
      date: '15 Jul 2026',
      description: 'Constructed a solar-powered deep aquifer water filtration well providing clean water to 800 villagers.',
      accentColor: 'from-blue-500 to-cyan-500',
      icon: Globe
    },
    {
      id: 3,
      title: 'Youth STEM & Education Learning Kits',
      category: 'Free Education',
      ngoName: 'GreenEarth Environmental Alliance',
      date: '10 Jun 2026',
      description: 'Provided 200 science kits and digital tablet access for primary school students in rural learning centers.',
      accentColor: 'from-emerald-500 to-teal-500',
      icon: GraduationCap
    }
  ];

  useEffect(() => {
    const loadData = async () => {
      try {
        setLoading(true);
        const [statsData, ngosData] = await Promise.all([
          apiFetch('/api/public/stats').catch(() => null),
          apiFetch('/api/public/ngos').catch(() => [])
        ]);
        if (statsData) setStats(statsData);
        if (ngosData) setNgos(ngosData);
      } catch (err) {
        console.error('Failed to load landing page data', err);
      } finally {
        setLoading(false);
      }
    };
    loadData();
  }, []);

  const getInitials = (name: string) => {
    return name
      .split(' ')
      .map(part => part[0])
      .join('')
      .substring(0, 2)
      .toUpperCase();
  };

  const handleDonateSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedNgo) return;
    if (!user) {
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
      apiFetch('/api/public/stats').then(setStats).catch(() => {});
    } catch (err: any) {
      alert(err.message || 'Donation submission failed');
    } finally {
      setIsSubmitting(false);
    }
  };

  const filteredNgos = selectedCategory === 'All' 
    ? ngos 
    : ngos.filter(n => n.category.toLowerCase().includes(selectedCategory.toLowerCase()) || selectedCategory.toLowerCase().includes(n.category.toLowerCase()));

  return (
    <div className="w-full bg-white text-slate-900">
      
      {/* 1. HERO SECTION */}
      <section className="w-full bg-gradient-to-b from-slate-50/70 via-white to-white py-16 sm:py-20 px-4 sm:px-6 lg:px-8 border-b border-slate-100">
        <div className="mx-auto max-w-7xl">
          <div className="grid grid-cols-1 lg:grid-cols-12 gap-12 items-center">
            
            {/* Left Hero Content */}
            <div className="lg:col-span-7 space-y-6">
              
              <div className="inline-flex items-center space-x-2 rounded-full border border-blue-200 bg-blue-50/80 px-3.5 py-1 text-xs font-semibold text-blue-700">
                <Sparkles className="h-3.5 w-3.5 text-blue-600" />
                <span>Verified Non-Profit & Financial Integrity Network</span>
              </div>

              <h1 className="text-4xl sm:text-5xl lg:text-6xl font-extrabold tracking-tight text-slate-900 leading-[1.15]">
                Make every <br />
                <span className="text-blue-600">contribution count.</span>
              </h1>

              <p className="text-base sm:text-lg text-slate-600 leading-relaxed max-w-2xl">
                Discover verified NGOs, understand their impact, and support causes with confidence. Every record is compliance-checked and backed by cryptographic transparency.
              </p>

              <div className="flex flex-wrap items-center gap-4 pt-2">
                <Link
                  href="/explore"
                  className="flex items-center space-x-2 rounded-xl bg-blue-600 hover:bg-blue-700 px-6 py-3.5 text-sm font-bold text-white shadow-sm shadow-blue-600/20 hover:shadow-md transition-all"
                >
                  <HeartHandshake className="h-4 w-4" />
                  <span>Explore NGOs</span>
                </Link>

                <a
                  href="#how-it-works"
                  className="flex items-center space-x-2 rounded-xl border border-slate-300 bg-white hover:bg-slate-50 px-6 py-3.5 text-sm font-semibold text-slate-700 transition-all"
                >
                  <span>How it works</span>
                  <ChevronRight className="h-4 w-4 text-slate-400" />
                </a>
              </div>

              {/* Trust Indicators */}
              <div className="pt-6 flex flex-wrap items-center gap-6 text-xs text-slate-500 border-t border-slate-200/70">
                <div className="flex items-center space-x-2">
                  <CheckCircle2 className="h-4 w-4 text-emerald-600" />
                  <span className="font-medium text-slate-700">100% Compliance Checked</span>
                </div>
                <div className="flex items-center space-x-2">
                  <Lock className="h-4 w-4 text-blue-600" />
                  <span className="font-medium text-slate-700">SHA-256 Ledger Audit</span>
                </div>
              </div>

            </div>

            {/* Right Graphic Feature Card */}
            <div className="lg:col-span-5">
              <div className="relative mx-auto max-w-md lg:max-w-none">
                
                <div className="relative rounded-2xl border border-slate-200 bg-white p-6 shadow-sm space-y-5">
                  
                  <div className="flex items-center justify-between border-b border-slate-100 pb-4">
                    <div className="flex items-center space-x-3">
                      <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-blue-600 text-white font-bold text-base shadow-xs">
                        HO
                      </div>
                      <div>
                        <h4 className="text-sm font-bold text-slate-900">Hope Foundation</h4>
                        <span className="text-xs text-slate-500">Verified NGO • Reg #NGO-8821</span>
                      </div>
                    </div>
                    <span className="inline-flex items-center space-x-1 rounded-full bg-emerald-50 px-2.5 py-1 text-[11px] font-bold text-emerald-700 border border-emerald-200">
                      <CheckCircle2 className="h-3 w-3 text-emerald-600" />
                      <span>Verified</span>
                    </span>
                  </div>

                  <div className="rounded-xl bg-slate-50 p-4 border border-slate-100 space-y-3">
                    <div className="flex justify-between items-center text-xs">
                      <span className="font-medium text-slate-600">Financial Transparency Score</span>
                      <span className="font-bold text-emerald-600">96 / 100</span>
                    </div>
                    <div className="h-2 w-full rounded-full bg-slate-200 overflow-hidden">
                      <div className="h-full bg-emerald-500 rounded-full w-[96%]"></div>
                    </div>
                    <div className="grid grid-cols-2 gap-2 text-xs pt-1">
                      <div>
                        <span className="text-slate-400 block text-[10px] uppercase font-semibold">Verified Funds</span>
                        <span className="font-bold text-slate-900 text-sm">₹1,24,500</span>
                      </div>
                      <div>
                        <span className="text-slate-400 block text-[10px] uppercase font-semibold">Beneficiaries</span>
                        <span className="font-bold text-slate-900 text-sm">3,420 Lives</span>
                      </div>
                    </div>
                  </div>

                  <div className="flex items-center justify-between rounded-xl bg-blue-50/70 p-3 text-xs text-blue-900 border border-blue-100">
                    <div className="flex items-center space-x-2">
                      <Database className="h-4 w-4 text-blue-600 shrink-0" />
                      <span className="font-mono text-[11px]">Ledger Block #8492 Verified</span>
                    </div>
                    <span className="font-semibold text-[10px] uppercase text-blue-700 bg-blue-200/60 px-2 py-0.5 rounded">SHA-256</span>
                  </div>

                </div>

                {/* Floating Active Badge */}
                <div className="absolute -bottom-3 -left-3 rounded-xl bg-emerald-600 text-white px-3.5 py-2 shadow-md flex items-center space-x-2 text-xs font-bold">
                  <ShieldCheck className="h-4 w-4" />
                  <span>AI Fraud Engine Active</span>
                </div>

              </div>
            </div>

          </div>
        </div>
      </section>

      {/* 2. TRUST / PLATFORM VALUE SECTION */}
      <section className="w-full py-16 sm:py-20 px-4 sm:px-6 lg:px-8 bg-slate-50/80 border-b border-slate-100">
        <div className="mx-auto max-w-7xl space-y-12">
          
          <div className="text-center max-w-2xl mx-auto space-y-2">
            <h2 className="text-2xl sm:text-3xl font-bold text-slate-900 tracking-tight">Why trust NGO Impact Commons?</h2>
            <p className="text-sm text-slate-600">Built to ensure maximum transparency, compliance, and donor confidence.</p>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
            
            <div className="rounded-2xl bg-white p-6 border border-slate-200/80 shadow-xs hover:shadow-md hover:border-blue-300 transition-all space-y-3 flex flex-col justify-between">
              <div className="space-y-3">
                <div className="h-10 w-10 rounded-xl bg-emerald-50 text-emerald-600 flex items-center justify-center border border-emerald-100">
                  <ShieldCheck className="h-5 w-5" />
                </div>
                <h3 className="text-base font-bold text-slate-900">Verified NGOs</h3>
                <p className="text-xs text-slate-600 leading-relaxed">
                  Organizations undergo thorough registration & compliance verification before appearing as verified.
                </p>
              </div>
            </div>

            <div className="rounded-2xl bg-white p-6 border border-slate-200/80 shadow-xs hover:shadow-md hover:border-blue-300 transition-all space-y-3 flex flex-col justify-between">
              <div className="space-y-3">
                <div className="h-10 w-10 rounded-xl bg-blue-50 text-blue-600 flex items-center justify-center border border-blue-100">
                  <FileText className="h-5 w-5" />
                </div>
                <h3 className="text-base font-bold text-slate-900">Transparent Impact</h3>
                <p className="text-xs text-slate-600 leading-relaxed">
                  See real project outcomes, verified impact records, and official supporting financial documents.
                </p>
              </div>
            </div>

            <div className="rounded-2xl bg-white p-6 border border-slate-200/80 shadow-xs hover:shadow-md hover:border-blue-300 transition-all space-y-3 flex flex-col justify-between">
              <div className="space-y-3">
                <div className="h-10 w-10 rounded-xl bg-purple-50 text-purple-600 flex items-center justify-center border border-purple-100">
                  <Lock className="h-5 w-5" />
                </div>
                <h3 className="text-base font-bold text-slate-900">Secure Donations</h3>
                <p className="text-xs text-slate-600 leading-relaxed">
                  Donation records are securely tracked and cryptographically immutably logged on the ledger.
                </p>
              </div>
            </div>

            <div className="rounded-2xl bg-white p-6 border border-slate-200/80 shadow-xs hover:shadow-md hover:border-blue-300 transition-all space-y-3 flex flex-col justify-between">
              <div className="space-y-3">
                <div className="h-10 w-10 rounded-xl bg-amber-50 text-amber-600 flex items-center justify-center border border-amber-100">
                  <Database className="h-5 w-5" />
                </div>
                <h3 className="text-base font-bold text-slate-900">Auditability</h3>
                <p className="text-xs text-slate-600 leading-relaxed">
                  Important platform activities and fund allocations can be independently audited and traced anytime.
                </p>
              </div>
            </div>

          </div>

        </div>
      </section>

      {/* 3. VERIFIED ORGANISATIONS SECTION */}
      <section className="w-full py-16 sm:py-20 px-4 sm:px-6 lg:px-8 bg-white border-b border-slate-100">
        <div className="mx-auto max-w-7xl space-y-8">
          
          <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-4">
            <div>
              <div className="flex items-center space-x-2 text-blue-600 font-bold text-xs uppercase tracking-wider mb-1">
                <Building2 className="h-4 w-4" />
                <span>Audited Non-Profits</span>
              </div>
              <h2 className="text-2xl sm:text-3xl font-bold text-slate-900 tracking-tight">Verified organisations</h2>
              <p className="text-sm text-slate-600 mt-1">Explore compliance-checked non-profits making a real difference.</p>
            </div>

            <Link
              href="/explore"
              className="inline-flex items-center space-x-1.5 text-xs font-bold text-blue-600 hover:text-blue-700"
            >
              <span>View all organisations</span>
              <ArrowRight className="h-4 w-4" />
            </Link>
          </div>

          {loading ? (
            <div className="text-center py-12 text-slate-400">
              <div className="inline-block h-6 w-6 animate-spin rounded-full border-2 border-blue-600 border-t-transparent mb-2"></div>
              <p className="text-xs">Loading verified NGO directory...</p>
            </div>
          ) : filteredNgos.length === 0 ? (
            <div className="rounded-2xl border border-slate-200 bg-slate-50 p-8 text-center text-slate-500">
              <p className="text-sm font-semibold">No verified NGOs found matching this cause category.</p>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {filteredNgos.slice(0, 6).map((ngo) => (
                <div 
                  key={ngo.id}
                  className="rounded-2xl border border-slate-200/80 bg-white p-6 shadow-xs hover:shadow-md hover:border-blue-300 transition-all flex flex-col justify-between space-y-5"
                >
                  <div className="space-y-4">
                    
                    <div className="flex items-start justify-between gap-3">
                      <div className="flex items-center space-x-3">
                        <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-blue-600 text-white font-extrabold text-sm shadow-xs">
                          {getInitials(ngo.org_name)}
                        </div>
                        <div>
                          <h3 className="text-base font-bold text-slate-900 leading-snug">
                            {ngo.org_name}
                          </h3>
                          <p className="text-xs text-slate-500">{ngo.address || 'India'}</p>
                        </div>
                      </div>

                      <span className="inline-flex items-center space-x-1 rounded-full bg-emerald-50 px-2.5 py-1 text-[11px] font-bold text-emerald-700 border border-emerald-200 shrink-0">
                        <CheckCircle2 className="h-3 w-3 text-emerald-600" />
                        <span>Verified</span>
                      </span>
                    </div>

                    <p className="text-xs text-slate-600 line-clamp-3 leading-relaxed">
                      {ngo.mission_statement || 'Dedicated to transparent social impact and community empowerment.'}
                    </p>

                    <div className="rounded-xl bg-slate-50 p-3.5 border border-slate-100 text-xs space-y-2">
                      <div className="flex justify-between items-center">
                        <span className="text-slate-500 text-[11px]">Transparency Score</span>
                        <span className="font-bold text-emerald-600">{ngo.transparency_score}%</span>
                      </div>
                      <div className="grid grid-cols-2 gap-2 pt-2 border-t border-slate-200/60 text-[11px]">
                        <div>
                          <span className="text-slate-400 block text-[10px] uppercase font-semibold">Total Raised</span>
                          <span className="font-bold text-slate-900">₹{ngo.total_donations_received.toLocaleString('en-IN')}</span>
                        </div>
                        <div>
                          <span className="text-slate-400 block text-[10px] uppercase font-semibold">Beneficiaries</span>
                          <span className="font-bold text-slate-900">{ngo.beneficiary_count.toLocaleString()}</span>
                        </div>
                      </div>
                    </div>

                  </div>

                  <div className="flex items-center space-x-2 pt-2 border-t border-slate-100">
                    <Link
                      href={`/ngo/${ngo.id}`}
                      className="w-1/2 text-center rounded-xl border border-slate-200 bg-slate-50 hover:bg-slate-100 py-2.5 text-xs font-semibold text-slate-700 transition-colors"
                    >
                      View impact
                    </Link>

                    <button
                      onClick={() => setSelectedNgo(ngo)}
                      className="w-1/2 rounded-xl bg-blue-600 hover:bg-blue-700 py-2.5 text-xs font-bold text-white shadow-xs shadow-blue-600/20 transition-all flex items-center justify-center space-x-1.5"
                    >
                      <HeartHandshake className="h-3.5 w-3.5" />
                      <span>Donate</span>
                    </button>
                  </div>

                </div>
              ))}
            </div>
          )}

        </div>
      </section>

      {/* 4. BROWSE BY CAUSE */}
      <section className="w-full py-16 sm:py-20 px-4 sm:px-6 lg:px-8 bg-slate-50/80 border-b border-slate-100">
        <div className="mx-auto max-w-7xl space-y-8">
          
          <div className="text-center max-w-2xl mx-auto space-y-2">
            <h2 className="text-2xl sm:text-3xl font-bold text-slate-900 tracking-tight">Browse by cause</h2>
            <p className="text-sm text-slate-600">Find non-profits and projects working in areas you care about most.</p>
          </div>

          <div className="flex flex-wrap justify-center gap-3 max-w-4xl mx-auto">
            {causes.map((c) => {
              const IconComp = c.icon;
              const isSelected = selectedCategory === c.name || (c.name === 'Other' && selectedCategory === 'All');
              return (
                <button
                  key={c.name}
                  onClick={() => setSelectedCategory(isSelected ? 'All' : c.name)}
                  className={`flex items-center space-x-2 rounded-full px-4.5 py-2.5 text-xs font-semibold border transition-all ${
                    isSelected
                      ? 'bg-blue-600 text-white border-blue-600 shadow-sm shadow-blue-600/20'
                      : 'bg-white text-slate-700 border-slate-200 hover:border-blue-300 hover:bg-blue-50/50'
                  }`}
                >
                  <IconComp className={`h-4 w-4 ${isSelected ? 'text-white' : 'text-blue-600'}`} />
                  <span>{c.name}</span>
                </button>
              );
            })}
          </div>

        </div>
      </section>

      {/* 5. RECENT IMPACT / RECENT WORK */}
      <section id="impact-gallery" className="w-full py-16 sm:py-20 px-4 sm:px-6 lg:px-8 bg-white border-b border-slate-100">
        <div className="mx-auto max-w-7xl space-y-8">
          
          <div className="flex flex-col sm:flex-row sm:items-end justify-between gap-4">
            <div>
              <div className="flex items-center space-x-2 text-emerald-600 font-bold text-xs uppercase tracking-wider mb-1">
                <Sparkles className="h-4 w-4" />
                <span>Verified Field Updates</span>
              </div>
              <h2 className="text-2xl sm:text-3xl font-bold text-slate-900 tracking-tight">Recent work</h2>
              <p className="text-sm text-slate-600 mt-1">Real impact stories and verified project completions funded by community support.</p>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {recentImpactWork.map((work) => {
              const IconComp = work.icon;
              return (
                <div 
                  key={work.id}
                  className="rounded-2xl border border-slate-200/80 bg-white overflow-hidden shadow-xs hover:shadow-md transition-all flex flex-col justify-between"
                >
                  <div>
                    {/* SVG Graphic Banner (No broken images!) */}
                    <div className={`h-40 w-full bg-gradient-to-br ${work.accentColor} p-5 relative flex flex-col justify-between text-white overflow-hidden`}>
                      <div className="absolute -right-6 -bottom-6 opacity-15">
                        <IconComp className="h-32 w-32" />
                      </div>
                      
                      <div className="flex justify-between items-start z-10">
                        <span className="rounded-full bg-white/20 backdrop-blur-md px-3 py-1 text-[11px] font-bold text-white border border-white/30">
                          {work.category}
                        </span>
                        <span className="flex items-center space-x-1 text-[10px] font-mono bg-black/20 px-2 py-1 rounded text-white">
                          <CheckCircle2 className="h-3 w-3 text-emerald-300" />
                          <span>Audit Verified</span>
                        </span>
                      </div>

                      <div className="z-10 flex items-center space-x-2">
                        <IconComp className="h-5 w-5 text-white" />
                        <span className="text-xs font-semibold tracking-wide text-white/90">Impact Record</span>
                      </div>
                    </div>

                    <div className="p-6 space-y-3">
                      <h3 className="text-base font-bold text-slate-900 leading-snug">
                        {work.title}
                      </h3>
                      
                      <p className="text-xs text-slate-600 leading-relaxed">
                        {work.description}
                      </p>
                    </div>
                  </div>

                  <div className="px-6 pb-6 pt-2 border-t border-slate-100 flex items-center justify-between text-xs text-slate-500 font-medium">
                    <span className="font-semibold text-slate-700">{work.ngoName}</span>
                    <span>{work.date}</span>
                  </div>
                </div>
              );
            })}
          </div>

        </div>
      </section>

      {/* 6. TRANSPARENCY / IMPACT SECTION */}
      <section className="w-full py-16 sm:py-20 px-4 sm:px-6 lg:px-8 bg-slate-50/80 border-b border-slate-100">
        <div className="mx-auto max-w-7xl">
          
          {/* Integrated Light-Themed Highlight Container */}
          <div className="rounded-3xl border border-slate-200 bg-white p-8 sm:p-12 shadow-sm space-y-10">
            
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-10 items-center">
              
              <div className="lg:col-span-6 space-y-6">
                <div className="inline-flex items-center space-x-2 rounded-full bg-blue-50 border border-blue-200 px-3.5 py-1 text-xs font-semibold text-blue-700">
                  <Lock className="h-3.5 w-3.5 text-blue-600" />
                  <span>Immutable Transparency Standard</span>
                </div>

                <h2 className="text-3xl sm:text-4xl font-extrabold text-slate-900 tracking-tight leading-tight">
                  Know where your <br />
                  <span className="text-blue-600">contribution goes.</span>
                </h2>

                <p className="text-sm text-slate-600 leading-relaxed">
                  NGO Impact Commons connects donors and audited non-profits through an open transparency standard. Every transaction is verifiable, preventing financial mismanagement and building long-term trust.
                </p>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
                  <div className="flex items-start space-x-3 bg-slate-50 p-4 rounded-xl border border-slate-100">
                    <CheckCircle2 className="h-5 w-5 text-emerald-600 shrink-0 mt-0.5" />
                    <div>
                      <span className="font-bold text-slate-900 block">NGO Audits</span>
                      <span className="text-slate-500 text-[11px]">Tax IDs & filings checked.</span>
                    </div>
                  </div>

                  <div className="flex items-start space-x-3 bg-slate-50 p-4 rounded-xl border border-slate-100">
                    <Database className="h-5 w-5 text-blue-600 shrink-0 mt-0.5" />
                    <div>
                      <span className="font-bold text-slate-900 block">SHA-256 Ledger</span>
                      <span className="text-slate-500 text-[11px]">Blocks tied to hash chains.</span>
                    </div>
                  </div>

                  <div className="flex items-start space-x-3 bg-slate-50 p-4 rounded-xl border border-slate-100">
                    <Sparkles className="h-5 w-5 text-purple-600 shrink-0 mt-0.5" />
                    <div>
                      <span className="font-bold text-slate-900 block">AI Fraud Engine</span>
                      <span className="text-slate-500 text-[11px]">Scans duplicate patterns.</span>
                    </div>
                  </div>

                  <div className="flex items-start space-x-3 bg-slate-50 p-4 rounded-xl border border-slate-100">
                    <FileText className="h-5 w-5 text-amber-600 shrink-0 mt-0.5" />
                    <div>
                      <span className="font-bold text-slate-900 block">Open Documents</span>
                      <span className="text-slate-500 text-[11px]">Access annual reports.</span>
                    </div>
                  </div>
                </div>

              </div>

              {/* Platform Live Stats */}
              <div className="lg:col-span-6">
                <div className="grid grid-cols-2 gap-4">
                  <div className="bg-slate-50 rounded-2xl p-6 border border-slate-200/80 text-center space-y-1">
                    <Building2 className="h-7 w-7 text-blue-600 mx-auto mb-2" />
                    <span className="text-3xl font-extrabold text-slate-900 block">{stats?.approved_ngos_count || 2}</span>
                    <span className="text-xs text-slate-500 font-semibold uppercase tracking-wider">Approved NGOs</span>
                  </div>

                  <div className="bg-slate-50 rounded-2xl p-6 border border-slate-200/80 text-center space-y-1">
                    <TrendingUp className="h-7 w-7 text-emerald-600 mx-auto mb-2" />
                    <span className="text-3xl font-extrabold text-emerald-600 block">
                      ₹{(stats?.total_funds_raised || 0).toLocaleString('en-IN', { minimumFractionDigits: 0 })}
                    </span>
                    <span className="text-xs text-slate-500 font-semibold uppercase tracking-wider">Verified Funds</span>
                  </div>

                  <div className="bg-slate-50 rounded-2xl p-6 border border-slate-200/80 text-center space-y-1">
                    <Users className="h-7 w-7 text-purple-600 mx-auto mb-2" />
                    <span className="text-3xl font-extrabold text-slate-900 block">
                      {(stats?.total_beneficiaries_impacted || 0).toLocaleString()}
                    </span>
                    <span className="text-xs text-slate-500 font-semibold uppercase tracking-wider">Lives Impacted</span>
                  </div>

                  <div className="bg-slate-50 rounded-2xl p-6 border border-slate-200/80 text-center space-y-1">
                    <Lock className="h-7 w-7 text-amber-600 mx-auto mb-2" />
                    <span className="text-3xl font-extrabold text-slate-900 block">{stats?.blockchain_ledger_blocks || 0}</span>
                    <span className="text-xs text-slate-500 font-semibold uppercase tracking-wider">Ledger Blocks</span>
                  </div>
                </div>
              </div>

            </div>

          </div>

        </div>
      </section>

      {/* 7. HOW IT WORKS */}
      <section id="how-it-works" className="w-full py-16 sm:py-20 px-4 sm:px-6 lg:px-8 bg-white border-b border-slate-100">
        <div className="mx-auto max-w-7xl space-y-12">
          
          <div className="text-center max-w-2xl mx-auto space-y-2">
            <h2 className="text-2xl sm:text-3xl font-bold text-slate-900 tracking-tight">How it works</h2>
            <p className="text-sm text-slate-600">Simple 4-step process for transparent social giving.</p>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
            
            <div className="rounded-2xl bg-slate-50 p-6 border border-slate-200/80 shadow-xs space-y-3 flex flex-col justify-between">
              <div>
                <span className="text-3xl font-black text-blue-600/30 font-mono block mb-1">01</span>
                <h3 className="text-base font-bold text-slate-900">Discover</h3>
                <p className="text-xs text-slate-600 leading-relaxed mt-2">
                  Find non-profits and field projects based on your preferred cause categories.
                </p>
              </div>
            </div>

            <div className="rounded-2xl bg-slate-50 p-6 border border-slate-200/80 shadow-xs space-y-3 flex flex-col justify-between">
              <div>
                <span className="text-3xl font-black text-blue-600/30 font-mono block mb-1">02</span>
                <h3 className="text-base font-bold text-slate-900">Verify</h3>
                <p className="text-xs text-slate-600 leading-relaxed mt-2">
                  Review NGO information, legal registration documents, and transparency scores.
                </p>
              </div>
            </div>

            <div className="rounded-2xl bg-slate-50 p-6 border border-slate-200/80 shadow-xs space-y-3 flex flex-col justify-between">
              <div>
                <span className="text-3xl font-black text-blue-600/30 font-mono block mb-1">03</span>
                <h3 className="text-base font-bold text-slate-900">Contribute</h3>
                <p className="text-xs text-slate-600 leading-relaxed mt-2">
                  Donate securely to verified causes with direct tracking on the platform.
                </p>
              </div>
            </div>

            <div className="rounded-2xl bg-slate-50 p-6 border border-slate-200/80 shadow-xs space-y-3 flex flex-col justify-between">
              <div>
                <span className="text-3xl font-black text-blue-600/30 font-mono block mb-1">04</span>
                <h3 className="text-base font-bold text-slate-900">Track Impact</h3>
                <p className="text-xs text-slate-600 leading-relaxed mt-2">
                  View project updates, verified beneficiary metrics, and immutable ledger records.
                </p>
              </div>
            </div>

          </div>

        </div>
      </section>

      {/* 8. CTA SECTION */}
      <section className="w-full py-16 sm:py-20 px-4 sm:px-6 lg:px-8 bg-slate-50/80">
        <div className="mx-auto max-w-7xl">
          
          <div className="rounded-3xl bg-slate-900 text-white p-8 sm:p-14 text-center space-y-6 shadow-md relative overflow-hidden">
            <div className="absolute top-0 right-0 -mt-12 -mr-12 h-64 w-64 rounded-full bg-blue-600/20 blur-3xl"></div>
            
            <h2 className="text-3xl sm:text-4xl font-extrabold tracking-tight max-w-2xl mx-auto leading-tight text-white">
              Support meaningful change with confidence.
            </h2>

            <p className="text-slate-300 text-sm sm:text-base max-w-xl mx-auto leading-relaxed">
              Join donors and audited non-profits working together to build transparent, accountable social impact.
            </p>

            <div className="flex flex-wrap justify-center gap-4 pt-2">
              <Link
                href="/explore"
                className="rounded-xl bg-blue-600 hover:bg-blue-700 px-6 py-3.5 text-xs font-bold text-white shadow-sm shadow-blue-600/30 transition-all"
              >
                Explore NGOs
              </Link>
              
              <Link
                href="/register?role=NGO"
                className="rounded-xl border border-slate-700 bg-slate-800 hover:bg-slate-750 px-6 py-3.5 text-xs font-bold text-white transition-all"
              >
                Register as an NGO
              </Link>
            </div>

          </div>

        </div>
      </section>

      {/* Donation Modal */}
      {selectedNgo && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/60 backdrop-blur-sm p-4">
          <div className="w-full max-w-lg rounded-2xl bg-white p-6 shadow-2xl space-y-5 border border-slate-100 text-slate-900">
            
            {donationSuccess ? (
              <div className="text-center space-y-4 py-4">
                <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-full bg-emerald-100 text-emerald-600 border border-emerald-200">
                  <CheckCircle2 className="h-8 w-8" />
                </div>
                <h3 className="text-xl font-bold text-slate-900">Donation Recorded & Ledger Blocked!</h3>
                <p className="text-xs text-slate-600">
                  Thank you! Your donation of <span className="font-bold text-blue-600">₹{donationSuccess.amount?.toLocaleString('en-IN')} {donationSuccess.currency}</span> to <span className="font-bold text-slate-900">{donationSuccess.ngo_name}</span> has been logged on the SHA-256 ledger.
                </p>

                <div className="bg-slate-50 p-3 rounded-xl border border-slate-200 text-left font-mono text-[11px] space-y-1">
                  <p className="text-slate-500">Cryptographic Tx Hash:</p>
                  <p className="text-blue-600 break-all">{donationSuccess.transaction_hash}</p>
                </div>

                <button
                  onClick={() => {
                    setSelectedNgo(null);
                    setDonationSuccess(null);
                  }}
                  className="w-full rounded-xl bg-blue-600 py-3 text-xs font-bold text-white hover:bg-blue-700"
                >
                  Done
                </button>
              </div>
            ) : (
              <form onSubmit={handleDonateSubmit} className="space-y-4">
                <div className="flex justify-between items-start border-b border-slate-100 pb-3">
                  <div>
                    <span className="text-[10px] font-bold text-blue-600 uppercase tracking-wider">Verified NGO Donation</span>
                    <h3 className="text-lg font-bold text-slate-900">{selectedNgo.org_name}</h3>
                  </div>
                  <button
                    type="button"
                    onClick={() => setSelectedNgo(null)}
                    className="text-slate-400 hover:text-slate-700 text-lg font-bold"
                  >
                    ✕
                  </button>
                </div>

                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-2">Select Donation Amount (INR)</label>
                  <div className="grid grid-cols-4 gap-2">
                    {[500, 1000, 2500, 5000].map((amt) => (
                      <button
                        key={amt}
                        type="button"
                        onClick={() => {
                          setDonationAmount(amt);
                          setCustomAmount('');
                        }}
                        className={`rounded-xl py-2.5 text-xs font-bold transition-all ${
                          donationAmount === amt && !customAmount
                            ? 'bg-blue-600 text-white border border-blue-600 shadow-xs'
                            : 'border border-slate-200 bg-slate-50 text-slate-700 hover:border-blue-300'
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
                  <label className="block text-xs font-semibold text-slate-700 mb-1">Impact Message (Optional)</label>
                  <textarea
                    rows={2}
                    value={donorMsg}
                    onChange={(e) => setDonorMsg(e.target.value)}
                    placeholder="Write a message of encouragement..."
                    className="w-full rounded-xl border border-slate-200 bg-slate-50 px-3.5 py-2 text-xs text-slate-900 placeholder-slate-400 focus:border-blue-500 focus:bg-white focus:outline-none"
                  />
                </div>

                <div className="bg-blue-50 p-3 rounded-xl border border-blue-100 text-[11px] text-blue-900 flex items-center gap-2">
                  <Lock className="h-4 w-4 text-blue-600 flex-shrink-0" />
                  <span>This transaction will generate a SHA-256 block hash for public auditability.</span>
                </div>

                <div className="flex space-x-2 pt-2">
                  <button
                    type="button"
                    onClick={() => setSelectedNgo(null)}
                    className="w-1/3 rounded-xl border border-slate-200 bg-white py-3 text-xs font-semibold text-slate-600 hover:bg-slate-50"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    disabled={isSubmitting}
                    className="w-2/3 rounded-xl bg-blue-600 py-3 text-xs font-bold text-white hover:bg-blue-700 disabled:opacity-50 shadow-xs shadow-blue-600/20"
                  >
                    {isSubmitting ? 'Recording on Ledger...' : 'Confirm Verified Donation'}
                  </button>
                </div>
              </form>
            )}

          </div>
        </div>
      )}

    </div>
  );
}

export default function LandingPage() {
  return (
    <Suspense fallback={<div className="flex min-h-screen items-center justify-center text-slate-500 text-sm">Loading NGO Impact Commons...</div>}>
      <LandingContent />
    </Suspense>
  );
}
