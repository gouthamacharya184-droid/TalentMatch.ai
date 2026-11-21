import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Briefcase,
  Plus,
  Search,
  Filter,
  Trash2,
  Edit3,
  Cpu,
  Trophy,
  CheckCircle2,
  X,
  Sparkles,
  FileText,
  Upload
} from 'lucide-react';
import { jobsApi } from '../services/api';
import type { Job, JobRequirement } from '../types';
import { formatApiError } from '../utils/errors';

export const JobsPage: React.FC = () => {
  const navigate = useNavigate();
  const [jobs, setJobs] = useState<Job[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [isCreateOpen, setIsCreateOpen] = useState(false);
  const [selectedJob, setSelectedJob] = useState<Job | null>(null);
  const [isEditReqsOpen, setIsEditReqsOpen] = useState(false);

  // Criteria Approval State
  const [isApproveOpen, setIsApproveOpen] = useState(false);
  const [approvingJob, setApprovingJob] = useState<Job | null>(null);
  const [approving, setApproving] = useState(false);
  const [approveWeights, setApproveWeights] = useState({
    required_skills: 35,
    relevant_projects: 25,
    professional_experience: 15,
    preferred_skills: 15,
    education_certifications: 10,
  });

  const openApproveModal = (job: Job) => {
    setApprovingJob(job);
    if (job.scoring_weights) {
      setApproveWeights({
        required_skills: job.scoring_weights.required_skills ?? 35,
        relevant_projects: job.scoring_weights.relevant_projects ?? 25,
        professional_experience: job.scoring_weights.professional_experience ?? 15,
        preferred_skills: job.scoring_weights.preferred_skills ?? 15,
        education_certifications: job.scoring_weights.education_certifications ?? 10,
      });
    }
    setIsApproveOpen(true);
  };

  const handleApproveCriteria = async () => {
    if (!approvingJob) return;
    setApproving(true);
    try {
      await jobsApi.approveCriteria(approvingJob.id, approveWeights);
      setIsApproveOpen(false);
      setApprovingJob(null);
      fetchJobs();
    } catch (e: any) {
      alert(formatApiError(e, 'Failed to approve job criteria.'));
    } finally {
      setApproving(false);
    }
  };

  // New Job Form State
  const [title, setTitle] = useState('');
  const [company, setCompany] = useState('AVOM Consultants');
  const [location, setLocation] = useState('Remote');
  const [employmentType, setEmploymentType] = useState('Full-time');
  const [minExp, setMinExp] = useState(3.0);
  const [educationReq, setEducationReq] = useState("Bachelor's Degree");
  const [description, setDescription] = useState('');
  const [creating, setCreating] = useState(false);
  const [uploadingJd, setUploadingJd] = useState(false);
  const jdFileInputRef = React.useRef<HTMLInputElement>(null);

  const handleJdFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setUploadingJd(true);
    try {
      const parsed = await jobsApi.uploadJDDocument(file);
      if (parsed.title) setTitle(parsed.title);
      if (parsed.company) setCompany(parsed.company);
      if (parsed.location) setLocation(parsed.location);
      if (parsed.min_experience !== undefined) setMinExp(parsed.min_experience);
      if (parsed.education_req) setEducationReq(parsed.education_req);
      if (parsed.description) setDescription(parsed.description);
    } catch (err: any) {
      alert(formatApiError(err, 'Failed to parse job description file.'));
    } finally {
      setUploadingJd(false);
      if (e.target) e.target.value = '';
    }
  };

  // Requirements Edit State
  const [editRequirements, setEditRequirements] = useState<Partial<JobRequirement>[]>([]);
  const [newSkillName, setNewSkillName] = useState('');
  const [newSkillCategory, setNewSkillCategory] = useState<'mandatory' | 'preferred'>('mandatory');

  const fetchJobs = async () => {
    setLoading(true);
    try {
      const res = await jobsApi.getJobs({ search: search || undefined });
      setJobs(res.items);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchJobs();
  }, [search]);

  const handleCreateJob = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!title || !description) return;
    setCreating(true);
    try {
      await jobsApi.createJob({
        title,
        company,
        location,
        employment_type: employmentType,
        min_experience: Number(minExp),
        education_req: educationReq,
        description,
      });
      setIsCreateOpen(false);
      resetForm();
      fetchJobs();
    } catch (e) {
      console.error(e);
    } finally {
      setCreating(false);
    }
  };

  const resetForm = () => {
    setTitle('');
    setCompany('AVOM Consultants');
    setLocation('Remote');
    setMinExp(3.0);
    setDescription('');
  };

  const handleDeleteJob = async (id: string) => {
    if (!window.confirm('Are you sure you want to delete this job description?')) return;
    try {
      await jobsApi.deleteJob(id);
      fetchJobs();
    } catch (e) {
      console.error(e);
    }
  };

  const openEditReqs = (job: Job) => {
    setSelectedJob(job);
    setEditRequirements(job.requirements || []);
    setIsEditReqsOpen(true);
  };

  const handleAddSkill = () => {
    if (!newSkillName.trim()) return;
    setEditRequirements([
      ...editRequirements,
      {
        skill_name: newSkillName.trim(),
        category: newSkillCategory,
        skill_type: 'technical',
      },
    ]);
    setNewSkillName('');
  };

  const handleRemoveSkill = (index: number) => {
    setEditRequirements(editRequirements.filter((_, i) => i !== index));
  };

  const handleSaveRequirements = async () => {
    if (!selectedJob) return;
    try {
      await jobsApi.updateRequirements(selectedJob.id, editRequirements);
      setIsEditReqsOpen(false);
      fetchJobs();
    } catch (e) {
      console.error(e);
    }
  };

  const handleReExtract = async (jobId: string) => {
    try {
      const reqs = await jobsApi.extractRequirements(jobId);
      setEditRequirements(reqs);
      fetchJobs();
    } catch (e) {
      console.error(e);
    }
  };

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* ── Page Header ────────────────────────────────────────── */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-black text-slate-900 tracking-tight">Job Descriptions</h1>
          <p className="text-xs text-slate-500 mt-1">
            Create, manage, and configure skills requirements for AI resume matching.
          </p>
        </div>

        <button
          onClick={() => setIsCreateOpen(true)}
          className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-blue-600 text-white text-xs font-semibold hover:bg-blue-700 transition-colors shadow-md shadow-blue-500/20 shrink-0"
        >
          <Plus className="w-4 h-4" />
          <span>Create New Job</span>
        </button>
      </div>

      {/* ── Search Bar ─────────────────────────────────────────── */}
      <div className="flex items-center gap-3 bg-white p-3 rounded-2xl border border-slate-200 shadow-sm">
        <Search className="w-4 h-4 text-slate-400 ml-2" />
        <input
          type="text"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Filter jobs by title or company..."
          className="w-full text-xs bg-transparent border-none outline-none text-slate-800 placeholder-slate-400"
        />
      </div>

      {/* ── Jobs Table ─────────────────────────────────────────── */}
      <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-50 border-b border-slate-200 text-slate-500 font-bold uppercase tracking-wider text-[11px]">
              <tr>
                <th className="p-4 pl-6">Job Title & Company</th>
                <th className="p-4">Location</th>
                <th className="p-4">Min Exp</th>
                <th className="p-4">Key Requirements</th>
                <th className="p-4">Status</th>
                <th className="p-4 pr-6 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {loading ? (
                <tr>
                  <td colSpan={6} className="p-8 text-center text-slate-400">
                    Loading jobs...
                  </td>
                </tr>
              ) : jobs.length === 0 ? (
                <tr>
                  <td colSpan={6} className="p-8 text-center text-slate-400">
                    No job descriptions found. Click "Create New Job" to add one.
                  </td>
                </tr>
              ) : (
                jobs.map((job) => (
                  <tr key={job.id} className="hover:bg-slate-50 transition-colors">
                    <td className="p-4 pl-6">
                      <p className="font-bold text-slate-900 text-sm">{job.title}</p>
                      <p className="text-[11px] text-slate-500">{job.company}</p>
                    </td>
                    <td className="p-4 text-slate-600 font-medium">{job.location}</td>
                    <td className="p-4 text-slate-600">{job.min_experience} Years</td>
                    <td className="p-4 max-w-xs">
                      <div className="flex flex-wrap gap-1">
                        {job.requirements?.slice(0, 4).map((r) => (
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
                        {(job.requirements?.length || 0) > 4 && (
                          <span className="text-[10px] text-slate-400 font-medium">
                            +{(job.requirements?.length || 0) - 4} more
                          </span>
                        )}
                      </div>
                    </td>
                    <td className="p-4">
                      <div className="space-y-1">
                        <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wide bg-emerald-100 text-emerald-700 block w-max">
                          {job.status}
                        </span>
                        {job.criteria_approved ? (
                          <span className="inline-flex items-center gap-1 text-[10px] font-semibold text-emerald-700">
                            <CheckCircle2 className="w-3 h-3 text-emerald-600" />
                            Approved
                          </span>
                        ) : (
                          <button
                            onClick={() => openApproveModal(job)}
                            className="inline-flex items-center gap-1 text-[10px] font-bold text-amber-700 bg-amber-50 border border-amber-200 px-2 py-0.5 rounded-md hover:bg-amber-100 transition-colors"
                            title="Review extracted criteria and approve for screening"
                          >
                            <Sparkles className="w-3 h-3 text-amber-600" />
                            Review Criteria
                          </button>
                        )}
                      </div>
                    </td>
                    <td className="p-4 pr-6 text-right space-x-2">
                      <button
                        onClick={() => openApproveModal(job)}
                        title="Review & Approve AI Criteria"
                        className="p-1.5 rounded-lg border border-slate-200 text-slate-600 hover:text-purple-600 hover:bg-purple-50 transition-colors"
                      >
                        <Sparkles className="w-3.5 h-3.5 text-purple-600" />
                      </button>
                      <button
                        onClick={() => openEditReqs(job)}
                        title="Edit Extracted Skills"
                        className="p-1.5 rounded-lg border border-slate-200 text-slate-600 hover:text-blue-600 hover:bg-blue-50 transition-colors"
                      >
                        <Edit3 className="w-3.5 h-3.5" />
                      </button>
                      <button
                        onClick={() => navigate(`/matching?job_id=${job.id}`)}
                        title="Run Matching"
                        className="px-2.5 py-1 rounded-lg bg-blue-600 text-white font-medium hover:bg-blue-700 transition-colors"
                      >
                        Match Resumes
                      </button>
                      <button
                        onClick={() => navigate(`/ranking?job_id=${job.id}`)}
                        title="View Leaderboard"
                        className="p-1.5 rounded-lg border border-slate-200 text-slate-600 hover:text-amber-600 hover:bg-amber-50 transition-colors"
                      >
                        <Trophy className="w-3.5 h-3.5" />
                      </button>
                      <button
                        onClick={() => handleDeleteJob(job.id)}
                        title="Delete Job"
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

      {/* ── Modal: Create Job Description ──────────────────────── */}
      {isCreateOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/50 backdrop-blur-sm p-4 overflow-y-auto">
          <div className="bg-white rounded-2xl max-w-2xl w-full p-6 shadow-2xl border border-slate-200 animate-in fade-in zoom-in-95 duration-200">
            <div className="flex items-center justify-between pb-4 border-b border-slate-100">
              <div className="flex items-center gap-2.5">
                <div className="w-8 h-8 rounded-xl bg-blue-100 text-blue-600 flex items-center justify-center">
                  <Briefcase className="w-4 h-4" />
                </div>
                <div>
                  <h3 className="text-base font-bold text-slate-900">Create Job Description</h3>
                  <p className="text-xs text-slate-500">AI automatically extracts requirements.</p>
                </div>
              </div>
              <button onClick={() => setIsCreateOpen(false)}>
                <X className="w-5 h-5 text-slate-400 hover:text-slate-700" />
              </button>
            </div>

            <div className="mt-4 p-3.5 bg-blue-50/60 border border-blue-200/80 rounded-xl flex items-center justify-between gap-3">
              <div className="flex items-center gap-2.5">
                <FileText className="w-5 h-5 text-blue-600 shrink-0" />
                <div>
                  <p className="text-xs font-bold text-slate-800">Upload Job Description Document</p>
                  <p className="text-[11px] text-slate-500">Supports PDF, DOCX, or TXT format with auto-extraction.</p>
                </div>
              </div>
              <div>
                <input
                  ref={jdFileInputRef}
                  type="file"
                  accept=".pdf,.docx,.doc,.txt"
                  onChange={handleJdFileUpload}
                  className="hidden"
                />
                <button
                  type="button"
                  disabled={uploadingJd}
                  onClick={() => jdFileInputRef.current?.click()}
                  className="px-3 py-1.5 bg-white border border-blue-300 rounded-lg text-blue-700 text-xs font-bold hover:bg-blue-50 flex items-center gap-1.5 shadow-sm disabled:opacity-50"
                >
                  <Upload className="w-3.5 h-3.5" />
                  <span>{uploadingJd ? 'Extracting...' : 'Browse JD File'}</span>
                </button>
              </div>
            </div>

            <form onSubmit={handleCreateJob} className="space-y-4 mt-4 text-xs">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block font-semibold text-slate-700 mb-1">Job Title *</label>
                  <input
                    type="text"
                    required
                    value={title}
                    onChange={(e) => setTitle(e.target.value)}
                    placeholder="e.g. Senior Backend Engineer"
                    className="w-full p-2.5 rounded-lg border border-slate-300 outline-none focus:border-blue-600"
                  />
                </div>
                <div>
                  <label className="block font-semibold text-slate-700 mb-1">Company *</label>
                  <input
                    type="text"
                    required
                    value={company}
                    onChange={(e) => setCompany(e.target.value)}
                    className="w-full p-2.5 rounded-lg border border-slate-300 outline-none focus:border-blue-600"
                  />
                </div>
              </div>

              <div className="grid grid-cols-3 gap-4">
                <div>
                  <label className="block font-semibold text-slate-700 mb-1">Location</label>
                  <input
                    type="text"
                    value={location}
                    onChange={(e) => setLocation(e.target.value)}
                    className="w-full p-2.5 rounded-lg border border-slate-300 outline-none focus:border-blue-600"
                  />
                </div>
                <div>
                  <label className="block font-semibold text-slate-700 mb-1">Min Experience (Yrs)</label>
                  <input
                    type="number"
                    step="0.5"
                    min="0"
                    value={minExp}
                    onChange={(e) => setMinExp(Number(e.target.value))}
                    className="w-full p-2.5 rounded-lg border border-slate-300 outline-none focus:border-blue-600"
                  />
                </div>
                <div>
                  <label className="block font-semibold text-slate-700 mb-1">Employment Type</label>
                  <select
                    value={employmentType}
                    onChange={(e) => setEmploymentType(e.target.value)}
                    className="w-full p-2.5 rounded-lg border border-slate-300 outline-none focus:border-blue-600 bg-white"
                  >
                    <option value="Full-time">Full-time</option>
                    <option value="Part-time">Part-time</option>
                    <option value="Contract">Contract</option>
                  </select>
                </div>
              </div>

              <div>
                <label className="block font-semibold text-slate-700 mb-1">
                  Job Description & Qualifications *
                </label>
                <textarea
                  required
                  rows={6}
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  placeholder="Paste complete job description, technical requirements, responsibilities, and qualifications..."
                  className="w-full p-3 rounded-lg border border-slate-300 outline-none focus:border-blue-600 leading-relaxed"
                />
              </div>

              <div className="flex items-center justify-end gap-3 pt-3 border-t border-slate-100">
                <button
                  type="button"
                  onClick={() => setIsCreateOpen(false)}
                  className="px-4 py-2 rounded-lg border border-slate-200 text-slate-600 font-medium hover:bg-slate-50"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={creating}
                  className="flex items-center gap-1.5 px-4 py-2 rounded-lg bg-blue-600 text-white font-semibold hover:bg-blue-700 disabled:opacity-50"
                >
                  <Sparkles className="w-3.5 h-3.5" />
                  <span>{creating ? 'Extracting & Saving...' : 'Create & Extract Skills'}</span>
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* ── Modal: Recruiter Skill Requirements Editor ─────────── */}
      {isEditReqsOpen && selectedJob && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/50 backdrop-blur-sm p-4 overflow-y-auto">
          <div className="bg-white rounded-2xl max-w-xl w-full p-6 shadow-2xl border border-slate-200 animate-in fade-in zoom-in-95 duration-200">
            <div className="flex items-center justify-between pb-4 border-b border-slate-100">
              <div>
                <h3 className="text-base font-bold text-slate-900">
                  Configure Job Skills: {selectedJob.title}
                </h3>
                <p className="text-xs text-slate-500">
                  Review, edit, add, or categorize skills as mandatory or preferred.
                </p>
              </div>
              <button onClick={() => setIsEditReqsOpen(false)}>
                <X className="w-5 h-5 text-slate-400 hover:text-slate-700" />
              </button>
            </div>

            {/* Add Custom Skill */}
            <div className="flex items-center gap-2 mt-4">
              <input
                type="text"
                value={newSkillName}
                onChange={(e) => setNewSkillName(e.target.value)}
                placeholder="Add custom skill (e.g. PyTorch, Docker)..."
                className="flex-1 p-2 rounded-lg border border-slate-300 text-xs outline-none focus:border-blue-600"
              />
              <select
                value={newSkillCategory}
                onChange={(e) => setNewSkillCategory(e.target.value as any)}
                className="p-2 rounded-lg border border-slate-300 text-xs bg-white outline-none"
              >
                <option value="mandatory">Mandatory</option>
                <option value="preferred">Preferred</option>
              </select>
              <button
                onClick={handleAddSkill}
                className="px-3 py-2 bg-slate-900 text-white rounded-lg text-xs font-semibold hover:bg-slate-800"
              >
                Add
              </button>
            </div>

            {/* Skills List */}
            <div className="mt-4 max-h-64 overflow-y-auto space-y-2 pr-1">
              {editRequirements.map((req, idx) => (
                <div
                  key={idx}
                  className="flex items-center justify-between p-2.5 rounded-xl bg-slate-50 border border-slate-200 text-xs"
                >
                  <span className="font-bold text-slate-900">{req.skill_name}</span>
                  <div className="flex items-center gap-2">
                    <span
                      className={`px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider ${
                        req.category === 'mandatory'
                          ? 'bg-blue-100 text-blue-700'
                          : 'bg-slate-200 text-slate-600'
                      }`}
                    >
                      {req.category}
                    </span>
                    <button
                      onClick={() => handleRemoveSkill(idx)}
                      className="text-slate-400 hover:text-rose-600 p-1"
                    >
                      <X className="w-3.5 h-3.5" />
                    </button>
                  </div>
                </div>
              ))}
            </div>

            <div className="flex items-center justify-between pt-4 border-t border-slate-100 mt-4">
              <button
                onClick={() => handleReExtract(selectedJob.id)}
                className="text-xs font-semibold text-blue-600 hover:underline flex items-center gap-1"
              >
                <Sparkles className="w-3.5 h-3.5" />
                <span>Re-Extract via AI</span>
              </button>
              <div className="flex items-center gap-2">
                <button
                  onClick={() => setIsEditReqsOpen(false)}
                  className="px-4 py-2 rounded-lg border border-slate-200 text-slate-600 text-xs font-medium hover:bg-slate-50"
                >
                  Cancel
                </button>
                <button
                  onClick={handleSaveRequirements}
                  className="px-4 py-2 rounded-lg bg-blue-600 text-white text-xs font-semibold hover:bg-blue-700"
                >
                  Save Requirements
                </button>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* ── Modal: Criteria Review & Approval Workflow ─────────── */}
      {isApproveOpen && approvingJob && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/50 backdrop-blur-sm p-4 overflow-y-auto">
          <div className="bg-white rounded-2xl max-w-2xl w-full p-6 shadow-2xl border border-slate-200 animate-in fade-in zoom-in-95 duration-200">
            <div className="flex items-center justify-between pb-4 border-b border-slate-100">
              <div className="flex items-center gap-2.5">
                <div className="w-8 h-8 rounded-xl bg-purple-100 text-purple-600 flex items-center justify-center">
                  <Sparkles className="w-4 h-4" />
                </div>
                <div>
                  <h3 className="text-base font-bold text-slate-900">
                    Review & Approve Criteria: {approvingJob.title}
                  </h3>
                  <p className="text-xs text-slate-500">
                    Human-in-the-loop checkpoint before candidate screening and ranking.
                  </p>
                </div>
              </div>
              <button onClick={() => setIsApproveOpen(false)}>
                <X className="w-5 h-5 text-slate-400 hover:text-slate-700" />
              </button>
            </div>

            <div className="space-y-4 mt-4 text-xs">
              {/* Job Summary Banner */}
              <div className="p-3 bg-slate-50 rounded-xl border border-slate-200 flex flex-wrap gap-4 justify-between items-center">
                <div>
                  <span className="text-[10px] text-slate-400 uppercase font-bold block">Target Organization</span>
                  <span className="font-semibold text-slate-800">{approvingJob.company}</span>
                </div>
                <div>
                  <span className="text-[10px] text-slate-400 uppercase font-bold block">Experience Requirement</span>
                  <span className="font-semibold text-slate-800">{approvingJob.min_experience} Years Minimum</span>
                </div>
                <div>
                  <span className="text-[10px] text-slate-400 uppercase font-bold block">Education Requirement</span>
                  <span className="font-semibold text-slate-800">{approvingJob.education_req || 'Degree Equivalent'}</span>
                </div>
              </div>

              {/* Mandatory vs Preferred Requirements */}
              <div>
                <h4 className="font-bold text-slate-700 uppercase text-[11px] tracking-wider mb-2">
                  Extracted Competencies & Skills
                </h4>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  <div className="p-3 rounded-xl bg-blue-50/70 border border-blue-200 space-y-2">
                    <span className="text-[11px] font-bold text-blue-900 uppercase tracking-wider block">
                      Mandatory Requirements ({approvingJob.requirements?.filter((r) => r.category === 'mandatory').length || 0})
                    </span>
                    <div className="flex flex-wrap gap-1.5">
                      {approvingJob.requirements
                        ?.filter((r) => r.category === 'mandatory')
                        .map((r) => (
                          <span
                            key={r.id}
                            className="px-2 py-0.5 rounded-md bg-blue-100 text-blue-800 text-[11px] font-semibold"
                          >
                            {r.skill_name}
                          </span>
                        ))}
                    </div>
                  </div>

                  <div className="p-3 rounded-xl bg-slate-50 border border-slate-200 space-y-2">
                    <span className="text-[11px] font-bold text-slate-700 uppercase tracking-wider block">
                      Preferred / Nice-to-Have ({approvingJob.requirements?.filter((r) => r.category !== 'mandatory').length || 0})
                    </span>
                    <div className="flex flex-wrap gap-1.5">
                      {approvingJob.requirements
                        ?.filter((r) => r.category !== 'mandatory')
                        .map((r) => (
                          <span
                            key={r.id}
                            className="px-2 py-0.5 rounded-md bg-white border border-slate-200 text-slate-700 text-[11px] font-medium"
                          >
                            {r.skill_name}
                          </span>
                        ))}
                    </div>
                  </div>
                </div>
              </div>

              {/* Scoring Weights Customizer */}
              <div>
                <h4 className="font-bold text-slate-700 uppercase text-[11px] tracking-wider mb-2">
                  Scoring Criteria Weights Configuration
                </h4>
                <div className="grid grid-cols-2 sm:grid-cols-5 gap-2 p-3 bg-purple-50/40 rounded-xl border border-purple-100">
                  <div>
                    <label className="text-[10px] font-bold text-slate-600 block mb-1">Required (35%)</label>
                    <input
                      type="number"
                      min={0}
                      max={100}
                      value={approveWeights.required_skills}
                      onChange={(e) =>
                        setApproveWeights({
                          ...approveWeights,
                          required_skills: Number(e.target.value),
                        })
                      }
                      className="w-full p-1.5 rounded-lg border border-slate-300 font-bold text-center"
                    />
                  </div>
                  <div>
                    <label className="text-[10px] font-bold text-slate-600 block mb-1">Projects (25%)</label>
                    <input
                      type="number"
                      min={0}
                      max={100}
                      value={approveWeights.relevant_projects}
                      onChange={(e) =>
                        setApproveWeights({
                          ...approveWeights,
                          relevant_projects: Number(e.target.value),
                        })
                      }
                      className="w-full p-1.5 rounded-lg border border-slate-300 font-bold text-center"
                    />
                  </div>
                  <div>
                    <label className="text-[10px] font-bold text-slate-600 block mb-1">Experience (15%)</label>
                    <input
                      type="number"
                      min={0}
                      max={100}
                      value={approveWeights.professional_experience}
                      onChange={(e) =>
                        setApproveWeights({
                          ...approveWeights,
                          professional_experience: Number(e.target.value),
                        })
                      }
                      className="w-full p-1.5 rounded-lg border border-slate-300 font-bold text-center"
                    />
                  </div>
                  <div>
                    <label className="text-[10px] font-bold text-slate-600 block mb-1">Preferred (15%)</label>
                    <input
                      type="number"
                      min={0}
                      max={100}
                      value={approveWeights.preferred_skills}
                      onChange={(e) =>
                        setApproveWeights({
                          ...approveWeights,
                          preferred_skills: Number(e.target.value),
                        })
                      }
                      className="w-full p-1.5 rounded-lg border border-slate-300 font-bold text-center"
                    />
                  </div>
                  <div>
                    <label className="text-[10px] font-bold text-slate-600 block mb-1">Education (10%)</label>
                    <input
                      type="number"
                      min={0}
                      max={100}
                      value={approveWeights.education_certifications}
                      onChange={(e) =>
                        setApproveWeights({
                          ...approveWeights,
                          education_certifications: Number(e.target.value),
                        })
                      }
                      className="w-full p-1.5 rounded-lg border border-slate-300 font-bold text-center"
                    />
                  </div>
                </div>
              </div>

              <div className="flex items-center justify-between pt-4 border-t border-slate-100">
                <button
                  type="button"
                  onClick={() => setIsApproveOpen(false)}
                  className="px-4 py-2 rounded-lg border border-slate-200 text-slate-600 text-xs font-medium hover:bg-slate-50"
                >
                  Cancel
                </button>
                <button
                  type="button"
                  onClick={handleApproveCriteria}
                  disabled={approving}
                  className="px-4 py-2 rounded-xl bg-purple-600 text-white text-xs font-semibold hover:bg-purple-700 disabled:opacity-50 flex items-center gap-1.5 shadow-sm"
                >
                  {approving ? (
                    <>
                      <div className="w-3.5 h-3.5 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                      <span>Approving Criteria...</span>
                    </>
                  ) : (
                    <>
                      <CheckCircle2 className="w-3.5 h-3.5" />
                      <span>Approve Criteria & Unlock Screening</span>
                    </>
                  )}
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
