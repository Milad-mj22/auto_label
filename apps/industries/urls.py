from django.urls import path
from .views import IndustryListView

urlpatterns = [
    path("", IndustryListView.as_view(), name="industry-list"),
]