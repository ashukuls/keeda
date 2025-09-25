# Graphic Novel Creation Workflow

This document describes the complete workflow for creating a graphic novel using the Keeda system, from initial concept to final images.

## Overview

The creation process follows a hierarchical, iterative approach where each level generates drafts that are reviewed and selected before proceeding to the next level.

```
Project Setup → Chapter Creation → Scene Generation → Panel Design → Image Generation
```

Each stage uses LLM task agents that generate multiple draft variants, allowing creators to choose the best option or refine requirements and regenerate.

## Workflow Stages

### 1. Project Initialization

**Manual Setup:**
- Create project with basic information (title, genre, target audience)
- Define style guide (visual style, tone, color palette)
- Set project-level instructions for AI agents

**Example:**
```python
project = {
    "name": "The Dark Prophecy",
    "genre": "Dark Fantasy",
    "tone": "Gritty and atmospheric",
    "description": "A tale of reluctant heroes fighting an ancient evil",
    "style_guide": {
        "visual_style": "Dark, realistic comic art",
        "color_palette": "Muted earth tones with vibrant magic effects"
    }
}
```

### 2. Character Development

**Task:** `CharacterProfileTask`
**Input:** Project context + character briefs
**Output:** Multiple character profile drafts

**Process:**
1. Creator provides character requirements:
   ```python
   context.additional_context = {
       "character_name": "Aria Shadowbane",
       "character_role": "protagonist",
       "character_brief": "A former assassin seeking redemption, haunted by her past"
   }
   ```

2. Task generates 3-5 draft variants with different interpretations
3. Creator selects preferred draft or combines elements
4. Selected draft becomes the character record

**Generated Content:**
- Biography and backstory
- Personality traits
- Motivations and fears
- Relationships
- Voice style
- Character arc

### 3. Chapter Outline

**Task:** `ChapterOutlineTask`
**Input:** Project context + chapter brief
**Output:** Chapter structure with scene breakdowns

**Process:**
1. Creator specifies chapter goals:
   ```python
   context.additional_context = {
       "chapter_number": 1,
       "chapter_title": "The Awakening",
       "chapter_brief": "Introduce protagonist, establish the threat, inciting incident"
   }
   ```

2. Task generates chapter outline with 5-8 scenes
3. Creator reviews and selects outline
4. System creates chapter and placeholder scenes

### 4. Scene Development

**Task:** `SceneSummaryTask`
**Input:** Project + Chapter context + scene requirements
**Output:** Detailed scene summaries

**Process:**
1. For each scene from chapter outline:
   ```python
   context.additional_context = {
       "chapter_id": "...",
       "scene_brief": "Aria discovers the ancient tome in the library",
       "scene_setting": "Abandoned monastery library, midnight",
       "previous_scenes": "..."  # Context from earlier scenes
   }
   ```

2. Task generates scene summary including:
   - Detailed plot points
   - Character interactions
   - Emotional tone
   - Visual highlights
   - Key dialogue moments

3. Creator selects/refines scene summary

### 5. Panel Breakdown

**Task:** `PanelDescriptionTask`
**Input:** Scene summary + panel requirements
**Output:** Individual panel descriptions

**Process:**
1. For each scene, generate panel breakdown:
   ```python
   context.additional_context = {
       "scene_id": "...",
       "num_panels": 6,
       "scene_summary": "...",
       "pacing": "slow build to action"
   }
   ```

2. Task creates 4-8 panels per scene with:
   - Visual descriptions
   - Camera angles (close-up, wide shot, etc.)
   - Character positions
   - Dialogue placement
   - Sound effects

3. Creator reviews panel flow and composition

### 6. Dialogue Generation

**Task:** `DialogueTask`
**Input:** Scene context + character profiles
**Output:** Character dialogue for panels

**Process:**
1. For panels needing dialogue:
   ```python
   context.additional_context = {
       "panel_id": "...",
       "characters_present": ["Aria", "Marcus"],
       "dialogue_purpose": "Reveal the prophecy",
       "tone": "tense, mysterious"
   }
   ```

2. Task generates dialogue maintaining:
   - Character voice consistency
   - Story progression
   - Emotional beats
   - Natural flow

### 7. Visual Prompt Generation

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

### 8. Image Generation

**Task:** Image generation service (DALL-E, Stable Diffusion, etc.)
**Input:** Visual prompts
**Output:** Multiple image variants per panel

**Process:**
1. Send visual prompts to image generation service
2. Generate 3-5 variants per panel
3. Creator selects best images or requests regeneration
4. Selected images attached to panels

## Draft and Selection Pattern

At each stage:

1. **Generation Phase**
   - Task generates multiple variants (typically 3-5)
   - Each variant stored as a draft with status "pending"
   - Variants offer different creative interpretations

2. **Review Phase**
   - Creator reviews all draft variants
   - Can request regeneration with refined requirements
   - Can combine elements from multiple drafts

3. **Selection Phase**
   - Creator selects preferred draft
   - Selected draft status changes to "selected"
   - Content from selected draft becomes the official record

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

| Task | Purpose | Model Preference | Output |
|------|---------|-----------------|--------|
| CharacterProfileTask | Create detailed character profiles | GPT-4 (creative) | Biography, traits, motivations |
| ChapterOutlineTask | Structure chapter with scenes | GPT-4 (planning) | Scene list with descriptions |
| SceneSummaryTask | Develop scene details | GPT-3.5 (fast) | Plot, tone, visual highlights |
| PanelDescriptionTask | Break scene into panels | GPT-3.5 (structured) | Panel compositions, angles |
| DialogueTask | Generate character dialogue | GPT-4 (voice) | Natural character dialogue |
| VisualPromptTask | Create image prompts | GPT-4 (descriptive) | Detailed visual descriptions |

## Status Tracking

Each generation task creates:
- `Generation` record: Tracks task execution
- `Draft` records: Stores each variant
- Status progression: `queued` → `processing` → `completed`

The system maintains a complete audit trail of the creative process, enabling analysis of what prompts and parameters produce the best results.