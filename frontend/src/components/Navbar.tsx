'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import { useAuth } from '@/context/AuthContext';
import { 
  Database, 
  LogOut, 
  HeartHandshake, 
  ShieldAlert, 
  Menu, 
  X, 
  Search, 
  AlertCircle,
  FileCheck,
  Building2,
  ShieldCheck,
  User as UserIcon
} from 'lucide-react';

export const Navbar: React.FC = () => {
  const { user, logout } = useAuth();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [showConcernModal, setShowConcernModal] = useState(false);
  const [concernMessage, setConcernMessage] = useState('');
  const [concernSubmitted, setConcernSubmitted] = useState(false);

  const handleReportSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!concernMessage.trim()) return;
    setConcernSubmitted(true);
    setTimeout(() => {
      setConcernSubmitted(false);
      setConcernMessage('');
      setShowConcernModal(false);
    }, 2500);
  };

  return (
    <>
      <header className="sticky top-0 z-40 w-full bg-white/90 backdrop-blur-md border-b border-slate-200/80 shadow-subtle transition-all">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-4 py-3 sm:px-6 lg:px-8">
          
          {/* Left: Brand Identity */}
          <Link href="/" className="flex items-center space-x-3 group">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-blue-600 text-white font-black text-sm shadow-md shadow-blue-500/20 group-hover:bg-blue-700 group-hover:scale-105 transition-all">
              NI
            </div>
            <div className="flex flex-col">
              <span className="text-base font-bold text-slate-900 tracking-tight leading-tight flex items-center gap-1">
                NGO Impact <span className="text-blue-600 font-extrabold">Commons</span>
              </span>
              <span className="text-[10px] font-bold text-slate-500 uppercase tracking-widest">
                Verified Philanthropy Platform
              </span>
            </div>
          </Link>

          {/* Center Navigation Links (Desktop) */}
          <nav className="hidden md:flex items-center space-x-7 text-xs font-semibold text-slate-600">
            <Link href="/explore" className="hover:text-blue-600 transition-colors flex items-center gap-1.5 py-1.5">
              <Search className="h-3.5 w-3.5 text-slate-400" />
              <span>Find NGOs</span>
            </Link>
            <Link href="/explore#impact-gallery" className="hover:text-blue-600 transition-colors flex items-center gap-1.5 py-1.5">
              <FileCheck className="h-3.5 w-3.5 text-slate-400" />
              <span>Impact gallery</span>
            </Link>
            <Link href="/ledger" className="hover:text-blue-600 transition-colors flex items-center gap-1.5 py-1.5">
              <Database className="h-3.5 w-3.5 text-blue-600" />
              <span>Fund records</span>
            </Link>
            <button 
              onClick={() => setShowConcernModal(true)}
              className="hover:text-rose-600 transition-colors flex items-center gap-1.5 text-slate-600 py-1.5 cursor-pointer"
            >
              <AlertCircle className="h-3.5 w-3.5 text-slate-400" />
              <span>Report a concern</span>
            </button>
          </nav>

          {/* Right Controls */}
          <div className="hidden md:flex items-center space-x-3">
            {user ? (
              <div className="flex items-center space-x-3 pl-3 border-l border-slate-200">
                <div className="flex flex-col items-end">
                  <span className="text-xs font-bold text-slate-900 leading-tight">{user.full_name}</span>
                  <span className={`text-[9px] px-2 py-0.5 rounded-full font-mono uppercase font-bold tracking-wider mt-0.5 ${
                    user.role === 'ADMIN' ? 'bg-amber-100 text-amber-800 border border-amber-300' :
                    user.role === 'NGO' ? 'bg-blue-100 text-blue-800 border border-blue-300' :
                    'bg-emerald-100 text-emerald-800 border border-emerald-300'
                  }`}>
                    {user.role}
                  </span>
                </div>

                {user.role === 'DONOR' && (
                  <Link href="/donor/dashboard" className="flex items-center space-x-1.5 rounded-xl bg-slate-100 px-3.5 py-2 text-xs font-bold text-slate-700 hover:bg-slate-200 transition-all">
                    <HeartHandshake className="h-3.5 w-3.5 text-blue-600" />
                    <span>Dashboard</span>
                  </Link>
                )}
                {user.role === 'NGO' && (
                  <Link href="/ngo/dashboard" className="flex items-center space-x-1.5 rounded-xl bg-blue-50 px-3.5 py-2 text-xs font-bold text-blue-700 hover:bg-blue-100 border border-blue-200/60 transition-all">
                    <Building2 className="h-3.5 w-3.5" />
                    <span>NGO Portal</span>
                  </Link>
                )}
                {user.role === 'ADMIN' && (
                  <Link href="/admin/dashboard" className="flex items-center space-x-1.5 rounded-xl bg-amber-50 px-3.5 py-2 text-xs font-bold text-amber-800 hover:bg-amber-100 border border-amber-200/60 transition-all">
                    <ShieldAlert className="h-3.5 w-3.5" />
                    <span>Admin Panel</span>
                  </Link>
                )}

                <button
                  onClick={logout}
                  className="flex items-center space-x-1.5 rounded-xl border border-slate-200 bg-white px-3.5 py-2 text-xs font-semibold text-slate-600 hover:bg-slate-50 hover:text-slate-900 transition-all shadow-2xs"
                >
                  <LogOut className="h-3.5 w-3.5" />
                  <span>Sign out</span>
                </button>
              </div>
            ) : (
              <div className="flex items-center space-x-2.5">
                <Link
                  href="/login"
                  className="rounded-xl border border-slate-200/90 bg-white px-4 py-2 text-xs font-semibold text-slate-700 hover:bg-slate-50 hover:text-blue-600 transition-all shadow-2xs"
                >
                  Sign in
                </Link>
                <Link
                  href="/register"
                  className="rounded-xl bg-blue-600 hover:bg-blue-700 px-4 py-2 text-xs font-bold text-white shadow-md shadow-blue-500/20 transition-all hover:scale-[1.02]"
                >
                  Register
                </Link>
              </div>
            )}
          </div>

          {/* Mobile Hamburger Button */}
          <div className="flex md:hidden items-center">
            <button
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="p-2 rounded-xl text-slate-600 hover:bg-slate-100 focus:outline-none"
            >
              {mobileMenuOpen ? <X className="h-6 w-6" /> : <Menu className="h-6 w-6" />}
            </button>
          </div>

        </div>

        {/* Mobile Navigation Drawer */}
        {mobileMenuOpen && (
          <div className="md:hidden border-t border-slate-200 bg-white px-4 pt-3 pb-6 space-y-3 shadow-lg">
            <Link
              href="/explore"
              onClick={() => setMobileMenuOpen(false)}
              className="block py-2 text-sm font-semibold text-slate-700 hover:text-blue-600"
            >
              Find NGOs
            </Link>
            <Link
              href="/explore#impact-gallery"
              onClick={() => setMobileMenuOpen(false)}
              className="block py-2 text-sm font-semibold text-slate-700 hover:text-blue-600"
            >
              Impact gallery
            </Link>
            <Link
              href="/ledger"
              onClick={() => setMobileMenuOpen(false)}
              className="block py-2 text-sm font-semibold text-slate-700 hover:text-blue-600"
            >
              Fund records
            </Link>
            <button
              onClick={() => {
                setMobileMenuOpen(false);
                setShowConcernModal(true);
              }}
              className="block w-full text-left py-2 text-sm font-semibold text-slate-700 hover:text-rose-600"
            >
              Report a concern
            </button>

            <div className="pt-3 border-t border-slate-100">
              {user ? (
                <div className="space-y-2">
                  <div className="text-xs font-bold text-slate-900">{user.full_name} ({user.role})</div>
                  <button
                    onClick={() => {
                      logout();
                      setMobileMenuOpen(false);
                    }}
                    className="w-full text-left py-2 text-sm font-semibold text-rose-600"
                  >
                    Sign out
                  </button>
                </div>
              ) : (
                <div className="flex flex-col space-y-2 pt-1">
                  <Link
                    href="/login"
                    onClick={() => setMobileMenuOpen(false)}
                    className="w-full text-center py-2.5 text-xs font-semibold text-slate-700 border border-slate-200 rounded-xl"
                  >
                    Sign in
                  </Link>
                  <Link
                    href="/register"
                    onClick={() => setMobileMenuOpen(false)}
                    className="w-full text-center py-2.5 text-xs font-bold text-white bg-blue-600 rounded-xl"
                  >
                    Register
                  </Link>
                </div>
              )}
            </div>
          </div>
        )}
      </header>

      {/* Report Concern Modal */}
      {showConcernModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/60 backdrop-blur-sm p-4 animate-in fade-in duration-200">
          <div className="w-full max-w-md rounded-2xl bg-white p-6 shadow-2xl space-y-4 border border-slate-100">
            <div className="flex justify-between items-center border-b border-slate-100 pb-3">
              <div className="flex items-center space-x-2 text-rose-600 font-bold">
                <AlertCircle className="h-5 w-5" />
                <span>Report a Concern</span>
              </div>
              <button
                onClick={() => setShowConcernModal(false)}
                className="text-slate-400 hover:text-slate-700 font-bold text-lg cursor-pointer"
              >
                ✕
              </button>
            </div>

            {concernSubmitted ? (
              <div className="text-center py-6 space-y-2">
                <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-emerald-100 text-emerald-600">
                  ✓
                </div>
                <h4 className="font-bold text-slate-900">Report Submitted</h4>
                <p className="text-xs text-slate-500">Thank you for helping maintain platform compliance. Our auditing team will review this report.</p>
              </div>
            ) : (
              <form onSubmit={handleReportSubmit} className="space-y-4">
                <p className="text-xs text-slate-600 leading-relaxed">
                  Notice financial anomalies or non-compliance? Submit an anonymous report to our AI & Compliance Auditing System.
                </p>
                <div>
                  <label className="block text-xs font-semibold text-slate-700 mb-1">Details / Organization Name</label>
                  <textarea
                    rows={3}
                    required
                    value={concernMessage}
                    onChange={(e) => setConcernMessage(e.target.value)}
                    placeholder="Describe your concern or specify the NGO registration number..."
                    className="w-full rounded-xl border border-slate-300 bg-slate-50 p-3 text-xs text-slate-900 focus:border-blue-500 focus:bg-white focus:outline-none transition-all"
                  />
                </div>
                <div className="flex space-x-2 pt-1">
                  <button
                    type="button"
                    onClick={() => setShowConcernModal(false)}
                    className="w-1/2 rounded-xl border border-slate-200 py-2.5 text-xs font-semibold text-slate-600 hover:bg-slate-50"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    className="w-1/2 rounded-xl bg-rose-600 py-2.5 text-xs font-bold text-white hover:bg-rose-700 shadow-md shadow-rose-600/20"
                  >
                    Submit Report
                  </button>
                </div>
              </form>
            )}
          </div>
        </div>
      )}
    </>
  );
};
