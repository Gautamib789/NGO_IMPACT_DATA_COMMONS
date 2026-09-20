'use client';

import React, { useState } from 'react';
import { Bot, X, Send, Sparkles, RefreshCw } from 'lucide-react';
import { useAuth } from '@/context/AuthContext';

interface Message {
  sender: 'user' | 'bot';
  text: string;
  timestamp: string;
}

export const AiChatbotWindow: React.FC = () => {
  const [isOpen, setIsOpen] = useState(false);
  const [messages, setMessages] = useState<Message[]>([
    {
      sender: 'bot',
      text: 'Hello! I am your AI Transparency Assistant. Ask me anything about NGO verification, document auditing, SHA-256 blockchain ledger, or donation safety.',
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    }
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const { apiFetch } = useAuth();

  const handleSend = async (textToSend?: string) => {
    const query = textToSend || input;
    if (!query.trim() || loading) return;

    const userMsg: Message = {
      sender: 'user',
      text: query,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    };

    setMessages(prev => [...prev, userMsg]);
    if (!textToSend) setInput('');
    setLoading(true);

    try {
      const res = await apiFetch('/api/chat', {
        method: 'POST',
        body: JSON.stringify({ message: query }),
      });

      const botMsg: Message = {
        sender: 'bot',
        text: res.response,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      };
      setMessages(prev => [...prev, botMsg]);
    } catch (err: any) {
      setMessages(prev => [...prev, {
        sender: 'bot',
        text: 'Sorry, I encountered an issue retrieving the response. Please try again.',
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      }]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed bottom-6 right-6 z-50">
      {!isOpen && (
        <button
          onClick={() => setIsOpen(true)}
          className="flex items-center space-x-2.5 rounded-full bg-blue-600 hover:bg-blue-700 text-white shadow-xl shadow-blue-600/30 border border-blue-500/40 px-4 py-3 transition-all font-bold text-xs sm:text-sm hover:scale-105"
        >
          <Bot className="h-5 w-5 animate-pulse text-white" />
          <span>AI Transparency Assistant</span>
          <span className="flex h-2 w-2 rounded-full bg-emerald-400"></span>
        </button>
      )}

      {isOpen && (
        <div className="flex h-[480px] w-[350px] sm:w-[400px] flex-col rounded-2xl border border-slate-200 bg-white shadow-2xl">
          {/* Header */}
          <div className="flex items-center justify-between border-b border-slate-800 bg-slate-900 px-4 py-3.5 rounded-t-2xl text-white">
            <div className="flex items-center space-x-2.5">
              <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-blue-500/20 text-blue-400 border border-blue-400/30">
                <Sparkles className="h-4 w-4" />
              </div>
              <div>
                <h3 className="text-xs font-bold text-white leading-tight">AI Transparency Advisor</h3>
                <span className="text-[10px] text-emerald-400 font-mono">Auditing Engine Active</span>
              </div>
            </div>
            <button
              onClick={() => setIsOpen(false)}
              className="rounded-lg p-1 text-slate-400 hover:bg-slate-800 hover:text-white"
            >
              <X className="h-5 w-5" />
            </button>
          </div>

          {/* Messages Scroll Area */}
          <div className="flex-1 overflow-y-auto p-4 space-y-3 text-xs bg-slate-50">
            {messages.map((msg, i) => (
              <div
                key={i}
                className={`flex ${msg.sender === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                <div className={`max-w-[85%] rounded-2xl p-3 ${
                  msg.sender === 'user'
                    ? 'bg-blue-600 text-white rounded-br-none shadow-sm'
                    : 'bg-white border border-slate-200 text-slate-800 rounded-bl-none shadow-xs'
                }`}>
                  <p className="whitespace-pre-wrap leading-relaxed text-xs">{msg.text}</p>
                  <span className={`block text-[9px] mt-1 ${msg.sender === 'user' ? 'text-blue-100' : 'text-slate-400'} text-right`}>
                    {msg.timestamp}
                  </span>
                </div>
              </div>
            ))}

            {loading && (
              <div className="flex items-center space-x-2 text-slate-500 text-xs italic">
                <RefreshCw className="h-3.5 w-3.5 animate-spin text-blue-600" />
                <span>Analyzing compliance & ledger metrics...</span>
              </div>
            )}
          </div>

          {/* Quick Prompts */}
          <div className="border-t border-slate-200 px-3 py-2 bg-white flex space-x-1.5 overflow-x-auto no-scrollbar">
            <button
              onClick={() => handleSend("How are transparency scores computed?")}
              className="whitespace-nowrap rounded-full border border-slate-200 bg-slate-50 px-3 py-1 text-[10px] text-slate-600 hover:border-blue-500 hover:bg-blue-50 hover:text-blue-700"
            >
              📊 Transparency Score
            </button>
            <button
              onClick={() => handleSend("How does the SHA-256 blockchain ledger work?")}
              className="whitespace-nowrap rounded-full border border-slate-200 bg-slate-50 px-3 py-1 text-[10px] text-slate-600 hover:border-blue-500 hover:bg-blue-50 hover:text-blue-700"
            >
              🔗 SHA-256 Ledger
            </button>
            <button
              onClick={() => handleSend("How does AI Fraud Detection scan NGOs?")}
              className="whitespace-nowrap rounded-full border border-slate-200 bg-slate-50 px-3 py-1 text-[10px] text-slate-600 hover:border-blue-500 hover:bg-blue-50 hover:text-blue-700"
            >
              🛡️ Fraud Detection
            </button>
          </div>

          {/* Input Box */}
          <div className="border-t border-slate-200 p-3 bg-white rounded-b-2xl">
            <form
              onSubmit={(e) => {
                e.preventDefault();
                handleSend();
              }}
              className="flex items-center space-x-2"
            >
              <input
                type="text"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder="Ask about NGO auditing & blockchain..."
                className="flex-1 rounded-xl border border-slate-200 bg-slate-50 px-3.5 py-2 text-xs text-slate-900 placeholder-slate-400 focus:border-blue-500 focus:bg-white focus:outline-none"
              />
              <button
                type="submit"
                disabled={loading || !input.trim()}
                className="flex h-8 w-8 items-center justify-center rounded-xl bg-blue-600 text-white hover:bg-blue-700 disabled:opacity-50 transition-colors shadow-sm"
              >
                <Send className="h-4 w-4" />
              </button>
            </form>
          </div>

        </div>
      )}
    </div>
  );
};
