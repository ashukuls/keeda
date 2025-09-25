# LLM Agent System Guide

This document outlines the design decisions and implementation details for the LLM agent system in Keeda.

## Design Philosophy

### Minimal and Clean Architecture
- **Single Source of Truth**: All schemas defined once in `app/schemas/schemas.py`
- **No Duplication**: No wrapper classes or duplicate schema definitions
- **Bare Minimum Fields**: Only essential fields in schemas, rich information in text fields
- **Native API Usage**: Use OpenAI's structured output API directly, no custom parsing

### Agent-Based Architecture
- Each agent is autonomous and selects its own LLM model
- Agents use generic typing for type-safe outputs
- Direct schema returns without wrapper objects
- Prompts stored in separate files for maintainability

## Agent Types

### List Generation Agents
Create multiple items at once from higher-level context:

1. **ProjectSummaryAgent**: Creates project from user input
   - Input: User story idea
   - Output: `ProjectSummary` (title, genre, description)
   - Model: `gpt-4o-mini`

2. **CharacterListAgent**: Generates main characters
   - Input: User input + project summary
   - Output: `CharacterList` (list of characters)
   - Model: `gpt-4o-mini`

3. **ChapterListAgent**: Creates chapter breakdown
   - Input: Project summary + character list
   - Output: `ChapterList` (list of chapters)
   - Model: `gpt-4o-mini`

4. **SceneListAgent**: Breaks chapter into scenes
   - Input: Chapter + project context
   - Output: `SceneList` (list of scenes)
   - Model: `gpt-4o-mini`

5. **PanelListAgent**: Creates comic panels for scene
   - Input: Scene + chapter context
   - Output: `PanelList` (list of panels with dialogue)
   - Model: `gpt-4o-mini`

### Detail Enhancement Agents
Add depth to existing items:

1. **CharacterProfileAgent**: Expands character details
   - Input: Character + story context
   - Output: `CharacterProfile` (biography)
   - Model: `gpt-4o-mini`

2. **SceneSummaryAgent**: Creates rich scene summary
   - Input: Scene + panels
   - Output: `SceneSummary` (detailed summary)
   - Model: `gpt-4o-mini`

3. **VisualPromptAgent**: Generates image prompts
   - Input: Panel/character/location context
   - Output: `ImagePrompt` (prompt + negative_prompt)
   - Model: `gpt-4o-mini`

## Schema Design Principles

### Minimal Fields
```python
class ProjectSummary(BaseModel):
    title: str
    genre: str
    description: str  # Rich text containing themes, story, etc.
```

Use single text fields for complex information instead of structured lists or dictionaries.

## Implementation Details

### Base Agent Class
```python
class BaseAgent(ABC, Generic[T]):
    agent_type: AgentType
    name: str
    output_schema: Type[T]
    config: AgentConfig = AgentConfig()

    async def execute(self) -> T:
        # Uses OpenAI's native structured output
        completion = await self.client.beta.chat.completions.parse(
            model=self.config.model,
            messages=[{"role": "user", "content": prompt}],
            response_format=self.output_schema,
            temperature=self.parameters.temperature
        )
        return completion.choices[0].message.parsed
```

### Prompt Management
- Prompts stored in `app/services/llm_agents/prompts/`
- One file per agent type
- Loaded dynamically using `load_prompt_template()`
- Format strings for variable substitution

### Data Flow Through Database

All data flows through the database, not directly between agents:

1. **ProjectSummaryAgent** → saves to `projects` collection
2. **CharacterListAgent** → reads `project`, saves to `characters` collection
3. **ChapterListAgent** → reads `project` and `characters`, saves to `chapters` collection
4. **SceneListAgent** → reads `chapter`, saves to `scenes` collection
5. **PanelListAgent** → reads `scene`, saves to `panels` collection

Each agent:
- Reads required data from database
- Generates new content
- Saves results to database
- Never passes data directly to other agents

## Model Selection

All agents currently use `gpt-4o-mini` because:
- Supports structured output natively
- Cost-effective for generation tasks
- Good balance of quality and speed

Future considerations:
- Ollama support for local models
- Anthropic Claude for creative tasks
- Model selection based on task complexity

## Key Design Decisions

### Why No Task Registry?
- Agents are instantiated directly when needed
- No central registration required
- Simpler dependency injection

### Why No Validation Methods?
- Pydantic handles schema validation
- OpenAI API ensures output matches schema
- Additional validation only if business logic requires

### Why No Quality Metrics?
- Quality determined by user selection (draft system)
- Multiple variants generated for user choice
- No automatic quality scoring needed

### Why Single Text Fields?
- Flexibility for LLM creativity
- Easier prompt engineering
- Natural language preserves context
- Simpler schema evolution

## Agent Manager

The `AgentManager` orchestrates agent execution and database operations:

```python
class AgentManager:
    def __init__(self, db):
        # Initialize repositories

    async def generate_project_summary(user_id, user_input, user_instructions, mode)
    async def generate_characters(project_id, num_characters, mode)
    async def generate_chapters(project_id, num_chapters, mode)
    async def generate_scenes(chapter_id, num_scenes, mode)
    async def generate_panels(scene_id, num_panels, mode)
```

Key responsibilities:
1. Load context from database
2. Execute appropriate agent
3. Handle generation modes (direct vs review)
4. Save results to database or drafts

## Generation Modes

Two modes control how generated content is saved:

### Direct Mode
- Saves generated content directly to database
- No user review required
- Faster workflow for trusted generation
- Triggered by keywords in user instructions: "auto", "direct"

### Review Mode (Default)
- Saves to drafts collection first
- Requires user approval before saving to database
- Allows feedback and regeneration
- Default mode for safety

### Mode Selection

Modes are determined from user instructions:
```python
class ProjectSettings:
    def _parse_agent_modes(instructions):
        # "auto" or "direct" → Direct mode for all
        # "review characters" → Review mode for characters
        # "auto generate chapters" → Direct mode for chapters
```

### Draft Workflow

1. **Generate**: Agent creates content → saved as draft
2. **Review**: User reviews draft
3. **Feedback**: User provides feedback (optional)
4. **Regenerate**: Agent regenerates with feedback (optional)
5. **Approve**: Draft approved → content saved to database

## Future Enhancements

### Planned
- Streaming support for long generations
- Batch processing for multiple items
- Caching of common prompts
- Agent chaining for complex workflows

### Not Planned
- Custom text parsing (use native APIs)
- Complex validation (keep it simple)
- Agent inheritance hierarchies (composition over inheritance)
- Wrapper result objects (direct schema returns)

## Testing Strategy

- Mock OpenAI API responses for unit tests
- Validate output structures match schemas
- Test prompt formatting with various inputs