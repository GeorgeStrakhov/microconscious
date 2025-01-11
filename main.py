import os
import warnings
from dotenv import load_dotenv
from loguru import logger
from datetime import datetime
import json
from config import Config
from llm import completion, execute_tool_calls
from schema import Action, Reflection, MemoryEntry
from mido import MiDO
from prompts import (
    ACTION_SYSTEM_PROMPT,
    ACTION_USER_PROMPT,
    REFLECTION_SYSTEM_PROMPT,
    REFLECTION_USER_PROMPT,
)
from typing import Optional

# Suppress Pydantic warning about fields config
warnings.filterwarnings('ignore', message='Valid config keys have changed in V2')

load_dotenv()

logger.add(
    Config.LOG_FILE,
    rotation=Config.LOG_ROTATION,
    retention=Config.LOG_RETENTION,
    format=Config.LOG_FORMAT,
    level=Config.LOG_LEVEL
)

def speak(content: str) -> str:
    """Output a message to the console"""
    return json.dumps({"type": "speak", "content": content})

def reflect(state_update: dict, memory_formation: Optional[dict] = None) -> str:
    """Create a reflection with updated state and optional memory"""
    if memory_formation:
        # Add required fields for memory formation
        memory_formation["timestamp"] = datetime.now().isoformat()
        memory_formation["conversation"] = None  # We don't store conversation in memory_formation during reflection
        
    return json.dumps({
        "state_update": state_update,
        "memory_formation": memory_formation
    })

AVAILABLE_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "speak",
            "description": "Output a message to the console",
            "parameters": {
                "type": "object",
                "properties": {
                    "content": {
                        "type": "string",
                        "description": "The message to output"
                    }
                },
                "required": ["content"]
            }
        }
    }
]

REFLECTION_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "reflect",
            "description": "Create a reflection with updated state and optional memory",
            "parameters": {
                "type": "object",
                "properties": {
                    "state_update": {
                        "type": "object",
                        "description": "Updated state including next intention",
                        "properties": {
                            "current_focus": {"type": "string"},
                            "emotional_state": {"type": "string"},
                            "energy_level": {"type": "integer", "minimum": 1, "maximum": 100},
                            "last_action": {"type": "string"},
                            "last_interaction": {"type": "string"},
                            "conversation_context": {"type": "string"}
                        },
                        "required": ["current_focus", "emotional_state", "energy_level"]
                    },
                    "memory_formation": {
                        "type": "object",
                        "description": "Optional memory to form",
                        "properties": {
                            "memory_type": {
                                "type": "string",
                                "enum": ["episodic", "semantic", "procedural", "reflection", "conversation"],
                                "description": "Type of memory"
                            },
                            "category": {
                                "type": "string",
                                "enum": ["human_interaction", "learning", "self_awareness", "skill", "knowledge"],
                                "description": "Category of the memory"
                            },
                            "content": {"type": "string", "description": "The actual memory content"},
                            "context": {"type": "string", "description": "The context in which this memory was formed"},
                            "importance": {"type": "integer", "minimum": 1, "maximum": 10, "description": "Importance score from 1-10"},
                            "metadata": {"type": "object", "description": "Additional metadata about the memory"},
                            "references": {"type": "array", "items": {"type": "string"}, "description": "Timestamps of related memories"},
                            "access_count": {"type": "integer", "description": "Number of times this memory has been accessed"},
                            "consolidated": {"type": "boolean", "description": "Whether this memory has been consolidated"}
                        },
                        "required": ["memory_type", "category", "content", "context", "importance"]
                    }
                },
                "required": ["state_update"]
            }
        }
    }
]

AVAILABLE_FUNCTIONS = {
    "speak": speak,
    "reflect": reflect
}

def get_action(mido: MiDO, user_input: str) -> Action:
    """Get next action from LLM based on current state and intention"""
    messages = [
        {
            "role": "system",
            "content": ACTION_SYSTEM_PROMPT.format(
                name=mido.identity.name,
                goal=mido.identity.goal,
                personality=mido.identity.personality
            )
        },
        {
            "role": "user",
            "content": ACTION_USER_PROMPT.format(
                state=mido.current_state.model_dump_json(),
                memories=[m.model_dump() for m in mido.get_relevant_memories(user_input)],
                conversation=mido.current_conversation.model_dump_json(),
                user_input=user_input
            )
        }
    ]
    
    response = completion(
        messages=messages,
        tools=AVAILABLE_TOOLS,
        tool_choice="auto"
    )
    
    tool_calls = response.choices[0].message.tool_calls
    if not tool_calls:
        raise ValueError("Model did not make any tool calls")
    
    # Execute the tool calls
    messages = execute_tool_calls(tool_calls, AVAILABLE_FUNCTIONS, messages)
    
    # Get the first tool call result (for now we only support one action at a time)
    tool_result = json.loads(messages[-1]["content"])
    return Action(**tool_result)

def get_reflection(mido: MiDO, action: Action, user_input: str) -> Reflection:
    """Get reflection from LLM based on current state, action taken, and input"""
    messages = [
        {
            "role": "system",
            "content": REFLECTION_SYSTEM_PROMPT.format(
                name=mido.identity.name
            )
        },
        {
            "role": "user",
            "content": REFLECTION_USER_PROMPT.format(
                state=mido.current_state.model_dump_json(),
                action=action.model_dump_json(),
                conversation=mido.current_conversation.model_dump_json(),
                user_input=user_input
            )
        }
    ]
    
    response = completion(
        messages=messages,
        tools=REFLECTION_TOOLS,
        tool_choice="auto"
    )
    
    tool_calls = response.choices[0].message.tool_calls
    if not tool_calls:
        raise ValueError("Model did not make any tool calls")
    
    # Execute the tool calls
    messages = execute_tool_calls(tool_calls, AVAILABLE_FUNCTIONS, messages)
    
    # Get the reflection result
    reflection_result = json.loads(messages[-1]["content"])
    return Reflection(**reflection_result)

def main():
    logger.info('Initializing MiDO...')
    mido = MiDO("InterChild")
    logger.info(f'MiDO {mido.identity.name} initialized with goal: {mido.identity.goal}')

    try:
        while True:
            # Execute action based on current state/intention
            action = get_action(mido, "")
            logger.info(f'Action: {action.model_dump_json()}')
            if action.type == "speak":
                print(f"\n{mido.identity.name}: {action.content}\n")
            mido.add_message("assistant", action.content)
            
            # Get user input
            user_input = input(f"{mido.identity.name}> ")
            if user_input.lower() in ['exit', 'quit', 'bye']:
                # Save final conversation before exiting
                mido.save_all()
                break
            
            # Record user message
            mido.add_message("user", user_input)
            
            # Reflect and form new intention
            reflection = get_reflection(mido, action, user_input)
            logger.info(f'Reflection: {reflection.model_dump_json()}')
            
            # Save state and memory updates
            mido.save_state(reflection.state_update)
            if reflection.memory_formation:
                mido.memory_system.add_memory(reflection.memory_formation)
            
            # Save conversation periodically (every 10 messages)
            if len(mido.current_conversation.messages) >= 10:
                mido.save_conversation()
    
    except KeyboardInterrupt:
        logger.info("Gracefully shutting down...")
        mido.save_all()
    
    logger.info("Goodbye!")

if __name__ == "__main__":
    main()