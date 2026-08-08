from rest_framework import serializers

from quality_assessment.schema.common import LinkEndpointSchema, PositionSchema
from quality_assessment.schema.workflow_components import WorkflowComponentSchema


class ChartPortSchema(serializers.Serializer):
    id = serializers.CharField()
    type = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    properties = serializers.DictField(required=False, default=dict)
    position = PositionSchema(required=False)


class ChartNodePropertiesSchema(serializers.Serializer):
    cell = WorkflowComponentSchema()


class ChartNodeSchema(serializers.Serializer):
    id = serializers.CharField()
    type = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    position = PositionSchema(required=False)
    orientation = serializers.IntegerField(required=False, allow_null=True)
    ports = serializers.DictField(
        child=ChartPortSchema(),
        required=False,
        default=dict,
    )
    properties = ChartNodePropertiesSchema()
    size = serializers.DictField(required=False)


class ChartLinkSchema(serializers.Serializer):
    id = serializers.CharField()
    from_ = LinkEndpointSchema()
    to = LinkEndpointSchema()

    def to_internal_value(self, data):
        if isinstance(data, dict) and "from" in data and "from_" not in data:
            data = {**data, "from_": data["from"]}

        value = super().to_internal_value(data)
        value["from"] = value.pop("from_")
        return value

    def to_representation(self, instance):
        if isinstance(instance, dict) and "from" in instance and "from_" not in instance:
            instance = {**instance, "from_": instance["from"]}

        value = super().to_representation(instance)
        value["from"] = value.pop("from_")
        return value


class ChartSelectionSchema(serializers.Serializer):
    type = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    id = serializers.CharField(required=False, allow_blank=True, allow_null=True)


class ChartSchema(serializers.Serializer):
    offset = PositionSchema(required=False)
    scale = serializers.FloatField(required=False)
    nodes = serializers.DictField(
        child=ChartNodeSchema(),
        required=False,
        default=dict,
    )
    links = serializers.DictField(
        child=ChartLinkSchema(),
        required=False,
        default=dict,
    )
    selected = ChartSelectionSchema(required=False, default=dict)
    hovered = serializers.DictField(required=False, default=dict)


class WorkflowFilePayloadSchema(serializers.Serializer):
    id = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    title = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    description = serializers.CharField(required=False, allow_blank=True)
    virtual_lab = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    fileName = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    chart = ChartSchema()
