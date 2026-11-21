import React, { useState, useEffect } from 'react';
import {
  Layers,
  Plus,
  Search,
  Briefcase,
  Users,
  CheckCircle2,
  Clock,
  ChevronRight,
  TrendingUp,
  X,
  Target,
  Building,
  MoreVertical,
  Filter
} from 'lucide-react';
import { campaignsApi, jobsApi } from '../services/api';
import type { Campaign, Job } from '../types';
import { formatApiError } from '../utils/errors';

export const CampaignsPage: React.FC = () => {
  const [campaigns, setCampaigns] = useState<Campaign[]>([]);
  const [allJobs, setAllJobs] = useState<Job[]>([]);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [search, setSearch] = useState('');
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [selectedCampaign, setSelectedCampaign] = useState<Campaign | null>(null);
  const [isLinkJobOpen, setIsLinkJobOpen] = useState(false);
  const [jobToLink, setJobToLink] = useState('');

  // Form states for creation
  const [title, setTitle] = useState('');
  const [department, setDepartment] = useState('Engineering');
  const [targetHeadcount, setTargetHeadcount] = useState<number>(3);
  const [description, setDescription] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchCampaigns = async () => {
    setLoading(true);
    try {
      const data = await campaignsApi.getCampaigns(
        statusFilter !== 'all' ? { status: statusFilter } : undefined
      );
      setCampaigns(data);
    } catch (e) {
      console.error(e);
      setError('Failed to fetch recruitment campaigns.');
    } finally {
      setLoading(false);
    }
  };

  const fetchJobs = async () => {
    try {
      const res = await jobsApi.getJobs({ limit: 100 });
      setAllJobs(res.items);
    } catch (e) {
      console.error(e);
    }
  };

  useEffect(() => {
    fetchCampaigns();
    fetchJobs();
  }, [statusFilter]);

  const handleCreateCampaign = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!title.trim()) return;
    setSubmitting(true);
    setError(null);
    try {
      await campaignsApi.createCampaign({
        title: title.trim(),
        department: department.trim(),
        target_headcount: Number(targetHeadcount) || 1,
        description: description.trim(),
        status: 'active',
      });
      setIsCreateOpen(false);
      resetForm();
      fetchCampaigns();
    } catch (err) {
      console.error(err);
      setError(formatApiError(err, 'Failed to create campaign.'));
    } finally {
      setSubmitting(false);
    }
  };

  const handleLinkJob = async () => {
    if (!selectedCampaign || !jobToLink) return;
    try {
      await campaignsApi.linkJob(selectedCampaign.id, jobToLink);
      setIsLinkJobOpen(false);
      setJobToLink('');
      fetchCampaigns();
    } catch (err) {
      alert(formatApiError(err, 'Failed to link job to campaign.'));
    }
  };

  const resetForm = () => {
    setTitle('');
    setDepartment('Engineering');
    setTargetHeadcount(3);
    setDescription('');
  };

  const filteredCampaigns = campaigns.filter((c) =>
    c.title.toLowerCase().includes(search.toLowerCase()) ||
    (c.department && c.department.toLowerCase().includes(search.toLowerCase()))
  );

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* ── Page Header ────────────────────────────────────────── */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-black text-slate-900 tracking-tight">Recruitment Campaigns</h1>
          <p className="text-xs text-slate-500 mt-1">
            Orchestrate strategic hiring drives, group related openings, and track team-level headcount fulfillment.
          </p>
        </div>

        <button
          onClick={() => setIsCreateOpen(true)}
          className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-blue-600 text-white text-xs font-semibold hover:bg-blue-700 transition-colors shadow-md shadow-blue-500/20 shrink-0"
        >
          <Plus className="w-4 h-4" />
          <span>New Campaign</span>
        </button>
      </div>

      {/* ── Filter Bar ─────────────────────────────────────────── */}
      <div className="flex flex-col sm:flex-row items-center gap-3 bg-white p-3 rounded-2xl border border-slate-200 shadow-sm">
        <div className="flex items-center gap-2 w-full sm:w-auto flex-1">
          <Search className="w-4 h-4 text-slate-400 ml-2" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search campaigns by title or department..."
            className="w-full text-xs bg-transparent border-none outline-none text-slate-800 placeholder-slate-400"
          />
        </div>

        <div className="flex items-center gap-2 shrink-0 border-t sm:border-t-0 sm:border-l border-slate-200 pt-2 sm:pt-0 sm:pl-3">
          <Filter className="w-3.5 h-3.5 text-slate-400" />
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="text-xs bg-slate-50 border border-slate-200 rounded-lg px-2.5 py-1.5 text-slate-700 font-medium outline-none focus:border-blue-600"
          >
            <option value="all">All Statuses</option>
            <option value="active">Active</option>
            <option value="draft">Draft</option>
            <option value="paused">Paused</option>
            <option value="closed">Closed</option>
          </select>
        </div>
      </div>

      {/* ── Campaigns Grid ──────────────────────────────────────── */}
      {loading ? (
        <div className="text-center py-16 bg-white rounded-2xl border border-slate-200">
          <div className="w-8 h-8 border-3 border-blue-600 border-t-transparent rounded-full animate-spin mx-auto mb-3"></div>
          <p className="text-xs text-slate-500 font-medium">Loading recruitment campaigns...</p>
        </div>
      ) : filteredCampaigns.length === 0 ? (
        <div className="text-center py-16 bg-white rounded-2xl border border-slate-200">
          <Layers className="w-12 h-12 text-slate-300 mx-auto mb-3" />
          <h3 className="text-sm font-bold text-slate-700">No campaigns found</h3>
          <p className="text-xs text-slate-500 mt-1">
            Create your first hiring campaign to bundle job postings and monitor collective hiring milestones.
          </p>
          <button
            onClick={() => setIsCreateOpen(true)}
            className="mt-4 inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-blue-600 text-white text-xs font-semibold hover:bg-blue-700"
          >
            <Plus className="w-3.5 h-3.5" />
            <span>Create Campaign</span>
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {filteredCampaigns.map((c) => {
            const target = c.target_headcount || 1;
            const hired = c.hired_count || 0;
            const progress = Math.min(100, Math.round((hired / target) * 100));

            return (
              <div
                key={c.id}
                className="bg-white rounded-2xl border border-slate-200/80 p-5 shadow-sm hover:shadow-md transition-all flex flex-col justify-between"
              >
                <div>
                  <div className="flex items-start justify-between gap-3 mb-2">
                    <span
                      className={`px-2 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider ${
                        c.status === 'active'
                          ? 'bg-emerald-100 text-emerald-800'
                          : c.status === 'draft'
                          ? 'bg-slate-100 text-slate-700'
                          : 'bg-amber-100 text-amber-800'
                      }`}
                    >
                      {c.status}
                    </span>
                    <span className="text-[11px] font-medium text-slate-400">
                      {new Date(c.created_at).toLocaleDateString()}
                    </span>
                  </div>

                  <h3 className="font-bold text-slate-900 text-base leading-snug mb-1">{c.title}</h3>
                  <p className="text-xs text-slate-500 line-clamp-2 mb-4">
                    {c.description || 'Strategic recruiting campaign for target talent acquisition.'}
                  </p>

                  <div className="flex items-center gap-4 text-xs text-slate-600 mb-4 pb-4 border-b border-slate-100">
                    <div className="flex items-center gap-1.5">
                      <Building className="w-3.5 h-3.5 text-slate-400" />
                      <span>{c.department || 'General'}</span>
                    </div>
                    <div className="flex items-center gap-1.5">
                      <Target className="w-3.5 h-3.5 text-slate-400" />
                      <span>Target: {target} hires</span>
                    </div>
                  </div>

                  {/* Headcount Progress */}
                  <div className="mb-4">
                    <div className="flex justify-between text-xs mb-1">
                      <span className="text-slate-500 font-medium">Headcount Fulfillment</span>
                      <span className="font-bold text-slate-900">
                        {hired} / {target} ({progress}%)
                      </span>
                    </div>
                    <div className="w-full bg-slate-100 rounded-full h-2 overflow-hidden">
                      <div
                        className={`h-2 rounded-full transition-all ${
                          progress >= 100
                            ? 'bg-emerald-500'
                            : progress > 50
                            ? 'bg-blue-600'
                            : 'bg-blue-400'
                        }`}
                        style={{ width: `${progress}%` }}
                      ></div>
                    </div>
                  </div>

                  {/* Linked Openings */}
                  <div className="space-y-1 mb-4">
                    <p className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">
                      Linked Openings ({c.jobs?.length || 0})
                    </p>
                    {c.jobs && c.jobs.length > 0 ? (
                      <div className="flex flex-wrap gap-1.5">
                        {c.jobs.slice(0, 3).map((job) => (
                          <span
                            key={job.id}
                            className="inline-flex items-center gap-1 px-2 py-0.5 rounded-md bg-slate-100 text-slate-700 text-[11px] font-medium"
                          >
                            <Briefcase className="w-3 h-3 text-slate-400" />
                            {job.title}
                          </span>
                        ))}
                        {c.jobs.length > 3 && (
                          <span className="text-[10px] text-slate-400 self-center">
                            +{c.jobs.length - 3} more
                          </span>
                        )}
                      </div>
                    ) : (
                      <p className="text-xs text-slate-400 italic">No job postings attached.</p>
                    )}
                  </div>
                </div>

                {/* Card Actions */}
                <div className="flex items-center justify-between pt-3 border-t border-slate-100">
                  <button
                    onClick={() => {
                      setSelectedCampaign(c);
                      setIsLinkJobOpen(true);
                    }}
                    className="text-xs font-semibold text-blue-600 hover:text-blue-800 transition-colors flex items-center gap-1"
                  >
                    <Plus className="w-3.5 h-3.5" />
                    <span>Link Job</span>
                  </button>
                  <span className="text-[11px] text-slate-400">
                    ID: {c.id.substring(0, 8)}
                  </span>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* ── Create Campaign Modal ──────────────────────────────── */}
      {isCreateOpen && (
        <div className="fixed inset-0 z-50 bg-slate-900/40 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-lg w-full p-6 shadow-2xl border border-slate-200">
            <div className="flex items-center justify-between pb-4 border-b border-slate-100">
              <h3 className="font-bold text-slate-900 text-base">Create Recruitment Campaign</h3>
              <button
                onClick={() => setIsCreateOpen(false)}
                className="text-slate-400 hover:text-slate-600 p-1"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleCreateCampaign} className="space-y-4 mt-4">
              <div>
                <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">
                  Campaign Title *
                </label>
                <input
                  type="text"
                  required
                  value={title}
                  onChange={(e) => setTitle(e.target.value)}
                  placeholder="e.g. Q3 Global Engineering Expansion"
                  className="w-full text-xs p-2.5 rounded-xl border border-slate-300 outline-none focus:border-blue-600"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">
                    Department
                  </label>
                  <input
                    type="text"
                    value={department}
                    onChange={(e) => setDepartment(e.target.value)}
                    placeholder="Engineering, Product..."
                    className="w-full text-xs p-2.5 rounded-xl border border-slate-300 outline-none focus:border-blue-600"
                  />
                </div>
                <div>
                  <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">
                    Target Headcount *
                  </label>
                  <input
                    type="number"
                    min={1}
                    required
                    value={targetHeadcount}
                    onChange={(e) => setTargetHeadcount(parseInt(e.target.value) || 1)}
                    className="w-full text-xs p-2.5 rounded-xl border border-slate-300 outline-none focus:border-blue-600"
                  />
                </div>
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">
                  Strategic Objective / Notes
                </label>
                <textarea
                  rows={3}
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  placeholder="Describe the hiring scope, deadlines, and key requirements..."
                  className="w-full text-xs p-2.5 rounded-xl border border-slate-300 outline-none focus:border-blue-600"
                />
              </div>

              {error && <p className="text-xs text-rose-600 font-medium">{error}</p>}

              <div className="flex items-center justify-end gap-2 pt-4 border-t border-slate-100">
                <button
                  type="button"
                  onClick={() => setIsCreateOpen(false)}
                  className="px-4 py-2 rounded-xl text-xs font-semibold text-slate-600 hover:bg-slate-100"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={submitting || !title.trim()}
                  className="px-4 py-2 rounded-xl bg-blue-600 text-white text-xs font-semibold hover:bg-blue-700 disabled:opacity-50"
                >
                  {submitting ? 'Creating...' : 'Create Campaign'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* ── Link Job Modal ─────────────────────────────────────── */}
      {isLinkJobOpen && selectedCampaign && (
        <div className="fixed inset-0 z-50 bg-slate-900/40 backdrop-blur-xs flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl max-w-md w-full p-6 shadow-2xl border border-slate-200">
            <div className="flex items-center justify-between pb-3 border-b border-slate-100">
              <h3 className="font-bold text-slate-900 text-sm">
                Link Job Opening to {selectedCampaign.title}
              </h3>
              <button
                onClick={() => setIsLinkJobOpen(false)}
                className="text-slate-400 hover:text-slate-600 p-1"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            <div className="space-y-4 mt-4">
              <p className="text-xs text-slate-500">
                Select an existing job description to associate with this campaign.
              </p>

              <div>
                <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">
                  Select Job Description
                </label>
                <select
                  value={jobToLink}
                  onChange={(e) => setJobToLink(e.target.value)}
                  className="w-full text-xs p-2.5 rounded-xl border border-slate-300 outline-none focus:border-blue-600"
                >
                  <option value="">-- Choose Job --</option>
                  {allJobs.map((j) => (
                    <option key={j.id} value={j.id}>
                      {j.title} ({j.company || 'AVOM Consultants'})
                    </option>
                  ))}
                </select>
              </div>

              <div className="flex items-center justify-end gap-2 pt-3 border-t border-slate-100">
                <button
                  type="button"
                  onClick={() => setIsLinkJobOpen(false)}
                  className="px-3.5 py-1.5 rounded-xl text-xs font-semibold text-slate-600 hover:bg-slate-100"
                >
                  Cancel
                </button>
                <button
                  type="button"
                  onClick={handleLinkJob}
                  disabled={!jobToLink}
                  className="px-4 py-1.5 rounded-xl bg-blue-600 text-white text-xs font-semibold hover:bg-blue-700 disabled:opacity-50"
                >
                  Link Job
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
