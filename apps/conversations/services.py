import logging
from django.db import transaction
from apps.image_analysis.models import ImageAnalysis
from apps.settings_app.services import get_default_question_limit
from apps.ai_services.providers import get_ai_provider, AIProviderError
from .models import AnalysisConversation, ConversationMessage

logger = logging.getLogger(__name__)


class ConversationError(Exception):
    pass


def get_or_create_conversation(analysis: ImageAnalysis) -> AnalysisConversation:
    conv, _ = AnalysisConversation.objects.get_or_create(analysis=analysis)
    return conv


def ask_question(analysis: ImageAnalysis, question: str) -> ConversationMessage:
    limit = get_default_question_limit()
    with transaction.atomic():
        # قفل روی تحلیل برای جلوگیری از عبور هم‌زمان از سقف
        locked = ImageAnalysis.objects.select_for_update().get(pk=analysis.pk)
        if locked.status != ImageAnalysis.Status.SUCCESS:
            raise ConversationError("این تحلیل کامل نشده و پرسش مجاز نیست.")
        if locked.questions_used >= limit:
            raise ConversationError(f"سقف {limit} پرسش برای این تصویر مصرف شده است.")

        conv = get_or_create_conversation(locked)
        ConversationMessage.objects.create(conversation=conv, role="user", content=question)
        locked.questions_used += 1
        locked.save(update_fields=["questions_used"])

    context = (
        f"صنعت: {analysis.industry.name}\n"
        f"خلاصه: {analysis.summary}\n"
        f"عیوب: {analysis.defects_json}"
    )
    try:
        provider = get_ai_provider()
        answer = provider.answer_question(
            image_path=analysis.image.path, context=context, question=question,
        )
    except AIProviderError:
        logger.exception("AI failed for question on %s", analysis.request_id)
        answer = "متأسفانه پاسخ‌گویی هوشمند در حال حاضر در دسترس نیست. لطفاً بعداً تلاش کنید."
    except Exception:
        logger.exception("Unexpected error for question")
        answer = "خطای داخلی در پاسخ‌گویی رخ داد."

    msg = ConversationMessage.objects.create(
        conversation=conv, role="assistant", content=answer,
    )
    return msg