from typing import Any

from quality_assessment.assets.base_asset import BaseAsset
from quality_assessment.assets.workflow_file import WorkflowFileAsset


class WorkflowFileAdapter:
    supported_asset_types = {"workflow_file", "workflow", "workflow_component"}

    def from_base_asset(
        self, asset: BaseAsset, asset_type: str = "workflow"
    ) -> WorkflowFileAsset:
        if asset_type not in self.supported_asset_types:
            raise ValueError(f"Unsupported workflow asset type: {asset_type}")

        workflow_data = self._workflow_data(asset)
        nodes = self._nodes(workflow_data)
        links = self._links(workflow_data)
        cells = [node["cell"] for node in nodes if node.get("cell")]
        derived_metadata = self._derived_metadata(cells)

        return WorkflowFileAsset(
            id=asset.id,
            title=asset.title,
            description=asset.description,
            created=asset.created,
            modified=asset.modified,
            owner=asset.owner,
            virtual_lab=asset.virtual_lab,
            shared_with_scopes=asset.shared_with_scopes,
            shared_with_users=asset.shared_with_users,
            raw_payload=asset.raw_payload,
            asset_type=asset_type,
            derived_metadata=derived_metadata,
            inputs=self._cell_items(cells, "inputs"),
            outputs=self._cell_items(cells, "outputs"),
            configurations=self._cell_items(cells, "confs"),
            parameters=self._cell_items(cells, "params"),
            secrets=self._cell_items(cells, "secrets"),
            nodes=nodes,
            links=links,
            dependencies=self._cell_items(cells, "dependencies"),
            container_images=self._container_images(cells),
        )

    def _workflow_data(self, asset: BaseAsset) -> dict[str, Any]:
        workflow_data = (
            asset.raw_payload.get("chart")
            or asset.raw_payload.get("data")
            or asset.raw_payload.get("workflow")
        )

        if isinstance(workflow_data, dict) and "chart" in workflow_data:
            return workflow_data["chart"]

        if isinstance(workflow_data, dict):
            return workflow_data

        return {}

    def _nodes(self, workflow_data: dict[str, Any]) -> list[dict[str, Any]]:
        raw_nodes = self._as_list(workflow_data.get("nodes"))
        nodes = []

        for node in raw_nodes:
            cell = node.get("properties", {}).get("cell", {})
            nodes.append(
                {
                    "id": node.get("id"),
                    "type": node.get("type"),
                    "position": node.get("position", {}),
                    "ports": node.get("ports", {}),
                    "cell": cell,
                    "cell_title": cell.get("title"),
                    "container_image": cell.get("container_image"),
                    "source_url": cell.get("source_url"),
                }
            )

        return nodes

    def _links(self, workflow_data: dict[str, Any]) -> list[dict[str, Any]]:
        links = self._as_list(workflow_data.get("links"))

        return [
            {
                "id": link.get("id"),
                "from": link.get("from", {}),
                "to": link.get("to", {}),
            }
            for link in links
        ]

    def _derived_metadata(self, cells: list[dict[str, Any]]) -> dict[str, Any]:
        metadata = {}
        owners = sorted({cell.get("owner") for cell in cells if cell.get("owner")})
        virtual_labs = sorted(
            {cell.get("virtual_lab") for cell in cells if cell.get("virtual_lab")}
        )

        metadata.setdefault("creators", owners)
        metadata.setdefault("virtual_labs", virtual_labs)
        metadata.setdefault("created", self._first_value(cells, "created"))
        metadata.setdefault("modified", self._first_value(cells, "modified"))

        return metadata

    def _cell_items(
        self, cells: list[dict[str, Any]], key: str
    ) -> list[dict[str, Any]]:
        items = []

        for cell in cells:
            for item in self._as_list(cell.get(key)):
                items.append(
                    {
                        "cell_title": cell.get("title"),
                        "cell_url": cell.get("url"),
                        **item,
                    }
                )

        return items

    def _container_images(self, cells: list[dict[str, Any]]) -> list[str]:
        images = []

        for cell in cells:
            image = cell.get("container_image")
            if image:
                images.append(str(image))

            base_image = cell.get("base_container_image")
            if isinstance(base_image, dict):
                images.extend(str(value) for value in base_image.values() if value)

        return sorted(set(images))

    def _first_value(self, cells: list[dict[str, Any]], key: str) -> Any:
        for cell in cells:
            value = cell.get(key)
            if value:
                return value

        return None

    def _as_list(self, value: Any) -> list[dict[str, Any]]:
        if value is None:
            return []

        if isinstance(value, list):
            return [item if isinstance(item, dict) else {"value": item} for item in value]

        if isinstance(value, dict):
            return list(value.values())

        return [{"value": value}]
