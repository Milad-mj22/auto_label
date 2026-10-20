from django.test import TestCase

# Create your tests here.
import pytest
from apps.users.models import UserIdentity
from apps.verification.models import OtpVerification
from apps.verification.services import request_otp, verify_otp, OtpError
from django.conf import settings


@pytest.fixture
def mock_sms(monkeypatch):
    sent = {}
    def fake_send(phone, code):
        sent["phone"] = phone
        sent["code"] = code
    monkeypatch.setattr("apps.sms_services.providers.ConsoleSmsService.send_otp", fake_send)
    return sent


@pytest.mark.django_db
def test_request_and_verify_otp(mock_sms):
    phone = request_otp("+989121234567")
    assert phone == "09121234567"
    otp = OtpVerification.objects.filter(phone=phone).last()
    assert otp is not None
    identity = verify_otp("09121234567", mock_sms["code"])
    assert identity.is_verified
    assert UserIdentity.objects.filter(phone=phone, is_verified=True).exists()


@pytest.mark.django_db
def test_wrong_otp_increments_attempts(mock_sms):
    request_otp("09121234567")
    with pytest.raises(OtpError):
        verify_otp("09121234567", "000000")
    otp = OtpVerification.objects.get(phone="09121234567")
    assert otp.attempts == 1


@pytest.mark.django_db
def test_otp_used_once(mock_sms):
    request_otp("09121234567")
    code = mock_sms["code"]
    verify_otp("09121234567", code)
    with pytest.raises(OtpError):
        verify_otp("09121234567", code)