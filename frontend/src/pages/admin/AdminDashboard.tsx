import React, { useState, useEffect } from 'react';
import {
  adminApi,
} from '../../services/api';
import {
  DoctorProfile,
  DoctorLeaveItem,
} from '../../types';
import {
  UserPlus,
  Calendar,
  Trash2,
  CheckCircle2,
  Plus,
} from 'lucide-react';

export const AdminDashboard: React.FC = () => {
  const [doctors, setDoctors] = useState<DoctorProfile[]>([]);
  const [leaves, setLeaves] = useState<DoctorLeaveItem[]>([]);
  const [activeTab, setActiveTab] = useState<'doctors' | 'onboard' | 'leave'>('doctors');
  const [loading, setLoading] = useState<boolean>(false);
  const [message, setMessage] = useState<string | null>(null);

  // Onboard form state
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('Password123!');
  const [specialization, setSpecialization] = useState('General Medicine');
  const [slotDuration, setSlotDuration] = useState<number>(30);
  const [fee, setFee] = useState<number>(100);

  // Leave form state
  const [selectedDoctorId, setSelectedDoctorId] = useState<string>('');
  const [leaveDate, setLeaveDate] = useState<string>(new Date().toISOString().split('T')[0]);
  const [endDate, setEndDate] = useState<string>(new Date().toISOString().split('T')[0]);
  const [reason, setReason] = useState<string>('Annual Conference');

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      const [docs, lvs] = await Promise.all([
        adminApi.listDoctors(),
        adminApi.listLeaves(),
      ]);
      setDoctors(docs);
      setLeaves(lvs);
      if (docs.length > 0 && !selectedDoctorId) {
        setSelectedDoctorId(docs[0].id);
      }
    } catch (err: any) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleOnboardDoctor = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await adminApi.createDoctor({
        name,
        email,
        password,
        specialization,
        slot_duration_minutes: Number(slotDuration),
        consultation_fee: Number(fee),
      });
      setMessage(`Dr. ${name} successfully onboarded.`);
      setName('');
      setEmail('');
      loadData();
      setActiveTab('doctors');
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to onboard doctor.');
    }
  };

  const handleCreateLeave = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedDoctorId) return;
    try {
      await adminApi.createLeave({
        doctor_id: selectedDoctorId,
        leave_date: leaveDate,
        end_date: endDate,
        reason,
      });
      setMessage('Doctor leave registered. Conflicting appointments cascaded to reschedule required.');
      loadData();
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to create leave.');
    }
  };

  const handleRemoveLeave = async (leaveId: string) => {
    if (!confirm('Are you sure you want to cancel this approved leave?')) return;
    try {
      await adminApi.removeLeave(leaveId);
      setMessage('Doctor leave cancelled.');
      loadData();
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to remove leave.');
    }
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10 space-y-8">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-4 border-b border-slate-200 pb-6">
        <div>
          <h1 className="text-3xl font-black text-slate-900 tracking-tight">Admin Command Center</h1>
          <p className="text-sm text-slate-600 mt-1">Doctor onboarding, specialization management, and automated leave cascading</p>
        </div>

        <div className="flex bg-slate-100 p-1.5 rounded-2xl border border-slate-200 gap-1 text-xs font-bold">
          <button
            onClick={() => setActiveTab('doctors')}
            className={`px-4 py-2 rounded-xl transition-all ${
              activeTab === 'doctors' ? 'bg-white text-teal-700 shadow-sm' : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            Doctors Directory
          </button>
          <button
            onClick={() => setActiveTab('onboard')}
            className={`px-4 py-2 rounded-xl transition-all ${
              activeTab === 'onboard' ? 'bg-white text-teal-700 shadow-sm' : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            Onboard Doctor
          </button>
          <button
            onClick={() => setActiveTab('leave')}
            className={`px-4 py-2 rounded-xl transition-all ${
              activeTab === 'leave' ? 'bg-white text-teal-700 shadow-sm' : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            Leave Management
          </button>
        </div>
      </div>

      {loading && <div className="text-xs text-teal-600 font-bold animate-pulse">Syncing with server...</div>}

      {message && (
        <div className="p-4 bg-emerald-50 border border-emerald-200 rounded-2xl text-emerald-800 text-xs font-semibold flex items-center justify-between">
          <div className="flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4" />
            <span>{message}</span>
          </div>
          <button onClick={() => setMessage(null)} className="text-emerald-600 hover:text-emerald-900">Dismiss</button>
        </div>
      )}

      {/* TAB 1: Doctors Directory */}
      {activeTab === 'doctors' && (
        <div className="space-y-6">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {doctors.map((doc) => (
              <div key={doc.id} className="bg-white rounded-3xl border border-slate-200 p-6 shadow-sm space-y-4">
                <div>
                  <h3 className="font-bold text-slate-900 text-base">{doc.name}</h3>
                  <span className="text-xs font-semibold text-teal-600 bg-teal-50 px-2.5 py-0.5 rounded-full inline-block mt-1">
                    {doc.specialization}
                  </span>
                  <p className="text-xs text-slate-500 mt-2">{doc.email}</p>
                </div>
                <div className="pt-3 border-t border-slate-100 flex items-center justify-between text-xs font-black text-slate-700">
                  <span>Slot: {doc.slot_duration_minutes}m</span>
                  <span>Fee: ${doc.consultation_fee}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* TAB 2: Onboard Doctor */}
      {activeTab === 'onboard' && (
        <div className="max-w-2xl bg-white rounded-3xl border border-slate-200 p-8 shadow-sm space-y-6">
          <div className="flex items-center gap-3">
            <div className="w-12 h-12 bg-teal-50 text-teal-600 rounded-2xl flex items-center justify-center font-black">
              <UserPlus className="w-6 h-6" />
            </div>
            <div>
              <h3 className="font-bold text-slate-900 text-lg">Onboard New Practitioner</h3>
              <p className="text-xs text-slate-500">Creates practitioner user account and doctor clinical profile</p>
            </div>
          </div>

          <form onSubmit={handleOnboardDoctor} className="space-y-4">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1.5">Doctor Name</label>
                <input
                  type="text"
                  required
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="Dr. Gregory House"
                  className="w-full p-3 bg-slate-50 border border-slate-200 rounded-xl text-xs"
                />
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1.5">Email Address</label>
                <input
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="house@clinic.com"
                  className="w-full p-3 bg-slate-50 border border-slate-200 rounded-xl text-xs"
                />
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1.5">Temporary Password</label>
                <input
                  type="password"
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full p-3 bg-slate-50 border border-slate-200 rounded-xl text-xs"
                />
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1.5">Specialization</label>
                <input
                  type="text"
                  required
                  value={specialization}
                  onChange={(e) => setSpecialization(e.target.value)}
                  placeholder="Cardiology / General"
                  className="w-full p-3 bg-slate-50 border border-slate-200 rounded-xl text-xs"
                />
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1.5">Slot Duration (Minutes)</label>
                <input
                  type="number"
                  required
                  value={slotDuration}
                  onChange={(e) => setSlotDuration(Number(e.target.value))}
                  className="w-full p-3 bg-slate-50 border border-slate-200 rounded-xl text-xs"
                />
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1.5">Consultation Fee ($)</label>
                <input
                  type="number"
                  required
                  value={fee}
                  onChange={(e) => setFee(Number(e.target.value))}
                  className="w-full p-3 bg-slate-50 border border-slate-200 rounded-xl text-xs"
                />
              </div>
            </div>

            <div className="pt-4 flex justify-end">
              <button
                type="submit"
                className="px-6 py-3 bg-teal-600 hover:bg-teal-700 text-white font-bold text-xs rounded-xl shadow-md shadow-teal-600/20 flex items-center gap-2"
              >
                <Plus className="w-4 h-4" />
                Register Practitioner
              </button>
            </div>
          </form>
        </div>
      )}

      {/* TAB 3: Leave Management */}
      {activeTab === 'leave' && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Create Leave Form */}
          <div className="bg-white rounded-3xl border border-slate-200 p-6 shadow-sm space-y-4">
            <h3 className="font-extrabold text-slate-900 text-base flex items-center gap-2">
              <Calendar className="w-5 h-5 text-amber-600" />
              Schedule Doctor Leave
            </h3>
            <p className="text-xs text-slate-500">
              Applying leave automatically disables all overlapping slots and transitions confirmed appointments to 'rescheduled_required'.
            </p>

            <form onSubmit={handleCreateLeave} className="space-y-3">
              <div>
                <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">Select Doctor</label>
                <select
                  value={selectedDoctorId}
                  onChange={(e) => setSelectedDoctorId(e.target.value)}
                  className="w-full p-3 bg-slate-50 border border-slate-200 rounded-xl text-xs font-semibold"
                >
                  {doctors.map((d) => (
                    <option key={d.id} value={d.id}>{d.name} ({d.specialization})</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">Start Date</label>
                <input
                  type="date"
                  required
                  value={leaveDate}
                  onChange={(e) => setLeaveDate(e.target.value)}
                  className="w-full p-3 bg-slate-50 border border-slate-200 rounded-xl text-xs"
                />
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">End Date</label>
                <input
                  type="date"
                  required
                  value={endDate}
                  onChange={(e) => setEndDate(e.target.value)}
                  className="w-full p-3 bg-slate-50 border border-slate-200 rounded-xl text-xs"
                />
              </div>

              <div>
                <label className="block text-xs font-bold text-slate-700 uppercase tracking-wider mb-1">Reason</label>
                <input
                  type="text"
                  value={reason}
                  onChange={(e) => setReason(e.target.value)}
                  placeholder="e.g. Annual Medical Conference"
                  className="w-full p-3 bg-slate-50 border border-slate-200 rounded-xl text-xs"
                />
              </div>

              <div className="pt-2">
                <button
                  type="submit"
                  className="w-full py-3 bg-amber-600 hover:bg-amber-700 text-white font-bold text-xs rounded-xl shadow-sm"
                >
                  Approve Leave & Cascade Slots
                </button>
              </div>
            </form>
          </div>

          {/* Existing Leaves List */}
          <div className="lg:col-span-2 bg-white rounded-3xl border border-slate-200 p-6 shadow-sm space-y-4">
            <h3 className="font-extrabold text-slate-900 text-base">Active & Approved Leaves</h3>

            {leaves.length === 0 ? (
              <p className="text-xs text-slate-500 py-12 text-center">No practitioner leaves on record.</p>
            ) : (
              <div className="space-y-3">
                {leaves.map((lv) => (
                  <div key={lv.id} className="p-4 bg-slate-50 rounded-2xl border border-slate-200 flex items-center justify-between">
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="text-xs font-black text-slate-900">{lv.leave_date} to {lv.end_date || lv.leave_date}</span>
                        <span className="text-[10px] bg-emerald-100 text-emerald-800 font-bold px-2 py-0.5 rounded-full uppercase">{lv.status}</span>
                      </div>
                      <p className="text-xs text-slate-600 mt-1">Reason: {lv.reason || 'Not specified'}</p>
                    </div>
                    {lv.status === 'approved' && (
                      <button
                        onClick={() => handleRemoveLeave(lv.id)}
                        className="p-2 text-rose-600 hover:bg-rose-50 rounded-xl"
                        title="Cancel leave"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};
