from dataclasses import dataclass, field
from typing import Any

from quality_assessment.assets.base_asset import BaseAsset


@dataclass(frozen=True)
class WorkflowFileAsset(BaseAsset):
    asset_type: str = "workflow_file"
    derived_metadata: dict[str, Any] = field(default_factory=dict)
    inputs: list[dict[str, Any]] = field(default_factory=list)
    outputs: list[dict[str, Any]] = field(default_factory=list)
    configurations: list[dict[str, Any]] = field(default_factory=list)
    parameters: list[dict[str, Any]] = field(default_factory=list)
    secrets: list[dict[str, Any]] = field(default_factory=list)
    steps: list[dict[str, Any]] = field(default_factory=list)
    links: list[dict[str, Any]] = field(default_factory=list)
    dependencies: list[dict[str, Any]] = field(default_factory=list)
    container_images: list[str] = field(default_factory=list)

    def __repr__(self) -> str:
        return (
            "WorkflowFileAsset("
            f"id={self.id!r}, "
            f"title={self.title!r}, "
            f"asset_type={self.asset_type!r}, "
            f"steps={len(self.steps)}, "
            f"links={len(self.links)}, "
            f"inputs={len(self.inputs)}, "
            f"outputs={len(self.outputs)}, "
            f"parameters={len(self.parameters)}, "
            f"dependencies={len(self.dependencies)}, "
            f"container_images={len(self.container_images)}"
            ")"
        )

    def to_assessment_context(self) -> dict[str, Any]:
        return {
            "asset_id": self.id,
            "asset_type": self.asset_type,
            "common_metadata": {
                "title": self.title,
                "description": self.description,
                "created": self.created,
                "modified": self.modified,
                "owner": self.owner,
                "virtual_lab": self.virtual_lab,
                "shared_with_scopes": self.shared_with_scopes,
                "shared_with_users": self.shared_with_users,
                "creators": self.derived_metadata.get("creators", []),
                "license": self.derived_metadata.get("license"),
                "keywords": self.derived_metadata.get("keywords", []),
                "version": self.derived_metadata.get("version"),
            },
            "asset_specific": {
                "inputs": self.inputs,
                "outputs": self.outputs,
                "configurations": self.configurations,
                "parameters": self.parameters,
                "secrets": self.secrets,
                "steps": self.steps,
                "links": self.links,
                "dependencies": self.dependencies,
                "container_images": self.container_images,
                "step_count": len(self.steps),
                "link_count": len(self.links),
            },
            "raw_payload": self.raw_payload,
        }
