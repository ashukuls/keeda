# Graphic Novel Creation Workflow

This document describes the complete workflow for creating a graphic novel using the Keeda system, from initial user input to final images.

## Overview

The creation process starts with a user's story idea and progressively breaks it down into smaller, manageable components through AI-assisted generation and user selection.

```
User Input → Project Summary → Characters → Chapters → Scenes → Panels → Images
```

Each stage generates multiple drafts that users review, provide feedback on, and select from before proceeding.

## Workflow Stages

### 1. Project Initialization from User Input

**Task:** `ProjectSummaryTask`
**Input:** User's story idea (can be a brief prompt or full story text)
**Output:** Structured project summary with genre, tone, themes

**Process:**
1. User provides initial input:
   ```
   "A noir detective story set in a cyberpunk city where AI-enhanced
   detectives solve crimes by entering victims' memories. The protagonist
   is haunted by a memory that isn't their own."
   ```

2. Task generates project summary drafts including:
   - Title suggestions
   - Genre classification
   - Tone and mood
   - Core themes
   - Target audience
   - Visual style suggestions
   - Expanded story synopsis

3. User reviews, provides feedback, selects or regenerates
4. Selected summary becomes the project foundation

**Example Output:**
```python
project_summary = {
    "name": "Memory Thieves",
    "genre": "Cyberpunk Noir",
    "tone": "Dark, psychological, mysterious",
    "themes": ["Identity", "Memory", "Reality vs Perception"],
    "target_audience": "Adult",
    "description": "In Neo-Tokyo 2087, detective Kaira Chen uses neural implants...",
    "style_guide": {
        "visual_style": "Noir with neon highlights, rain-soaked streets",
        "color_palette": "Black, grey, electric blue, neon pink"
    }
}
```

### 2. Character Generation from Project Summary

**Task:** `CharacterListTask`
**Input:** User input + Project summary
**Output:** List of main characters with basic profiles

**Process:**
1. Using the original user input AND project summary:
   ```python
   context.additional_context = {
       "user_input": "original story idea...",
       "project_summary": "expanded synopsis...",
       "num_characters": 5  # Generate 5 main characters
   }
   ```

2. Task generates a LIST of characters in one go:
   - Protagonist(s)
   - Antagonist(s)
   - Supporting characters
   - Their relationships to each other

3. User reviews the character list, provides feedback
4. System creates individual character records from the list

**Example Output (List of characters):**
```python
characters = [
    {
        "name": "Kaira Chen",
        "role": "protagonist",
        "brief": "Memory detective with corrupted neural implant",
        "relationships": {"Marcus": "former partner", "Dr. Yuki": "therapist"}
    },
    {
        "name": "Marcus Vale",
        "role": "deuteragonist",
        "brief": "Kaira's former partner, now investigating her",
        "relationships": {"Kaira": "former partner, conflicted feelings"}
    },
    {
        "name": "The Architect",
        "role": "antagonist",
        "brief": "Memory hacker selling false memories to the highest bidder",
        "relationships": {"Kaira": "unknown connection through implanted memory"}
    }
]
```

### 2b. Individual Character Development

**Task:** `CharacterProfileTask`
**Input:** Character from list + project context
**Output:** Detailed character profile

**Process:**
1. For each character from the list:
   ```python
   context.additional_context = {
       "character_name": "Kaira Chen",
       "character_role": "protagonist",
       "character_brief": "Memory detective with corrupted neural implant",
       "other_characters": [...]  # For relationship context
   }
   ```

2. Task generates detailed profile with:
   - Full biography and backstory
   - Personality traits
   - Motivations and fears
   - Detailed relationships
   - Voice style and speech patterns
   - Character arc
   - Physical appearance

3. User reviews and selects profile variant

### 3. Chapter List Generation

**Task:** `ChapterListTask`
**Input:** Project summary + Character list + User input
**Output:** List of all chapters with brief outlines

**Process:**
1. Generate complete chapter list for the entire story:
   ```python
   context.additional_context = {
       "user_input": "original story...",
       "project_summary": "...",
       "characters": [...],
       "num_chapters": 12  # Or auto-determine based on story
   }
   ```

