from django.db import models


class Industry(models.Model):
    name = models.CharField(max_length=120, unique=True, verbose_name="نام صنعت")
    description = models.TextField(blank=True, verbose_name="توضیحات")
    is_active = models.BooleanField(default=True, verbose_name="فعال")
    display_order = models.PositiveIntegerField(default=0, verbose_name="ترتیب نمایش")
    custom_prompt = models.TextField(
        blank=True,
        verbose_name="پرامپت اختصاصی (اختیاری)",
        help_text="در صورت خالی بودن، پرامپت عمومی استفاده می‌شود.",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "صنعت"
        verbose_name_plural = "صنایع"
        ordering = ["display_order", "name"]

    def __str__(self) -> str:
        return self.name