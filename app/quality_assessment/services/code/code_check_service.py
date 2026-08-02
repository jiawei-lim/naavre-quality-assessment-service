from dataclasses import asdict

from radon import complexity, raw
from .github_client_service import get_raw_file
import ast
import re
import textwrap
from ...types.result_types import ValueCheckResult
from typing import Any

_URL_PATTERN = re.compile(r"(?:https?|ftps?|s3|gs)://\S+")

def run_code_checks(source_url:str) -> list[ValueCheckResult]:
    source_code = get_raw_file(source_url)
    raw_analysis = raw.analyze(source_code)

    loc = get_sloc(raw_analysis)

    cc = get_cc(source_code)

    urls = get_external_urls(source_code) 

    return (loc, cc, urls)

def get_cc(code:str) -> ValueCheckResult:
    wrapped_code = _wrap_code(code)

    return ValueCheckResult(
        check_type = "cyclomatic_complexity",
        quality_dimension = "maintainability",
        quality_subcharacteristic= "analyzability",
        message = "The cyclomatic complexity of the source code of the component",
        value = complexity.cc_visit(wrapped_code)[0].complexity
    )

def get_sloc(raw_analysis) -> ValueCheckResult:
    return ValueCheckResult(
        check_type = "sloc",
        quality_dimension = "maintainability",
        quality_subcharacteristic= "analyzability",
        message = "The count of source code lines of the component",
        value = raw_analysis.sloc
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