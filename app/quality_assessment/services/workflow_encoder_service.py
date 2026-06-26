import json
from typing import Any

import networkx as nx


def encode_workflow_graph_for_semantic_analysis(
    graph: nx.MultiDiGraph,
) -> str:
    return json.dumps(
        _encode_workflow_graph_for_semantic_analysis_payload(graph),
        sort_keys=True,
    )


def _encode_workflow_graph_for_semantic_analysis_payload(
    graph: nx.MultiDiGraph,
) -> dict[str, Any]:
    return {
        "workflow": _encode_workflow_metadata(graph),
        "nodes": [
            _encode_node(node_id, node_data)
            for node_id, node_data in sorted(
                graph.nodes(data=True),
                key=lambda item: _sort_value(item[0]),
            )
        ],
        "links": _encode_links(graph),
        "invalid_links": _encode_invalid_links(
            graph.graph.get("invalid_links", [])
        ),
    }


def _encode_workflow_metadata(graph: nx.MultiDiGraph) -> dict[str, Any]:
    return {
        "id": graph.graph.get("asset_id"),
        "asset_type": graph.graph.get("asset_type"),
        "title": graph.graph.get("title"),
        "description": graph.graph.get("description")
    }


def _encode_node(node_id: str, node_data: dict[str, Any]) -> dict[str, Any]:
    if node_data.get("referenced_only"):
        return {
            "id": node_id,
            "referenced_only": True,
        }

    component = node_data.get("component")

    return {
        "id": node_id,
        "node_type": node_data.get("node_type"),
        "referenced_only": False,
        "title": node_data.get("title") or getattr(component, "title", None),
        "description": getattr(component, "description", None),
        "component_ref": getattr(component, "component_ref", None),
        "version": getattr(component, "version", None),
        "inputs": _encode_ports(getattr(component, "inputs", [])),
        "outputs": _encode_ports(getattr(component, "outputs", [])),
        "parameters": _encode_parameters(
            getattr(component, "parameters", [])
        ),
        "configurations": _encode_configurations(
            getattr(component, "configurations", [])
        ),
        "dependencies": _encode_dependencies(
            getattr(component, "dependencies", [])
        ),
        "runtime": _encode_runtime(node_data, component),
    }


def _encode_links(graph: nx.MultiDiGraph) -> list[dict[str, Any]]:
    links = [
        _encode_link(from_node, to_node, edge_key, edge_data)
        for from_node, to_node, edge_key, edge_data in graph.edges(
            keys=True,
            data=True,
        )
    ]

    return sorted(
        links,
        key=lambda link: (
            _sort_value(link.get("id")),
            _sort_value(link.get("from_node_id")),
            _sort_value(link.get("to_node_id")),
            _sort_value(link.get("from_port_name")),
            _sort_value(link.get("to_port_name")),
        ),
    )


def _encode_link(
    from_node: str,
    to_node: str,
    edge_key: str,
    edge_data: dict[str, Any],
) -> dict[str, Any]:
    return {
        "id": edge_data.get("link_id") or edge_key,
        "from_node_id": from_node,
        "from_port_name": edge_data.get("from_port_name"),
        "to_node_id": to_node,
        "to_port_name": edge_data.get("to_port_name"),
    }


def _encode_invalid_links(
    invalid_links: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    encoded_links = [
        _encode_invalid_link(raw_link)
        for raw_link in invalid_links
        if isinstance(raw_link, dict)
    ]

    return sorted(
        encoded_links,
        key=lambda link: (
            _sort_value(link.get("id")),
            _sort_value(link.get("from_node_id")),
            _sort_value(link.get("to_node_id")),
            _sort_value(link.get("from_port_name")),
            _sort_value(link.get("to_port_name")),
        ),
    )


def _encode_invalid_link(raw_link: dict[str, Any]) -> dict[str, Any]:
    from_data = raw_link.get("from", {})
    to_data = raw_link.get("to", {})

    if not isinstance(from_data, dict):
        from_data = {}

    if not isinstance(to_data, dict):
        to_data = {}

    return {
        "id": raw_link.get("id"),
        "from_node_id": from_data.get("nodeId"),
        "from_port_name": from_data.get("portId"),
        "to_node_id": to_data.get("nodeId"),
        "to_port_name": to_data.get("portId"),
    }


def _encode_ports(ports: list[Any]) -> list[dict[str, Any]]:
    return [
        {
            "name": port.name,
            "type": port.type,
        }
        for port in ports
    ]


def _encode_parameters(parameters: list[Any]) -> list[dict[str, Any]]:
    return [
        {
            "name": parameter.name,
            "type": parameter.type,
            "has_default": parameter.default_value is not None,
        }
        for parameter in parameters
    ]


def _encode_configurations(configurations: list[Any]) -> list[dict[str, Any]]:
    return [
        {
            "name": configuration.name,
        }
        for configuration in configurations
    ]


def _encode_dependencies(dependencies: list[Any]) -> list[dict[str, Any]]:
    return [
        {
            "name": dependency.name,
            "module": dependency.module,
            "asname": dependency.asname,
        }
        for dependency in dependencies
    ]


def _encode_runtime(
    node_data: dict[str, Any],
    component: Any,
) -> dict[str, Any]:
    return {
        "container_image": node_data.get("container_image")
        or getattr(component, "container_image", None),
        "base_container_image": _encode_base_container_image(
            getattr(component, "base_container_image", None)
        ),
        "kernel": getattr(component, "kernel", None),
    }


def _encode_base_container_image(base_container_image: Any) -> dict[str, Any] | None:
    if base_container_image is None:
        return None

    return {
        "build": getattr(base_container_image, "build", None),
        "runtime": getattr(base_container_image, "runtime", None),
    }


def _sort_value(value: Any) -> str:
    if value is None:
        return ""

    return str(value)
