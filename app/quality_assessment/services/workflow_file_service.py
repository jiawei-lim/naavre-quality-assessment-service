from typing import Any

import networkx as nx

from quality_assessment.assets.workflow_file import WorkflowFileAsset


def build_workflow_multidigraph(
    workflow_file: WorkflowFileAsset,
) -> nx.MultiDiGraph:
    graph = nx.MultiDiGraph()

    graph.graph.update(
        {
            "asset_id": workflow_file.id,
            "asset_type": workflow_file.asset_type,
            "title": workflow_file.title,
            "description": workflow_file.description,
            "node_count": len(workflow_file.nodes),
            "link_count": len(workflow_file.links),
            "invalid_links": [],
        }
    )

    for node in workflow_file.nodes:
        node_id = node.get("id")
        if not node_id:
            continue

        graph.add_node(
            node_id,
            node_type=node.get("type"),
            title=node.get("cell_title"),
            position=node.get("position", {}),
            ports=node.get("ports", {}),
            cell=node.get("cell", {}),
            container_image=node.get("container_image"),
            source_url=node.get("source_url"),
            raw_node=node,
            referenced_only=False,
        )

    for index, link in enumerate(workflow_file.links):
        edge = _edge_from_link(link, index)

        if not edge["from_node_id"] or not edge["to_node_id"]:
            graph.graph["invalid_links"].append(link)
            continue

        _ensure_referenced_node(graph, edge["from_node_id"])
        _ensure_referenced_node(graph, edge["to_node_id"])

        graph.add_edge(
            edge["from_node_id"],
            edge["to_node_id"],
            key=edge["edge_key"],
            link_id=edge["link_id"],
            from_port_id=edge["from_port_id"],
            to_port_id=edge["to_port_id"],
            raw_link=link,
        )

    return graph


def get_self_loops(graph: nx.MultiDiGraph) -> list[dict[str, Any]]:
    return [
        {
            "node_id": from_node,
            "edge_key": edge_key,
            "link_id": edge_data.get("link_id"),
            "from_port_id": edge_data.get("from_port_id"),
            "to_port_id": edge_data.get("to_port_id"),
        }
        for from_node, _, edge_key, edge_data in nx.selfloop_edges(
            graph,
            keys=True,
            data=True,
        )
    ]


def get_cycles(graph: nx.MultiDiGraph) -> list[list[str]]:
    return [list(cycle) for cycle in nx.simple_cycles(graph)]


def get_isolated_nodes(graph: nx.MultiDiGraph) -> list[dict[str, Any]]:
    return [_node_summary(graph, node_id) for node_id in nx.isolates(graph)]


def get_disconnected_components(graph: nx.MultiDiGraph) -> list[list[str]]:
    return [
        sorted(component)
        for component in nx.weakly_connected_components(graph)
        if len(component) < graph.number_of_nodes()
    ]


def get_orphaned_nodes(graph: nx.MultiDiGraph) -> list[dict[str, Any]]:
    return [
        _node_summary(graph, node_id)
        for node_id, node_data in graph.nodes(data=True)
        if node_data.get("referenced_only")
    ]


def get_input_output_type_mismatches(
    graph: nx.MultiDiGraph,
) -> list[dict[str, Any]]:
    mismatches = []

    for from_node, to_node, edge_key, edge_data in graph.edges(keys=True, data=True):
        from_port_id = edge_data.get("from_port_id")
        to_port_id = edge_data.get("to_port_id")
        from_type = _declared_port_type(graph, from_node, "outputs", from_port_id)
        to_type = _declared_port_type(graph, to_node, "inputs", to_port_id)

        if not from_type or not to_type or from_type == to_type:
            continue

        mismatches.append(
            {
                "link_id": edge_data.get("link_id"),
                "edge_key": edge_key,
                "from_node_id": from_node,
                "from_node_title": graph.nodes[from_node].get("title"),
                "from_port_id": from_port_id,
                "from_type": from_type,
                "to_node_id": to_node,
                "to_node_title": graph.nodes[to_node].get("title"),
                "to_port_id": to_port_id,
                "to_type": to_type,
            }
        )

    return mismatches


def run_graph_checks(graph: nx.MultiDiGraph) -> dict[str, Any]:
    return {
            "self_loops": get_self_loops(graph),
            "cycles": get_cycles(graph),
            "isolated_nodes": get_isolated_nodes(graph),
            "disconnected_components": get_disconnected_components(graph),
            "orphaned_nodes": get_orphaned_nodes(graph),
            "input_output_type_mismatches": get_input_output_type_mismatches(graph),
            "invalid_links": graph.graph.get("invalid_links", []),
        }


def _edge_from_link(link: dict[str, Any], index: int) -> dict[str, Any]:
    from_data = link.get("from", {})
    to_data = link.get("to", {})
    link_id = link.get("id")
    edge_key = link_id or f"link-{index}"

    return {
        "edge_key": edge_key,
        "link_id": link_id,
        "from_node_id": from_data.get("nodeId"),
        "from_port_id": from_data.get("portId"),
        "to_node_id": to_data.get("nodeId"),
        "to_port_id": to_data.get("portId"),
    }


def _ensure_referenced_node(graph: nx.MultiDiGraph, node_id: str) -> None:
    if node_id not in graph:
        graph.add_node(node_id, referenced_only=True)


def _node_summary(graph: nx.MultiDiGraph, node_id: str) -> dict[str, Any]:
    node_data = graph.nodes[node_id]

    return {
        "node_id": node_id,
        "title": node_data.get("title"),
        "node_type": node_data.get("node_type"),
        "referenced_only": node_data.get("referenced_only", False),
        "in_degree": graph.in_degree(node_id),
        "out_degree": graph.out_degree(node_id),
    }


def _declared_port_type(
    graph: nx.MultiDiGraph,
    node_id: str,
    direction: str,
    port_id: str | None,
) -> str | None:
    if not port_id or node_id not in graph:
        return None

    cell = graph.nodes[node_id].get("cell", {})

    for port in cell.get(direction, []):
        if port.get("name") == port_id:
            return port.get("type")

    return None
