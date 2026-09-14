from enum import StrEnum


class CheckType(StrEnum):
    # Workflow graph checks
    WORKFLOW_SIZE = "workflow_size"
    WORKFLOW_LONGEST_PATH = "workflow_longest_path"
    WORKFLOW_CNC = "workflow_cnc"
    SPECIFICATION_COMPLETENESS = "specification_completeness"
    GRAPH_ACYCLICITY = "graph_acyclicity"
    INPUT_OUTPUT_TYPE_MISMATCH = "input_output_type_mismatch"
    UNFULFILLED_INPUT = "unfulfilled_input"
    INVALID_LINK = "invalid_link"
    SHARED_CONFIGURATION = "shared_configuration"

    # Component checks
    FAN_IN = "fan_in"
    FAN_OUT = "fan_out"
    HARDCODED_CONFIGURATIONS = "hardcoded_configurations"
    INTERFACE_SIZE = "interface_size"
    DEFAULT_VALUE_COMPLETENESS = "default_value_completeness"
    EXTERNAL_SERVICE_DEPENDENCY = "external_service_dependency"

    # Component source code checks
    LOC = "loc"
    CYCLOMATIC_COMPLEXITY = "cyclomatic_complexity"

    # FAIR checks
    F4_REGISTERED = "f4_registered"
    F1_PERSISTENT = "f1_persistent"
    A1_PERSISTENT = "a1_persistent"
    F2_RICH = "f2_rich"
    R1_1_LICENSE = "r1.1_license"
    R1_1_COMPONENT_LICENSE = "r1.1_component_license"