2. Task generates a LIST of chapters covering the entire story arc:
   - Chapter titles
   - Brief synopsis for each
   - Key events
   - Character appearances
   - Story arc progression

3. User reviews chapter list, can request regeneration
4. System creates chapter records from the list

**Example Output (List of chapters):**
```python
chapters = [
    {
        "number": 1,
        "title": "Ghost in the Machine",
        "synopsis": "Kaira investigates a murder, discovers victim's memories are fabricated",
        "key_events": ["Murder scene", "Memory dive", "Corruption discovery"],
        "characters": ["Kaira", "Marcus", "Victim"]
    },
    {
        "number": 2,
        "title": "Fractured Recall",
        "synopsis": "Kaira experiences memory glitches, questions her own past",
        "key_events": ["Glitch episode", "Dr. Yuki session", "First Architect clue"],
        "characters": ["Kaira", "Dr. Yuki"]
    },
    # ... more chapters
]
```

### 4. Scene List Generation per Chapter

**Task:** `SceneListTask`
**Input:** Chapter details + Project context
**Output:** List of scenes for the chapter

**Process:**
1. For each chapter, generate scene breakdown:
   ```python
   context.additional_context = {
       "chapter": {
           "title": "Ghost in the Machine",
           "synopsis": "...",
           "key_events": [...]
       },
       "num_scenes": 5  # Or auto-determine
   }
   ```

2. Task generates a LIST of scenes for the chapter:
   - Scene titles/descriptions
   - Settings
   - Characters involved
   - Key actions
   - Emotional beats

3. User reviews scene list, provides feedback
4. System creates scene records from the list

**Example Output (List of scenes for Chapter 1):**
```python
scenes = [
    {
        "number": 1,
        "title": "Crime Scene",
        "setting": "Luxury apartment, 47th floor, night",
        "description": "Kaira arrives at murder scene, initial investigation",
        "characters": ["Kaira", "Marcus", "Forensics team"],
        "mood": "Tense, clinical"
    },
    {
        "number": 2,
        "title": "Memory Dive",
        "setting": "Neural interface chamber",
        "description": "Kaira connects to victim's memories, sees impossible events",
        "characters": ["Kaira", "Tech specialist"],
        "mood": "Surreal, disturbing"
    },
    # ... more scenes
]
```

### 4b. Individual Scene Development

**Task:** `SceneSummaryTask`
**Input:** Scene from list + chapter context
**Output:** Detailed scene summary

For each scene, generate expanded summary with:
- Full plot details
- Character interactions and dialogue beats
- Visual highlights
- Pacing notes

### 5. Panel List Generation per Scene

**Task:** `PanelListTask`
**Input:** Scene details + visual style guide
**Output:** List of panels for the scene

**Process:**
1. For each scene, generate panel breakdown:
   ```python
   context.additional_context = {
       "scene": {
           "title": "Crime Scene",
           "description": "...",
           "mood": "Tense, clinical"
       },
       "num_panels": 6,  # Target number of panels
       "pacing": "slow build to reveal"
   }
   ```

2. Task generates a LIST of panels for the scene:
   - Panel descriptions
   - Camera angles (establishing, wide, medium, close-up)
   - Character positions
   - Full dialogue with character voices
   - Narration text
   - Sound effects
   - Visual focus

3. User reviews panel flow, can adjust pacing
4. System creates panel records from the list

**Example Output (List of panels for Scene 1):**
```python
panels = [
    {
        "number": 1,
        "type": "establishing_shot",
        "description": "Wide shot of rain-soaked skyscraper at night",
        "dialogue": [],
        "narration": "Neo-Tokyo, 2087. 11:47 PM.",
        "sound_effects": []
    },
    {
        "number": 2,
        "type": "medium_shot",
        "description": "Kaira stepping out of hover-car, looking up at building",
        "dialogue": [
            {"character": "Kaira", "text": "Another night, another dead memory."}
        ],
        "characters": ["Kaira"],
        "sound_effects": []
    },
    {
        "number": 3,
        "type": "close_up",
        "description": "Kaira's neural implant glowing blue behind her ear",
        "dialogue": [],
        "sound_effects": ["BZZT"],
        "narration": null
    },
    # ... more panels
]
```

