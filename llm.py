import litellm
from litellm import completion as litellm_completion
from config import Config
import json
from typing import Optional, Dict, Any, List

def completion(
    messages: list,
    model: str = Config.LLM,
    tools: Optional[List[Dict[str, Any]]] = None,
    tool_choice: str = "auto"
) -> str:
    """
    Make a completion call to the LLM.
    If tools are provided, the model may choose to call them.
    """
    if tools and not litellm.supports_function_calling(model):
        raise ValueError(f"Model {model} does not support function calling")

    response = litellm_completion(
        messages=messages,
        model=model,
        tools=tools,
        tool_choice=tool_choice
    )
    
    return response

def execute_tool_calls(
    tool_calls: List[Any],
    available_functions: Dict[str, callable],
    messages: List[Dict[str, str]]
) -> List[Dict[str, str]]:
    """
    Execute tool calls and append results to messages.
    Returns updated messages list.
    """
    for tool_call in tool_calls:
        function_name = tool_call.function.name
        function_to_call = available_functions[function_name]
        function_args = json.loads(tool_call.function.arguments)
        function_response = function_to_call(**function_args)
        
        messages.append({
            "tool_call_id": tool_call.id,
            "role": "tool",
            "name": function_name,
            "content": function_response
        })
    
    return messages

# Example usage:
"""
messages = [
    {"role": "system", "content": "You are a helpful assistant that provides city information."},
    {"role": "user", "content": "Tell me about Paris"}
]

response = completion(
    messages=messages,
    response_format=Location,
    enable_json_validation=True
)
"""