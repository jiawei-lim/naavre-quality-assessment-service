import networkx as nx
from networkx.exception import NetworkXUnfeasible

from ..fair.fair_check_service import FairCheck
from ...types.result_types import (
    GraphCheckComponent,
    GraphCheckLink,
    GraphCheckResult,
    BaseCheck
)
from ...types.quality_dimensions import QualityDimension
from ...types.check_types import CheckType
from ...types.workflow_components import WorkflowComponent


THRESHOLDS = {
    "WORKFLOW_SIZE" : 31,
    "CNC": 3,
    "LONGEST_PATH" : 15
}

def get_size(graph: nx.MultiDiGraph) -> BaseCheck:
    size = len(graph.nodes)
    return BaseCheck(
            check_type = CheckType.WORKFLOW_SIZE,
            quality_dimension = QualityDimension.MAINTAINABILITY,
            quality_subcharacteristic= "analyzability",
            message = "Size of the workflow (number of nodes)",
            value = size,
            severity = "passed" if size <= THRESHOLDS["WORKFLOW_SIZE"] else "failed"
        )

def get_longest_path(graph: nx.MultiDiGraph) -> BaseCheck:
    try:
        value = nx.dag_longest_path_length(graph)
        return BaseCheck(
                check_type = CheckType.WORKFLOW_LONGEST_PATH,
                quality_dimension = QualityDimension.MAINTAINABILITY,
                quality_subcharacteristic= "analyzability",
                message = "Longest path of the workflow",
                value = value,
                severity = "failed" if value >= THRESHOLDS["LONGEST_PATH"] else "passed"
            )
    except NetworkXUnfeasible:
        return BaseCheck(
                check_type = CheckType.WORKFLOW_LONGEST_PATH,
                quality_dimension = QualityDimension.MAINTAINABILITY,
                quality_subcharacteristic= "analyzability",
                message = "Longest path of the workflow can not be assessed due to cycle",
                severity = "warning"
            )


def get_cnc(graph: nx.MultiDiGraph) -> BaseCheck:
    cnc  = round(len(graph.edges) / len(graph.nodes),2)
    return BaseCheck(
            check_type = CheckType.WORKFLOW_CNC,
            quality_dimension = QualityDimension.MAINTAINABILITY,
            quality_subcharacteristic= "analyzability",
            message = "Ration of components in workflow to number of edges",
            value =  cnc,
            severity = "failed" if cnc >= THRESHOLDS["CNC"] else "passed"
        )

def get_specification_completeness(graph: nx.MultiDiGraph) -> list[GraphCheckResult]:
    results = []

    for node_id, node_data in graph.nodes(data=True):
        component = node_data.get("component")
        if node_data.get("referenced_only") or component is None or node_data.get("node_type") != "workflow-cell":
            continue

        results.extend(
            GraphCheckResult(
                check_type=CheckType.SPECIFICATION_COMPLETENESS,
                quality_dimension=QualityDimension.FUNCTIONAL_SUITABILITY,
                quality_subcharacteristic="Completeness",
                severity="failed",
                message=f"Component '{node_id}' {issue}.",
                components=[_component_ref(graph, node_id)],
                links=[],
            )
            for issue in _incomplete_specifications(component)
        )

    if results == []:
        results.append(
            GraphCheckResult(
                check_type=CheckType.SPECIFICATION_COMPLETENESS,
                quality_dimension=QualityDimension.FUNCTIONAL_SUITABILITY,
                quality_subcharacteristic="Completeness",
                severity="passed",
                message="All components are fully specified",
                components=[],
                links=[],
            )
        )

    return results

def get_cycles(graph: nx.MultiDiGraph) -> list[GraphCheckResult]:
    """
    Graph Acyclicity
    """
    result = [
        GraphCheckResult(
            check_type=CheckType.GRAPH_ACYCLICITY,
            quality_dimension=QualityDimension.FUNCTIONAL_SUITABILITY,
            quality_subcharacteristic="Correctness",
            severity="failed",
            message="Workflow contains a directed cycle.",
            components=[_component_ref(graph, node_id) for node_id in cycle],
            links=_links_between_node_sequence(graph, cycle),
        )
        for cycle in nx.simple_cycles(graph)
    ]

    if result == []:
        result = [
            GraphCheckResult(
            check_type=CheckType.GRAPH_ACYCLICITY,
            quality_dimension=QualityDimension.FUNCTIONAL_SUITABILITY,
            quality_subcharacteristic="Correctness",
            severity="passed",
            message="Workflow does not contain a cycle.",
            components=[],
            links=[],
        )
        ]
    return  result


