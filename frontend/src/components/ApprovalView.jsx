import React, { useState, useEffect } from 'react';
import { Check, X, AlertCircle, Edit, FileCheck2, User } from 'lucide-react';
import { API_BASE_URL } from '../config';

export default function ApprovalView({ currentUser, onTransactionAdded }) {
  const [expenses, setExpenses] = useState([]);
  const [selectedExpense, setSelectedExpense] = useState(null);
  const [loading, setLoading] = useState(false);
  
  // Edited values
  const [category, setCategory] = useState('');
  const [amount, setAmount] = useState('');
  const [date, setDate] = useState('');
  const [vendor, setVendor] = useState('');
  const [isEditing, setIsEditing] = useState(false);

  const categories = [
    "Science Supplies",
    "Office Supplies",
    "Classroom Decor",
    "Software License",
    "Staff Utilities",
    "Athletics Equipment"
  ];

  const fetchPending = async () => {
    setLoading(true);
    try {
      const response = await fetch(`${API_BASE_URL}/api/expenses/pending`);
      const data = await response.json();
      setExpenses(data);
      if (data.length > 0) {
        selectExpense(data[0]);
      } else {
        setSelectedExpense(null);
      }
    } catch (err) {
      console.error('Failed to load pending expenses:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchPending();
  }, []);

  const selectExpense = (exp) => {
    setSelectedExpense(exp);
    setCategory(exp.category);
    setAmount(exp.amount);
    setDate(exp.date);
    
    // Parse vendor from OCR JSON if available
    try {
      const parsed = JSON.parse(exp.ocr_extracted_json);
      setVendor(parsed.vendor || 'Unknown Vendor');
    } catch (e) {
      setVendor('Unknown Vendor');
    }
    setIsEditing(false);
  };

  const handleApprove = async () => {
    if (!selectedExpense) return;
    setLoading(true);
    
    try {
      const response = await fetch(`${API_BASE_URL}/api/expenses/approve`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          expense_id: selectedExpense.id,
          action: 'approved',
          approver_id: currentUser.id,
          category,
          amount: parseFloat(amount),
          date
        })
      });
      
      const data = await response.json();
      if (data.success) {
        // Trigger parent state update to refresh dashboard
        if (onTransactionAdded) onTransactionAdded();
        await fetchPending();
      } else {
        alert('Approval failed: ' + data.error);
      }
    } catch (err) {
      console.error(err);
      alert('Network error while approving');
    } finally {
      setLoading(false);
    }
  };

  const handleReject = async () => {
    if (!selectedExpense) return;
    setLoading(true);
    
    try {
      const response = await fetch(`${API_BASE_URL}/api/expenses/approve`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          expense_id: selectedExpense.id,
          action: 'rejected',
          approver_id: currentUser.id
        })
      });
      
      const data = await response.json();
      if (data.success) {
        await fetchPending();
      } else {
        alert('Rejection failed: ' + data.error);
      }
    } catch (err) {
      console.error(err);
      alert('Network error while rejecting');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-bold text-slate-900">Approvals Console</h2>
        <p className="text-slate-500 text-sm">HOD Console: Audit, edit, and approve pending teacher reimbursements</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        
        {/* Pending List Column */}
        <div className="lg:col-span-4 glass-card rounded-xl p-5 h-[550px] flex flex-col">
          <div className="flex justify-between items-center mb-4">
            <h3 className="text-sm font-bold text-slate-800 uppercase tracking-wider">Pending Approvals</h3>
            <span className="bg-amber-50 border border-amber-100 text-amber-600 px-2 py-0.5 rounded text-[10px] font-bold">
              {expenses.length} Pending
            </span>
          </div>

          {loading && expenses.length === 0 ? (
            <div className="flex-1 flex items-center justify-center text-slate-500 text-xs">
              <span className="w-4 h-4 border-2 border-slate-500 border-t-transparent rounded-full animate-spin mr-2"></span>
              Loading pending items...
            </div>
          ) : expenses.length === 0 ? (
            <div className="flex-1 flex flex-col items-center justify-center text-slate-500 text-center px-4">
              <FileCheck2 className="w-10 h-10 text-slate-350 mb-2" />
              <h4 className="text-xs font-bold text-slate-500">All Expenses Handled</h4>
              <p className="text-[10px] text-slate-400 mt-1">There are no pending expenses waiting for HOD approval.</p>
            </div>
          ) : (
            <div className="flex-1 overflow-y-auto space-y-2 pr-1">
              {expenses.map((exp) => {
                const isSelected = selectedExpense?.id === exp.id;
                return (
                  <div
                    key={exp.id}
                    onClick={() => selectExpense(exp)}
                    className={`p-3 rounded-lg border cursor-pointer transition-all ${
                      isSelected 
                        ? 'border-emerald-500 bg-emerald-50/50 shadow-[0_4px_12px_rgba(16,185,129,0.05)]' 
                        : 'border-slate-200 bg-white hover:bg-slate-50'
                    }`}
                  >
                    <div className="flex justify-between items-start">
                      <span className="text-xs font-bold text-slate-850">{exp.submitted_by}</span>
                      <span className="text-xs font-extrabold text-emerald-600">${exp.amount.toFixed(2)}</span>
                    </div>
                    <div className="flex justify-between items-center mt-2 text-[10px] text-slate-500">
                      <span>{exp.category}</span>
                      <span>{exp.date}</span>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* Expense Detail View Column */}
        <div className="lg:col-span-8">
          {selectedExpense ? (
            <div className="glass-card rounded-xl p-6 h-full flex flex-col justify-between">
              
              <div className="flex justify-between items-start pb-4 border-b border-slate-200 mb-4">
                <div>
                  <h3 className="text-base font-bold text-slate-900">Reviewing Request #{selectedExpense.id}</h3>
                  <div className="flex items-center text-xs text-slate-500 mt-1">
                    <User className="w-3.5 h-3.5 mr-1 text-emerald-600" />
                    Submitted by: <strong className="text-slate-700 ml-1">{selectedExpense.submitted_by}</strong>
                  </div>
                </div>
                
                <button
                  onClick={() => setIsEditing(!isEditing)}
                  className={`px-3 py-1 rounded text-xs font-bold border transition flex items-center ${
                    isEditing 
                      ? 'border-emerald-500 text-emerald-600 bg-emerald-50' 
                      : 'border-slate-300 text-slate-500 hover:border-slate-400'
                  }`}
                >
                  <Edit className="w-3.5 h-3.5 mr-1" />
                  {isEditing ? 'Viewing Mode' : 'Edit OCR Data'}
                </button>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6 flex-1 mb-6">
                
                {/* Image display */}
                <div className="space-y-2">
                  <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider block">Submitted Receipt</span>
                  <div className="border border-slate-200 rounded-lg overflow-hidden bg-white p-2 flex items-center justify-center h-64 shadow-inner">
                    <img 
                      src={`${API_BASE_URL}${selectedExpense.receipt_image_path}`} 
                      alt="Receipt detail" 
                      className="max-h-full max-w-full object-contain rounded" 
                    />
                  </div>
                </div>

                {/* Form fields review */}
                <div className="space-y-4">
                  <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider block">Reimbursement Metadata</span>

                  {isEditing ? (
                    <div className="space-y-3">
                      <div className="p-3 bg-amber-50 border border-amber-100 text-amber-600 rounded text-[10px] flex items-start">
                        <AlertCircle className="w-4 h-4 mr-1.5 shrink-0" />
                        <span><strong>OCR Mistakes Review</strong>: You are modifying the extracted values before final ledger commitment. This simulates correcting a scanner fault live.</span>
                      </div>
                      
                      <div>
                        <label className="text-[10px] text-slate-500 block mb-1">Vendor Name</label>
                        <input
                          type="text"
                          value={vendor}
                          onChange={(e) => setVendor(e.target.value)}
                          className="w-full px-2.5 py-1.5 rounded glass-input text-xs"
                        />
                      </div>
                      <div>
                        <label className="text-[10px] text-slate-500 block mb-1">Category</label>
                        <select
                          value={category}
                          onChange={(e) => setCategory(e.target.value)}
                          className="w-full px-2.5 py-1.5 rounded glass-input text-xs bg-white"
                        >
                          {categories.map((cat) => (
                            <option key={cat} value={cat}>{cat}</option>
                          ))}
                        </select>
                      </div>
                      <div className="grid grid-cols-2 gap-2">
                        <div>
                          <label className="text-[10px] text-slate-500 block mb-1">Amount ($)</label>
                          <input
                            type="number"
                            step="0.01"
                            value={amount}
                            onChange={(e) => setAmount(e.target.value)}
                            className="w-full px-2.5 py-1.5 rounded glass-input text-xs"
                          />
                        </div>
                        <div>
                          <label className="text-[10px] text-slate-500 block mb-1">Date</label>
                          <input
                            type="date"
                            value={date}
                            onChange={(e) => setDate(e.target.value)}
                            className="w-full px-2.5 py-1.5 rounded glass-input text-xs"
                          />
                        </div>
                      </div>
                    </div>
                  ) : (
                    <div className="space-y-4 bg-slate-50 border border-slate-200/80 rounded-xl p-4">
                      <div className="flex justify-between pb-2 border-b border-slate-200 text-xs">
                        <span className="text-slate-500">Vendor</span>
                        <span className="font-bold text-slate-800">{vendor}</span>
                      </div>
                      <div className="flex justify-between pb-2 border-b border-slate-200 text-xs">
                        <span className="text-slate-500">Category</span>
                        <span className="font-bold text-slate-800">{category}</span>
                      </div>
                      <div className="flex justify-between pb-2 border-b border-slate-200 text-xs">
                        <span className="text-slate-500">Amount</span>
                        <span className="font-extrabold text-emerald-600 text-sm">${parseFloat(amount).toFixed(2)}</span>
                      </div>
                      <div className="flex justify-between text-xs">
                        <span className="text-slate-500">Transaction Date</span>
                        <span className="font-bold text-slate-800">{date}</span>
                      </div>
                    </div>
                  )}
                </div>

              </div>

              {/* Approval controls */}
              <div className="flex space-x-3 border-t border-slate-200 pt-4">
                <button
                  onClick={handleReject}
                  disabled={loading}
                  className="flex-1 py-3 border border-rose-200 hover:border-rose-500 text-rose-600 hover:text-white hover:bg-rose-500 font-bold rounded-lg transition flex items-center justify-center space-x-2"
                >
                  <X className="w-4 h-4" />
                  <span>Reject Request</span>
                </button>
                <button
                  onClick={handleApprove}
                  disabled={loading}
                  className="flex-1 py-3 bg-gradient-to-r from-emerald-500 to-teal-600 hover:from-emerald-400 hover:to-teal-500 text-white font-bold rounded-lg shadow-md transition-all flex items-center justify-center space-x-2"
                >
                  <Check className="w-4 h-4" />
                  <span>Approve & Write to Ledger</span>
                </button>
              </div>

            </div>
          ) : (
            <div className="glass-card rounded-xl p-6 h-full flex flex-col items-center justify-center text-center text-slate-500 min-h-[350px]">
              <FileCheck2 className="w-12 h-12 text-slate-350 mb-3" />
              <h3 className="font-bold text-sm text-slate-500">No Expense Selected</h3>
              <p className="text-xs text-slate-400 max-w-xs mt-1">Select a pending expense request on the left side to review and action it.</p>
            </div>
          )}
        </div>

      </div>
    </div>
  );
}
