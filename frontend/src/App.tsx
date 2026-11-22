import React, { Suspense } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import { DashboardLayout } from './layouts/DashboardLayout';
import { ErrorBoundary } from './components/ErrorBoundary';

// Loading Skeleton for Lazy-Loaded Pages
const PageLoadingFallback: React.FC = () => (
  <div className="p-8 space-y-6 max-w-7xl mx-auto animate-pulse">
    <div className="h-8 bg-slate-200 dark:bg-slate-700 rounded-lg w-1/4"></div>
    <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
      <div className="h-32 bg-slate-100 dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700"></div>
      <div className="h-32 bg-slate-100 dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700"></div>
      <div className="h-32 bg-slate-100 dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700"></div>
    </div>
    <div className="h-96 bg-slate-100 dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700"></div>
  </div>
);

// Lazy-Loaded Pages for High Performance & Code Splitting
const DashboardPage = React.lazy(() => import('./pages/DashboardPage').then(m => ({ default: m.DashboardPage })));
const ResumeUploadPage = React.lazy(() => import('./pages/ResumeUploadPage').then(m => ({ default: m.ResumeUploadPage })));
const AIMatchingPage = React.lazy(() => import('./pages/AIMatchingPage').then(m => ({ default: m.AIMatchingPage })));
const CandidatesPage = React.lazy(() => import('./pages/CandidatesPage').then(m => ({ default: m.CandidatesPage })));
const CandidateRankingPage = React.lazy(() => import('./pages/CandidateRankingPage').then(m => ({ default: m.CandidateRankingPage })));
const ShortlistPage = React.lazy(() => import('./pages/ShortlistPage').then(m => ({ default: m.ShortlistPage })));
const AnalyticsPage = React.lazy(() => import('./pages/AnalyticsPage').then(m => ({ default: m.AnalyticsPage })));
const AnalysisHistoryPage = React.lazy(() => import('./pages/AnalysisHistoryPage').then(m => ({ default: m.AnalysisHistoryPage })));
const ProfilePage = React.lazy(() => import('./pages/ProfilePage').then(m => ({ default: m.ProfilePage })));
const SettingsPage = React.lazy(() => import('./pages/SettingsPage').then(m => ({ default: m.SettingsPage })));
const SecurityPage = React.lazy(() => import('./pages/SecurityPage').then(m => ({ default: m.SecurityPage })));
const LoginPage = React.lazy(() => import('./pages/LoginPage').then(m => ({ default: m.LoginPage })));
const RegisterPage = React.lazy(() => import('./pages/RegisterPage').then(m => ({ default: m.RegisterPage })));
const AgentActivityPage = React.lazy(() => import('./pages/AgentActivityPage').then(m => ({ default: m.AgentActivityPage })));

const ProtectedRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { user, loading, token } = useAuth();

  if (loading) {
    return (
      <div className="h-screen w-screen flex items-center justify-center bg-slate-50 font-sans">
        <div className="text-center space-y-3">
          <div className="w-10 h-10 border-4 border-blue-600 border-t-transparent rounded-full animate-spin mx-auto"></div>
          <p className="text-xs font-semibold text-slate-500">Loading TalentMatch AI...</p>
        </div>
      </div>
    );
  }

  // If unauthenticated, redirect to login
  if (!token && !user) {
    return <Navigate to="/login" replace />;
  }

  return <ErrorBoundary fallbackTitle="Workspace Interface Error">{children}</ErrorBoundary>;
};

export const App: React.FC = () => {
  return (
    <ErrorBoundary fallbackTitle="Application Error Boundary">
      <AuthProvider>
        <BrowserRouter>
          <Suspense fallback={<PageLoadingFallback />}>
            <Routes>
              {/* Public Authentication */}
              <Route path="/login" element={<LoginPage />} />
              <Route path="/register" element={<RegisterPage />} />

              {/* Protected Recruiter Workspace */}
              <Route
                path="/"
                element={
                  <ProtectedRoute>
                    <DashboardLayout />
                  </ProtectedRoute>
                }
              >
                <Route index element={<DashboardPage />} />
                <Route path="resumes/upload" element={<ResumeUploadPage />} />
                <Route path="matching" element={<AIMatchingPage />} />
                <Route path="candidates" element={<CandidatesPage />} />
                <Route path="ranking" element={<CandidateRankingPage />} />
                <Route path="shortlist" element={<ShortlistPage />} />
                <Route path="analytics" element={<AnalyticsPage />} />
                <Route path="history" element={<AnalysisHistoryPage />} />
                <Route path="agent-activity" element={<AgentActivityPage />} />
                <Route path="profile" element={<ProfilePage />} />
                <Route path="settings" element={<SettingsPage />} />
                <Route path="security" element={<SecurityPage />} />
              </Route>

              {/* Fallback */}
              <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
          </Suspense>
        </BrowserRouter>
      </AuthProvider>
    </ErrorBoundary>
  );
};

export default App;
