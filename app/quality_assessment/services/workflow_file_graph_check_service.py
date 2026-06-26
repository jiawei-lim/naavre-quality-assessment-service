from dataclasses import asdict

import networkx as nx

from quality_assessment.types import (
    GraphCheckComponentRef,
    GraphCheckLinkRef,
    GraphCheckResult,
)


def get_self_loops(graph: nx.MultiDiGraph) -> list[GraphCheckResult]:
    results = []

    for from_node, _, _, edge_data in nx.selfloop_edges(
        graph,
        keys=True,
        data=True,
    ):
        results.append(
            GraphCheckResult(
                check_type="self_loop",
                severity="warning",
                message=f"Component '{from_node}' has a link to itself.",
                components=[_component_ref(graph, from_node)],
                links=[_link_ref(from_node, from_node, edge_data)],
            )
        )

    return results


def get_cycles(graph: nx.MultiDiGraph) -> list[GraphCheckResult]:
    return [
        GraphCheckResult(
            check_type="cycle",
            severity="warning",
            message="Workflow contains a directed cycle.",
            components=[_component_ref(graph, node_id) for node_id in cycle],
            links=_links_between_node_sequence(graph, cycle),
        )
        for cycle in nx.simple_cycles(graph)
    ]


def get_isolated_nodes(graph: nx.MultiDiGraph) -> list[GraphCheckResult]:
    return [
        GraphCheckResult(
            check_type="isolated_node",
            severity="warning",
            message=f"Component '{node_id}' is not connected to the workflow graph.",
            components=[_component_ref(graph, node_id)],
            links=[],
        )
        for node_id in nx.isolates(graph)
    ]


def get_disconnected_components(graph: nx.MultiDiGraph) -> list[GraphCheckResult]:
    results = []

    for component in nx.weakly_connected_components(graph):
        if len(component) == graph.number_of_nodes():
            continue

        component_node_ids = sorted(component)
        results.append(
            GraphCheckResult(
                check_type="disconnected_component",
                severity="warning",
                message="Workflow contains a disconnected component.",
                components=[
                    _component_ref(graph, node_id) for node_id in component_node_ids
                ],
                links=_links_within_component(graph, set(component_node_ids)),
            )
        )

    return results


def get_orphaned_nodes(graph: nx.MultiDiGraph) -> list[GraphCheckResult]:
    return [
        GraphCheckResult(
            check_type="orphaned_node",
            severity="warning",
            message=(
                f"Component '{node_id}' is referenced by a link but is missing "
                "from the workflow nodes."
            ),
            components=[_component_ref(graph, node_id)],
            links=_incident_links(graph, node_id),
        )
        for node_id, node_data in graph.nodes(data=True)
        if node_data.get("referenced_only")
    ]


def get_input_output_type_mismatches(
    graph: nx.MultiDiGraph,
) -> list[GraphCheckResult]:
    results = []

    for from_node, to_node, _, edge_data in graph.edges(keys=True, data=True):
        from_port_name = edge_data.get("from_port_name")
        to_port_name = edge_data.get("to_port_name")
        from_type = _declared_port_type(graph, from_node, "outputs", from_port_name)
        to_type = _declared_port_type(graph, to_node, "inputs", to_port_name)

        if not from_type or not to_type or from_type == to_type:
            continue

        results.append(
            GraphCheckResult(
                check_type="input_output_type_mismatch",
                severity="warning",
                message=(
                    f"Link from '{from_node}.{from_port_name}' ({from_type}) "
                    f"to '{to_node}.{to_port_name}' ({to_type}) has mismatched "
                    "input/output types."
                ),
                components=[
                    _component_ref(graph, from_node),
                    _component_ref(graph, to_node),
                ],
                links=[_link_ref(from_node, to_node, edge_data)],
            )
        )

    return results


