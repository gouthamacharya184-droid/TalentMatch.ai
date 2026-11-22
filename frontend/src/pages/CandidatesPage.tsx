import React, { useState, useEffect } from 'react';
import {
  Search,
  Trash2,
  Briefcase,
  Mail,
  LayoutGrid,
  List,
  AlertCircle,
  RefreshCw
} from 'lucide-react';
import { candidatesApi } from '../services/api';
import type { Candidate } from '../types';
import { CandidateDetailModal } from '../components/CandidateDetailModal';

export const CandidatesPage: React.FC = () => {
  const [candidates, setCandidates] = useState<Candidate[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [minExp, setMinExp] = useState<number | undefined>(undefined);
  const [viewMode, setViewMode] = useState<'grid' | 'table'>('table');
  const [selectedCandidateId, setSelectedCandidateId] = useState<string | null>(null);

  const fetchCandidates = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await candidatesApi.getCandidates({
        search: search || undefined,
        status: statusFilter || undefined,
        min_experience: minExp,
      });
      setCandidates(res?.items ?? []);
    } catch (e: any) {
      console.error(e);
      setError(e?.response?.data?.detail || e?.message || 'Could not load candidates');
      setCandidates([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCandidates();
  }, [search, statusFilter, minExp]);

  const handleDelete = async (id: string) => {
    if (!window.confirm('Delete this candidate record and associated resume?')) return;
    try {
      await candidatesApi.deleteCandidate(id);
      fetchCandidates();
    } catch (e) {
      console.error(e);
    }
  };

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* ── Page Header ────────────────────────────────────────── */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-black text-slate-900 tracking-tight">Candidates Repository</h1>
          <p className="text-xs text-slate-500 mt-1">
            Browse and manage all parsed candidate records, extracted skills, and contact profiles.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <div className="flex items-center bg-white border border-slate-200 rounded-xl p-1 shadow-sm">
            <button
              onClick={() => setViewMode('table')}
              className={`p-1.5 rounded-lg ${
                viewMode === 'table' ? 'bg-blue-600 text-white' : 'text-slate-500 hover:text-slate-900'
              }`}
            >
              <List className="w-4 h-4" />
            </button>
            <button
              onClick={() => setViewMode('grid')}
              className={`p-1.5 rounded-lg ${
                viewMode === 'grid' ? 'bg-blue-600 text-white' : 'text-slate-500 hover:text-slate-900'
              }`}
            >
              <LayoutGrid className="w-4 h-4" />
            </button>
          </div>
        </div>
      </div>

      {/* ── Filter Bar ─────────────────────────────────────────── */}
      <div className="bg-white p-4 rounded-2xl border border-slate-200 shadow-sm grid grid-cols-1 sm:grid-cols-3 gap-3 text-xs">
        <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg border border-slate-300 bg-white">
          <Search className="w-3.5 h-3.5 text-slate-400" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search by name, email, or location..."
            className="w-full text-xs outline-none bg-transparent"
          />
        </div>

        <div>
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="w-full p-2.5 rounded-lg border border-slate-300 bg-white font-medium text-slate-800 outline-none"
          >
            <option value="">All Statuses</option>
            <option value="new">New</option>
            <option value="analyzed">Analyzed</option>
            <option value="shortlisted">Shortlisted</option>
            <option value="under_review">Under Review</option>
            <option value="interview">Interview</option>
            <option value="hired">Hired</option>
            <option value="rejected">Rejected</option>
          </select>
        </div>

        <div>
          <select
            value={minExp === undefined ? '' : String(minExp)}
            onChange={(e) => setMinExp(e.target.value ? Number(e.target.value) : undefined)}
            className="w-full p-2.5 rounded-lg border border-slate-300 bg-white font-medium text-slate-800 outline-none"
          >
            <option value="">Any Experience Level</option>
            <option value="2">2+ Years</option>
            <option value="4">4+ Years</option>
            <option value="6">6+ Years</option>
          </select>
        </div>
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-rose-50 border border-rose-200 text-xs text-rose-800 flex items-center justify-between shadow-sm">
          <div className="flex items-center gap-2">
            <AlertCircle className="w-4 h-4 text-rose-600 shrink-0" />
            <span className="font-semibold">{error}</span>
          </div>
          <button
            onClick={() => fetchCandidates()}
            className="flex items-center gap-1 px-3 py-1 rounded-lg bg-rose-100 hover:bg-rose-200 text-rose-900 font-bold transition-colors cursor-pointer"
          >
            <RefreshCw className="w-3 h-3" />
            <span>Retry</span>
          </button>
        </div>
      )}

      {/* ── Views: Table vs Grid ────────────────────────────────── */}
      {viewMode === 'table' ? (
        <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-50 border-b border-slate-200 text-slate-500 font-bold uppercase tracking-wider text-[11px]">
                <tr>
                  <th className="p-4 pl-6">Candidate Details</th>
                  <th className="p-4">Location</th>
                  <th className="p-4">Experience</th>
                  <th className="p-4">Extracted Skills</th>
                  <th className="p-4">Status</th>
                  <th className="p-4 pr-6 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {loading ? (
                  <tr>
                    <td colSpan={6} className="p-8 text-center text-slate-400">
                      Loading candidate profiles...
                    </td>
                  </tr>
                ) : candidates.length === 0 ? (
                  <tr>
                    <td colSpan={6} className="p-8 text-center text-slate-400">
                      No candidates match the specified filters.
                    </td>
                  </tr>
                ) : (
                  candidates.map((c) => (
                    <tr key={c.id} className="hover:bg-slate-50 transition-colors">
                      <td className="p-4 pl-6">
                        <div className="flex items-center gap-3">
                          <div className="w-8 h-8 rounded-full bg-blue-100 text-blue-700 font-bold flex items-center justify-center text-xs shrink-0">
                            {c.name.charAt(0).toUpperCase()}
                          </div>
                          <div>
                            <p className="font-bold text-slate-900 text-sm">{c.name}</p>
                            <p className="text-[11px] text-slate-400">{c.email || 'No email'}</p>
                          </div>
                        </div>
                      </td>
                      <td className="p-4 text-slate-600 font-medium">{c.location || 'Remote'}</td>
                      <td className="p-4 text-slate-600 font-semibold">{c.total_experience_years} Years</td>
                      <td className="p-4 max-w-xs">
                        <div className="flex flex-wrap gap-1">
                          {c.skills?.slice(0, 4).map((s) => (
                            <span
                              key={s.id}
                              className="px-2 py-0.5 rounded text-[10px] font-semibold bg-slate-100 text-slate-700"
                            >
                              {s.skill_name}
                            </span>
                          ))}
                          {(c.skills?.length || 0) > 4 && (
                            <span className="text-[10px] text-slate-400 font-medium">
                              +{(c.skills?.length || 0) - 4}
                            </span>
                          )}
                        </div>
                      </td>
                      <td className="p-4">
                        <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider bg-blue-50 text-blue-700">
                          {c.status.replace('_', ' ')}
                        </span>
                      </td>
                      <td className="p-4 pr-6 text-right space-x-2">
                        <button
                          onClick={() => setSelectedCandidateId(c.id)}
                          className="px-2.5 py-1 rounded-lg bg-blue-50 text-blue-700 font-medium hover:bg-blue-100 text-xs transition-colors"
                        >
                          View Profile
                        </button>
                        <button
                          onClick={() => handleDelete(c.id)}
                          title="Delete Candidate"
                          className="p-1.5 rounded-lg border border-slate-200 text-slate-400 hover:text-rose-600 hover:bg-rose-50 transition-colors"
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                        </button>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      ) : candidates.length === 0 ? (
        <div className="bg-white rounded-2xl border border-slate-200 p-8 text-center text-slate-400 text-xs">
          No candidates match the specified filters.
        </div>
      ) : (
        /* Grid View */
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {candidates.map((c) => (
            <div
              key={c.id}
              className="bg-white rounded-2xl border border-slate-200 shadow-sm p-5 space-y-4 flex flex-col justify-between"
            >
              <div className="space-y-3">
                <div className="flex items-start justify-between">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-xl bg-gradient-to-tr from-blue-600 to-indigo-600 text-white font-bold flex items-center justify-center text-sm shadow-sm">
                      {c.name.charAt(0).toUpperCase()}
                    </div>
                    <div>
                      <h3 className="font-bold text-slate-900 text-sm">{c.name}</h3>
                      <p className="text-[11px] text-slate-400">{c.location || 'Remote'}</p>
                    </div>
                  </div>
                  <span className="px-2 py-0.5 rounded-full text-[10px] font-bold uppercase bg-blue-50 text-blue-700">
                    {c.status}
                  </span>
                </div>

                <div className="text-xs text-slate-600 space-y-1">
                  <div className="flex items-center gap-1.5">
                    <Mail className="w-3.5 h-3.5 text-slate-400" />
                    <span className="truncate">{c.email || 'Not specified'}</span>
                  </div>
                  <div className="flex items-center gap-1.5">
                    <Briefcase className="w-3.5 h-3.5 text-slate-400" />
                    <span>{c.total_experience_years} Years Experience</span>
                  </div>
                </div>

                <div>
                  <span className="text-[10px] font-bold text-slate-400 uppercase tracking-wider block mb-1">
                    Skills:
                  </span>
                  <div className="flex flex-wrap gap-1">
                    {c.skills?.slice(0, 5).map((s) => (
                      <span
                        key={s.id}
                        className="px-2 py-0.5 rounded text-[10px] font-semibold bg-slate-100 text-slate-700"
                      >
                        {s.skill_name}
                      </span>
                    ))}
                  </div>
                </div>
              </div>

              <div className="pt-3 border-t border-slate-100 flex items-center justify-between">
                <button
                  onClick={() => setSelectedCandidateId(c.id)}
                  className="px-3 py-1.5 rounded-lg bg-blue-600 text-white text-xs font-semibold hover:bg-blue-700 transition-colors"
                >
                  Inspect Candidate
                </button>
                <button
                  onClick={() => handleDelete(c.id)}
                  className="p-1.5 text-slate-400 hover:text-rose-600"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Candidate Profile Modal */}
      {selectedCandidateId && (
        <CandidateDetailModal
          candidateId={selectedCandidateId}
          onClose={() => setSelectedCandidateId(null)}
          onStatusChange={fetchCandidates}
        />
      )}
    </div>
  );
};
