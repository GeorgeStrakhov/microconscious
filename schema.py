from enum import Enum
from typing import Optional, List, Dict, Union
from pydantic import BaseModel, Field
from datetime import datetime

class ActionType(str, Enum):
    SPEAK = "speak"
    # Future types:
    # RESEARCH = "research"
    # READ_FILE = "read_file"

class MemoryType(str, Enum):
    EPISODIC = "episodic"    # Event memories, experiences
    SEMANTIC = "semantic"     # Facts, concepts, knowledge
    PROCEDURAL = "procedural"  # Skills, procedures
    REFLECTION = "reflection"  # Self-reflective thoughts
    CONVERSATION = "conversation"  # Conversation records

class MemoryCategory(str, Enum):
    HUMAN_INTERACTION = "human_interaction"
    LEARNING = "learning"
    SELF_AWARENESS = "self_awareness"
    SKILL = "skill"
    KNOWLEDGE = "knowledge"

class Action(BaseModel):
    type: ActionType = Field(description="The type of action to take")
    content: str = Field(description="The content of the action (e.g., message to speak)")

class State(BaseModel):
    current_focus: str = Field(description="What the MiDO is currently focused on")
    emotional_state: str = Field(description="Current emotional state")
    energy_level: int = Field(description="Energy level from 1-100", ge=1, le=100)
    last_action: Optional[str] = Field(description="The last action taken")
    last_interaction: Optional[str] = Field(description="The last interaction with the user")
    conversation_context: Optional[str] = Field(description="Current conversation context")

class Message(BaseModel):
    role: str = Field(description="Who sent the message (user or assistant)")
    content: str = Field(description="The actual message content")
    timestamp: str = Field(description="ISO format timestamp of when the message was sent")

class Conversation(BaseModel):
    messages: List[Message] = Field(description="List of messages in the conversation")
    summary: Optional[str] = Field(description="Optional summary of the conversation")

class MemoryEmbedding(BaseModel):
    vector: List[float] = Field(description="The embedding vector for this memory")
    model: str = Field(description="The model used to generate this embedding")

class MemoryEntry(BaseModel):
    timestamp: str = Field(description="ISO format timestamp of when this memory was formed")
    memory_type: MemoryType = Field(description="Type of memory (episodic, semantic, etc.)")
    category: MemoryCategory = Field(description="Category of the memory for organization")
    content: str = Field(description="The actual memory content")
    context: str = Field(description="The context in which this memory was formed")
    importance: int = Field(description="Importance score from 1-10", ge=1, le=10)
    conversation: Optional[Conversation] = Field(default=None, description="Associated conversation if memory_type is conversation")
    metadata: Dict = Field(default_factory=dict, description="Additional metadata about the memory")
    embedding: Optional[MemoryEmbedding] = Field(default=None, description="Vector embedding for semantic search")
    references: List[str] = Field(default_factory=list, description="Timestamps of related memories")
    last_accessed: Optional[str] = Field(default=None, description="When this memory was last retrieved")
    access_count: int = Field(default=0, description="Number of times this memory has been accessed")
    consolidated: bool = Field(default=False, description="Whether this memory has been consolidated")

class Identity(BaseModel):
    name: str = Field(description="Name of the MiDO")
    goal: str = Field(description="Primary goal/purpose of the MiDO")
    personality: str = Field(description="Description of the MiDO's personality traits")

class Reflection(BaseModel):
    state_update: State = Field(description="Updated state after reflection")
    memory_formation: Optional[MemoryEntry] = Field(description="New memory to be formed, if any")