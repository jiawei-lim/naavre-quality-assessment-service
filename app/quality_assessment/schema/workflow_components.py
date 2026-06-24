from rest_framework import serializers

from quality_assessment.schema.common import (
    BaseImageSchema,
    ConfigurationSchema,
    DependencySchema,
    ParameterSchema,
    SecretSchema,
    VariableSchema,
)


SPECIAL_WORKFLOW_COMPONENT_TYPES = {"splitter", "merger"}


class AssetVersionRefSchema(serializers.Serializer):
    version = serializers.IntegerField()
    url = serializers.CharField()


class WorkflowComponentSchema(serializers.Serializer):
    url = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    title = serializers.CharField()
    description = serializers.CharField(required=False, allow_blank=True)
    created = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    modified = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    owner = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    virtual_lab = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    shared_with_scopes = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        default=list,
    )
    shared_with_users = serializers.ListField(
        child=serializers.CharField(),
        required=False,
        default=list,
    )
    type = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    version = serializers.IntegerField(required=False, allow_null=True)
    versions = AssetVersionRefSchema(many=True, required=False, default=list)
    container_image = serializers.CharField(
        required=False,
        allow_blank=True,
        allow_null=True,
    )
    base_container_image = BaseImageSchema(required=False, allow_null=True)
    dependencies = DependencySchema(many=True, required=False, default=list)
    inputs = VariableSchema(many=True, required=False, default=list)
    outputs = VariableSchema(many=True, required=False, default=list)
    confs = ConfigurationSchema(many=True, required=False, default=list)
    params = ParameterSchema(many=True, required=False, default=list)
    secrets = SecretSchema(many=True, required=False, default=list)
    kernel = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    source_url = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    is_draft = serializers.BooleanField(required=False)

    def validate(self, attrs):
        if self._is_special_workflow_component(attrs):
            return attrs

        if not self._has_url(attrs):
            raise serializers.ValidationError(
                {
                    "url": (
                        "Workflow components must provide url unless they are "
                        "splitter or merger cells."
                    )
                }
            )

        if not self._has_image(attrs):
            message = (
                "Workflow components must provide container_image or "
                "base_container_image unless they are splitter or merger cells."
            )
            raise serializers.ValidationError(
                {
                    "container_image": message,
                    "base_container_image": message,
                }
            )

        return attrs

    @staticmethod
    def _is_special_workflow_component(attrs):
        component_type = attrs.get("type")
        return component_type in SPECIAL_WORKFLOW_COMPONENT_TYPES

    @staticmethod
    def _has_url(attrs):
        component_url = attrs.get("url")
        return isinstance(component_url, str) and bool(component_url.strip())

    @staticmethod
    def _has_image(attrs):
        container_image = attrs.get("container_image")
        if isinstance(container_image, str) and container_image.strip():
            return True

        base_container_image = attrs.get("base_container_image") or {}
        return any(
            isinstance(base_container_image.get(field), str)
            and base_container_image[field].strip()
            for field in ("build", "runtime")
        )
