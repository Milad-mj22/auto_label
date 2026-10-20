from django.contrib import admin
from .models import SystemSetting


@admin.register(SystemSetting)
class SystemSettingAdmin(admin.ModelAdmin):
    list_display = ("key", "value", "is_secret", "updated_at")
    search_fields = ("key", "description")
    readonly_fields = ("updated_at",)