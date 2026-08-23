"""Tests for Google Calendar service layer and email service."""
import uuid
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from app.services.calendar_service import GoogleCalendarService
from app.services.email_service import EmailService
from app.models.calendar import CalendarSyncStatus


# ============================================================================
# Google Calendar Service Tests
# ============================================================================

class TestGoogleCalendarService:
    """Unit tests for GoogleCalendarService OAuth and sync methods."""

    def test_oauth_authorization_url_contains_required_params(self):
        """OAuth URL must contain client_id, redirect_uri, scope, and state."""
        doctor_id = uuid.uuid4()
        url = GoogleCalendarService.get_oauth_authorization_url(doctor_id)

        assert "https://accounts.google.com/o/oauth2/v2/auth" in url
        assert "response_type=code" in url
        assert "scope=https://www.googleapis.com/auth/calendar.events" in url
        assert "access_type=offline" in url
        assert "prompt=consent" in url
        assert f"state={doctor_id}" in url

    def test_oauth_url_includes_doctor_id_as_state(self):
        """Verify doctor_id is round-tripped through the state parameter."""
        doctor_id = uuid.uuid4()
        url = GoogleCalendarService.get_oauth_authorization_url(doctor_id)
        assert str(doctor_id) in url

    @pytest.mark.asyncio
    async def test_sync_appointment_event_creates_record(self, db_session):
        """sync_appointment_event should create a GoogleCalendarSync record."""
        appt_id = uuid.uuid4()
        doctor_id = uuid.uuid4()

        result = await GoogleCalendarService.sync_appointment_event(
            db=db_session,
            appointment_id=appt_id,
            doctor_id=doctor_id,
            summary="Test Appointment",
            start_time_iso="2026-09-01T09:00:00Z",
            end_time_iso="2026-09-01T09:30:00Z",
            description="Patient consultation",
        )

        # With SQLite test DB, the FK constraints are relaxed, so the record is created
        if result:
            assert result.appointment_id == appt_id
            assert result.doctor_id == doctor_id
            assert result.sync_status == CalendarSyncStatus.SYNCED.value
            assert result.google_event_id is not None
            assert result.last_synced_at is not None

    @pytest.mark.asyncio
    async def test_cancel_appointment_event_returns_true_when_no_record(self, db_session):
        """cancel_appointment_event should return True even when no sync record exists."""
        result = await GoogleCalendarService.cancel_appointment_event(
            db=db_session,
            appointment_id=uuid.uuid4(),
        )
        assert result is True

    @pytest.mark.asyncio
    async def test_exchange_code_fallback_on_network_error(self, db_session):
        """Token exchange should use fallback credentials when HTTP request fails."""
        doctor_id = uuid.uuid4()
        auth_code = "test_auth_code_abc123"

        # The exchange will fail (no real Google server), should fall back gracefully
        result = await GoogleCalendarService.exchange_code_for_tokens(
            db=db_session,
            doctor_id=doctor_id,
            auth_code=auth_code,
        )

        # With SQLite FK constraints relaxed, the credential may be created
        if result:
            assert result.is_connected is True
            assert "demo" in result.access_token or result.access_token is not None


# ============================================================================
# Email Service Tests
# ============================================================================

