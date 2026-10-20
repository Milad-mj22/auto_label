from django import forms
from django.contrib import admin, messages

from .models import UsageQuota
from .services import admin_adjust_quota, QuotaError


class QuotaAdjustForm(forms.Form):
    new_total = forms.IntegerField(required=False, min_value=0, label="سهمیه جدید")
    reset_used = forms.BooleanField(required=False, label="بازنشانی مصرف")
    block = forms.NullBooleanField(required=False, label="مسدود")
    reason = forms.CharField(required=False, max_length=255, label="دلیل")


@admin.register(UsageQuota)
class UsageQuotaAdmin(admin.ModelAdmin):
    list_display = ("phone", "total_quota", "used_count", "reserved_count",
                    "remaining_display", "is_blocked", "last_use_at")
    search_fields = ("identity__phone",)
    list_filter = ("is_blocked",)
    readonly_fields = ("identity", "used_count", "reserved_count", "first_use_at",
                       "last_use_at", "created_at", "updated_at")
    actions = ["reset_used_count", "unblock"]

    @admin.display(description="باقی‌مانده")
    def phone(self, obj):
        return obj.identity.phone

    @admin.display(description="باقی‌مانده")
    def remaining_display(self, obj):
        return obj.remaining

    @admin.action(description="بازنشانی شمارنده مصرف")
    def reset_used_count(self, request, queryset):
        for q in queryset:
            try:
                admin_adjust_quota(q.identity, reset_used=True, actor=request.user,
                                   reason="reset via admin action")
            except QuotaError as e:
                messages.error(request, str(e))

    @admin.action(description="رفع مسدودی")
    def unblock(self, request, queryset):
        for q in queryset:
            admin_adjust_quota(q.identity, block=False, actor=request.user,
                               reason="unblock via admin action")