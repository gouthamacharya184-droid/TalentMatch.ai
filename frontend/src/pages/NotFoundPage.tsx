import React from 'react';
import { Link } from 'react-router-dom';
import { Home, ArrowLeft, Search, HelpCircle } from 'lucide-react';

export const NotFoundPage: React.FC = () => {
  return (
    <div className="min-h-screen bg-slate-50 flex items-center justify-center p-6 font-sans">
      <div className="max-w-md w-full bg-white rounded-3xl border border-slate-200 p-8 shadow-xl text-center space-y-6">
        <div className="w-16 h-16 rounded-2xl bg-blue-50 text-blue-600 flex items-center justify-center mx-auto border border-blue-100 shadow-sm">
          <Search className="w-8 h-8" />
        </div>

        <div className="space-y-2">
          <span className="text-4xl font-black text-blue-600 tracking-tight">404</span>
          <h1 className="text-xl font-bold text-slate-900">Page Not Found</h1>
          <p className="text-xs text-slate-500 max-w-sm mx-auto leading-relaxed">
            The workspace route or candidate intelligence view you requested does not exist or may have been moved.
          </p>
        </div>

        <div className="pt-2 flex flex-col sm:flex-row items-center justify-center gap-3">
          <Link
            to="/dashboard"
            className="w-full sm:w-auto flex items-center justify-center gap-2 px-5 py-2.5 rounded-xl bg-blue-600 text-white text-xs font-semibold hover:bg-blue-700 transition-colors shadow-md shadow-blue-500/20 cursor-pointer"
          >
            <Home className="w-4 h-4" />
            <span>Dashboard</span>
          </Link>
          <button
            onClick={() => window.history.back()}
            className="w-full sm:w-auto flex items-center justify-center gap-2 px-5 py-2.5 rounded-xl bg-white border border-slate-200 text-slate-700 text-xs font-semibold hover:bg-slate-50 transition-colors cursor-pointer"
          >
            <ArrowLeft className="w-4 h-4" />
            <span>Go Back</span>
          </button>
        </div>

        <div className="pt-4 border-t border-slate-100 flex items-center justify-center gap-1.5 text-[11px] text-slate-400">
          <HelpCircle className="w-3.5 h-3.5" />
          <span>Need assistance? Contact support@talentmatch.ai</span>
        </div>
      </div>
    </div>
  );
};

export default NotFoundPage;
