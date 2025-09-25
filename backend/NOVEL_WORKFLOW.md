# Novel Creation Workflow

This document describes the agent-based workflow for creating graphic novels.

## Overview

The system transforms a user's story idea into a complete graphic novel through hierarchical content generation:
User Input → Project → Characters → Chapters → Scenes → Panels → Images

## Agent Workflow

### 1. Project Summary Generation
**Agent**: `ProjectSummaryAgent`
- **Trigger**: User submits story idea
- **Input**: Raw user text (brief concept or detailed outline)
- **Process**: Expands idea into structured project
- **Output**: Title, genre, rich description
- **Database**: Creates new project document

### 2. Character List Generation
**Agent**: `CharacterListAgent`
- **Trigger**: After project creation
- **Input**: Project data from DB + original user input
- **Process**: Creates main cast with personalities and roles
- **Output**: 5-8 characters with names, roles, descriptions
- **Database**: Creates character document for each

### 3. Chapter List Generation
**Agent**: `ChapterListAgent`
- **Trigger**: After characters created
- **Input**: Project + all characters from DB
- **Process**: Breaks story into narrative chapters
- **Output**: 10-15 chapters with summaries
- **Database**: Creates chapter document for each

### 4. Scene List Generation
**Agent**: `SceneListAgent`
- **Trigger**: Per chapter (can be parallel)
- **Input**: Chapter + project context from DB
- **Process**: Breaks chapter into visual scenes
- **Output**: 6-10 scenes per chapter
- **Database**: Creates scene document for each

### 5. Panel List Generation
**Agent**: `PanelListAgent`
- **Trigger**: Per scene (can be parallel)
- **Input**: Scene + chapter context from DB
- **Process**: Creates comic panel breakdown
- **Output**: 4-8 panels with shots and dialogue
- **Database**: Creates panel document for each

### 6. Enhancement Agents

**`CharacterProfileAgent`**: Expands character biography
- Input: Character + story context from DB
- Output: Detailed biography text

**`SceneSummaryAgent`**: Enriches scene description
- Input: Scene + panels from DB
- Output: Comprehensive scene summary

**`VisualPromptAgent`**: Creates image prompts
- Input: Panel/character/location from DB
- Output: Prompt for image generation

## Data Flow Architecture

```
AgentManager orchestrates:
    ├── Load context from DB
    ├── Execute agent
    ├── Save results to DB
    └── Create draft version
```

Key principles:
- **No direct agent communication** - all through database
- **Stateless agents** - each execution independent
- **Context from DB** - agents read what they need
- **Parallel execution** - scenes/panels can generate simultaneously

## Generation Strategy

### Batch Generation
Agents generate multiple items in one execution:
- One agent call → Multiple characters
- One agent call → Multiple chapters
- One agent call → Multiple scenes

This ensures consistency within each batch.

### Progressive Refinement
1. **First pass**: Generate all content hierarchically
2. **Enhancement**: Add detail with profile/summary agents
3. **Selection**: User picks from draft variants
4. **Finalization**: Selected drafts become official

## Agent Configuration

All agents use minimal configuration:
- Model: `gpt-4o-mini` (supports structured output)
- Temperature: 0.7 (creative but consistent)
- Prompts: Loaded from separate files
- Output: Direct Pydantic schemas

## Workflow Example

```python
# User submits idea
project_id = await manager.generate_project_summary(user_id, "space detective story")

# Generate content hierarchy
character_ids = await manager.generate_characters(project_id)
chapter_ids = await manager.generate_chapters(project_id)

for chapter_id in chapter_ids:
    scene_ids = await manager.generate_scenes(chapter_id)
    for scene_id in scene_ids:
        panel_ids = await manager.generate_panels(scene_id)
```

## Database Collections Used

- `projects`: Story metadata
- `characters`: Cast information
- `chapters`: Story structure
- `scenes`: Scene breakdowns
- `panels`: Comic panels
- `drafts`: All generated variants
- `images`: Visual assets