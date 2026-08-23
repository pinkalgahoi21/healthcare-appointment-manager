export type UserRole = 'PATIENT' | 'DOCTOR' | 'ADMIN' | 'patient' | 'doctor' | 'admin';

export interface User {
  id: string;
  name: string;
  email: string;
  role: UserRole;
  is_active: boolean;
  created_at?: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: User;
}

export interface DoctorProfile {
  id: string;
  user_id: string;
  name: string;
  email: string;
  specialization: string;
  bio?: string;
  slot_duration_minutes: number;
  consultation_fee: number;
  is_active: boolean;
  working_hours?: WorkingHour[];
}

export interface WorkingHour {
  id?: string;
  day_of_week: number; // 0 = Mon, 6 = Sun
  start_time: string; // "09:00:00"
  end_time: string; // "17:00:00"
  is_active: boolean;
}

export interface AppointmentSlot {
  id: string;
  doctor_id: string;
  slot_date: string;
  start_time: string;
  end_time: string;
  status: 'available' | 'held' | 'booked' | 'unavailable';
  held_by_user_id?: string;
  held_until?: string;
}

export interface SlotHold {
  id: string;
  slot_id: string;
  patient_id: string;
  status: 'active' | 'expired' | 'released' | 'converted';
  expires_at: string;
  created_at: string;
}

export interface Appointment {
  id: string;
  patient_id: string;
  doctor_id: string;
  slot_id: string;
  status: 'held' | 'confirmed' | 'completed' | 'cancelled' | 'rescheduled_required';
  chief_complaint?: string;
  cancellation_reason?: string;
  booked_at?: string;
  confirmed_at?: string;
  completed_at?: string;
  cancelled_at?: string;
  created_at: string;
  doctor_name?: string;
  patient_name?: string;
  slot?: AppointmentSlot;
}

export interface ClinicalNote {
  id: string;
  appointment_id: string;
  doctor_id: string;
  content: string;
  created_at: string;
  updated_at: string;
}

export interface Prescription {
  id: string;
  appointment_id: string;
  patient_id: string;
  doctor_id: string;
  medication_name: string;
  dosage: string;
  frequency: string;
  instructions?: string;
  active: boolean;
  created_at: string;
}

export interface PreVisitSummary {
  urgency: 'LOW' | 'MEDIUM' | 'HIGH';
  chief_complaint: string;
  suggested_questions: string[];
  source: string;
  disclaimer: string;
}

export interface PostVisitSummary {
  id: string;
  appointment_id: string;
  doctor_id: string;
  content: {
    visit_explanation?: string;
    medication_schedule?: any[];
    follow_up_steps?: string;
    source?: string;
  };
  is_published: boolean;
  created_at: string;
  updated_at: string;
}

export interface NotificationItem {
  id: string;
  user_id: string;
  type: string;
  title: string;
  body: string;
  data: Record<string, any>;
  read_at?: string;
  created_at: string;
}

export interface MedicationReminderItem {
  id: string;
  patient_id: string;
  prescription_id: string;
  schedule: Record<string, any>;
  next_reminder_at?: string;
  is_active: boolean;
  created_at: string;
}

export interface DoctorLeaveItem {
  id: string;
  doctor_id: string;
  leave_date: string;
  end_date?: string;
  reason?: string;
  status: string;
  created_at: string;
}

export interface ServiceStatus {
  status: 'connected' | 'disconnected';
  latency_ms?: number;
  error?: string;
}

export interface HealthResponse {
  status: 'healthy' | 'degraded' | 'error';
  service: string;
  version: string;
  environment: string;
  timestamp: string;
  services: {
    database: ServiceStatus;
    redis: ServiceStatus;
  };
}
