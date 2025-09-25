# Backend Implementation TODO

## Phase 1: Database Layer ✅

### Models (Priority 1) ✅
- [x] Create User model (`app/models/models.py`)
- [x] Create Project model (`app/models/models.py`)
- [x] Create Chapter model (`app/models/models.py`)
- [x] Create Scene model (`app/models/models.py`)
- [x] Create Panel model (`app/models/models.py`)
- [x] Create Image model (`app/models/models.py`)
- [x] Create Character model (`app/models/models.py`)
- [x] Create Location model (`app/models/models.py`)
- [x] Create Draft model (`app/models/models.py`)
- [x] Create Generation model (`app/models/models.py`)
- [x] Create ProjectInstruction model (`app/models/models.py`)

### Repositories (Priority 2) ✅
- [x] Create base repository with CRUD operations (`app/db/repositories/base.py`)
- [x] Create UserRepository (`app/db/repositories/user.py`)
- [x] Create ProjectRepository (`app/db/repositories/project.py`)
- [x] Create ContentRepository for chapters/scenes/panels (`app/db/repositories/content.py`)
- [x] Create DraftRepository (`app/db/repositories/draft.py`)
- [x] Create GenerationRepository (`app/db/repositories/generation.py`)

### Database Indexes (Priority 3)
- [ ] Create index initialization script (`scripts/init_indexes.py`)
- [ ] Document all required indexes

## Phase 2: LLM Task Management System ✅

### Base Infrastructure (Priority 1) ✅
- [x] Create base task class (`app/services/llm_tasks/base.py`)
- [x] Create task registry (`app/services/llm_tasks/registry.py`)
- [x] Create context manager (`app/services/llm_tasks/context.py`)
- [x] Create prompt template manager (`app/services/llm_tasks/templates.py`)
- [x] Create task executor service (`app/services/llm_tasks/executor.py`)

### Task Implementations (Priority 2) 🔄
- [x] Implement SceneSummaryTask (`app/services/llm_tasks/tasks/scene_summary.py`)
- [ ] Implement CharacterProfileTask (`app/services/llm_tasks/tasks/character_profile.py`)
- [ ] Implement PanelDescriptionTask (`app/services/llm_tasks/tasks/panel_description.py`)
- [ ] Implement DialogueGenerationTask (`app/services/llm_tasks/tasks/dialogue.py`)
- [ ] Implement ChapterOutlineTask (`app/services/llm_tasks/tasks/chapter_outline.py`)
- [ ] Implement VisualPromptTask (`app/services/llm_tasks/tasks/visual_prompt.py`)

### AI Service Integration (Priority 1) ✅
- [x] Create base LLM interface (`app/services/ai/base.py`)
- [x] Create OpenAI service (`app/services/ai/openai_service.py`)
- [ ] Create Anthropic service (`app/services/ai/anthropic_service.py`)
- [ ] Create Ollama service (`app/services/ai/ollama_service.py`)
- [x] Create unified LLM client with provider selection (`app/services/ai/llm_client.py`)

### Task Management Features (Priority 3)
- [ ] Add task result caching with Redis
- [ ] Add task status tracking
- [ ] Add task validation and quality checks
- [ ] Add context window management
- [ ] Add retry logic with exponential backoff

## Phase 3: API Layer ⏳

### Pydantic Schemas (Priority 1)
- [ ] Create request/response schemas for User (`app/schemas/user.py`)
- [ ] Create request/response schemas for Project (`app/schemas/project.py`)
- [ ] Create request/response schemas for Content (`app/schemas/content.py`)
- [ ] Create request/response schemas for Generation (`app/schemas/generation.py`)
- [ ] Create request/response schemas for Draft (`app/schemas/draft.py`)
- [ ] Create common schemas (pagination, response wrapper) (`app/schemas/common.py`)

### Authentication (Priority 2)
- [ ] Implement JWT token creation (`app/core/security.py`)
- [ ] Create authentication dependencies (`app/api/dependencies/auth.py`)
- [ ] Create auth endpoints (register, login, refresh) (`app/api/v1/endpoints/auth.py`)
- [ ] Add password hashing utilities

### API Endpoints (Priority 3)
- [ ] Create project endpoints (`app/api/v1/endpoints/projects.py`)
- [ ] Create chapter endpoints (`app/api/v1/endpoints/chapters.py`)
- [ ] Create scene endpoints (`app/api/v1/endpoints/scenes.py`)
- [ ] Create panel endpoints (`app/api/v1/endpoints/panels.py`)
- [ ] Create character endpoints (`app/api/v1/endpoints/characters.py`)
- [ ] Create location endpoints (`app/api/v1/endpoints/locations.py`)
- [ ] Create draft endpoints (`app/api/v1/endpoints/drafts.py`)
- [ ] Create generation endpoints (`app/api/v1/endpoints/generations.py`)
- [ ] Create instruction endpoints (`app/api/v1/endpoints/instructions.py`)

