from dataclasses import dataclass

from radon import complexity, raw
from .github_client_service import get_raw_file
import ast
import re
import textwrap
from ...types.result_types import BaseCheck
from ...types.quality_dimensions import QualityDimension
from ...types.check_types import CheckType
from typing import Any
from ...adapters.workflow_components import WorkflowComponent


_URL_PATTERN = re.compile(r"(?:https?|ftps?|s3|gs)://\S+")
THRESHOLDS = {
    "LOC" : 60,
    "CC" : 25,
}

@dataclass(frozen=True)
class ComponentSource:
    code: str | None = None
    error: str | None = None


def fetch_source(source_url: str | None) -> ComponentSource:
    if not source_url:
        return ComponentSource()
    try:
        return ComponentSource(code = get_raw_file(source_url + "/task.py"))
    except Exception:
        return ComponentSource(error = "Source code could not be retrieved")


def get_loc(node:dict[str,Any], source:ComponentSource) -> BaseCheck | None:
    if source.error:
        return BaseCheck(
            check_type = CheckType.LOC,
            quality_dimension = QualityDimension.MAINTAINABILITY,
            quality_subcharacteristic = "analyzability",
            message = "The count of source code lines of the component",
            severity = "",
            value = source.error,
        )

    if source.code is None:
        return None

    loc = raw.analyze(source.code).sloc

    component: WorkflowComponent = node.get("component")
    template_code_length = 8 + ( 2 * len(component.inputs) ) + ( 2 * len(component.parameters) )+ len(component.configurations) + (3 * len(component.outputs) + len(component.secrets) + len(component.dependencies) )
    loc -= template_code_length

    if loc <= 0:
        raise Exception("Negative or Zero LoC calculated")

    return BaseCheck(
        check_type = CheckType.LOC,
        quality_dimension = QualityDimension.MAINTAINABILITY,
        quality_subcharacteristic = "analyzability",
        message = "The count of source code lines of the component",
        severity = "failed" if loc > THRESHOLDS["LOC"] else "passed",
        value = loc,
    )

def get_cc(source:ComponentSource) -> BaseCheck | None:
    if source.error:
        return BaseCheck(
            check_type = CheckType.CYCLOMATIC_COMPLEXITY,
            quality_dimension = QualityDimension.MAINTAINABILITY,
            quality_subcharacteristic = "analyzability",
            message = "The cyclomatic complexity of the source code of the component",
            severity = "",
            value = source.error,
        )

    if source.code is None:
        return None

    wrapped_code = _wrap_code(source.code)
    cc = _total_cc(complexity.cc_visit(wrapped_code)[0])

    return BaseCheck(
        check_type = CheckType.CYCLOMATIC_COMPLEXITY,
        quality_dimension = QualityDimension.MAINTAINABILITY,
        quality_subcharacteristic = "analyzability",
        message = "The cyclomatic complexity of the source code of the component",
        severity = "failed" if cc > THRESHOLDS["CC"] else "passed",
        value = cc,
    )

def get_comment_density(code:str) -> BaseCheck:
    raw_analysis = raw.analyze(code)
    return BaseCheck(
        check_type = "comment_density",
        quality_dimension = QualityDimension.MAINTAINABILITY,
        quality_subcharacteristic= "analyzability",
        message = "Ratio of code comments to source code size",
        value = (raw_analysis.comments / raw_analysis.sloc)
    )

def get_external_urls(code:str) -> list[str]:
    tree = ast.parse(code)

    docstrings = {
        id(node.value)
        for node in ast.walk(tree)
        if isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant)
    }

    return [
        url
        for node in ast.walk(tree)
        if isinstance(node, ast.Constant)
        and isinstance(node.value, str)
        and id(node) not in docstrings
        for url in _URL_PATTERN.findall(node.value)
    ]


##################################
#        HELPER METHODS          #
##################################

def _wrap_code(code:str) -> str:
    return f"def generic():\n{textwrap.indent(code, '    ')}"

def _total_cc(block) -> int:
    return block.complexity + sum(_total_cc(c) for c in getattr(block, "closures", []))