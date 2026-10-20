from django.db import models
from apps.users.models import UserIdentity


class UsageQuota(models.Model):
    identity = models.OneToOneField(
        UserIdentity, on_delete=models.CASCADE, related_name="quota",
        verbose_name="هویت",
    )
    total_quota = models.PositiveIntegerField(default=5, verbose_name="سهمیه کل")
    used_count = models.PositiveIntegerField(default=0, verbose_name="تصاویر مصرف‌شده")
    reserved_count = models.PositiveIntegerField(default=0, verbose_name="رزرو شده (در حال پردازش)")
    is_blocked = models.BooleanField(default=False, verbose_name="مسدود")
    first_use_at = models.DateTimeField(null=True, blank=True, verbose_name="اولین استفاده")
    last_use_at = models.DateTimeField(null=True, blank=True, verbose_name="آخرین استفاده")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "سهمیه شماره"
        verbose_name_plural = "سهمیه شماره‌ها"
        constraints = [
            models.CheckConstraint(
                check=models.Q(used_count__gte=0),
                name="used_count_non_negative",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.identity.phone}: {self.used_count}/{self.total_quota}"

    @property
    def remaining(self) -> int:
        return max(0, self.total_quota - self.used_count - self.reserved_count)

    @property
    def can_use(self) -> bool:
        return not self.is_blocked and self.remaining > 0