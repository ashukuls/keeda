# LLM Task Management System

## Overview

A Python library for managing LLM text generation tasks in the graphic novel creation system. Tasks are defined as Python classes that handle data fetching, prompt construction, generation, and draft creation workflows.

## Architecture

### Core Components

#### 1. Task Base Class
Abstract base class that all LLM tasks inherit from:
- **Data Fetching**: Methods to retrieve relevant context from MongoDB
- **Prompt Construction**: Template-based prompt building with context injection
- **Generation**: LLM API calls with retry logic and error handling
- **Draft Creation**: Automatic draft record creation for review workflow
- **Validation**: Output validation and quality checks

#### 2. Task Registry
Central registry for all available task types:
- Task discovery and registration
- Task type to class mapping
- Task validation and dependencies
- Task scheduling and prioritization

#### 3. Context Manager
Handles context assembly for tasks:
- Fetches related entities (characters, scenes, panels)
- Maintains context window limits
- Provides relevant history and references
- Manages style guide and project instructions

## Task Types

### 1. Scene Summary Generation
**Purpose**: Generate concise summaries of scenes for overview and navigation

**Input Data**:
- Scene description and mood
- Panel sequence and key moments
- Character appearances
- Dialogue highlights

**Output**:
- 2-3 paragraph scene summary
- Key plot points
- Character interactions
- Emotional beats

**Context Requirements**:
- Previous scene summaries
- Chapter context
- Character profiles
- Story arc information

### 2. Character Profile Generation
**Purpose**: Create detailed character profiles from initial concepts

**Input Data**:
- Basic character information (name, role)
- Appearance notes
- Story role and importance
- User-provided traits

**Output**:
- Full character biography
- Personality traits
- Motivations and goals
- Character voice and speech patterns
- Relationships with other characters

**Context Requirements**:
- Other character profiles
- Story genre and tone
- World-building elements
- Character arc intentions

### 3. Panel Description Generation
**Purpose**: Convert scene beats into detailed panel descriptions

**Input Data**:
- Scene summary
- Target panel count
- Pacing requirements
- Key moments to visualize

**Output**:
- Panel-by-panel breakdown
- Camera angles and shots
- Character positions and expressions
- Background elements
- Action descriptions

**Context Requirements**:
- Previous panel sequences
- Visual style guide
- Character visual references
- Location descriptions

### 4. Dialogue Generation
**Purpose**: Generate character dialogue for panels

**Input Data**:
- Scene context
- Character profiles
- Emotional tone
- Plot requirements

**Output**:
- Character dialogue options
- Narration text
- Internal monologue
- Sound effects suggestions

**Context Requirements**:
- Character voice profiles
- Previous conversations
- Story tone and style
- Pacing requirements

### 5. Chapter Outline Generation
**Purpose**: Create structured chapter outlines from story concepts

**Input Data**:
- Chapter goals
- Key plot points
- Character developments
- Target page count

**Output**:
- Scene breakdown
- Pacing structure
- Narrative arc
- Cliffhangers and hooks

**Context Requirements**:
- Overall story outline
- Previous chapter summaries
- Character arcs
- Story themes

### 6. Visual Prompt Generation
**Purpose**: Create detailed image generation prompts from panel descriptions

**Input Data**:
- Panel description
- Character appearances
- Location details
- Mood and atmosphere

**Output**:
- Detailed image prompt
- Style modifiers
- Composition notes
- Lighting and color suggestions

**Context Requirements**:
- Visual style guide
- Character reference sheets
- Location visual references
- Previous panel imagery

## Task Execution Flow

### 1. Task Initialization
```
1. Receive task request with parameters
2. Validate required parameters
3. Load task class from registry
4. Initialize task with project context
```

### 2. Data Collection Phase
```
1. Query MongoDB for required entities
2. Fetch related context based on task type
3. Apply context window limits
4. Prepare structured input data
```

