from django.shortcuts import render

# Create your views here.
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from apps.users.models import UserIdentity
from apps.users.utils import normalize_phone
from .services import get_or_create_quota
from .serializers import QuotaStatusSerializer


class QuotaStatusView(APIView):
    """
    وضعیت سهمیه بر اساس شماره تلفن. برای جلوگیری از افشای اطلاعات،
    فقط شماره‌ای که در همین لحظه با OTP تأیید شده قابل استفاده است؛
    اما چون فرانت‌اند بعد از تأیید این را صدا می‌زند، وضعیت تأیید را بررسی می‌کنیم.
    """
    def get(self, request):
        raw = request.query_params.get("phone", "")
        try:
            phone = normalize_phone(raw)
        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        identity = UserIdentity.objects.filter(phone=phone, is_verified=True).first()
        if not identity:
            return Response(
                {"detail": "این شماره تأیید نشده است."},
                status=status.HTTP_403_FORBIDDEN,
            )
        quota = get_or_create_quota(identity)
        return Response(QuotaStatusSerializer(quota).data)