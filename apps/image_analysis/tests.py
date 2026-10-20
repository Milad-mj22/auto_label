from django.test import TestCase

# Create your tests here.
import io
import pytest
from PIL import Image
from django.core.files.uploadedfile import SimpleUploadedFile

from apps.users.models import UserIdentity
from apps.industries.models import Industry
from apps.image_analysis.validators import validate_image_file
from apps.image_analysis.services import run_analysis
from apps.quota.models import UsageQuota
from django.core.exceptions import ValidationError


def _fake_png(name="t.png"):
    buf = io.BytesIO()
    Image.new("RGB", (200, 200), color=(120, 120, 120)).save(buf, format="PNG")
    buf.seek(0)
    return SimpleUploadedFile(name, buf.read(), content_type="image/png")


@pytest.mark.django_db
def test_validate_image_rejects_bad_format():
    bad = SimpleUploadedFile("x.txt", b"hello", content_type="text/plain")
    with pytest.raises(ValidationError):
        validate_image_file(bad)


@pytest.mark.django_db
def test_run_analysis_consumes_quota(monkeypatch, settings):
    settings.AI_PROVIDER = "mock"
    identity = UserIdentity.objects.create(phone="09120000077", is_verified=True)
    industry = Industry.objects.create(name="تست")
    monkeypatch.setattr("apps.quota.services.get_default_image_quota", lambda: 5)
    from apps.quota.services import get_or_create_quota
    get_or_create_quota(identity)

    analysis = run_analysis(identity, industry, _fake_png())
    assert analysis.status == "success"
    q = UsageQuota.objects.get(identity=identity)
    assert q.used_count == 1


@pytest.mark.django_db
def test_run_analysis_failure_releases_quota(monkeypatch, settings):
    settings.AI_PROVIDER = "openai"
    identity = UserIdentity.objects.create(phone="09120000078", is_verified=True)
    industry = Industry.objects.create(name="تست۲")
    from apps.quota.services import get_or_create_quota
    get_or_create_quota(identity)

    def boom(**kwargs):
        from apps.ai_services.base import AIProviderError
        raise AIProviderError("boom")

    monkeypatch.setattr("apps.ai_services.providers.OpenAIVisionProvider.analyze_image",
                        lambda self, **kwargs: boom())
    from apps.image_analysis.services import AnalysisError
    with pytest.raises(AnalysisError):
        run_analysis(identity, industry, _fake_png())
    q = UsageQuota.objects.get(identity=identity)
    assert q.used_count == 0
    assert q.reserved_count == 0