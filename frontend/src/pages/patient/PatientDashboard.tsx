import React, { useState, useEffect } from 'react';
import {
  doctorApi,
  appointmentApi,
  clinicalApi,
  engagementApi,
} from '../../services/api';
import {
  DoctorProfile,
  AppointmentSlot,
  SlotHold,
  Appointment,
  Prescription,
  PreVisitSummary,
  PostVisitSummary,
} from '../../types';
import {
  Search,
  Calendar,
  Clock,
  User,
  Sparkles,
  AlertTriangle,
  CheckCircle2,
  Pill,
  FileText,
} from 'lucide-react';

export const PatientDashboard: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'search' | 'appointments' | 'prescriptions' | 'summaries'>('search');
  const [doctors, setDoctors] = useState<DoctorProfile[]>([]);
  const [specializations, setSpecializations] = useState<string[]>([]);
  const [selectedSpec, setSelectedSpec] = useState<string>('');
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);

  // Slot booking & hold state
  const [selectedDoctor, setSelectedDoctor] = useState<DoctorProfile | null>(null);
  const [selectedDate, setSelectedDate] = useState<string>(new Date().toISOString().split('T')[0]);
  const [slots, setSlots] = useState<AppointmentSlot[]>([]);
  const [activeHold, setActiveHold] = useState<SlotHold | null>(null);
  const [holdTimeLeft, setHoldTimeLeft] = useState<number>(0);
  const [symptoms, setSymptoms] = useState<string>('');
  const [aiSummary, setAiSummary] = useState<PreVisitSummary | null>(null);
  const [analyzingAi, setAnalyzingAi] = useState<boolean>(false);

  // Appointments & Clinical data
  const [appointments, setAppointments] = useState<Appointment[]>([]);
  const [prescriptions, setPrescriptions] = useState<Prescription[]>([]);
  const [selectedAppointmentForSummary, setSelectedAppointmentForSummary] = useState<string | null>(null);
  const [viewedSummary, setViewedSummary] = useState<PostVisitSummary | null>(null);

  // Countdown timer for active hold
  useEffect(() => {
    if (!activeHold) return;
    const interval = setInterval(() => {
      const remaining = Math.max(0, Math.floor((new Date(activeHold.expires_at).getTime() - Date.now()) / 1000));
      setHoldTimeLeft(remaining);
      if (remaining === 0) {
        setActiveHold(null);
        setError('Your slot hold has expired. Please select an available slot again.');
      }
    }, 1000);
    return () => clearInterval(interval);
  }, [activeHold]);

  // Load doctors & specializations
  useEffect(() => {
    loadDoctors();
  }, [selectedSpec, searchQuery]);

  // Load data based on tab
  useEffect(() => {
    if (activeTab === 'appointments') loadAppointments();
    if (activeTab === 'prescriptions') loadPrescriptions();
  }, [activeTab]);

  const loadDoctors = async () => {
    try {
      setLoading(true);
      const [docs, specs] = await Promise.all([
        doctorApi.listDoctors({ specialization: selectedSpec || undefined, search: searchQuery || undefined }),
        doctorApi.listSpecializations(),
      ]);
      setDoctors(docs);
      setSpecializations(specs);
    } catch (err: any) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const loadAppointments = async () => {
    try {
      setLoading(true);
      const appts = await appointmentApi.listMyAppointments();
      setAppointments(appts);
    } catch (err: any) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const loadPrescriptions = async () => {
    try {
      setLoading(true);
      const rxs = await clinicalApi.listMyPrescriptions();
      setPrescriptions(rxs);
    } catch (err: any) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleSelectDoctor = async (doc: DoctorProfile) => {
    setSelectedDoctor(doc);
    setError(null);
    try {
      const res = await doctorApi.getSlots(doc.id, selectedDate);
      setSlots(res.slots);
    } catch (err: any) {
      setError('Could not load slots for this doctor.');
    }
  };

  const handleHoldSlot = async (slotId: string) => {
    setError(null);
    try {
      const hold = await appointmentApi.holdSlot({ slot_id: slotId });
      setActiveHold(hold);
      setHoldTimeLeft(Math.floor((new Date(hold.expires_at).getTime() - Date.now()) / 1000));
      // Refresh slots
      if (selectedDoctor) {
        const res = await doctorApi.getSlots(selectedDoctor.id, selectedDate);
        setSlots(res.slots);
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'This slot is no longer available.');
    }
  };

  const handleAnalyzeSymptoms = async () => {
    if (!activeHold || !symptoms.trim()) return;
    setAnalyzingAi(true);
    setError(null);
    try {
      const summary = await engagementApi.getPreVisitSummary(activeHold.id, symptoms);
      setAiSummary(summary);
    } catch (err: any) {
      setError('AI summary service fallback active.');
    } finally {
      setAnalyzingAi(false);
    }
  };

  const handleConfirmBooking = async () => {
    if (!activeHold) return;
    setError(null);
    try {
      await appointmentApi.confirmAppointment(activeHold.id, { chief_complaint: symptoms });
      setActiveHold(null);
      setAiSummary(null);
      setSymptoms('');
      setSelectedDoctor(null);
      setActiveTab('appointments');
      loadAppointments();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Could not confirm appointment.');
    }
  };

  const handleCancelAppointment = async (apptId: string) => {
    if (!confirm('Are you sure you want to cancel this appointment?')) return;
    try {
      await appointmentApi.cancelAppointment(apptId, 'Patient requested cancellation');
      loadAppointments();
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to cancel appointment.');
    }
  };

  const handleViewPostVisitSummary = async (apptId: string) => {
    setSelectedAppointmentForSummary(apptId);
    setViewedSummary(null);
    setError(null);
    try {
      const sum = await engagementApi.getPatientPostVisitSummary(apptId);
      setViewedSummary(sum);
    } catch (err: any) {
      setError('Published summary not yet available. Your doctor will publish it after clinical review.');
    }
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10 space-y-8">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-4 border-b border-slate-200 pb-6">
        <div>
          <h1 className="text-3xl font-black text-slate-900 tracking-tight">Patient Portal</h1>
          <p className="text-sm text-slate-600 mt-1">Book appointments, describe symptoms, and access post-visit records</p>
        </div>

        {/* Tab Switcher */}
        <div className="flex bg-slate-100 p-1.5 rounded-2xl border border-slate-200 gap-1 text-xs font-bold">
          <button
            onClick={() => setActiveTab('search')}
            className={`px-4 py-2 rounded-xl transition-all ${
              activeTab === 'search' ? 'bg-white text-teal-700 shadow-sm' : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            Find Doctors & Book
          </button>
          <button
            onClick={() => setActiveTab('appointments')}
            className={`px-4 py-2 rounded-xl transition-all ${
              activeTab === 'appointments' ? 'bg-white text-teal-700 shadow-sm' : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            My Appointments
          </button>
          <button
            onClick={() => setActiveTab('prescriptions')}
            className={`px-4 py-2 rounded-xl transition-all ${
              activeTab === 'prescriptions' ? 'bg-white text-teal-700 shadow-sm' : 'text-slate-600 hover:text-slate-900'
            }`}
          >
            Prescriptions
          </button>
        </div>
      </div>

      {loading && <div className="text-xs text-teal-600 font-bold animate-pulse">Fetching records...</div>}

      {error && (
        <div className="p-4 bg-rose-50 border border-rose-200 rounded-2xl text-rose-700 text-xs font-semibold flex items-center justify-between">
          <div className="flex items-center gap-2">
            <AlertTriangle className="w-4 h-4" />
            <span>{error}</span>
          </div>
          <button onClick={() => setError(null)} className="text-rose-500 hover:text-rose-800">Dismiss</button>
        </div>
      )}

      {/* Active Temporary Hold Banner */}
      {activeHold && (
        <div className="bg-amber-50 border-2 border-amber-300 rounded-3xl p-6 shadow-sm space-y-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <Clock className="w-6 h-6 text-amber-600 animate-pulse" />
              <div>
                <h3 className="font-extrabold text-amber-900 text-base">Appointment Slot Held</h3>
                <p className="text-xs text-amber-700">Complete pre-visit symptom details and confirm before time expires.</p>
              </div>
            </div>
            <div className="bg-amber-200/80 px-4 py-2 rounded-2xl font-black text-amber-900 text-sm">
              {Math.floor(holdTimeLeft / 60)}:{(holdTimeLeft % 60).toString().padStart(2, '0')} remaining
            </div>
          </div>

          <div className="space-y-3 pt-2">
            <label className="block text-xs font-bold text-slate-800 uppercase tracking-wider">Describe your symptoms (for AI pre-visit preparation)</label>
            <textarea
              rows={3}
              value={symptoms}
              onChange={(e) => setSymptoms(e.target.value)}
              placeholder="e.g. Mild headache and fatigue for the past 2 days, worse in bright light..."
              className="w-full p-3.5 bg-white border border-amber-200 rounded-2xl text-xs text-slate-800 focus:outline-none focus:ring-2 focus:ring-amber-500"
            />
            <div className="flex flex-wrap items-center gap-3">
              <button
                onClick={handleAnalyzeSymptoms}
                disabled={analyzingAi || !symptoms.trim()}
                className="px-4 py-2.5 bg-indigo-600 hover:bg-indigo-700 text-white font-bold text-xs rounded-xl flex items-center gap-2 shadow-sm disabled:opacity-50"
              >
                <Sparkles className="w-4 h-4" />
                {analyzingAi ? 'Analyzing Symptoms...' : 'Analyze with Medical AI'}
              </button>
              <button
                onClick={handleConfirmBooking}
                className="px-6 py-2.5 bg-teal-600 hover:bg-teal-700 text-white font-bold text-xs rounded-xl flex items-center gap-2 shadow-md shadow-teal-600/20"
              >
                <CheckCircle2 className="w-4 h-4" />
                Confirm & Book Appointment
              </button>
              <button
                onClick={() => {
                  appointmentApi.releaseHold(activeHold.id);
                  setActiveHold(null);
                }}
                className="px-4 py-2.5 bg-white border border-slate-300 hover:bg-slate-50 text-slate-700 font-semibold text-xs rounded-xl"
              >
                Release Hold
              </button>
            </div>
          </div>

          {/* AI Pre-visit Analysis Card */}
          {aiSummary && (
            <div className="bg-white border border-indigo-100 rounded-2xl p-5 mt-4 space-y-3">
              <div className="flex items-center justify-between">
                <div className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-black bg-indigo-100 text-indigo-800">
                  <Sparkles className="w-3.5 h-3.5" />
                  <span>AI Pre-Visit Assessment</span>
                </div>
                <span className={`text-xs font-extrabold px-2.5 py-0.5 rounded-full ${
                  aiSummary.urgency === 'HIGH' ? 'bg-rose-100 text-rose-800' :
                  aiSummary.urgency === 'MEDIUM' ? 'bg-amber-100 text-amber-800' : 'bg-emerald-100 text-emerald-800'
                }`}>
                  Urgency: {aiSummary.urgency}
                </span>
              </div>
              <p className="text-xs text-slate-700"><strong>Summary:</strong> {aiSummary.chief_complaint}</p>
              <div>
                <p className="text-xs font-bold text-slate-800 mb-1.5">Suggested Clarification Questions for Doctor:</p>
                <ul className="space-y-1 text-xs text-slate-600">
                  {aiSummary.suggested_questions.map((q, idx) => (
                    <li key={idx} className="flex items-start gap-2">
                      <span className="text-indigo-600 font-bold">•</span>
                      <span>{q}</span>
                    </li>
                  ))}
                </ul>
              </div>
              <p className="text-[10px] text-slate-400 italic">{aiSummary.disclaimer}</p>
            </div>
          )}
        </div>
      )}

      {/* TAB 1: Search Doctors & Available Slots */}
      {activeTab === 'search' && (
        <div className="space-y-6">
          <div className="bg-white p-6 rounded-3xl border border-slate-200 shadow-sm flex flex-wrap items-center gap-4">
            <div className="flex-1 min-w-[240px] relative">
              <Search className="w-5 h-5 text-slate-400 absolute left-3.5 top-1/2 -translate-y-1/2" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search doctors by name..."
                className="w-full pl-11 pr-4 py-3 bg-slate-50 border border-slate-200 rounded-xl text-xs focus:outline-none focus:ring-2 focus:ring-teal-500"
              />
            </div>

            <div className="w-64">
              <select
                value={selectedSpec}
                onChange={(e) => setSelectedSpec(e.target.value)}
                className="w-full px-4 py-3 bg-slate-50 border border-slate-200 rounded-xl text-xs font-semibold text-slate-700 focus:outline-none focus:ring-2 focus:ring-teal-500"
              >
                <option value="">All Specializations</option>
                {specializations.map((s) => (
                  <option key={s} value={s}>{s}</option>
                ))}
              </select>
            </div>
          </div>

          {/* Doctor Cards */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {doctors.map((doc) => (
              <div key={doc.id} className="bg-white rounded-3xl border border-slate-200 p-6 shadow-sm hover:shadow-md transition-shadow flex flex-col justify-between space-y-4">
                <div>
                  <div className="flex items-center gap-3 mb-3">
                    <div className="w-12 h-12 bg-teal-50 text-teal-600 rounded-2xl flex items-center justify-center font-black">
                      <User className="w-6 h-6" />
                    </div>
                    <div>
                      <h3 className="font-bold text-slate-900 text-base">{doc.name}</h3>
                      <span className="inline-block text-xs font-semibold text-teal-600 bg-teal-50 px-2.5 py-0.5 rounded-full">
                        {doc.specialization}
                      </span>
                    </div>
                  </div>
                  <p className="text-xs text-slate-600 line-clamp-2">{doc.bio || 'General clinical consultation.'}</p>
                </div>

                <div className="pt-3 border-t border-slate-100 flex items-center justify-between">
                  <div>
                    <span className="text-[10px] uppercase font-bold text-slate-400 block">Fee / Duration</span>
                    <span className="text-xs font-black text-slate-800">${doc.consultation_fee} • {doc.slot_duration_minutes}m</span>
                  </div>
                  <button
                    onClick={() => handleSelectDoctor(doc)}
                    className="px-4 py-2 bg-slate-900 hover:bg-teal-600 text-white font-bold text-xs rounded-xl transition-colors"
                  >
                    View Slots
                  </button>
                </div>
              </div>
            ))}
          </div>

          {/* Slots Picker for Selected Doctor */}
          {selectedDoctor && (
            <div className="bg-white rounded-3xl border border-slate-200 p-6 shadow-lg space-y-6">
              <div className="flex flex-wrap items-center justify-between gap-4 border-b border-slate-100 pb-4">
                <div>
                  <h3 className="text-lg font-black text-slate-900">Available Slots with Dr. {selectedDoctor.name}</h3>
                  <p className="text-xs text-slate-500">Pick a convenient time to temporarily hold and confirm your booking</p>
                </div>
                <div className="flex items-center gap-2">
                  <Calendar className="w-4 h-4 text-slate-500" />
                  <input
                    type="date"
                    value={selectedDate}
                    onChange={(e) => {
                      setSelectedDate(e.target.value);
                      handleSelectDoctor(selectedDoctor);
                    }}
                    className="px-3 py-1.5 border border-slate-200 rounded-xl text-xs font-semibold focus:outline-none focus:ring-2 focus:ring-teal-500"
                  />
                </div>
              </div>

              {slots.length === 0 ? (
                <div className="text-center py-8 text-slate-500 text-xs">
                  No open slots on this date. The doctor may be off-shift or on approved leave.
                </div>
              ) : (
                <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-3">
                  {slots.map((s) => {
                    const startStr = new Date(s.start_time).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
                    const isAvailable = s.status === 'available';
                    return (
                      <button
                        key={s.id}
                        disabled={!isAvailable || !!activeHold}
                        onClick={() => handleHoldSlot(s.id)}
                        className={`p-3 rounded-2xl border text-center font-bold text-xs transition-all ${
                          isAvailable
                            ? 'bg-teal-50/50 border-teal-200 text-teal-800 hover:bg-teal-600 hover:text-white shadow-sm'
                            : 'bg-slate-100 border-slate-200 text-slate-400 cursor-not-allowed'
                        }`}
                      >
                        {startStr}
                        <span className="block text-[10px] font-normal uppercase opacity-75">{s.status}</span>
                      </button>
                    );
                  })}
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* TAB 2: My Appointments */}
      {activeTab === 'appointments' && (
        <div className="space-y-4">
          {appointments.length === 0 ? (
            <div className="text-center py-16 bg-white rounded-3xl border border-slate-200 text-slate-500 text-xs">
              You have no scheduled appointments yet. Use the "Find Doctors & Book" tab to book a consultation.
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {appointments.map((appt) => (
                <div key={appt.id} className="bg-white rounded-3xl border border-slate-200 p-6 shadow-sm space-y-4">
                  <div className="flex items-center justify-between">
                    <span className={`text-xs font-black px-3 py-1 rounded-full uppercase ${
                      appt.status === 'confirmed' ? 'bg-emerald-100 text-emerald-800' :
                      appt.status === 'completed' ? 'bg-blue-100 text-blue-800' :
                      appt.status === 'rescheduled_required' ? 'bg-amber-100 text-amber-800' : 'bg-rose-100 text-rose-800'
                    }`}>
                      {appt.status}
                    </span>
                    <span className="text-xs text-slate-400">{new Date(appt.created_at).toLocaleDateString()}</span>
                  </div>

                  <div>
                    <h4 className="font-bold text-slate-900 text-sm">Doctor Consultation</h4>
                    <p className="text-xs text-slate-600 mt-1">Chief Complaint: {appt.chief_complaint || 'General medical follow-up'}</p>
                  </div>

                  <div className="pt-3 border-t border-slate-100 flex items-center justify-between gap-2">
                    {appt.status === 'confirmed' && (
                      <button
                        onClick={() => handleCancelAppointment(appt.id)}
                        className="px-3 py-1.5 bg-rose-50 text-rose-700 hover:bg-rose-100 font-bold text-xs rounded-xl"
                      >
                        Cancel Appointment
                      </button>
                    )}
                    {appt.status === 'completed' && (
                      <button
                        onClick={() => handleViewPostVisitSummary(appt.id)}
                        className="px-3 py-1.5 bg-indigo-50 text-indigo-700 hover:bg-indigo-100 font-bold text-xs rounded-xl flex items-center gap-1.5"
                      >
                        <FileText className="w-3.5 h-3.5" />
                        View Post-Visit Summary
                      </button>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* Post-Visit Summary Modal */}
          {selectedAppointmentForSummary && (
            <div className="bg-white border-2 border-indigo-200 rounded-3xl p-6 shadow-xl space-y-4">
              <div className="flex items-center justify-between border-b border-slate-100 pb-3">
                <div className="flex items-center gap-2">
                  <Sparkles className="w-5 h-5 text-indigo-600" />
                  <h3 className="font-black text-slate-900 text-base">Doctor-Approved Post-Visit Summary</h3>
                </div>
                <button onClick={() => setSelectedAppointmentForSummary(null)} className="text-slate-400 hover:text-slate-600 text-xs font-bold">
                  Close
                </button>
              </div>

              {viewedSummary ? (
                <div className="space-y-3 text-xs text-slate-700">
                  <div>
                    <span className="font-bold uppercase text-[10px] text-slate-400 block">Explanation of Visit</span>
                    <p className="mt-1 leading-relaxed bg-slate-50 p-3 rounded-xl">{viewedSummary.content?.visit_explanation || 'No summary available.'}</p>
                  </div>
                  <div>
                    <span className="font-bold uppercase text-[10px] text-slate-400 block">Follow-Up Guidance</span>
                    <p className="mt-1 leading-relaxed bg-slate-50 p-3 rounded-xl">{viewedSummary.content?.follow_up_steps || 'Follow regular care instructions.'}</p>
                  </div>
                </div>
              ) : (
                <p className="text-xs text-slate-500 py-4">Loading post-visit clinical summary...</p>
              )}
            </div>
          )}
        </div>
      )}

      {/* TAB 3: Prescriptions */}
      {activeTab === 'prescriptions' && (
        <div className="space-y-4">
          {prescriptions.length === 0 ? (
            <div className="text-center py-16 bg-white rounded-3xl border border-slate-200 text-slate-500 text-xs">
              No prescriptions recorded yet.
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {prescriptions.map((rx) => (
                <div key={rx.id} className="bg-white rounded-3xl border border-slate-200 p-6 shadow-sm space-y-3">
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 bg-teal-50 text-teal-600 rounded-2xl flex items-center justify-center">
                      <Pill className="w-5 h-5" />
                    </div>
                    <div>
                      <h4 className="font-bold text-slate-900 text-sm">{rx.medication_name}</h4>
                      <span className="text-xs text-slate-500">{rx.dosage} • {rx.frequency}</span>
                    </div>
                  </div>
                  <p className="text-xs text-slate-600 bg-slate-50 p-3 rounded-xl">{rx.instructions || 'Take as prescribed.'}</p>
                  <div className="pt-2 flex items-center justify-between">
                    <span className="text-[10px] text-emerald-600 font-bold uppercase">Active Prescription</span>
                    <button
                      onClick={() => {
                        engagementApi.createMedicationReminder({
                          prescription_id: rx.id,
                          schedule: { times: ['08:00', '20:00'] },
                        });
                        alert('Daily medication reminder configured!');
                      }}
                      className="px-3 py-1.5 bg-teal-600 hover:bg-teal-700 text-white font-bold text-xs rounded-xl"
                    >
                      Set Daily Reminder
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
};
