import logging
import secrets
from django.conf import settings
from django.db import transaction
from django.utils import timezone
from datetime import timedelta

from apps.users.utils import normalize_phone
from apps.users.models import UserIdentity
from apps.sms_services.providers import get_sms_service
from .models import OtpVerification

logger = logging.getLogger(__name__)


class OtpError(Exception):
    pass


def request_otp(raw_phone: str) -> str:
    phone = normalize_phone(raw_phone)
    one_hour_ago = timezone.now() - timedelta(hours=1)
    recent = OtpVerification.objects.filter(phone=phone, created_at__gte=one_hour_ago).count()
    if recent >= settings.OTP_MAX_SEND_PER_HOUR:
        raise OtpError("تعداد درخواست‌های کد تأیید بیش از حد مجاز است. بعداً تلاش کنید.")

    code = f"{secrets.randbelow(900000) + 100000}"
    OtpVerification.issue(phone, code)
    get_sms_service().send_otp(phone, code)
    return phone


def verify_otp(raw_phone: str, code: str) -> UserIdentity:
    phone = normalize_phone(raw_phone)
    otp = (
        OtpVerification.objects
        .filter(phone=phone, is_used=False)
        .order_by("-created_at")
        .first()
    )
    if not otp:
        raise OtpError("کد تأیید یافت نشد. لطفاً کد جدید دریافت کنید.")
    if otp.attempts >= settings.OTP_MAX_ATTEMPTS:
        raise OtpError("تعداد تلاش‌های ناموفق بیش از حد مجاز است.")
    with transaction.atomic():
        # قفل منطقی: از مصرف هم‌زمان یک OTP جلوگیری می‌شود
        OtpVerification.objects.select_for_update().filter(pk=otp.pk).exists()
        otp.refresh_from_db()
        if not otp.verify(code):
            raise OtpError("کد تأیید نامعتبر یا منقضی است.")
        identity, _ = UserIdentity.objects.get_or_create(phone=phone)
        if not identity.is_verified:
            identity.mark_verified()
    return identity