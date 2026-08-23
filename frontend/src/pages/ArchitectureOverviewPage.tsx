import { Database, Layers, ArrowRight } from 'lucide-react';
import { Link } from 'react-router-dom';

export const ArchitectureOverviewPage: React.FC = () => {
  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
      <div className="mb-10">
        <h1 className="text-3xl font-extrabold text-slate-900 tracking-tight">System Architecture & Design Blueprint</h1>
        <p className="text-slate-600 mt-2 text-base max-w-3xl">
          Complete breakdown of the technical stack, database tables, concurrency guards, and deployment patterns planned for production.
        </p>
      </div>

      {/* Tech Stack Matrix */}
      <div className="bg-white border border-slate-200 rounded-2xl p-6 sm:p-8 shadow-sm mb-10">
        <h2 className="text-xl font-bold text-slate-900 mb-6 flex items-center gap-2">
          <Layers className="w-5 h-5 text-brand-600" />
          Full-Stack Technology Stack
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <div className="p-4 rounded-xl bg-slate-50 border border-slate-100">
            <span className="text-xs font-bold uppercase text-brand-700 tracking-wider">Frontend</span>
            <h3 className="text-base font-bold text-slate-900 mt-1">React + Vite + TS</h3>
            <p className="text-xs text-slate-500 mt-2">Tailwind CSS utility styling, Lucide icons, responsive SPA layout with React Router.</p>
          </div>
          <div className="p-4 rounded-xl bg-slate-50 border border-slate-100">
            <span className="text-xs font-bold uppercase text-blue-700 tracking-wider">Backend API</span>
            <h3 className="text-base font-bold text-slate-900 mt-1">FastAPI + AsyncPG</h3>
            <p className="text-xs text-slate-500 mt-2">Python 3.12+ async ASGI, Pydantic v2 validation, SQLAlchemy 2.0 async session pooling.</p>
          </div>
          <div className="p-4 rounded-xl bg-slate-50 border border-slate-100">
            <span className="text-xs font-bold uppercase text-indigo-700 tracking-wider">Database</span>
            <h3 className="text-base font-bold text-slate-900 mt-1">PostgreSQL 16</h3>
            <p className="text-xs text-slate-500 mt-2">Btree_gist exclusion constraints, ACID row locks, Alembic migration tracking.</p>
          </div>
          <div className="p-4 rounded-xl bg-slate-50 border border-slate-100">
            <span className="text-xs font-bold uppercase text-rose-700 tracking-wider">Queue & Broker</span>
            <h3 className="text-base font-bold text-slate-900 mt-1">Redis 7 + Celery</h3>
            <p className="text-xs text-slate-500 mt-2">Background job workers for emails, Google Calendar OAuth syncing, hold sweepers.</p>
          </div>
        </div>
      </div>

      {/* Database Tables Summary */}
      <div className="bg-white border border-slate-200 rounded-2xl p-6 sm:p-8 shadow-sm mb-10">
        <h2 className="text-xl font-bold text-slate-900 mb-6 flex items-center gap-2">
          <Database className="w-5 h-5 text-brand-600" />
          Planned PostgreSQL Schema
        </h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4 text-xs">
          {[
            { name: 'users', desc: 'Patients, Doctors, Admins authentication and role profiles.' },
            { name: 'doctor_profiles', desc: 'Specializations, slot durations, consultation fees, bio.' },
            { name: 'doctor_working_hours', desc: 'Weekly recurring day/time availability shifts.' },
            { name: 'doctor_leave', desc: 'Leave dates with cascade appointment rescheduling.' },
            { name: 'appointments', desc: 'Lifecycle states with PostgreSQL exclusion constraints.' },
            { name: 'slot_holds', desc: '10-minute temporary holds with auto-expiration timestamps.' },
            { name: 'clinical_notes', desc: 'Doctor post-visit notes and AI-generated summary approval.' },
            { name: 'prescriptions', desc: 'Structured medication dosages, frequency, and instructions.' },
            { name: 'medication_reminders', desc: 'Patient reminder preferences and dispatch logs.' },
            { name: 'calendar_events', desc: 'Google Calendar API OAuth 2.0 event IDs and sync status.' },
            { name: 'notifications', desc: 'Transactional outbox for reliable email delivery & retries.' }
          ].map((t) => (
            <div key={t.name} className="p-3.5 rounded-xl border border-slate-200 bg-slate-50/50">
              <code className="text-brand-700 font-bold font-mono text-sm">{t.name}</code>
              <p className="text-slate-600 mt-1.5 leading-relaxed">{t.desc}</p>
            </div>
          ))}
        </div>
      </div>

      {/* Docs Quick Reference */}
      <div className="bg-slate-900 text-white rounded-2xl p-6 sm:p-8 flex flex-col sm:flex-row items-center justify-between gap-6">
        <div>
          <h3 className="text-lg font-bold">Comprehensive Documentation Created</h3>
          <p className="text-slate-400 text-xs sm:text-sm mt-1">
            Detailed specifications are documented in <code className="text-teal-300 font-mono">docs/architecture.md</code>, <code className="text-teal-300 font-mono">docs/database-design.md</code>, and <code className="text-teal-300 font-mono">docs/api-design.md</code>.
          </p>
        </div>
        <Link
          to="/health"
          className="inline-flex items-center gap-2 px-5 py-2.5 bg-brand-600 hover:bg-brand-700 text-white font-semibold text-xs sm:text-sm rounded-xl shadow transition-colors flex-shrink-0"
        >
          Check System Status <ArrowRight className="w-4 h-4" />
        </Link>
      </div>
    </div>
  );
};
