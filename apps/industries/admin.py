from django.contrib import admin
from .models import Industry


@admin.register(Industry)
class IndustryAdmin(admin.ModelAdmin):
    list_display = ("name", "is_active", "display_order", "updated_at")
    list_filter = ("is_active",)
    search_fields = ("name",)
    list_editable = ("is_active", "display_order")