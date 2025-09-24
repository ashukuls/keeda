# Graphic Novel Creation System Schema Summary

A MongoDB schema design for AI-assisted graphic novel creation, featuring hierarchical panel management, image generation tracking, visual consistency, and creator preferences.

## Core Design Principles

- **Visual Content Hierarchy**: Projects → Chapters → Scenes → Panels → Images
- **Universal Drafts**: Common draft system for both narrative and visual content
- **Style Consistency**: Visual style guides and character design references
- **Dual Generation Modes**: Direct application vs. draft review for images
- **Generation Tracking**: Full lineage from prompts to final images
- **Preference Learning**: Learning from visual style choices and feedback

## 1. Core Content Collections

### 1.1 Projects
- Graphic novel project information (title, genre, art style)
- Owner reference (owner_id → Users collection)
- Target page count and panel count
- Visual style guide and color palette
- Generation settings and preferences
- Project metadata and progress tracking
- Created and updated timestamps

### 1.2 Chapters
- Chapter number and title
- Cover image reference
- Target page count
- Summary and themes
- Order keys and hierarchy
- Status tracking (storyboard, pencils, inks, colors, complete)

### 1.3 Scenes
- Parent chapter relationship
- Scene description and mood
- Location and time of day
- Character appearances
- Target panel count
- Scene pacing and transitions

### 1.4 Panels
- Parent scene relationship
- Panel number and position in layout
- Panel size and shape (full, half, quarter, etc.)
- Camera angle and shot type
- Composition notes
- Associated image reference
- Dialogue and narration text
- Sound effects

### 1.5 Images
- Image file path (local filesystem)
- Generation metadata (prompt, model, settings)
- Image dimensions and format
- Associated panel reference
- Version number
- Style consistency score
- Approval status

### 1.6 Characters
- Character profile and backstory
- Visual reference sheets
- Multiple design variations
- Costume/outfit variations
- Expression sheets
- Color specifications
- Personality and voice

### 1.7 Locations
- Location descriptions
- Visual reference images
- Architectural details
- Lighting and atmosphere notes
- Multiple angle references
- Time of day variations

## 2. Relationship Management

### 2.1 Content Edges
- Visual relationships between panels and characters
- Scene-to-panel flow connections
- Character appearances across panels
- Location usage tracking
- Visual continuity links
- Panel transition types

## 3. Draft Management System

### 3.1 Drafts - Universal Draft Collection
- Target references (panel, scene, character design, etc.)
- Polymorphic content structure supporting:
  - panel_composition
  - image_variations
  - character_designs
  - scene_breakdown
  - dialogue_options
  - cover_designs
- Multiple image variants for comparison
- Status tracking (pending, selected, rejected, revised)
- Visual feedback and ratings
- Style consistency scoring
- Revision tracking with visual diffs

## 4. Generation and Lineage Tracking

### 4.1 Generations
- Image generation requests and results
- Text-to-image prompts
- Model used (DALL-E, Stable Diffusion, etc.)
- Generation parameters (size, style, seed)
- Image file references
- Generation cost tracking
- Performance metrics (generation time)
- Status tracking (queued, processing, completed, failed)

### 4.2 Artifacts - Derived Content
- Thumbnail generations
- Style-transferred images
- Composite panel layouts
- Character expression sheets
- Background extractions
- Color palette derivations

## 5. Revision and History Management

### 5.1 Revisions - Version History
- Panel and image version snapshots
- Visual diff tracking
- Composition changes
- Color/style modifications
- Text and dialogue updates
- Revision notes

## 6. Project Instructions and Guidelines

### 6.1 Project Instructions
- Hierarchical instructions (project → chapter → scene → panel level)
- Content-type specific guidelines (character, dialogue, panel composition, etc.)
- Priority system for instruction override
- Custom rules for each chapter or scene
- User-provided creative direction
- Constraints and preferences for AI generation

Example instruction levels:
- **Project-level**: Overall tone, art style, themes
- **Chapter-level**: Specific mood, pacing, focus characters
- **Scene-level**: Action intensity, emotional tone, visual style
- **Panel-level**: Specific composition, camera angle, lighting

### 6.2 Style Guides
- Project-wide visual style specifications
- Character design guidelines
- Panel composition rules
- Color palette definitions
- Typography and lettering styles
- Mood and atmosphere guidelines

### 6.3 Generation Templates
- Reusable prompt templates
- Genre-specific visual styles
- Character pose libraries
- Panel layout templates
- Scene composition guides

## 7. Preferences and Learning

### 7.1 Generation Preferences
- Preferred AI models for generation
- Default image sizes and formats
- Style preferences (realistic, manga, comic, etc.)
- Auto-approval thresholds
- Review workflow settings
- Batch generation preferences

### 7.2 Visual Feedback
- Image quality ratings
- Style consistency feedback
- Composition preferences
- Character likeness scores
- Color palette satisfaction
- Learning from selections

## 8. Instruction System

### 8.1 Project Instructions Collection
- Instruction ID and version
- Target scope (project_id, chapter_id, scene_id, or panel_id)
- Content type (image_generation, dialogue, panel_layout, etc.)
- Instruction text (user-provided guidelines)
- Priority level (0-1000, higher overrides lower)
- Active status (enabled/disabled)
- Created and updated timestamps

Key features:
- **Hierarchical Override**: Chapter instructions override project, scene overrides chapter, etc.
- **Content-Type Specific**: Different instructions for images vs text generation
- **Priority System**: Multiple instructions can apply with priority resolution
- **Version History**: Track changes to instructions over time

## 9. Supporting Collections

### 9.1 Users
- Username (unique)
- Hashed password
- Created timestamp
- Project references (project_ids)

### 8.2 Projects Settings
- Project ownership (owner_id references Users)
- Default generation settings
- Preferred art styles
- Access control (collaborators, permissions)

### 8.3 Activity Log
- User action tracking (user_id, action, timestamp)
- Image generation history
- Panel creation/modification
- Export activities
- Task execution logs

## 9. Key Indexes

### Performance-Critical Indexes
- User authentication (username - unique)
- Project ownership (owner_id, created_at)
- Panel sequence ordering (scene_id, panel_number)
- Image lookups (panel_id, version)
- Character appearances (character_id, panel_id)
- Generation status queries
- Project hierarchy traversal
- Draft status filtering

## 10. Schema Evolution

- Schema versioning in all collections
- Migration support structure
- Version field for backward compatibility

## Key Features

1. **Visual Hierarchy**: Project → Chapter → Scene → Panel → Image structure
2. **Image Draft System**: Multiple visual variants with comparison tools
3. **Generation Tracking**: Complete history of image generation attempts
4. **Style Consistency**: Visual style guides and reference management
5. **Panel Management**: Flexible panel layouts and compositions
6. **Character Visual Tracking**: Design consistency across panels
7. **Version Control**: Image and panel revision history
8. **Local Storage**: Filesystem-based image storage with metadata
9. **Performance**: Optimized indexes for visual content queries
10. **Extensibility**: Schema versioning for future features