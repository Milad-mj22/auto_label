from rest_framework import serializers
from .models import ConversationMessage


class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ConversationMessage
        fields = ("id", "role", "content", "created_at")


class AskSerializer(serializers.Serializer):
    request_id = serializers.UUIDField()
    question = serializers.CharField(max_length=1000)