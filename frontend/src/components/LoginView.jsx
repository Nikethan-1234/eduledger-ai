import React, { useState } from 'react';
import { Shield, BookOpen, CheckSquare, UserCheck } from 'lucide-react';
import { API_BASE_URL } from '../config';

export default function LoginView({ onLogin }) {
  const [role, setRole] = useState('teacher');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleRoleSelect = (selectedRole) => {
    setRole(selectedRole);
  };

  const handleLoginSubmit = async () => {
    setLoading(true);
    setError('');
    try {
      const response = await fetch(`${API_BASE_URL}/api/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ role })
      });
      const data = await response.json();
      if (data.success) {
        onLogin(data.user);
      } else {
        setError(data.error || 'Failed to authenticate');
      }
    } catch (err) {
      setError('Backend connection failed. Make sure Flask server is running.');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-50 px-4 relative overflow-hidden">
      {/* Background gradients */}
      <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-emerald-500/5 rounded-full filter blur-[100px] pointer-events-none"></div>
      <div className="absolute bottom-1/4 right-1/4 w-96 h-96 bg-cyan-500/5 rounded-full filter blur-[100px] pointer-events-none"></div>

      <div className="w-full max-w-md glass-card rounded-2xl p-8 relative z-10 border border-slate-200">
        <div className="text-center mb-8">
          <div className="inline-flex p-3 rounded-full bg-emerald-50 border border-emerald-100 text-emerald-600 mb-3 shadow-md glow-active">
            <Shield className="w-8 h-8" />
          </div>
          <h1 className="text-3xl font-extrabold tracking-tight text-slate-900 mb-1">
            EduLedger <span className="text-gradient">AI</span>
          </h1>
          <p className="text-slate-500 text-sm">School Financial Management Demo Hub</p>
        </div>

        {error && (
          <div className="mb-6 p-4 bg-rose-50 border border-rose-100 rounded-lg text-rose-600 text-xs text-center">
            {error}
          </div>
        )}

        <div className="space-y-4 mb-8">
          <label className="text-xs font-semibold text-slate-500 uppercase tracking-wider block">
            Select Your Demo Role
          </label>
          
          {/* Role Cards */}
          <div className="grid grid-cols-1 gap-3">
            {[
              { id: 'teacher', title: 'Teacher (Sarah Jenkins)', desc: 'Upload expense receipts, review OCR, submit requests', icon: BookOpen },
              { id: 'approver', title: 'Approver / HOD (Marcus)', desc: 'Approve or edit pending expenses, view anomalies', icon: CheckSquare },
              { id: 'admin', title: 'Administrator', desc: 'Full permissions, dashboard analytics, forecasts, and AI Chat', icon: UserCheck }
            ].map((roleItem) => {
              const IconComp = roleItem.icon;
              const isSelected = role === roleItem.id;
              return (
                <div
                  key={roleItem.id}
                  onClick={() => handleRoleSelect(roleItem.id)}
                  className={`p-4 rounded-xl border cursor-pointer transition-all duration-200 flex items-start space-x-3 hover:bg-slate-50 ${
                    isSelected 
                      ? 'border-emerald-500 bg-emerald-50/60 shadow-[0_4px_20px_rgba(16,185,129,0.08)]' 
                      : 'border-slate-200 bg-white/60'
                  }`}
                >
                  <div className={`p-2 rounded-lg ${isSelected ? 'bg-emerald-100 text-emerald-700' : 'bg-slate-100 text-slate-500'}`}>
                    <IconComp className="w-5 h-5" />
                  </div>
                  <div className="flex-1">
                    <h3 className={`text-sm font-bold ${isSelected ? 'text-slate-900' : 'text-slate-700'}`}>
                      {roleItem.title}
                    </h3>
                    <p className="text-xs text-slate-500 mt-0.5">{roleItem.desc}</p>
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        <button
          onClick={handleLoginSubmit}
          disabled={loading}
          className="w-full py-3.5 bg-gradient-to-r from-emerald-500 to-teal-600 hover:from-emerald-400 hover:to-teal-500 text-white font-bold rounded-xl shadow-lg shadow-emerald-500/10 transition-all duration-200 flex items-center justify-center space-x-2 disabled:opacity-50"
        >
          {loading ? (
            <span className="w-5 h-5 border-2 border-white border-t-transparent rounded-full animate-spin"></span>
          ) : (
            <>
              <span>Enter Dashboard</span>
            </>
          )}
        </button>

        <div className="mt-6 text-center text-xs text-slate-400">
          EduLedger AI Demo Hub &bull; Powered by Anthropic Claude & ML
        </div>
      </div>
    </div>
  );
}
