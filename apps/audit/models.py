from django.conf import settings
from django.db import models


class AuditLog(models.Model):
    class Action(models.TextChoices):
        QUOTA_INCREASE = "quota_increase", "افزایش سهمیه"
        QUOTA_RESET = "quota_reset", "بازنشانی سهمیه"
        ACCESS_BLOCK = "access_block", "مسدودسازی دسترسی"
        ACCESS_UNBLOCK = "access_unblock", "فعال‌سازی دسترسی"
        SETTING_CHANGE = "setting_change", "تغییر تنظیمات"
        PROMPT_CHANGE = "prompt_change", "تغییر پرامپت"
        LOGIN = "login", "ورود"
        OTHER = "other", "سایر"

    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, verbose_name="کاربر ادمین",
    )
    action = models.CharField(max_length=32, choices=Action.choices, verbose_name="نوع رخداد")
    target_type = models.CharField(max_length=64, blank=True, verbose_name="نوع هدف")
    target_id = models.CharField(max_length=64, blank=True, verbose_name="شناسه هدف")
    detail = models.JSONField(default=dict, blank=True, verbose_name="جزئیات")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="زمان")

    class Meta:
        verbose_name = "رخداد مدیریتی"
        verbose_name_plural = "رخدادهای مدیریتی"
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["action", "created_at"])]

    def __str__(self) -> str:
        return f"{self.get_action_display()} @ {self.created_at:%Y-%m-%d %H:%M}"


def log_action(actor, action, target_type="", target_id="", detail=None):
    return AuditLog.objects.create(
        actor=actor if getattr(actor, "pk", None) else None,
        action=action,
        target_type=target_type,
        target_id=str(target_id),
        detail=detail or {},
    )