import React, { useState, useEffect } from 'react';
import { api } from '../services/api';
import { HealthResponse } from '../types';
import { 
  Database, 
  Cpu, 
  Server, 
  RefreshCw, 
  CheckCircle2, 
  AlertTriangle, 
  XCircle, 
  Clock, 
  ShieldAlert
} from 'lucide-react';

export const HealthStatusPage: React.FC = () => {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const [lastChecked, setLastChecked] = useState<Date | null>(null);

  const fetchHealth = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.getHealth();
      setHealth(data);
      setLastChecked(new Date());
    } catch (err: any) {
      setError(err.message || 'Failed to connect to backend service.');
      setHealth(null);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchHealth();
    const interval = setInterval(fetchHealth, 15000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-8">
        <div>
          <div className="flex items-center gap-2.5">
            <h1 className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight">
              Live System Diagnostics
            </h1>
            <span className="flex h-3 w-3 relative">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-3 w-3 bg-emerald-500"></span>
            </span>
          </div>
          <p className="text-slate-600 mt-1 text-sm sm:text-base">
            Real-time connectivity and latency telemetry for FastAPI backend, PostgreSQL 16, and Redis 7.
          </p>
        </div>

        <button
          onClick={fetchHealth}
          disabled={loading}
          className="inline-flex items-center gap-2 px-4 py-2 bg-brand-600 hover:bg-brand-700 active:bg-brand-800 disabled:opacity-50 text-white text-sm font-semibold rounded-lg shadow-sm transition-all self-start md:self-auto"
        >
          <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
          {loading ? 'Testing...' : 'Refresh Status'}
        </button>
      </div>

      {/* Global Status Banner */}
      {error ? (
        <div className="mb-8 p-5 bg-rose-50 border border-rose-200 rounded-2xl flex items-start gap-4 shadow-sm">
          <XCircle className="w-6 h-6 text-rose-600 flex-shrink-0 mt-0.5" />
          <div className="flex-1">
            <h3 className="text-rose-900 font-bold text-base">Backend Service Unreachable</h3>
            <p className="text-rose-700 text-sm mt-1">{error}</p>
            <p className="text-rose-600 text-xs mt-2">
              Tip: Ensure the backend is running on <code className="bg-rose-100 px-1 py-0.5 rounded font-mono">http://localhost:8000</code> or Docker containers are active.
            </p>
          </div>
        </div>
      ) : health ? (
        <div className={`mb-8 p-5 rounded-2xl border flex items-center justify-between gap-4 shadow-sm ${
          health.status === 'healthy' 
            ? 'bg-emerald-50/80 border-emerald-200 text-emerald-950' 
            : 'bg-amber-50/80 border-amber-200 text-amber-950'
        }`}>
          <div className="flex items-center gap-3.5">
            {health.status === 'healthy' ? (
              <CheckCircle2 className="w-7 h-7 text-emerald-600 flex-shrink-0" />
            ) : (
              <AlertTriangle className="w-7 h-7 text-amber-600 flex-shrink-0" />
            )}
            <div>
              <div className="flex items-center gap-2">
                <h3 className="font-bold text-base sm:text-lg">
                  System Operational Status: {health.status.toUpperCase()}
                </h3>
              </div>
              <p className="text-xs sm:text-sm text-slate-600 mt-0.5">
                Service: <span className="font-semibold text-slate-800">{health.service}</span> • Environment: <span className="font-mono bg-slate-200/70 px-1.5 py-0.5 rounded text-xs">{health.environment}</span> • Version: <span className="font-semibold">{health.version}</span>
              </p>
            </div>
          </div>
          {lastChecked && (
            <div className="hidden sm:flex items-center gap-1.5 text-xs text-slate-500">
              <Clock className="w-3.5 h-3.5" />
              <span>Checked {lastChecked.toLocaleTimeString()}</span>
            </div>
          )}
        </div>
      ) : null}

      {/* Services Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-10">
        {/* Backend API Card */}
        <div className="bg-white border border-slate-200 rounded-2xl p-6 shadow-sm hover:shadow transition-shadow">
          <div className="flex items-center justify-between mb-4">
            <div className="w-12 h-12 rounded-xl bg-brand-50 text-brand-600 flex items-center justify-center">
              <Server className="w-6 h-6" />
            </div>
            {health ? (
              <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200">
                <CheckCircle2 className="w-3.5 h-3.5" /> Active
              </span>
            ) : (
              <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-rose-50 text-rose-700 border border-rose-200">
                <XCircle className="w-3.5 h-3.5" /> Offline
              </span>
            )}
          </div>
          <h3 className="text-lg font-bold text-slate-900">FastAPI Core API</h3>
          <p className="text-xs text-slate-500 mt-1 mb-4">Asynchronous Python ASGI Engine (Uvicorn)</p>
          <div className="border-t border-slate-100 pt-3 space-y-2 text-xs">
            <div className="flex justify-between">
              <span className="text-slate-500">Endpoint:</span>
              <span className="font-mono text-slate-700">/api/health</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-500">Docs (Swagger):</span>
              <a href="http://localhost:8000/docs" target="_blank" rel="noreferrer" className="text-brand-600 hover:underline">/docs</a>
            </div>
          </div>
        </div>

        {/* PostgreSQL Database Card */}
        <div className="bg-white border border-slate-200 rounded-2xl p-6 shadow-sm hover:shadow transition-shadow">
          <div className="flex items-center justify-between mb-4">
            <div className="w-12 h-12 rounded-xl bg-blue-50 text-blue-600 flex items-center justify-center">
              <Database className="w-6 h-6" />
            </div>
            {health?.services.database.status === 'connected' ? (
              <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200">
                <CheckCircle2 className="w-3.5 h-3.5" /> Connected
              </span>
            ) : (
              <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-amber-50 text-amber-700 border border-amber-200">
                <AlertTriangle className="w-3.5 h-3.5" /> Standby
              </span>
            )}
          </div>
          <h3 className="text-lg font-bold text-slate-900">PostgreSQL 16</h3>
          <p className="text-xs text-slate-500 mt-1 mb-4">Primary Relational Storage + btree_gist</p>
          <div className="border-t border-slate-100 pt-3 space-y-2 text-xs">
            <div className="flex justify-between">
              <span className="text-slate-500">Driver:</span>
              <span className="font-mono text-slate-700">AsyncPG / SQLAlchemy 2.0</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-500">Latency:</span>
              <span className="font-semibold text-slate-800">
                {health?.services.database.latency_ms !== undefined ? `${health.services.database.latency_ms} ms` : 'N/A'}
              </span>
            </div>
            {health?.services.database.error && (
              <div className="text-rose-600 text-[11px] truncate" title={health.services.database.error}>
                Error: {health.services.database.error}
              </div>
            )}
          </div>
        </div>

        {/* Redis Cache & Broker Card */}
        <div className="bg-white border border-slate-200 rounded-2xl p-6 shadow-sm hover:shadow transition-shadow">
          <div className="flex items-center justify-between mb-4">
            <div className="w-12 h-12 rounded-xl bg-red-50 text-red-600 flex items-center justify-center">
              <Cpu className="w-6 h-6" />
            </div>
            {health?.services.redis.status === 'connected' ? (
              <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200">
                <CheckCircle2 className="w-3.5 h-3.5" /> Connected
              </span>
            ) : (
              <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-semibold bg-amber-50 text-amber-700 border border-amber-200">
                <AlertTriangle className="w-3.5 h-3.5" /> Standby
              </span>
            )}
          </div>
          <h3 className="text-lg font-bold text-slate-900">Redis 7</h3>
          <p className="text-xs text-slate-500 mt-1 mb-4">In-Memory Cache & Celery Task Broker</p>
          <div className="border-t border-slate-100 pt-3 space-y-2 text-xs">
            <div className="flex justify-between">
              <span className="text-slate-500">Role:</span>
              <span className="font-mono text-slate-700">Slot Holds & Task Queue</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-500">Latency:</span>
              <span className="font-semibold text-slate-800">
                {health?.services.redis.latency_ms !== undefined ? `${health.services.redis.latency_ms} ms` : 'N/A'}
              </span>
            </div>
            {health?.services.redis.error && (
              <div className="text-rose-600 text-[11px] truncate" title={health.services.redis.error}>
                Error: {health.services.redis.error}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Architecture Readiness Box */}
      <div className="bg-slate-900 text-white rounded-2xl p-6 sm:p-8">
        <div className="flex items-center gap-3 mb-4">
          <ShieldAlert className="w-6 h-6 text-brand-400" />
          <h2 className="text-lg font-bold">Phase 1 Foundation Checklist</h2>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 text-sm">
          <div className="bg-slate-800/80 p-4 rounded-xl border border-slate-700">
            <div className="text-emerald-400 font-semibold mb-1 flex items-center gap-1.5">
              <CheckCircle2 className="w-4 h-4" /> Docker Architecture
            </div>
            <p className="text-xs text-slate-300">Docker compose configured for Frontend, Backend, PG 16, Redis 7 & Celery.</p>
          </div>
          <div className="bg-slate-800/80 p-4 rounded-xl border border-slate-700">
            <div className="text-emerald-400 font-semibold mb-1 flex items-center gap-1.5">
              <CheckCircle2 className="w-4 h-4" /> Concurrency Guard
            </div>
            <p className="text-xs text-slate-300">Pessimistic locking and exclusion constraint schema designed.</p>
          </div>
          <div className="bg-slate-800/80 p-4 rounded-xl border border-slate-700">
            <div className="text-emerald-400 font-semibold mb-1 flex items-center gap-1.5">
              <CheckCircle2 className="w-4 h-4" /> Resilient AI Flow
            </div>
            <p className="text-xs text-slate-300">Non-blocking symptom & post-visit LLM summary pipeline architected.</p>
          </div>
          <div className="bg-slate-800/80 p-4 rounded-xl border border-slate-700">
            <div className="text-emerald-400 font-semibold mb-1 flex items-center gap-1.5">
              <CheckCircle2 className="w-4 h-4" /> Outbox Queue
            </div>
            <p className="text-xs text-slate-300">Async Celery notifications and calendar syncing architecture specified.</p>
          </div>
        </div>
      </div>
    </div>
  );
};
