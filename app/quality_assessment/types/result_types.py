from dataclasses import dataclass, field
from typing import Any, Literal

@dataclass(frozen=True)
class BaseCheck:
    check_type: str
    quality_dimension:str
    message: str
    quality_subcharacteristic:str | None = None
    severity: Literal["warning", "failed", "passed"] | None = None


@dataclass(frozen=True)
class GraphCheckComponent:
    node_id: str
    title: str | None = None
    node_type: str | None = None
    component_ref: str | None = None


@dataclass(frozen=True)
class GraphCheckLink:
    link_id: str | None = None
    from_node_id: str | None = None
    to_node_id: str | None = None
    from_port_name: str | None = None
    to_port_name: str | None = None

@dataclass(frozen=True)
class ValueCheckResult(BaseCheck):
    value: float | int | str | list[Any] | None = None

@dataclass(frozen=True)
class GraphCheckResult(BaseCheck):
    components: list[GraphCheckComponent] = field(default_factory=list)
    links: list[GraphCheckLink] = field(default_factory=list)
    value: float | int | list[Any] = None
    

@dataclass(frozen=True)
class ComponentCheckResult(GraphCheckComponent):
    checks: list[ValueCheckResult] | list[GraphCheckResult] = field(default_factory=list)