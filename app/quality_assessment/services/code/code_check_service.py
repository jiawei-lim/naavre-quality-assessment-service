from dataclasses import dataclass

from radon import complexity, raw
from .github_client_service import get_raw_file
import ast
import re
import textwrap
from ...types.result_types import BaseCheck
from ...types.quality_dimensions import QualityDimension
from ...types.check_types import CheckType
from typing import Any, Callable
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


@dataclass(frozen=True)
class CodeCheckMeta:
    """Identity of a code check, so a degraded result cannot drift from the real one."""
    check_type: CheckType
    quality_dimension: QualityDimension
    message: str
    quality_subcharacteristic: str | None = None

    def result(self, severity: str, value = None) -> BaseCheck:
        return BaseCheck(
            check_type = self.check_type,
            quality_dimension = self.quality_dimension,
            quality_subcharacteristic = self.quality_subcharacteristic,
            message = self.message,
            severity = severity,
            value = value
        )

    def unavailable(self, reason: str) -> BaseCheck:
        return self.result("", reason)


LOC = CodeCheckMeta(
    check_type = CheckType.LOC,
    quality_dimension = QualityDimension.MAINTAINABILITY,
    quality_subcharacteristic = "analyzability",
    message = "The count of source code lines of the component",
)

CC = CodeCheckMeta(
    check_type = CheckType.CYCLOMATIC_COMPLEXITY,
    quality_dimension = QualityDimension.MAINTAINABILITY,
    quality_subcharacteristic = "analyzability",
    message = "The cyclomatic complexity of the source code of the component",
)


def get_loc(node:dict[str,Any], source:ComponentSource) -> BaseCheck | None:
    return _from_source(LOC, source, lambda code: _loc(node, code))

def get_cc(source:ComponentSource) -> BaseCheck | None:
    return _from_source(CC, source, _cc)

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

def _loc(node:dict[str,Any], code:str) -> BaseCheck:
    loc = raw.analyze(code).sloc

    component: WorkflowComponent = node.get("component")
    template_code_length = 8 + len(component.inputs) + len(component.parameters) + len(component.configurations) + (3 * len(component.outputs))
    loc -= template_code_length

    if loc <= 0:
        raise Exception("Negative or Zero LoC calculated")

    return LOC.result(
        "failed" if loc > THRESHOLDS["LOC"] else "passed",
        value = loc
    )

def _cc(code:str) -> BaseCheck:
    wrapped_code = _wrap_code(code)
    cc = complexity.cc_visit(wrapped_code)[0].complexity

    return CC.result(
        "failed" if cc > THRESHOLDS["CC"] else "passed",
        value = cc
    )

def _from_source(
    meta:CodeCheckMeta,
    source:ComponentSource,
    check:Callable[[str], BaseCheck],
) -> BaseCheck | None:
    if source.error:
        return meta.unavailable(source.error)

    if source.code is None:
        return None

    return _safe(meta, lambda: check(source.code))

def _safe(meta:CodeCheckMeta, check:Callable[[], BaseCheck]) -> BaseCheck:
    """Run a check, degrading it to a warning when the source cannot be analyzed."""
    try:
        return check()
    except Exception as error:
        return meta.unavailable(f"{meta.check_type} could not be computed: {error}")

def _wrap_code(code:str) -> str:
    return f"def generic():\n{textwrap.indent(code, '    ')}"
