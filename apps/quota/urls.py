from django.urls import path
from .views import QuotaStatusView

urlpatterns = [
    path("status/", QuotaStatusView.as_view(), name="quota-status"),
]