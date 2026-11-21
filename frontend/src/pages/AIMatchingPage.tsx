import React, { useState, useEffect, useRef } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import {
  Cpu,
  Briefcase,
  Users,
  Sparkles,
  Trophy,
  ArrowRight,
  CheckCircle2,
  AlertCircle,
  RefreshCw,
  Eye,
  Upload,
  X,
  FileText
} from 'lucide-react';
import { jobsApi, candidatesApi, matchingApi } from '../services/api';
import type { Job, Candidate, MatchingAnalysis } from '../types';
import { CandidateDetailModal } from '../components/CandidateDetailModal';
import { formatApiError } from '../utils/errors';

export const AIMatchingPage: React.FC = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const initialJobId = searchParams.get('job_id') || '';

  const [jobs, setJobs] = useState<Job[]>([]);
  const [selectedJobId, setSelectedJobId] = useState<string>(initialJobId);
  const [candidates, setCandidates] = useState<Candidate[]>([]);
  const [selectedCandidateIds, setSelectedCandidateIds] = useState<string[]>([]);
  const [loading, setLoading] = useState(true);
  const [matching, setMatching] = useState(false);
  const [results, setResults] = useState<MatchingAnalysis[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [detailCandidateId, setDetailCandidateId] = useState<string | null>(null);

  // Card 1: Custom Job Description Input States
  const fileInputRef = useRef<HTMLInputElement | null>(null);
  const [uploadedFile, setUploadedFile] = useState<File | null>(null);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [pastedText, setPastedText] = useState<string>('');
  const [parsing, setParsing] = useState<boolean>(false);
  const [parseError, setParseError] = useState<string | null>(null);
  const [activeSource, setActiveSource] = useState<'dropdown' | 'upload' | 'paste'>('dropdown');
  const lastAppliedTextRef = useRef<string>('');

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      try {
        const [jobsRes, candsRes] = await Promise.all([
          jobsApi.getJobs({ limit: 100 }),
          candidatesApi.getCandidates({ limit: 100 }),
        ]);
        setJobs(jobsRes.items);
        setCandidates(candsRes.items);

        // Auto select first job if none chosen
        const activeJobId = initialJobId || (jobsRes.items.length > 0 ? jobsRes.items[0].id : '');
        setSelectedJobId(activeJobId);

        // Pre-select all candidate IDs
        setSelectedCandidateIds(candsRes.items.map((c) => c.id));

        // If job chosen, fetch existing results
        if (activeJobId) {
          const matchRes = await matchingApi.getRankings(activeJobId);
          setResults(matchRes);
        }
      } catch (e) {
        console.error(e);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, [initialJobId]);

  const handleJobChange = async (jobId: string) => {
    setSelectedJobId(jobId);
    setError(null);
    try {
      const matchRes = await matchingApi.getRankings(jobId);
      setResults(matchRes);
    } catch {
      setResults([]);
    }
  };

  const handleDropdownChange = (jobId: string) => {
    setActiveSource('dropdown');
    setUploadedFile(null);
    setPastedText('');
    lastAppliedTextRef.current = '';
    setUploadError(null);
    setParseError(null);
    if (fileInputRef.current) fileInputRef.current.value = '';
    handleJobChange(jobId);
  };

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setUploadError(null);
    setParseError(null);

    const validExtensions = ['.pdf', '.docx', '.txt'];
    const lowerName = file.name.toLowerCase();
    const isSupported = validExtensions.some((ext) => lowerName.endsWith(ext));
    if (!isSupported) {
      setUploadError('Unsupported file type. Please upload a .pdf, .docx, or .txt file.');
      if (fileInputRef.current) fileInputRef.current.value = '';
      return;
    }

    const MAX_SIZE = 5 * 1024 * 1024; // 5 MB
    if (file.size > MAX_SIZE) {
      setUploadError('File size exceeds the 5 MB limit.');
      if (fileInputRef.current) fileInputRef.current.value = '';
      return;
    }

    setActiveSource('upload');
    setUploadedFile(file);
    setPastedText('');
    lastAppliedTextRef.current = '';

    setParsing(true);
    try {
      const parsed = await jobsApi.uploadJDDocument(file);
      const newJob = await jobsApi.createJob({
        title: parsed.title || 'Custom Job Description',
        company: parsed.company || 'Custom Upload',
        location: parsed.location || 'Remote',
        employment_type: parsed.employment_type || 'Full-time',
        min_experience: parsed.min_experience !== undefined ? parsed.min_experience : 3.0,
        education_req: parsed.education_req || "Bachelor's Degree",
        description: parsed.description,
      });

      setJobs((prev) => [newJob, ...prev.filter((j) => j.id !== newJob.id)]);
      setSelectedJobId(newJob.id);
      setResults([]);
    } catch (err: any) {
      setParseError(formatApiError(err, 'Failed to parse job description file.'));
    } finally {
      setParsing(false);
    }
  };

  const handleRemoveUploadedFile = () => {
    setUploadedFile(null);
    setUploadError(null);
    setParseError(null);
    if (fileInputRef.current) fileInputRef.current.value = '';
    setActiveSource('dropdown');
    if (jobs.length > 0) {
      const fallbackJob = jobs.find((j) => j.company !== 'Custom' && j.company !== 'Custom Upload' && j.company !== 'Custom Paste') || jobs[0];
      setSelectedJobId(fallbackJob.id);
      handleJobChange(fallbackJob.id);
    }
  };

  const applyPastedText = async (text: string) => {
    const trimmed = text.trim();
    if (!trimmed || trimmed === lastAppliedTextRef.current.trim()) return;

    if (trimmed.length < 20) {
      setParseError('Please enter at least 20 characters for the job description.');
      return;
    }

    lastAppliedTextRef.current = trimmed;
    setActiveSource('paste');
    setUploadedFile(null);
    setUploadError(null);
    setParseError(null);
    if (fileInputRef.current) fileInputRef.current.value = '';

    setParsing(true);
    try {
      const newJob = await jobsApi.createJob({
        title: 'Custom Job Description',
        company: 'Custom Paste',
        location: 'Remote',
        employment_type: 'Full-time',
        min_experience: 3.0,
        education_req: "Bachelor's Degree",
        description: trimmed,
      });

      setJobs((prev) => [newJob, ...prev.filter((j) => j.id !== newJob.id)]);
      setSelectedJobId(newJob.id);
      setResults([]);
    } catch (err: any) {
      setParseError(formatApiError(err, 'Failed to extract requirements from pasted text.'));
    } finally {
      setParsing(false);
    }
  };

  const handlePasteChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    const text = e.target.value;
    setPastedText(text);
    setActiveSource('paste');
    setUploadedFile(null);
    setUploadError(null);
    setParseError(null);
    if (fileInputRef.current) fileInputRef.current.value = '';
  };

  useEffect(() => {
    if (activeSource !== 'paste' || !pastedText.trim()) return;
    const timer = setTimeout(() => {
      applyPastedText(pastedText);
    }, 600);
    return () => clearTimeout(timer);
  }, [pastedText, activeSource]);

  const toggleCandidate = (id: string) => {
    if (selectedCandidateIds.includes(id)) {
      setSelectedCandidateIds(selectedCandidateIds.filter((cId) => cId !== id));
    } else {
      setSelectedCandidateIds([...selectedCandidateIds, id]);
    }
  };

  const toggleAllCandidates = () => {
    if (selectedCandidateIds.length === candidates.length) {
      setSelectedCandidateIds([]);
    } else {
      setSelectedCandidateIds(candidates.map((c) => c.id));
    }
  };

  const handleRunMatching = async () => {
    if (!selectedJobId || selectedCandidateIds.length === 0) return;
    setMatching(true);
    setError(null);

    try {
      const analyses = await matchingApi.analyzeMatch(selectedJobId, selectedCandidateIds);
      setResults(analyses);
    } catch (err: any) {
      setError(formatApiError(err, 'Semantic matching failed. Check backend server.'));
    } finally {
      setMatching(false);
    }
  };

  const currentJob = jobs.find((j) => j.id === selectedJobId);

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* ── Page Header ────────────────────────────────────────── */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-black text-slate-900 tracking-tight flex items-center gap-2">
            AI Semantic Matching Engine
            <span className="text-xs font-bold uppercase tracking-wider px-2 py-0.5 rounded-full bg-blue-100 text-blue-700">
              0 - 100 Scoring
            </span>
          </h1>
          <p className="text-xs text-slate-500 mt-1">
            Compare candidate resumes against job descriptions with NLP skill matching and Sentence Transformers embeddings.
          </p>
        </div>

        {results.length > 0 && (
          <button
            onClick={() => navigate(`/ranking?job_id=${selectedJobId}`)}
            className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-blue-600 text-white text-xs font-semibold hover:bg-blue-700 transition-colors shadow-md shadow-blue-500/20 shrink-0"
          >
            <Trophy className="w-4 h-4" />
            <span>Open Ranking Leaderboard</span>
            <ArrowRight className="w-3.5 h-3.5" />
          </button>
        )}
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-rose-50 border border-rose-200 text-xs text-rose-700 flex items-center gap-2">
          <AlertCircle className="w-4 h-4 text-rose-600 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* ── Selection Workspace ─────────────────────────────────── */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Step 1: Select Job Description */}
        <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-5 space-y-4 max-h-[720px] overflow-y-auto">
          <div className="flex items-center gap-2 pb-3 border-b border-slate-100">
            <div className="w-7 h-7 rounded-lg bg-blue-50 text-blue-600 font-bold flex items-center justify-center text-xs">
              1
            </div>
            <h3 className="text-xs font-bold text-slate-900 uppercase tracking-wide">
              Select Target Job
            </h3>
          </div>

          <div>
            <label className="block text-[11px] font-semibold text-slate-500 mb-1.5">
              Configured Job Description
            </label>
            <select
              value={activeSource === 'dropdown' ? selectedJobId : ''}
              onChange={(e) => handleDropdownChange(e.target.value)}
              className="w-full p-2.5 rounded-xl border border-slate-300 text-xs font-semibold text-slate-900 bg-white outline-none focus:border-blue-600"
            >
              {activeSource !== 'dropdown' && (
                <option value="" disabled>
                  Select from configured jobs...
                </option>
              )}
              {jobs.map((j) => (
                <option key={j.id} value={j.id}>
                  {j.title} ({j.company})
                </option>
              ))}
            </select>
          </div>

          {/* Small divider label "OR" */}
          <div className="relative flex items-center justify-center my-1">
            <div className="w-full border-t border-slate-200"></div>
            <span className="absolute bg-white px-2 text-[10px] font-bold text-slate-400 uppercase tracking-wider">
              OR
            </span>
          </div>

          {/* New Input Options: Upload (A) & Paste (B) */}
          <div className="space-y-3">
            {/* (A) File Upload Button */}
            <div>
              <input
                type="file"
                ref={fileInputRef}
                onChange={handleFileUpload}
                accept=".pdf,.docx,.txt"
                className="hidden"
              />
              <button
                type="button"
                onClick={() => fileInputRef.current?.click()}
                disabled={parsing}
                className="flex items-center justify-center gap-2 w-full py-2 px-3 rounded-xl border border-slate-300 bg-white text-xs font-semibold text-slate-700 hover:bg-slate-50 hover:border-slate-400 transition-colors cursor-pointer disabled:opacity-50"
              >
                <Upload className="w-3.5 h-3.5 text-slate-600" />
                <span>Upload Job Description</span>
              </button>

              {/* Show selected file with "x" remove button */}
              {uploadedFile && (
                <div className="flex items-center justify-between p-2 rounded-xl bg-blue-50/70 border border-blue-200 text-xs text-blue-900 mt-1.5">
                  <div className="flex items-center gap-1.5 truncate">
                    <FileText className="w-3.5 h-3.5 text-blue-600 shrink-0" />
                    <span className="truncate font-medium">{uploadedFile.name}</span>
                    <span className="text-[10px] text-blue-500 shrink-0">
                      ({(uploadedFile.size / 1024).toFixed(0)} KB)
                    </span>
                  </div>
                  <button
                    type="button"
                    onClick={handleRemoveUploadedFile}
                    className="p-1 rounded hover:bg-blue-100 text-blue-600 hover:text-blue-800 transition-colors ml-1 shrink-0 cursor-pointer"
                    title="Remove file"
                  >
                    <X className="w-3.5 h-3.5" />
                  </button>
                </div>
              )}

              {uploadError && (
                <p className="text-[11px] text-rose-600 font-medium flex items-center gap-1 mt-1">
                  <AlertCircle className="w-3 h-3 shrink-0" />
                  <span>{uploadError}</span>
                </p>
              )}
            </div>

            {/* (B) Paste Text Box */}
            <div className="space-y-1">
              <textarea
                rows={5}
                value={pastedText}
                onChange={handlePasteChange}
                placeholder="Or paste the job description here..."
                className="w-full p-2.5 rounded-xl border border-slate-300 text-xs text-slate-900 bg-white outline-none focus:border-blue-600 focus:ring-1 focus:ring-blue-600 resize-y leading-relaxed"
              />
              <div className="flex items-center justify-between">
                <button
                  type="button"
                  onClick={() => applyPastedText(pastedText)}
                  disabled={!pastedText.trim() || parsing || activeSource === 'paste'}
                  className="px-2.5 py-1 rounded-lg bg-blue-50 text-blue-600 text-[11px] font-semibold hover:bg-blue-100 disabled:opacity-40 transition-colors cursor-pointer"
                >
                  Use this description
                </button>
                <span className="text-[10px] text-slate-400 font-medium">
                  {pastedText.length} characters
                </span>
              </div>
            </div>

            {/* Parsing / Loading State */}
            {parsing && (
              <div className="flex items-center gap-2 p-2.5 rounded-xl bg-blue-50/70 border border-blue-200 text-xs text-blue-700 animate-pulse">
                <RefreshCw className="w-3.5 h-3.5 animate-spin text-blue-600 shrink-0" />
                <span>Extracting job requirements & skills...</span>
              </div>
            )}

            {parseError && (
              <p className="text-[11px] text-rose-600 font-medium flex items-center gap-1">
                <AlertCircle className="w-3 h-3 shrink-0" />
                <span>{parseError}</span>
              </p>
            )}
          </div>

          {currentJob && (
            <div className="space-y-3 pt-2">
              <div className="p-3 bg-slate-50 rounded-xl border border-slate-100 text-xs space-y-1.5">
                <p className="font-bold text-slate-900">{currentJob.title}</p>
                <p className="text-[11px] text-slate-500">
                  {currentJob.company} • {currentJob.min_experience} yrs min • {currentJob.location}
                </p>
                <p className="text-[11px] text-slate-600 line-clamp-3 leading-relaxed mt-1">
                  {currentJob.description}
                </p>
              </div>

              <div>
                <span className="text-[11px] font-bold text-slate-400 uppercase tracking-wider block mb-1.5">
                  Extracted Job Requirements ({currentJob.requirements?.length || 0})
                </span>
                <div className="flex flex-wrap gap-1 max-h-36 overflow-y-auto">
                  {currentJob.requirements?.map((r) => (
                    <span
                      key={r.id}
                      className={`px-2 py-0.5 rounded text-[10px] font-semibold ${
                        r.category === 'mandatory'
                          ? 'bg-blue-100 text-blue-700'
                          : 'bg-slate-100 text-slate-600'
                      }`}
                    >
                      {r.skill_name}
                    </span>
                  ))}
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Step 2: Candidate Selection Pool */}
        <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-5 space-y-4">
          <div className="flex items-center justify-between pb-3 border-b border-slate-100">
            <div className="flex items-center gap-2">
              <div className="w-7 h-7 rounded-lg bg-blue-50 text-blue-600 font-bold flex items-center justify-center text-xs">
                2
              </div>
              <h3 className="text-xs font-bold text-slate-900 uppercase tracking-wide">
                Candidate Pool ({candidates.length})
              </h3>
            </div>
            <button
              onClick={toggleAllCandidates}
              className="text-[11px] font-semibold text-blue-600 hover:underline"
            >
              {selectedCandidateIds.length === candidates.length ? 'Deselect All' : 'Select All'}
            </button>
          </div>

          <div className="max-h-80 overflow-y-auto space-y-1.5 pr-1">
            {candidates.map((c) => {
              const isSelected = selectedCandidateIds.includes(c.id);
              return (
                <div
                  key={c.id}
                  onClick={() => toggleCandidate(c.id)}
                  className={`p-2.5 rounded-xl border text-xs flex items-center justify-between cursor-pointer transition-colors ${
                    isSelected
                      ? 'border-blue-600 bg-blue-50/50'
                      : 'border-slate-200 bg-white hover:bg-slate-50'
                  }`}
                >
                  <div className="flex items-center gap-2.5 min-w-0">
                    <input
                      type="checkbox"
                      checked={isSelected}
                      onChange={() => {}}
                      className="rounded border-slate-300 text-blue-600 pointer-events-none"
                    />
                    <div className="truncate">
                      <p className="font-semibold text-slate-900 truncate">{c.name}</p>
                      <p className="text-[10px] text-slate-400">
                        {c.total_experience_years} yrs exp • {c.skills?.length || 0} skills
                      </p>
                    </div>
                  </div>
                  <span className="text-[10px] px-1.5 py-0.5 rounded bg-slate-100 text-slate-600 capitalize">
                    {c.status}
                  </span>
                </div>
              );
            })}
          </div>
        </div>

        {/* Step 3: Run AI Matching Action */}
        <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-5 flex flex-col justify-between space-y-4">
          <div>
            <div className="flex items-center gap-2 pb-3 border-b border-slate-100">
              <div className="w-7 h-7 rounded-lg bg-blue-50 text-blue-600 font-bold flex items-center justify-center text-xs">
                3
              </div>
              <h3 className="text-xs font-bold text-slate-900 uppercase tracking-wide">
                Execute AI Matching
              </h3>
            </div>

            <div className="space-y-3 mt-4 text-xs text-slate-600">
              <p className="leading-relaxed">
                Matches candidate profiles against the job description using our 4-component weighted algorithm:
              </p>
              <div className="p-3 bg-slate-50 rounded-xl space-y-1 text-[11px] font-medium border border-slate-100">
                <div className="flex justify-between">
                  <span>1. Technical Skill Match</span>
                  <span className="font-bold text-blue-600">40 Points</span>
                </div>
                <div className="flex justify-between">
                  <span>2. Semantic Similarity</span>
                  <span className="font-bold text-blue-600">30 Points</span>
                </div>
                <div className="flex justify-between">
                  <span>3. Relevant Experience</span>
                  <span className="font-bold text-blue-600">20 Points</span>
                </div>
                <div className="flex justify-between">
                  <span>4. Education & Qualifications</span>
                  <span className="font-bold text-blue-600">10 Points</span>
                </div>
              </div>
            </div>
          </div>

          <div className="space-y-2 pt-4 border-t border-slate-100">
            <button
              onClick={handleRunMatching}
              disabled={matching || !selectedJobId || selectedCandidateIds.length === 0}
              className="w-full py-3 rounded-xl bg-gradient-to-r from-blue-600 to-indigo-600 text-white text-xs font-bold hover:from-blue-700 hover:to-indigo-700 transition-all flex items-center justify-center gap-2 shadow-lg shadow-blue-500/25 disabled:opacity-50"
            >
              {matching ? (
                <>
                  <RefreshCw className="w-4 h-4 animate-spin" />
                  <span>Computing Semantic Vectors & Scoring...</span>
                </>
              ) : (
                <>
                  <Sparkles className="w-4 h-4" />
                  <span>Run Matching ({selectedCandidateIds.length} Candidates)</span>
                </>
              )}
            </button>
            <p className="text-[10px] text-center text-slate-400">
              Deterministic, open-source AI. Zero hallucinated scores.
            </p>
          </div>
        </div>
      </div>

      {/* ── Results Leaderboard Preview ─────────────────────────── */}
      {results.length > 0 && (
        <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden space-y-4 p-6">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 pb-4 border-b border-slate-100">
            <div>
              <h3 className="text-sm font-bold text-slate-900">
                Ranked Matching Results ({results.length} Candidates)
              </h3>
              <p className="text-xs text-slate-500">
                Ranked automatically from highest to lowest matching score.
              </p>
            </div>
            <button
              onClick={() => navigate(`/ranking?job_id=${selectedJobId}`)}
              className="text-xs font-semibold text-blue-600 hover:text-blue-700 flex items-center gap-1"
            >
              <span>View Full Interactive Ranking Board</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs">
              <thead className="bg-slate-50 border-b border-slate-200 text-slate-500 font-bold uppercase tracking-wider text-[11px]">
                <tr>
                  <th className="p-3 pl-4">Rank</th>
                  <th className="p-3">Candidate</th>
                  <th className="p-3">Overall Score</th>
                  <th className="p-3">Tech (40)</th>
                  <th className="p-3">Semantic (30)</th>
                  <th className="p-3">Exp (20)</th>
                  <th className="p-3">Edu (10)</th>
                  <th className="p-3">Matched Skills</th>
                  <th className="p-3 pr-4 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {results.map((res, index) => (
                  <tr key={res.id} className="hover:bg-slate-50 transition-colors">
                    <td className="p-3 pl-4">
                      <span
                        className={`w-6 h-6 rounded-full inline-flex items-center justify-center font-bold text-xs ${
                          index === 0
                            ? 'bg-amber-100 text-amber-700'
                            : index === 1
                            ? 'bg-slate-200 text-slate-700'
                            : index === 2
                            ? 'bg-amber-50 text-amber-800'
                            : 'text-slate-400'
                        }`}
                      >
                        {index + 1}
                      </span>
                    </td>
                    <td className="p-3">
                      <p className="font-bold text-slate-900">{res.candidate?.name}</p>
                      <p className="text-[10px] text-slate-400">{res.candidate?.email}</p>
                    </td>
                    <td className="p-3">
                      <span className="font-black text-sm text-emerald-600">
                        {res.overall_score}%
                      </span>
                    </td>
                    <td className="p-3 font-semibold text-slate-700">{res.technical_score}</td>
                    <td className="p-3 font-semibold text-slate-700">{res.semantic_score}</td>
                    <td className="p-3 font-semibold text-slate-700">{res.experience_score}</td>
                    <td className="p-3 font-semibold text-slate-700">{res.education_score}</td>
                    <td className="p-3">
                      <span className="px-2 py-0.5 rounded bg-emerald-50 text-emerald-700 font-semibold text-[10px]">
                        {res.matched_skills?.length || 0} Matched
                      </span>
                    </td>
                    <td className="p-3 pr-4 text-right">
                      <button
                        onClick={() => setDetailCandidateId(res.candidate_id)}
                        className="px-2.5 py-1 rounded-lg bg-blue-50 text-blue-700 font-medium hover:bg-blue-100 text-xs transition-colors"
                      >
                        Inspect Breakdown
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Candidate Analysis Modal */}
      {detailCandidateId && (
        <CandidateDetailModal
          candidateId={detailCandidateId}
          jobId={selectedJobId}
          onClose={() => setDetailCandidateId(null)}
        />
      )}
    </div>
  );
};
