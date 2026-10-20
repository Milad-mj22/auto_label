from rest_framework import generics
from .models import Industry
from .serializers import IndustrySerializer


class IndustryListView(generics.ListAPIView):
    serializer_class = IndustrySerializer
    pagination_class = None

    def get_queryset(self):
        return Industry.objects.filter(is_active=True)