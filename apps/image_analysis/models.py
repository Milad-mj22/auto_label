import uuid
from django.db import models
from apps.users.models import UserIdentity
from apps.industries.models import Industry


def upload_to(instance, filename):
    return f"analysis/{instance.request_id}/{filename}"


class PromptConfiguration(models.Model):
    name = models.CharField(max_length=120, verbose_name="نام")
    general_prompt = models.TextField(verbose_name="پرامپت عمومی")
    industry = models.ForeignKey(
        Industry, null=True, blank=True, on_delete=models.SET_NULL,
        related_name="prompt_configs", verbose_name="صنعت اختصاصی",
    )
    version = models.PositiveIntegerField(default=1, verbose_name="نسخه")
    is_active = models.BooleanField(default=True, verbose_name="فعال")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "پرامپت تحلیل"
        verbose_name_plural = "پرامپت‌های تحلیل"
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["industry", "is_active"])]

    def __str__(self) -> str:
        return f"{self.name} (v{self.version})"


class ImageAnalysis(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "در انتظار"
        RESERVED = "reserved", "رزرو سهمیه"
        PROCESSING = "processing", "در حال پردازش"
        SUCCESS = "success", "موفق"
        FAILED = "failed", "ناموفق"

    request_id = models.UUIDField(default=uuid.uuid4, unique=True, editable=False, db_index=True)
    identity = models.ForeignKey(UserIdentity, on_delete=models.PROTECT, related_name="analyses")
    industry = models.ForeignKey(Industry, on_delete=models.PROTECT, related_name="analyses")
    image = models.ImageField(upload_to=upload_to, verbose_name="تصویر")
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.PENDING)
    prompt_used = models.TextField(blank=True)
    summary = models.TextField(blank=True)
    defects_json = models.JSONField(default=list, blank=True)
    raw_response = models.TextField(blank=True)
    error_message = models.TextField(blank=True)
    questions_used = models.PositiveIntegerField(default=0, verbose_name="پرسش مصرف‌شده")
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "تحلیل تصویر"
        verbose_name_plural = "تحلیل‌های تصویر"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["identity", "status"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self) -> str:
        return f"{self.request_id} - {self.identity.phone} - {self.status}"