### 3. Prompt Construction
```
1. Load task-specific prompt template
2. Inject context and parameters
3. Add project-specific instructions
4. Include few-shot examples if available
```

### 4. Generation Phase
```
1. Select appropriate LLM model
2. Execute generation with retry logic
3. Parse and validate output
4. Calculate quality metrics
```

### 5. Draft Creation
```
1. Create draft record in MongoDB
2. Store multiple variants if requested
3. Link to target entity
4. Set initial status to 'pending'
```

### 6. Review Workflow Integration
```
1. Notify UI of new drafts
2. Present options for review
3. Collect user selection/feedback
4. Apply selected draft to target
5. Update learning preferences
```

## Task Configuration

### Task Parameters
Each task type supports:
- **num_variants**: Number of alternatives to generate (1-5)
- **temperature**: Creativity level (0.0-1.0)
- **max_tokens**: Output length limit
- **model_override**: Specific model selection
- **include_context**: Context inclusion depth
- **style_preset**: Predefined style preferences

### Quality Metrics
Tasks calculate quality scores based on:
- Output completeness
- Consistency with context
- Style adherence
- Length appropriateness
- Keyword inclusion
- Sentiment matching

## Integration Points

### MongoDB Collections
Tasks interact with:
- **projects**: Project settings and style guides
- **chapters**: Chapter structure and summaries
- **scenes**: Scene descriptions and breakdowns
- **panels**: Panel compositions and descriptions
- **characters**: Character profiles and references
- **drafts**: Generated content for review
- **generations**: Task execution history

### API Endpoints
FastAPI endpoints for task management:
- `POST /api/tasks/execute`: Execute a task
- `GET /api/tasks/status/{task_id}`: Check task status
- `GET /api/tasks/types`: List available task types
- `POST /api/tasks/cancel/{task_id}`: Cancel running task

### Celery Integration
Long-running tasks use Celery workers:
- Async task execution
- Progress tracking
- Result caching
- Retry on failure
- Task prioritization

## Error Handling

### Retry Strategy
- Exponential backoff for API failures
- Maximum 3 retry attempts
- Fallback to alternative models
- Graceful degradation

### Error Types
- **ValidationError**: Invalid input or parameters
- **ContextError**: Unable to fetch required context
- **GenerationError**: LLM API failure
- **TimeoutError**: Task execution timeout

## Caching Strategy

### Redis Cache Layers
1. **Context Cache**: Frequently used context data
2. **Prompt Cache**: Compiled prompts with context
3. **Result Cache**: Recent generation results
4. **Embedding Cache**: Vector embeddings for similarity

### Cache Invalidation
- Time-based expiry (TTL)
- Entity update triggers
- Manual cache clearing
- Memory pressure eviction

## Learning and Improvement

### Feedback Collection
- User selections from variants
- Quality ratings
- Edit tracking
- Rejection reasons

### Preference Learning
- Task-specific preferences
- Style preferences per project
- Model performance tracking
- Context relevance scoring

### Metrics Tracking
- Task execution times
- Success/failure rates
- User satisfaction scores
- Cost per task type
- Model performance comparison

## Extension Points

### Custom Task Types
Developers can add new task types by:
1. Inheriting from `BaseTask` class
2. Implementing required methods
3. Registering with task registry
4. Defining prompt templates
5. Adding validation rules

### Plugin Architecture
Support for external plugins:
- Custom prompt templates
- External data sources
- Alternative LLM providers
- Custom quality metrics
- Specialized validators

## Security Considerations

### Input Sanitization
- Prompt injection prevention
- Content filtering
- Size limits enforcement
- Character encoding validation

## Performance Optimization

### Batch Processing
- Group similar tasks
- Shared context loading
- Parallel execution where possible
- Result deduplication

### Context Optimization
- Selective context inclusion
- Context compression
- Relevant entity filtering
- Smart truncation

### Model Selection
- Task-appropriate model sizing
- Cost/quality trade-offs
- Latency requirements
- Fallback model chains