#Check all input fulfilled
def get_unfulfilled_inputs(graph: nx.MultiDiGraph) -> list[GraphCheckResult]:
    results = []

    #For all nodes in graph
    for node_id, node_data in graph.nodes(data=True):
        if node_data.get("referenced_only"):
            continue
        
        #Get component data 
        component = node_data.get("component")
        if component is None:
            continue
        
        #Get port name of input edges by node id
        fulfilled_input_names = {
            edge_data.get("to_port_name")
            for _, _, edge_data in graph.in_edges(node_id, data=True)
            if edge_data.get("to_port_name")
        }

        for input_port in component.inputs:
            if input_port.name in fulfilled_input_names:
                continue

            results.append(
                GraphCheckResult(
                    check_type="unfulfilled_input",
                    severity="warning",
                    message=(
                        f"Input '{input_port.name}' of component '{node_id}' "
                        "is not fulfilled by any incoming link."
                    ),
                    components=[_component_ref(graph, node_id)],
                    links=[],
                )
            )

    return results


def get_invalid_links(graph: nx.MultiDiGraph) -> list[GraphCheckResult]:
    return [
        *_get_links_with_missing_endpoints(graph),
        *_get_duplicate_links(graph),
        *_get_same_direction_port_links(graph),
    ]


def serialize_graph_check_results(
    results: list[GraphCheckResult],
) -> list[dict]:
    return [asdict(result) for result in results]


def _component_ref(
    graph: nx.MultiDiGraph,
    node_id: str,
) -> GraphCheckComponentRef:
    if node_id not in graph:
        return GraphCheckComponentRef(node_id=node_id)

    node_data = graph.nodes[node_id]
    component = node_data.get("component")

    return GraphCheckComponentRef(
        node_id=node_id,
        title=node_data.get("title") or getattr(component, "title", None),
        node_type=node_data.get("node_type"),
        component_ref=getattr(component, "component_ref", None),
    )


def _link_ref(
    from_node: str,
    to_node: str,
    edge_data: dict,
) -> GraphCheckLinkRef:
    return GraphCheckLinkRef(
        link_id=edge_data.get("link_id"),
        from_node_id=from_node,
        to_node_id=to_node,
        from_port_name=edge_data.get("from_port_name"),
        to_port_name=edge_data.get("to_port_name"),
    )


def _raw_link_ref(raw_link: dict) -> GraphCheckLinkRef:
    from_data = raw_link.get("from", {}) if isinstance(raw_link, dict) else {}
    to_data = raw_link.get("to", {}) if isinstance(raw_link, dict) else {}

    return GraphCheckLinkRef(
        link_id=raw_link.get("id") if isinstance(raw_link, dict) else None,
        from_node_id=from_data.get("nodeId"),
        to_node_id=to_data.get("nodeId"),
        from_port_name=from_data.get("portId"),
        to_port_name=to_data.get("portId"),
    )


def _links_between_node_sequence(
    graph: nx.MultiDiGraph,
    node_ids: list[str],
) -> list[GraphCheckLinkRef]:
    links = []

    if not node_ids:
        return links

    if len(node_ids) == 1:
        node_id = node_ids[0]
        edge_map = graph.get_edge_data(node_id, node_id, default={})
        return [
            _link_ref(node_id, node_id, edge_data)
            for edge_data in edge_map.values()
        ]

    node_pairs = zip(node_ids, [*node_ids[1:], node_ids[0]])
    for from_node, to_node in node_pairs:
        edge_map = graph.get_edge_data(from_node, to_node, default={})
        links.extend(
            _link_ref(from_node, to_node, edge_data)
            for edge_data in edge_map.values()
        )

    return links


def _links_within_component(
    graph: nx.MultiDiGraph,
    node_ids: set[str],
) -> list[GraphCheckLinkRef]:
    return [
        _link_ref(from_node, to_node, edge_data)
        for from_node, to_node, edge_data in graph.edges(data=True)
        if from_node in node_ids and to_node in node_ids
    ]


def _incident_links(
    graph: nx.MultiDiGraph,
    node_id: str,
) -> list[GraphCheckLinkRef]:
    return [
        _link_ref(from_node, to_node, edge_data)
        for from_node, to_node, edge_data in graph.in_edges(node_id, data=True)
    ] + [
        _link_ref(from_node, to_node, edge_data)
        for from_node, to_node, edge_data in graph.out_edges(node_id, data=True)
    ]