### Middleware (Priority 4)
- [ ] Implement CORS middleware (`app/api/middleware/cors.py`)
- [ ] Implement request ID middleware (`app/api/middleware/request_id.py`)
- [ ] Implement error handling middleware (`app/api/middleware/error_handler.py`)
- [ ] Integrate Jaeger tracing (`app/api/middleware/tracing.py`)

## Phase 4: Services & Business Logic 🧮

### Core Services (Priority 1)
- [ ] Create ProjectService (`app/services/project.py`)
- [ ] Create ContentService (`app/services/content.py`)
- [ ] Create DraftService (`app/services/draft.py`)
- [ ] Create GenerationService (`app/services/generation.py`)

### Image Generation (Priority 2)
- [ ] Create base image generation interface (`app/services/ai/image_generation/base.py`)
- [ ] Create DALL-E integration (`app/services/ai/image_generation/dalle.py`)
- [ ] Create local API integration (`app/services/ai/image_generation/local_api.py`)
  - [ ] Text-to-image support
  - [ ] Image-to-image support
  - [ ] Inpainting support
  - [ ] ControlNet support
- [ ] Create unified image generation client (`app/services/ai/image_generation/client.py`)

### File Management (Priority 3)
- [ ] Create image storage service (`app/services/storage.py`)
- [ ] Create file upload handler (`app/services/upload.py`)
- [ ] Create thumbnail generation service

## Phase 5: Background Tasks 🔄

### Celery Setup (Priority 1)
- [ ] Configure Celery app (`app/tasks/celery_app.py`)
- [ ] Create task base class (`app/tasks/base.py`)

### Task Implementation (Priority 2)
- [ ] Create image generation tasks (`app/tasks/image_generation.py`)
- [ ] Create LLM task execution wrapper (`app/tasks/llm_tasks.py`)
- [ ] Create draft processing tasks (`app/tasks/draft_processing.py`)
- [ ] Create batch generation tasks (`app/tasks/batch_generation.py`)
- [ ] Add task progress tracking
- [ ] Add task result callbacks

## Phase 6: WebSocket Support 🔌

### Real-time Features (Priority 3)
- [ ] Setup WebSocket manager (`app/api/websocket/manager.py`)
- [ ] Create WebSocket endpoints (`app/api/v1/endpoints/websocket.py`)
- [ ] Implement generation progress updates
- [ ] Implement collaborative features

## Phase 7: Testing 🧪

### Unit Tests (Priority 2)
- [x] Test database models (`tests/test_models.py`)
- [x] Test repositories (`tests/test_repositories.py`)
- [ ] Test LLM tasks
- [ ] Test services
- [ ] Test API endpoints

### Integration Tests (Priority 3)
- [ ] Test authentication flow
- [ ] Test project creation workflow
- [ ] Test LLM task pipeline
- [ ] Test generation pipeline
- [ ] Test draft selection workflow

## Phase 8: Deployment & DevOps 🚀

### Docker Setup (Priority 1)
- [ ] Create Dockerfile for backend (`backend/Dockerfile`)
- [ ] Create docker-compose.yml (root level)
- [ ] Create docker-compose.dev.yml for development
- [ ] Create .dockerignore

### Scripts & Utilities (Priority 2)
- [ ] Create database initialization script (`scripts/init_db.py`)
- [ ] Create seed data script (`scripts/seed_data.py`)
- [ ] Create backup script (`scripts/backup.py`)

### Documentation (Priority 3)
- [ ] Create API documentation setup (OpenAPI/Swagger)
- [ ] Write development setup guide
- [ ] Create deployment guide

## Phase 9: Main Application 🎯

### Application Entry Point (Priority 1)
- [ ] Create main FastAPI app (`app/main.py`)
- [ ] Setup route registration
- [ ] Configure middleware stack
- [ ] Add startup/shutdown events

## Current Status

**Current Phase**: Phase 3 - API Layer
**Next Steps**: Create Pydantic schemas and authentication system
**Completed**:
- Phase 1 - Database Layer (models, repositories, tests)
- Phase 2 - LLM Task Management System (base infrastructure, OpenAI integration, sample task)

## Notes

- Each completed phase should be tested before moving to the next
- Priority 1 items are blocking, Priority 2 are important, Priority 3 are nice-to-have
- Update this TODO as items are completed or new requirements emerge
- Consider creating feature branches for each phase

## Legend

- ⏳ In Progress
- ✅ Completed
- 🔄 Needs Review
- ❌ Blocked
- 🧮 Business Logic
- 🔌 Real-time Features
- 🧪 Testing Required
- 🚀 Deployment Ready
- 🎯 Core Feature