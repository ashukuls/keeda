# FastAPI Layer Design

## Overview

FastAPI-based REST API for the graphic novel creation system, providing endpoints for content management, AI generation, draft workflows, and real-time collaboration features.

## Core Architecture

### Application Structure

- **Main Application**: FastAPI app initialization and configuration
- **Routers**: Modular endpoint definitions for each resource type
- **Models**: Pydantic models for request/response validation
- **Services**: Business logic and external service integrations
- **Dependencies**: Shared dependencies and authentication
- **Middleware**: CORS, tracing, and error handling
- **Utils**: Helper functions and validators

### Key Components

- **Database**: MongoDB with PyMongo driver
- **Cache**: Redis for session and cache management
- **Task Queue**: Celery with Redis backend
- **Tracing**: Jaeger for distributed tracing
- **File Storage**: Local filesystem for images

### Environment Configuration

Required environment variables:
- MongoDB connection settings
- Redis connection settings
- AI service API keys
- JWT secret key
- File storage paths
- Jaeger configuration

## API Endpoints

### Project Management

#### Projects
```
GET    /api/v1/projects
POST   /api/v1/projects
GET    /api/v1/projects/{project_id}
PUT    /api/v1/projects/{project_id}
DELETE /api/v1/projects/{project_id}
GET    /api/v1/projects/{project_id}/stats
GET    /api/v1/projects/{project_id}/export
POST   /api/v1/projects/{project_id}/duplicate
```

#### Style Guides
```
GET    /api/v1/projects/{project_id}/style-guide
PUT    /api/v1/projects/{project_id}/style-guide
POST   /api/v1/projects/{project_id}/style-guide/apply
```

### Content Hierarchy

#### Chapters
```
GET    /api/v1/projects/{project_id}/chapters
POST   /api/v1/projects/{project_id}/chapters
GET    /api/v1/chapters/{chapter_id}
PUT    /api/v1/chapters/{chapter_id}
DELETE /api/v1/chapters/{chapter_id}
POST   /api/v1/chapters/{chapter_id}/reorder
GET    /api/v1/chapters/{chapter_id}/cover
POST   /api/v1/chapters/{chapter_id}/generate-cover
```

#### Scenes
```
GET    /api/v1/chapters/{chapter_id}/scenes
POST   /api/v1/chapters/{chapter_id}/scenes
GET    /api/v1/scenes/{scene_id}
PUT    /api/v1/scenes/{scene_id}
DELETE /api/v1/scenes/{scene_id}
POST   /api/v1/scenes/{scene_id}/breakdown
GET    /api/v1/scenes/{scene_id}/panels
POST   /api/v1/scenes/{scene_id}/reorder-panels
```

#### Panels
```
GET    /api/v1/scenes/{scene_id}/panels
POST   /api/v1/scenes/{scene_id}/panels
GET    /api/v1/panels/{panel_id}
PUT    /api/v1/panels/{panel_id}
DELETE /api/v1/panels/{panel_id}
POST   /api/v1/panels/{panel_id}/split
POST   /api/v1/panels/{panel_id}/merge
GET    /api/v1/panels/{panel_id}/image
POST   /api/v1/panels/{panel_id}/generate-image
PUT    /api/v1/panels/{panel_id}/dialogue
```

### Visual Assets

#### Images
```
GET    /api/v1/images/{image_id}
POST   /api/v1/images/upload
DELETE /api/v1/images/{image_id}
GET    /api/v1/images/{image_id}/thumbnail
POST   /api/v1/images/{image_id}/variations
POST   /api/v1/images/{image_id}/style-transfer
GET    /api/v1/images/{image_id}/metadata
```

#### Characters
```
GET    /api/v1/projects/{project_id}/characters
POST   /api/v1/projects/{project_id}/characters
GET    /api/v1/characters/{character_id}
PUT    /api/v1/characters/{character_id}
DELETE /api/v1/characters/{character_id}
POST   /api/v1/characters/{character_id}/designs
GET    /api/v1/characters/{character_id}/appearances
POST   /api/v1/characters/{character_id}/generate-sheet
```

#### Locations
```
GET    /api/v1/projects/{project_id}/locations
POST   /api/v1/projects/{project_id}/locations
GET    /api/v1/locations/{location_id}
PUT    /api/v1/locations/{location_id}
DELETE /api/v1/locations/{location_id}
POST   /api/v1/locations/{location_id}/references
GET    /api/v1/locations/{location_id}/usage
```

### AI Generation

