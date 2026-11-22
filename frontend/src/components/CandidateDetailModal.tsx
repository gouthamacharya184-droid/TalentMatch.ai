import React, { useState, useEffect } from 'react';
import {
  X,
  Mail,
  Phone,
  MapPin,
  Briefcase,
  GraduationCap,
  Award,
  CheckCircle2,
  AlertTriangle,
  FileText,
  Download,
  Save,
  Sparkles,
  Eye,
} from 'lucide-react';
import type { Candidate, MatchingAnalysis, EvidenceReference, InterviewKit } from '../types';
import { candidatesApi, shortlistApi, resumesApi, matchingApi, interviewKitsApi } from '../services/api';
import { ResumeViewerModal } from './ResumeViewerModal';

interface CandidateDetailModalProps {
  candidateId: string;
  jobId?: string;
  initialAnalysis?: MatchingAnalysis;
  onClose: () => void;
  onStatusChange?: (newStatus: string) => void;
}

export const CandidateDetailModal: React.FC<CandidateDetailModalProps> = ({
  candidateId,
  jobId,
  initialAnalysis,
  onClose,
  onStatusChange,
}) => {
  const [candidate, setCandidate] = useState<Candidate | null>(null);
  const [analysis, setAnalysis] = useState<MatchingAnalysis | null>(initialAnalysis || null);
  const [loading, setLoading] = useState(true);
  const [noteContent, setNoteContent] = useState('');
  const [savedNotes, setSavedNotes] = useState<any[]>([]);
  const [savingNote, setSavingNote] = useState(false);
  const [activeTab, setActiveTab] = useState<
    'overview' | 'skills' | 'evidence' | 'interview' | 'recommendations' | 'notes' | 'resume'
  >('overview');
  const [showResumeViewer, setShowResumeViewer] = useState(false);

  // Agentic Evidence & Interview Kit State
  const [evidenceList, setEvidenceList] = useState<EvidenceReference[]>([]);
  const [interviewKit, setInterviewKit] = useState<InterviewKit | null>(null);
  const [generatingKit, setGeneratingKit] = useState(false);
  const [evidenceFilter, setEvidenceFilter] = useState<string>('all');
  const [recommendedJobs, setRecommendedJobs] = useState<any[]>([]);

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      try {
        const c = await candidatesApi.getCandidate(candidateId);
        setCandidate(c);

        if (!analysis && jobId) {
          try {
            const rankings = await matchingApi.getRankings(jobId);
            const found = rankings.find((r) => r.candidate_id === candidateId);
            if (found) setAnalysis(found);
          } catch {
            // ignore if no rankings yet
          }
        }

        const notes = await shortlistApi.getNotes(candidateId, jobId);
        setSavedNotes(notes);

        // Fetch Agentic Evidence references
        try {
          const evData = await candidatesApi.getEvidence(candidateId, jobId);
          setEvidenceList(evData);
        } catch {
          // ignore if no evidence yet
        }

        // Fetch Agentic Interview Kit if generated
        try {
          const kitData = await interviewKitsApi.getKitForCandidate(candidateId, jobId);
          setInterviewKit(kitData);
        } catch {
          // ignore if no kit yet
        }

        // Fetch Other Recommended Jobs for Candidate
        try {
          const recs = await matchingApi.getRecommendedJobs(candidateId, jobId);
          setRecommendedJobs(recs || []);
        } catch {
          // ignore if not available
        }
      } catch (e) {
        console.error(e);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, [candidateId, jobId]);

  const handleGenerateKit = async () => {
    if (!jobId || !candidate) return;
    setGeneratingKit(true);
    try {
      const kit = await interviewKitsApi.generateKit(jobId, candidate.id);
      setInterviewKit(kit);
    } catch (e) {
      console.error(e);
    } finally {
      setGeneratingKit(false);
    }
  };

  const handleStatusUpdate = async (status: string) => {
    if (!candidate) return;
    try {
      const updated = await candidatesApi.updateCandidate(candidate.id, { status: status as any });
      setCandidate(updated);
      if (onStatusChange) onStatusChange(status);
    } catch (e) {
      console.error(e);
    }
  };

  const handleSaveNote = async () => {
    if (!noteContent.trim() || !candidate) return;
    setSavingNote(true);
    try {
      const newNote = await shortlistApi.addNote(candidate.id, jobId || '', noteContent.trim());
      setSavedNotes([newNote, ...savedNotes]);
      setNoteContent('');
    } catch (e) {
      console.error(e);
    } finally {
      setSavingNote(false);
    }
  };

  const handleDownloadResume = async () => {
    if (!candidate?.resume?.id) return;
    try {
      const blob = await resumesApi.downloadResume(candidate.resume.id);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = candidate.resume.original_filename || `${candidate.name}_Resume.pdf`;
      a.click();
    } catch (e) {
      console.error(e);
    }
  };

  if (loading || !candidate) {
    return (
      <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/50 backdrop-blur-sm p-4">
        <div className="bg-white rounded-2xl p-8 max-w-sm w-full text-center shadow-xl">
          <div className="w-10 h-10 border-4 border-blue-600 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-sm font-medium text-slate-600">Loading Candidate Profile...</p>
        </div>
      </div>
    );
  }

  const overallScore = analysis?.overall_score || 0;
  const questions = (analysis?.explanation as any)?.interview_questions || [];
  const insights = (analysis?.explanation as any)?.recruiter_insights || null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/50 backdrop-blur-sm p-4 sm:p-6 overflow-y-auto">
      <div className="bg-white rounded-2xl max-w-4xl w-full max-h-[90vh] flex flex-col shadow-2xl border border-slate-200 overflow-hidden animate-in fade-in zoom-in-95 duration-200">
        {/* Header */}
        <div className="p-6 border-b border-slate-100 flex items-start justify-between bg-gradient-to-r from-blue-50/50 via-white to-slate-50">
          <div className="flex items-start gap-4">
            <div className="w-14 h-14 rounded-2xl bg-gradient-to-tr from-blue-600 to-indigo-600 text-white font-bold flex items-center justify-center text-xl shadow-md shadow-blue-500/20 shrink-0">
              {candidate.name.charAt(0).toUpperCase()}
            </div>
            <div>
              <div className="flex items-center gap-3">
                <h2 className="text-xl font-bold text-slate-900">{candidate.name}</h2>
                <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold uppercase tracking-wide bg-blue-100 text-blue-700">
                  {candidate.status.replace('_', ' ')}
                </span>
              </div>
              <div className="flex flex-wrap items-center gap-y-1 gap-x-4 text-xs text-slate-500 mt-1.5">
                {candidate.email && (
                  <span className="flex items-center gap-1">
                    <Mail className="w-3.5 h-3.5 text-slate-400" />
                    {candidate.email}
                  </span>
                )}
                {candidate.phone && (
                  <span className="flex items-center gap-1">
                    <Phone className="w-3.5 h-3.5 text-slate-400" />
                    {candidate.phone}
                  </span>
                )}
                {candidate.location && (
                  <span className="flex items-center gap-1">
                    <MapPin className="w-3.5 h-3.5 text-slate-400" />
                    {candidate.location}
                  </span>
                )}
                <span className="flex items-center gap-1">
                  <Briefcase className="w-3.5 h-3.5 text-slate-400" />
                  {candidate.total_experience_years} Years Exp
                </span>
              </div>
            </div>
          </div>

          <div className="flex items-center gap-2">
            {candidate.resume && (
              <>
                <button
                  id="view-resume-btn"
                  onClick={() => setShowResumeViewer(true)}
                  className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-blue-200 bg-blue-50 text-blue-700 text-xs font-semibold hover:bg-blue-100 transition-colors shadow-sm"
                  title="View uploaded resume"
                >
                  <Eye className="w-3.5 h-3.5 text-blue-600" />
                  <span>View Resume</span>
                </button>
                <button
                  onClick={handleDownloadResume}
                  className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-slate-200 text-slate-700 text-xs font-medium hover:bg-slate-50 transition-colors"
                  title="Download original file"
                >
                  <Download className="w-3.5 h-3.5" />
                  <span>Resume</span>
                </button>
              </>
            )}
            <button
              onClick={onClose}
              className="p-1.5 text-slate-400 hover:text-slate-700 rounded-lg hover:bg-slate-100 transition-colors"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
        </div>

        {/* Status Bar & Overall Score Banner */}
        {analysis && (
          <div className="px-6 py-3 bg-slate-900 text-white flex items-center justify-between shrink-0">
            <div className="flex items-center gap-6">
              <div>
                <span className="text-[11px] text-slate-400 uppercase tracking-wider block">
                  Overall Match
                </span>
                <span className="text-2xl font-black text-emerald-400">{overallScore}%</span>
              </div>
              <div className="h-8 w-px bg-slate-800"></div>
              <div className="grid grid-cols-4 gap-4 text-xs">
                <div>
                  <span className="text-slate-400 block text-[10px]">Technical (40)</span>
                  <span className="font-bold text-white">{analysis.technical_score} pts</span>
                </div>
                <div>
                  <span className="text-slate-400 block text-[10px]">Semantic (30)</span>
                  <span className="font-bold text-white">{analysis.semantic_score} pts</span>
                </div>
                <div>
                  <span className="text-slate-400 block text-[10px]">Experience (20)</span>
                  <span className="font-bold text-white">{analysis.experience_score} pts</span>
                </div>
                <div>
                  <span className="text-slate-400 block text-[10px]">Education (10)</span>
                  <span className="font-bold text-white">{analysis.education_score} pts</span>
                </div>
              </div>
            </div>

            <div className="flex items-center gap-2">
              <span className="text-xs text-slate-400">Recruiter Status:</span>
              <select
                value={candidate.status}
                onChange={(e) => handleStatusUpdate(e.target.value)}
                className="bg-slate-800 border border-slate-700 text-white text-xs rounded-lg px-2.5 py-1.5 outline-none focus:border-blue-500 font-medium"
              >
                <option value="new">New</option>
                <option value="analyzed">Analyzed</option>
                <option value="shortlisted">Shortlisted</option>
                <option value="under_review">Under Review</option>
                <option value="interview">Interview</option>
                <option value="hired">Hired</option>
                <option value="rejected">Rejected</option>
              </select>
            </div>
          </div>
        )}

        {/* Tab Navigation */}
        <div className="flex border-b border-slate-200 px-6 gap-6 bg-white text-xs font-semibold">
          <button
            onClick={() => setActiveTab('overview')}
            className={`py-3 border-b-2 transition-colors ${
              activeTab === 'overview'
                ? 'border-blue-600 text-blue-600'
                : 'border-transparent text-slate-500 hover:text-slate-800'
            }`}
          >
            Candidate Profile
          </button>
          <button
            onClick={() => setActiveTab('skills')}
            className={`py-3 border-b-2 transition-colors ${
              activeTab === 'skills'
                ? 'border-blue-600 text-blue-600'
                : 'border-transparent text-slate-500 hover:text-slate-800'
            }`}
          >
            Skills & Match Analysis ({analysis?.matched_skills?.length || 0})
          </button>
          <button
            onClick={() => setActiveTab('evidence')}
            className={`py-3 border-b-2 transition-colors flex items-center gap-1.5 ${
              activeTab === 'evidence'
                ? 'border-blue-600 text-blue-600'
                : 'border-transparent text-slate-500 hover:text-slate-800'
            }`}
          >
            <span>Evidence Inspector</span>
            <span className="px-1.5 py-0.5 rounded-full text-[10px] bg-purple-100 text-purple-700 font-bold">
              {evidenceList.length}
            </span>
          </button>
          <button
            onClick={() => setActiveTab('interview')}
            className={`py-3 border-b-2 transition-colors ${
              activeTab === 'interview'
                ? 'border-blue-600 text-blue-600'
                : 'border-transparent text-slate-500 hover:text-slate-800'
            }`}
          >
            AI Interview Questions ({questions.length})
          </button>
          <button
            onClick={() => setActiveTab('recommendations')}
            className={`py-3 border-b-2 transition-colors flex items-center gap-1.5 ${
              activeTab === 'recommendations'
                ? 'border-blue-600 text-blue-600'
                : 'border-transparent text-slate-500 hover:text-slate-800'
            }`}
          >
            <Sparkles className="w-3.5 h-3.5 text-blue-600" />
            <span>Other Job Matches ({recommendedJobs.length})</span>
          </button>
          <button
            onClick={() => setActiveTab('notes')}
            className={`py-3 border-b-2 transition-colors ${
              activeTab === 'notes'
                ? 'border-blue-600 text-blue-600'
                : 'border-transparent text-slate-500 hover:text-slate-800'
            }`}
          >
            Recruiter Notes ({savedNotes.length})
          </button>
          {candidate.resume && (
            <button
              onClick={() => setActiveTab('resume')}
              className={`py-3 border-b-2 transition-colors flex items-center gap-1.5 ${
                activeTab === 'resume'
                  ? 'border-blue-600 text-blue-600'
                  : 'border-transparent text-slate-500 hover:text-slate-800'
              }`}
            >
              <FileText className="w-3.5 h-3.5" />
              <span>Resume Document</span>
            </button>
          )}
        </div>

        {/* Tab Body */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {/* TAB 1: OVERVIEW */}
          {activeTab === 'overview' && (
            <div className="space-y-6">
              {/* Recruiter Insights Callout */}
              {insights && (
                <div className="p-4 rounded-xl bg-blue-50/70 border border-blue-200">
                  <div className="flex items-center gap-2 mb-2">
                    <Sparkles className="w-4 h-4 text-blue-600" />
                    <span className="text-xs font-bold text-blue-900 uppercase tracking-wide">
                      AI Recruiter Assessment • {insights.tier}
                    </span>
                  </div>
                  <p className="text-xs text-blue-950 leading-relaxed">{insights.summary}</p>
                  {insights.verification_checklist?.length > 0 && (
                    <div className="mt-3 pt-3 border-t border-blue-200/60">
                      <p className="text-[11px] font-bold text-blue-900 uppercase tracking-wider mb-1">
                        Recommended Screening Checklist:
                      </p>
                      <ul className="space-y-1">
                        {insights.verification_checklist.map((item: string, i: number) => (
                          <li key={i} className="flex items-start gap-1.5 text-xs text-blue-900">
                            <span className="text-blue-500">•</span>
                            <span>{item}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              )}

              {/* Bio / Summary */}
              {Boolean(candidate.extracted_profile && (candidate.extracted_profile as any).bio) && (
                <div>
                  <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-1.5">
                    Professional Summary
                  </h4>
                  <p className="text-xs text-slate-700 leading-relaxed bg-slate-50 p-3.5 rounded-xl border border-slate-100">
                    {String((candidate.extracted_profile as any).bio || '')}
                  </p>
                </div>
              )}

              {/* Education */}
              <div>
                <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-2 flex items-center gap-1.5">
                  <GraduationCap className="w-4 h-4 text-slate-500" />
                  Education & Qualifications
                </h4>
                {Array.isArray(candidate.education) && (candidate.education as any[]).length > 0 ? (
                  <div className="space-y-2">
                    {(candidate.education as any[]).map((edu: any, idx: number) => (
                      <div
                        key={idx}
                        className="p-3 bg-slate-50 rounded-xl border border-slate-100 flex items-center justify-between text-xs"
                      >
                        <div>
                          <p className="font-semibold text-slate-900">{edu.degree || 'Degree'}</p>
                          <p className="text-slate-500">{edu.institution || 'University'}</p>
                        </div>
                        {edu.year && (
                          <span className="px-2 py-0.5 rounded bg-white border border-slate-200 text-slate-600 font-medium text-[11px]">
                            {edu.year}
                          </span>
                        )}
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-xs text-slate-400 italic">No formal education record parsed.</p>
                )}
              </div>

              {/* Key Projects */}
              {Array.isArray((candidate.extracted_profile as any)?.projects) && (
                <div>
                  <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-2 flex items-center gap-1.5">
                    <Award className="w-4 h-4 text-slate-500" />
                    Key Projects & Achievements
                  </h4>
                  <div className="space-y-2">
                    {((candidate.extracted_profile as any).projects as any[]).map((proj: any, idx: number) => (
                      <div
                        key={idx}
                        className="p-3 bg-slate-50 rounded-xl border border-slate-100 text-xs"
                      >
                        <p className="font-semibold text-slate-900">{proj.name}</p>
                        <p className="text-slate-600 mt-0.5 leading-relaxed">{proj.description}</p>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          {/* TAB 2: SKILLS & MATCH ANALYSIS */}
          {activeTab === 'skills' && analysis && (
            <div className="space-y-6">
              {/* Strengths & Skill Gaps */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="p-4 rounded-xl bg-emerald-50/70 border border-emerald-200">
                  <div className="flex items-center gap-1.5 mb-2">
                    <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                    <span className="text-xs font-bold text-emerald-900 uppercase tracking-wider">
                      Candidate Strengths
                    </span>
                  </div>
                  <ul className="space-y-1.5">
                    {analysis.strengths.map((str, i) => (
                      <li key={i} className="text-xs text-emerald-900 flex items-start gap-1.5">
                        <span className="text-emerald-500 font-bold">•</span>
                        <span>{str}</span>
                      </li>
                    ))}
                  </ul>
                </div>

                <div className="p-4 rounded-xl bg-amber-50/70 border border-amber-200">
                  <div className="flex items-center gap-1.5 mb-2">
                    <AlertTriangle className="w-4 h-4 text-amber-600" />
                    <span className="text-xs font-bold text-amber-900 uppercase tracking-wider">
                      Identified Skill Gaps
                    </span>
                  </div>
                  <ul className="space-y-1.5">
                    {analysis.skill_gaps.map((gap, i) => (
                      <li key={i} className="text-xs text-amber-900 flex items-start gap-1.5">
                        <span className="text-amber-500 font-bold">•</span>
                        <span>{gap}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              </div>

              {/* Matched Skills */}
              <div>
                <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-2">
                  Verified Skills Alignment ({analysis.matched_skills.length})
                </h4>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
                  {analysis.matched_skills.map((m: any, idx: number) => (
                    <div
                      key={idx}
                      className="p-3 bg-slate-50 border border-slate-200 rounded-xl flex items-start justify-between text-xs"
                    >
                      <div>
                        <div className="flex items-center gap-2">
                          <span className="font-bold text-slate-900">{m.skill}</span>
                          <span
                            className={`px-1.5 py-0.5 rounded text-[10px] font-semibold uppercase ${
                              m.type === 'exact'
                                ? 'bg-emerald-100 text-emerald-700'
                                : 'bg-blue-100 text-blue-700'
                            }`}
                          >
                            {m.type}
                          </span>
                        </div>
                        <p className="text-[11px] text-slate-500 mt-1">{m.evidence}</p>
                      </div>
                      <span className="text-[11px] font-bold text-emerald-600">
                        {Math.round((m.confidence || 0.95) * 100)}%
                      </span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Missing Skills */}
              {analysis.missing_skills.length > 0 && (
                <div>
                  <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-2">
                    Missing Requirements ({analysis.missing_skills.length})
                  </h4>
                  <div className="flex flex-wrap gap-2">
                    {analysis.missing_skills.map((s, idx) => (
                      <span
                        key={idx}
                        className="px-2.5 py-1 rounded-lg text-xs font-medium bg-rose-50 border border-rose-200 text-rose-700"
                      >
                        {s}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          {/* TAB: EVIDENCE INSPECTOR */}
          {activeTab === 'evidence' && (
            <div className="space-y-4">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 p-4 bg-purple-50/60 rounded-xl border border-purple-100">
                <div>
                  <h4 className="font-bold text-slate-900 text-xs uppercase tracking-wider flex items-center gap-1.5">
                    <Sparkles className="w-3.5 h-3.5 text-purple-600" />
                    <span>Evidence-Grounded Resume Verification</span>
                  </h4>
                  <p className="text-[11px] text-slate-500 mt-0.5">
                    Every evaluated competency is pinned to concrete source document text and page locations.
                  </p>
                </div>
                <div className="flex items-center gap-1.5">
                  <span className="text-[10px] font-bold text-slate-400 uppercase">Filter:</span>
                  <select
                    value={evidenceFilter}
                    onChange={(e) => setEvidenceFilter(e.target.value)}
                    className="text-xs bg-white border border-purple-200 rounded-lg px-2 py-1 text-slate-700 outline-none"
                  >
                    <option value="all">All Evidence ({evidenceList.length})</option>
                    <option value="explicitly_mentioned">Explicitly Mentioned</option>
                    <option value="demonstrated_in_project">Demonstrated in Project</option>
                    <option value="demonstrated_professionally">Demonstrated Professionally</option>
                    <option value="weakly_inferred">Weakly Inferred</option>
                    <option value="not_found">Not Found</option>
                  </select>
                </div>
              </div>

              {evidenceList.length === 0 ? (
                <div className="text-center py-12 bg-slate-50 rounded-xl border border-slate-100">
                  <FileText className="w-8 h-8 text-slate-300 mx-auto mb-2" />
                  <p className="text-xs text-slate-500 font-medium">No verified evidence records found.</p>
                  <p className="text-[11px] text-slate-400 mt-1">
                    Run AI Matching against this candidate to extract grounded citations.
                  </p>
                </div>
              ) : (
                <div className="space-y-3">
                  {evidenceList
                    .filter((ev) =>
                      evidenceFilter === 'all'
                        ? true
                        : ev.confidence_level?.toLowerCase() === evidenceFilter.toLowerCase()
                    )
                    .map((ev, idx) => {
                      const level = ev.confidence_level || 'explicitly_mentioned';
                      const badgeColor =
                        level === 'demonstrated_professionally'
                          ? 'bg-purple-100 text-purple-800'
                          : level === 'demonstrated_in_project'
                          ? 'bg-blue-100 text-blue-800'
                          : level === 'explicitly_mentioned'
                          ? 'bg-emerald-100 text-emerald-800'
                          : level === 'weakly_inferred'
                          ? 'bg-amber-100 text-amber-800'
                          : 'bg-rose-100 text-rose-800';

                      return (
                        <div
                          key={ev.id || idx}
                          className="p-4 rounded-xl bg-white border border-slate-200 shadow-xs space-y-2 text-xs"
                        >
                          <div className="flex items-center justify-between gap-2">
                            <span className="font-bold text-slate-900 text-sm">
                              {ev.claim_text}
                            </span>
                            <span
                              className={`px-2 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider ${badgeColor}`}
                            >
                              {level.replace(/_/g, ' ')}
                            </span>
                          </div>

                          <div className="flex items-center gap-3 text-[11px] text-slate-500">
                            <span>Type: <strong className="text-slate-700 capitalize">{ev.claim_type}</strong></span>
                            <span>•</span>
                            <span>Document: <strong className="text-slate-700">{ev.source_document || candidate.resume?.original_filename || 'Resume'}</strong></span>
                            {ev.page_number && (
                              <>
                                <span>•</span>
                                <span className="font-bold text-blue-600 bg-blue-50 px-1.5 py-0.2 rounded">
                                  Page {ev.page_number}
                                </span>
                              </>
                            )}
                          </div>

                          {ev.exact_quote && (
                            <blockquote className="p-2.5 rounded-lg bg-slate-50 border-l-3 border-blue-500 font-mono text-[11px] text-slate-700 leading-relaxed italic">
                              "{ev.exact_quote}"
                            </blockquote>
                          )}
                        </div>
                      );
                    })}
                </div>
              )}
            </div>
          )}

          {/* TAB 3: AI INTERVIEW QUESTIONS */}
          {activeTab === 'interview' && (
            <div className="space-y-4">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 p-4 bg-blue-50/60 rounded-xl border border-blue-100">
                <div>
                  <h4 className="font-bold text-slate-900 text-xs uppercase tracking-wider flex items-center gap-1.5">
                    <Sparkles className="w-3.5 h-3.5 text-blue-600" />
                    <span>Personalized Interview Intelligence</span>
                  </h4>
                  <p className="text-[11px] text-slate-500 mt-0.5">
                    Tailored interview questions with claim verification rubrics generated by InterviewIntelligenceAgent.
                  </p>
                </div>
                {jobId && (
                  <button
                    onClick={handleGenerateKit}
                    disabled={generatingKit}
                    className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-blue-600 text-white text-xs font-semibold hover:bg-blue-700 transition-colors shadow-xs disabled:opacity-50 shrink-0"
                  >
                    {generatingKit ? (
                      <>
                        <div className="w-3 h-3 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                        <span>Generating Kit...</span>
                      </>
                    ) : (
                      <>
                        <Sparkles className="w-3.5 h-3.5" />
                        <span>{interviewKit ? 'Regenerate Kit' : 'Generate Interview Kit'}</span>
                      </>
                    )}
                  </button>
                )}
              </div>

              {interviewKit && interviewKit.questions?.length > 0 ? (
                <div className="space-y-3">
                  {interviewKit.questions.map((q, idx) => (
                    <div
                      key={idx}
                      className="p-4 bg-slate-50/70 border border-slate-200 rounded-xl space-y-2 text-xs"
                    >
                      <div className="flex items-center justify-between gap-2">
                        <span className="px-2 py-0.5 rounded bg-blue-100 text-blue-700 font-bold text-[10px] uppercase">
                          {q.category?.replace(/_/g, ' ')}
                        </span>
                        {q.claim_to_verify && (
                          <span className="text-[10px] text-amber-800 bg-amber-50 border border-amber-200 px-2 py-0.5 rounded-md font-medium">
                            Verifies Claim: "{q.claim_to_verify}"
                          </span>
                        )}
                      </div>
                      <p className="font-bold text-slate-900 leading-snug text-sm">
                        {idx + 1}. {q.question}
                      </p>
                      {q.purpose && (
                        <p className="text-[11px] text-slate-500 italic">
                          Objective: {q.purpose}
                        </p>
                      )}
                      {q.expected_indicators && q.expected_indicators.length > 0 && (
                        <div className="bg-white p-2.5 rounded-lg border border-slate-100">
                          <span className="font-bold text-emerald-800 text-[10px] uppercase block mb-1">
                            Signals of Competency:
                          </span>
                          <ul className="list-disc pl-4 space-y-0.5 text-[11px] text-slate-600">
                            {q.expected_indicators.map((ind, i) => (
                              <li key={i}>{ind}</li>
                            ))}
                          </ul>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              ) : questions.length > 0 ? (
                <div className="space-y-3">
                  {questions.map((q: any, idx: number) => (
                    <div
                      key={idx}
                      className="p-4 bg-slate-50 border border-slate-200 rounded-xl space-y-2 text-xs"
                    >
                      <div className="flex items-center justify-between">
                        <span className="px-2 py-0.5 rounded bg-blue-100 text-blue-700 font-bold text-[10px] uppercase">
                          {q.type} • {q.skill}
                        </span>
                        <span className="text-[11px] font-medium text-slate-500">
                          Difficulty: {q.difficulty}
                        </span>
                      </div>
                      <p className="font-semibold text-slate-900 leading-relaxed text-sm">
                        {q.question}
                      </p>
                      <div className="pt-2 border-t border-slate-200/60">
                        <span className="font-semibold text-slate-700">Evaluation Criteria: </span>
                        <span className="text-slate-600">{q.evaluation_criteria}</span>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-12 text-slate-400 text-xs bg-slate-50 rounded-xl border border-slate-100">
                  <p>No interview questions formulated yet.</p>
                  <p className="text-[11px] text-slate-400 mt-1">
                    Click "Generate Interview Kit" above to formulate evidence-based questions.
                  </p>
                </div>
              )}
            </div>
          )}

          {/* TAB: OTHER JOB RECOMMENDATIONS */}
          {activeTab === 'recommendations' && (
            <div className="space-y-4">
              <div className="p-4 bg-gradient-to-r from-blue-50/70 via-indigo-50/50 to-purple-50/70 rounded-xl border border-blue-200/80">
                <h4 className="font-bold text-slate-900 text-xs uppercase tracking-wider flex items-center gap-1.5">
                  <Sparkles className="w-3.5 h-3.5 text-blue-600" />
                  <span>AI Cross-Requisition Match Recommendations</span>
                </h4>
                <p className="text-[11px] text-slate-600 mt-0.5">
                  The AI matching engine scanned all other open requisitions in your organization and evaluated this candidate's profile for alternative job placement opportunities.
                </p>
              </div>

              {recommendedJobs.length === 0 ? (
                <div className="text-center py-12 bg-slate-50 rounded-xl border border-slate-100">
                  <Briefcase className="w-8 h-8 text-slate-300 mx-auto mb-2" />
                  <p className="text-xs text-slate-500 font-medium">No other matching job openings found.</p>
                  <p className="text-[11px] text-slate-400 mt-1">
                    Create additional job requisitions to enable cross-role candidate placement.
                  </p>
                </div>
              ) : (
                <div className="space-y-3">
                  {recommendedJobs.map((rec: any, idx: number) => (
                    <div
                      key={idx}
                      className="p-4 bg-white border border-slate-200 rounded-xl hover:border-blue-300 transition-colors shadow-xs space-y-3"
                    >
                      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2">
                        <div>
                          <div className="flex items-center gap-2">
                            <h5 className="font-bold text-slate-900 text-sm">{rec.title}</h5>
                            <span className="text-[10px] px-2 py-0.5 rounded-full font-bold uppercase bg-blue-50 text-blue-700 border border-blue-200">
                              {rec.company}
                            </span>
                          </div>
                          <p className="text-[11px] text-slate-500 mt-0.5">
                            {rec.location} • Min {rec.min_experience} yrs required
                          </p>
                        </div>
                        <div className="flex items-center gap-2 shrink-0">
                          <div className="text-right">
                            <span className="text-[10px] text-slate-400 font-medium block">Match Fit</span>
                            <span className={`text-base font-black ${
                              rec.fit_score >= 70 ? 'text-emerald-600' : rec.fit_score >= 50 ? 'text-blue-600' : 'text-amber-600'
                            }`}>
                              {rec.fit_score}%
                            </span>
                          </div>
                        </div>
                      </div>

                      <p className="text-xs text-slate-600 bg-slate-50 p-2.5 rounded-lg border border-slate-100 leading-relaxed">
                        <strong className="text-slate-800">AI Rationale: </strong>
                        {rec.recommendation_reason}
                      </p>

                      <div className="flex flex-wrap items-center gap-x-4 gap-y-1.5 text-xs">
                        {rec.matched_skills && rec.matched_skills.length > 0 && (
                          <div className="flex items-center gap-1.5 flex-wrap">
                            <span className="text-[10px] font-bold text-emerald-700 uppercase">Aligned Skills:</span>
                            {rec.matched_skills.map((s: string, i: number) => (
                              <span key={i} className="px-1.5 py-0.5 rounded text-[10px] font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200">
                                {s}
                              </span>
                            ))}
                          </div>
                        )}
                        {rec.missing_skills && rec.missing_skills.length > 0 && (
                          <div className="flex items-center gap-1.5 flex-wrap">
                            <span className="text-[10px] font-bold text-amber-700 uppercase">Gaps to Probe:</span>
                            {rec.missing_skills.map((s: string, i: number) => (
                              <span key={i} className="px-1.5 py-0.5 rounded text-[10px] font-medium bg-amber-50 text-amber-700 border border-amber-200">
                                {s}
                              </span>
                            ))}
                          </div>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* TAB 4: RECRUITER NOTES */}
          {activeTab === 'notes' && (
            <div className="space-y-6">
              {/* Add Note */}
              <div className="p-4 bg-slate-50 rounded-xl border border-slate-200 space-y-3">
                <label className="text-xs font-bold text-slate-700 uppercase tracking-wider block">
                  Add Private Recruiter Note
                </label>
                <textarea
                  value={noteContent}
                  onChange={(e) => setNoteContent(e.target.value)}
                  placeholder="Record interview impressions, compensation expectations, or screening remarks..."
                  rows={3}
                  className="w-full text-xs p-3 rounded-lg border border-slate-300 bg-white outline-none focus:border-blue-600"
                />
                <button
                  onClick={handleSaveNote}
                  disabled={savingNote || !noteContent.trim()}
                  className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-blue-600 text-white text-xs font-semibold hover:bg-blue-700 transition-colors disabled:opacity-50"
                >
                  <Save className="w-3.5 h-3.5" />
                  <span>{savingNote ? 'Saving...' : 'Save Note'}</span>
                </button>
              </div>

              {/* Notes List */}
              <div className="space-y-2">
                <h4 className="text-xs font-bold text-slate-400 uppercase tracking-wider">
                  Previous Notes ({savedNotes.length})
                </h4>
                {savedNotes.length === 0 ? (
                  <p className="text-xs text-slate-400 italic">No notes logged yet.</p>
                ) : (
                  savedNotes.map((n) => (
                    <div key={n.id} className="p-3 rounded-xl bg-white border border-slate-200 text-xs">
                      <p className="text-slate-800 leading-relaxed">{n.content}</p>
                      <span className="text-[10px] text-slate-400 mt-1 block">
                        Logged on {new Date(n.created_at).toLocaleString()}
                      </span>
                    </div>
                  ))
                )}
              </div>
            </div>
          )}

          {/* TAB 5: ORIGINAL RESUME DOCUMENT */}
          {activeTab === 'resume' && candidate.resume && (
            <div className="space-y-4">
              <div className="flex flex-wrap items-center justify-between gap-3 p-4 bg-slate-50 rounded-xl border border-slate-200">
                <div className="flex items-center gap-3 min-w-0">
                  <div className="w-10 h-10 rounded-lg bg-blue-100 text-blue-700 flex items-center justify-center font-bold text-xs uppercase shrink-0">
                    {candidate.resume.original_filename?.split('.').pop() || 'DOC'}
                  </div>
                  <div className="min-w-0">
                    <h4 className="text-xs font-bold text-slate-900 truncate">
                      {candidate.resume.original_filename || `${candidate.name}_Resume`}
                    </h4>
                    <p className="text-[11px] text-slate-500">
                      Uploaded on {new Date(candidate.resume.created_at || candidate.created_at).toLocaleDateString()}
                    </p>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => setShowResumeViewer(true)}
                    className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-blue-600 text-white text-xs font-semibold hover:bg-blue-700 transition-colors shadow-sm"
                  >
                    <Eye className="w-3.5 h-3.5" />
                    <span>Open Fullscreen Viewer</span>
                  </button>
                  <button
                    onClick={handleDownloadResume}
                    className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg border border-slate-300 bg-white text-slate-700 text-xs font-medium hover:bg-slate-50 transition-colors"
                  >
                    <Download className="w-3.5 h-3.5" />
                    <span>Download</span>
                  </button>
                </div>
              </div>

              <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-sm">
                <div className="flex items-center justify-between pb-3 mb-4 border-b border-slate-100">
                  <h5 className="text-xs font-bold text-slate-700 uppercase tracking-wider">
                    Extracted Resume Content
                  </h5>
                  <span className="text-[11px] text-slate-400 font-medium">
                    {candidate.resume.raw_text ? `${candidate.resume.raw_text.trim().split(/\s+/).length} words` : ''}
                  </span>
                </div>
                {candidate.resume.raw_text ? (
                  <pre className="whitespace-pre-wrap font-sans text-xs text-slate-800 leading-relaxed max-h-[520px] overflow-y-auto p-4 bg-slate-50/80 rounded-lg border border-slate-100 selection:bg-blue-100">
                    {candidate.resume.raw_text}
                  </pre>
                ) : (
                  <div className="text-center py-12 text-slate-400 text-xs">
                    <FileText className="w-8 h-8 mx-auto mb-2 text-slate-300" />
                    <p>No extracted text available for this document.</p>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Dedicated Resume Viewer Modal */}
      {candidate.resume && showResumeViewer && (
        <ResumeViewerModal
          isOpen={showResumeViewer}
          onClose={() => setShowResumeViewer(false)}
          resumeId={candidate.resume.id}
          candidateName={candidate.name}
          filename={candidate.resume.original_filename}
          rawText={candidate.resume.raw_text}
        />
      )}
    </div>
  );
};
