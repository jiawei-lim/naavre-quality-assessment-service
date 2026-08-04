from dataclasses import asdict

from radon import complexity, raw
from .github_client_service import get_raw_file
import ast
import re
import textwrap
from ...types.result_types import ValueCheckResult
from typing import Any
from ...adapters.workflow_components import WorkflowComponent


_URL_PATTERN = re.compile(r"(?:https?|ftps?|s3|gs)://\S+")
THRESHOLDS = {
    "LOC" : 60,
    "CC" : 25,
}

def run_code_checks(node:dict[str,Any],source_url:str) -> list[ValueCheckResult]:
    source_code = get_raw_file(source_url)
    raw_analysis = raw.analyze(source_code)

    loc = get_loc(node,raw_analysis)

    cc = get_cc(source_code)

    urls = get_external_urls(source_code) 

    return (loc, cc, urls)

def get_cc(code:str) -> ValueCheckResult:
    wrapped_code = _wrap_code(code)
    cc = complexity.cc_visit(wrapped_code)[0].complexity

    return ValueCheckResult(
        check_type = "cyclomatic_complexity",
        quality_dimension = "maintainability",
        quality_subcharacteristic= "analyzability",
        message = "The cyclomatic complexity of the source code of the component",
        value = cc,
        severity = "failed" if cc > THRESHOLDS["CC"] else "passed"
    )

def get_loc(node:dict[str,Any],raw_analysis) -> ValueCheckResult:
    loc = raw_analysis.sloc

    component: WorkflowComponent = node.get("component")
    template_code_length = 8 + len(component.inputs) + len(component.parameters) + len(component.configurations) + (3 * len(component.outputs))
    loc -= template_code_length

    if loc <= 0:
        raise Exception("Negative or Zero LoC calculated")

    return ValueCheckResult(
        check_type = "loc",
        quality_dimension = "maintainability",
        quality_subcharacteristic= "analyzability",
        message = "The count of source code lines of the component",
        value = loc,
        severity = "failed" if loc > THRESHOLDS["LOC"] else "passed"
    )

def get_comment_density(raw_analysis) -> ValueCheckResult:
    return ValueCheckResult(
        check_type = "comment_density",
        quality_dimension = "maintainability",
        quality_subcharacteristic= "analyzability",
        message = "Ratio of code comments to source code size",
        value = (raw_analysis.comments / raw_analysis.sloc)
    )

def get_external_urls(code:str) -> ValueCheckResult:
    tree = ast.parse(code)

    docstrings = {
        id(node.value)
        for node in ast.walk(tree)
        if isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant)
    }

    urls = [
        url
        for node in ast.walk(tree)
        if isinstance(node, ast.Constant)
        and isinstance(node.value, str)
        and id(node) not in docstrings
        for url in _URL_PATTERN.findall(node.value)
    ]

    return ValueCheckResult(
        check_type = "external_service_dependency",
        quality_dimension = "sustainability",
        message = "The number of distinct external URLs used by the component",
        value = urls
    )

def _wrap_code(code:str) -> str:
    return f"def generic():\n{textwrap.indent(code, '    ')}"