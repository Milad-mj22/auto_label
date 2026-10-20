import secrets
from datetime import timedelta
from django.db import models
from django.utils import timezone
from django.conf import settings


class OtpVerification(models.Model):
    phone = models.CharField(max_length=11, db_index=True, verbose_name="شماره موبایل")
    code_hash = models.CharField(max_length=128, verbose_name="هش کد")
    expires_at = models.DateTimeField(verbose_name="انقضا")
    attempts = models.PositiveIntegerField(default=0, verbose_name="تلاش ناموفق")
    is_used = models.BooleanField(default=False, verbose_name="مصرف‌شده")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "کد تأیید"
        verbose_name_plural = "کدهای تأیید"
        indexes = [models.Index(fields=["phone", "is_used", "expires_at"])]

    @staticmethod
    def _hash(phone: str, code: str) -> str:
        import hashlib
        return hashlib.sha256(f"{phone}:{code}".encode()).hexdigest()

    @classmethod
    def issue(cls, phone: str, code: str, ttl_seconds: int = None) -> "OtpVerification":
        ttl = ttl_seconds or settings.OTP_TTL_SECONDS
        return cls.objects.create(
            phone=phone,
            code_hash=cls._hash(phone, code),
            expires_at=timezone.now() + timedelta(seconds=ttl),
        )

    def matches(self, code: str) -> bool:
        return not self.is_used and self.expires_at > timezone.now() and \
               self.code_hash == self._hash(self.phone, code)

    def verify(self, code: str) -> bool:
        if self.matches(code):
            self.is_used = True
            self.save(update_fields=["is_used"])
            return True
        self.attempts += 1
        self.save(update_fields=["attempts"])
        return False