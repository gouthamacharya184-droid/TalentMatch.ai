import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Briefcase,
  UploadCloud,
  Cpu,
  Users,
  Trophy,
  BookmarkCheck,
  TrendingUp,
  Clock,
  Sparkles,
  ArrowRight,
  CheckCircle2,
  AlertCircle
} from 'lucide-react';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid
} from 'recharts';
import { analyticsApi, jobsApi } from '../services/api';
import type { DashboardStats, Job, MatchingAnalysis } from '../types';
import { CandidateDetailModal } from '../components/CandidateDetailModal';

export const DashboardPage: React.FC = () => {
  const navigate = useNavigate();
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [selectedCandidateId, setSelectedCandidateId] = useState<string | null>(null);

  useEffect(() => {
    const fetchDashboard = async () => {
      try {
        const data = await analyticsApi.getDashboard();
        setStats(data);
      } catch (e) {
        console.error(e);
      } finally {
        setLoading(false);
      }
    };
    fetchDashboard();
  }, []);

  if (loading) {
    return (
      <div className="space-y-6 animate-pulse">
        <div className="h-8 bg-slate-200 rounded w-64"></div>
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
          {[...Array(6)].map((_, i) => (
            <div key={i} className="h-28 bg-slate-200 rounded-xl"></div>
          ))}
        </div>
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <div className="h-72 bg-slate-200 rounded-2xl"></div>
          <div className="h-72 bg-slate-200 rounded-2xl"></div>
        </div>
      </div>
    );
  }

  if (!stats) {
    return (
      <div className="p-8 bg-white rounded-2xl border border-rose-200 shadow-sm text-center space-y-4 max-w-lg mx-auto my-12">
        <div className="w-12 h-12 rounded-xl bg-rose-50 text-rose-600 flex items-center justify-center mx-auto">
          <AlertCircle className="w-6 h-6" />
        </div>
        <div>
          <h3 className="text-base font-bold text-slate-900">Dashboard Metrics Unavailable</h3>
          <p className="text-xs text-slate-500 mt-1">
            Unable to connect to the analytics engine. Ensure the backend server is active.
          </p>
        </div>
        <button
          onClick={() => {
            setLoading(true);
            analyticsApi
              .getDashboard()
              .then(setStats)
              .catch(console.error)
              .finally(() => setLoading(false));
          }}
          className="px-4 py-2 bg-blue-600 text-white text-xs font-semibold rounded-xl hover:bg-blue-700 transition-colors shadow-md shadow-blue-500/20 cursor-pointer"
        >
          Retry Loading Dashboard
        </button>
      </div>
    );
  }

  // Format score distribution for recharts
  const scoreData = Object.entries(stats.score_distribution || {}).map(([range, count]) => ({
    range,
    count,
  }));

  // Format skills availability for recharts
  const skillData = Object.entries(stats.skills_availability || {})
    .slice(0, 6)
    .map(([skill, count]) => ({
      skill,
      count,
    }));

  return (
    <div className="space-y-8 max-w-7xl mx-auto">
      {/* ── Page Header ────────────────────────────────────────── */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-black text-slate-900 tracking-tight flex items-center gap-2.5">
            Recruiter Overview
            <span className="text-xs font-bold uppercase tracking-wider px-2 py-0.5 rounded-full bg-blue-100 text-blue-700">
              Live SaaS
            </span>
          </h1>
          <p className="text-xs text-slate-500 mt-1">
            AVOM Consultants AI-Based Resume Matching & Candidate Ranking System.
          </p>
        </div>

        {/* Quick Action Buttons */}
        <div className="flex items-center gap-2.5">
          <button
            onClick={() => navigate('/jobs')}
            className="flex items-center gap-1.5 px-3 py-2 rounded-xl bg-white border border-slate-200 text-xs font-semibold text-slate-700 hover:bg-slate-50 transition-colors shadow-sm"
          >
            <Briefcase className="w-3.5 h-3.5 text-blue-600" />
            <span>Post Job</span>
          </button>
          <button
            onClick={() => navigate('/resumes/upload')}
            className="flex items-center gap-1.5 px-3 py-2 rounded-xl bg-white border border-slate-200 text-xs font-semibold text-slate-700 hover:bg-slate-50 transition-colors shadow-sm"
          >
            <UploadCloud className="w-3.5 h-3.5 text-blue-600" />
            <span>Upload 10-50 Resumes</span>
          </button>
          <button
            onClick={() => navigate('/matching')}
            className="flex items-center gap-1.5 px-3.5 py-2 rounded-xl bg-blue-600 text-white text-xs font-semibold hover:bg-blue-700 transition-colors shadow-md shadow-blue-500/20"
          >
            <Cpu className="w-3.5 h-3.5" />
            <span>Run AI Matching</span>
          </button>
        </div>
      </div>

      {/* ── KPI Metric Cards ───────────────────────────────────── */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
        <div className="bg-white p-4 rounded-2xl border border-slate-200/80 shadow-sm">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-xs font-medium">Jobs Active</span>
            <Briefcase className="w-4 h-4 text-blue-600" />
          </div>
          <p className="text-2xl font-black text-slate-900">{stats.total_jobs}</p>
          <span className="text-[10px] text-slate-400 mt-1 block">Configured roles</span>
        </div>

        <div className="bg-white p-4 rounded-2xl border border-slate-200/80 shadow-sm">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-xs font-medium">Resumes</span>
            <UploadCloud className="w-4 h-4 text-indigo-600" />
          </div>
          <p className="text-2xl font-black text-slate-900">{stats.total_resumes}</p>
          <span className="text-[10px] text-slate-400 mt-1 block">Parsed documents</span>
        </div>

        <div className="bg-white p-4 rounded-2xl border border-slate-200/80 shadow-sm">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-xs font-medium">Candidates</span>
            <Users className="w-4 h-4 text-emerald-600" />
          </div>
          <p className="text-2xl font-black text-slate-900">{stats.total_candidates}</p>
          <span className="text-[10px] text-slate-400 mt-1 block">Applicant profiles</span>
        </div>

        <div className="bg-white p-4 rounded-2xl border border-slate-200/80 shadow-sm">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-xs font-medium">Avg Match</span>
            <TrendingUp className="w-4 h-4 text-blue-600" />
          </div>
          <p className="text-2xl font-black text-blue-600">{stats.avg_matching_score}%</p>
          <span className="text-[10px] text-slate-400 mt-1 block">Across all pool</span>
        </div>

        <div className="bg-white p-4 rounded-2xl border border-slate-200/80 shadow-sm">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-xs font-medium">Shortlisted</span>
            <BookmarkCheck className="w-4 h-4 text-amber-500" />
          </div>
          <p className="text-2xl font-black text-slate-900">{stats.total_shortlisted}</p>
          <span className="text-[10px] text-slate-400 mt-1 block">Selected candidates</span>
        </div>

        <div className="bg-white p-4 rounded-2xl border border-slate-200/80 shadow-sm">
          <div className="flex items-center justify-between text-slate-400 mb-2">
            <span className="text-xs font-medium">Under Review</span>
            <Clock className="w-4 h-4 text-purple-600" />
          </div>
          <p className="text-2xl font-black text-slate-900">{stats.under_review}</p>
          <span className="text-[10px] text-slate-400 mt-1 block">In evaluation</span>
        </div>
      </div>

      {/* ── Charts Grid ────────────────────────────────────────── */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Score Distribution */}
        <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="text-sm font-bold text-slate-900">Score Distribution</h3>
              <p className="text-xs text-slate-500">Candidate alignment tiers (0-100 pts)</p>
            </div>
            <span className="text-xs font-semibold px-2 py-0.5 rounded bg-blue-50 text-blue-700">
              Semantic AI
            </span>
          </div>
          <div className="h-60 w-full">
            {stats.total_candidates > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={scoreData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#F1F5F9" />
                  <XAxis dataKey="range" tick={{ fontSize: 11, fill: '#64748B' }} />
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
            ) : (
              <div className="h-full flex flex-col items-center justify-center text-center p-4">
                <TrendingUp className="w-8 h-8 text-slate-300 mb-2" />
                <p className="text-xs font-medium text-slate-500">No candidate scores yet</p>
                <p className="text-[11px] text-slate-400 mt-0.5">Scores will appear once AI matching runs</p>
              </div>
            )}
          </div>
        </div>

        {/* Skills Availability */}
        <div className="bg-white p-6 rounded-2xl border border-slate-200 shadow-sm">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="text-sm font-bold text-slate-900">Skills Frequency in Pool</h3>
              <p className="text-xs text-slate-500">Top verified technical skills across resumes</p>
            </div>
            <span className="text-xs font-semibold px-2 py-0.5 rounded bg-emerald-50 text-emerald-700">
              Taxonomy Extracted
            </span>
          </div>
          <div className="h-60 w-full">
            {skillData.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={skillData} layout="vertical" margin={{ top: 10, right: 20, left: 20, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="#F1F5F9" />
                  <XAxis type="number" tick={{ fontSize: 11, fill: '#64748B' }} allowDecimals={false} />
                  <YAxis dataKey="skill" type="category" tick={{ fontSize: 11, fill: '#0F172A' }} width={80} />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: '#0F172A',
                      borderRadius: '8px',
                      color: '#fff',
                      fontSize: '12px',
                    }}
                  />
                  <Bar dataKey="count" fill="#10B981" radius={[0, 6, 6, 0]} />
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <div className="h-full flex flex-col items-center justify-center text-center p-4">
                <Users className="w-8 h-8 text-slate-300 mb-2" />
                <p className="text-xs font-medium text-slate-500">No skills data available yet</p>
                <p className="text-[11px] text-slate-400 mt-0.5">Upload resumes to extract technical skills</p>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* ── Tables Grid: Recent Jobs & Top Candidates ──────────── */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Recent Jobs */}
        <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden flex flex-col">
          <div className="p-5 border-b border-slate-100 flex items-center justify-between">
            <div>
              <h3 className="text-sm font-bold text-slate-900">Active Job Openings</h3>
              <p className="text-xs text-slate-500">Jobs ready for resume matching</p>
            </div>
            <button
              onClick={() => navigate('/jobs')}
              className="text-xs font-semibold text-blue-600 hover:text-blue-700 flex items-center gap-1"
            >
              <span>View all</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
          </div>
          <div className="divide-y divide-slate-100 flex-1">
            {stats.recent_jobs && stats.recent_jobs.length > 0 ? (
              stats.recent_jobs.map((j) => (
                <div key={j.id} className="p-4 hover:bg-slate-50 transition-colors flex items-center justify-between">
                  <div>
                    <h4 className="text-xs font-bold text-slate-900">{j.title}</h4>
                    <p className="text-[11px] text-slate-500 mt-0.5">
                      {j.company} • {j.min_experience} yrs min • {j.location}
                    </p>
                  </div>
                  <button
                    onClick={() => navigate(`/ranking?job_id=${j.id}`)}
                    className="px-2.5 py-1 rounded-lg bg-blue-50 text-blue-700 hover:bg-blue-100 text-xs font-medium transition-colors"
                  >
                    View Rankings
                  </button>
                </div>
              ))
            ) : (
              <div className="p-8 text-center flex flex-col items-center justify-center">
                <Briefcase className="w-8 h-8 text-slate-300 mb-2" />
                <p className="text-xs font-medium text-slate-600">No active job openings</p>
                <p className="text-[11px] text-slate-400 mt-0.5">Create your first role to start matching</p>
                <button
                  onClick={() => navigate('/jobs')}
                  className="mt-3 px-3 py-1.5 rounded-lg bg-blue-50 text-blue-600 hover:bg-blue-100 text-xs font-semibold transition-colors"
                >
                  Post a Job
                </button>
              </div>
            )}
          </div>
        </div>

        {/* Top-Ranked Candidates */}
        <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden flex flex-col">
          <div className="p-5 border-b border-slate-100 flex items-center justify-between">
            <div>
              <h3 className="text-sm font-bold text-slate-900">Top-Ranked Candidates</h3>
              <p className="text-xs text-slate-500">Highest matching applicants</p>
            </div>
            <button
              onClick={() => navigate('/ranking')}
              className="text-xs font-semibold text-blue-600 hover:text-blue-700 flex items-center gap-1"
            >
              <span>Full leaderboard</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
          </div>
          <div className="divide-y divide-slate-100 flex-1">
            {stats.top_candidates && stats.top_candidates.length > 0 ? (
              stats.top_candidates.map((a, idx) => (
                <div
                  key={a.id}
                  onClick={() => setSelectedCandidateId(a.candidate_id)}
                  className="p-4 hover:bg-slate-50 transition-colors flex items-center justify-between cursor-pointer"
                >
                  <div className="flex items-center gap-3">
                    <span
                      className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold ${
                        idx === 0
                          ? 'bg-amber-100 text-amber-700'
                          : idx === 1
                          ? 'bg-slate-200 text-slate-700'
                          : idx === 2
                          ? 'bg-amber-50 text-amber-800'
                          : 'text-slate-400'
                      }`}
                    >
                      {idx + 1}
                    </span>
                    <div>
                      <h4 className="text-xs font-bold text-slate-900">
                        {a.candidate?.name || 'Candidate'}
                      </h4>
                      <p className="text-[11px] text-slate-500">
                        {a.candidate?.total_experience_years || 0}y Exp • {a.matched_skills?.length || 0} skills matched
                      </p>
                    </div>
                  </div>
                  <div className="text-right">
                    <span className="text-sm font-black text-emerald-600 block">{a.overall_score}%</span>
                    <span className="text-[10px] text-slate-400">Match score</span>
                  </div>
                </div>
              ))
            ) : (
              <div className="p-8 text-center flex flex-col items-center justify-center">
                <Users className="w-8 h-8 text-slate-300 mb-2" />
                <p className="text-xs font-medium text-slate-600">No ranked candidates yet</p>
                <p className="text-[11px] text-slate-400 mt-0.5">Upload resumes and run matching to see rankings</p>
                <button
                  onClick={() => navigate('/resumes/upload')}
                  className="mt-3 px-3 py-1.5 rounded-lg bg-blue-50 text-blue-600 hover:bg-blue-100 text-xs font-semibold transition-colors"
                >
                  Upload Resumes
                </button>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Candidate Modal */}
      {selectedCandidateId && (
        <CandidateDetailModal
          candidateId={selectedCandidateId}
          onClose={() => setSelectedCandidateId(null)}
        />
      )}
    </div>
  );
};
