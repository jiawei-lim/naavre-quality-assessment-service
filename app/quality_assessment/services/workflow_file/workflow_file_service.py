from typing import Any, Collection

import networkx as nx
from ..code.code_check_service import *

from quality_assessment.types import WorkflowFile
from quality_assessment.types.quality_dimensions import QualityDimension
from .graph_check_service import *
from ..fair.fair_check_service import *


def build_workflow_multidigraph(
    workflow_file: WorkflowFile,
) -> nx.MultiDiGraph:
    graph = nx.MultiDiGraph()

    #Graph level Metadata
    graph.graph.update(
        {
            "asset_id": workflow_file.id,
            "asset_type": "workflow_file",
            "title": workflow_file.title,
            "description": workflow_file.description,
            "file_name": workflow_file.file_name,
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



def run_graph_checks(
    graph: nx.MultiDiGraph,
    dimensions: Collection[QualityDimension],
) -> dict[str, Any]:
    results = []

    for dimension in QualityDimension:
        if dimension not in dimensions:
            continue
        for check in GRAPH_CHECKS.get(dimension, []):
            result = check(graph)
            results += result if isinstance(result, list) else [result]

    # Constructing FairCheck is what queries the metadata catalogue, so the guard
    # has to cover the construction and not just the run_checks() call.
    if QualityDimension.FAIR in dimensions:
        results += FairCheck(graph.graph["file_name"]).run_checks()

    return {
        "graph_checks": serialize_graph_check_results(results),
    }


def run_workflow_checks(
    graph: nx.MultiDiGraph,
    dimensions: Collection[QualityDimension],
) -> dict[str, Any]:
    result = run_graph_checks(graph, dimensions)

    try:
        result["semantic_checks"] = get_semantic_checks(graph)
        result["semantic_checks_error"] = None
    except Exception as error:
        result["semantic_checks"] = []
        result["semantic_checks_error"] = {
            "message": "Semantic checks could not be completed.",
            "detail": str(error),
        }

    return result


def _ensure_referenced_node(graph: nx.MultiDiGraph, node_id: str) -> None:
    if node_id not in graph:
        graph.add_node(node_id, referenced_only=True)
