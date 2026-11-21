import React, { useState } from 'react';
import { Settings, Sliders, CheckCircle2, ShieldCheck, Database, Cpu } from 'lucide-react';

export const SettingsPage: React.FC = () => {
  const [techWeight, setTechWeight] = useState(() => {
    try {
      const saved = localStorage.getItem('talentmatch_scoring_weights');
      return saved ? JSON.parse(saved).techWeight ?? 40 : 40;
    } catch {
      return 40;
    }
  });
  const [semanticWeight, setSemanticWeight] = useState(() => {
    try {
      const saved = localStorage.getItem('talentmatch_scoring_weights');
      return saved ? JSON.parse(saved).semanticWeight ?? 30 : 30;
    } catch {
      return 30;
    }
  });
  const [expWeight, setExpWeight] = useState(() => {
    try {
      const saved = localStorage.getItem('talentmatch_scoring_weights');
      return saved ? JSON.parse(saved).expWeight ?? 20 : 20;
    } catch {
      return 20;
    }
  });
  const [eduWeight, setEduWeight] = useState(() => {
    try {
      const saved = localStorage.getItem('talentmatch_scoring_weights');
      return saved ? JSON.parse(saved).eduWeight ?? 10 : 10;
    } catch {
      return 10;
    }
  });
  const [saved, setSaved] = useState(false);

  const total = techWeight + semanticWeight + expWeight + eduWeight;

  const handleSave = (e: React.FormEvent) => {
    e.preventDefault();
    localStorage.setItem(
      'talentmatch_scoring_weights',
      JSON.stringify({ techWeight, semanticWeight, expWeight, eduWeight })
    );
    setSaved(true);
    setTimeout(() => setSaved(false), 3000);
  };

  return (
    <div className="space-y-6 max-w-4xl mx-auto">
      <div>
        <h1 className="text-2xl font-black text-slate-900 tracking-tight flex items-center gap-2">
          System & Algorithm Settings
          <span className="text-xs font-bold uppercase tracking-wider px-2 py-0.5 rounded-full bg-blue-100 text-blue-700">
            Configuration
          </span>
        </h1>
        <p className="text-xs text-slate-500 mt-1">
          Configure transparent AI scoring weights, semantic models, and file processing boundaries.
        </p>
      </div>

      {saved && (
        <div className="p-3.5 bg-emerald-50 border border-emerald-200 text-emerald-800 rounded-xl text-xs flex items-center gap-2">
          <CheckCircle2 className="w-4 h-4 text-emerald-600" />
          <span>Scoring weights and system parameters successfully updated.</span>
        </div>
      )}

      {/* ── Scoring Algorithm Weights ───────────────────────────── */}
      <form onSubmit={handleSave} className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6 space-y-6">
        <div className="flex items-center justify-between pb-4 border-b border-slate-100">
          <div>
            <h3 className="text-sm font-bold text-slate-900">4-Component Matching Weights</h3>
            <p className="text-xs text-slate-500">
              Configure point allocation for total 100-point candidate scoring.
            </p>
          </div>
          <span
            className={`px-3 py-1 rounded-full text-xs font-bold ${
              total === 100 ? 'bg-emerald-100 text-emerald-800' : 'bg-rose-100 text-rose-800'
            }`}
          >
            Total: {total} / 100 Pts
          </span>
        </div>

        <div className="space-y-4 text-xs">
          <div>
            <div className="flex justify-between font-semibold text-slate-700 mb-1">
              <span>Technical Skills Match ({techWeight}%)</span>
              <span className="text-blue-600">{techWeight} Points</span>
            </div>
            <input
              type="range"
              min="20"
              max="60"
              value={techWeight}
              onChange={(e) => setTechWeight(Number(e.target.value))}
              className="w-full h-2 bg-slate-200 rounded-lg cursor-pointer accent-blue-600"
            />
          </div>

          <div>
            <div className="flex justify-between font-semibold text-slate-700 mb-1">
              <span>Semantic Similarity ({semanticWeight}%)</span>
              <span className="text-blue-600">{semanticWeight} Points</span>
            </div>
            <input
              type="range"
              min="10"
              max="50"
              value={semanticWeight}
              onChange={(e) => setSemanticWeight(Number(e.target.value))}
              className="w-full h-2 bg-slate-200 rounded-lg cursor-pointer accent-blue-600"
            />
          </div>

          <div>
            <div className="flex justify-between font-semibold text-slate-700 mb-1">
              <span>Relevant Experience ({expWeight}%)</span>
              <span className="text-blue-600">{expWeight} Points</span>
            </div>
            <input
              type="range"
              min="10"
              max="35"
              value={expWeight}
              onChange={(e) => setExpWeight(Number(e.target.value))}
              className="w-full h-2 bg-slate-200 rounded-lg cursor-pointer accent-blue-600"
            />
          </div>

          <div>
            <div className="flex justify-between font-semibold text-slate-700 mb-1">
              <span>Education & Qualifications ({eduWeight}%)</span>
              <span className="text-blue-600">{eduWeight} Points</span>
            </div>
            <input
              type="range"
              min="5"
              max="20"
              value={eduWeight}
              onChange={(e) => setEduWeight(Number(e.target.value))}
              className="w-full h-2 bg-slate-200 rounded-lg cursor-pointer accent-blue-600"
            />
          </div>
        </div>

        <div className="pt-4 border-t border-slate-100 flex justify-end">
          <button
            type="submit"
            className="px-4 py-2 bg-blue-600 text-white rounded-xl text-xs font-semibold hover:bg-blue-700 shadow-md shadow-blue-500/20"
          >
            Save Weight Configuration
          </button>
        </div>
      </form>

      {/* ── System Status & Environment ─────────────────────────── */}
      <div className="bg-white rounded-2xl border border-slate-200 shadow-sm p-6 space-y-4 text-xs">
        <h3 className="text-sm font-bold text-slate-900">Runtime & Model Specifications</h3>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-slate-600">
          <div className="p-3 bg-slate-50 rounded-xl border border-slate-100">
            <span className="font-bold text-slate-900 block mb-1">Semantic Embedding Model</span>
            <p className="font-mono text-[11px] text-blue-700">sentence-transformers/all-MiniLM-L6-v2</p>
            <span className="text-[10px] text-slate-400 mt-0.5 block">Zero paid external API dependency</span>
          </div>

          <div className="p-3 bg-slate-50 rounded-xl border border-slate-100">
            <span className="font-bold text-slate-900 block mb-1">Taxonomy Dictionary</span>
            <p className="font-mono text-[11px] text-emerald-700">1,200+ Categorized Skills & Synonyms</p>
            <span className="text-[10px] text-slate-400 mt-0.5 block">Languages, frameworks, databases, cloud, AI/ML</span>
          </div>

          <div className="p-3 bg-slate-50 rounded-xl border border-slate-100">
            <span className="font-bold text-slate-900 block mb-1">Bulk Upload Limits</span>
            <p className="font-medium">10 – 50 Resumes / Batch (15MB max file)</p>
            <span className="text-[10px] text-slate-400 mt-0.5 block">Multi-format: PDF, DOCX, TXT</span>
          </div>

          <div className="p-3 bg-slate-50 rounded-xl border border-slate-100">
            <span className="font-bold text-slate-900 block mb-1">Database Architecture</span>
            <p className="font-medium">PostgreSQL Production / SQLite Local</p>
            <span className="text-[10px] text-slate-400 mt-0.5 block">SQLAlchemy ORM + Alembic Migrations</span>
          </div>
        </div>
      </div>
    </div>
  );
};
