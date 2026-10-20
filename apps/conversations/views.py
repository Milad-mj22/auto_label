from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.throttling import AnonRateThrottle

from apps.image_analysis.models import ImageAnalysis
from .models import AnalysisConversation
from .serializers import AskSerializer, MessageSerializer
from .services import ask_question, ConversationError


class QuestionThrottle(AnonRateThrottle):
    scope = "question"


class AskView(APIView):
    throttle_classes = [QuestionThrottle]

    def post(self, request):
        s = AskSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        analysis = ImageAnalysis.objects.filter(request_id=s.validated_data["request_id"]).first()
        if not analysis:
            return Response({"detail": "تحلیل یافت نشد."}, status=404)
        try:
            msg = ask_question(analysis, s.validated_data["question"])
        except ConversationError as e:
            return Response({"detail": str(e)}, status=status.HTTP_409_CONFLICT)
        return Response(MessageSerializer(msg).data, status=201)


class MessagesView(APIView):
    def get(self, request, request_id):
        analysis = ImageAnalysis.objects.filter(request_id=request_id).first()
        if not analysis:
            return Response({"detail": "تحلیل یافت نشد."}, status=404)
        conv = AnalysisConversation.objects.filter(analysis=analysis).first()
        if not conv:
            return Response({"messages": [], "questions_used": analysis.questions_used})
        return Response({
            "messages": MessageSerializer(conv.messages.all(), many=True).data,
            "questions_used": analysis.questions_used,
        })