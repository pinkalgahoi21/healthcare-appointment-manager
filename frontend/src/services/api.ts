import {
  AuthResponse,
  DoctorProfile,
  AppointmentSlot,
  SlotHold,
  Appointment,
  ClinicalNote,
  Prescription,
  PreVisitSummary,
  PostVisitSummary,
  NotificationItem,
  MedicationReminderItem,
  DoctorLeaveItem,
  HealthResponse,
  WorkingHour,
} from '../types';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

async function request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const token = localStorage.getItem('auth_token');
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(options.headers as Record<string, string>),
  };

  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const url = endpoint.startsWith('http') ? endpoint : `${API_BASE_URL}${endpoint}`;
  const response = await fetch(url, {
    ...options,
    headers,
  });

  if (!response.ok) {
    let errorDetail = `HTTP Error ${response.status}`;
    try {
      const errorJson = await response.json();
      errorDetail = errorJson.detail || JSON.stringify(errorJson);
    } catch {
      errorDetail = await response.text();
    }
    const err: any = new Error(errorDetail);
    err.response = { status: response.status, data: { detail: errorDetail } };
    throw err;
  }

  return response.json();
}

export const authApi = {
  login: async (credentials: { email: string; password: string }): Promise<AuthResponse> => {
    return request<AuthResponse>('/api/v1/auth/login', {
      method: 'POST',
      body: JSON.stringify(credentials),
    });
  },
  register: async (payload: { name: string; email: string; password: string; role?: string }): Promise<AuthResponse> => {
    return request<AuthResponse>('/api/v1/auth/register', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },
  getMe: async () => {
    return request('/api/v1/auth/me');
  },
};

export const healthApi = {
  getHealth: async (): Promise<HealthResponse> => {
    return request<HealthResponse>('/api/health');
  },
};

export const doctorApi = {
  listDoctors: async (params?: { specialization?: string; search?: string }): Promise<DoctorProfile[]> => {
    const searchParams = new URLSearchParams();
    if (params?.specialization) searchParams.append('specialization', params.specialization);
    if (params?.search) searchParams.append('search', params.search);
    const qs = searchParams.toString();
    return request<DoctorProfile[]>(`/api/v1/doctors${qs ? `?${qs}` : ''}`);
  },
  getDoctorById: async (doctorId: string): Promise<DoctorProfile> => {
    return request<DoctorProfile>(`/api/v1/doctors/${doctorId}`);
  },
  listSpecializations: async (): Promise<string[]> => {
    return request<string[]>('/api/v1/doctors/specializations');
  },
  getSlots: async (doctorId: string, date: string): Promise<{ doctor_id: string; date: string; slots: AppointmentSlot[] }> => {
    return request(`/api/v1/doctors/${doctorId}/slots?date=${encodeURIComponent(date)}`);
  },
  setWorkingHours: async (workingHours: WorkingHour[]): Promise<WorkingHour[]> => {
    return request<WorkingHour[]>('/api/v1/doctors/working-hours', {
      method: 'POST',
      body: JSON.stringify({ working_hours: workingHours }),
    });
  },
};

export const appointmentApi = {
  holdSlot: async (payload: { slot_id: string; chief_complaint?: string }): Promise<SlotHold> => {
    return request<SlotHold>('/api/v1/appointments/hold', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },
  confirmAppointment: async (holdId: string, payload?: { chief_complaint?: string }): Promise<Appointment> => {
    return request<Appointment>(`/api/v1/appointments/${holdId}/confirm`, {
      method: 'POST',
      body: JSON.stringify(payload || {}),
    });
  },
  releaseHold: async (holdId: string): Promise<SlotHold> => {
    return request<SlotHold>(`/api/v1/appointments/holds/${holdId}/release`, {
      method: 'POST',
    });
  },
  cancelAppointment: async (appointmentId: string, reason?: string): Promise<Appointment> => {
    return request<Appointment>(`/api/v1/appointments/${appointmentId}/cancel`, {
      method: 'POST',
      body: JSON.stringify({ reason }),
    });
  },
  listMyAppointments: async (status?: string): Promise<Appointment[]> => {
    const qs = status ? `?appointment_status=${encodeURIComponent(status)}` : '';
    return request<Appointment[]>(`/api/v1/appointments/me${qs}`);
  },
  completeAppointment: async (appointmentId: string): Promise<Appointment> => {
    return request<Appointment>(`/api/v1/appointments/${appointmentId}/complete`, {
      method: 'POST',
    });
  },
  markRescheduleRequired: async (appointmentId: string): Promise<Appointment> => {
    return request<Appointment>(`/api/v1/appointments/${appointmentId}/reschedule-required`, {
      method: 'POST',
    });
  },
};

export const clinicalApi = {
  upsertNote: async (appointmentId: string, content: string): Promise<ClinicalNote> => {
    return request<ClinicalNote>(`/api/v1/clinical/appointments/${appointmentId}/note`, {
      method: 'PUT',
      body: JSON.stringify({ content }),
    });
  },
  createPrescription: async (appointmentId: string, payload: { medication_name: string; dosage: string; frequency: string; instructions?: string }): Promise<Prescription> => {
    return request<Prescription>(`/api/v1/clinical/appointments/${appointmentId}/prescriptions`, {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },
  listMyPrescriptions: async (): Promise<Prescription[]> => {
    return request<Prescription[]>('/api/v1/clinical/prescriptions/me');
  },
};

export const engagementApi = {
  getPreVisitSummary: async (appointmentId: string, symptoms: string): Promise<PreVisitSummary> => {
    return request<PreVisitSummary>(`/api/v1/engagement/appointments/${appointmentId}/pre-visit-summary`, {
      method: 'POST',
      body: JSON.stringify({ symptoms }),
    });
  },
  createPostVisitSummary: async (appointmentId: string, followUpInstructions: string): Promise<PostVisitSummary> => {
    return request<PostVisitSummary>(`/api/v1/engagement/appointments/${appointmentId}/post-visit-summary`, {
      method: 'POST',
      body: JSON.stringify({ follow_up_instructions: followUpInstructions }),
    });
  },
  publishPostVisitSummary: async (summaryId: string): Promise<PostVisitSummary> => {
    return request<PostVisitSummary>(`/api/v1/engagement/post-visit-summaries/${summaryId}/publish`, {
      method: 'POST',
    });
  },
  getPatientPostVisitSummary: async (appointmentId: string): Promise<PostVisitSummary> => {
    return request<PostVisitSummary>(`/api/v1/engagement/appointments/${appointmentId}/post-visit-summary`);
  },
  listNotifications: async (): Promise<NotificationItem[]> => {
    return request<NotificationItem[]>('/api/v1/engagement/notifications/me');
  },
  createMedicationReminder: async (payload: { prescription_id: string; schedule: Record<string, any> }): Promise<MedicationReminderItem> => {
    return request<MedicationReminderItem>('/api/v1/engagement/reminders', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },
  listMedicationReminders: async (): Promise<MedicationReminderItem[]> => {
    return request<MedicationReminderItem[]>('/api/v1/engagement/reminders/me');
  },
};

export const adminApi = {
  createDoctor: async (payload: { name: string; email: string; password: string; specialization: string; slot_duration_minutes?: number; consultation_fee?: number }): Promise<DoctorProfile> => {
    return request<DoctorProfile>('/api/v1/admin/doctors', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },
  updateDoctor: async (doctorId: string, payload: Partial<DoctorProfile>): Promise<DoctorProfile> => {
    return request<DoctorProfile>(`/api/v1/admin/doctors/${doctorId}`, {
      method: 'PUT',
      body: JSON.stringify(payload),
    });
  },
  listDoctors: async (): Promise<DoctorProfile[]> => {
    return request<DoctorProfile[]>('/api/v1/admin/doctors');
  },
  setDoctorWorkingHours: async (doctorId: string, workingHours: WorkingHour[]): Promise<WorkingHour[]> => {
    return request<WorkingHour[]>(`/api/v1/admin/doctors/${doctorId}/working-hours`, {
      method: 'POST',
      body: JSON.stringify({ working_hours: workingHours }),
    });
  },
  createLeave: async (payload: { doctor_id: string; leave_date: string; end_date?: string; reason?: string }): Promise<DoctorLeaveItem> => {
    return request<DoctorLeaveItem>('/api/v1/admin/leaves', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },
  listLeaves: async (doctorId?: string): Promise<DoctorLeaveItem[]> => {
    const qs = doctorId ? `?doctor_id=${encodeURIComponent(doctorId)}` : '';
    return request<DoctorLeaveItem[]>(`/api/v1/admin/leaves${qs}`);
  },
  removeLeave: async (leaveId: string): Promise<DoctorLeaveItem> => {
    return request<DoctorLeaveItem>(`/api/v1/admin/leaves/${leaveId}`, {
      method: 'DELETE',
    });
  },
};

export const api = {
  getHealth: healthApi.getHealth,
};

export default {
  auth: authApi,
  doctor: doctorApi,
  appointment: appointmentApi,
  clinical: clinicalApi,
  engagement: engagementApi,
  admin: adminApi,
  health: healthApi,
};
