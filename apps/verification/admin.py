from django.contrib import admin
from .models import OtpVerification


@admin.register(OtpVerification)
class OtpVerificationAdmin(admin.ModelAdmin):
    list_display = ("phone", "is_used", "attempts", "expires_at", "created_at")
    list_filter = ("is_used",)
    search_fields = ("phone",)
    readonly_fields = ("phone", "code_hash", "expires_at", "attempts", "is_used", "created_at")