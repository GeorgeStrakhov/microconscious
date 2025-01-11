import litellm
from litellm import completion as litellm_completion, get_supported_openai_params, supports_response_schema
from config import Config
from typing import Optional, Union, Type
from pydantic import BaseModel

def completion(
    messages: list, 
    model: str = Config.LLM,
    response_format: Optional[Union[dict, Type[BaseModel]]] = None,
    enable_json_validation: bool = False
):
    # Always enable JSON schema validation
    litellm.enable_json_schema_validation = True
    
    # Check if model supports JSON response format
    supported_params = get_supported_openai_params(model)
    if response_format and "response_format" not in supported_params:
        raise ValueError(f"Model {model} does not support response_format parameter")
    
    # Check if model supports JSON schema
    if not supports_response_schema(model):
        raise ValueError(f"Model {model} does not support JSON schema validation")

    response = litellm_completion(
        messages=messages, 
        model=model,
        response_format=response_format  # Pass Pydantic model directly
    )
    return response['choices'][0]['message']['content']

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