from django.urls import path
from .views import AnalyzeImageView

urlpatterns = [
    path("analyze/", AnalyzeImageView.as_view(), name="image-analyze"),
]