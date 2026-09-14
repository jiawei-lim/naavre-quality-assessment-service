"""Tooltip text explaining what each check means.

Served by the quality model endpoint so the frontend can explain a result to the
user without hardcoding anything about the checks themselves.

Keys are CheckType members, so a typo fails at import rather than silently
producing a tooltip nothing looks up.
"""

from .types.check_types import CheckType


TOOLTIPS: dict[CheckType, str] = {

    # Workflow graph
    CheckType.WORKFLOW_SIZE: "",
    CheckType.WORKFLOW_LONGEST_PATH: "The maximum length between two components in the workflow",
    CheckType.WORKFLOW_CNC: "",
    CheckType.SPECIFICATION_COMPLETENESS: "Checks that all components have an Image, Build Image, Runtime Image and Kernel specified",
    CheckType.GRAPH_ACYCLICITY: "Checks if there are any cycles formed on the workflow",
    CheckType.INPUT_OUTPUT_TYPE_MISMATCH: "Checks component links to ensure matching data types between ports",
    CheckType.UNFULFILLED_INPUT: "Checks if every component's input ports in the workflow are connected",
    CheckType.INVALID_LINK: "Checks for duplicated links (Links with the same component and ports) and invalid link direction (Input to Output, Output to Output, Input to Input)",
    CheckType.SHARED_CONFIGURATION: "Highlights configuration variables of the same value among components",

    # Component
    CheckType.FAN_IN: "",
    CheckType.FAN_OUT: "",
    CheckType.HARDCODED_CONFIGURATIONS: "",
    CheckType.INTERFACE_SIZE: "The sum of parameters and input ports of the component",
    CheckType.DEFAULT_VALUE_COMPLETENESS: "Checks if every parameter is supplied with a default value",
    CheckType.EXTERNAL_SERVICE_DEPENDENCY: "Checks if the component relies on externel web services",

    # Component source code
    CheckType.LOC: "Calculated through counting non-empty, non-comment code lines, subtracting template code lines",
    CheckType.CYCLOMATIC_COMPLEXITY: "Calculates the complexity of code through counting decision points. Read more at: https://radon.readthedocs.io/en/latest/api.html#module-radon.complexity",

    # FAIR
    CheckType.F4_REGISTERED: "Checks if the current workflow is registered in the metadata catalogue",
    CheckType.F1_PERSISTENT: "Checks if a DOI exists",
    CheckType.A1_PERSISTENT: "",
    CheckType.F2_RICH: "Checks if existing metadata fulfils all Dublin Core fields",
    CheckType.R1_1_LICENSE: "",
    CheckType.R1_1_COMPONENT_LICENSE: "",
}
