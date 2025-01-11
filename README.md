# Microconscious

Microconscious is an experiment in trying to string together LLM calls across time to create minimal self-awareness.
The idea is simple: single LLM call represents a single thought. But consciousness and self-awareness depend on the model of itself and its own state and continuation of intention.

## Core Concepts

Our microconscious iterative digital organism (MIDO) has:

- **Identity**: Name, goal, and personality traits defined in YAML
- **State**: Current focus, emotional state, energy level, and context
- **Memory**: A sophisticated dual-storage system with semantic search
- **Actions**: Ways to interact with the world
- **Reflection**: Self-awareness loop for processing experiences

## Implementation

### Memory System
The memory system uses two complementary storage mechanisms:
- **JSONL Storage**: Complete memory entries with full context and metadata
- **Vector Store**: Semantic search index using OpenAI embeddings
- **Memory Types**: Episodic, semantic, procedural, reflection, and conversation
- **Features**:
  - Automatic memory consolidation
  - Importance-based filtering
  - Memory pruning
  - Semantic search with filters
  - Conversation tracking

### Interaction Loop
1. Load MIDO configuration and initialize systems
2. Process current state and relevant memories
3. Generate action based on context (currently speaking)
4. Get user input
5. Reflect on interaction:
   - Update emotional state and focus
   - Form new memories
   - Consolidate experiences
6. Save state and memories
7. Repeat

### Files
- `mido.yaml`: Identity and configuration
- `state.jsonl`: State history
- `memory.jsonl`: Persistent memory storage
- `vector_store/`: Semantic search index

## Next Steps

### Research Capability
Planning to add online research capabilities using:
- Integration with exa.ai API
- Integration with Perplexity API
- New action type: `RESEARCH`
- Features to implement:
  - Query formulation based on context
  - Information synthesis
  - Memory formation from research
  - Source tracking and citation
  - Confidence scoring for information

### Future Enhancements
1. **Memory System**:
   - Cross-reference between memories
   - Long-term vs short-term memory distinction
   - Memory decay simulation
   - Emotional tagging of memories

2. **Interaction**:
   - Multiple simultaneous actions
   - More sophisticated emotional modeling
   - Learning from interactions
   - Skill development tracking

3. **Self-Awareness**:
   - Goal evolution
   - Personal growth metrics
   - Value system development
   - Curiosity-driven learning

4. **Technical Improvements**:
   - Async processing
   - Better error handling
   - Performance optimization
   - Testing framework
