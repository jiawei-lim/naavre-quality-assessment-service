from dataclasses import asdict, dataclass

import networkx as nx
from typing import Any, Callable, Collection
from ..code.code_check_service import *
from ...types.result_types import BaseCheck, ComponentCheckResult
from ...types.quality_dimensions import QualityDimension
from ...adapters.workflow_components import WorkflowComponent

THRESHOLDS = {
    "INTERFACE_SIZE" : 7,
    "FAN_IN" : 5,
    "FAN_OUT" : 5
}

@dataclass(frozen=True)
class ComponentContext:
    """Everything a component check may need, so they share one call signature."""
    graph: nx.MultiDiGraph
    node_id: str
    node_data: dict[str, Any]
    external_urls: BaseCheck | None = None


def run_component_checks(
    graph:nx.MultiDiGraph,
    dimensions:Collection[QualityDimension],
) -> dict[str, Any]:
    component_check_results = []
    for node_id, node_data in graph.nodes(data=True):
        if node_data.get("node_type") == "workflow-cell":
            source_url = node_data.get("source_url")

            code_checks, external_urls = [], None
            if source_url:
                code_checks, external_urls = run_code_checks(
                    node_data, source_url + "/task.py", dimensions
                )

            context = ComponentContext(
                graph = graph,
                node_id = node_id,
                node_data = node_data,
                external_urls = external_urls,
            )

            checks = list(code_checks)
            for dimension in QualityDimension:
                if dimension not in dimensions:
                    continue
                checks += [check(context) for check in COMPONENT_CHECKS.get(dimension, [])]

            if not checks:
                continue

            component_check_results += [
                ComponentCheckResult(
                    node_id = node_id,
                    title = node_data.get("title"),
                    node_type = node_data.get("node_type"),
                    component_ref = source_url,
                    checks = checks
                    )
                ]

    return {
        "component_checks": [asdict(result) for result in component_check_results],
    }

def get_fan_in(graph:nx.MultiDiGraph, node_id:str) -> BaseCheck:
    fan_in = len(set(graph.predecessors(node_id)))
    return BaseCheck(
            check_type = "fan_in",
            quality_dimension = QualityDimension.MAINTAINABILITY,
            quality_subcharacteristic= "modularity",
            message = "The number of distinct components that the component takes input from",
            value = fan_in,
            severity = "failed" if fan_in >= THRESHOLDS["FAN_IN"] else "passed"
        )

def get_fan_out(graph:nx.MultiDiGraph, node_id:str) -> BaseCheck:
    fan_out = len(set(graph.successors(node_id)))
    return BaseCheck(
            check_type = "fan_out",
            quality_dimension = QualityDimension.MAINTAINABILITY,
            quality_subcharacteristic= "modularity",
            message = "The number of links that have the component as a source",
            value = fan_out,
            severity = "failed" if fan_out >= THRESHOLDS["FAN_OUT"] else "passed"
        )

def get_hardcoded_configurations(node:dict[str,Any]) -> BaseCheck:
    component = node.get("component")
    confs = component.configurations
    return BaseCheck(
            check_type = "hardcoded_configurations",
            quality_dimension = QualityDimension.MAINTAINABILITY,
            quality_subcharacteristic= "reusability",
            message = "The number of unchangeable containerized configurations",
            value = confs
        )

def get_interface_size(node:dict[str,Any]) -> BaseCheck:
    component:WorkflowComponent = node.get("component")
    inputs = len(component.inputs)
    parameters = len(component.parameters)
    return BaseCheck(
        check_type = "interface_size",
        quality_dimension = QualityDimension.MAINTAINABILITY,
        quality_subcharacteristic= "modularity",
        message = "Interface size of the component",
        value = inputs + parameters,
        severity = "failed" if (inputs + parameters) > THRESHOLDS["INTERFACE_SIZE"] else "passed"
    )

def get_default_value_completeness(node:dict[str,Any]) -> BaseCheck:
    component = node.get("component")
    parameters = component.parameters
    if len(parameters) > 0 :
        parameters_no_default = [param for param in parameters if not param.default_value]
        if len(parameters_no_default) > 0:
            return BaseCheck(
                check_type = "default_value_completeness",
                quality_dimension = QualityDimension.SUSTAINABILITY,
                quality_subcharacteristic= None,
                message = "Parameters should have default values",
                severity = "warning",
                value = parameters_no_default,
            )

    return BaseCheck(
            check_type = "default_value_completeness",
            quality_dimension = QualityDimension.SUSTAINABILITY,
            quality_subcharacteristic= None,
            message = "Parameters should have default values",
            severity = "passed"
        )

def get_external_service_dependency(node:dict[str,Any],urls:BaseCheck | None = None) -> BaseCheck:
    component = node.get("component")
    secrets = component.secrets

    if urls and urls.severity == "warning":
        return BaseCheck(
            check_type = "external_service_dependency",
            quality_dimension = QualityDimension.SUSTAINABILITY,
            quality_subcharacteristic= None,
            message = "External service dependencies could not be determined",
            value = urls.value,
            severity = "warning"
        )

    external_urls = urls.value if urls else []

    if len(secrets) > 0 or len(external_urls) > 0:
        return BaseCheck(
            check_type = "external_service_dependency",
            quality_dimension = QualityDimension.SUSTAINABILITY,
            quality_subcharacteristic= None,
            message = "Calls to external services increases exposure to decay",
            value = external_urls + secrets,
            severity = "warning"
        )

    return BaseCheck(
            check_type = "external_service_dependency",
            quality_dimension = QualityDimension.SUSTAINABILITY,
            quality_subcharacteristic= None,
            message = "No calls to external services detected",
            severity = "passed"
        )


# The per-component checks belonging to each quality dimension. They are bound
# through ComponentContext so the registry can call them uniformly.
COMPONENT_CHECKS: dict[QualityDimension, list[Callable[[ComponentContext], BaseCheck]]] = {
    QualityDimension.MAINTAINABILITY: [
        lambda ctx: get_hardcoded_configurations(ctx.node_data),
        lambda ctx: get_fan_in(ctx.graph, ctx.node_id),
        lambda ctx: get_fan_out(ctx.graph, ctx.node_id),
        lambda ctx: get_interface_size(ctx.node_data),
    ],
    QualityDimension.SUSTAINABILITY: [
        lambda ctx: get_default_value_completeness(ctx.node_data),
        lambda ctx: get_external_service_dependency(ctx.node_data, ctx.external_urls),
    ],
}
