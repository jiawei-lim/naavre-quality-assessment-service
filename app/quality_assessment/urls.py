from django.urls import path

from .views import *

urlpatterns = [
    path("report/", AssessmentReportListView.as_view(), name="assessment-report-list"),
    path("report/<uuid:id>/", AssessmentReportDetailView.as_view(), name="assessment-report-detail"),
    path("run/", AssessmentRunView.as_view(), name="assessment-run"),
    path("quality-model/", QualityModelView.as_view(), name="quality-model"),
]
