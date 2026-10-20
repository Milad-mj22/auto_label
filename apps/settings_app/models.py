from django.db import models


class SystemSetting(models.Model):
    """key/value تنظیمات سامانه. مقادیر حساس در AuditLog/DB نگه داشته نمی‌شوند."""
    key = models.CharField(max_length=120, unique=True)
    value = models.TextField(blank=True)
    description = models.CharField(max_length=255, blank=True)
    is_secret = models.BooleanField(default=False, help_text="در UI نمایش داده نشود.")
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "تنظیم سامانه"
        verbose_name_plural = "تنظیمات سامانه"

    def __str__(self) -> str:
        return self.key

    @classmethod
    def get(cls, key: str, default: str = "") -> str:
        obj = cls.objects.filter(key=key).first()
        return obj.value if obj else default

    @classmethod
    def get_int(cls, key: str, default: int) -> int:
        try:
            return int(cls.get(key, str(default)))
        except (TypeError, ValueError):
            return default


# کلیدهای شناخته‌شده
KEY_MANAGEMENT_PHONE = "management_phone"
KEY_DEFAULT_IMAGE_QUOTA = "default_image_quota"
KEY_DEFAULT_QUESTION_LIMIT = "default_question_limit"
KEY_ACTIVE_PROMPT_ID = "active_prompt_id"
KEY_AI_PROVIDER = "ai_provider"
KEY_MAX_IMAGE_SIZE_MB = "max_image_size_mb"