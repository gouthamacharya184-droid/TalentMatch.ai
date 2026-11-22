import React, { useState, useEffect } from 'react';
import { NavLink, Outlet, useNavigate } from 'react-router-dom';
import {
  LayoutDashboard,
  UploadCloud,
  Cpu,
  Users,
  Trophy,
  BookmarkCheck,
  BarChart3,
  History,
  UserCircle,
  Settings,
  ShieldCheck,
  LogOut,
  Bell,
  Search,
  Menu,
  X,
  Sparkles,
  WifiOff,
  Activity
} from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { notificationsApi } from '../services/api';
import type { Notification } from '../types';
import { ChatbotWidget } from '../components/ChatbotWidget';
import { ErrorBoundary } from '../components/ErrorBoundary';

export const DashboardLayout: React.FC = () => {
  const { user, logout, isOffline, checkBackendHealth } = useAuth();
  const navigate = useNavigate();
  const [mobileOpen, setMobileOpen] = useState(false);
  const [notifOpen, setNotifOpen] = useState(false);
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [unreadCount, setUnreadCount] = useState(0);

  const fetchNotifications = async () => {
    try {
      const res = await notificationsApi.getNotifications({ limit: 5 });
      setNotifications(res.items);
      const countRes = await notificationsApi.getUnreadCount();
      setUnreadCount(countRes.count);
    } catch {
      // gracefully ignore if offline
    }
  };

  useEffect(() => {
    fetchNotifications();
    const interval = setInterval(fetchNotifications, 15000);
    return () => clearInterval(interval);
  }, []);

  const handleMarkAllRead = async () => {
    try {
      await notificationsApi.markAllRead();
      setUnreadCount(0);
      setNotifications((prev) => prev.map((n) => ({ ...n, is_read: true })));
    } catch (e) {
      console.error(e);
    }
  };

  const handleLogout = () => {
    logout();
    navigate('/login');
  };

  const navClass = ({ isActive }: { isActive: boolean }) =>
    `flex items-center gap-3 px-3.5 py-2.5 rounded-lg text-sm font-medium transition-colors ${
      isActive
        ? 'bg-blue-600 text-white shadow-sm shadow-blue-500/20'
        : 'text-slate-600 hover:text-blue-600 hover:bg-blue-50/70'
    }`;

  return (
    <div className="flex h-screen bg-slate-50 overflow-hidden font-sans">
      {/* ── Sidebar (Desktop) ─────────────────────────────────── */}
      <aside className="hidden lg:flex lg:flex-col w-64 bg-white border-r border-slate-200 shrink-0">
        {/* Brand */}
        <div className="h-16 flex items-center gap-3 px-6 border-b border-slate-100">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-blue-700 to-blue-500 flex items-center justify-center text-white shadow-md shadow-blue-500/30">
            <Sparkles className="w-5 h-5" />
          </div>
          <div>
            <span className="font-bold text-lg text-slate-900 tracking-tight">TalentMatch</span>
            <span className="text-xs font-semibold uppercase ml-1 px-1.5 py-0.5 rounded bg-blue-100 text-blue-700">AI</span>
          </div>
        </div>

        {/* Navigation Items */}
        <div className="flex-1 overflow-y-auto px-4 py-4 space-y-6">
          {/* Main Menu */}
          <div>
            <p className="px-3 text-[11px] font-semibold text-slate-400 uppercase tracking-wider mb-2">
              Main Menu
            </p>
            <nav className="space-y-1">
              <NavLink to="/" end className={navClass}>
                <LayoutDashboard className="w-4 h-4" />
                <span>Dashboard</span>
              </NavLink>
              <NavLink to="/resumes/upload" className={navClass}>
                <UploadCloud className="w-4 h-4" />
                <span>Resume Upload</span>
              </NavLink>
              <NavLink to="/matching" className={navClass}>
                <Cpu className="w-4 h-4" />
                <span>AI Matching</span>
              </NavLink>
              <NavLink to="/candidates" className={navClass}>
                <Users className="w-4 h-4" />
                <span>Candidates</span>
              </NavLink>
              <NavLink to="/ranking" className={navClass}>
                <Trophy className="w-4 h-4" />
                <span>Candidate Ranking</span>
              </NavLink>
              <NavLink to="/shortlist" className={navClass}>
                <BookmarkCheck className="w-4 h-4" />
                <span>Shortlisted</span>
              </NavLink>
            </nav>
          </div>

          {/* Reports */}
          <div>
            <p className="px-3 text-[11px] font-semibold text-slate-400 uppercase tracking-wider mb-2">
              Reports & Audit
            </p>
            <nav className="space-y-1">
              <NavLink to="/analytics" className={navClass}>
                <BarChart3 className="w-4 h-4" />
                <span>Analytics & Reports</span>
              </NavLink>
              <NavLink to="/history" className={navClass}>
                <History className="w-4 h-4" />
                <span>Analysis History</span>
              </NavLink>
              <NavLink to="/agent-activity" className={navClass}>
                <Activity className="w-4 h-4" />
                <span>Agent Observability</span>
              </NavLink>
            </nav>
          </div>

          {/* Account */}
          <div>
            <p className="px-3 text-[11px] font-semibold text-slate-400 uppercase tracking-wider mb-2">
              Account
            </p>
            <nav className="space-y-1">
              <NavLink to="/profile" className={navClass}>
                <UserCircle className="w-4 h-4" />
                <span>User Profile</span>
              </NavLink>
              <NavLink to="/settings" className={navClass}>
                <Settings className="w-4 h-4" />
                <span>Settings</span>
              </NavLink>
              <NavLink to="/security" className={navClass}>
                <ShieldCheck className="w-4 h-4" />
                <span>Security & Privacy</span>
              </NavLink>
              <button
                onClick={handleLogout}
                className="w-full flex items-center gap-3 px-3.5 py-2.5 rounded-lg text-sm font-medium text-rose-600 hover:bg-rose-50/70 transition-colors"
              >
                <LogOut className="w-4 h-4" />
                <span>Logout</span>
              </button>
            </nav>
          </div>
        </div>

        {/* User Card */}
        <div className="p-4 border-t border-slate-100 flex items-center gap-3">
          <div className="w-9 h-9 rounded-full bg-blue-100 text-blue-700 font-semibold flex items-center justify-center text-sm">
            {user?.full_name ? user.full_name.charAt(0).toUpperCase() : 'R'}
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-sm font-semibold text-slate-900 truncate">
              {user?.full_name || 'Recruiter'}
            </p>
            <p className="text-xs text-slate-500 capitalize truncate">
              {user?.role?.replace('_', ' ') || 'Recruiter'}
            </p>
          </div>
        </div>
      </aside>

      {/* ── Main Content Area ─────────────────────────────────── */}
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        {/* Top Header */}
        <header className="h-16 bg-white border-b border-slate-200 px-6 flex items-center justify-between shrink-0">
          <div className="flex items-center gap-4">
            <button
              onClick={() => setMobileOpen(!mobileOpen)}
              className="lg:hidden p-2 text-slate-600 hover:text-slate-900 rounded-lg hover:bg-slate-100"
            >
              <Menu className="w-5 h-5" />
            </button>
            <div className="hidden sm:flex items-center gap-2 px-3 py-1.5 rounded-lg bg-slate-100/80 text-slate-500 text-sm w-72">
              <Search className="w-4 h-4 text-slate-400" />
              <input
                type="text"
                placeholder="Search candidates, jobs..."
                className="bg-transparent border-none outline-none text-slate-800 placeholder-slate-400 w-full text-xs"
              />
            </div>
          </div>

          <div className="flex items-center gap-4">
            {/* Notifications Dropdown */}
            <div className="relative">
              <button
                onClick={() => setNotifOpen(!notifOpen)}
                className="relative p-2 text-slate-600 hover:text-blue-600 hover:bg-slate-100 rounded-lg transition-colors"
              >
                <Bell className="w-5 h-5" />
                {unreadCount > 0 && (
                  <span className="absolute top-1 right-1 w-4 h-4 bg-blue-600 text-white rounded-full text-[10px] font-bold flex items-center justify-center">
                    {unreadCount}
                  </span>
                )}
              </button>

              {notifOpen && (
                <div className="absolute right-0 mt-2 w-80 bg-white rounded-xl shadow-xl border border-slate-200 py-2 z-50">
                  <div className="px-4 py-2 border-b border-slate-100 flex items-center justify-between">
                    <span className="text-sm font-semibold text-slate-900">Notifications</span>
                    <button
                      onClick={handleMarkAllRead}
                      className="text-xs text-blue-600 hover:underline font-medium"
                    >
                      Mark all as read
                    </button>
                  </div>
                  <div className="max-h-72 overflow-y-auto divide-y divide-slate-100">
                    {notifications.length === 0 ? (
                      <div className="p-4 text-center text-xs text-slate-400">
                        No notifications yet.
                      </div>
                    ) : (
                      notifications.map((n) => (
                        <div
                          key={n.id}
                          className={`p-3 text-xs transition-colors ${
                            n.is_read ? 'bg-white' : 'bg-blue-50/50'
                          }`}
                        >
                          <p className="font-semibold text-slate-800">{n.title}</p>
                          <p className="text-slate-500 mt-0.5">{n.message}</p>
                          <span className="text-[10px] text-slate-400 mt-1 block">
                            {new Date(n.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                          </span>
                        </div>
                      ))
                    )}
                  </div>
                </div>
              )}
            </div>

            {/* Recruiter Avatar */}
            <div
              onClick={() => navigate('/profile')}
              className="flex items-center gap-2.5 cursor-pointer pl-2 border-l border-slate-200"
            >
              <div className="w-8 h-8 rounded-full bg-gradient-to-tr from-blue-600 to-indigo-600 text-white font-medium flex items-center justify-center text-xs shadow-sm">
                {user?.full_name ? user.full_name.charAt(0).toUpperCase() : 'R'}
              </div>
              <div className="hidden sm:block text-left">
                <p className="text-xs font-semibold text-slate-900 leading-tight">
                  {user?.full_name || 'Recruiter'}
                </p>
                <p className="text-[11px] text-slate-400 leading-tight">AVOM Recruiter</p>
              </div>
            </div>
          </div>
        </header>

        {/* Page Body */}
        <main className="flex-1 overflow-y-auto p-6 md:p-8">
          {isOffline && (
            <div className="mb-4 p-3 bg-amber-50 border border-amber-200 rounded-2xl text-xs text-amber-800 flex items-center justify-between shadow-sm">
              <div className="flex items-center gap-2">
                <WifiOff className="w-4 h-4 text-amber-600 shrink-0" />
                <span>
                  Backend API is currently unreachable. Operating in preview mode.
                </span>
              </div>
              <button
                onClick={() => checkBackendHealth()}
                className="px-2.5 py-1 rounded-lg bg-amber-200 text-amber-900 font-semibold hover:bg-amber-300 transition-colors cursor-pointer"
              >
                Retry Connection
              </button>
            </div>
          )}
          <ErrorBoundary fallbackTitle="Module Interface Error">
            <Outlet />
          </ErrorBoundary>
        </main>
      </div>

      {/* ── Mobile Sidebar Overlay ────────────────────────────── */}
      {mobileOpen && (
        <div className="fixed inset-0 z-50 flex lg:hidden">
          <div
            className="fixed inset-0 bg-slate-900/40 backdrop-blur-sm"
            onClick={() => setMobileOpen(false)}
          ></div>
          <div className="relative w-64 bg-white flex flex-col h-full shadow-2xl z-10">
            <div className="h-16 flex items-center justify-between px-6 border-b border-slate-100">
              <span className="font-bold text-slate-900">TalentMatch AI</span>
              <button onClick={() => setMobileOpen(false)}>
                <X className="w-5 h-5 text-slate-400" />
              </button>
            </div>
            <div className="flex-1 overflow-y-auto p-4 space-y-4" onClick={() => setMobileOpen(false)}>
              <NavLink to="/" end className={navClass}>
                <LayoutDashboard className="w-4 h-4" />
                <span>Dashboard</span>
              </NavLink>
              <NavLink to="/resumes/upload" className={navClass}>
                <UploadCloud className="w-4 h-4" />
                <span>Resume Upload</span>
              </NavLink>
              <NavLink to="/matching" className={navClass}>
                <Cpu className="w-4 h-4" />
                <span>AI Matching</span>
              </NavLink>
              <NavLink to="/candidates" className={navClass}>
                <Users className="w-4 h-4" />
                <span>Candidates</span>
              </NavLink>
              <NavLink to="/ranking" className={navClass}>
                <Trophy className="w-4 h-4" />
                <span>Candidate Ranking</span>
              </NavLink>
              <NavLink to="/shortlist" className={navClass}>
                <BookmarkCheck className="w-4 h-4" />
                <span>Shortlisted</span>
              </NavLink>
              <NavLink to="/analytics" className={navClass}>
                <BarChart3 className="w-4 h-4" />
                <span>Analytics</span>
              </NavLink>
              <NavLink to="/history" className={navClass}>
                <History className="w-4 h-4" />
                <span>History</span>
              </NavLink>
              <NavLink to="/agent-activity" className={navClass}>
                <Activity className="w-4 h-4" />
                <span>Agent Activity</span>
              </NavLink>
              <NavLink to="/profile" className={navClass}>
                <UserCircle className="w-4 h-4" />
                <span>Profile</span>
              </NavLink>
              <NavLink to="/settings" className={navClass}>
                <Settings className="w-4 h-4" />
                <span>Settings</span>
              </NavLink>
              <NavLink to="/security" className={navClass}>
                <ShieldCheck className="w-4 h-4" />
                <span>Security</span>
              </NavLink>
            </div>
          </div>
        </div>
      )}
      {/* AI Chatbot Floating Copilot */}
      <ChatbotWidget />
    </div>
  );
};
