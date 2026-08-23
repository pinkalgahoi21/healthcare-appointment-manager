import React, { useState, useEffect } from 'react';
import {
  appointmentApi,
  clinicalApi,
  engagementApi,
} from '../../services/api';
import {
  Appointment,
  PostVisitSummary,
} from '../../types';
import {
  Clock,
  User,
  Sparkles,
  FileText,
  Pill,
  CheckCircle2,
  Calendar,
  Send,
} from 'lucide-react';

export const DoctorDashboard: React.FC = () => {
  const [appointments, setAppointments] = useState<Appointment[]>([]);
  const [selectedAppt, setSelectedAppt] = useState<Appointment | null>(null);
  const [clinicalNote, setClinicalNote] = useState<string>('');
  const [medName, setMedName] = useState<string>('');
  const [dosage, setDosage] = useState<string>('');
  const [frequency, setFrequency] = useState<string>('');
  const [instructions, setInstructions] = useState<string>('');
  const [followUp, setFollowUp] = useState<string>('');
  const [generatedSummary, setGeneratedSummary] = useState<PostVisitSummary | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [generatingAi, setGeneratingAi] = useState<boolean>(false);
  const [message, setMessage] = useState<string | null>(null);

  useEffect(() => {
    loadAppointments();
  }, []);

  const loadAppointments = async () => {
    try {
      setLoading(true);
      const data = await appointmentApi.listMyAppointments();
      setAppointments(data);
    } catch (err: any) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleSelectAppointment = async (appt: Appointment) => {
    setSelectedAppt(appt);
    setClinicalNote('');
    setGeneratedSummary(null);
    setMessage(null);
  };

  const handleSaveClinicalNote = async () => {
    if (!selectedAppt || !clinicalNote.trim()) return;
    try {
      await clinicalApi.upsertNote(selectedAppt.id, clinicalNote);
      setMessage('Clinical note saved successfully.');
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to save note.');
    }
  };

  const handleAddPrescription = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedAppt || !medName.trim()) return;
    try {
      await clinicalApi.createPrescription(selectedAppt.id, {
        medication_name: medName,
        dosage,
        frequency,
        instructions,
      });
      setMedName('');
      setDosage('');
      setFrequency('');
      setInstructions('');
      setMessage('Prescription recorded for patient.');
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to add prescription.');
    }
  };

  const handleGeneratePostVisitSummary = async () => {
    if (!selectedAppt) return;
    setGeneratingAi(true);
    try {
      const summary = await engagementApi.createPostVisitSummary(selectedAppt.id, followUp);
      setGeneratedSummary(summary);
      setMessage('AI draft post-visit summary created. Review and publish below.');
    } catch (err: any) {
      alert('Could not generate post-visit summary.');
    } finally {
      setGeneratingAi(false);
    }
  };

  const handlePublishSummary = async () => {
    if (!generatedSummary) return;
    try {
      const published = await engagementApi.publishPostVisitSummary(generatedSummary.id);
      setGeneratedSummary(published);
      setMessage('Summary approved and published! Now visible in patient portal.');
    } catch (err: any) {
      alert('Failed to publish summary.');
    }
  };

  const handleCompleteAppointment = async (apptId: string) => {
    try {
      await appointmentApi.completeAppointment(apptId);
      loadAppointments();
      if (selectedAppt?.id === apptId) {
        setSelectedAppt((prev) => prev ? { ...prev, status: 'completed' } : null);
      }
      setMessage('Appointment marked as COMPLETED.');
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to complete appointment.');
    }
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10 space-y-8">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-4 border-b border-slate-200 pb-6">
        <div>
          <h1 className="text-3xl font-black text-slate-900 tracking-tight">Doctor Clinical Workspace</h1>
          <p className="text-sm text-slate-600 mt-1">Review pre-visit symptoms, manage clinical notes, prescribe, and publish AI summaries</p>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => alert('Redirecting to Google OAuth 2.0 calendar consent...')}
            className="px-4 py-2 bg-white border border-slate-200 hover:bg-slate-50 text-slate-700 font-bold text-xs rounded-xl shadow-sm flex items-center gap-2"
          >
            <Calendar className="w-4 h-4 text-blue-600" />
            Connect Google Calendar
          </button>
        </div>
      </div>

      {loading && <div className="text-xs text-teal-600 font-bold animate-pulse">Loading consultations...</div>}

      {message && (
        <div className="p-4 bg-emerald-50 border border-emerald-200 rounded-2xl text-emerald-800 text-xs font-semibold flex items-center justify-between">
          <div className="flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4" />
            <span>{message}</span>
          </div>
          <button onClick={() => setMessage(null)} className="text-emerald-600 hover:text-emerald-900">Dismiss</button>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Left Column: Scheduled Appointments */}
        <div className="bg-white rounded-3xl border border-slate-200 p-6 shadow-sm space-y-4">
          <h3 className="font-extrabold text-slate-900 text-base flex items-center gap-2">
            <Clock className="w-5 h-5 text-teal-600" />
            Assigned Consultations
          </h3>

          {appointments.length === 0 ? (
            <p className="text-xs text-slate-500 py-8 text-center">No assigned consultations yet.</p>
          ) : (
            <div className="space-y-3">
              {appointments.map((appt) => (
                <div
                  key={appt.id}
                  onClick={() => handleSelectAppointment(appt)}
                  className={`p-4 rounded-2xl border transition-all cursor-pointer ${
                    selectedAppt?.id === appt.id
                      ? 'bg-teal-50/70 border-teal-300 shadow-sm'
                      : 'bg-slate-50/50 border-slate-200 hover:bg-slate-50'
                  }`}
                >
                  <div className="flex items-center justify-between mb-1.5">
                    <span className={`text-[10px] font-black px-2 py-0.5 rounded-full uppercase ${
                      appt.status === 'confirmed' ? 'bg-emerald-100 text-emerald-800' :
                      appt.status === 'completed' ? 'bg-blue-100 text-blue-800' : 'bg-amber-100 text-amber-800'
                    }`}>
                      {appt.status}
                    </span>
                    <span className="text-[10px] text-slate-400">{new Date(appt.created_at).toLocaleDateString()}</span>
                  </div>
                  <h4 className="font-bold text-slate-800 text-xs">Patient Consultation</h4>
                  <p className="text-[11px] text-slate-500 mt-1 line-clamp-2">
                    Symptoms: {appt.chief_complaint || 'None provided'}
                  </p>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Right 2 Columns: Clinical Workstation */}
        <div className="lg:col-span-2 space-y-6">
          {selectedAppt ? (
            <div className="space-y-6">
              {/* Patient Pre-Visit Overview */}
              <div className="bg-white rounded-3xl border border-slate-200 p-6 shadow-sm space-y-3">
                <div className="flex items-center justify-between">
                  <h3 className="font-extrabold text-slate-900 text-base flex items-center gap-2">
                    <User className="w-5 h-5 text-indigo-600" />
                    Patient Symptoms & Pre-Visit Triage
                  </h3>
                  {selectedAppt.status === 'confirmed' && (
                    <button
                      onClick={() => handleCompleteAppointment(selectedAppt.id)}
                      className="px-3 py-1.5 bg-emerald-600 hover:bg-emerald-700 text-white font-bold text-xs rounded-xl shadow-sm"
                    >
                      Mark Visit Completed
                    </button>
                  )}
                </div>
                <div className="bg-slate-50 p-4 rounded-2xl text-xs text-slate-700">
                  <span className="font-bold block uppercase text-[10px] text-slate-400 mb-1">Chief Complaint</span>
                  <p>{selectedAppt.chief_complaint || 'No symptoms pre-entered by patient.'}</p>
                </div>
              </div>

              {/* Clinical Notes Editor */}
              <div className="bg-white rounded-3xl border border-slate-200 p-6 shadow-sm space-y-3">
                <h3 className="font-extrabold text-slate-900 text-base flex items-center gap-2">
                  <FileText className="w-5 h-5 text-teal-600" />
                  Clinical Notes (Confidential)
                </h3>
                <textarea
                  rows={4}
                  value={clinicalNote}
                  onChange={(e) => setClinicalNote(e.target.value)}
                  placeholder="Record objective observations, physical exam findings, and clinical assessment..."
                  className="w-full p-3.5 bg-slate-50 border border-slate-200 rounded-2xl text-xs focus:outline-none focus:ring-2 focus:ring-teal-500"
                />
                <div className="flex justify-end">
                  <button
                    onClick={handleSaveClinicalNote}
                    className="px-4 py-2 bg-teal-600 hover:bg-teal-700 text-white font-bold text-xs rounded-xl shadow-sm"
                  >
                    Save Clinical Note
                  </button>
                </div>
              </div>

              {/* Prescription Generator */}
              <div className="bg-white rounded-3xl border border-slate-200 p-6 shadow-sm space-y-4">
                <h3 className="font-extrabold text-slate-900 text-base flex items-center gap-2">
                  <Pill className="w-5 h-5 text-blue-600" />
                  Issue Prescription
                </h3>
                <form onSubmit={handleAddPrescription} className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  <input
                    type="text"
                    required
                    value={medName}
                    onChange={(e) => setMedName(e.target.value)}
                    placeholder="Medication Name (e.g. Amoxicillin 500mg)"
                    className="p-3 bg-slate-50 border border-slate-200 rounded-xl text-xs"
                  />
                  <input
                    type="text"
                    required
                    value={dosage}
                    onChange={(e) => setDosage(e.target.value)}
                    placeholder="Dosage (e.g. 1 Capsule)"
                    className="p-3 bg-slate-50 border border-slate-200 rounded-xl text-xs"
                  />
                  <input
                    type="text"
                    required
                    value={frequency}
                    onChange={(e) => setFrequency(e.target.value)}
                    placeholder="Frequency (e.g. Three times daily with meals)"
                    className="p-3 bg-slate-50 border border-slate-200 rounded-xl text-xs"
                  />
                  <input
                    type="text"
                    value={instructions}
                    onChange={(e) => setInstructions(e.target.value)}
                    placeholder="Special Instructions (e.g. Take full 7 days)"
                    className="p-3 bg-slate-50 border border-slate-200 rounded-xl text-xs"
                  />
                  <div className="sm:col-span-2 flex justify-end">
                    <button
                      type="submit"
                      className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white font-bold text-xs rounded-xl shadow-sm"
                    >
                      Issue & Sign Prescription
                    </button>
                  </div>
                </form>
              </div>

              {/* AI Post-Visit Summary & Publishing Gate */}
              <div className="bg-white rounded-3xl border border-slate-200 p-6 shadow-sm space-y-4">
                <div className="flex items-center justify-between">
                  <h3 className="font-extrabold text-slate-900 text-base flex items-center gap-2">
                    <Sparkles className="w-5 h-5 text-indigo-600" />
                    AI Patient-Friendly Post-Visit Summary
                  </h3>
                  <span className="text-[10px] bg-amber-100 text-amber-900 px-2 py-0.5 rounded-full font-bold">
                    Doctor Review Gate
                  </span>
                </div>

                <textarea
                  rows={2}
                  value={followUp}
                  onChange={(e) => setFollowUp(e.target.value)}
                  placeholder="Enter discharge & follow-up instructions for the patient..."
                  className="w-full p-3.5 bg-slate-50 border border-slate-200 rounded-2xl text-xs focus:outline-none focus:ring-2 focus:ring-indigo-500"
                />

                <div className="flex items-center gap-3">
                  <button
                    onClick={handleGeneratePostVisitSummary}
                    disabled={generatingAi}
                    className="px-4 py-2.5 bg-indigo-600 hover:bg-indigo-700 text-white font-bold text-xs rounded-xl flex items-center gap-2 shadow-sm disabled:opacity-50"
                  >
                    <Sparkles className="w-4 h-4" />
                    {generatingAi ? 'Generating Draft...' : 'Generate AI Summary Draft'}
                  </button>
                </div>

                {generatedSummary && (
                  <div className="bg-slate-50 border border-indigo-200 rounded-2xl p-5 space-y-3 mt-4">
                    <div className="flex items-center justify-between">
                      <span className="font-extrabold text-xs text-indigo-900">Generated Patient Explanation (Draft)</span>
                      <span className={`text-[10px] font-black px-2 py-0.5 rounded-full ${
                        generatedSummary.is_published ? 'bg-emerald-100 text-emerald-800' : 'bg-amber-100 text-amber-800'
                      }`}>
                        {generatedSummary.is_published ? 'Published to Patient' : 'Unpublished Draft'}
                      </span>
                    </div>

                    <p className="text-xs text-slate-700 bg-white p-3 rounded-xl border border-slate-200">
                      {generatedSummary.content?.visit_explanation}
                    </p>

                    <div className="pt-2 flex justify-end">
                      {!generatedSummary.is_published && (
                        <button
                          onClick={handlePublishSummary}
                          className="px-5 py-2.5 bg-emerald-600 hover:bg-emerald-700 text-white font-bold text-xs rounded-xl flex items-center gap-2 shadow-md shadow-emerald-600/20"
                        >
                          <Send className="w-4 h-4" />
                          Approve & Publish to Patient
                        </button>
                      )}
                    </div>
                  </div>
                )}
              </div>
            </div>
          ) : (
            <div className="text-center py-24 bg-white rounded-3xl border border-slate-200 text-slate-400 text-xs">
              Select an appointment from the left schedule to view patient symptoms and manage clinical records.
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
