from rest_framework import serializers
from .models import *

class AssessmentRunSerializer(serializers.ModelSerializer):
    class Meta:
        model = AssessmentRun
        fields = [
            "id",
            "asset_id",
            "asset_reference",
            "asset_type",
            "triggered_by",
            "requested_at",
            "started_at",
            "completed_at",
        ]

        read_only_fields = [
            "id",
            "requested_at",
            "started_at",
            "completed_at",
        ]


class AssessmentReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = AssessmentReport
        fields = [
            "id",
            "assessment_run",
            "description",
            "generated_at",
            "data",
        ]
        
        read_only_fields = [
            "id",
            "generated_at",
        ]