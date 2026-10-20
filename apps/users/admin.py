from django.contrib import admin
from .models import UserIdentity


@admin.register(UserIdentity)
class UserIdentityAdmin(admin.ModelAdmin):
    list_display = ("phone", "is_verified", "verified_at", "created_at")
    list_filter = ("is_verified",)
    search_fields = ("phone",)
    readonly_fields = ("phone", "created_at", "updated_at")