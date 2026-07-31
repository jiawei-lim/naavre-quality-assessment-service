from dataclasses import dataclass, field

@dataclass(frozen=True)
class BaseCheck:
    check_type: str
    quality_dimension:str
    quality_subcharacteristic:str
    message: str
    severity: str | None = None


@dataclass(frozen=True)
class GraphCheckComponent:
    node_id: str
    severity: str | None = None
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
class GraphCheckResult(BaseCheck):
    components: list[GraphCheckComponent] = field(default_factory=list)
    links: list[GraphCheckLink] = field(default_factory=list)

@dataclass(frozen=True)
class ValueCheckResult(BaseCheck):
    value: float | int = 0