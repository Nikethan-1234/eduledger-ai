import React, { useState, useEffect } from 'react';
import { LineChart, Line, BarChart, Bar, PieChart, Pie, Cell, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { Landmark, TrendingUp, AlertTriangle, AlertCircle, Sparkles, DollarSign, Calendar } from 'lucide-react';
import { API_BASE_URL } from '../config';

export default function DashboardView({ transactionTrigger }) {
  const [stats, setStats] = useState(null);
  const [charts, setCharts] = useState(null);
  const [forecast, setForecast] = useState([]);
  const [anomalies, setAnomalies] = useState([]);
  const [loading, setLoading] = useState(true);

  // Curated Colors
  const COLORS = ['#10b981', '#06b6d4', '#8b5cf6', '#f59e0b', '#ec4899', '#3b82f6'];
  const EXPENSE_COLORS = ['#ec4899', '#f43f5e', '#ef4444', '#f97316', '#eab308', '#a855f7'];

  const fetchData = async () => {
    try {
      setLoading(true);
      // Fetch Stats
      const statsRes = await fetch(`${API_BASE_URL}/api/dashboard/stats`);
      const statsData = await statsRes.json();
      setStats(statsData);

      // Fetch Charts
      const chartsRes = await fetch(`${API_BASE_URL}/api/dashboard/charts`);
      const chartsData = await chartsRes.json();
      setCharts(chartsData);

      // Fetch Forecasts
      const forecastRes = await fetch(`${API_BASE_URL}/api/dashboard/forecast`);
      const forecastData = await forecastRes.json();
      setForecast(forecastData);

      // Fetch Anomalies
      const anomaliesRes = await fetch(`${API_BASE_URL}/api/dashboard/anomalies`);
      const anomaliesData = await anomaliesRes.json();
      setAnomalies(anomaliesData);
    } catch (err) {
      console.error('Failed to load dashboard data:', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, [transactionTrigger]);

  if (loading || !stats || !charts) {
    return (
      <div className="flex items-center justify-center min-h-[400px] text-slate-500">
        <span className="w-6 h-6 border-2 border-emerald-500 border-t-transparent rounded-full animate-spin mr-3"></span>
        <span>Loading EduLedger AI Intelligence Layer...</span>
      </div>
    );
  }

  // Combine monthly actual trend and predictions for the line chart
  const combinedTrendData = [...charts.monthly_trend];
  if (forecast && forecast.length > 0) {
    // Add overlap connecting line
    const lastActual = charts.monthly_trend[charts.monthly_trend.length - 1];
    if (lastActual) {
      combinedTrendData.push({
        month: lastActual.month,
        revenue: lastActual.revenue,
        expenses: lastActual.expenses,
        forecast: lastActual.revenue // starting point for forecast line
      });
    }
    
    // Add forecasted months
    forecast.forEach(item => {
      combinedTrendData.push({
        month: item.month,
        forecast: item.forecast
      });
    });
  }

  const flaggedAnoms = anomalies.filter(a => a.is_anomaly);

  return (
    <div className="space-y-6">
      
      {/* Header */}
      <div>
        <h2 className="text-2xl font-bold text-slate-900 flex items-center">
          Revenue Intelligence Dashboard 
          <span className="ml-2.5 px-2 py-0.5 rounded text-[10px] font-extrabold bg-emerald-50 border border-emerald-100 text-emerald-600 flex items-center gap-1">
            <Sparkles className="w-3 h-3" /> ML Engine Active
          </span>
        </h2>
        <p className="text-slate-500 text-sm">Real-time ledger overview, automated forecasts, and machine learning anomaly reports</p>
      </div>

      {/* 4 Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-5">
        {[
          { title: 'Total Revenue Collected', value: stats.total_revenue, sub: 'Fee payments synced', icon: Landmark, color: 'text-emerald-600 bg-emerald-50 border-emerald-100' },
          { title: 'Total Approved Expenses', value: stats.total_expenses, sub: 'OCR approved disbursements', icon: TrendingUp, color: 'text-rose-600 bg-rose-50 border-rose-100' },
          { title: 'Net Ledger Balance', value: stats.net_balance, sub: 'Shared transaction spine', icon: DollarSign, color: 'text-cyan-600 bg-cyan-50 border-cyan-100' },
          { title: 'Outstanding Pending Fees', value: stats.pending_fees, sub: 'Due in current terms', icon: Calendar, color: 'text-amber-600 bg-amber-50 border-amber-100' }
        ].map((card, idx) => {
          const Icon = card.icon;
          return (
            <div key={idx} className="glass-card rounded-xl p-5 border border-slate-200/80 flex items-center justify-between">
              <div className="space-y-1">
                <span className="text-[11px] font-bold text-slate-500 uppercase tracking-wider block">{card.title}</span>
                <span className="text-2xl font-extrabold text-slate-900 block">${card.value.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</span>
                <span className="text-[10px] text-slate-400 block">{card.sub}</span>
              </div>
              <div className={`p-3 rounded-lg border ${card.color}`}>
                <Icon className="w-5 h-5" />
              </div>
            </div>
          );
        })}
      </div>

      {/* Main Charts Row */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        
        {/* Line Chart: Revenue Actuals vs Forecasts */}
        <div className="lg:col-span-8 glass-card rounded-xl p-5 border border-slate-200/80">
          <h3 className="text-sm font-bold text-slate-800 uppercase tracking-wider mb-4 flex items-center gap-1.5">
            Monthly Transactions & Revenue Forecast <span className="text-[10px] font-normal text-slate-500 font-mono">(12m History + 3m Prediction)</span>
          </h3>
          <div className="h-80">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={combinedTrendData} margin={{ top: 10, right: 30, left: 10, bottom: 5 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(0,0,0,0.05)" />
                <XAxis dataKey="month" stroke="#64748b" fontSize={10} tickLine={false} />
                <YAxis stroke="#64748b" fontSize={10} tickLine={false} axisLine={false} tickFormatter={(v) => `$${v}`} />
                <Tooltip 
                  contentStyle={{ backgroundColor: '#ffffff', borderColor: '#e2e8f0', borderRadius: '8px', color: '#1e293b' }}
                  labelClassName="text-slate-700 font-bold font-sans text-xs"
                  itemStyle={{ fontSize: '11px', fontFamily: 'sans-serif' }}
                />
                <Legend wrapperStyle={{ fontSize: '11px', paddingTop: '10px' }} />
                
                <Line type="monotone" dataKey="revenue" stroke="#10b981" strokeWidth={3} name="Actual Revenue (Fees)" dot={{ r: 3 }} activeDot={{ r: 5 }} />
                <Line type="monotone" dataKey="forecast" stroke="#0ea5e9" strokeWidth={3} strokeDasharray="6 4" name="ML Forecasted Revenue" dot={false} />
                <Line type="monotone" dataKey="expenses" stroke="#f43f5e" strokeWidth={2.5} name="Actual Expenses" dot={{ r: 2 }} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Expense Distribution Pie Chart */}
        <div className="lg:col-span-4 glass-card rounded-xl p-5 border border-slate-200/80 flex flex-col justify-between">
          <h3 className="text-sm font-bold text-slate-800 uppercase tracking-wider mb-4">Expenses by Category</h3>
          <div className="h-60 flex items-center justify-center relative">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={charts.expense_breakdown}
                  cx="50%"
                  cy="50%"
                  innerRadius={60}
                  outerRadius={80}
                  paddingAngle={3}
                  dataKey="value"
                >
                  {charts.expense_breakdown.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={EXPENSE_COLORS[index % EXPENSE_COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip 
                  contentStyle={{ backgroundColor: '#ffffff', borderColor: '#e2e8f0', borderRadius: '8px' }}
                  itemStyle={{ fontSize: '11px', color: '#0f172a' }}
                  formatter={(val) => [`$${val.toFixed(2)}`, 'Spent']}
                />
              </PieChart>
            </ResponsiveContainer>
            <div className="absolute flex flex-col items-center justify-center text-center">
              <span className="text-[10px] text-slate-500 font-bold uppercase">Total Exp</span>
              <span className="text-sm font-extrabold text-slate-800">${stats.total_expenses.toLocaleString(undefined, { maximumFractionDigits: 0 })}</span>
            </div>
          </div>
          <div className="grid grid-cols-2 gap-2 text-[10px] font-semibold mt-2">
            {charts.expense_breakdown.map((item, idx) => (
              <div key={idx} className="flex items-center space-x-1.5">
                <span className="w-2.5 h-2.5 rounded-full shrink-0" style={{ backgroundColor: EXPENSE_COLORS[idx % EXPENSE_COLORS.length] }}></span>
                <span className="text-slate-600 truncate">{item.category}</span>
              </div>
            ))}
          </div>
        </div>

      </div>

      {/* Second row: Fee collections by class & Anomalies list */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        
        {/* Class Collection Bar Chart */}
        <div className="lg:col-span-6 glass-card rounded-xl p-5 border border-slate-200/80">
          <h3 className="text-sm font-bold text-slate-800 uppercase tracking-wider mb-4">Fee Collection Rate by Class</h3>
          <div className="h-64">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={charts.class_rates} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(0,0,0,0.05)" />
                <XAxis dataKey="class" stroke="#64748b" fontSize={10} tickLine={false} />
                <YAxis stroke="#64748b" fontSize={10} tickLine={false} axisLine={false} tickFormatter={(v) => `${v}%`} />
                <Tooltip 
                  contentStyle={{ backgroundColor: '#ffffff', borderColor: '#e2e8f0', borderRadius: '8px' }}
                  formatter={(val, name) => [name === 'rate' ? `${val}%` : `$${val.toLocaleString()}`, name === 'rate' ? 'Collection Rate' : name.toUpperCase()]}
                />
                <Bar dataKey="rate" fill="#10b981" radius={[4, 4, 0, 0]} name="Collection Rate">
                  {charts.class_rates.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Anomaly Alerts & SHAP Explainability Panel */}
        <div className="lg:col-span-6 glass-card rounded-xl p-5 border border-slate-200/80 flex flex-col h-full">
          <div className="flex justify-between items-center mb-4 pb-2 border-b border-slate-200">
            <h3 className="text-sm font-bold text-slate-800 uppercase tracking-wider flex items-center gap-1.5">
              <AlertTriangle className="w-4 h-4 text-rose-500 shrink-0" /> Expense Anomaly Reports (Isolation Forest)
            </h3>
            <span className="bg-rose-100 text-rose-700 px-2 py-0.5 rounded text-[10px] font-bold">
              {flaggedAnoms.length} Flags Detected
            </span>
          </div>

          <div className="flex-1 overflow-y-auto space-y-3 max-h-56 pr-1">
            {flaggedAnoms.length === 0 ? (
              <div className="h-full flex items-center justify-center text-slate-500 text-xs">
                No anomalies flagged. SQLite ledger matches expected patterns.
              </div>
            ) : (
              flaggedAnoms.map((anom) => (
                <div key={anom.id} className="p-3.5 rounded-lg bg-rose-50 border border-rose-100 flex items-start space-x-2.5">
                  <AlertCircle className="w-4 h-4 text-rose-500 shrink-0 mt-0.5 animate-pulse" />
                  <div className="space-y-1">
                    <div className="flex justify-between items-baseline gap-2">
                      <span className="text-xs font-bold text-slate-850">
                        {anom.category} <span className="text-[10px] font-normal text-slate-500">by {anom.submitted_by}</span>
                      </span>
                      <span className="text-xs font-extrabold text-rose-600">${anom.amount.toFixed(2)}</span>
                    </div>
                    <p className="text-[10px] text-slate-500 leading-relaxed font-semibold">
                      SHAP: <span className="text-rose-700 font-normal italic">{anom.explanation}</span>
                    </p>
                    <div className="flex justify-between items-center pt-1.5 text-[9px] text-slate-400">
                      <span>Ref ID: #{anom.id}</span>
                      <span>Date: {anom.date}</span>
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>

      </div>

    </div>
  );
}
