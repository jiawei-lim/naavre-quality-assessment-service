from rest_framework import serializers
from .models import *
from .types.quality_dimensions import QualityDimension

class AssessmentRunSerializer(serializers.ModelSerializer):
    # Add asset data type field
    asset_data = serializers.JSONField(write_only=True, required=False, default=dict)
    fileName = serializers.CharField(write_only=True, required=True)

    quality_dimensions = serializers.ListField(
        child=serializers.CharField(),
        write_only=True,
        required=False,
        allow_empty=False
    )

    # Uses AssessmentRun model fields
    class Meta:
        model = AssessmentRun
        fields = [
            "id",
            "asset_id",
            "asset_reference",
            "asset_type",
            "asset_data",
            "fileName",
            "quality_dimensions",
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

    def validate_quality_dimensions(self, value):
        try:
            return [QualityDimension.parse(dimension) for dimension in value]
        except ValueError as error:
            raise serializers.ValidationError(str(error))

    def create(self, validated_data):
        self.asset_data = validated_data.pop("asset_data", {})
        validated_data.pop("fileName", None)
        validated_data.pop("quality_dimensions", None)
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