def _invalid_link_component_refs(
    graph: nx.MultiDiGraph,
    raw_link: dict,
) -> list[GraphCheckComponentRef]:
    link_ref = _raw_link_ref(raw_link)
    node_ids = [
        node_id
        for node_id in (link_ref.from_node_id, link_ref.to_node_id)
        if node_id and node_id in graph
    ]
    return [_component_ref(graph, node_id) for node_id in node_ids]


def _get_links_with_missing_endpoints(
    graph: nx.MultiDiGraph,
) -> list[GraphCheckResult]:
    return [
        GraphCheckResult(
            check_type="invalid_link",
            severity="error",
            message="Workflow contains a link with a missing source or target node.",
            components=_invalid_link_component_refs(graph, raw_link),
            links=[_raw_link_ref(raw_link)],
        )
        for raw_link in graph.graph.get("invalid_links", [])
    ]


def _get_duplicate_links(graph: nx.MultiDiGraph) -> list[GraphCheckResult]:
    links_by_endpoints = {}

    for from_node, to_node, edge_data in graph.edges(data=True):
        from_port_name = edge_data.get("from_port_name")
        to_port_name = edge_data.get("to_port_name")
        if not from_port_name or not to_port_name:
            continue

        endpoint_key = (from_node, from_port_name, to_node, to_port_name)
        links_by_endpoints.setdefault(endpoint_key, []).append(
            _link_ref(from_node, to_node, edge_data)
        )

    results = []
    for endpoint_key, links in links_by_endpoints.items():
        if len(links) < 2:
            continue

        from_node, from_port_name, to_node, to_port_name = endpoint_key
        results.append(
            GraphCheckResult(
                check_type="invalid_link",
                severity="error",
                message=(
                    "Workflow contains duplicate links from "
                    f"'{from_node}.{from_port_name}' to "
                    f"'{to_node}.{to_port_name}'."
                ),
                components=[
                    _component_ref(graph, from_node),
                    _component_ref(graph, to_node),
                ],
                links=links,
            )
        )

    return results


def _get_same_direction_port_links(
    graph: nx.MultiDiGraph,
) -> list[GraphCheckResult]:
    results = []

    for from_node, to_node, edge_data in graph.edges(data=True):
        from_port_name = edge_data.get("from_port_name")
        to_port_name = edge_data.get("to_port_name")
        from_direction = _declared_port_direction(graph, from_node, from_port_name)
        to_direction = _declared_port_direction(graph, to_node, to_port_name)

        if not from_direction or not to_direction:
            continue

        if from_direction == "output" and to_direction == "input":
            continue

        results.append(
            GraphCheckResult(
                check_type="invalid_link",
                severity="error",
                message=(
                    "Workflow contains an invalid "
                    f"{from_direction}-to-{to_direction} link from "
                    f"'{from_node}.{from_port_name}' to "
                    f"'{to_node}.{to_port_name}'."
                ),
                components=[
                    _component_ref(graph, from_node),
                    _component_ref(graph, to_node),
                ],
                links=[_link_ref(from_node, to_node, edge_data)],
            )
        )

    return results


def _declared_port_direction(
    graph: nx.MultiDiGraph,
    node_id: str,
    port_id: str | None,
) -> str | None:
    if not port_id or node_id not in graph:
        return None

    component = graph.nodes[node_id].get("component")
    if component is None:
        return None

    if any(port.name == port_id for port in component.inputs):
        return "input"

    if any(port.name == port_id for port in component.outputs):
        return "output"

    return None


def _declared_port_type(
    graph: nx.MultiDiGraph,
    node_id: str,
    direction: str,
    port_id: str | None,
) -> str | None:
    if not port_id or node_id not in graph:
        return None

    component = graph.nodes[node_id].get("component")
    if component is None:
        return None

    for port in getattr(component, direction, []):
        if port.name == port_id:
            return port.type

    return None
