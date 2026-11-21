import React, { useState, useEffect } from 'react';
import { Check, Minus } from 'lucide-react';
import { jobsApi, candidatesApi, comparisonApi } from '../services/api';
import type { Job, Candidate, ComparisonResult } from '../types';
import { formatApiError } from '../utils/errors';

export const CompareCandidatesPage: React.FC = () => {
  const [jobs, setJobs] = useState<Job[]>([]);
  const [selectedJobId, setSelectedJobId] = useState<string>('');
  const [allCandidates, setAllCandidates] = useState<Candidate[]>([]);
  const [selectedCandidateIds, setSelectedCandidateIds] = useState<string[]>([]);
  const [comparison, setComparison] = useState<ComparisonResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const runCompare = async (jobId: string, candIds: string[]) => {
    if (!jobId || candIds.length < 2) {
      setComparison(null);
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const res = await comparisonApi.compareCandidates(jobId, candIds);
      setComparison(res);
    } catch (err: any) {
      setError(formatApiError(err, 'Comparison failed.'));
      setComparison(null);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    const fetchInit = async () => {
      try {
        const [jobsRes, candsRes] = await Promise.all([
          jobsApi.getJobs({ limit: 50 }),
          candidatesApi.getCandidates({ limit: 100 }),
        ]);
        setJobs(jobsRes.items);
        setAllCandidates(candsRes.items);

        if (jobsRes.items.length > 0) {
          const firstJobId = jobsRes.items[0].id;
          setSelectedJobId(firstJobId);

          // Pre-select first 3 candidates for immediate side-by-side comparison
          if (candsRes.items.length >= 2) {
            const initialThree = candsRes.items.slice(0, 3).map((c) => c.id);
            setSelectedCandidateIds(initialThree);
            runCompare(firstJobId, initialThree);
          }
        }
      } catch (e) {
        console.error(e);
      }
    };
    fetchInit();
  }, []);

  const handleToggleCandidate = (id: string) => {
    let updated: string[];
    if (selectedCandidateIds.includes(id)) {
      if (selectedCandidateIds.length <= 2) {
        setError('Select at least 2 candidates to compare.');
        return;
      }
      updated = selectedCandidateIds.filter((cId) => cId !== id);
    } else {
      if (selectedCandidateIds.length >= 5) {
        setError('Maximum 5 candidates can be compared simultaneously.');
        return;
      }
      updated = [...selectedCandidateIds, id];
    }
    setSelectedCandidateIds(updated);
    runCompare(selectedJobId, updated);
  };

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* ── Page Header ────────────────────────────────────────── */}
      <div>
        <h1 className="text-2xl font-black text-slate-900 tracking-tight flex items-center gap-2">
          Side-by-Side Candidate Comparison
          <span className="text-xs font-bold uppercase tracking-wider px-2 py-0.5 rounded-full bg-blue-100 text-blue-700">
            Multi-Candidate Matrix
          </span>
        </h1>
        <p className="text-xs text-slate-500 mt-1">
          Deep comparative analysis of skills, scoring breakdown, experience, and capability overlap.
        </p>
      </div>

      {error && (
        <div className="p-3 bg-amber-50 border border-amber-200 text-amber-800 rounded-xl text-xs">
          {error}
        </div>
      )}

      {/* ── Candidate Selector Chips ────────────────────────────── */}
      <div className="bg-white p-4 rounded-2xl border border-slate-200 shadow-sm space-y-3">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div className="flex items-center gap-2">
            <span className="text-xs font-bold text-slate-700 uppercase tracking-wider">
              Comparing Target Job:
            </span>
            <select
              value={selectedJobId}
              onChange={(e) => {
                setSelectedJobId(e.target.value);
                runCompare(e.target.value, selectedCandidateIds);
              }}
              className="p-1.5 rounded-lg border border-slate-300 text-xs font-semibold text-slate-900 bg-white outline-none"
            >
              {jobs.map((j) => (
                <option key={j.id} value={j.id}>
                  {j.title} ({j.company})
                </option>
              ))}
            </select>
          </div>
          <span className="text-xs text-slate-500">
            Selected: <strong className="text-blue-600">{selectedCandidateIds.length}</strong> / 5 Candidates
          </span>
        </div>

        <div className="flex flex-wrap gap-2 pt-2 border-t border-slate-100">
          {allCandidates.map((c) => {
            const isSelected = selectedCandidateIds.includes(c.id);
            return (
              <button
                key={c.id}
                onClick={() => handleToggleCandidate(c.id)}
                className={`px-3 py-1.5 rounded-xl text-xs font-semibold transition-all flex items-center gap-1.5 ${
                  isSelected
                    ? 'bg-blue-600 text-white shadow-sm shadow-blue-500/20'
                    : 'bg-slate-100 text-slate-700 hover:bg-slate-200'
                }`}
              >
                <span>{c.name}</span>
                {isSelected ? <Check className="w-3.5 h-3.5" /> : <span className="text-slate-400">+</span>}
              </button>
            );
          })}
        </div>
      </div>

      {loading ? (
        <div className="p-12 text-center text-slate-400 text-xs">
          Calculating comparative matrix...
        </div>
      ) : !comparison ? (
        <div className="p-12 text-center text-slate-400 text-xs">
          Select at least 2 candidates above to generate side-by-side comparison.
        </div>
      ) : (
        <div className="space-y-6">
          {/* ── Candidate Scoring Cards Grid ──────────────────────── */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
            {comparison.candidates.map((item) => {
              const c = item.candidate;
              const a = item.analysis;
              return (
                <div
                  key={c.id}
                  className="bg-white rounded-2xl border border-slate-200 shadow-sm p-5 space-y-4 flex flex-col justify-between"
                >
                  <div className="space-y-3">
                    <div className="flex items-start justify-between">
                      <div>
                        <h3 className="font-bold text-slate-900 text-sm">{c.name}</h3>
                        <p className="text-[11px] text-slate-500">{c.location || 'Remote'}</p>
                      </div>
                      <span className="px-2 py-0.5 rounded-full text-[10px] font-bold uppercase bg-blue-100 text-blue-700">
                        {c.status}
                      </span>
                    </div>

                    <div className="p-3 bg-slate-900 text-white rounded-xl flex items-center justify-between">
                      <span className="text-xs text-slate-400 font-medium">Overall Score</span>
                      <span className="text-xl font-black text-emerald-400">{a.overall_score}%</span>
                    </div>

                    <div className="space-y-1.5 text-xs">
                      <div className="flex justify-between text-slate-600">
                        <span>Technical (40):</span>
                        <span className="font-bold text-slate-900">{a.technical_score}</span>
                      </div>
                      <div className="flex justify-between text-slate-600">
                        <span>Semantic (30):</span>
                        <span className="font-bold text-slate-900">{a.semantic_score}</span>
                      </div>
                      <div className="flex justify-between text-slate-600">
                        <span>Experience (20):</span>
                        <span className="font-bold text-slate-900">{a.experience_score} ({c.total_experience_years}y)</span>
                      </div>
                      <div className="flex justify-between text-slate-600">
                        <span>Education (10):</span>
                        <span className="font-bold text-slate-900">{a.education_score}</span>
                      </div>
                    </div>
                  </div>

                  <div className="pt-3 border-t border-slate-100 text-xs">
                    <p className="text-[11px] font-bold text-slate-400 uppercase tracking-wider mb-1">
                      Strengths Summary:
                    </p>
                    <p className="text-[11px] text-slate-700 line-clamp-2 leading-relaxed">
                      {a.strengths?.[0] || 'Strong alignment across core requirements.'}
                    </p>
                  </div>
                </div>
              );
            })}
          </div>

          {/* ── Full Skill Overlap Matrix ─────────────────────────── */}
          <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden p-6 space-y-4">
            <div>
              <h3 className="text-sm font-bold text-slate-900">Skill Competency Overlap Matrix</h3>
              <p className="text-xs text-slate-500">
                Direct verification of technical capabilities across selected candidates.
              </p>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs">
                <thead className="bg-slate-50 border-b border-slate-200 text-slate-500 font-bold uppercase tracking-wider text-[11px]">
                  <tr>
                    <th className="p-3 pl-4">Skill / Requirement</th>
                    {comparison.candidates.map((item) => (
                      <th key={item.candidate.id} className="p-3 text-center">
                        {item.candidate.name}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                  {comparison.skill_overlap.map((entry, idx) => (
                    <tr key={idx} className="hover:bg-slate-50 transition-colors">
                      <td className="p-3 pl-4 font-bold text-slate-900">{entry.skill}</td>
                      {comparison.candidates.map((item) => {
                        const hasSkill = entry.candidates[item.candidate.id];
                        return (
                          <td key={item.candidate.id} className="p-3 text-center">
                            {hasSkill ? (
                              <span className="inline-flex items-center justify-center w-6 h-6 rounded-full bg-emerald-100 text-emerald-700">
                                <Check className="w-3.5 h-3.5 stroke-[3]" />
                              </span>
                            ) : (
                              <span className="inline-flex items-center justify-center w-6 h-6 rounded-full bg-slate-100 text-slate-400">
                                <Minus className="w-3.5 h-3.5" />
                              </span>
                            )}
                          </td>
                        );
                      })}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
