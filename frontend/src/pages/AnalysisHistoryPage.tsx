import React, { useState, useEffect } from 'react';
import { History, Search, ArrowRight, Eye, Calendar, Sparkles } from 'lucide-react';
import { analyticsApi } from '../services/api';
import type { MatchingAnalysis } from '../types';
import { CandidateDetailModal } from '../components/CandidateDetailModal';

export const AnalysisHistoryPage: React.FC = () => {
  const [history, setHistory] = useState<MatchingAnalysis[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedCandidateId, setSelectedCandidateId] = useState<string | null>(null);

  useEffect(() => {
    const fetchHistory = async () => {
      try {
        const res = await analyticsApi.getHistory({ limit: 50 });
        setHistory(res.items);
      } catch (e) {
        console.error(e);
      } finally {
        setLoading(false);
      }
    };
    fetchHistory();
  }, []);

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      <div>
        <h1 className="text-2xl font-black text-slate-900 tracking-tight flex items-center gap-2">
          AI Analysis History
          <span className="text-xs font-bold uppercase tracking-wider px-2 py-0.5 rounded-full bg-blue-100 text-blue-700">
            Records
          </span>
        </h1>
        <p className="text-xs text-slate-500 mt-1">
          Chronological record of all previous candidate evaluations, scoring runs, and timestamps.
        </p>
      </div>

      <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-50 border-b border-slate-200 text-slate-500 font-bold uppercase tracking-wider text-[11px]">
              <tr>
                <th className="p-4 pl-6">Analysis Timestamp</th>
                <th className="p-4">Candidate Evaluated</th>
                <th className="p-4">Target Job</th>
                <th className="p-4">Overall Score</th>
                <th className="p-4">Skills Verified</th>
                <th className="p-4 pr-6 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {loading ? (
                <tr>
                  <td colSpan={6} className="p-8 text-center text-slate-400">
                    Loading history logs...
                  </td>
                </tr>
              ) : history.length === 0 ? (
                <tr>
                  <td colSpan={6} className="p-8 text-center text-slate-400">
                    No matching history records found.
                  </td>
                </tr>
              ) : (
                history.map((item) => (
                  <tr key={item.id} className="hover:bg-slate-50 transition-colors">
                    <td className="p-4 pl-6 text-slate-500 font-medium text-[11px]">
                      {new Date(item.created_at).toLocaleString()}
                    </td>
                    <td className="p-4 font-bold text-slate-900">{item.candidate?.name || 'Candidate'}</td>
                    <td className="p-4 text-slate-600 font-medium">{item.job?.title || 'Job Opening'}</td>
                    <td className="p-4 font-black text-emerald-600 text-sm">
                      {item.overall_score}%
                    </td>
                    <td className="p-4">
                      <span className="px-2 py-0.5 rounded bg-blue-50 text-blue-700 font-semibold text-[10px]">
                        {item.matched_skills?.length || 0} Matched Skills
                      </span>
                    </td>
                    <td className="p-4 pr-6 text-right">
                      <button
                        onClick={() => setSelectedCandidateId(item.candidate_id)}
                        className="px-2.5 py-1 rounded-lg bg-blue-50 text-blue-700 hover:bg-blue-100 font-semibold text-xs transition-colors"
                      >
                        Inspect Result
                      </button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {selectedCandidateId && (
        <CandidateDetailModal
          candidateId={selectedCandidateId}
          onClose={() => setSelectedCandidateId(null)}
        />
      )}
    </div>
  );
};