def get_input_output_type_mismatches(
    graph: nx.MultiDiGraph,
) -> list[GraphCheckResult]:
    """
    I/O mismatch check
    """
    results = []

    for from_node, to_node, _, edge_data in graph.edges(keys=True, data=True):
        from_port_name = edge_data.get("from_port_name")
        to_port_name = edge_data.get("to_port_name")
        from_type = _declared_port_type(graph, from_node, "outputs", from_port_name)
        to_type = _declared_port_type(graph, to_node, "inputs", to_port_name)
        from_label = _node_label(graph, from_node)
        to_label = _node_label(graph, to_node)

        if not from_type or not to_type or from_type == to_type:
            continue

        results.append(
            GraphCheckResult(
                check_type=CheckType.INPUT_OUTPUT_TYPE_MISMATCH,
                quality_dimension=QualityDimension.FUNCTIONAL_SUITABILITY,
                quality_subcharacteristic="Correctness",
                severity="failed",
                message=(
                    f"Link from '{from_label}.{from_port_name}' ({from_type}) "
                    f"to '{to_label}.{to_port_name}' ({to_type}) has mismatched "
                    "input/output types."
                ),
                components=[
                    _component_ref(graph, from_node),
                    _component_ref(graph, to_node),
                ],
                links=[_link_ref(from_node, to_node, edge_data)],
            )
        )

        if results == []:
            results.append(
                GraphCheckResult(
                check_type=CheckType.INPUT_OUTPUT_TYPE_MISMATCH,
                quality_dimension=QualityDimension.FUNCTIONAL_SUITABILITY,
                quality_subcharacteristic="Correctness",
                severity="passed",
                message="All input and output links have matching types",
                components=[],
                links=[],
                )
            )

    return results



def get_unfulfilled_inputs(graph: nx.MultiDiGraph) -> list[GraphCheckResult]:
    """
    Check if all inputs fulfilled
    """
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
                    check_type=CheckType.UNFULFILLED_INPUT,
                    quality_dimension=QualityDimension.FUNCTIONAL_SUITABILITY,
                    quality_subcharacteristic="Correctness",
                    severity="failed",
                    message=(
                        f"Input '{input_port.name}' of component '{node_id}' "
                        "is not fulfilled by any incoming link."
                    ),
                    components=[_component_ref(graph, node_id)],
                    links=[],
                )
            )

    if results == []:
        results.append(
            GraphCheckResult(
                check_type=CheckType.UNFULFILLED_INPUT,
                quality_dimension=QualityDimension.FUNCTIONAL_SUITABILITY,
                quality_subcharacteristic="Correctness",
                severity="passed",
                message="All inputs are fulfilled",
                components=[],
                links=[],
            )
        )

    return results


def get_invalid_links(graph: nx.MultiDiGraph) -> list[GraphCheckResult]:
    """
    Check for invalid links
    """
    results = [
        *_get_duplicate_links(graph),
        *_get_same_direction_port_links(graph),
    ]

    if results == []:
        results.append(
        GraphCheckResult(
            check_type=CheckType.INVALID_LINK,
            quality_dimension=QualityDimension.FUNCTIONAL_SUITABILITY,
            quality_subcharacteristic="Correctness",
            severity="passed",
            message="No invalid links are detected",
            components=[],
            links=[],
            )
        )

    return results


def get_shared_configurations(graph: nx.MultiDiGraph) -> list[GraphCheckResult]:
    """
    Configuration variable coupling check
    """
    nodes_by_conf: dict[tuple[str, str], list[str]] = {}

    for node_id, node_data in graph.nodes(data=True):
        if node_data.get("referenced_only") or node_data.get("node_type") != "workflow-cell":
            continue

        component = node_data.get("component")
        if component is None:
            continue

        for conf in component.configurations:
            nodes_by_conf.setdefault((conf.name, conf.assignation), []).append(node_id)

    return [
        GraphCheckResult(
            check_type=CheckType.SHARED_CONFIGURATION,
            quality_dimension=QualityDimension.MAINTAINABILITY,
            quality_subcharacteristic="Reusability",
            message=(
                f"Configuration '{conf_name}' ({assignation}) is shared by "
                f"{len(node_ids)} components."
            ),
            components=[_component_ref(graph, node_id) for node_id in node_ids],
            links=[],
            value = conf_name
        )
        for (conf_name, assignation), node_ids in nodes_by_conf.items()
        if len(node_ids) > 1
    ]


