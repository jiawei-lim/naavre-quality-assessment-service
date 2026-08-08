import json

import networkx as nx

from .llm_client_service import LLMMessage, LLMRequest, get_llm_client
from .workflow_encoder_service import encode_workflow_graph_for_semantic_analysis

SYSTEM_PROMPT = """
You are a semantic quality assessor for NaaVRE scientific workflows.

Your task is to assess scientific workflow descriptions represented as structured JSON. The workflows consist of components, inputs, outputs, parameters, metadata, and data-flow relations. 
You evaluate whether the workflow is semantically coherent and whether it satisfies the provided workflow quality dimensions.

There are two system pre-defined nodes, which are the Splitter and Merger. 
The 'splitter' component takes a list as an input, and outputs a list to parallelize computation in the next workflow component. 
The 'merger' component is used to merge the outputs of multiple cells into a single array.
Not all outputs from a component is mandatory to be utilized by another component.

You must use only the information provided in the workflow JSON and the provided quality-dimension definitions. 
Do not invent missing metadata, component behavior, domain assumptions, or hidden workflow steps. 

Focus on semantic workflow quality. Assess whether components, artifacts, inputs, outputs, parameters, metadata, and relations make sense with respect to the stated workflow goal and the given quality dimensions.

Do not focus on purely structural graph properties unless they are relevant to a stated quality dimension. For example, do not perform generic checks such as cycle detection, graph connectivity, or topological validity unless the quality dimension explicitly requires them.

Return only valid JSON. Do not include Markdown, prose outside the JSON, or explanatory text before or after the JSON.
If there are no detected issues, return {"semantic_checks": []}.
Only include detected semantic issues. Never include checks whose conclusion is "no issue", "compatible", "consistent", or "no clear incompatibility detected".
Do not mention compatible or logically consistent links in an issue message. The message must describe only the single detected problem.
The JSON response must follow this structure:
{
    "semantic_checks": [
        {
            "check_type": "semantic_type_compatibility or component_purpose_alignment or workflow anti-patterns",
            "quality_dimension: "Functional Suitability",
            "quality_subcharacteristic":"Appropriateness",
            "severity": "always output as warning",
            "message": "Explain the semantic issue clearly.",
            "components": [
                {
                    "node_id": "node GUID",
                    "title": "Component title if available",
                    "node_type": "cell_type",
                    "component_ref": "component_ref if available"
                }
            ],
            "links": [
                {
                    "link_id": "link id",
                    "from_node_id": "source node GUID",
                    "to_node_id": "target node GUID",
                    "from_port_name": "output_port",
                    "to_port_name": "input_port"
                }
            ]
        }
    ]
}

The check_type value must be exactly one of:
- "semantic_type_compatibility"
- "component_purpose_alignment"
- "workflow anti-patterns"

Each object in semantic_checks must correspond to exactly one detected issue instance.
Do not combine multiple problems, multiple unrelated links, or multiple unrelated components into one semantic check.
The same check_type may appear multiple times when the same kind of issue occurs in multiple places.
If multiple issues are detected on a same set of components and links, return one separate object per issue instance.
If a quality dimension has no detected issue, omit it entirely from semantic_checks.
"""

def get_semantic_type_incompatibility() -> str:
    return """
    You need to check for Semantic Type Compatibility. This means you need to check for the input and output links and relationship between components, and ensure that they are logically compatible.
    For example, a component that outputs a list of temperature would not be semantically compatible with a component that accepts a list of weight.
    """

def get_component_purpose_incompatibility() -> str:
    return """
    You need to check for Component-purpose alignment. This means you need to ensure that components in a workflow are all aligned with the domain. For example, a component which explicitly belongs in the life sciences domain,
    should not belong in a workflow tailored for the physical sciences domain. 
    """

def get_workflow_antipatterns() -> str:
    return """
    You need to check for Workflow Anti-Patterns. This means you need to ensure that workflow steps flow logically. For example, a workflow which visualizes results is used before data generation, or
    running a model before preprocessing.
    """ 


def get_semantic_checks(graph: nx.MultiDiGraph) -> list[dict]:
    client = get_llm_client()
    encoded_workflow_file = encode_workflow_graph_for_semantic_analysis(graph)

    response = client.complete(
        LLMRequest(
            messages=[
                LLMMessage(
                    role="system",
                    content=SYSTEM_PROMPT,
                ),
                LLMMessage(
                    role="user",
                    content=(
                        f"{get_semantic_type_incompatibility()}\n\n"
                        f"{get_component_purpose_incompatibility()}\n\n"
                        f"Workflow JSON: \n {encoded_workflow_file}"
                    ),
                ),
            ],
            json_output=True,
        )
    )

    payload = json.loads(response.content)
    semantic_checks = payload.get("semantic_checks")

    if not isinstance(semantic_checks, list):
        raise ValueError("Expected semantic_checks to be a list.")

    return semantic_checks

