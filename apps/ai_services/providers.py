import base64
import json
import logging
import mimetypes
import requests
from django.conf import settings

from .base import AIProvider, AnalysisResult, DefectItem, AIProviderError

logger = logging.getLogger(__name__)


def _encode_image(path: str) -> tuple[str, str]:
    mime, _ = mimetypes.guess_type(path)
    mime = mime or "image/jpeg"
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode("ascii"), mime


class MockAIProvider(AIProvider):
    """فقط برای توسعه/آزمون. هیچ فراخوانی شبکه‌ای انجام نمی‌دهد."""

    def analyze_image(self, image_path: str, prompt: str, industry: str) -> AnalysisResult:
        return AnalysisResult(
            summary=f"[MOCK] تحلیل نمایشی برای صنعت «{industry}». نتیجه واقعی نیست.",
            defects=[
                DefectItem(name="خراش سطحی", description="[MOCK] نشانه‌های خطی روی سطح.", confidence=0.5),
            ],
            raw_text="mock",
        )

    def answer_question(self, image_path: str, context: str, question: str) -> str:
        return f"[MOCK] پاسخ نمایشی به: {question}"


class OpenAIVisionProvider(AIProvider):
    def __init__(self):
        if not settings.OPENAI_API_KEY:
            raise AIProviderError("OPENAI_API_KEY تنظیم نشده است.")
        self.api_key = settings.OPENAI_API_KEY
        self.model = settings.OPENAI_MODEL
        self.base_url = settings.OPENAI_BASE_URL.rstrip("/")

    def _chat(self, messages: list[dict], max_tokens: int = 900) -> str:
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.2,
            "max_tokens": max_tokens,
        }
        try:
            r = requests.post(
                f"{self.base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json",
                },
                json=payload,
                timeout=60,
            )
        except requests.RequestException as e:
            logger.exception("AI request failed")
            raise AIProviderError("ارتباط با سرویس هوش مصنوعی برقرار نشد.") from e

        if r.status_code >= 400:
            logger.error("AI provider error %s: %s", r.status_code, r.text[:500])
            raise AIProviderError("سرویس هوش مصنوعی خطا برگرداند.")

        try:
            return r.json()["choices"][0]["message"]["content"]
        except (KeyError, IndexError, ValueError) as e:
            raise AIProviderError("خروجی سرویس هوش مصنوعی نامعتبر بود.") from e

    def analyze_image(self, image_path: str, prompt: str, industry: str) -> AnalysisResult:
        b64, mime = _encode_image(image_path)
        messages = [
            {
                "role": "system",
                "content": (
                    "تو یک دستیار تحلیل تصویر صنعتی هستی. فقط بر اساس تصویر پاسخ بده. "
                    "خروجی را به‌صورت JSON با کلیدهای 'summary' و 'defects' (آرایه‌ای از "
                    "{'name','description','confidence'}) برگردان. "
                    "مهم: این تحلیل صرفاً نمایشی و ارزیابی اولیه است و نباید ادعای دقت صنعتی تأییدشده کند."
                ),
            },
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": f"صنعت: {industry}\n{prompt}"},
                    {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{b64}"}},
                ],
            },
        ]
        raw = self._chat(messages)
        return self._parse_analysis(raw)

    def answer_question(self, image_path: str, context: str, question: str) -> str:
        b64, mime = _encode_image(image_path)
        messages = [
            {
                "role": "system",
                "content": (
                    "تو دستیار تحلیل تصویر صنعتی هستی و باید به پرسش کاربر درباره "
                    "همین تصویر پاسخ دهی. پاسخ را کوتاه، محتاطانه و به فارسی بده."
                ),
            },
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": f"زمینه تحلیل قبلی:\n{context}\n\nپرسش: {question}"},
                    {"type": "image_url", "image_url": {"url": f"data:{mime};base64,{b64}"}},
                ],
            },
        ]
        return self._chat(messages, max_tokens=500).strip()

    @staticmethod
    def _parse_analysis(raw: str) -> AnalysisResult:
        # مدل ممکن است JSON را در بلوک ``` قرار دهد
        text = raw.strip()
        if text.startswith("```"):
            text = text.strip("`")
            if text.lower().startswith("json"):
                text = text[4:]
            text = text.strip()
        try:
            data = json.loads(text)
            defects = [
                DefectItem(
                    name=str(d.get("name", "عیب نامشخص")),
                    description=str(d.get("description", "")),
                    confidence=float(d["confidence"]) if d.get("confidence") is not None else None,
                )
                for d in data.get("defects", [])
            ]
            return AnalysisResult(
                summary=str(data.get("summary", "")),
                defects=defects,
                raw_text=raw,
            )
        except (json.JSONDecodeError, TypeError, ValueError):
            # fallback: متن خام
            return AnalysisResult(summary=raw.strip()[:2000], defects=[], raw_text=raw)


def get_ai_provider() -> AIProvider:
    provider = (settings.AI_PROVIDER or "openai").lower()
    if provider == "mock":
        return MockAIProvider()
    return OpenAIVisionProvider()