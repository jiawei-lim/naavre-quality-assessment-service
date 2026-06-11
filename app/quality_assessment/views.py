from rest_framework import generics

from .models import *
from .serializers import *


class AssessmentReportListView(generics.ListAPIView):
    queryset = AssessmentReport.objects.all()
    serializer_class = AssessmentReportSerializer


class AssessmentReportDetailView(generics.RetrieveAPIView):
    queryset = AssessmentReport.objects.all()
    serializer_class = AssessmentReportSerializer
    lookup_field = "id"


class AssessmentRunView(generics.CreateAPIView):
    queryset = AssessmentRun.objects.all()
    serializer_class = AssessmentRunSerializer
