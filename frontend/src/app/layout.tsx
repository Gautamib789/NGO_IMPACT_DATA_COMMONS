import './globals.css';
import React from 'react';
import Link from 'next/link';
import { AuthProvider } from '@/context/AuthContext';
import { Navbar } from '@/components/Navbar';
import { AiChatbotWindow } from '@/components/AiChatbotWindow';
import { ShieldCheck, Heart, Sparkles, ExternalLink } from 'lucide-react';

export const metadata = {
  title: 'NGO Impact Commons | Verified Philanthropy Platform',
  description: 'Discover verified NGOs, understand their impact, and support causes with confidence.',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="scroll-smooth">
      <body className="bg-slate-50 text-slate-900 min-h-screen flex flex-col antialiased selection:bg-blue-500 selection:text-white font-sans">
        <AuthProvider>
          <Navbar />
          <main className="flex-1 w-full bg-slate-50">
            {children}
          </main>
          <AiChatbotWindow />
          <footer className="border-t border-slate-800 bg-slate-950 text-slate-400 text-sm py-12 px-4 sm:px-6 lg:px-8">
            <div className="mx-auto max-w-7xl space-y-10">
              <div className="grid grid-cols-1 md:grid-cols-4 gap-8 pb-10 border-b border-slate-850">
                {/* Brand */}
                <div className="space-y-3.5 md:col-span-1">
                  <div className="flex items-center space-x-2.5">
                    <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-blue-600 text-white font-black text-sm shadow-md shadow-blue-500/20">
                      NI
                    </div>
                    <span className="text-base font-bold text-white tracking-tight">
                      NGO Impact <span className="text-blue-400">Commons</span>
                    </span>
                  </div>
                  <p className="text-xs text-slate-400 leading-relaxed">
                    Connecting donors with compliance-audited non-profits to make every contribution count.
                  </p>
                </div>

                {/* Navigation */}
                <div>
                  <h4 className="text-xs font-bold uppercase tracking-wider text-slate-200 mb-3.5">Navigation</h4>
                  <ul className="space-y-2.5 text-xs">
                    <li><Link href="/explore" className="hover:text-blue-400 transition-colors">Find NGOs</Link></li>
                    <li><Link href="/explore#impact-gallery" className="hover:text-blue-400 transition-colors">Impact gallery</Link></li>
                    <li><Link href="/ledger" className="hover:text-blue-400 transition-colors">Fund records</Link></li>
                    <li><Link href="/explore#report-concern" className="hover:text-blue-400 transition-colors">Report a concern</Link></li>
                  </ul>
                </div>

                {/* Account */}
                <div>
                  <h4 className="text-xs font-bold uppercase tracking-wider text-slate-200 mb-3.5">Account</h4>
                  <ul className="space-y-2.5 text-xs">
                    <li><Link href="/login" className="hover:text-blue-400 transition-colors">Sign in</Link></li>
                    <li><Link href="/register" className="hover:text-blue-400 transition-colors">Register</Link></li>
                    <li><Link href="/register?role=NGO" className="hover:text-blue-400 transition-colors">Register as an NGO</Link></li>
                  </ul>
                </div>

                {/* Platform */}
                <div>
                  <h4 className="text-xs font-bold uppercase tracking-wider text-slate-200 mb-3.5">Platform</h4>
                  <ul className="space-y-2.5 text-xs">
                    <li><Link href="/ledger" className="hover:text-blue-400 transition-colors">Transparency</Link></li>
                    <li><span className="text-slate-400">Security & Ledger Verification</span></li>
                    <li><span className="text-slate-400">About NGO Impact Commons</span></li>
                  </ul>
                </div>
              </div>

              {/* Bottom Copyright */}
              <div className="flex flex-col sm:flex-row justify-between items-center text-xs text-slate-500 gap-4">
                <p>© 2026 NGO Impact Commons. Verified Philanthropy Platform.</p>
                <div className="flex items-center space-x-2 text-emerald-400 text-[11px] font-mono bg-slate-900 px-3.5 py-1.5 rounded-full border border-slate-800 shadow-inner">
                  <span className="relative flex h-2 w-2">
                    <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
                    <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
                  </span>
                  <span>SHA-256 Cryptographic Ledger Online</span>
                </div>
              </div>
            </div>
          </footer>
        </AuthProvider>
      </body>
    </html>
  );
}
