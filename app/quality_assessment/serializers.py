from rest_framework import serializers
from .models import *

class AssessmentRunSerializer(serializers.ModelSerializer):
    # Add asset data type field
    asset_data = serializers.JSONField(write_only=True, required=False, default=dict)

    # Uses AssessmentRun model fields
    class Meta:
        model = AssessmentRun
        fields = [
            "id",
            "asset_id",
            "asset_reference",
            "asset_type",
            "asset_data",
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

    def create(self, validated_data):
        self.asset_data = validated_data.pop("asset_data", {})
        return super().create(validated_data)


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
