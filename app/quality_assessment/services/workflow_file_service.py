from typing import Any

import networkx as nx

from quality_assessment.types import WorkflowFile
from .workflow_file_graph_check_service import (
    get_cycles,
    get_disconnected_components,
    get_input_output_type_mismatches,
    get_invalid_links,
    get_isolated_nodes,
    get_orphaned_nodes,
    get_self_loops,
    get_unfulfilled_inputs,
    serialize_graph_check_results,
)

def build_workflow_multidigraph(
    workflow_file: WorkflowFile,
) -> nx.MultiDiGraph:
    graph = nx.MultiDiGraph()

    graph.graph.update(
        {
            "asset_id": workflow_file.id,
            "asset_type": "workflow_file",
            "title": workflow_file.title,
            "description": workflow_file.description,
            "node_count": len(workflow_file.nodes),
            "link_count": len(workflow_file.links),
            "invalid_links": [],
        }
    )

    for node in workflow_file.nodes:
        node_id = node.id
        if not node_id:
            continue

        component = node.component
        graph.add_node(
            node_id,
            node_type=node.node_type,
            title=component.title,
            component=component,
            container_image=component.container_image,
            source_url=component.source_url,
            raw_node=node.raw_node,
            referenced_only=False,
        )

    for index, link in enumerate(workflow_file.links):
        if not link.from_node_id or not link.to_node_id:
            graph.graph["invalid_links"].append(link.raw_link)
            continue

        _ensure_referenced_node(graph, link.from_node_id)
        _ensure_referenced_node(graph, link.to_node_id)

        graph.add_edge(
            link.from_node_id,
            link.to_node_id,
            key=link.id or f"link-{index}",
            link_id=link.id,
            from_port_name=link.from_port_name,
            to_port_name=link.to_port_name,
            raw_link=link.raw_link,
        )

    return graph



def run_graph_checks(graph: nx.MultiDiGraph) -> dict[str, Any]:
    results = [
        *get_self_loops(graph),
        *get_cycles(graph),
        *get_isolated_nodes(graph),
        *get_disconnected_components(graph),
        *get_orphaned_nodes(graph),
        *get_input_output_type_mismatches(graph),
        *get_unfulfilled_inputs(graph),
        *get_invalid_links(graph),
    ]

    return {
        "graph_checks": serialize_graph_check_results(results),
    }


def _ensure_referenced_node(graph: nx.MultiDiGraph, node_id: str) -> None:
    if node_id not in graph:
        graph.add_node(node_id, referenced_only=True)
