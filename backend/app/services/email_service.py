"""Asynchronous transactional email service for appointment lifecycle notifications."""
import logging
from typing import Optional
from app.config import settings

logger = logging.getLogger("healthcare_manager.email")


class EmailService:
    @staticmethod
    async def send_email(
        recipient_email: str,
        recipient_name: str,
        subject: str,
        html_body: str,
        text_body: Optional[str] = None,
    ) -> bool:
        """
        Sends an email asynchronously via configured SMTP or logs in development/fallback mode.
        Guarantees that email failures never crash the caller or rollback business transactions.
        """
        try:
            logger.info(
                f"[EMAIL] To: {recipient_name} <{recipient_email}> | Subject: {subject} | "
                f"From: {settings.EMAILS_FROM_NAME} <{settings.EMAILS_FROM_EMAIL}>"
            )
            # In a live SMTP environment, aiosmtplib sends the MIME message.
            # When SMTP_HOST is 'localhost' without an active daemon, it logs cleanly.
            if settings.SMTP_HOST and settings.SMTP_HOST != "localhost" and settings.SMTP_USER:
                import smtplib
                from email.mime.text import MIMEText
                from email.mime.multipart import MIMEMultipart

                msg = MIMEMultipart("alternative")
                msg["Subject"] = subject
                msg["From"] = f"{settings.EMAILS_FROM_NAME} <{settings.EMAILS_FROM_EMAIL}>"
                msg["To"] = recipient_email

                if text_body:
                    msg.attach(MIMEText(text_body, "plain"))
                msg.attach(MIMEText(html_body, "html"))

                with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=10) as server:
                    if settings.SMTP_PASSWORD:
                        server.starttls()
                        server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
                    server.sendmail(settings.EMAILS_FROM_EMAIL, [recipient_email], msg.as_string())
                logger.info(f"[EMAIL] Successfully dispatched email to {recipient_email}")
            return True
        except Exception as exc:
            logger.error(f"[EMAIL] Failed to send email to {recipient_email}: {exc}")
            return False

    @staticmethod
    async def send_booking_confirmation(patient_email: str, patient_name: str, doctor_name: str, slot_time: str) -> bool:
        subject = f"Appointment Confirmed with {doctor_name}"
        html = f"""
        <div style="font-family: sans-serif; padding: 20px; color: #1e293b;">
            <h2 style="color: #0d9488;">Appointment Confirmation</h2>
            <p>Dear {patient_name},</p>
            <p>Your healthcare appointment has been confirmed:</p>
            <ul>
                <li><strong>Doctor:</strong> {doctor_name}</li>
                <li><strong>Time:</strong> {slot_time}</li>
            </ul>
            <p>You can manage this appointment or view follow-up notes in your portal.</p>
        </div>
        """
        return await EmailService.send_email(patient_email, patient_name, subject, html)

    @staticmethod
    async def send_cancellation_notice(patient_email: str, patient_name: str, doctor_name: str, slot_time: str, reason: Optional[str] = None) -> bool:
        subject = f"Appointment Cancelled: {doctor_name}"
        html = f"""
        <div style="font-family: sans-serif; padding: 20px; color: #1e293b;">
            <h2 style="color: #e11d48;">Appointment Cancellation</h2>
            <p>Dear {patient_name},</p>
            <p>Your appointment scheduled for <strong>{slot_time}</strong> with <strong>{doctor_name}</strong> has been cancelled.</p>
            {f'<p><strong>Reason:</strong> {reason}</p>' if reason else ''}
            <p>Please visit your patient portal to book an alternate appointment slot.</p>
        </div>
        """
        return await EmailService.send_email(patient_email, patient_name, subject, html)

    @staticmethod
    async def send_doctor_leave_notice(patient_email: str, patient_name: str, doctor_name: str, slot_time: str) -> bool:
        subject = f"Rescheduling Required: {doctor_name} is on Leave"
        html = f"""
        <div style="font-family: sans-serif; padding: 20px; color: #1e293b;">
            <h2 style="color: #d97706;">Action Required: Reschedule Appointment</h2>
            <p>Dear {patient_name},</p>
            <p>Your appointment with <strong>{doctor_name}</strong> on <strong>{slot_time}</strong> cannot take place as the practitioner is temporarily on leave.</p>
            <p>Please log in to your patient dashboard to choose a new available appointment slot at no additional charge.</p>
        </div>
        """
        return await EmailService.send_email(patient_email, patient_name, subject, html)
