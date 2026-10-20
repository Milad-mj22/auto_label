from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

from .views import landing_view, test_view

urlpatterns = [
    path("", landing_view, name="landing"),
    path("test/", test_view, name="test-page"),

    path("admin/", admin.site.urls),
    path("api/industries/", include("apps.industries.urls")),
    path("api/verification/", include("apps.verification.urls")),
    path("api/quota/", include("apps.quota.urls")),
    path("api/analysis/", include("apps.image_analysis.urls")),
    path("api/conversations/", include("apps.conversations.urls")),
    path("api/settings/", include("apps.settings_app.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    # در حالت DEBUG، Django خودش static/ را از STATICFILES_DIRS سرو می‌کند