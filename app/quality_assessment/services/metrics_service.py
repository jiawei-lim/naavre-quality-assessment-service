from dataclasses import asdict
from typing import Any, Callable, Collection

import networkx as nx

from .code import code_check_service as code
from .workflow_file import component_check_service as component
from .workflow_file import workflow_check_service as workflow
from ..types.quality_dimensions import QualityDimension
from ..types.result_types import BaseCheck, ComponentCheckResult

GraphCheck = Callable[[nx.MultiDiGraph], Any]
ComponentCheck = Callable[[component.ComponentContext], BaseCheck | None]

GRAPH_CHECKS: dict[QualityDimension, list[GraphCheck]] = {
    QualityDimension.FUNCTIONAL_SUITABILITY: [
        workflow.get_cycles,
        workflow.get_input_output_type_mismatches,
        workflow.get_unfulfilled_inputs,
        workflow.get_invalid_links,
        workflow.get_specification_completeness,
    ],
    QualityDimension.MAINTAINABILITY: [
        workflow.get_shared_configurations,
        workflow.get_size,
        workflow.get_longest_path,
    ],
    QualityDimension.FAIR: [
        workflow.run_fair_checks,
    ],
}

COMPONENT_CHECKS: dict[QualityDimension, list[ComponentCheck]] = {
    QualityDimension.MAINTAINABILITY: [
        lambda ctx: code.get_loc(ctx.node_data, ctx.source),
        lambda ctx: code.get_cc(ctx.source),
        lambda ctx: component.get_hardcoded_configurations(ctx.node_data),
        lambda ctx: component.get_fan_in(ctx.graph, ctx.node_id),
        lambda ctx: component.get_fan_out(ctx.graph, ctx.node_id),
        lambda ctx: component.get_interface_size(ctx.node_data),
    ],
    QualityDimension.SUSTAINABILITY: [
        lambda ctx: component.get_default_value_completeness(ctx.node_data),
        lambda ctx: component.get_external_service_dependency(ctx.node_data, ctx.source),
    ],
}


def run_checks(
    graph: nx.MultiDiGraph,
    dimensions: Collection[QualityDimension] | None = None,
) -> dict[str, Any]:
    dimensions = frozenset(dimensions) if dimensions else frozenset(QualityDimension)

    return {
        "graph_checks": _run_graph_checks(graph, dimensions),
        "component_checks": _run_component_checks(graph, dimensions),
    }


def _selected(
    registry: dict[QualityDimension, list],
    dimensions: Collection[QualityDimension],
) -> list:
    """The requested dimensions' checks, in quality dimension declaration order."""
    return [
        check
        for dimension in QualityDimension
        if dimension in dimensions
        for check in registry.get(dimension, [])
    ]


def _run_graph_checks(
    graph: nx.MultiDiGraph,
    dimensions: Collection[QualityDimension],
) -> list[dict]:
    results = []

    for check in _selected(GRAPH_CHECKS, dimensions):
        result = check(graph)
        results += result if isinstance(result, list) else [result]

    return [asdict(result) for result in results]


def _run_component_checks(
    graph: nx.MultiDiGraph,
    dimensions: Collection[QualityDimension],
) -> list[dict]:
    selected = _selected(COMPONENT_CHECKS, dimensions)
    if not selected:
        return []

    results = []

    for node_id, node_data in graph.nodes(data=True):
        if node_data.get("node_type") != "workflow-cell":
            continue

        context = component.ComponentContext(
            graph = graph,
            node_id = node_id,
            node_data = node_data,
        )

        checks = [check(context) for check in selected]
        checks = [check for check in checks if check is not None]

        if not checks:
            continue

        results.append(
            ComponentCheckResult(
                node_id = node_id,
                title = node_data.get("title"),
                node_type = node_data.get("node_type"),
                component_ref = node_data.get("source_url"),
                checks = checks,
            )
        )

    return [asdict(result) for result in results]
