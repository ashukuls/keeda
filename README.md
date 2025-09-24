# Keeda - AI-Powered Graphic Novel Creation System

An AI-assisted graphic novel creation platform that helps creators develop visual narratives through intelligent panel management, image generation, and storytelling tools.

## Documentation

- [System Design](./SYSTEM_DESIGN.md) - Architecture, tech stack, and components
- [Database Design](./DB_DESIGN.md) - MongoDB schema and collections
- [API Design](./API_DESIGN.md) - REST API endpoints and specifications
- [LLM Task System](./LLM_TASK_SYSTEM.md) - Text generation task management
- [Full Design Document](./DESIGN.md) - Detailed schema with JSON examples
- [Design Summary](./DESIGN_SUMMARY.md) - Condensed schema overview

## Quick Start

### Prerequisites
- Windows 11
- Docker Desktop
- Python 3.10+
- Node.js 18+

### Environment Setup

Create a `.env` file with:
```
MONGODB_URL=mongodb://localhost:27017
DATABASE_NAME=keeda
REDIS_URL=redis://localhost:6379
OPENAI_API_KEY=your_key_here
ANTHROPIC_API_KEY=your_key_here
SECRET_KEY=your_jwt_secret_key
IMAGE_STORAGE_PATH=./data/images
```

### Docker Deployment

```bash
# Start all services
docker-compose up -d

# Services will be available at:
# - Frontend: http://localhost:3000
# - API: http://localhost:8000
# - MongoDB: localhost:27017
# - Redis: localhost:6379
# - Jaeger UI: http://localhost:16686
```


## Development

### Backend Development
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
```

### Frontend Development
```bash
cd frontend
npm install
npm run dev
```

### Running Tests
```bash
# Backend tests
cd backend
pytest

# Frontend tests
cd frontend
npm test
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Submit a pull request

## License

[License information to be added]

## Contact

[Contact information to be added]
