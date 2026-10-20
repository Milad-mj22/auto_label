from rest_framework import serializers
from .models import UsageQuota


class QuotaStatusSerializer(serializers.ModelSerializer):
    phone = serializers.CharField(source="identity.phone", read_only=True)
    remaining = serializers.IntegerField(read_only=True)
    can_use = serializers.BooleanField(read_only=True)

    class Meta:
        model = UsageQuota
        fields = ("phone", "total_quota", "used_count", "remaining", "can_use",
                  "is_blocked", "first_use_at", "last_use_at")