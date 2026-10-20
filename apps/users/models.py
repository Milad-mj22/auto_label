from django.db import models
from django.utils import timezone


class UserIdentity(models.Model):
    phone = models.CharField(max_length=11, unique=True, verbose_name="شماره موبایل استاندارد")
    is_verified = models.BooleanField(default=False, verbose_name="تأیید پیامکی شده")
    verified_at = models.DateTimeField(null=True, blank=True, verbose_name="زمان تأیید")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "هویت شماره موبایل"
        verbose_name_plural = "هویت‌های شماره موبایل"
        indexes = [models.Index(fields=["phone"])]

    def __str__(self) -> str:
        return self.phone

    def mark_verified(self):
        self.is_verified = True
        self.verified_at = timezone.now()
        self.save(update_fields=["is_verified", "verified_at", "updated_at"])