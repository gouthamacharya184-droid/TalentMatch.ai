import React, { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import {
  Search,
  AlertCircle,
  FileSpreadsheet,
  FileText,
  FileCode,
  BookmarkCheck,
  Sparkles,
  GraduationCap,
  ChevronLeft,
  ChevronRight
} from 'lucide-react';
import { jobsApi, matchingApi, shortlistApi, analyticsApi } from '../services/api';
import type { Job, MatchingAnalysis, WhatIfSimulationResponse } from '../types';
import { CandidateDetailModal } from '../components/CandidateDetailModal';
import { formatApiError } from '../utils/errors';

export const CandidateRankingPage: React.FC = () => {
  const [searchParams] = useSearchParams();
  const initialJobId = searchParams.get('job_id') || '';

  const [jobs, setJobs] = useState<Job[]>([]);
  const [selectedJobId, setSelectedJobId] = useState<string>(initialJobId);
  const [rankings, setRankings] = useState<MatchingAnalysis[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [minScore, setMinScore] = useState<number>(0);
  const [minExperience, setMinExperience] = useState<number>(0);
  const [sortBy, setSortBy] = useState('overall_score');
  const [sortOrder] = useState<'desc' | 'asc'>('desc');
  const [selectedCandidateId, setSelectedCandidateId] = useState<string | null>(null);
  const [exporting, setExporting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // What-If Simulator state
  const [isWhatIfOpen, setIsWhatIfOpen] = useState(false);
  const [weights, setWeights] = useState({
    required_skills: 35,
    relevant_projects: 25,
    professional_experience: 15,
    preferred_skills: 15,
    education_certifications: 10,
  });
  const [simulating, setSimulating] = useState(false);
  const [simulationResult, setSimulationResult] = useState<WhatIfSimulationResponse | null>(null);
  const [simError, setSimError] = useState<string | null>(null);

  const totalSimWeight =
    weights.required_skills +
    weights.relevant_projects +
    weights.professional_experience +
    weights.preferred_skills +
    weights.education_certifications;

  const handleRunSimulation = async () => {
    if (!selectedJobId) return;
    setSimulating(true);
    setSimError(null);
    try {
      const res = await matchingApi.simulateWhatIf({
        job_id: selectedJobId,
        custom_weights: weights,
      });
      setSimulationResult(res);
    } catch (e: any) {
      console.error(e);
      setSimError(formatApiError(e, 'Failed to execute What-If simulation.'));
    } finally {
      setSimulating(false);
    }
  };

  // Pagination state
  const [currentPage, setCurrentPage] = useState<number>(1);
  const [pageSize, setPageSize] = useState<number>(10);

  useEffect(() => {
    const fetchJobs = async () => {
      try {
        const res = await jobsApi.getJobs({ limit: 50 });
        const items = res?.items ?? [];
        setJobs(items);
        if (!selectedJobId && items.length > 0) {
          setSelectedJobId(items[0].id);
        }
      } catch (e: any) {
        console.error(e);
        setJobs([]);
        setError('Failed to load active jobs for ranking analysis.');
      }
    };
    fetchJobs();
  }, []);

  const fetchRankings = async () => {
    if (!selectedJobId) return;
    setLoading(true);
    setError(null);
    try {
      const data = await matchingApi.getRankings(selectedJobId, {
        sort_by: sortBy,
        sort_order: sortOrder,
        min_score: minScore > 0 ? minScore : undefined,
      });
      setRankings(Array.isArray(data) ? data : []);
    } catch (e: any) {
      console.error(e);
      setRankings([]);
      setError(formatApiError(e, 'Failed to retrieve candidate rankings.'));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchRankings();
    setCurrentPage(1);
  }, [selectedJobId, sortBy, sortOrder, minScore]);

  useEffect(() => {
    setCurrentPage(1);
  }, [search, minExperience]);

  const handleExport = async (format: 'csv' | 'xlsx' | 'pdf') => {
    if (!selectedJobId) return;
    setExporting(true);
    try {
      const blob = await analyticsApi.exportReport(selectedJobId, format);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `TalentMatch_Rankings.${format}`;
      a.click();
    } catch (e) {
      console.error(e);
      alert(`Exporting ${format.toUpperCase()} report failed.`);
    } finally {
      setExporting(false);
    }
  };

  const handleShortlist = async (candidateId: string) => {
    if (!selectedJobId) return;
    try {
      await shortlistApi.addToShortlist(selectedJobId, candidateId, 'Shortlisted from Leaderboard');
      fetchRankings();
    } catch (e) {
      console.error(e);
    }
  };

  // Filter local search by candidate name, email, designation, or verified skills
  const filteredRankings = rankings.filter((r) => {
    if (minExperience > 0) {
      const exp = r.candidate?.total_experience_years || 0;
      if (exp < minExperience) return false;
    }
    if (!search.trim()) return true;
    const term = search.toLowerCase();
    const name = r.candidate?.name?.toLowerCase() || '';
    const email = r.candidate?.email?.toLowerCase() || '';
    const desig = (((r.candidate?.extracted_profile as any)?.experience?.[0]?.title) || '').toLowerCase();
    const skills = (r.candidate?.skills || []).map((s) => s.skill_name.toLowerCase()).join(' ');
    return name.includes(term) || email.includes(term) || desig.includes(term) || skills.includes(term);
  });

  // Calculate pagination slice
  const totalPages = Math.ceil(filteredRankings.length / pageSize) || 1;
  const startIndex = (currentPage - 1) * pageSize;
  const paginatedRankings = filteredRankings.slice(startIndex, startIndex + pageSize);

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* ── Page Header ────────────────────────────────────────── */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-black text-slate-900 tracking-tight flex items-center gap-2">
            Candidate Ranking Leaderboard
            <span className="text-xs font-bold uppercase tracking-wider px-2 py-0.5 rounded-full bg-blue-100 text-blue-700">
              Verified AI Rankings
            </span>
          </h1>
          <p className="text-xs text-slate-500 mt-1">
            Dynamic, explainable candidate ranking grounded in 4-component weighted scoring: Technical (40%), Semantic (30%), Experience (20%), Education (10%).
          </p>
        </div>

        {/* Export & Simulator Buttons */}
        <div className="flex items-center gap-2">
          <button
            onClick={() => setIsWhatIfOpen(true)}
            disabled={!selectedJobId || rankings.length === 0}
            className="flex items-center gap-1.5 px-3 py-2 rounded-xl bg-purple-600 text-white text-xs font-semibold hover:bg-purple-700 transition-colors shadow-sm disabled:opacity-50"
            title="Simulate candidate rankings under custom scoring weights"
          >
            <Sparkles className="w-3.5 h-3.5" />
            <span>What-If Simulator</span>
          </button>
          <button
            onClick={() => handleExport('csv')}
            disabled={exporting || rankings.length === 0}
            className="flex items-center gap-1.5 px-3 py-2 rounded-xl bg-white border border-slate-200 text-xs font-semibold text-slate-700 hover:bg-slate-50 transition-colors shadow-sm disabled:opacity-50"
            title="Download CSV report of candidate scores"
          >
            <FileCode className="w-3.5 h-3.5 text-blue-600" />
            <span>CSV</span>
          </button>
          <button
            onClick={() => handleExport('xlsx')}
            disabled={exporting || rankings.length === 0}
            className="flex items-center gap-1.5 px-3 py-2 rounded-xl bg-white border border-slate-200 text-xs font-semibold text-slate-700 hover:bg-slate-50 transition-colors shadow-sm disabled:opacity-50"
            title="Download formatted Excel spreadsheet"
          >
            <FileSpreadsheet className="w-3.5 h-3.5 text-emerald-600" />
            <span>Excel</span>
          </button>
          <button
            onClick={() => handleExport('pdf')}
            disabled={exporting || rankings.length === 0}
            className="flex items-center gap-1.5 px-3 py-2 rounded-xl bg-white border border-slate-200 text-xs font-semibold text-slate-700 hover:bg-slate-50 transition-colors shadow-sm disabled:opacity-50"
            title="Download executive candidate summary report in PDF"
          >
            <FileText className="w-3.5 h-3.5 text-rose-600" />
            <span>PDF Report</span>
          </button>
        </div>
      </div>

      {error && (
        <div className="p-3 bg-rose-50 border border-rose-200 text-rose-800 rounded-xl text-xs flex items-center gap-2">
          <AlertCircle className="w-4 h-4 text-rose-600 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* ── Filter Bar ─────────────────────────────────────────── */}
      <div className="bg-white p-4 rounded-2xl border border-slate-200 shadow-sm grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3 text-xs">
        <div>
          <label className="block text-[11px] font-semibold text-slate-500 mb-1">Target Job</label>
          <select
            value={selectedJobId}
            onChange={(e) => setSelectedJobId(e.target.value)}
            className="w-full p-2 rounded-lg border border-slate-300 font-semibold text-slate-900 bg-white outline-none focus:border-blue-600"
          >
            {jobs.map((j) => (
              <option key={j.id} value={j.id}>
                {j.title} ({j.company})
              </option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-[11px] font-semibold text-slate-500 mb-1">Sort Metric</label>
          <select
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value)}
            className="w-full p-2 rounded-lg border border-slate-300 font-medium text-slate-800 bg-white outline-none focus:border-blue-600"
          >
            <option value="overall_score">Overall Score (100 pts)</option>
            <option value="technical_score">Technical Skills (40 pts)</option>
            <option value="semantic_score">Semantic Similarity (30 pts)</option>
            <option value="experience_score">Experience Match (20 pts)</option>
            <option value="education_score">Education Match (10 pts)</option>
            <option value="candidate_experience">Total Experience Years</option>
          </select>
        </div>

        <div>
          <label className="block text-[11px] font-semibold text-slate-500 mb-1">
            Min Score: {minScore > 0 ? `${minScore}%` : 'All'}
          </label>
          <input
            type="range"
            min="0"
            max="90"
            step="5"
            value={minScore}
            onChange={(e) => setMinScore(Number(e.target.value))}
            className="w-full h-2 bg-slate-200 rounded-lg cursor-pointer accent-blue-600 mt-2"
          />
        </div>

        <div>
          <label className="block text-[11px] font-semibold text-slate-500 mb-1">
            Min Experience: {minExperience > 0 ? `${minExperience} yrs+` : 'All'}
          </label>
          <input
            type="range"
            min="0"
            max="15"
            step="1"
            value={minExperience}
            onChange={(e) => setMinExperience(Number(e.target.value))}
            className="w-full h-2 bg-slate-200 rounded-lg cursor-pointer accent-blue-600 mt-2"
          />
        </div>

        <div>
          <label className="block text-[11px] font-semibold text-slate-500 mb-1">Search Candidates</label>
          <div className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-lg border border-slate-300 bg-white">
            <Search className="w-3.5 h-3.5 text-slate-400" />
            <input
              type="text"
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Name, title, or skill..."
              className="w-full text-xs outline-none bg-transparent"
            />
          </div>
        </div>
      </div>

      {/* ── Ranking Table ──────────────────────────────────────── */}
      <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-50 border-b border-slate-200 text-slate-500 font-bold uppercase tracking-wider text-[11px]">
              <tr>
                <th className="p-4 pl-6">Rank</th>
                <th className="p-4">Candidate & Designation</th>
                <th className="p-4">Education</th>
                <th className="p-4">Experience</th>
                <th className="p-4">Overall Score</th>
                <th className="p-4">Tech (40)</th>
                <th className="p-4">Semantic (30)</th>
                <th className="p-4">Exp (20)</th>
                <th className="p-4">Edu (10)</th>
                <th className="p-4">Skills Alignment</th>
                <th className="p-4">Status</th>
                <th className="p-4 pr-6 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {loading ? (
                <tr>
                  <td colSpan={12} className="p-8 text-center text-slate-400">
                    <div className="flex items-center justify-center gap-2">
                      <div className="w-4 h-4 border-2 border-blue-600 border-t-transparent rounded-full animate-spin"></div>
                      <span>Calculating dynamic matching scores...</span>
                    </div>
                  </td>
                </tr>
              ) : filteredRankings.length === 0 ? (
                <tr>
                  <td colSpan={12} className="p-8 text-center text-slate-400">
                    No matching candidates found for this filter criteria. Try adjusting the score or experience threshold.
                  </td>
                </tr>
              ) : (
                paginatedRankings.map((r, pageIdx) => {
                  const globalRank = startIndex + pageIdx + 1;
                  const designation =
                    ((r.candidate?.extracted_profile as any)?.experience?.[0]?.title) ||
                    ((r.candidate?.extracted_profile as any)?.bio ? 'Software Professional' : 'Candidate');
                  const eduList = Array.isArray(r.candidate?.education) ? (r.candidate.education as any[]) : [];
                  const eduRecord = eduList.length > 0 && eduList[0]?.degree ? eduList[0].degree : 'Degree not listed';

                  return (
                    <tr key={r.id} className="hover:bg-slate-50 transition-colors">
                      <td className="p-4 pl-6">
                        <span
                          className={`w-7 h-7 rounded-xl inline-flex items-center justify-center font-black text-xs ${
                            globalRank === 1
                              ? 'bg-amber-100 text-amber-800 border border-amber-300 shadow-sm'
                              : globalRank === 2
                              ? 'bg-slate-200 text-slate-800 border border-slate-300'
                              : globalRank === 3
                              ? 'bg-amber-50 text-amber-900 border border-amber-200'
                              : 'bg-slate-100 text-slate-500'
                          }`}
                        >
                          {globalRank}
                        </span>
                      </td>
                      <td className="p-4">
                        <p className="font-bold text-slate-900 text-sm">{r.candidate?.name}</p>
                        <p className="text-[11px] text-blue-600 font-medium truncate max-w-[180px]">{designation}</p>
                        <p className="text-[10px] text-slate-400">{r.candidate?.email}</p>
                      </td>
                      <td className="p-4 text-slate-600 font-medium truncate max-w-[140px]" title={String(eduRecord)}>
                        <div className="flex items-center gap-1">
                          <GraduationCap className="w-3 h-3 text-slate-400 shrink-0" />
                          <span className="truncate">{eduRecord}</span>
                        </div>
                      </td>
                      <td className="p-4 text-slate-600 font-medium whitespace-nowrap">
                        {r.candidate?.total_experience_years} Yrs
                      </td>
                      <td className="p-4">
                        <div className="flex items-center gap-2">
                          <span className="font-black text-base text-emerald-600">
                            {r.overall_score}%
                          </span>
                          <div className="w-16 bg-slate-100 h-1.5 rounded-full overflow-hidden hidden sm:block">
                            <div
                              className="bg-emerald-500 h-1.5 rounded-full"
                              style={{ width: `${r.overall_score}%` }}
                            ></div>
                          </div>
                        </div>
                      </td>
                      <td className="p-4 font-semibold text-slate-800">{r.technical_score}</td>
                      <td className="p-4 font-semibold text-slate-800">{r.semantic_score}</td>
                      <td className="p-4 font-semibold text-slate-800">{r.experience_score}</td>
                      <td className="p-4 font-semibold text-slate-800">{r.education_score}</td>
                      <td className="p-4 whitespace-nowrap">
                        <span className="px-2 py-0.5 rounded bg-emerald-50 text-emerald-700 font-semibold text-[10px] mr-1">
                          {r.matched_skills?.length || 0} Matched
                        </span>
                        {(r.missing_skills?.length || 0) > 0 && (
                          <span className="px-2 py-0.5 rounded bg-rose-50 text-rose-700 font-semibold text-[10px]">
                            {r.missing_skills.length} Missing
                          </span>
                        )}
                      </td>
                      <td className="p-4 whitespace-nowrap">
                        <span
                          className={`px-2.5 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider ${
                            r.candidate?.status === 'shortlisted'
                              ? 'bg-amber-100 text-amber-800'
                              : r.candidate?.status === 'interview'
                              ? 'bg-purple-100 text-purple-800'
                              : 'bg-blue-100 text-blue-800'
                          }`}
                        >
                          {r.candidate?.status?.replace('_', ' ') || 'Analyzed'}
                        </span>
                      </td>
                      <td className="p-4 pr-6 text-right space-x-1.5 whitespace-nowrap">
                        <button
                          onClick={() => setSelectedCandidateId(r.candidate_id)}
                          className="px-2.5 py-1 rounded-lg bg-blue-50 text-blue-700 hover:bg-blue-100 font-semibold text-xs transition-colors"
                        >
                          Inspect
                        </button>
                        <button
                          onClick={() => handleShortlist(r.candidate_id)}
                          title="Shortlist Candidate"
                          className="p-1 rounded-lg border border-slate-200 text-slate-600 hover:text-amber-600 hover:bg-amber-50 transition-colors"
                        >
                          <BookmarkCheck className="w-4 h-4" />
                        </button>
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>

        {/* ── Pagination Controls ─────────────────────────────────── */}
        {filteredRankings.length > 0 && (
          <div className="p-4 border-t border-slate-200 flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs text-slate-600">
            <div className="flex items-center gap-2">
              <span>
                Showing <span className="font-bold text-slate-900">{startIndex + 1}</span> to{' '}
                <span className="font-bold text-slate-900">
                  {Math.min(startIndex + pageSize, filteredRankings.length)}
                </span>{' '}
                of <span className="font-bold text-slate-900">{filteredRankings.length}</span> candidates
              </span>
              <span className="text-slate-300">|</span>
              <div className="flex items-center gap-1.5">
                <span>Per Page:</span>
                <select
                  value={pageSize}
                  onChange={(e) => {
                    setPageSize(Number(e.target.value));
                    setCurrentPage(1);
                  }}
                  className="px-2 py-1 rounded border border-slate-300 bg-white font-medium text-slate-800 outline-none"
                >
                  <option value={10}>10</option>
                  <option value={20}>20</option>
                  <option value={50}>50</option>
                </select>
              </div>
            </div>

            <div className="flex items-center gap-1.5 self-end sm:self-auto">
              <button
                onClick={() => setCurrentPage((p) => Math.max(1, p - 1))}
                disabled={currentPage === 1}
                className="flex items-center gap-1 px-3 py-1.5 rounded-lg border border-slate-200 bg-white font-medium hover:bg-slate-50 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
              >
                <ChevronLeft className="w-3.5 h-3.5" />
                <span>Previous</span>
              </button>

              <span className="px-2 font-bold text-slate-800">
                Page {currentPage} of {totalPages}
              </span>

              <button
                onClick={() => setCurrentPage((p) => Math.min(totalPages, p + 1))}
                disabled={currentPage === totalPages}
                className="flex items-center gap-1 px-3 py-1.5 rounded-lg border border-slate-200 bg-white font-medium hover:bg-slate-50 disabled:opacity-40 disabled:cursor-not-allowed transition-colors"
              >
                <span>Next</span>
                <ChevronRight className="w-3.5 h-3.5" />
              </button>
            </div>
          </div>
        )}
      </div>

      {/* ── What-If Sensitivity Simulator Modal ──────────────── */}
      {isWhatIfOpen && (
        <div className="fixed inset-0 z-50 bg-slate-900/40 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-3xl w-full p-6 shadow-2xl border border-slate-200 max-h-[90vh] flex flex-col">
            <div className="flex items-center justify-between pb-3 border-b border-slate-100">
              <div className="flex items-center gap-2">
                <Sparkles className="w-5 h-5 text-purple-600" />
                <div>
                  <h3 className="font-bold text-slate-900 text-base">
                    What-If Sensitivity Simulator
                  </h3>
                  <p className="text-[11px] text-slate-500">
                    Test how ranking and scores shift across {rankings.length} candidates when adjusting criteria weights.
                  </p>
                </div>
              </div>
              <button
                onClick={() => setIsWhatIfOpen(false)}
                className="text-slate-400 hover:text-slate-600 p-1 text-lg font-bold"
              >
                &times;
              </button>
            </div>

            <div className="flex-1 overflow-y-auto py-4 space-y-4">
              {/* Sliders Grid */}
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3 p-4 bg-purple-50/50 rounded-xl border border-purple-100 text-xs">
                <div>
                  <div className="flex justify-between font-semibold text-slate-700 mb-1">
                    <span>Required Skills</span>
                    <span className="font-bold text-purple-700">{weights.required_skills}%</span>
                  </div>
                  <input
                    type="range"
                    min="0"
                    max="100"
                    step="5"
                    value={weights.required_skills}
                    onChange={(e) =>
                      setWeights({ ...weights, required_skills: Number(e.target.value) })
                    }
                    className="w-full accent-purple-600"
                  />
                </div>

                <div>
                  <div className="flex justify-between font-semibold text-slate-700 mb-1">
                    <span>Relevant Projects</span>
                    <span className="font-bold text-purple-700">{weights.relevant_projects}%</span>
                  </div>
                  <input
                    type="range"
                    min="0"
                    max="100"
                    step="5"
                    value={weights.relevant_projects}
                    onChange={(e) =>
                      setWeights({ ...weights, relevant_projects: Number(e.target.value) })
                    }
                    className="w-full accent-purple-600"
                  />
                </div>

                <div>
                  <div className="flex justify-between font-semibold text-slate-700 mb-1">
                    <span>Experience History</span>
                    <span className="font-bold text-purple-700">
                      {weights.professional_experience}%
                    </span>
                  </div>
                  <input
                    type="range"
                    min="0"
                    max="100"
                    step="5"
                    value={weights.professional_experience}
                    onChange={(e) =>
                      setWeights({ ...weights, professional_experience: Number(e.target.value) })
                    }
                    className="w-full accent-purple-600"
                  />
                </div>

                <div>
                  <div className="flex justify-between font-semibold text-slate-700 mb-1">
                    <span>Preferred Skills</span>
                    <span className="font-bold text-purple-700">{weights.preferred_skills}%</span>
                  </div>
                  <input
                    type="range"
                    min="0"
                    max="100"
                    step="5"
                    value={weights.preferred_skills}
                    onChange={(e) =>
                      setWeights({ ...weights, preferred_skills: Number(e.target.value) })
                    }
                    className="w-full accent-purple-600"
                  />
                </div>

                <div>
                  <div className="flex justify-between font-semibold text-slate-700 mb-1">
                    <span>Education & Certs</span>
                    <span className="font-bold text-purple-700">
                      {weights.education_certifications}%
                    </span>
                  </div>
                  <input
                    type="range"
                    min="0"
                    max="100"
                    step="5"
                    value={weights.education_certifications}
                    onChange={(e) =>
                      setWeights({ ...weights, education_certifications: Number(e.target.value) })
                    }
                    className="w-full accent-purple-600"
                  />
                </div>

                <div className="flex flex-col justify-center items-center p-2 rounded-lg bg-white border border-purple-200">
                  <span className="text-[10px] uppercase font-bold text-slate-400">Total Weight</span>
                  <span
                    className={`text-base font-black ${
                      totalSimWeight === 100 ? 'text-emerald-600' : 'text-amber-600'
                    }`}
                  >
                    {totalSimWeight}%
                  </span>
                  {totalSimWeight !== 100 && (
                    <span className="text-[10px] text-amber-600">Auto-normalized</span>
                  )}
                </div>
              </div>

              <div className="flex justify-between items-center">
                <button
                  onClick={() =>
                    setWeights({
                      required_skills: 35,
                      relevant_projects: 25,
                      professional_experience: 15,
                      preferred_skills: 15,
                      education_certifications: 10,
                    })
                  }
                  className="text-xs text-slate-500 hover:text-slate-800 underline"
                >
                  Reset to Default Weights
                </button>

                <button
                  onClick={handleRunSimulation}
                  disabled={simulating}
                  className="px-4 py-2 rounded-xl bg-purple-600 text-white text-xs font-semibold hover:bg-purple-700 disabled:opacity-50 flex items-center gap-2 shadow-xs"
                >
                  {simulating ? (
                    <>
                      <div className="w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                      <span>Simulating Sensitivity...</span>
                    </>
                  ) : (
                    <>
                      <Sparkles className="w-3.5 h-3.5" />
                      <span>Run Simulation</span>
                    </>
                  )}
                </button>
              </div>

              {simError && <p className="text-xs text-rose-600 font-medium">{simError}</p>}

              {/* Simulation Results Table */}
              {simulationResult && (
                <div className="space-y-2 pt-2 border-t border-slate-100">
                  <div className="flex items-center justify-between text-xs font-bold text-slate-700">
                    <span>Simulated Sensitivity Results ({simulationResult.total_candidates} candidates)</span>
                    <span className="text-emerald-700 font-medium text-[11px]">Normalized to 100%</span>
                  </div>

                  <div className="overflow-x-auto border border-slate-200 rounded-xl max-h-72">
                    <table className="w-full text-left text-xs">
                      <thead className="bg-slate-50 border-b border-slate-200 text-[10px] uppercase font-bold text-slate-500">
                        <tr>
                          <th className="p-2.5">Sim. Rank</th>
                          <th className="p-2.5">Candidate Name</th>
                          <th className="p-2.5">Score Shift</th>
                          <th className="p-2.5">Rank Delta</th>
                          <th className="p-2.5 text-right">Simulated Score</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-slate-100">
                        {simulationResult.rankings.map((c) => {
                          const isPositiveRank = c.rank_delta > 0;
                          const isNegativeRank = c.rank_delta < 0;
                          return (
                            <tr key={c.candidate_id} className="hover:bg-slate-50">
                              <td className="p-2.5 font-bold text-slate-900">#{c.simulated_rank}</td>
                              <td className="p-2.5 font-semibold text-slate-800">{c.candidate_name}</td>
                              <td className="p-2.5">
                                <span className="text-slate-400 font-mono text-[11px]">
                                  {c.previous_score.toFixed(1)} →{' '}
                                </span>
                                <span className="font-bold text-slate-900 font-mono text-[11px]">
                                  {c.simulated_score.toFixed(1)}
                                </span>
                                <span
                                  className={`ml-1 text-[10px] font-bold ${
                                    c.score_delta >= 0 ? 'text-emerald-600' : 'text-rose-600'
                                  }`}
                                >
                                  ({c.score_delta >= 0 ? '+' : ''}
                                  {c.score_delta.toFixed(1)})
                                </span>
                              </td>
                              <td className="p-2.5">
                                <span
                                  className={`inline-flex items-center gap-0.5 px-2 py-0.5 rounded text-[10px] font-bold ${
                                    isPositiveRank
                                      ? 'bg-emerald-100 text-emerald-800'
                                      : isNegativeRank
                                      ? 'bg-rose-100 text-rose-800'
                                      : 'bg-slate-100 text-slate-600'
                                  }`}
                                >
                                  {isPositiveRank ? '▲ +' : isNegativeRank ? '▼ ' : '▬ '}
                                  {c.rank_delta}
                                </span>
                              </td>
                              <td className="p-2.5 text-right font-black text-purple-700">
                                {c.simulated_score.toFixed(1)}%
                              </td>
                            </tr>
                          );
                        })}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}
            </div>

            <div className="pt-3 border-t border-slate-100 flex justify-end">
              <button
                onClick={() => setIsWhatIfOpen(false)}
                className="px-4 py-2 rounded-xl bg-slate-100 text-slate-700 text-xs font-semibold hover:bg-slate-200"
              >
                Close Simulator
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Candidate Modal */}
      {selectedCandidateId && (
        <CandidateDetailModal
          candidateId={selectedCandidateId}
          jobId={selectedJobId}
          onClose={() => setSelectedCandidateId(null)}
          onStatusChange={fetchRankings}
        />
      )}
    </div>
  );
};
