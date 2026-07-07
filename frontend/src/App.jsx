import React, { useState } from 'react';
import LoginView from './components/LoginView';
import DashboardView from './components/DashboardView';
import ExpenseView from './components/ExpenseView';
import ApprovalView from './components/ApprovalView';
import AssistantView from './components/AssistantView';
import { Landmark, FileText, CheckSquare, MessageSquareCode, LogOut, User } from 'lucide-react';

export default function App() {
  const [currentUser, setCurrentUser] = useState(null);
  const [activeTab, setActiveTab] = useState('dashboard');
  const [transactionTrigger, setTransactionTrigger] = useState(0);

  const handleLogin = (user) => {
    setCurrentUser(user);
    // Direct users to relevant tabs based on role by default
    if (user.role === 'teacher') {
      setActiveTab('expenses');
    } else if (user.role === 'approver') {
      setActiveTab('approvals');
    } else {
      setActiveTab('dashboard');
    }
  };

  const handleLogout = () => {
    setCurrentUser(null);
  };

  // Signal dashboard to reload stats & charts
  const triggerTransactionSync = () => {
    setTransactionTrigger(prev => prev + 1);
  };

  if (!currentUser) {
    return <LoginView onLogin={handleLogin} />;
  }

  // Determine role-based view visibility
  const isTeacher = currentUser.role === 'teacher';
  const isApprover = currentUser.role === 'approver';
  const isAdmin = currentUser.role === 'admin';

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col">
      {/* Top Navbar */}
      <nav className="glass-card sticky top-0 z-40 border-b border-slate-200/80 px-6 py-4 flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-emerald-500 to-teal-600 flex items-center justify-center font-black text-white text-base shadow-md shadow-emerald-500/5">
            EL
          </div>
          <div>
            <h1 className="text-base font-extrabold text-slate-900 flex items-center">
              EduLedger <span className="text-gradient ml-1">AI</span>
            </h1>
            <span className="text-[10px] text-slate-400 font-bold uppercase tracking-wider block">Unified Financial Spine</span>
          </div>
        </div>

        {/* Desktop Tab Selector */}
        <div className="hidden md:flex items-center space-x-1.5">
          {/* Dashboard Tab */}
          <button
            onClick={() => setActiveTab('dashboard')}
            className={`px-4 py-2 rounded-lg text-xs font-bold transition flex items-center space-x-1.5 ${
              activeTab === 'dashboard'
                ? 'bg-emerald-50 border border-emerald-100 text-emerald-600'
                : 'text-slate-500 hover:text-slate-800 border border-transparent'
            }`}
          >
            <Landmark className="w-3.5 h-3.5" />
            <span>Dashboard</span>
          </button>

          {/* Teacher Upload Tab (Teachers & Admins) */}
          {(isTeacher || isAdmin) && (
            <button
              onClick={() => setActiveTab('expenses')}
              className={`px-4 py-2 rounded-lg text-xs font-bold transition flex items-center space-x-1.5 ${
                activeTab === 'expenses'
                  ? 'bg-emerald-50 border border-emerald-100 text-emerald-600'
                  : 'text-slate-500 hover:text-slate-800 border border-transparent'
              }`}
            >
              <FileText className="w-3.5 h-3.5" />
              <span>Submit Expense</span>
            </button>
          )}

          {/* HOD Approvals Tab (Approvers & Admins) */}
          {(isApprover || isAdmin) && (
            <button
              onClick={() => setActiveTab('approvals')}
              className={`px-4 py-2 rounded-lg text-xs font-bold transition flex items-center space-x-1.5 ${
                activeTab === 'approvals'
                  ? 'bg-emerald-50 border border-emerald-100 text-emerald-600'
                  : 'text-slate-500 hover:text-slate-800 border border-transparent'
              }`}
            >
              <CheckSquare className="w-3.5 h-3.5" />
              <span>Approvals</span>
            </button>
          )}

          {/* AI Chat Assistant Tab */}
          <button
            onClick={() => setActiveTab('assistant')}
            className={`px-4 py-2 rounded-lg text-xs font-bold transition flex items-center space-x-1.5 ${
              activeTab === 'assistant'
                ? 'bg-emerald-50 border border-emerald-100 text-emerald-600'
                : 'text-slate-500 hover:text-slate-800 border border-transparent'
            }`}
          >
            <MessageSquareCode className="w-3.5 h-3.5" />
            <span>AI Assistant</span>
          </button>
        </div>

        {/* User Badge / Logout */}
        <div className="flex items-center space-x-4">
          <div className="flex items-center space-x-2 border-r border-slate-250 pr-4">
            <div className="w-7 h-7 rounded-full bg-slate-100 border border-slate-200 flex items-center justify-center text-slate-650">
              <User className="w-4 h-4" />
            </div>
            <div className="hidden sm:block text-right">
              <div className="text-xs font-bold text-slate-800">{currentUser.name}</div>
              <div className="text-[9px] text-slate-400 font-bold uppercase tracking-wider">{currentUser.role}</div>
            </div>
          </div>
          <button
            onClick={handleLogout}
            className="p-2 bg-white hover:bg-rose-50 border border-slate-200 hover:border-rose-200 rounded-lg text-slate-500 hover:text-rose-600 transition"
            title="Log Out"
          >
            <LogOut className="w-4 h-4" />
          </button>
        </div>
      </nav>

      {/* Main Content Pane */}
      <main className="flex-1 max-w-7xl w-full mx-auto p-6 md:p-8">
        {activeTab === 'dashboard' && <DashboardView transactionTrigger={transactionTrigger} />}
        {activeTab === 'expenses' && (isTeacher || isAdmin) && <ExpenseView currentUser={currentUser} />}
        {activeTab === 'approvals' && (isApprover || isAdmin) && (
          <ApprovalView currentUser={currentUser} onTransactionAdded={triggerTransactionSync} />
        )}
        {activeTab === 'assistant' && <AssistantView />}
      </main>

      {/* Footer */}
      <footer className="py-6 border-t border-slate-200 text-center text-[10px] text-slate-400 bg-slate-50 font-semibold uppercase tracking-wider">
        EduLedger AI Platform &bull; Hackathon Demo Pipeline &bull; SQLite Spine
      </footer>
    </div>
  );
}
