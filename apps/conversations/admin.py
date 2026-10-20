from django.contrib import admin
from .models import AnalysisConversation, ConversationMessage


class MessageInline(admin.TabularInline):
    model = ConversationMessage
    extra = 0
    readonly_fields = ("role", "content", "created_at")
    can_delete = False


@admin.register(AnalysisConversation)
class AnalysisConversationAdmin(admin.ModelAdmin):
    list_display = ("id", "analysis", "created_at")
    inlines = [MessageInline]