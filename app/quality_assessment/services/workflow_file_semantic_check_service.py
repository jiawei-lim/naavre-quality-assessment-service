from .llm_client_service import LLMMessage, LLMRequest, LLMResponse, get_llm_client
import networkx as nx
from .workflow_encoder_service import *

SYSTEM_PROMPT = """
You are a semantic quality assessor for NaaVRE scientific workflows.

Your task is to assess scientific workflow descriptions represented as structured JSON. The workflows consist of components, inputs, outputs, parameters, metadata, and data-flow relations. 
You evaluate whether the workflow is semantically coherent and whether it satisfies the provided workflow quality dimensions.

There are two system pre-defined nodes, which are the Splitter and Merger. 
The 'splitter' component splits the items from a list or array into its elements to parallelize computation in the next workflow component. It takes a list as an input, and outputs a list.
The 'merger' component is used to merge the outputs of multiple cells into a single array.
Not all outputs from a component is mandatory to be utilized by another component.

You must use only the information provided in the workflow JSON and the provided quality-dimension definitions. 
Do not invent missing metadata, component behavior, domain assumptions, or hidden workflow steps. 
If the available information is insufficient to assess a dimension, mark it as "insufficient_information".

Focus on semantic workflow quality. Assess whether components, artifacts, inputs, outputs, parameters, metadata, and relations make sense with respect to the stated workflow goal and the given quality dimensions.

Do not focus on purely structural graph properties unless they are relevant to a stated quality dimension. For example, do not perform generic checks such as cycle detection, graph connectivity, or topological validity unless the quality dimension explicitly requires them.

Return only valid JSON. Do not include Markdown, prose outside the JSON, or explanatory text before or after the JSON.
If there are no detected issues, only respond with an empty list.
The JSON response must follow this structure:
[
        {
            "check_type": "checked quality dimension",
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
One check should only correspond to one detected issue. If multiple issues are related to the same check, they should be listed separately.

"""

def get_semantic_type_incompatibility() -> str:
    return """
    You need to check for Semantic Type Compatibility. This means you need to check for the input and output links and relationship between components, and ensure that they are logically compatible.
    For example, a component that outputs a list of temperature would not be semantically compatible with a component that accepts a list of weight.
    """

def get_semantic_checks(graph: nx.MultiDiGraph) -> LLMResponse:
    client = get_llm_client()
    encoded_workflow_file = encode_workflow_graph_for_semantic_analysis(graph)

    return client.complete(
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
                        f"Workflow JSON: \n {encoded_workflow_file}"
                    ),
                ),
            ],
            json_output=True,
        )
    )
