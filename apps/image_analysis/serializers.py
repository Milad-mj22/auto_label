from rest_framework import serializers
from .models import ImageAnalysis


class DefectSerializer(serializers.Serializer):
    name = serializers.CharField()
    description = serializers.CharField(allow_blank=True)
    confidence = serializers.FloatField(required=False, allow_null=True)


class AnalysisResultSerializer(serializers.ModelSerializer):
    defects = serializers.JSONField(source="defects_json", read_only=True)
    industry_name = serializers.CharField(source="industry.name", read_only=True)
    questions_remaining = serializers.SerializerMethodField()
    image_url = serializers.SerializerMethodField()

    class Meta:
        model = ImageAnalysis
        fields = (
            "request_id", "industry_name", "status", "summary", "defects",
            "questions_used", "questions_remaining", "created_at",
            "completed_at", "image_url", "error_message",
        )

    def get_questions_remaining(self, obj):
        from apps.settings_app.services import get_default_question_limit
        return max(0, get_default_question_limit() - obj.questions_used)

    def get_image_url(self, obj):
        if not obj.image:
            return None
        request = self.context.get("request")
        url = obj.image.url
        return request.build_absolute_uri(url) if request else url