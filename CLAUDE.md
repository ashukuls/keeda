# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Keeda is an AI-powered graphic novel creation system that helps creators develop visual narratives through structured content management, AI generation, and iterative refinement workflows. The system follows a hierarchical content model: Project → Chapter → Scene → Panel → Image.

## Architecture

### Tech Stack

- **Backend**: FastAPI with PyMongo (direct MongoDB driver, not Beanie/Motor)
- **Database**: MongoDB for content storage
- **Cache/Queue**: Redis for caching, Celery for background tasks
- **AI Services**: OpenAI, Anthropic, Ollama (local), local image APIs (Automatic1111/ComfyUI)
- **Frontend** (planned): Next.js 14+ with TypeScript
- **Deployment**: Docker on Windows 11 desktop

### Content Hierarchy

```
Project (Graphic Novel)
├── Chapters
│   ├── Scenes
│   │   └── Panels
│   │       ├── Images (multiple variants)
│   │       ├── Drafts (text variations)
│   │       └── Visual descriptions
│   └── Instructions (hierarchical)
├── Characters (with visual references)
└── Locations (with visual references)
```

## Development Commands

### Backend Setup

```bash
cd backend
python -m .venv venv
source .venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### Running the Application

```bash
# Backend (once implemented)
cd backend
uvicorn app.main:app --reload --port 8000

# MongoDB (Docker)
docker run -d -p 27017:27017 --name mongodb mongo:7.0

# Redis (Docker)
docker run -d -p 6379:6379 --name redis redis:7.2
```

### Environment Configuration

Copy `backend/.env.example` to `backend/.env` and configure:

- MongoDB and Redis URLs
- AI service API keys (OPENAI_API_KEY, ANTHROPIC_API_KEY)
- Optional: OLLAMA_BASE_URL, IMAGE_API_BASE_URL for local AI services

## Code Organization

### Database Models

All models are consolidated in `backend/app/models/models.py`:

- **User**: Authentication and project ownership
- **Project**: Main project with settings and statistics
- **Chapter/Scene/Panel**: Content hierarchy
- **Image**: Generated/uploaded images with metadata
- **Character/Location**: Story entities with visual references
- **Draft**: LLM-generated content variations
- **Generation**: AI generation task tracking
- **ProjectInstruction**: Hierarchical AI guidance

### LLM Task Management System

The system defines six core task types for text generation:

1. Scene Summary Generation
2. Character Profile Generation
3. Panel Description Generation
4. Dialogue Generation
5. Chapter Outline Generation
6. Visual Prompt Generation

Each task should:

- Accept context from the content hierarchy
- Use project instructions for guidance
- Generate multiple draft variants
- Support provider selection (OpenAI/Anthropic/Ollama)

### API Design Patterns

- RESTful endpoints under `/api/v1/`
- JWT authentication with refresh tokens
- Hierarchical resource paths (e.g., `/projects/{id}/chapters/{id}/scenes`)
- WebSocket support for real-time updates at `/ws`
- Background task tracking via Celery

### Image Generation Workflow

1. Generate visual prompts using LLM tasks
2. Submit to image generation service (DALL-E or local API)
3. Store multiple variants with metadata
4. Track generation status and parameters
5. Support image-to-image and inpainting for refinements

## Implementation Status

### Completed

- System architecture documentation
- Database schema design
- Model definitions (`backend/app/models/models.py`)
- Configuration structure

### In Progress (TODO.md tracks detailed tasks)

- Phase 1: Database repositories
- Phase 2: LLM task management implementation
- Phase 3: API endpoints
- Phase 4: Service layer
- Phase 5: Background tasks with Celery

### Not Started

- Frontend application
- Docker Compose configuration
- Main FastAPI application entry point
- Test suite

## Key Design Decisions

1. **PyMongo over ODM**: Direct MongoDB driver for flexibility
2. **Consolidated Models**: All models in single file for easier maintenance
3. **LLM Tasks Before API**: Implement core generation logic before endpoints
4. **Draft System**: Universal draft management for both text and images
5. **Hierarchical Instructions**: Project-level defaults with cascading overrides
6. **Local AI Support**: Ollama and local image APIs for offline/private usage

## Common Workflows

### Adding a New Model

1. Add to `backend/app/models/models.py`
2. Export in `backend/app/models/__init__.py`
3. Create repository in `backend/app/db/repositories/`
4. Add indexes in model Config class

### Creating an LLM Task

1. Inherit from base task class in `app/services/llm_tasks/base.py`
2. Define prompt template
3. Implement context gathering
4. Register in task registry
5. Add draft type in Draft model if needed

### Implementing an API Endpoint

1. Create schema in `app/schemas/`
2. Add endpoint in `app/api/v1/endpoints/`
3. Implement service layer in `app/services/`
4. Add repository methods if needed
5. Include in API router

## Database Indexes Strategy

Each model includes indexes for:

- Foreign key relationships (e.g., `project_id`, `chapter_id`)
- Unique constraints (e.g., `chapter_number` within project)
- Query optimization (e.g., `status`, `created_at`)
- Full-text search where applicable

## Error Handling Patterns

- Use FastAPI's HTTPException for API errors
- Implement retry logic for AI service calls
- Track generation failures in Generation model
- Provide fallback options for local AI services
- Store error messages for debugging
