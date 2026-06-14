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
