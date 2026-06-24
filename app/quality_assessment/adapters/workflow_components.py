from typing import Any

from quality_assessment.schema.workflow_components import WorkflowComponentSchema
from quality_assessment.types import (
    BaseContainerImage,
    Configuration,
    Dependency,
    Parameter,
    Port,
    Secret,
    WorkflowComponent,
)


class WorkflowComponentAdapter:
    def from_payload(self, payload: dict[str, Any]) -> WorkflowComponent:
        data = self._validated_data(payload)
        component_ref = data.get("url")
        component_id = component_ref or data.get("type") or ""

        return WorkflowComponent(
            id=component_id,
            title=data.get("title"),
            description=data.get("description"),
            component_ref=component_ref,
            version=data.get("version"),
            owner=data.get("owner"),
            virtual_lab=data.get("virtual_lab"),
            inputs=[self._port(item) for item in data.get("inputs", [])],
            outputs=[self._port(item) for item in data.get("outputs", [])],
            configurations=[
                self._configuration(item) for item in data.get("confs", [])
            ],
            parameters=[self._parameter(item) for item in data.get("params", [])],
            secrets=[self._secret(item) for item in data.get("secrets", [])],
            dependencies=[
                self._dependency(item) for item in data.get("dependencies", [])
            ],
            container_image=data.get("container_image"),
            base_container_image=self._base_container_image(
                data.get("base_container_image")
            ),
            kernel=data.get("kernel"),
            source_url=data.get("source_url"),
            is_draft=data.get("is_draft", False),
            raw_payload=payload,
        )

    def _validated_data(self, payload: dict[str, Any]) -> dict[str, Any]:
        serializer = WorkflowComponentSchema(data=payload)
        serializer.is_valid(raise_exception=True)
        return serializer.validated_data

    def _port(self, data: dict[str, Any]) -> Port:
        return Port(name=data["name"], type=data.get("type"))

    def _configuration(self, data: dict[str, Any]) -> Configuration:
        return Configuration(name=data["name"], assignation=data["assignation"])

    def _parameter(self, data: dict[str, Any]) -> Parameter:
        return Parameter(
            name=data["name"],
            type=data.get("type"),
            default_value=data.get("default_value"),
        )

    def _secret(self, data: dict[str, Any]) -> Secret:
        return Secret(name=data["name"], type=data.get("type"))

    def _dependency(self, data: dict[str, Any]) -> Dependency:
        return Dependency(
            name=data["name"],
            module=data.get("module"),
            asname=data.get("asname"),
        )

    def _base_container_image(
        self,
        data: dict[str, Any] | None,
    ) -> BaseContainerImage | None:
        if data is None:
            return None

        return BaseContainerImage(
            build=data.get("build"),
            runtime=data.get("runtime"),
        )
