import React, { useState, useEffect } from 'react';
import {
  HelpCircle,
  Briefcase,
  Users,
  Search,
  Sparkles,
  Download,
  Printer,
  CheckCircle2,
  AlertTriangle,
  Code2,
  FileCheck2,
  Filter,
  Plus,
  ChevronRight,
  BookOpen
} from 'lucide-react';
import { interviewKitsApi, jobsApi, candidatesApi } from '../services/api';
import type { InterviewKit, Job, Candidate, InterviewQuestionItem } from '../types';
import { formatApiError } from '../utils/errors';

export const InterviewIntelligencePage: React.FC = () => {
  const [kits, setKits] = useState<InterviewKit[]>([]);
  const [jobs, setJobs] = useState<Job[]>([]);
  const [candidates, setCandidates] = useState<Candidate[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedKit, setSelectedKit] = useState<InterviewKit | null>(null);
  const [selectedCategory, setSelectedCategory] = useState<string>('all');
  const [generating, setGenerating] = useState(false);
  const [isGenerateOpen, setIsGenerateOpen] = useState(false);

  // New Kit Form State
  const [genJobId, setGenJobId] = useState('');
  const [genCandidateId, setGenCandidateId] = useState('');
  const [error, setError] = useState<string | null>(null);

  const fetchKits = async () => {
    setLoading(true);
    try {
      const data = await interviewKitsApi.listKits();
      setKits(data);
      if (data.length > 0 && !selectedKit) {
        setSelectedKit(data[0]);
      }
    } catch (e) {
      console.error(e);
      setError('Failed to fetch interview kits.');
    } finally {
      setLoading(false);
    }
  };

  const fetchMeta = async () => {
    try {
      const [jobsRes, candRes] = await Promise.all([
        jobsApi.getJobs({ limit: 100 }),
        candidatesApi.getCandidates({ limit: 100 }),
      ]);
      setJobs(jobsRes.items);
      setCandidates(candRes.items);
    } catch (e) {
      console.error(e);
    }
  };

  useEffect(() => {
    fetchKits();
    fetchMeta();
  }, []);

  const handleGenerate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!genJobId || !genCandidateId) return;
    setGenerating(true);
    setError(null);
    try {
      const newKit = await interviewKitsApi.generateKit(genJobId, genCandidateId);
      setIsGenerateOpen(false);
      setGenJobId('');
      setGenCandidateId('');
      setKits([newKit, ...kits]);
      setSelectedKit(newKit);
    } catch (err) {
      console.error(err);
      setError(formatApiError(err, 'Failed to generate tailored interview kit.'));
    } finally {
      setGenerating(false);
    }
  };

  const handlePrint = () => {
    window.print();
  };

  const filteredQuestions = selectedKit?.questions?.filter((q) =>
    selectedCategory === 'all' ? true : q.category.toLowerCase() === selectedCategory.toLowerCase()
  ) || [];

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* ── Page Header ────────────────────────────────────────── */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-black text-slate-900 tracking-tight">
            Interview Intelligence
          </h1>
          <p className="text-xs text-slate-500 mt-1">
            Personalized, evidence-grounded interview kits with claim verification rubrics and expected indicators.
          </p>
        </div>

        <button
          onClick={() => setIsGenerateOpen(true)}
          className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-blue-600 text-white text-xs font-semibold hover:bg-blue-700 transition-colors shadow-md shadow-blue-500/20 shrink-0"
        >
          <Sparkles className="w-4 h-4" />
          <span>Generate New Kit</span>
        </button>
      </div>

      {/* ── Content Layout: Left Kit Selector + Right Detail View ── */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        {/* Left Column: Kits List (4 cols) */}
        <div className="lg:col-span-4 bg-white rounded-2xl border border-slate-200 shadow-sm p-4 space-y-3">
          <div className="flex items-center justify-between pb-2 border-b border-slate-100">
            <h3 className="text-xs font-bold text-slate-900 uppercase tracking-wider">
              Saved Kits ({kits.length})
            </h3>
            <span className="text-[11px] text-slate-400">Agentic Generation</span>
          </div>

          {loading ? (
            <div className="text-center py-12">
              <div className="w-6 h-6 border-2 border-blue-600 border-t-transparent rounded-full animate-spin mx-auto mb-2"></div>
              <p className="text-xs text-slate-400">Loading interview kits...</p>
            </div>
          ) : kits.length === 0 ? (
            <div className="text-center py-12">
              <BookOpen className="w-8 h-8 text-slate-300 mx-auto mb-2" />
              <p className="text-xs text-slate-500 font-medium">No interview kits generated yet.</p>
              <p className="text-[11px] text-slate-400 mt-1">
                Generate one against candidate resumes and job criteria.
              </p>
            </div>
          ) : (
            <div className="space-y-2 max-h-[640px] overflow-y-auto pr-1">
              {kits.map((k) => {
                const isSelected = selectedKit?.id === k.id;
                const candidateName = k.candidate?.name || 'Candidate ' + k.candidate_id.substring(0, 6);
                const jobTitle = k.job?.title || 'Job Opening ' + k.job_id.substring(0, 6);

                return (
                  <button
                    key={k.id}
                    onClick={() => setSelectedKit(k)}
                    className={`w-full text-left p-3 rounded-xl border transition-all ${
                      isSelected
                        ? 'bg-blue-50/80 border-blue-300 shadow-xs'
                        : 'bg-white border-slate-200/80 hover:bg-slate-50'
                    }`}
                  >
                    <div className="flex items-center justify-between mb-1">
                      <span className="font-bold text-xs text-slate-900 truncate">
                        {candidateName}
                      </span>
                      <span className="text-[10px] font-semibold text-blue-700 bg-blue-100/80 px-1.5 py-0.5 rounded">
                        {k.questions?.length || 0} Qs
                      </span>
                    </div>
                    <p className="text-[11px] text-slate-500 truncate flex items-center gap-1">
                      <Briefcase className="w-3 h-3 text-slate-400 shrink-0" />
                      <span>{jobTitle}</span>
                    </p>
                    <span className="text-[10px] text-slate-400 block mt-1">
                      {k.created_at ? new Date(k.created_at).toLocaleDateString() : 'Recent'}
                    </span>
                  </button>
                );
              })}
            </div>
          )}
        </div>

        {/* Right Column: Active Kit Inspection (8 cols) */}
        <div className="lg:col-span-8 bg-white rounded-2xl border border-slate-200 shadow-sm p-6 space-y-6">
          {selectedKit ? (
            <>
              {/* Header Info */}
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-5 border-b border-slate-100">
                <div>
                  <div className="flex items-center gap-2">
                    <h2 className="text-lg font-bold text-slate-900">
                      {selectedKit.candidate?.name || 'Candidate Interview Dossier'}
                    </h2>
                    <span className="px-2 py-0.5 rounded bg-emerald-100 text-emerald-800 text-[10px] font-bold uppercase">
                      Evidence Grounded
                    </span>
                  </div>
                  <p className="text-xs text-slate-500 mt-0.5">
                    Job Role: <span className="font-semibold text-slate-700">{selectedKit.job?.title || selectedKit.job_id}</span>
                  </p>
                </div>

                <div className="flex items-center gap-2">
                  <button
                    onClick={handlePrint}
                    className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl border border-slate-200 bg-white text-slate-700 text-xs font-semibold hover:bg-slate-50 transition-colors"
                  >
                    <Printer className="w-3.5 h-3.5" />
                    <span>Print Kit</span>
                  </button>
                </div>
              </div>

              {/* Category Filter Pills */}
              <div className="flex flex-wrap items-center gap-2">
                <span className="text-xs font-bold text-slate-400 uppercase tracking-wider mr-1">
                  Category:
                </span>
                {['all', 'technical', 'project', 'coding', 'claim_verification', 'behavioral'].map((cat) => (
                  <button
                    key={cat}
                    onClick={() => setSelectedCategory(cat)}
                    className={`px-3 py-1 rounded-lg text-xs font-semibold capitalize transition-colors ${
                      selectedCategory === cat
                        ? 'bg-blue-600 text-white'
                        : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
                    }`}
                  >
                    {cat.replace('_', ' ')}
                  </button>
                ))}
              </div>

              {/* Questions Stream */}
              <div className="space-y-4">
                {filteredQuestions.length === 0 ? (
                  <p className="text-xs text-slate-400 italic py-6 text-center">
                    No questions under the selected category.
                  </p>
                ) : (
                  filteredQuestions.map((q, idx) => (
                    <div
                      key={idx}
                      className="p-5 rounded-2xl border border-slate-200/80 bg-slate-50/50 space-y-3 hover:border-slate-300 transition-colors"
                    >
                      <div className="flex items-center justify-between gap-2">
                        <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider bg-blue-100 text-blue-800">
                          {q.category?.replace('_', ' ')}
                        </span>
                        {q.claim_to_verify && (
                          <span className="text-[11px] text-amber-700 bg-amber-50 border border-amber-200 px-2 py-0.5 rounded-md font-medium flex items-center gap-1">
                            <AlertTriangle className="w-3 h-3 text-amber-600" />
                            <span>Claim Audit: "{q.claim_to_verify}"</span>
                          </span>
                        )}
                      </div>

                      <h4 className="font-bold text-slate-900 text-sm leading-snug">
                        {idx + 1}. {q.question}
                      </h4>

                      {q.purpose && (
                        <p className="text-xs text-slate-600 italic">
                          <span className="font-semibold text-slate-700 not-italic">Evaluation Objective: </span>
                          {q.purpose}
                        </p>
                      )}

                      {/* Expected Indicators */}
                      {q.expected_indicators && q.expected_indicators.length > 0 && (
                        <div className="bg-white p-3 rounded-xl border border-slate-200/60 space-y-1.5">
                          <p className="text-[11px] font-bold text-emerald-800 uppercase tracking-wider flex items-center gap-1">
                            <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                            <span>Key Signals to Look For:</span>
                          </p>
                          <ul className="space-y-1 pl-4 list-disc text-xs text-slate-700">
                            {q.expected_indicators.map((ind, i) => (
                              <li key={i}>{ind}</li>
                            ))}
                          </ul>
                        </div>
                      )}

                      {/* Evaluation Rubric */}
                      {q.rubric && Object.keys(q.rubric).length > 0 && (
                        <div className="bg-white p-3 rounded-xl border border-slate-200/60">
                          <p className="text-[11px] font-bold text-slate-500 uppercase tracking-wider mb-2">
                            Standardized Evaluation Rubric:
                          </p>
                          <div className="grid grid-cols-1 sm:grid-cols-3 gap-2 text-xs">
                            {Object.entries(q.rubric).map(([score, desc]) => (
                              <div key={score} className="p-2 rounded-lg bg-slate-50 border border-slate-100">
                                <span className="font-bold text-slate-800 uppercase text-[10px] block">
                                  {score.replace('_', ' ')}
                                </span>
                                <span className="text-slate-600 text-[11px] leading-tight">
                                  {String(desc)}
                                </span>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}

                      {/* Follow-ups */}
                      {q.follow_ups && q.follow_ups.length > 0 && (
                        <div className="pt-2 border-t border-slate-200/60">
                          <p className="text-[11px] font-semibold text-slate-500 mb-1">
                            Suggested Follow-Up Probes:
                          </p>
                          <div className="space-y-1 pl-3 text-xs text-slate-600 border-l-2 border-blue-400">
                            {q.follow_ups.map((f, fi) => (
                              <p key={fi}>↳ {f}</p>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  ))
                )}
              </div>
            </>
          ) : (
            <div className="text-center py-20">
              <HelpCircle className="w-12 h-12 text-slate-300 mx-auto mb-3" />
              <h3 className="text-sm font-bold text-slate-700">No interview kit selected</h3>
              <p className="text-xs text-slate-500 mt-1">
                Choose a candidate from the left panel or generate a new tailored kit.
              </p>
            </div>
          )}
        </div>
      </div>

      {/* ── Generate Kit Modal ─────────────────────────────────── */}
      {isGenerateOpen && (
        <div className="fixed inset-0 z-50 bg-slate-900/40 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-lg w-full p-6 shadow-2xl border border-slate-200">
            <div className="flex items-center justify-between pb-3 border-b border-slate-100">
              <div className="flex items-center gap-2">
                <Sparkles className="w-5 h-5 text-blue-600" />
                <h3 className="font-bold text-slate-900 text-base">
                  Generate Agentic Interview Kit
                </h3>
              </div>
              <button
                onClick={() => setIsGenerateOpen(false)}
                className="text-slate-400 hover:text-slate-600 p-1"
              >
                &times;
              </button>
            </div>

            <form onSubmit={handleGenerate} className="space-y-4 mt-4">
              <p className="text-xs text-slate-500">
                The Interview Intelligence Agent will synthesize the job description requirements
                against the candidate's exact resume evidence to formulate technical, architectural,
                and claim-verification questions with scoring rubrics.
              </p>

              <div>
                <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">
                  Target Job Opening *
                </label>
                <select
                  required
                  value={genJobId}
                  onChange={(e) => setGenJobId(e.target.value)}
                  className="w-full text-xs p-2.5 rounded-xl border border-slate-300 outline-none focus:border-blue-600"
                >
                  <option value="">-- Select Job Description --</option>
                  {jobs.map((j) => (
                    <option key={j.id} value={j.id}>
                      {j.title} ({j.company || 'AVOM Consultants'})
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">
                  Candidate to Evaluate *
                </label>
                <select
                  required
                  value={genCandidateId}
                  onChange={(e) => setGenCandidateId(e.target.value)}
                  className="w-full text-xs p-2.5 rounded-xl border border-slate-300 outline-none focus:border-blue-600"
                >
                  <option value="">-- Select Candidate --</option>
                  {candidates.map((c) => (
                    <option key={c.id} value={c.id}>
                      {c.name} {c.email ? `(${c.email})` : ''}
                    </option>
                  ))}
                </select>
              </div>

              {error && <p className="text-xs text-rose-600 font-medium">{error}</p>}

              <div className="flex items-center justify-end gap-2 pt-4 border-t border-slate-100">
                <button
                  type="button"
                  onClick={() => setIsGenerateOpen(false)}
                  className="px-4 py-2 rounded-xl text-xs font-semibold text-slate-600 hover:bg-slate-100"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={generating || !genJobId || !genCandidateId}
                  className="px-4 py-2 rounded-xl bg-blue-600 text-white text-xs font-semibold hover:bg-blue-700 disabled:opacity-50 flex items-center gap-2"
                >
                  {generating ? (
                    <>
                      <div className="w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                      <span>Synthesizing Kit...</span>
                    </>
                  ) : (
                    <>
                      <Sparkles className="w-3.5 h-3.5" />
                      <span>Generate Kit</span>
                    </>
                  )}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
