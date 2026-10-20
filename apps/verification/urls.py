from django.urls import path
from .views import RequestOtpView, VerifyOtpView, CheckVerificationView

urlpatterns = [
    path("request/", RequestOtpView.as_view(), name="otp-request"),
    path("verify/", VerifyOtpView.as_view(), name="otp-verify"),
    path("check/", CheckVerificationView.as_view(), name="otp-check"),  # ← جدید
]