Note: Dialogue is generated as part of the panel list, maintaining character voice consistency based on character profiles.

### 6. Visual Prompt Generation

**Task:** `VisualPromptTask`
**Input:** Panel description + style guide
**Output:** Detailed image generation prompts

**Process:**
1. For each panel:
   ```python
   context.additional_context = {
       "scene_id": "...",
       "panel_description": "...",
       "panel_type": "wide_shot",
       "characters": "Aria in foreground, ancient tome glowing"
   }
   ```

2. Task creates detailed prompts for image generation:
   - Artistic style details
   - Character descriptions and positions
   - Background and environment
   - Lighting and atmosphere
   - Color palette
   - Composition guidelines

### 7. Image Generation

**Task:** Image generation service (DALL-E, Stable Diffusion, ComfyUI, etc.)
**Input:** Visual prompts from VisualPromptTask
**Output:** Multiple image variants per panel

**Process:**
1. Send visual prompts to image generation service
2. Generate 3-5 variants per panel
3. Creator selects best images or requests regeneration
4. Selected images attached to panels

## Generation Patterns

### List Generation vs Individual Items

The workflow uses two patterns:

1. **List Generation Tasks** (for bulk creation):
   - `ProjectSummaryTask` - Creates project from user input
   - `CharacterListTask` - Generates all main characters
   - `ChapterListTask` - Generates all chapters
   - `SceneListTask` - Generates scenes per chapter
   - `PanelListTask` - Generates panels per scene

2. **Individual Enhancement Tasks** (for details):
   - `CharacterProfileTask` - Detailed character development
   - `SceneSummaryTask` - Expanded scene details
   - `DialogueTask` - Specific dialogue generation
   - `VisualPromptTask` - Panel-specific image prompts

### Draft, Feedback, and Selection Pattern

At each stage:

1. **Generation Phase**
   - Task generates drafts based on context
   - For lists: generates complete list in one draft
   - For individuals: generates variants (3-5)
   - Each draft stored with status "pending"

2. **Feedback Loop**
   - User reviews draft(s)
   - Provides specific feedback:
     ```python
     feedback = {
         "draft_id": "...",
         "comments": "Make the protagonist more conflicted",
         "regenerate": True,
         "additional_context": {"trauma": "lost memory of sister"}
     }
     ```
   - System regenerates with feedback incorporated

3. **Selection Phase**
   - User selects preferred draft
   - For lists: System creates individual records from list
   - For items: Selected content becomes official
   - Unselected drafts remain for reference

## Iteration and Refinement

The workflow supports iteration at any level:

- **Regeneration:** Generate new drafts with updated requirements
- **Cascading Updates:** Changes at higher levels can trigger regeneration below
- **Parallel Exploration:** Work on multiple chapters/scenes simultaneously
- **Version Control:** All drafts preserved for reference and rollback

## Example: Creating Chapter 1

```python
# 1. Generate character profiles
character_task = CharacterProfileTask(...)
character_drafts = await character_task.execute()
# Creator selects Aria profile draft #2

# 2. Generate chapter outline
chapter_task = ChapterOutlineTask(...)
chapter_drafts = await chapter_task.execute()
# Creator selects outline with 7 scenes

# 3. Generate each scene
for scene_brief in selected_outline.scenes:
    scene_task = SceneSummaryTask(...)
    scene_drafts = await scene_task.execute()
    # Creator selects best interpretation

# 4. Generate panels for each scene
for scene in chapter.scenes:
    panel_task = PanelDescriptionTask(...)
    panel_drafts = await panel_task.execute()
    # Creator reviews panel flow

# 5. Generate dialogue
for panel in scene.panels:
    if panel.needs_dialogue:
        dialogue_task = DialogueTask(...)
        dialogue_drafts = await dialogue_task.execute()

# 6. Generate visual prompts
for panel in scene.panels:
    visual_task = VisualPromptTask(...)
    prompt_drafts = await visual_task.execute()

# 7. Generate images
for panel in scene.panels:
    images = await image_service.generate(panel.visual_prompt)
    # Creator selects final artwork
```

