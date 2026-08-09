from .workflow_file.workflow_file_service import run_graph_checks
from .workflow_file.component_check_service import run_component_checks
from ..types.quality_dimensions import QualityDimension
import networkx as nx
from typing import Any, Collection

def run_checks(
    graph: nx.MultiDiGraph,
    dimensions: Collection[QualityDimension] | None = None,
) -> dict[str, Any]:
    dimensions = frozenset(dimensions) if dimensions else frozenset(QualityDimension)

    graph_check_result = run_graph_checks(graph, dimensions)
    component_check_result = run_component_checks(graph, dimensions)
    return {
        **graph_check_result,
        **component_check_result
    }