#### Image Generation
```
POST   /api/v1/generate/image
POST   /api/v1/generate/panel-sequence
POST   /api/v1/generate/character-design
POST   /api/v1/generate/background
GET    /api/v1/generate/status/{generation_id}
POST   /api/v1/generate/cancel/{generation_id}
GET    /api/v1/generate/history
```

#### Text Generation (LLM Tasks)
```
POST   /api/v1/tasks/execute
GET    /api/v1/tasks/types
GET    /api/v1/tasks/{task_id}/status
POST   /api/v1/tasks/{task_id}/cancel
GET    /api/v1/tasks/{task_id}/result
```

Task types:
- `scene_summary`: Generate scene summaries
- `character_profile`: Create character profiles
- `panel_description`: Generate panel descriptions
- `dialogue`: Generate dialogue options
- `chapter_outline`: Create chapter outlines
- `visual_prompt`: Generate image prompts

### Draft Management

```
GET    /api/v1/drafts
GET    /api/v1/drafts/{draft_id}
POST   /api/v1/drafts/{draft_id}/select
POST   /api/v1/drafts/{draft_id}/reject
POST   /api/v1/drafts/{draft_id}/revise
POST   /api/v1/drafts/{draft_id}/feedback
GET    /api/v1/drafts/pending
POST   /api/v1/drafts/bulk-action
```

### Workflow Operations

```
POST   /api/v1/workflow/storyboard
POST   /api/v1/workflow/generate-chapter
POST   /api/v1/workflow/auto-panel
POST   /api/v1/workflow/consistency-check
GET    /api/v1/workflow/suggestions
```

### Project Instructions

```
GET    /api/v1/projects/{project_id}/instructions
POST   /api/v1/projects/{project_id}/instructions
GET    /api/v1/instructions/{instruction_id}
PUT    /api/v1/instructions/{instruction_id}
DELETE /api/v1/instructions/{instruction_id}
POST   /api/v1/instructions/{instruction_id}/toggle

# Scoped instructions
POST   /api/v1/chapters/{chapter_id}/instructions
POST   /api/v1/scenes/{scene_id}/instructions
POST   /api/v1/panels/{panel_id}/instructions
GET    /api/v1/instructions/applicable?scope={type}&id={id}
```

## Pydantic Models

### Base Models
- **BaseModel**: Common fields (id, timestamps, version)
- **PaginationParams**: Query parameters for list endpoints
- **APIResponse**: Standardized response wrapper

### Project Models
- **ProjectCreate**: New project creation fields
- **ProjectUpdate**: Partial update fields
- **ProjectResponse**: Complete project data
- **StyleGuide**: Visual style specifications

### Content Models
- **ChapterCreate/Update/Response**: Chapter data structures
- **SceneCreate/Update/Response**: Scene information
- **PanelCreate/Update/Response**: Panel specifications
- **DialogueBubble**: Text content for panels

### Generation Models
- **ImageGenerationRequest**: Parameters for image generation
- **TaskExecutionRequest**: LLM task parameters
- **GenerationStatus**: Progress and result tracking

### Draft Models
- **DraftCreate**: New draft with variants
- **DraftVariant**: Individual variant data
- **DraftSelection**: User choice and feedback
- **DraftFeedback**: Detailed feedback structure

### Instruction Models
- **InstructionCreate**: New instruction with scope and content
- **InstructionUpdate**: Modify instruction text or priority
- **InstructionResponse**: Full instruction with metadata
- **ApplicableInstructions**: List of instructions for a given scope

## Error Handling

### Exception Types
- **NotFoundError** (404): Resource not found
- **ValidationError** (422): Input validation failed
- **AuthenticationError** (401): Invalid credentials
- **AuthorizationError** (403): Insufficient permissions
- **GenerationError** (500): AI generation failed
- **QuotaExceededError** (429): Rate limit exceeded

### Error Response Format
All errors return consistent JSON structure with:
- Success flag (false)
- Error message
- Error details (if applicable)
- Timestamp

## WebSocket Endpoints

### Real-time Updates
```
WS /api/v1/ws/{project_id}
```

### Message Types

**Server → Client:**
- `generation_progress`: Image/text generation progress updates
- `draft_ready`: New draft available for review
- `content_update`: Content changes in project
- `task_complete`: Background task completion

**Client → Server:**
- `subscribe`: Subscribe to specific resource updates
- `unsubscribe`: Stop receiving updates for resource

## Middleware

### CORS Configuration
- Allow configured origins (localhost for development)
- Support credentials for authentication
- Enable all HTTP methods and headers

