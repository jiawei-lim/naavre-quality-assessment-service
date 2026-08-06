from dataclasses import asdict

import networkx as nx
from typing import Any
from ..code.code_check_service import *
from ...types.result_types import ValueCheckResult, ComponentCheckResult
from ...adapters.workflow_components import WorkflowComponent

THRESHOLDS = {
    "INTERFACE_SIZE" : 7,
    "FAN_IN" : 5,
    "FAN_OUT" : 5
}


def run_component_checks(graph:nx.MultiDiGraph) -> dict[str, Any]:
    component_check_results = []
    for node_id, node_data in graph.nodes(data=True):
        if node_data.get("node_type") == "workflow-cell":
            checks = []
            source_url = node_data.get("source_url")
            if source_url:
                loc,cc,urls = run_code_checks(node_data,source_url + "/task.py")
                checks += [loc,cc]

            checks += [
                get_hardcoded_configurations(node_data),
                get_fan_in(graph, node_id),
                get_fan_out(graph, node_id),
                get_interface_size(node_data),
                get_default_value_completeness(node_data),
                get_external_service_dependency(node_data,urls)
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
    fan_in = len(set(graph.predecessors(node_id)))
    return ValueCheckResult(
            check_type = "fan_in",
            quality_dimension = "maintainability",
            quality_subcharacteristic= "modularity",
            message = "The number of distinct components that the component takes input from",
            value = fan_in,
            severity = "failed" if fan_in >= THRESHOLDS["FAN_IN"] else "passed"
        )

def get_fan_out(graph:nx.MultiDiGraph, node_id:str) -> ValueCheckResult:
    fan_out = len(set(graph.successors(node_id)))
    return ValueCheckResult(
            check_type = "fan_out",
            quality_dimension = "maintainability",
            quality_subcharacteristic= "modularity",
            message = "The number of links that have the component as a source",
            value = fan_out,
            severity = "failed" if fan_out >= THRESHOLDS["FAN_OUT"] else "passed"
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
    component:WorkflowComponent = node.get("component")
    inputs = len(component.inputs)
    parameters = len(component.parameters)
    return ValueCheckResult(
        check_type = "interface_size",
        quality_dimension = "maintainability",
        quality_subcharacteristic= "modularity",
        message = "Interface size of the component",
        value = inputs + parameters,
        severity = "failed" if (inputs + parameters) > THRESHOLDS["INTERFACE_SIZE"] else "passed"
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

def get_external_service_dependency(node:dict[str,Any],urls:ValueCheckResult) -> ValueCheckResult:
    component = node.get("component")
    secrets = component.secrets

    if len(secrets) > 0 or len(urls.value) > 0:
        return ValueCheckResult(
            check_type = "external_service_dependency",
            quality_dimension = "sustainability",
            quality_subcharacteristic= None,
            message = "Calls to external services increases exposure to decay",
            value = urls.value + secrets,
            severity = "warning"
        )

    return ValueCheckResult(
            check_type = "external_service_dependency",
            quality_dimension = "sustainability",
            quality_subcharacteristic= None,
            message = "No calls to external services detected",
            severity = "passed"
        )
