from typing import List, Optional, Dict
from datetime import datetime, timedelta
import json
from pathlib import Path
from langchain_community.document_loaders import JSONLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_chroma import Chroma
from langchain_core.documents import Document
from schema import MemoryEntry, MemoryType, MemoryCategory

class MemorySystem:
    def __init__(self, mido_dir: Path, settings: Dict):
        self.mido_dir = mido_dir
        self.settings = settings
        self.memory_path = mido_dir / "memory.jsonl"
        self.vector_store_path = mido_dir / "vector_store"
        
        # Initialize embeddings and text splitter
        self.embeddings = OpenAIEmbeddings()
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            add_start_index=True
        )
        
        # Load memories and initialize vector store
        self.memories = self._load_memories()
        self.vector_store = self._initialize_vector_store()
        
        # Schedule periodic consolidation
        self.last_consolidation = datetime.now()
    
    def _load_memories(self) -> List[MemoryEntry]:
        """Load memories from JSONL file"""
        memories = []
        if self.memory_path.exists():
            with open(self.memory_path, 'r') as f:
                for line in f:
                    if line.strip():  # Skip empty lines
                        memory_data = json.loads(line)
                        memories.append(MemoryEntry(**memory_data))
        return memories
    
    def _initialize_vector_store(self) -> Chroma:
        """Initialize vector store with existing memories"""
        documents = []
        
        for memory in self.memories:
            # Create searchable text combining content and context
            text = self._create_memory_text(memory)
            
            # Create metadata for retrieval
            metadata = {
                "timestamp": memory.timestamp,
                "memory_type": memory.memory_type.value,
                "category": memory.category.value,
                "importance": memory.importance,
            }
            
            # Split into chunks if needed
            chunks = self.text_splitter.split_text(text)
            
            # Create documents for each chunk
            for i, chunk in enumerate(chunks):
                doc = Document(
                    page_content=chunk,
                    metadata={
                        **metadata,
                        "chunk_index": i,
                        "total_chunks": len(chunks)
                    }
                )
                documents.append(doc)
        
        # Create and return the vector store
        vector_store = Chroma(
            collection_name="memories",
            embedding_function=self.embeddings,
            persist_directory=str(self.vector_store_path)
        )
        
        # Only add documents if we have any
        if documents:
            vector_store.add_documents(documents=documents)
            
        return vector_store
    
    def _create_memory_text(self, memory: MemoryEntry) -> str:
        """Create searchable text from memory for embedding"""
        text = f"{memory.content}\nContext: {memory.context}"
        if memory.metadata:
            text += f"\nMetadata: {json.dumps(memory.metadata)}"
        if memory.conversation:
            # Include conversation content if available
            messages = [
                f"{msg.role}: {msg.content}"
                for msg in memory.conversation.messages
            ]
            text += f"\nConversation:\n{chr(10).join(messages)}"
        return text
    
    def add_memory(self, memory: MemoryEntry):
        """Add new memory if it meets importance threshold"""
        if memory.importance >= self.settings["importance_threshold"]:
            # Create document from memory
            text = self._create_memory_text(memory)
            chunks = self.text_splitter.split_text(text)
            
            documents = []
            for i, chunk in enumerate(chunks):
                doc = Document(
                    page_content=chunk,
                    metadata={
                        "timestamp": memory.timestamp,
                        "memory_type": memory.memory_type.value,
                        "category": memory.category.value,
                        "importance": memory.importance,
                        "chunk_index": i,
                        "total_chunks": len(chunks)
                    }
                )
                documents.append(doc)
            
            # Add to vector store
            self.vector_store.add_documents(documents=documents)
            
            # Save to JSONL
            with open(self.memory_path, "a") as f:
                f.write(memory.model_dump_json() + "\n")
            
            self.memories.append(memory)
            
            # Check if consolidation is needed
            self._check_consolidation()
    
    async def aget_relevant_memories(
        self, 
        context: str, 
        memory_type: Optional[MemoryType] = None,
        category: Optional[MemoryCategory] = None,
        limit: int = 5
    ) -> List[MemoryEntry]:
        """Async version of get_relevant_memories"""
        filter_dict = {}
        if memory_type:
            filter_dict["memory_type"] = memory_type.value
        if category:
            filter_dict["category"] = category.value
            
        results = await self.vector_store.asimilarity_search_with_relevance_scores(
            query=context,
            k=limit * 2,
            filter=filter_dict if filter_dict else None
        )
        return self._process_search_results(results, limit)
    
    def get_relevant_memories(
        self, 
        context: str, 
        memory_type: Optional[MemoryType] = None,
        category: Optional[MemoryCategory] = None,
        limit: int = 5
    ) -> List[MemoryEntry]:
        """Get relevant memories using semantic search with optional filters"""
        filter_dict = {}
        if memory_type:
            filter_dict["memory_type"] = memory_type.value
        if category:
            filter_dict["category"] = category.value
            
        results = self.vector_store.similarity_search_with_relevance_scores(
            query=context,
            k=limit * 2,
            filter=filter_dict if filter_dict else None
        )
        return self._process_search_results(results, limit)
    
    def _process_search_results(self, results, limit: int) -> List[MemoryEntry]:
        """Process search results and apply filters"""
        relevant_memories = []
        seen_timestamps = set()
        
        for doc, score in results:
            # Find matching memory
            timestamp = doc.metadata["timestamp"]
            if timestamp in seen_timestamps:
                continue
                
            memory = next(
                (m for m in self.memories if m.timestamp == timestamp),
                None
            )
            
            if memory:
                # Update access metrics
                memory.last_accessed = datetime.now().isoformat()
                memory.access_count += 1
                relevant_memories.append(memory)
                seen_timestamps.add(timestamp)
                
                if len(relevant_memories) >= limit:
                    break
        
        return relevant_memories
    
    def _check_consolidation(self):
        """Check if memory consolidation is needed"""
        consolidation_interval = timedelta(
            hours=self.settings.get("consolidation_interval_hours", 24)
        )
        
        if datetime.now() - self.last_consolidation > consolidation_interval:
            self._consolidate_memories()
    
    def _consolidate_memories(self):
        """Consolidate memories to form higher-level insights"""
        # Get unconsolidated memories
        unconsolidated = [m for m in self.memories if not m.consolidated]
        if len(unconsolidated) < 2:
            return
        
        # Group by category
        by_category = {}
        for memory in unconsolidated:
            if memory.category not in by_category:
                by_category[memory.category] = []
            by_category[memory.category].append(memory)
        
        # For each category with multiple memories
        for category, memories in by_category.items():
            if len(memories) < 2:
                continue
            
            # Create consolidated memory
            content = f"Consolidated insights from {len(memories)} memories about {category}:\n"
            content += "\n".join([f"- {m.content}" for m in memories])
            
            consolidated_memory = MemoryEntry(
                timestamp=datetime.now().isoformat(),
                memory_type=MemoryType.SEMANTIC,
                category=category,
                content=content,
                context=f"Memory consolidation for category {category}",
                importance=max(m.importance for m in memories),
                metadata={
                    "consolidated_from": [m.timestamp for m in memories],
                    "memory_count": len(memories)
                },
                references=[m.timestamp for m in memories],
                consolidated=True
            )
            
            # Add the consolidated memory
            self.add_memory(consolidated_memory)
            
            # Mark source memories as consolidated
            for memory in memories:
                memory.consolidated = True
        
        self.last_consolidation = datetime.now()
    
    def prune_memories(self):
        """Remove old, low-importance memories based on settings"""
        retention_days = self.settings.get("memory_retention_days", 30)
        cutoff_date = datetime.now() - timedelta(days=retention_days)
        importance_threshold = self.settings.get("pruning_importance_threshold", 5)
        
        # Keep memories that are either:
        # 1. Recent enough
        # 2. Important enough
        # 3. Frequently accessed
        # 4. Consolidated insights
        self.memories = [
            m for m in self.memories
            if (
                datetime.fromisoformat(m.timestamp) > cutoff_date or
                m.importance >= importance_threshold or
                m.access_count >= self.settings.get("min_access_keep", 3) or
                m.consolidated
            )
        ]
        
        # Rebuild vector store
        self.vector_store = self._initialize_vector_store() 