import React from 'react';
import { Link } from 'react-router-dom';
import { 
  ShieldCheck, 
  Calendar, 
  Clock, 
  Activity, 
  Users, 
  Sparkles, 
  Stethoscope, 
  CheckCircle2, 
  ArrowRight,
  Database,
  Lock
} from 'lucide-react';

export const HomePage: React.FC = () => {
  return (
    <div className="space-y-16 pb-16">
      {/* Hero Section */}
      <section className="relative overflow-hidden bg-gradient-to-b from-brand-50/60 via-slate-50 to-slate-50 pt-16 pb-12 sm:pt-24 sm:pb-20 border-b border-slate-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center max-w-3xl mx-auto">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-semibold bg-brand-100 text-brand-800 mb-6 shadow-sm">
              <Sparkles className="w-3.5 h-3.5 text-brand-600" />
              <span>Full-Stack Foundation Established</span>
            </div>
            
            <h1 className="text-4xl sm:text-5xl lg:text-6xl font-black text-slate-900 tracking-tight leading-[1.15]">
              Healthcare Appointment & <span className="text-brand-600">Follow-up Manager</span>
            </h1>
            
            <p className="mt-6 text-base sm:text-lg text-slate-600 leading-relaxed">
              An enterprise-grade coordination system with database-level race condition prevention, doctor leave cascading, and AI-assisted clinical workflows.
            </p>

            <div className="mt-8 flex flex-wrap items-center justify-center gap-4">
              <Link
                to="/health"
                className="inline-flex items-center gap-2 px-6 py-3.5 rounded-xl bg-brand-600 hover:bg-brand-700 active:bg-brand-800 text-white font-semibold text-sm shadow-md shadow-brand-500/25 transition-all hover:scale-[1.02]"
              >
                <Activity className="w-4 h-4" />
                View Live Diagnostics
                <ArrowRight className="w-4 h-4" />
              </Link>
              <Link
                to="/architecture"
                className="inline-flex items-center gap-2 px-6 py-3.5 rounded-xl bg-white hover:bg-slate-50 text-slate-700 font-semibold text-sm border border-slate-200 shadow-sm transition-all"
              >
                <Database className="w-4 h-4 text-slate-500" />
                Explore Architecture Docs
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* 3 Core Roles Section */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center max-w-2xl mx-auto mb-12">
          <h2 className="text-2xl sm:text-3xl font-extrabold text-slate-900 tracking-tight">
            Designed for the Entire Healthcare Ecosystem
          </h2>
          <p className="text-slate-600 text-sm mt-2">
            Tailored workflows for Patients, Doctors, and Administrators with strict role-based authorization.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          {/* Patient Card */}
          <div className="bg-white border border-slate-200 rounded-2xl p-7 shadow-sm hover:shadow-md transition-shadow">
            <div className="w-12 h-12 rounded-xl bg-teal-50 text-teal-600 flex items-center justify-center mb-5">
              <Users className="w-6 h-6" />
            </div>
            <h3 className="text-xl font-bold text-slate-900 mb-2">Patient Experience</h3>
            <p className="text-sm text-slate-600 mb-5 leading-relaxed">
              Frictionless appointment discovery with temporary slot holds, pre-visit symptom entry, AI summaries, and automated medication reminders.
            </p>
            <ul className="space-y-2 text-xs text-slate-700 font-medium">
              <li className="flex items-center gap-2"><CheckCircle2 className="w-4 h-4 text-teal-600" /> Doctor search by specialization</li>
              <li className="flex items-center gap-2"><CheckCircle2 className="w-4 h-4 text-teal-600" /> 10-minute temporary slot holds</li>
              <li className="flex items-center gap-2"><CheckCircle2 className="w-4 h-4 text-teal-600" /> AI pre-visit triage questions</li>
              <li className="flex items-center gap-2"><CheckCircle2 className="w-4 h-4 text-teal-600" /> Post-visit summary & prescriptions</li>
            </ul>
          </div>

          {/* Doctor Card */}
          <div className="bg-white border border-slate-200 rounded-2xl p-7 shadow-sm hover:shadow-md transition-shadow">
            <div className="w-12 h-12 rounded-xl bg-blue-50 text-blue-600 flex items-center justify-center mb-5">
              <Stethoscope className="w-6 h-6" />
            </div>
            <h3 className="text-xl font-bold text-slate-900 mb-2">Doctor Workspace</h3>
            <p className="text-sm text-slate-600 mb-5 leading-relaxed">
              Schedule management, pre-visit symptom triage review, clinical note logging, prescription writing, and AI patient-summary generator.
            </p>
            <ul className="space-y-2 text-xs text-slate-700 font-medium">
              <li className="flex items-center gap-2"><CheckCircle2 className="w-4 h-4 text-blue-600" /> Working hours & slot duration config</li>
              <li className="flex items-center gap-2"><CheckCircle2 className="w-4 h-4 text-blue-600" /> Pre-appointment symptom overview</li>
              <li className="flex items-center gap-2"><CheckCircle2 className="w-4 h-4 text-blue-600" /> Clinical notes & prescription entry</li>
              <li className="flex items-center gap-2"><CheckCircle2 className="w-4 h-4 text-blue-600" /> Doctor review gate for AI summaries</li>
            </ul>
          </div>

          {/* Admin Card */}
          <div className="bg-white border border-slate-200 rounded-2xl p-7 shadow-sm hover:shadow-md transition-shadow">
            <div className="w-12 h-12 rounded-xl bg-purple-50 text-purple-600 flex items-center justify-center mb-5">
              <ShieldCheck className="w-6 h-6" />
            </div>
            <h3 className="text-xl font-bold text-slate-900 mb-2">Admin Command Center</h3>
            <p className="text-sm text-slate-600 mb-5 leading-relaxed">
              Doctor onboarding, profile updates, slot duration settings, and intelligent leave management with automatic appointment rescheduling cascades.
            </p>
            <ul className="space-y-2 text-xs text-slate-700 font-medium">
              <li className="flex items-center gap-2"><CheckCircle2 className="w-4 h-4 text-purple-600" /> Doctor profile & specialization mgmt</li>
              <li className="flex items-center gap-2"><CheckCircle2 className="w-4 h-4 text-purple-600" /> Shift & working hours configuration</li>
              <li className="flex items-center gap-2"><CheckCircle2 className="w-4 h-4 text-purple-600" /> Intelligent leave cascade handling</li>
              <li className="flex items-center gap-2"><CheckCircle2 className="w-4 h-4 text-purple-600" /> Clinic-wide appointment monitoring</li>
            </ul>
          </div>
        </div>
      </section>

      {/* Critical Business Rules Highlights */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="bg-slate-900 text-white rounded-3xl p-8 sm:p-12 shadow-xl">
          <div className="max-w-2xl mb-8">
            <h2 className="text-2xl sm:text-3xl font-extrabold tracking-tight mb-3">
              Built for Production Concurrency & Resilience
            </h2>
            <p className="text-slate-400 text-sm">
              Critical architecture decisions implemented from the foundation up.
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <div className="bg-slate-800/60 border border-slate-700 rounded-2xl p-6">
              <div className="flex items-center gap-3 mb-3">
                <Lock className="w-5 h-5 text-teal-400" />
                <h4 className="font-bold text-base">Zero Double-Booking Guarantee</h4>
              </div>
              <p className="text-xs text-slate-300 leading-relaxed">
                Uses PostgreSQL <code className="bg-slate-900 px-1 py-0.5 rounded text-teal-300">btree_gist</code> exclusion constraints combined with pessimistic <code className="bg-slate-900 px-1 py-0.5 rounded text-teal-300">SELECT ... FOR UPDATE</code> transactions. Conflicting simultaneous requests immediately receive a clean <code className="bg-slate-900 px-1 py-0.5 rounded text-rose-300">409 Conflict</code>.
              </p>
            </div>

            <div className="bg-slate-800/60 border border-slate-700 rounded-2xl p-6">
              <div className="flex items-center gap-3 mb-3">
                <Clock className="w-5 h-5 text-teal-400" />
                <h4 className="font-bold text-base">Automatic Expiring Slot Holds</h4>
              </div>
              <p className="text-xs text-slate-300 leading-relaxed">
                Slots are temporarily held while patients enter symptoms. Expired holds automatically lapse without blocking future bookings, swept by periodic Redis/Celery workers.
              </p>
            </div>

            <div className="bg-slate-800/60 border border-slate-700 rounded-2xl p-6">
              <div className="flex items-center gap-3 mb-3">
                <Calendar className="w-5 h-5 text-teal-400" />
                <h4 className="font-bold text-base">Safe Doctor Leave Cascading</h4>
              </div>
              <p className="text-xs text-slate-300 leading-relaxed">
                Doctor leaves identify all affected appointments, transitioning them safely to <code className="bg-slate-900 px-1 py-0.5 rounded text-amber-300">rescheduling_required</code> and asynchronously notifying patients and updating calendar events.
              </p>
            </div>

            <div className="bg-slate-800/60 border border-slate-700 rounded-2xl p-6">
              <div className="flex items-center gap-3 mb-3">
                <Sparkles className="w-5 h-5 text-teal-400" />
                <h4 className="font-bold text-base">Non-Blocking AI Resiliency</h4>
              </div>
              <p className="text-xs text-slate-300 leading-relaxed">
                AI symptom analysis and post-visit summaries degrade gracefully. LLM timeouts or quota exhaustion never crash or block core appointment booking flows.
              </p>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
};
