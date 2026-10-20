from rest_framework.views import APIView
from rest_framework.response import Response
from .services import get_management_phone, get_default_question_limit


class PublicSettingsView(APIView):
    """تنظیمات عمومی که فرانت‌اند برای نمایش نیاز دارد."""
    def get(self, request):
        return Response({
            "management_phone": get_management_phone(),
            "question_limit": get_default_question_limit(),
        })