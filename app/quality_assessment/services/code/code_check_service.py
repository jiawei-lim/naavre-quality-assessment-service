from dataclasses import asdict, dataclass

from radon import complexity, raw
from .github_client_service import get_raw_file
import ast
import re
import textwrap
from ...types.result_types import BaseCheck
from ...types.quality_dimensions import QualityDimension
from typing import Any, Callable, Collection
from ...adapters.workflow_components import WorkflowComponent


_URL_PATTERN = re.compile(r"(?:https?|ftps?|s3|gs)://\S+")
THRESHOLDS = {
    "LOC" : 60,
    "CC" : 25,
}


@dataclass(frozen=True)
class CodeCheckMeta:
    """Identity of a code check, so a degraded result cannot drift from the real one."""
    check_type: str
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
        return self.result("warning", reason)


LOC = CodeCheckMeta(
    check_type = "loc",
    quality_dimension = QualityDimension.MAINTAINABILITY,
    quality_subcharacteristic = "analyzability",
    message = "The count of source code lines of the component",
)

CC = CodeCheckMeta(
    check_type = "cyclomatic_complexity",
    quality_dimension = QualityDimension.MAINTAINABILITY,
    quality_subcharacteristic = "analyzability",
    message = "The cyclomatic complexity of the source code of the component",
)

EXTERNAL_URLS = CodeCheckMeta(
    check_type = "external_service_dependency",
    quality_dimension = QualityDimension.SUSTAINABILITY,
    message = "The number of distinct external URLs used by the component",
)


def run_code_checks(
    node:dict[str,Any],
    source_url:str,
    dimensions:Collection[QualityDimension],
) -> tuple[list[BaseCheck], BaseCheck | None]:
    requiresMaintainability = QualityDimension.MAINTAINABILITY in dimensions
    requiresUrl = QualityDimension.SUSTAINABILITY in dimensions

    if not (requiresMaintainability or requiresUrl):
        return [], None

    # Components written in another language have no task.py to fetch. Degrade the
    # code checks to warnings instead of failing the whole assessment.
    try:
        source_code = get_raw_file(source_url)
    except Exception as error:
        reason = f"Source code could not be retrieved"
        checks = [LOC.unavailable(reason), CC.unavailable(reason)] if requiresMaintainability else []
        return checks, (EXTERNAL_URLS.unavailable(reason) if requiresUrl else None)

    checks = []
    if requiresMaintainability:
        checks += [
            _safe(LOC, lambda: get_loc(node, raw.analyze(source_code))),
            _safe(CC, lambda: get_cc(source_code)),
        ]

    urls = _safe(EXTERNAL_URLS, lambda: get_external_urls(source_code)) if requiresUrl else None

    return checks, urls

def get_cc(code:str) -> BaseCheck:
    wrapped_code = _wrap_code(code)
    cc = complexity.cc_visit(wrapped_code)[0].complexity

    return CC.result(
        "failed" if cc > THRESHOLDS["CC"] else "passed",
        value = cc
    )

def get_loc(node:dict[str,Any],raw_analysis) -> BaseCheck:
    loc = raw_analysis.sloc

    component: WorkflowComponent = node.get("component")
    template_code_length = 8 + len(component.inputs) + len(component.parameters) + len(component.configurations) + (3 * len(component.outputs))
    loc -= template_code_length

    if loc <= 0:
        raise Exception("Negative or Zero LoC calculated")

    return LOC.result(
        "failed" if loc > THRESHOLDS["LOC"] else "passed",
        value = loc
    )

def get_comment_density(raw_analysis) -> BaseCheck:
    return BaseCheck(
        check_type = "comment_density",
        quality_dimension = QualityDimension.MAINTAINABILITY,
        quality_subcharacteristic= "analyzability",
        message = "Ratio of code comments to source code size",
        value = (raw_analysis.comments / raw_analysis.sloc)
    )

def get_external_urls(code:str) -> BaseCheck:
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

    return EXTERNAL_URLS.result(None, value = urls)

def _safe(meta:CodeCheckMeta, check:Callable[[], BaseCheck]) -> BaseCheck:
    """Run a check, degrading it to a warning when the source cannot be analyzed."""
    try:
        return check()
    except Exception as error:
        return meta.unavailable(f"{meta.check_type} could not be computed: {error}")

def _wrap_code(code:str) -> str:
    return f"def generic():\n{textwrap.indent(code, '    ')}"
