from django.urls import path

from .views import *

urlpatterns = [
    path("report/", AssessmentReportView.as_view(), name="assessment-report-list"),
    path("report/<uuid:id>/", AssessmentReportView.as_view(), name="assessment-report"),
    path("run/", AssessmentRunView.as_view(), name="assessment-run"),
]
