import networkx as nx

from quality_assessment.types import WorkflowFile


def build_workflow_multidigraph(
    workflow_file: WorkflowFile,
) -> nx.MultiDiGraph:
    graph = nx.MultiDiGraph()

    #Graph level Metadata
    graph.graph.update(
        {
            "asset_type": "workflow_file",
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


def _ensure_referenced_node(graph: nx.MultiDiGraph, node_id: str) -> None:
    if node_id not in graph:
        graph.add_node(node_id, referenced_only=True)
