import React from 'react';
import { ShieldCheck, Cpu, Database, Server } from 'lucide-react';

export const Footer: React.FC = () => {
  return (
    <footer className="bg-slate-900 text-slate-400 border-t border-slate-800 py-10 mt-auto">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-8 mb-8">
          <div className="col-span-1 md:col-span-2">
            <div className="flex items-center gap-2 text-white font-bold text-lg mb-2">
              <ShieldCheck className="w-5 h-5 text-brand-400" />
              Healthcare Appointment & Follow-up Manager
            </div>
            <p className="text-sm text-slate-400 max-w-md">
              Designed for mission-critical healthcare workflows with database-level race condition prevention, AI clinical assistance, and resilient background queues.
            </p>
          </div>
          <div>
            <h4 className="text-white text-sm font-semibold mb-3 tracking-wider uppercase">Architecture</h4>
            <ul className="text-sm space-y-2">
              <li className="flex items-center gap-2"><Server className="w-3.5 h-3.5 text-brand-400" /> FastAPI + AsyncPG</li>
              <li className="flex items-center gap-2"><Database className="w-3.5 h-3.5 text-brand-400" /> PostgreSQL + btree_gist</li>
              <li className="flex items-center gap-2"><Cpu className="w-3.5 h-3.5 text-brand-400" /> Redis + Celery</li>
            </ul>
          </div>
          <div>
            <h4 className="text-white text-sm font-semibold mb-3 tracking-wider uppercase">Project Status</h4>
            <div className="text-sm text-slate-400 space-y-1">
              <p>Current: <span className="text-emerald-400 font-medium">Foundation Setup</span></p>
              <p>Ready for: <span className="text-slate-300">Phase 2 (Auth & Core Models)</span></p>
            </div>
          </div>
        </div>
        <div className="pt-6 border-t border-slate-800 text-xs text-slate-500 flex flex-col sm:flex-row justify-between items-center gap-4">
          <p>© 2026 Healthcare Appointment & Follow-up Manager. All rights reserved.</p>
          <p>Production Ready Full-Stack Blueprint</p>
        </div>
      </div>
    </footer>
  );
};