def run_fair_checks(graph: nx.MultiDiGraph) -> list[BaseCheck]:
    # Constructing FairCheck is what queries the metadata catalogue, so this is
    # only reached when the FAIR dimension was actually requested.
    return FairCheck(graph.graph["file_name"]).run_checks()


##################################
#        HELPER METHODS          #
##################################

def _component_ref(
    graph: nx.MultiDiGraph,
    node_id: str,
) -> GraphCheckComponent:
    """
    Format component for output
    """
    if node_id not in graph:
        return GraphCheckComponent(node_id=node_id)

    node_data = graph.nodes[node_id]
    component = node_data.get("component")

    return GraphCheckComponent(
        node_id=node_id,
        title=node_data.get("title") or getattr(component, "title", None),
        node_type=node_data.get("node_type"),
        component_ref=getattr(component, "component_ref", None),
    )


def _node_label(graph: nx.MultiDiGraph, node_id: str) -> str:
    """
    Human-readable name for a node, falling back to its id
    """
    if node_id not in graph:
        return node_id

    node_data = graph.nodes[node_id]

    return (
        node_data.get("title")
        or getattr(node_data.get("component"), "title", None)
        or node_id
    )


def _incomplete_specifications(component: WorkflowComponent) -> list[str]:
    base_image = component.base_container_image

    return [
        issue
        for issue, incomplete in [
            ("has no container image", not component.container_image),
            ("has no base container image build", not getattr(base_image, "build", None)),
            ("has no base container image runtime", not getattr(base_image, "runtime", None)),
            ("has no kernel", not component.kernel),
            ("is still a draft", component.is_draft),
        ]
        if incomplete
    ]


def _link_ref(
    from_node: str,
    to_node: str,
    edge_data: dict,
) -> GraphCheckLink:
    """
    Format edges for output
    """
    return GraphCheckLink(
        link_id=edge_data.get("link_id"),
        from_node_id=from_node,
        to_node_id=to_node,
        from_port_name=edge_data.get("from_port_name"),
        to_port_name=edge_data.get("to_port_name"),
    )


def _raw_link_ref(raw_link: dict) -> GraphCheckLink:
    from_data = raw_link.get("from", {}) if isinstance(raw_link, dict) else {}
    to_data = raw_link.get("to", {}) if isinstance(raw_link, dict) else {}

    return GraphCheckLink(
        link_id=raw_link.get("id") if isinstance(raw_link, dict) else None,
        from_node_id=from_data.get("nodeId"),
        to_node_id=to_data.get("nodeId"),
        from_port_name=from_data.get("portId"),
        to_port_name=to_data.get("portId"),
    )


def _links_between_node_sequence(
    graph: nx.MultiDiGraph,
    node_ids: list[str],
) -> list[GraphCheckLink]:
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
        from_label = _node_label(graph, from_node)
        to_label = _node_label(graph, to_node)
        results.append(
            GraphCheckResult(
                check_type=CheckType.INVALID_LINK,
                quality_dimension=QualityDimension.FUNCTIONAL_SUITABILITY,
                quality_subcharacteristic="Correctness",
                severity="failed",
                message=(
                    "Duplicate links from "
                    f"'{from_label}.{from_port_name}' to "
                    f"'{to_label}.{to_port_name}'."
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
                check_type=CheckType.INVALID_LINK,
                quality_dimension=QualityDimension.FUNCTIONAL_SUITABILITY,
                quality_subcharacteristic="Correctness",
                severity="failed",
                message=(
                    "Invalid "
                    f"{from_direction}-to-{to_direction} link from "
                    f"'{_node_label(graph, from_node)}.{from_port_name}' to "
                    f"'{_node_label(graph, to_node)}.{to_port_name}'."
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
