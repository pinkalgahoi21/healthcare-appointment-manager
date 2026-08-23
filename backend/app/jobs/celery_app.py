"""Celery application and idempotent transactional-outbox dispatcher with background jobs."""
import asyncio
from datetime import datetime, timezone
import logging

from celery import Celery
from sqlalchemy import or_, select

from app.config import settings
from app.database import AsyncSessionLocal
from app.models.appointment import Appointment
from app.models.doctor import DoctorProfile
from app.models.engagement import MedicationReminder, Notification
from app.models.outbox_event import OutboxEvent, OutboxStatus
from app.models.user import User
from app.services.booking_service import BookingService
from app.services.calendar_service import GoogleCalendarService
from app.services.email_service import EmailService

logger = logging.getLogger("healthcare_manager.celery")

celery_app = Celery(
    "healthcare_manager",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["app.jobs.celery_app"],
)

celery_app.conf.update(
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    task_track_started=True,
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
)


@celery_app.task(name="healthcare.health_ping")
def health_ping() -> dict:
    return {"status": "ok"}


async def _handle_single_outbox_event(session, event: OutboxEvent):
    """Dispatches asynchronous external side-effects (Email, Google Calendar, Notifications)."""
    payload = event.payload or {}
    event_type = event.event_type

    if event_type == "APPOINTMENT_CONFIRMED":
        appointment_id = payload.get("appointment_id")
        if appointment_id:
            # Query appointment details for notification and email
            appt = (await session.execute(
                select(Appointment).where(Appointment.id == appointment_id)
            )).scalar_one_or_none()
            if appt:
                patient = (await session.execute(select(User).where(User.id == appt.patient_id))).scalar_one_or_none()
                doctor = (await session.execute(select(DoctorProfile).where(DoctorProfile.id == appt.doctor_id))).scalar_one_or_none()
                doc_user = (await session.execute(select(User).where(User.id == doctor.user_id))).scalar_one_or_none() if doctor else None

                doc_name = doc_user.name if doc_user else "Doctor"
                if patient:
                    # In-app notification
                    session.add(Notification(
                        user_id=patient.id,
                        type="APPOINTMENT_CONFIRMED",
                        title="Appointment Confirmed",
                        body=f"Your appointment with Dr. {doc_name} is confirmed.",
                        data={"appointment_id": str(appt.id)},
                    ))
                    # Asynchronous Email
                    await EmailService.send_booking_confirmation(
                        patient_email=patient.email,
                        patient_name=patient.name,
                        doctor_name=f"Dr. {doc_name}",
                        slot_time=str(appt.booked_at or "Scheduled Time"),
                    )
                # Google Calendar sync
                if doctor:
                    await GoogleCalendarService.sync_appointment_event(
                        db=session,
                        appointment_id=appt.id,
                        doctor_id=doctor.id,
                        summary=f"Consultation: {patient.name if patient else 'Patient'}",
                        start_time_iso=str(appt.booked_at or datetime.now(timezone.utc).isoformat()),
                        end_time_iso=str(appt.booked_at or datetime.now(timezone.utc).isoformat()),
                    )

    elif event_type == "APPOINTMENT_CANCELLED":
        appointment_id = payload.get("appointment_id")
        if appointment_id:
            appt = (await session.execute(
                select(Appointment).where(Appointment.id == appointment_id)
            )).scalar_one_or_none()
            if appt:
                patient = (await session.execute(select(User).where(User.id == appt.patient_id))).scalar_one_or_none()
                if patient:
                    session.add(Notification(
                        user_id=patient.id,
                        type="APPOINTMENT_CANCELLED",
                        title="Appointment Cancelled",
                        body="Your appointment has been cancelled.",
                        data={"appointment_id": str(appt.id)},
                    ))
                    await EmailService.send_cancellation_notice(
                        patient_email=patient.email,
                        patient_name=patient.name,
                        doctor_name="Doctor",
                        slot_time="Scheduled Time",
                        reason=appt.cancellation_reason,
                    )
                await GoogleCalendarService.cancel_appointment_event(session, appt.id)

    elif event_type == "APPOINTMENT_RESCHEDULE_REQUIRED":
        appointment_id = payload.get("appointment_id")
        if appointment_id:
            appt = (await session.execute(
                select(Appointment).where(Appointment.id == appointment_id)
            )).scalar_one_or_none()
            if appt:
                patient = (await session.execute(select(User).where(User.id == appt.patient_id))).scalar_one_or_none()
                if patient:
                    session.add(Notification(
                        user_id=patient.id,
                        type="RESCHEDULE_REQUIRED",
                        title="Reschedule Required",
                        body="Your appointment requires rescheduling due to doctor availability.",
                        data={"appointment_id": str(appt.id)},
                    ))
                    await EmailService.send_doctor_leave_notice(
                        patient_email=patient.email,
                        patient_name=patient.name,
                        doctor_name="Doctor",
                        slot_time="Scheduled Time",
                    )
                await GoogleCalendarService.cancel_appointment_event(session, appt.id)


async def _process_pending_events(limit: int) -> int:
    now = datetime.now(timezone.utc)
    async with AsyncSessionLocal() as session:
        events = (await session.execute(
            select(OutboxEvent)
            .where(
                OutboxEvent.status == OutboxStatus.PENDING.value,
                or_(OutboxEvent.next_attempt_at.is_(None), OutboxEvent.next_attempt_at <= now),
            )
            .order_by(OutboxEvent.created_at)
            .limit(limit)
            .with_for_update(skip_locked=True)
        )).scalars().all()

        for event in events:
            try:
                await _handle_single_outbox_event(session, event)
                event.status = OutboxStatus.PROCESSED.value
                event.processed_at = now
                event.error = None
            except Exception as exc:
                logger.error(f"[OUTBOX] Event {event.id} processing failed: {exc}")
                event.retry_count += 1
                event.error = str(exc)
                if event.retry_count >= 5:
                    event.status = OutboxStatus.FAILED.value
                else:
                    event.next_attempt_at = now
        await session.commit()
        return len(events)


@celery_app.task(
    bind=True,
    name="healthcare.process_outbox",
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_jitter=True,
    retry_kwargs={"max_retries": 5},
)
def process_outbox(self, limit: int = 100) -> int:
    return asyncio.run(_process_pending_events(limit))


@celery_app.task(name="healthcare.sweep_expired_holds")
def sweep_expired_holds() -> int:
    """Periodic task that sweeps and releases expired slot holds."""
    async def _sweep():
        async with AsyncSessionLocal() as session:
            return await BookingService.release_expired_holds(session)
    return asyncio.run(_sweep())
