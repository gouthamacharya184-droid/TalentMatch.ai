import React, { useState, useEffect } from 'react';
import {
  BookmarkCheck,
  Briefcase,
  Users,
  Search,
  MessageSquare,
  Trash2,
  CheckCircle2,
  Clock,
  ArrowRight
} from 'lucide-react';
import { jobsApi, shortlistApi, candidatesApi } from '../services/api';
import type { Job, Shortlist } from '../types';
import { CandidateDetailModal } from '../components/CandidateDetailModal';

export const ShortlistPage: React.FC = () => {
  const [jobs, setJobs] = useState<Job[]>([]);
  const [selectedJobId, setSelectedJobId] = useState<string>('');
  const [shortlists, setShortlists] = useState<Shortlist[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedCandidateId, setSelectedCandidateId] = useState<string | null>(null);

  useEffect(() => {
    const fetchJobs = async () => {
      try {
        const res = await jobsApi.getJobs({ limit: 50 });
        setJobs(res.items);
        if (res.items.length > 0) {
          setSelectedJobId(res.items[0].id);
        }
      } catch (e) {
        console.error(e);
      }
    };
    fetchJobs();
  }, []);

  const fetchShortlists = async () => {
    if (!selectedJobId) return;
    setLoading(true);
    try {
      const data = await shortlistApi.getJobShortlist(selectedJobId);
      setShortlists(data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchShortlists();
  }, [selectedJobId]);

  const handleStatusChange = async (shortlistId: string, status: string) => {
    try {
      await shortlistApi.updateShortlistStatus(shortlistId, status);
      fetchShortlists();
    } catch (e) {
      console.error(e);
    }
  };

  const handleRemove = async (shortlistId: string) => {
    if (!window.confirm('Remove candidate from this job shortlist?')) return;
    try {
      await shortlistApi.removeFromShortlist(shortlistId);
      fetchShortlists();
    } catch (e) {
      console.error(e);
    }
  };

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* ── Page Header ────────────────────────────────────────── */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-black text-slate-900 tracking-tight flex items-center gap-2">
            Shortlisted Candidates
            <span className="text-xs font-bold uppercase tracking-wider px-2 py-0.5 rounded-full bg-amber-100 text-amber-800">
              Pipeline
            </span>
          </h1>
          <p className="text-xs text-slate-500 mt-1">
            Recruiter shortlists, interview stage progressions, and private screening comments.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <label className="text-xs font-bold text-slate-500 uppercase tracking-wider">
            Job Role:
          </label>
          <select
            value={selectedJobId}
            onChange={(e) => setSelectedJobId(e.target.value)}
            className="p-2 rounded-xl border border-slate-300 text-xs font-bold text-slate-900 bg-white outline-none focus:border-blue-600 shadow-sm"
          >
            {jobs.map((j) => (
              <option key={j.id} value={j.id}>
                {j.title} ({j.company})
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* ── Shortlist Pipeline Table ───────────────────────────── */}
      <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-50 border-b border-slate-200 text-slate-500 font-bold uppercase tracking-wider text-[11px]">
              <tr>
                <th className="p-4 pl-6">Candidate</th>
                <th className="p-4">Contact & Location</th>
                <th className="p-4">Recruiter Comments</th>
                <th className="p-4">Stage Status</th>
                <th className="p-4">Added On</th>
                <th className="p-4 pr-6 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {loading ? (
                <tr>
                  <td colSpan={6} className="p-8 text-center text-slate-400">
                    Loading shortlists...
                  </td>
                </tr>
              ) : shortlists.length === 0 ? (
                <tr>
                  <td colSpan={6} className="p-8 text-center text-slate-400">
                    No candidates currently shortlisted for this role.
                  </td>
                </tr>
              ) : (
                shortlists.map((s) => (
                  <tr key={s.id} className="hover:bg-slate-50 transition-colors">
                    <td className="p-4 pl-6">
                      <div className="flex items-center gap-3">
                        <div className="w-8 h-8 rounded-full bg-amber-100 text-amber-800 font-bold flex items-center justify-center text-xs shrink-0">
                          {s.candidate?.name?.charAt(0).toUpperCase() || 'C'}
                        </div>
                        <div>
                          <p className="font-bold text-slate-900 text-sm">{s.candidate?.name}</p>
                          <p className="text-[11px] text-slate-400">
                            {s.candidate?.total_experience_years || 0} Years Exp
                          </p>
                        </div>
                      </div>
                    </td>
                    <td className="p-4 text-slate-600">
                      <p className="font-medium text-slate-800">{s.candidate?.email || 'N/A'}</p>
                      <p className="text-[11px] text-slate-400">{s.candidate?.location || 'Remote'}</p>
                    </td>
                    <td className="p-4 text-slate-700 max-w-xs leading-relaxed">
                      {s.comments || <span className="text-slate-400 italic">No notes added</span>}
                    </td>
                    <td className="p-4">
                      <select
                        value={s.status}
                        onChange={(e) => handleStatusChange(s.id, e.target.value)}
                        className="p-1.5 rounded-lg border border-slate-300 text-xs font-semibold bg-white outline-none"
                      >
                        <option value="shortlisted">Shortlisted</option>
                        <option value="interview">Interview</option>
                        <option value="hired">Hired</option>
                        <option value="rejected">Rejected</option>
                      </select>
                    </td>
                    <td className="p-4 text-slate-500 font-medium text-[11px]">
                      {new Date(s.created_at).toLocaleDateString()}
                    </td>
                    <td className="p-4 pr-6 text-right space-x-2">
                      <button
                        onClick={() => setSelectedCandidateId(s.candidate_id)}
                        className="px-2.5 py-1 rounded-lg bg-blue-50 text-blue-700 hover:bg-blue-100 font-semibold text-xs transition-colors"
                      >
                        Inspect
                      </button>
                      <button
                        onClick={() => handleRemove(s.id)}
                        className="p-1 rounded-lg border border-slate-200 text-slate-400 hover:text-rose-600 hover:bg-rose-50 transition-colors"
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

      {/* Candidate Modal */}
      {selectedCandidateId && (
        <CandidateDetailModal
          candidateId={selectedCandidateId}
          jobId={selectedJobId}
          onClose={() => setSelectedCandidateId(null)}
          onStatusChange={fetchShortlists}
        />
      )}
    </div>
  );
};
