from dataclasses import dataclass, field
from typing import Any

from quality_assessment.types.common import (
    BaseContainerImage,
    Configuration,
    Dependency,
    Parameter,
    Port,
    Secret,
)


@dataclass(frozen=True)
class WorkflowComponent:
    id: str
    title: str | None = None
    description: str | None = None
    component_ref: str | None = None
    version: int | None = None
    owner: str | None = None
    virtual_lab: str | None = None
    inputs: list[Port] = field(default_factory=list)
    outputs: list[Port] = field(default_factory=list)
    configurations: list[Configuration] = field(default_factory=list)
    parameters: list[Parameter] = field(default_factory=list)
    secrets: list[Secret] = field(default_factory=list)
    dependencies: list[Dependency] = field(default_factory=list)
    container_image: str | None = None
    base_container_image: BaseContainerImage | None = None
    kernel: str | None = None
    source_url: str | None = None
    is_draft: bool = False
    raw_payload: dict[str, Any] = field(default_factory=dict)
