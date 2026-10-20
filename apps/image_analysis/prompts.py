from apps.industries.models import Industry
from .models import PromptConfiguration

DEFAULT_GENERAL_PROMPT = (
    "این تصویر یک سطح صنعتی است. عیوب سطحی احتمالی مانند خراش، ترک، حفره، "
    "زنگ‌زدگی، تغییر رنگ یا ناهمواری را بررسی کن. توضیح کوتاه و محتاطانه بده. "
    "این تحلیل صرفاً ارزیابی اولیه و نمایشی است."
)


def get_active_prompt(industry: Industry) -> str:
    # ۱) پرامپت اختصاصی خود صنعت
    if industry.custom_prompt.strip():
        return industry.custom_prompt.strip()
    # ۲) پرامپت فعال تنظیم‌شده برای صنعت
    p = (
        PromptConfiguration.objects
        .filter(industry=industry, is_active=True)
        .order_by("-version", "-created_at")
        .first()
    )
    if p:
        return p.general_prompt.strip()
    # ۳) پرامپت عمومی فعال
    p = (
        PromptConfiguration.objects
        .filter(industry__isnull=True, is_active=True)
        .order_by("-version", "-created_at")
        .first()
    )
    if p:
        return p.general_prompt.strip()
    return DEFAULT_GENERAL_PROMPT