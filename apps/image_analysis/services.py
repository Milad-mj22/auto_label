import logging
from django.db import transaction
from django.utils import timezone

from apps.users.models import UserIdentity
from apps.industries.models import Industry
from apps.quota.services import reserve_quota, commit_quota, QuotaError
from apps.ai_services.providers import get_ai_provider, AIProviderError
from apps.audit.models import log_action, AuditLog
from .models import ImageAnalysis
from .prompts import get_active_prompt

logger = logging.getLogger(__name__)


class AnalysisError(Exception):
    pass


def run_analysis(identity: UserIdentity, industry: Industry, image_file, request_id=None) -> ImageAnalysis:
    """
    ۱. ساخت رکورد تحلیل
    ۲. رزرو اتمیک سهمیه
    ۳. فراخوانی AI
    ۴. commit موفق/ناموفق
    در صورت خطا سهمیه آزاد می‌شود.
    """
    if not identity.is_verified:
        raise AnalysisError("شماره تلفن تأیید نشده است.")

    prompt = get_active_prompt(industry)

    analysis = ImageAnalysis.objects.create(
        identity=identity,
        industry=industry,
        image=image_file,
        status=ImageAnalysis.Status.PENDING,
        prompt_used=prompt,
    )

    try:
        reserve_quota(identity)
    except QuotaError as e:
        analysis.status = ImageAnalysis.Status.FAILED
        analysis.error_message = str(e)
        analysis.save(update_fields=["status", "error_message"])
        raise AnalysisError(str(e))

    analysis.status = ImageAnalysis.Status.PROCESSING
    analysis.save(update_fields=["status"])

    try:
        provider = get_ai_provider()
        result = provider.analyze_image(
            image_path=analysis.image.path,
            prompt=prompt,
            industry=industry.name,
        )
        analysis.summary = result.summary
        analysis.defects_json = [
            {"name": d.name, "description": d.description, "confidence": d.confidence}
            for d in result.defects
        ]
        analysis.raw_response = result.raw_text
        analysis.status = ImageAnalysis.Status.SUCCESS
        analysis.completed_at = timezone.now()
        analysis.save()
        commit_quota(identity, success=True)
        return analysis
    except (AIProviderError, Exception) as e:
        logger.exception("Analysis failed for request %s", analysis.request_id)
        analysis.status = ImageAnalysis.Status.FAILED
        analysis.error_message = str(e) if isinstance(e, AIProviderError) else "خطای داخلی پردازش تحلیل."
        analysis.completed_at = timezone.now()
        analysis.save(update_fields=["status", "error_message", "completed_at"])
        commit_quota(identity, success=False)
        raise AnalysisError("تحلیل تصویر با خطا مواجه شد. سهمیه مصرف نشد.")