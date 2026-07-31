from .code.code_check_service import run_component_checks
from .workflow_file.workflow_file_service import run_graph_checks
import networkx as nx
from typing import Any

def run_checks(graph: nx.MultiDiGraph) -> dict[str, Any]:
    graph_check_result = run_graph_checks(graph)
    code_check_result = run_component_checks(graph)

    return {
        **graph_check_result,
        "component_checks": code_check_result,
    }