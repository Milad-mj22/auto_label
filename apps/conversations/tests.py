from django.test import TestCase

# Create your tests here.
import pytest
from apps.users.models import UserIdentity
from apps.industries.models import Industry
from apps.image_analysis.models import ImageAnalysis
from apps.conversations.services import ask_question, ConversationError


@pytest.fixture
def analysis(db):
    identity = UserIdentity.objects.create(phone="09120000099", is_verified=True)
    industry = Industry.objects.create(name="فلزات")
    a = ImageAnalysis.objects.create(
        identity=identity, industry=industry, status=ImageAnalysis.Status.SUCCESS,
        summary="نتیجه تست", defects_json=[],
    )
    return a


@pytest.mark.django_db
def test_question_limit_enforced(analysis, monkeypatch):
    monkeypatch.setattr(
        "apps.ai_services.providers.MockAIProvider.answer_question",
        lambda self, path, ctx, q: "پاسخ تست",
    )
    monkeypatch.setattr("apps.ai_services.providers.get_ai_provider",
                        lambda: __import__("apps.ai_services.providers", fromlist=["MockAIProvider"]).MockAIProvider())
    for i in range(5):
        ask_question(analysis, f"سوال {i}")
    with pytest.raises(ConversationError):
        ask_question(analysis, "سوال ششم")