from django.urls import path
from .views import AskView, MessagesView

urlpatterns = [
    path("ask/", AskView.as_view(), name="ask"),
    path("<uuid:request_id>/messages/", MessagesView.as_view(), name="messages"),
]