import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import { DashboardLayout } from './layouts/DashboardLayout';
import { ErrorBoundary } from './components/ErrorBoundary';

// Pages
import { DashboardPage } from './pages/DashboardPage';
import { JobsPage } from './pages/JobsPage';
import { ResumeUploadPage } from './pages/ResumeUploadPage';
import { AIMatchingPage } from './pages/AIMatchingPage';
import { CandidatesPage } from './pages/CandidatesPage';
import { CandidateRankingPage } from './pages/CandidateRankingPage';
import { CompareCandidatesPage } from './pages/CompareCandidatesPage';
import { ShortlistPage } from './pages/ShortlistPage';
import { AnalyticsPage } from './pages/AnalyticsPage';
import { AnalysisHistoryPage } from './pages/AnalysisHistoryPage';
import { ProfilePage } from './pages/ProfilePage';
import { SettingsPage } from './pages/SettingsPage';
import { SecurityPage } from './pages/SecurityPage';
import { LoginPage } from './pages/LoginPage';
import { RegisterPage } from './pages/RegisterPage';
import { CampaignsPage } from './pages/CampaignsPage';
import { InterviewIntelligencePage } from './pages/InterviewIntelligencePage';
import { AgentActivityPage } from './pages/AgentActivityPage';

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
              <Route path="campaigns" element={<CampaignsPage />} />
              <Route path="jobs" element={<JobsPage />} />
              <Route path="resumes/upload" element={<ResumeUploadPage />} />
              <Route path="matching" element={<AIMatchingPage />} />
              <Route path="candidates" element={<CandidatesPage />} />
              <Route path="ranking" element={<CandidateRankingPage />} />
              <Route path="compare" element={<CompareCandidatesPage />} />
              <Route path="shortlist" element={<ShortlistPage />} />
              <Route path="interview-kits" element={<InterviewIntelligencePage />} />
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
        </BrowserRouter>
      </AuthProvider>
    </ErrorBoundary>
  );
};

export default App;
