from django.contrib import admin
from .models import ImageAnalysis, PromptConfiguration


@admin.register(PromptConfiguration)
class PromptConfigurationAdmin(admin.ModelAdmin):
    list_display = ("name", "industry", "version", "is_active", "created_at")
    list_filter = ("is_active", "industry")
    search_fields = ("name",)


@admin.register(ImageAnalysis)
class ImageAnalysisAdmin(admin.ModelAdmin):
    list_display = ("request_id", "phone_display", "industry", "status",
                    "questions_used", "created_at", "completed_at")
    list_filter = ("status", "industry")
    search_fields = ("identity__phone", "request_id")
    readonly_fields = ("request_id", "identity", "industry", "image", "prompt_used",
                       "summary", "defects_json", "raw_response", "created_at",
                       "completed_at")

    @admin.display(description="شماره")
    def phone_display(self, obj):
        return obj.identity.phone