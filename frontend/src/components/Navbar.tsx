import React, { useState, useEffect } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { engagementApi } from '../services/api';
import { NotificationItem } from '../types';
import {
  HeartPulse,
  Activity,
  Layers,
  LogOut,
  Bell,
  Calendar,
  Stethoscope,
  ShieldCheck,
} from 'lucide-react';

export const Navbar: React.FC = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const { user, role, isAuthenticated, logout } = useAuth();
  const [notifications, setNotifications] = useState<NotificationItem[]>([]);
  const [showNotifs, setShowNotifs] = useState<boolean>(false);

  useEffect(() => {
    if (isAuthenticated) {
      engagementApi.listNotifications().then(setNotifications).catch(() => {});
    }
  }, [isAuthenticated]);

  return (
    <header className="sticky top-0 z-50 bg-white/95 backdrop-blur-md border-b border-slate-200">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-16 items-center">
          {/* Brand */}
          <Link to="/" className="flex items-center gap-3 group">
            <div className="w-10 h-10 rounded-2xl bg-teal-600 flex items-center justify-center text-white shadow-md shadow-teal-500/20 group-hover:scale-105 transition-transform">
              <HeartPulse className="w-6 h-6" />
            </div>
            <div>
              <span className="font-black text-slate-900 text-base tracking-tight block">HealthPulse</span>
              <span className="text-[10px] text-teal-700 font-bold uppercase tracking-wider">Clinical Coordination</span>
            </div>
          </Link>

          {/* Navigation Links */}
          <nav className="hidden md:flex items-center gap-1">
            <Link
              to="/"
              className={`flex items-center gap-1.5 px-3 py-2 rounded-xl text-xs font-bold transition-colors ${
                location.pathname === '/' ? 'bg-teal-50 text-teal-700' : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              Overview
            </Link>

            {isAuthenticated && role === 'PATIENT' && (
              <Link
                to="/patient"
                className={`flex items-center gap-1.5 px-3 py-2 rounded-xl text-xs font-bold transition-colors ${
                  location.pathname === '/patient' ? 'bg-teal-50 text-teal-700' : 'text-slate-600 hover:text-slate-900'
                }`}
              >
                <Calendar className="w-3.5 h-3.5" />
                Patient Portal
              </Link>
            )}

            {isAuthenticated && role === 'DOCTOR' && (
              <Link
                to="/doctor"
                className={`flex items-center gap-1.5 px-3 py-2 rounded-xl text-xs font-bold transition-colors ${
                  location.pathname === '/doctor' ? 'bg-teal-50 text-teal-700' : 'text-slate-600 hover:text-slate-900'
                }`}
              >
                <Stethoscope className="w-3.5 h-3.5" />
                Doctor Workspace
              </Link>
            )}

            {isAuthenticated && role === 'ADMIN' && (
              <Link
                to="/admin"
                className={`flex items-center gap-1.5 px-3 py-2 rounded-xl text-xs font-bold transition-colors ${
                  location.pathname === '/admin' ? 'bg-teal-50 text-teal-700' : 'text-slate-600 hover:text-slate-900'
                }`}
              >
                <ShieldCheck className="w-3.5 h-3.5" />
                Admin Center
              </Link>
            )}

            <Link
              to="/health"
              className={`flex items-center gap-1.5 px-3 py-2 rounded-xl text-xs font-bold transition-colors ${
                location.pathname === '/health' ? 'bg-teal-50 text-teal-700' : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              <Activity className="w-3.5 h-3.5" />
              Diagnostics
            </Link>

            <Link
              to="/architecture"
              className={`flex items-center gap-1.5 px-3 py-2 rounded-xl text-xs font-bold transition-colors ${
                location.pathname === '/architecture' ? 'bg-teal-50 text-teal-700' : 'text-slate-600 hover:text-slate-900'
              }`}
            >
              <Layers className="w-3.5 h-3.5" />
              Architecture
            </Link>
          </nav>

          {/* Right Action Items: Notifications & Auth State */}
          <div className="flex items-center gap-3">
            {isAuthenticated ? (
              <div className="flex items-center gap-3">
                {/* Notifications Button */}
                <div className="relative">
                  <button
                    onClick={() => setShowNotifs(!showNotifs)}
                    className="p-2 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-700 relative"
                  >
                    <Bell className="w-4 h-4" />
                    {notifications.length > 0 && (
                      <span className="absolute -top-1 -right-1 w-4 h-4 bg-teal-600 text-white rounded-full text-[9px] font-black flex items-center justify-center">
                        {notifications.length}
                      </span>
                    )}
                  </button>

                  {/* Dropdown */}
                  {showNotifs && (
                    <div className="absolute right-0 mt-2 w-80 bg-white rounded-2xl shadow-xl border border-slate-200 p-4 space-y-3 z-50">
                      <div className="flex items-center justify-between border-b border-slate-100 pb-2">
                        <span className="font-extrabold text-xs text-slate-900">In-App Notifications</span>
                        <button onClick={() => setShowNotifs(false)} className="text-slate-400 text-xs font-bold">✕</button>
                      </div>
                      {notifications.length === 0 ? (
                        <p className="text-xs text-slate-400 py-3 text-center">No new notifications.</p>
                      ) : (
                        <div className="space-y-2 max-h-60 overflow-y-auto">
                          {notifications.map((n) => (
                            <div key={n.id} className="p-2.5 bg-slate-50 rounded-xl text-xs space-y-1">
                              <span className="font-bold text-slate-800 block">{n.title}</span>
                              <p className="text-slate-600 text-[11px]">{n.body}</p>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  )}
                </div>

                {/* User Pill */}
                <div className="flex items-center gap-2 pl-2 border-l border-slate-200">
                  <div className="text-right">
                    <span className="block text-xs font-bold text-slate-900 leading-tight">{user?.name}</span>
                    <span className="text-[10px] font-black text-teal-600 uppercase tracking-wider">{role}</span>
                  </div>
                  <button
                    onClick={() => {
                      logout();
                      navigate('/login');
                    }}
                    title="Sign out"
                    className="p-2 text-slate-400 hover:text-rose-600 rounded-xl hover:bg-rose-50 transition-colors"
                  >
                    <LogOut className="w-4 h-4" />
                  </button>
                </div>
              </div>
            ) : (
              <div className="flex items-center gap-2">
                <Link
                  to="/login"
                  className="px-4 py-2 text-xs font-bold text-slate-700 hover:text-slate-900 hover:bg-slate-100 rounded-xl transition-colors"
                >
                  Sign In
                </Link>
                <Link
                  to="/register"
                  className="px-4 py-2 text-xs font-bold bg-teal-600 hover:bg-teal-700 text-white rounded-xl shadow-sm transition-all"
                >
                  Get Started
                </Link>
              </div>
            )}
          </div>
        </div>
      </div>
    </header>
  );
};