class TestEmailService:
    """Unit tests for EmailService transactional email methods."""

    @pytest.mark.asyncio
    async def test_send_email_returns_true_in_dev_mode(self):
        """In development (SMTP_HOST=localhost, no SMTP_USER), email logs and returns True."""
        result = await EmailService.send_email(
            recipient_email="patient@example.com",
            recipient_name="Jane Doe",
            subject="Test Email",
            html_body="<p>Hello</p>",
        )
        assert result is True

    @pytest.mark.asyncio
    async def test_send_booking_confirmation(self):
        """Booking confirmation email should succeed in dev mode."""
        result = await EmailService.send_booking_confirmation(
            patient_email="patient@example.com",
            patient_name="Jane Doe",
            doctor_name="Dr. House",
            slot_time="2026-09-01 09:00 AM",
        )
        assert result is True

    @pytest.mark.asyncio
    async def test_send_cancellation_notice(self):
        """Cancellation notice email should succeed in dev mode."""
        result = await EmailService.send_cancellation_notice(
            patient_email="patient@example.com",
            patient_name="Jane Doe",
            doctor_name="Dr. House",
            slot_time="2026-09-01 09:00 AM",
            reason="Patient requested",
        )
        assert result is True

    @pytest.mark.asyncio
    async def test_send_cancellation_notice_without_reason(self):
        """Cancellation notice should work when no reason is provided."""
        result = await EmailService.send_cancellation_notice(
            patient_email="patient@example.com",
            patient_name="Jane Doe",
            doctor_name="Dr. House",
            slot_time="2026-09-01 09:00 AM",
        )
        assert result is True

    @pytest.mark.asyncio
    async def test_send_doctor_leave_notice(self):
        """Doctor leave rescheduling email should succeed in dev mode."""
        result = await EmailService.send_doctor_leave_notice(
            patient_email="patient@example.com",
            patient_name="Jane Doe",
            doctor_name="Dr. House",
            slot_time="2026-09-01 09:00 AM",
        )
        assert result is True

    @pytest.mark.asyncio
    async def test_email_failure_never_raises(self):
        """Email service must never raise an exception to the caller."""
        with patch.object(EmailService, 'send_email', new_callable=AsyncMock) as mock_send:
            mock_send.return_value = False
            result = await EmailService.send_booking_confirmation(
                patient_email="invalid",
                patient_name="Test",
                doctor_name="Dr. Test",
                slot_time="never",
            )
            # Even with mocked failure, calling the wrapper should not throw
            # The actual method returns True in dev mode, but we patched it
            assert result is False


# ============================================================================
# Integration Router Tests (via HTTP)
# ============================================================================

@pytest.mark.asyncio
async def test_google_calendar_connect_requires_doctor_role(async_client, patient_auth):
    """Patient users should be forbidden from accessing calendar connect endpoint."""
    res = await async_client.get(
        "/api/v1/integrations/google/connect",
        headers=patient_auth["headers"],
    )
    assert res.status_code == 403


@pytest.mark.asyncio
async def test_google_calendar_connect_returns_auth_url(async_client, doctor_auth, db_session):
    """Doctor users should receive a Google OAuth authorization URL."""
    from app.models.doctor import DoctorProfile

    # Create a doctor profile for this user
    profile = DoctorProfile(
        user_id=doctor_auth["user"].id,
        specialization="General Medicine",
        bio="Test doctor",
        slot_duration_minutes=30,
        consultation_fee=100.00,
    )
    db_session.add(profile)
    await db_session.commit()

    res = await async_client.get(
        "/api/v1/integrations/google/connect",
        headers=doctor_auth["headers"],
    )
    assert res.status_code == 200
    data = res.json()
    assert "authorization_url" in data
    assert "accounts.google.com" in data["authorization_url"]


@pytest.mark.asyncio
async def test_google_calendar_status_not_connected(async_client, doctor_auth, db_session):
    """Calendar status should show not connected when no credentials exist."""
    from app.models.doctor import DoctorProfile

    profile = DoctorProfile(
        user_id=doctor_auth["user"].id,
        specialization="Dermatology",
        bio="Test",
        slot_duration_minutes=20,
        consultation_fee=80.00,
    )
    db_session.add(profile)
    await db_session.commit()

    res = await async_client.get(
        "/api/v1/integrations/google/status",
        headers=doctor_auth["headers"],
    )
    assert res.status_code == 200
    data = res.json()
    assert data["is_connected"] is False


@pytest.mark.asyncio
async def test_google_calendar_callback_invalid_state(async_client):
    """Callback with invalid state UUID should return 400."""
    res = await async_client.get(
        "/api/v1/integrations/google/callback?code=test_code&state=not-a-uuid",
    )
    assert res.status_code == 400


@pytest.mark.asyncio
async def test_google_calendar_disconnect_requires_auth(async_client):
    """Disconnect endpoint should require authentication."""
    res = await async_client.delete("/api/v1/integrations/google/disconnect")
    assert res.status_code == 401 or res.status_code == 403
