from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.throttling import AnonRateThrottle

from apps.users.utils import normalize_phone
from .serializers import RequestOtpSerializer, VerifyOtpSerializer
from .services import request_otp, verify_otp, OtpError

class OtpRequestThrottle(AnonRateThrottle):
    scope = "otp_request"

class OtpVerifyThrottle(AnonRateThrottle):
    scope = "otp_verify"

class RequestOtpView(APIView):
    throttle_classes = [OtpRequestThrottle]
    authentication_classes = []  # <--- این خط اضافه شود (غیرفعال کردن CSRF برای این ویو)

    def post(self, request):
        s = RequestOtpSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        try:
            phone = request_otp(s.validated_data["phone"])
        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except OtpError as e:
            return Response({"detail": str(e)}, status=status.HTTP_429_TOO_MANY_REQUESTS)
        return Response({"detail": "کد تأیید ارسال شد.", "phone": phone})

class VerifyOtpView(APIView):
    throttle_classes = [OtpVerifyThrottle]
    authentication_classes = []  # <--- این خط اضافه شود

    def post(self, request):
        s = VerifyOtpSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        try:
            identity = verify_otp(s.validated_data["phone"], s.validated_data["code"])
        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except OtpError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response({
            "detail": "شماره تأیید شد.",
            "phone": identity.phone,
            "verified": True,
        })



from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from datetime import timedelta

from apps.users.models import UserIdentity
from apps.users.utils import normalize_phone

class CheckVerificationView(APIView):
    authentication_classes = []
    
    def get(self, request):
        raw_phone = request.query_params.get("phone", "")
        try:
            phone = normalize_phone(raw_phone)
        except ValueError:
            return Response({"verified": False}, status=status.HTTP_400_BAD_REQUEST)
        
        identity = UserIdentity.objects.filter(phone=phone, is_verified=True).first()
        if not identity or not identity.verified_at:
            return Response({"verified": False})
        
        # بررسی ۳۰ دقیقه‌ای
        if timezone.now() - identity.verified_at < timedelta(minutes=30):
            return Response({"verified": True, "phone": phone})
        
        return Response({"verified": False})