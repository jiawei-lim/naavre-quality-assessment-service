from dataclasses import asdict

from radon import complexity, raw
from .github_client_service import get_raw_file
import textwrap
from ...types.result_types import ValueCheckResult
import networkx as nx

def run_component_checks(graph:nx.MultiDiGraph) -> list[dict]:
    result = []
    for node_id, node_data in graph.nodes(data=True):
        node_source_url = node_data.get("source_url")
        if node_source_url:
            checks = run_code_checks(node_source_url + "/task.py")
            result.extend(serialize_code_check_results(checks))
    return result

def serialize_code_check_results(results: list[ValueCheckResult]) -> list[dict]:
    return [asdict(result) for result in results]

def run_code_checks(source_url:str) -> list[ValueCheckResult]:
    source_code = get_raw_file(source_url)

    loc = get_sloc(source_code)

    cc = get_cc(source_code)

    return [loc, cc]

def get_cc(code:str) -> int:
    wrapped_code = _wrap_code(code)

    return ValueCheckResult(
        check_type = "cyclomatic_complexity",
        quality_dimension = "maintainability",
        quality_subcharacteristic= "analyzability",
        message = "The cyclomatic complexity of the source code of the component",
        value = complexity.cc_visit(wrapped_code)[0].complexity
    )

def get_sloc(code:str) -> ValueCheckResult:
    return ValueCheckResult(
        check_type = "sloc",
        quality_dimension = "maintainability",
        quality_subcharacteristic= "analyzability",
        message = "The count of source code lines of the component",
        value = raw.analyze(code).sloc
    )

def _wrap_code(code:str) -> str:
    return f"def generic():\n{textwrap.indent(code, '    ')}"