from django.db import models
from apps.image_analysis.models import ImageAnalysis


class AnalysisConversation(models.Model):
    analysis = models.OneToOneField(
        ImageAnalysis, on_delete=models.CASCADE, related_name="conversation",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"Conversation<{self.analysis.request_id}>"


class ConversationMessage(models.Model):
    class Role(models.TextChoices):
        USER = "user", "کاربر"
        ASSISTANT = "assistant", "دستیار"

    conversation = models.ForeignKey(
        AnalysisConversation, on_delete=models.CASCADE, related_name="messages",
    )
    role = models.CharField(max_length=16, choices=Role.choices)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]
        indexes = [models.Index(fields=["conversation", "created_at"])]