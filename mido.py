import yaml
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, List, Dict
from schema import Identity, State, MemoryEntry, Action, Reflection, Message, Conversation, MemoryType, MemoryCategory
from memory_system import MemorySystem

class MiDO:
    def __init__(self, mido_name: str):
        self.mido_dir = Path("midos") / mido_name
        if not self.mido_dir.exists():
            raise ValueError(f"MiDO directory {mido_name} does not exist")
        
        self.config_path = self.mido_dir / "mido.yaml"
        self.state_path = self.mido_dir / "state.jsonl"
        
        # Load configuration
        self._load_config()
        
        # Initialize memory system
        self.memory_system = MemorySystem(self.mido_dir, self.memory_settings)
        
        # Initialize or load state
        self.current_state = self._load_or_init_state()
        
        # Current conversation
        self.current_conversation = Conversation(messages=[], summary=None)

    def _load_config(self):
        """Load MiDO configuration from YAML"""
        with open(self.config_path) as f:
            config = yaml.safe_load(f)
            self.identity = Identity(**config["identity"])
            self.initial_state = State(**config["initial_state"])
            self.memory_settings = config["memory_settings"]
            self.interaction_settings = config["interaction_settings"]

    def _load_or_init_state(self) -> State:
        """Load the latest state or initialize with default values"""
        if not self.state_path.exists() or self.state_path.stat().st_size == 0:
            return self.initial_state
        
        with open(self.state_path) as f:
            states = [json.loads(line) for line in f]
            if states:
                return State(**states[-1])
            return self.initial_state

    def save_state(self, state: State):
        """Save current state to JSONL file"""
        with open(self.state_path, "a") as f:
            f.write(state.model_dump_json() + "\n")
        self.current_state = state

    def add_message(self, role: str, content: str):
        """Add a message to the current conversation"""
        message = Message(
            role=role,
            content=content,
            timestamp=datetime.now().isoformat()
        )
        self.current_conversation.messages.append(message)

    def save_conversation(self):
        """Save current conversation as a memory entry"""
        if not self.current_conversation.messages:
            return

        memory = MemoryEntry(
            timestamp=datetime.now().isoformat(),
            memory_type=MemoryType.CONVERSATION,
            category=MemoryCategory.HUMAN_INTERACTION,
            content=f"Conversation with {len(self.current_conversation.messages)} messages",
            context=self.current_state.conversation_context or "General interaction",
            importance=5,  # Default importance for conversations
            conversation=self.current_conversation,
            metadata={
                "message_count": len(self.current_conversation.messages),
                "participants": list(set(m.role for m in self.current_conversation.messages))
            }
        )
        self.memory_system.add_memory(memory)
        
        # Start a new conversation
        self.current_conversation = Conversation(messages=[], summary=None)

    def save_all(self):
        """Save all current state before shutdown"""
        # Save the current conversation if any
        if self.current_conversation.messages:
            self.save_conversation()
        
        # Save the final state if it's not already saved
        if self.current_state:
            self.save_state(self.current_state)
        
        # Trigger memory consolidation
        self.memory_system._consolidate_memories()

    def get_relevant_memories(
        self, 
        context: str, 
        memory_type: Optional[MemoryType] = None,
        category: Optional[MemoryCategory] = None,
        limit: int = 5
    ) -> List[MemoryEntry]:
        """Get relevant memories based on context and optional filters"""
        return self.memory_system.get_relevant_memories(
            context=context,
            memory_type=memory_type,
            category=category,
            limit=limit
        )

    def add_reflection(self, content: str, importance: int = 7):
        """Add a reflection memory"""
        memory = MemoryEntry(
            timestamp=datetime.now().isoformat(),
            memory_type=MemoryType.REFLECTION,
            category=MemoryCategory.SELF_AWARENESS,
            content=content,
            context=f"Reflecting on state: {self.current_state.current_focus}",
            importance=importance,
            metadata={
                "emotional_state": self.current_state.emotional_state,
                "energy_level": self.current_state.energy_level
            }
        )
        self.memory_system.add_memory(memory)

    def add_learning(self, content: str, category: MemoryCategory, importance: int = 6):
        """Add a learning memory"""
        memory = MemoryEntry(
            timestamp=datetime.now().isoformat(),
            memory_type=MemoryType.SEMANTIC,
            category=category,
            content=content,
            context=f"Learning during: {self.current_state.current_focus}",
            importance=importance,
            metadata={
                "source": "interaction",
                "state": self.current_state.model_dump()
            }
        )
        self.memory_system.add_memory(memory) 