### Jaeger Tracing
- Automatic request tracing
- Trace ID in response headers
- Performance monitoring
- Distributed tracing across services

## Dependencies

### Common Dependencies
- **Database**: MongoDB connection and collection access
- **Pagination**: Standard pagination parameters (skip, limit, sort)
- **Authentication**: Current user extraction from JWT
- **Project Access**: Verify user has access to project
- **Cache**: Redis connection for caching

## User Authentication

### Authentication Endpoints

```
POST   /api/v1/auth/register
POST   /api/v1/auth/login
POST   /api/v1/auth/logout
POST   /api/v1/auth/refresh
GET    /api/v1/auth/me
POST   /api/v1/auth/change-password
```

### Authentication Models
- **UserRegister**: Username and password for registration
- **UserLogin**: Login credentials
- **UserInDB**: User data stored in database
- **UserResponse**: Public user information
- **Token**: JWT access and refresh tokens

### JWT Configuration
- Access token expiry: 30 minutes
- Refresh token expiry: 7 days
- Token blacklisting via Redis
- Secure token generation with secret key

### Authentication Flow
1. User registers with username/password
2. Password is hashed using bcrypt
3. Login returns JWT access and refresh tokens
4. Protected endpoints require valid JWT
5. Tokens can be refreshed before expiry
6. Logout blacklists the token

### Protected Routes
All content management endpoints require authentication. Users can only access their own projects.

## API Versioning

All endpoints are versioned under `/api/v1/` to allow for future API evolution without breaking existing clients.

Version strategy:
- `v1`: Initial stable API
- Major changes require new version (v2, v3, etc.)
- Deprecation notices for old versions
- Parallel version support during transition

## Rate Limiting

- Default limit: 1000 requests/hour
- Generation endpoints: 10 requests/minute
- Implemented using in-memory storage for desktop deployment
- Limits apply per user when authenticated

## Response Formats

### Successful Response
```json
{
    "success": true,
    "data": {
        "id": "123",
        "title": "Chapter 1",
        // ... entity data
    },
    "timestamp": "2024-01-01T00:00:00Z"
}
```

### Error Response
```json
{
    "success": false,
    "error": "Validation failed",
    "details": {
        "field": "title",
        "message": "Title is required"
    },
    "timestamp": "2024-01-01T00:00:00Z"
}
```

### Paginated Response
```json
{
    "success": true,
    "data": {
        "items": [...],
        "total": 100,
        "skip": 0,
        "limit": 20,
        "has_more": true
    },
    "timestamp": "2024-01-01T00:00:00Z"
}
```

## Health Checks

```
GET /api/v1/health        # Basic health check
GET /api/v1/health/ready  # Readiness probe
GET /api/v1/health/live   # Liveness probe
```

Response:
```json
{
    "status": "healthy",
    "services": {
        "mongodb": "connected",
        "redis": "connected",
        "filesystem": "available"
    },
    "timestamp": "2024-01-01T00:00:00Z"
}
```

## File Uploads

### Image Upload
- Endpoint: `POST /api/v1/images/upload`
- Accepted formats: JPEG, PNG, WebP
- Max file size: 10MB
- Files stored in local filesystem
- Returns image ID and metadata
- Optional panel association

## Background Tasks

### Celery Integration
- Task queue with Redis backend
- Async image generation
- LLM text generation tasks
- Progress tracking via task ID
- Status polling endpoints
- Result caching in Redis

## Testing Considerations

### Test Coverage
- Unit tests for business logic
- Integration tests for API endpoints
- End-to-end workflow tests
- Mock AI service responses
- Test database with automatic cleanup
- Authentication and authorization tests

## Security Considerations

### Input Validation
- Pydantic models for automatic validation
- Custom validators for complex rules
- SQL injection prevention (NoSQL parameterized queries)
- File type validation for uploads

### Authentication (Future)
- JWT tokens for authentication
- Session management in Redis
- API key support for automation

### Data Protection
- Sanitize user inputs
- Prevent path traversal in file operations
- Validate image files before processing
- Size limits on uploads

## Performance Optimization

### Caching Strategy
- Redis caching for frequently accessed data
- Response caching for read-heavy endpoints
- Image thumbnail caching
- Query result caching

### Database Optimization
- Proper indexing as defined in DB_DESIGN_SUMMARY
- Pagination for list endpoints
- Projection to limit returned fields
- Aggregation pipelines for complex queries

### Async Operations
- Async database operations with motor
- Background task processing with Celery
- WebSocket for real-time updates
- Non-blocking I/O throughout