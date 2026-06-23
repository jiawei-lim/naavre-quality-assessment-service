from rest_framework import serializers


class BaseImageSchema(serializers.Serializer):
    build = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    runtime = serializers.CharField(required=False, allow_blank=True, allow_null=True)


class DependencySchema(serializers.Serializer):
    name = serializers.CharField()
    module = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    asname = serializers.CharField(required=False, allow_blank=True, allow_null=True)


class VariableSchema(serializers.Serializer):
    name = serializers.CharField()
    type = serializers.CharField(required=False, allow_blank=True, allow_null=True)


class ConfigurationSchema(serializers.Serializer):
    name = serializers.CharField()
    assignation = serializers.CharField()


class ParameterSchema(VariableSchema):
    default_value = serializers.CharField(
        required=False,
        allow_blank=True,
        allow_null=True,
    )


class SecretSchema(VariableSchema):
    pass


class PositionSchema(serializers.Serializer):
    x = serializers.FloatField()
    y = serializers.FloatField()


class LinkEndpointSchema(serializers.Serializer):
    nodeId = serializers.CharField()
    portId = serializers.CharField()
