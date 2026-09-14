from dataclasses import dataclass
from functools import cached_property

import networkx as nx
from typing import Any
from ..code.code_check_service import ComponentSource, fetch_source, get_external_urls
from ...types.result_types import BaseCheck
from ...types.quality_dimensions import QualityDimension
from ...types.check_types import CheckType
from ...adapters.workflow_components import WorkflowComponent

THRESHOLDS = {
    "INTERFACE_SIZE" : 7,
    "FAN_IN" : 5,
    "FAN_OUT" : 5
}

@dataclass
class ComponentContext:
    """Everything a component check may need, so they share one call signature."""
    graph: nx.MultiDiGraph
    node_id: str
    node_data: dict[str, Any]

    @cached_property
    def source(self) -> ComponentSource:
        """Fetched at most once per component, and only if a check asks for it."""
        return fetch_source(self.node_data.get("source_url"))


def get_fan_in(graph:nx.MultiDiGraph, node_id:str) -> BaseCheck:
    fan_in = len(set(graph.predecessors(node_id)))
    return BaseCheck(
            check_type = CheckType.FAN_IN,
            quality_dimension = QualityDimension.MAINTAINABILITY,
            quality_subcharacteristic= "modularity",
            message = "The number of distinct components that the component takes input from",
            value = fan_in,
            severity = "failed" if fan_in >= THRESHOLDS["FAN_IN"] else "passed"
        )

def get_fan_out(graph:nx.MultiDiGraph, node_id:str) -> BaseCheck:
    fan_out = len(set(graph.successors(node_id)))
    return BaseCheck(
            check_type = CheckType.FAN_OUT,
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
            check_type = CheckType.HARDCODED_CONFIGURATIONS,
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
        check_type = CheckType.INTERFACE_SIZE,
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
                check_type = CheckType.DEFAULT_VALUE_COMPLETENESS,
                quality_dimension = QualityDimension.SUSTAINABILITY,
                quality_subcharacteristic= None,
                message = "Parameters should have default values",
                severity = "warning",
                value = parameters_no_default,
            )

    return BaseCheck(
            check_type = CheckType.DEFAULT_VALUE_COMPLETENESS,
            quality_dimension = QualityDimension.SUSTAINABILITY,
            quality_subcharacteristic= None,
            message = "Parameters should have default values",
            severity = "passed"
        )

def get_external_service_dependency(
    node:dict[str,Any],
    source:ComponentSource,
) -> BaseCheck:
    component = node.get("component")
    secrets = component.secrets

    external_urls, unavailable = [], source.error
    if source.code is not None:
        try:
            external_urls = get_external_urls(source.code)
        except Exception as error:
            unavailable = f"external_service_dependency could not be computed: {error}"

    if unavailable:
        return BaseCheck(
            check_type = CheckType.EXTERNAL_SERVICE_DEPENDENCY,
            quality_dimension = QualityDimension.SUSTAINABILITY,
            quality_subcharacteristic= None,
            message = "External service dependencies could not be determined",
            value = unavailable,
            severity = ""
        )

    if len(secrets) > 0 or len(external_urls) > 0:
        return BaseCheck(
            check_type = CheckType.EXTERNAL_SERVICE_DEPENDENCY,
            quality_dimension = QualityDimension.SUSTAINABILITY,
            quality_subcharacteristic= None,
            message = "Calls to external services increases exposure to decay",
            value = external_urls + secrets,
            severity = "warning"
        )

    return BaseCheck(
            check_type = CheckType.EXTERNAL_SERVICE_DEPENDENCY,
            quality_dimension = QualityDimension.SUSTAINABILITY,
            quality_subcharacteristic= None,
            message = "No calls to external services detected",
            severity = "passed"
        )
