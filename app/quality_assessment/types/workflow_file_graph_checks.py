from dataclasses import dataclass, field


@dataclass(frozen=True)
class GraphCheckComponentRef:
    node_id: str
    title: str | None = None
    node_type: str | None = None
    component_ref: str | None = None


@dataclass(frozen=True)
class GraphCheckLinkRef:
    link_id: str | None = None
    from_node_id: str | None = None
    to_node_id: str | None = None
    from_port_name: str | None = None
    to_port_name: str | None = None


@dataclass(frozen=True)
class GraphCheckResult:
    check_type: str
    severity: str
    message: str
    components: list[GraphCheckComponentRef] = field(default_factory=list)
    links: list[GraphCheckLinkRef] = field(default_factory=list)
