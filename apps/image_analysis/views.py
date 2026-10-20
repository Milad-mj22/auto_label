from django.db import transaction
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from rest_framework import status
from rest_framework.throttling import AnonRateThrottle

from apps.users.models import UserIdentity
from apps.users.utils import normalize_phone
from apps.industries.models import Industry
from .validators import validate_image_file
from .services import run_analysis, AnalysisError
from .serializers import AnalysisResultSerializer
from django.core.exceptions import ValidationError


class AnalyzeThrottle(AnonRateThrottle):
    scope = "analyze"


class AnalyzeImageView(APIView):
    """
    multipart/form-data:
      phone, industry_id, image, request_id (اختیاری برای idempotency سبک)
    """
    parser_classes = [MultiPartParser, FormParser]
    throttle_classes = [AnalyzeThrottle]

    def post(self, request):
        raw_phone = request.data.get("phone", "")
        industry_id = request.data.get("industry_id")
        image = request.FILES.get("image")
        client_request_id = request.data.get("request_id")

        if not image:
            return Response({"detail": "تصویر ارسال نشده است."}, status=400)
        if not industry_id:
            return Response({"detail": "صنعت انتخاب نشده است."}, status=400)

        try:
            phone = normalize_phone(raw_phone)
        except ValueError as e:
            return Response({"detail": str(e)}, status=400)

        identity = UserIdentity.objects.filter(phone=phone, is_verified=True).first()
        if not identity:
            return Response({"detail": "شماره تأیید نشده است."}, status=403)

        industry = Industry.objects.filter(pk=industry_id, is_active=True).first()
        if not industry:
            return Response({"detail": "صنعت نامعتبر است."}, status=400)

        try:
            validate_image_file(image)
        except ValidationError as e:
            return Response({"detail": e.messages[0]}, status=400)

        # idempotency سبک: اگر request_id تکرار شود و تحلیل موجود باشد، همان برگردانده می‌شود.
        if client_request_id:
            from .models import ImageAnalysis
            existing = ImageAnalysis.objects.filter(request_id=client_request_id).first()
            if existing:
                return Response(AnalysisResultSerializer(existing, context={"request": request}).data)

        try:
            analysis = run_analysis(identity, industry, image)
        except AnalysisError as e:
            return Response({"detail": str(e)}, status=status.HTTP_409_CONFLICT)

        return Response(
            AnalysisResultSerializer(analysis, context={"request": request}).data,
            status=status.HTTP_201_CREATED,
        )