from dataclasses import dataclass, field
from typing import Any

from quality_assessment.types.workflow_components import WorkflowComponent


@dataclass(frozen=True)
class WorkflowFileNode:
    id: str
    component: WorkflowComponent
    node_type: str | None = None
    raw_node: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class WorkflowFileLink:
    id: str
    from_node_id: str
    to_node_id: str
    from_port_name: str | None = None
    to_port_name: str | None = None
    raw_link: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class WorkflowFile:
    id: str
    title: str | None = None
    description: str | None = None
    virtual_lab: str | None = None
    file_name: str | None = None
    nodes: list[WorkflowFileNode] = field(default_factory=list)
    links: list[WorkflowFileLink] = field(default_factory=list)
    raw_payload: dict[str, Any] = field(default_factory=dict)
