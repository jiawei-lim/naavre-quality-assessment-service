from dataclasses import asdict

import networkx as nx
from typing import Any
from ..code.code_check_service import run_code_checks
from ...types.result_types import ValueCheckResult, ComponentCheckResult

def run_component_checks(graph:nx.MultiDiGraph) -> dict[str, Any]:
    component_check_results = []
    for node_id, node_data in graph.nodes(data=True):
        if node_data.get("node_type") == "workflow-cell":
            checks = []
            source_url = node_data.get("source_url")
            if source_url:
                checks += run_code_checks(source_url + "/task.py")

            checks += [
                get_hardcoded_configurations(node_data),
                get_fan_in(graph, node_id),
                get_fan_out(graph, node_id),
                get_interface_size(node_data),
                get_default_value_completeness(node_data),
            ]

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

def get_fan_in(graph:nx.MultiDiGraph, node_id:str) -> ValueCheckResult:
    return ValueCheckResult(
            check_type = "fan_in",
            quality_dimension = "maintainability",
            quality_subcharacteristic= "modularity",
            message = "The number of links that have the component as a destination",
            value = graph.in_degree(node_id)
        )

def get_fan_out(graph:nx.MultiDiGraph, node_id:str) -> ValueCheckResult:
    return ValueCheckResult(
            check_type = "fan_out",
            quality_dimension = "maintainability",
            quality_subcharacteristic= "modularity",
            message = "The number of links that have the component as a source",
            value = graph.out_degree(node_id)
        )

def get_hardcoded_configurations(node:dict[str,Any]) -> ValueCheckResult:
    component = node.get("component")
    confs = component.configurations
    return ValueCheckResult(
            check_type = "hardcoded_configurations",
            quality_dimension = "maintainability",
            quality_subcharacteristic= "reusability",
            message = "The number of unchangeable containerized configurations",
            value = confs
        )

def get_interface_size(node:dict[str,Any]) -> ValueCheckResult:
    component = node.get("component")
    inputs = len(component.inputs)
    outputs = len(component.outputs)
    parameters = len(component.parameters)
    secrets = len(component.secrets)
    return ValueCheckResult(
        check_type = "interface_size",
        quality_dimension = "maintainability",
        quality_subcharacteristic= "modularity",
        message = "Interface size of the component",
        value = inputs + outputs + parameters + secrets
    )

def get_default_value_completeness(node:dict[str,Any]) -> ValueCheckResult:
    component = node.get("component")
    parameters = component.parameters
    if len(parameters) > 0 :
        parameters_no_default = [param for param in parameters if not param.default_value]
        if len(parameters_no_default) > 0:
            return ValueCheckResult(
                check_type = "default_value_completeness",
                quality_dimension = "sustainability",
                quality_subcharacteristic= None,
                message = "Parameters should have default values",
                severity = "warning",
                value = parameters_no_default,
            )

    return ValueCheckResult(
            check_type = "default_value_completeness",
            quality_dimension = "sustainability",
            quality_subcharacteristic= None,
            message = "Parameters should have default values",
            severity = "passed"
        )