## Benefits of This Workflow

1. **Creative Control:** Multiple options at each stage
2. **Consistency:** Context flows through all levels
3. **Efficiency:** Parallel generation and batch processing
4. **Quality:** Specialized agents for each task type
5. **Flexibility:** Iterate and refine at any level
6. **Traceability:** Complete history of creative decisions

## Task Agent Summary

| Task Type | Purpose | Model Preference | Output |
|-----------|---------|-----------------|--------|
| **List Generation Tasks** |
| ProjectSummaryTask | Transform user input to project | GPT-4 (creative) | Title, genre, synopsis, style |
| CharacterListTask | Generate all main characters | GPT-4 (creative) | Character names, roles, relationships |
| ChapterListTask | Create chapter breakdown | GPT-4 (planning) | Chapter titles, synopsis, progression |
| SceneListTask | Break chapter into scenes | GPT-3.5 (fast) | Scene list with settings, characters |
| PanelListTask | Break scene into panels | GPT-4 (dialogue) | Panels with dialogue, narration |
| **Detail Enhancement Tasks** |
| CharacterProfileTask | Detailed character development | GPT-4 (creative) | Full biography, traits, arc |
| SceneSummaryTask | Expand scene details | GPT-3.5 (fast) | Detailed plot, interactions |
| VisualPromptTask | Create image prompts | GPT-4 (descriptive) | Detailed visual descriptions |

## Complete Example Flow

Starting from user input to first panel:

```python
# 1. User provides story idea
user_input = "A noir detective story in cyberpunk setting..."

# 2. Generate project summary
project_task = ProjectSummaryTask(context={"user_input": user_input})
project_draft = await project_task.execute()
# User reviews and selects
project = create_project_from_draft(selected_draft)

# 3. Generate character list
char_list_task = CharacterListTask(context={
    "user_input": user_input,
    "project_summary": project.description,
    "num_characters": 5
})
char_list_draft = await char_list_task.execute()
# User provides feedback: "Add a mysterious informant character"
char_list_draft_v2 = await char_list_task.execute_with_feedback(feedback)
# User selects v2, system creates 5 character records

# 4. Generate chapter list
chapter_list_task = ChapterListTask(context={
    "project": project,
    "characters": characters,
    "num_chapters": 10
})
chapter_drafts = await chapter_list_task.execute()
# User selects draft, system creates 10 chapter records

# 5. For Chapter 1: Generate scene list
scene_list_task = SceneListTask(context={
    "chapter": chapters[0],
    "num_scenes": 5
})
scene_drafts = await scene_list_task.execute()
# User selects draft, system creates 5 scene records

# 6. For Scene 1: Generate panel list (including dialogue)
panel_list_task = PanelListTask(context={
    "scene": scenes[0],
    "num_panels": 6,
    "character_profiles": characters  # For dialogue consistency
})
panel_drafts = await panel_list_task.execute()
# User reviews flow and dialogue, selects draft
# System creates 6 panel records with dialogue

# 7. For Panel 1: Generate visual prompt
visual_task = VisualPromptTask(context={
    "panel": panels[0],
    "scene": scenes[0],
    "style_guide": project.style_guide
})
prompt_drafts = await visual_task.execute()
# User selects prompt variant

# 8. Generate image
images = await image_service.generate(selected_prompt)
# User selects final image
```

## Status Tracking

Each generation task creates:
- `Generation` record: Tracks task execution
- `Draft` records: Stores each variant/list
- Feedback records: Captures user feedback
- Status progression: `queued` → `processing` → `completed`

The system maintains a complete audit trail of the creative process, enabling analysis of what prompts and parameters produce the best results.

## Key Principles

1. **Progressive Breakdown**: Start with the whole (user input) and break down into parts (chapters → scenes → panels)
2. **Context Accumulation**: Each level adds context for the next
3. **List-First Generation**: Generate lists of items before detailing individuals
4. **Feedback Integration**: User feedback improves generation at each step
5. **Draft Preservation**: All attempts preserved for learning and rollback
6. **Parallel Processing**: Multiple chapters/scenes can be developed simultaneously once lists are created