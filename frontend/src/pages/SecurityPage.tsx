import React from 'react';
import { ShieldCheck, Lock, EyeOff, UserCheck, KeyRound, CheckCircle2 } from 'lucide-react';

export const SecurityPage: React.FC = () => {
  return (
    <div className="space-y-6 max-w-4xl mx-auto">
      <div>
        <h1 className="text-2xl font-black text-slate-900 tracking-tight flex items-center gap-2">
          Security, Privacy & Compliance
          <span className="text-xs font-bold uppercase tracking-wider px-2 py-0.5 rounded-full bg-emerald-100 text-emerald-700">
            Enterprise Grade
          </span>
        </h1>
        <p className="text-xs text-slate-500 mt-1">
          Architectural security measures, ethical AI transparency standards, and PII privacy protections.
        </p>
      </div>

      {/* ── Non-Discrimination Ethical AI Policy ─────────────────── */}
      <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6 space-y-4">
        <div className="flex items-center gap-3 pb-3 border-b border-slate-100">
          <div className="w-10 h-10 rounded-xl bg-emerald-50 text-emerald-600 flex items-center justify-center">
            <EyeOff className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-sm font-bold text-slate-900">
              Ethical AI & Non-Discrimination Mandate
            </h3>
            <p className="text-xs text-slate-500">
              Zero bias guarantee for fair, merit-based talent matching.
            </p>
          </div>
        </div>

        <div className="space-y-3 text-xs text-slate-700 leading-relaxed">
          <p>
            TalentMatch AI strictly evaluates verified technical competencies, relevant project experience,
            and stated educational credentials. The platform explicitly prohibits and enforces technical barriers
            against using sensitive demographic attributes:
          </p>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 pt-1 font-medium">
            <div className="flex items-center gap-2 p-2.5 rounded-lg bg-slate-50 border border-slate-100">
              <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
              <span>No Gender, Age, or Photo analysis</span>
            </div>
            <div className="flex items-center gap-2 p-2.5 rounded-lg bg-slate-50 border border-slate-100">
              <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
              <span>No Race, Caste, or Religion evaluation</span>
            </div>
            <div className="flex items-center gap-2 p-2.5 rounded-lg bg-slate-50 border border-slate-100">
              <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
              <span>Zero Automated Rejection (Human-in-the-Loop)</span>
            </div>
            <div className="flex items-center gap-2 p-2.5 rounded-lg bg-slate-50 border border-slate-100">
              <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
              <span>Evidence-based explainability on every score point</span>
            </div>
          </div>
        </div>
      </div>

      {/* ── Security Architecture ───────────────────────────────── */}
      <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6 space-y-4">
        <div className="flex items-center gap-3 pb-3 border-b border-slate-100">
          <div className="w-10 h-10 rounded-xl bg-blue-50 text-blue-600 flex items-center justify-center">
            <Lock className="w-5 h-5" />
          </div>
          <div>
            <h3 className="text-sm font-bold text-slate-900">Authentication & Access Controls</h3>
            <p className="text-xs text-slate-500">
              Role-based authorization and cryptographic session handling.
            </p>
          </div>
        </div>

        <div className="space-y-3 text-xs text-slate-600">
          <div className="p-3 bg-slate-50 rounded-xl border border-slate-100 flex items-start gap-3">
            <KeyRound className="w-4 h-4 text-blue-600 shrink-0 mt-0.5" />
            <div>
              <p className="font-bold text-slate-900">Bcrypt Password Hashing & JWT Access Tokens</p>
              <p className="text-[11px] text-slate-500 mt-0.5">
                Passwords are salted and hashed using Bcrypt (12 rounds). Stateless HS256 JWT tokens with rotating refresh cycles protect all sensitive REST endpoints.
              </p>
            </div>
          </div>

          <div className="p-3 bg-slate-50 rounded-xl border border-slate-100 flex items-start gap-3">
            <UserCheck className="w-4 h-4 text-indigo-600 shrink-0 mt-0.5" />
            <div>
              <p className="font-bold text-slate-900">Granular Role-Based Access Control (RBAC)</p>
              <p className="text-[11px] text-slate-500 mt-0.5">
                Supports Super Admin, Recruiter, and Hiring Manager personas with scoped permissions for candidate deletion, job configuration, and report exports.
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* ── Role Permissions Matrix ─────────────────────────────── */}
      <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden p-6 space-y-4">
        <div>
          <h3 className="text-sm font-bold text-slate-900">Role Permissions Matrix</h3>
          <p className="text-xs text-slate-500">Access control rights across user tiers</p>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-50 border-b border-slate-200 text-slate-500 font-bold uppercase tracking-wider text-[11px]">
              <tr>
                <th className="p-3 pl-4">Platform Capability</th>
                <th className="p-3 text-center">Super Admin</th>
                <th className="p-3 text-center">Recruiter</th>
                <th className="p-3 text-center">Hiring Manager</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              <tr className="hover:bg-slate-50">
                <td className="p-3 pl-4 font-semibold text-slate-800">Create & Manage Jobs</td>
                <td className="p-3 text-center font-bold text-emerald-600">✓</td>
                <td className="p-3 text-center font-bold text-emerald-600">✓</td>
                <td className="p-3 text-center font-bold text-slate-400">View Only</td>
              </tr>
              <tr className="hover:bg-slate-50">
                <td className="p-3 pl-4 font-semibold text-slate-800">Bulk Upload Resumes (10-50)</td>
                <td className="p-3 text-center font-bold text-emerald-600">✓</td>
                <td className="p-3 text-center font-bold text-emerald-600">✓</td>
                <td className="p-3 text-center font-bold text-slate-400">—</td>
              </tr>
              <tr className="hover:bg-slate-50">
                <td className="p-3 pl-4 font-semibold text-slate-800">Run AI Semantic Matching</td>
                <td className="p-3 text-center font-bold text-emerald-600">✓</td>
                <td className="p-3 text-center font-bold text-emerald-600">✓</td>
                <td className="p-3 text-center font-bold text-emerald-600">✓</td>
              </tr>
              <tr className="hover:bg-slate-50">
                <td className="p-3 pl-4 font-semibold text-slate-800">Shortlist & Add Notes</td>
                <td className="p-3 text-center font-bold text-emerald-600">✓</td>
                <td className="p-3 text-center font-bold text-emerald-600">✓</td>
                <td className="p-3 text-center font-bold text-emerald-600">✓</td>
              </tr>
              <tr className="hover:bg-slate-50">
                <td className="p-3 pl-4 font-semibold text-slate-800">Export Reports (CSV/Excel/PDF)</td>
                <td className="p-3 text-center font-bold text-emerald-600">✓</td>
                <td className="p-3 text-center font-bold text-emerald-600">✓</td>
                <td className="p-3 text-center font-bold text-emerald-600">✓</td>
              </tr>
              <tr className="hover:bg-slate-50">
                <td className="p-3 pl-4 font-semibold text-slate-800">Delete Candidate Data / Resumes</td>
                <td className="p-3 text-center font-bold text-emerald-600">✓</td>
                <td className="p-3 text-center font-bold text-emerald-600">✓</td>
                <td className="p-3 text-center font-bold text-slate-400">—</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
};
