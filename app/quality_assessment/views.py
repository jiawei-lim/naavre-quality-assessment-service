from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from .models import *
from .serializers import *

class AssessmentReportView(APIView):
    def get(self, request, id=None):
        if id is None:
            reports = AssessmentReport.objects.all()
            serializer = AssessmentReportSerializer(reports, many=True)
            return Response(serializer.data)

        report = get_object_or_404(AssessmentReport, id=id)
        serializer = AssessmentReportSerializer(report)
        return Response(serializer.data)

class AssessmentRunView(APIView):
    def post(self,request):
        serializer = AssessmentRunSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
