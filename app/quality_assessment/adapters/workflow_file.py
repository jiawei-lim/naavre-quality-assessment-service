from typing import Any

from quality_assessment.adapters.workflow_components import WorkflowComponentAdapter
from quality_assessment.schema.workflow_file import WorkflowFilePayloadSchema
from quality_assessment.types import WorkflowFile, WorkflowFileLink, WorkflowFileNode


class WorkflowFileAdapter:
    """
    Adapts workflow file from API payload into WorkflowFile type
    """
    def __init__(
        self,
        workflow_component_adapter: WorkflowComponentAdapter | None = None,
    ) -> None:
        self.workflow_component_adapter = (
            workflow_component_adapter or WorkflowComponentAdapter()
        )

    def from_payload(self, payload: dict[str, Any]) -> WorkflowFile:
        # verify data against workflow file schema
        data = self._validated_data(payload)

        chart = data["chart"]
        raw_chart = payload.get("chart", {}) if isinstance(payload, dict) else {}

        return WorkflowFile(
            id=data.get("id") or "",
            title=data.get("title"),
            description=data.get("description"),
            virtual_lab=data.get("virtual_lab"),
            file_name=data.get("fileName"),
            nodes=self._nodes(chart.get("nodes", {}), raw_chart.get("nodes", {})),
            links=self._links(chart.get("links", {}), raw_chart.get("links", {})),
            raw_payload=payload,
        )

    def _validated_data(self, payload: dict[str, Any]) -> dict[str, Any]:
        serializer = WorkflowFilePayloadSchema(data=payload)
        serializer.is_valid(raise_exception=True)
        return serializer.validated_data

    def _nodes(
        self,
        nodes: dict[str, dict[str, Any]],
        raw_nodes: dict[str, dict[str, Any]],
    ) -> list[WorkflowFileNode]:
        workflow_file_nodes = []

        for node_key, node in nodes.items():
            raw_node = self._raw_item(raw_nodes, node_key, node)
            raw_cell = (
                raw_node.get("properties", {}).get("cell", {})
                if isinstance(raw_node, dict)
                else {}
            )
            component = self.workflow_component_adapter.from_payload(raw_cell)
            workflow_file_nodes.append(
                WorkflowFileNode(
                    id=node.get("id") or node_key,
                    component=component,
                    node_type=node.get("type"),
                    raw_node=raw_node,
                )
            )

        return workflow_file_nodes

    def _links(
        self,
        links: dict[str, dict[str, Any]],
        raw_links: dict[str, dict[str, Any]],
    ) -> list[WorkflowFileLink]:
        workflow_file_links = []

        for link_key, link in links.items():
            raw_link = self._raw_item(raw_links, link_key, link)
            from_data = link.get("from", {})
            to_data = link.get("to", {})

            workflow_file_links.append(
                WorkflowFileLink(
                    id=link.get("id") or link_key,
                    from_node_id=from_data["nodeId"],
                    to_node_id=to_data["nodeId"],
                    from_port_name=from_data.get("portId"),
                    to_port_name=to_data.get("portId"),
                    raw_link=raw_link,
                )
            )

        return workflow_file_links

    def _raw_item(
        self,
        raw_items: dict[str, dict[str, Any]],
        item_key: str,
        fallback: dict[str, Any],
    ) -> dict[str, Any]:
        if isinstance(raw_items, dict):
            raw_item = raw_items.get(item_key)
            if isinstance(raw_item, dict):
                return raw_item

        return fallback
