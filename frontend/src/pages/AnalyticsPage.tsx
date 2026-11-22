import React, { useState, useEffect } from 'react';
import {
  FileSpreadsheet,
  FileCode,
  FileText
} from 'lucide-react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
  PieChart as RechartsPie,
  Pie,
  Cell
} from 'recharts';
import { analyticsApi, jobsApi } from '../services/api';
import type { DashboardStats, Job } from '../types';

export const AnalyticsPage: React.FC = () => {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [jobs, setJobs] = useState<Job[]>([]);
  const [selectedJobId, setSelectedJobId] = useState<string>('');
  const [loading, setLoading] = useState(true);
  const [exporting, setExporting] = useState(false);

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [dashRes, jobsRes] = await Promise.all([
          analyticsApi.getDashboard().catch(() => null),
          jobsApi.getJobs({ limit: 50 }).catch(() => ({ items: [], total: 0 })),
        ]);
        setStats(dashRes);
        const items = jobsRes?.items ?? [];
        setJobs(items);
        if (items.length > 0) {
          setSelectedJobId(items[0].id);
        }
      } catch (e) {
        console.error(e);
        setJobs([]);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  const handleExport = async (format: 'csv' | 'xlsx' | 'pdf') => {
    if (!selectedJobId) return;
    setExporting(true);
    try {
      const blob = await analyticsApi.exportReport(selectedJobId, format);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `TalentMatch_Analytics_Report.${format}`;
      a.click();
    } catch (e) {
      console.error(e);
    } finally {
      setExporting(false);
    }
  };

  if (loading) {
    return (
      <div className="p-8 text-center text-xs text-slate-400">
        Loading recruitment analytics...
      </div>
    );
  }

  if (!stats) {
    return (
      <div className="p-8 bg-white rounded-2xl border border-rose-200 shadow-sm text-center space-y-4 max-w-lg mx-auto my-12">
        <h3 className="text-base font-bold text-slate-900">Analytics Data Unavailable</h3>
        <p className="text-xs text-slate-500">
          Failed to fetch recruitment metrics. Please verify the backend connection.
        </p>
        <button
          onClick={() => {
            setLoading(true);
            Promise.all([analyticsApi.getDashboard(), jobsApi.getJobs({ limit: 50 })])
              .then(([d, j]) => {
                setStats(d);
                setJobs(j.items);
                if (j.items.length > 0) setSelectedJobId(j.items[0].id);
              })
              .catch(console.error)
              .finally(() => setLoading(false));
          }}
          className="px-4 py-2 bg-blue-600 text-white text-xs font-semibold rounded-xl hover:bg-blue-700 transition-colors shadow-md shadow-blue-500/20 cursor-pointer"
        >
          Retry Analytics
        </button>
      </div>
    );
  }

  const scoreData = Object.entries(stats.score_distribution || {}).map(([range, count]) => ({
    name: range,
    value: count,
  }));

  const COLORS = ['#10B981', '#3B82F6', '#6366F1', '#F59E0B', '#EF4444'];

  const skillData = Object.entries(stats.skills_availability || {}).map(([skill, count]) => ({
    skill,
    count,
  }));

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* ── Page Header ────────────────────────────────────────── */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-black text-slate-900 tracking-tight flex items-center gap-2">
            Analytics & Reports
            <span className="text-xs font-bold uppercase tracking-wider px-2 py-0.5 rounded-full bg-blue-100 text-blue-700">
              Audit Data
            </span>
          </h1>
          <p className="text-xs text-slate-500 mt-1">
            Aggregated recruitment metrics, score distributions, and exportable reports.
          </p>
        </div>

        {/* Export Selection */}
        <div className="flex items-center gap-2">
          <select
            value={selectedJobId}
            onChange={(e) => setSelectedJobId(e.target.value)}
            className="p-2 rounded-xl border border-slate-300 text-xs font-bold text-slate-900 bg-white outline-none"
          >
            {jobs.map((j) => (
              <option key={j.id} value={j.id}>
                {j.title}
              </option>
            ))}
          </select>
          <button
            onClick={() => handleExport('csv')}
            disabled={exporting}
            className="flex items-center gap-1.5 px-3 py-2 rounded-xl bg-white border border-slate-200 text-xs font-semibold text-slate-700 hover:bg-slate-50 shadow-sm"
          >
            <FileCode className="w-3.5 h-3.5 text-blue-600" />
            <span>CSV</span>
          </button>
          <button
            onClick={() => handleExport('xlsx')}
            disabled={exporting}
            className="flex items-center gap-1.5 px-3 py-2 rounded-xl bg-white border border-slate-200 text-xs font-semibold text-slate-700 hover:bg-slate-50 shadow-sm"
          >
            <FileSpreadsheet className="w-3.5 h-3.5 text-emerald-600" />
            <span>Excel</span>
          </button>
          <button
            onClick={() => handleExport('pdf')}
            disabled={exporting}
            className="flex items-center gap-1.5 px-3 py-2 rounded-xl bg-blue-600 text-white text-xs font-semibold hover:bg-blue-700 shadow-md shadow-blue-500/20"
          >
            <FileText className="w-3.5 h-3.5" />
            <span>PDF</span>
          </button>
        </div>
      </div>

      {/* ── Visual Charts ──────────────────────────────────────── */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Score Tier Distribution */}
        <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm space-y-4">
          <h3 className="text-sm font-bold text-slate-900">Score Range Breakdown</h3>
          <p className="text-xs text-slate-500">Distribution of candidate pool scores</p>
          <div className="h-64 w-full flex items-center justify-center">
            <ResponsiveContainer width="100%" height="100%">
              <RechartsPie>
                <Pie
                  data={scoreData}
                  cx="50%"
                  cy="50%"
                  outerRadius={85}
                  dataKey="value"
                  label={({ name, percent }: any) => `${name} (${(percent * 100).toFixed(0)}%)`}
                >
                  {scoreData.map((_, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip />
              </RechartsPie>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Skills Availability */}
        <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm space-y-4">
          <h3 className="text-sm font-bold text-slate-900">Extracted Skills Availability</h3>
          <p className="text-xs text-slate-500">Most frequent candidate competencies</p>
          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={skillData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#F1F5F9" />
                <XAxis dataKey="skill" tick={{ fontSize: 11, fill: '#64748B' }} />
                <YAxis tick={{ fontSize: 11, fill: '#64748B' }} allowDecimals={false} />
                <Tooltip
                  contentStyle={{
                    backgroundColor: '#0F172A',
                    borderRadius: '8px',
                    color: '#fff',
                    fontSize: '12px',
                  }}
                />
                <Bar dataKey="count" fill="#2563EB" radius={[6, 6, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* ── System Audit Log Table ──────────────────────────────── */}
      <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden p-6 space-y-4">
        <div>
          <h3 className="text-sm font-bold text-slate-900">Recruitment Activity & Audit Log</h3>
          <p className="text-xs text-slate-500">
            Immutable trace of resume uploads, matching runs, and status changes.
          </p>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-50 border-b border-slate-200 text-slate-500 font-bold uppercase tracking-wider text-[11px]">
              <tr>
                <th className="p-3 pl-4">Timestamp</th>
                <th className="p-3">Action</th>
                <th className="p-3">Entity Type</th>
                <th className="p-3">Details</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {stats.recent_activity?.map((act) => (
                <tr key={act.id} className="hover:bg-slate-50 transition-colors">
                  <td className="p-3 pl-4 text-slate-400 text-[11px]">
                    {new Date(act.created_at).toLocaleString()}
                  </td>
                  <td className="p-3 font-bold text-slate-900">{act.action}</td>
                  <td className="p-3">
                    <span className="px-2 py-0.5 rounded text-[10px] font-semibold uppercase bg-slate-100 text-slate-700">
                      {act.entity_type}
                    </span>
                  </td>
                  <td className="p-3 text-slate-600 font-mono text-[11px]">
                    {JSON.stringify(act.details)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
