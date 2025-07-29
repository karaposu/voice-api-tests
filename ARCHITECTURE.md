# Voice API Architecture Documentation

## Table of Contents
1. [Overview](#overview)
2. [Architecture Layers](#architecture-layers)
3. [Core Design Patterns](#core-design-patterns)
4. [Layer Details](#layer-details)
5. [Data Flow Examples](#data-flow-examples)
6. [LLM Service Integration](#llm-service-integration)
7. [Database Schema](#database-schema)
8. [Best Practices](#best-practices)

## Overview

This project implements a clean, layered architecture for a voice-enabled affirmations and chat API. The system follows Domain-Driven Design (DDD) principles with clear separation of concerns across multiple layers.

### Key Technologies
- **Framework**: FastAPI (async Python web framework)
- **Database**: SQLAlchemy ORM with SQLite/PostgreSQL
- **Dependency Injection**: dependency-injector library
- **Authentication**: JWT tokens with passlib for password hashing
- **LLM Integration**: Custom LLM service layer for AI features
- **API Documentation**: OpenAPI/Swagger auto-generated

## Architecture Layers

```
┌─────────────────────────────────────────────────────────┐
│                   API Layer (FastAPI)                    │
│                 src/apis/*.py                            │
├─────────────────────────────────────────────────────────┤
│                  Service Layer                           │
│           src/impl/services/*/                          │
├─────────────────────────────────────────────────────────┤
│                   LLM Service Layer                      │
│              src/impl/myllmservice.py                   │
├─────────────────────────────────────────────────────────┤
│                 Repository Layer                         │
│           src/db/repositories/*.py                      │
├─────────────────────────────────────────────────────────┤
│              Database Models (SQLAlchemy)                │
│              src/db/models/*.py                         │
└─────────────────────────────────────────────────────────┘
```

## Core Design Patterns

### 1. Dependency Injection (DI)
The system uses the `dependency-injector` library to manage dependencies:

```python
# core/containers.py
class Services(containers.DeclarativeContainer):
    config = providers.Configuration()
    
    # Database
    engine = providers.Singleton(create_engine, config.db_url)
    session_factory = providers.Singleton(sessionmaker, bind=engine)
    
    # Repositories
    user_repository = providers.Factory(UserRepository, session=providers.Dependency())
    chat_repository = providers.Factory(ChatRepository, session=providers.Dependency())
    message_repository = providers.Factory(MessageRepository, session=providers.Dependency())
    affirmation_repository = providers.Factory(AffirmationRepository, session=providers.Dependency())
```

### 2. Service Pattern
Services encapsulate business logic and follow a consistent pattern:

```python
class ServiceName:
    def __init__(self, request, dependencies, **kwargs):
        self.request = request
        self.dependencies = dependencies
        self.response = None
        
        self._preprocess_request_data()  # Validation & business logic
        self._process_request()          # Build response
```

### 3. Repository Pattern
Repositories abstract database operations:

```python
class Repository:
    def __init__(self, session: Session):
        self.session = session
    
    # CRUD operations only, no business logic
```

## Layer Details

### 1. API Layer (FastAPI Routers)

**Location**: `src/apis/`

**Responsibilities**:
- HTTP request/response handling
- Authentication/authorization via JWT tokens
- Request validation using Pydantic models
- Dependency injection setup
- Error handling and HTTP status codes

**Example**: `auth_api.py`
```python
@router.post("/auth/register")
async def auth_register_post(
    auth_register_post_request: AuthRegisterPostRequest = Body(None),
    services: Services = Depends(get_services),
) -> AuthRegisterPost200Response:
    try:
        # Extract user_id from JWT token if needed
        # Instantiate service with request and dependencies
        service = RegisterService(auth_register_post_request, dependencies=services)
        return service.response
    except Exception as e:
        logger.error(f"Error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")
```

### 2. Service Layer

**Location**: `src/impl/services/`

**Responsibilities**:
- Business logic implementation
- Transaction management
- Orchestration between multiple repositories
- Integration with external services (LLM, email, etc.)
- Data transformation and validation

**Service Structure**:
```
src/impl/services/
├── auth/
│   ├── login_service.py
│   ├── register_service.py
│   └── login_with_refresh_service.py
├── chat/
│   ├── create_chat_service.py
│   ├── bring_messages_service.py
│   └── erase_chat_service.py
├── affirmations/
│   ├── create_affirmation_service.py
│   ├── ai_create_affirmations_service.py
│   ├── get_affirmations_service.py
│   ├── edit_affirmation_service.py
│   ├── delete_affirmation_service.py
│   ├── schedule_affirmation_service.py
│   └── unschedule_affirmation_service.py
└── messages/
    └── process_new_message_service.py
```

**Service Lifecycle**:
1. **Initialization**: Receive request data and dependencies
2. **Preprocessing**: Validate data, execute business logic
3. **Processing**: Build and return response

### 3. LLM Service Layer

**Location**: `src/impl/myllmservice.py`

**Purpose**: Centralized AI/LLM functionality with clean abstraction

**Key Features**:
- Inherits from `BaseLLMService` for common LLM operations
- Encapsulates all prompts and LLM-specific logic
- Provides domain-specific methods for different AI features
- Handles rate limiting and concurrent request management

**Architecture**:
```python
class MyLLMService(BaseLLMService):
    def __init__(self):
        super().__init__(
            default_model_name="gpt-4o-mini",
            max_rpm=500,
            max_concurrent_requests=200
        )
    
    def generate_ai_answer(self, chat_history: str, user_msg: str) -> GenerationResult:
        """Generate AI coach response"""
        # Prompt engineering encapsulated here
        
    def generate_affirmations_with_llm(self, context: str, category: str = None, 
                                     count: int = 5) -> GenerationResult:
        """Generate personalized affirmations"""
        # Affirmation-specific prompt logic
```

**Benefits**:
- **Separation of Concerns**: AI logic separated from business logic
- **Reusability**: Methods can be used by multiple services
- **Maintainability**: Centralized prompt management
- **Testability**: Easy to mock for unit tests
- **Flexibility**: Easy to switch LLM providers

### 4. Repository Layer

**Location**: `src/db/repositories/`

**Responsibilities**:
- Database CRUD operations
- Query construction
- Transaction handling
- Data persistence logic
- No business logic

**Repository Methods Pattern**:
```python
class AffirmationRepository:
    def create_affirmation(self, user_id: int, content: str, **kwargs) -> Affirmation:
        """Create new affirmation - database operation only"""
        
    def get_affirmation_by_id(self, affirmation_id: int) -> Optional[Affirmation]:
        """Fetch by ID - simple query"""
        
    def get_user_affirmations(self, user_id: int, category: str = None) -> List[Affirmation]:
        """Fetch with filters - query building"""
        
    def update_affirmation(self, affirmation_id: int, **kwargs) -> Optional[Affirmation]:
        """Update fields - handles partial updates"""
        
    def delete_affirmation(self, affirmation_id: int) -> bool:
        """Soft delete - sets is_active=False"""
```

### 5. Database Models

**Location**: `src/db/models/`

**SQLAlchemy Models**:
- `User`: User accounts with authentication
- `UserDetails`: Extended user profile information
- `Chat`: Chat sessions with settings
- `Message`: Chat messages with metadata
- `Affirmation`: Affirmations with voice and scheduling support
- `LoginTimeLog`: User login history

## Data Flow Examples

### Example 1: Creating an AI-Generated Affirmation

```
1. Client Request → POST /affirmations/ai-create
   {
     "context": "I'm starting a new job and feeling nervous",
     "category": "confidence",
     "count": 3
   }

2. API Layer (affirmations_api.py)
   - Validates JWT token
   - Extracts user_id
   - Creates AiCreateAffirmationsService

3. Service Layer (ai_create_affirmations_service.py)
   - Validates context is not empty
   - Calls MyLLMService.generate_affirmations_with_llm()

4. LLM Service Layer (myllmservice.py)
   - Constructs prompt with context
   - Calls LLM API
   - Returns structured JSON response

5. Service Layer (continued)
   - Parses LLM response
   - Iterates through generated affirmations
   - Calls repository to save each

6. Repository Layer (affirmation_repository.py)
   - Creates Affirmation records in database
   - Returns saved entities

7. Service Layer (final)
   - Converts to response models
   - Returns to API layer

8. API Response → 201 Created
   {
     "message": "Successfully generated 3 affirmations",
     "affirmations": [...]
   }
```

### Example 2: User Login Flow

```
1. Client → POST /auth/login
2. API Layer → LoginService
3. Service Layer:
   - Validates email
   - Gets UserRepository from DI
   - Fetches user by email
   - Verifies password hash
   - Generates JWT token
   - Logs login time
4. Repository Layer:
   - Queries User table
   - Updates LoginTimeLog
5. Response → JWT access token
```

## LLM Service Integration

### Design Principles

1. **Abstraction**: LLM details hidden from business logic
2. **Centralization**: All AI prompts in one place
3. **Type Safety**: Structured request/response objects
4. **Error Handling**: Graceful degradation
5. **Rate Limiting**: Built-in request management

### Integration Pattern

```python
# In Service Layer
class AiCreateAffirmationsService:
    def __init__(self, request, user_id, dependencies):
        self.llm_service = MyLLMService()  # Initialize once
        
    def _preprocess_request_data(self):
        # Call LLM service method
        result = self.llm_service.generate_affirmations_with_llm(
            context=self.request.context,
            category=self.request.category,
            count=self.request.count
        )
        
        if not result.success:
            raise HTTPException(500, "AI generation failed")
            
        # Process result.content
```

### Prompt Engineering

Prompts are encapsulated within MyLLMService methods:

```python
def generate_affirmations_with_llm(self, context, category, count):
    formatted_prompt = f"""Generate {count} positive affirmations based on:
    
    Context: {context}
    Category: {category}
    
    Requirements:
    1. First person (I am, I have, I can)
    2. Present tense and positive
    3. Specific to context
    4. Return as JSON array
    
    Example format:
    [{"content": "I am confident..."}]
    """
    
    # Execute with proper error handling
```

## Database Schema

### Core Tables

1. **users**
   - user_id (PK)
   - email (unique)
   - password_hash
   - is_verified

2. **user_details**
   - user_detail_id (PK)
   - user_id (FK)
   - default_currency
   - login_time_logs (relationship)

3. **chats**
   - id (PK)
   - user_id (FK)
   - settings (JSON)
   - created_at

4. **messages**
   - id (PK)
   - chat_id (FK)
   - user_id
   - message (text)
   - timestamp

5. **affirmations**
   - id (PK)
   - user_id (FK)
   - content (text)
   - category
   - voice_enabled
   - voice_id
   - schedule_config_id
   - is_active
   - timestamps

## Best Practices

### 1. Service Layer
- One service per use case
- Services are stateless
- Handle transactions at service level
- Don't leak database entities to API layer

### 2. Repository Layer
- One repository per aggregate root
- Methods should be database-agnostic
- Use query builders for complex queries
- Handle SQLAlchemy exceptions

### 3. LLM Integration
- Centralize prompt templates
- Version prompts for A/B testing
- Monitor token usage
- Implement retry logic
- Cache responses when appropriate

### 4. Error Handling
- Use domain-specific exceptions
- Log errors with context
- Return user-friendly messages
- Maintain error codes catalog

### 5. Security
- Validate JWT tokens at API layer
- Check resource ownership in services
- Hash passwords with bcrypt
- Never log sensitive data
- Use environment variables for secrets

### 6. Testing Strategy
- Unit test services with mocked dependencies
- Integration test repositories with test database
- Mock LLM service for predictable tests
- API tests with TestClient

## Future Considerations

1. **Caching Layer**: Redis for session management
2. **Message Queue**: Celery for async tasks
3. **WebSockets**: Real-time chat features
4. **Microservices**: Split into smaller services
5. **GraphQL**: Alternative API layer
6. **Event Sourcing**: Audit trail for critical operations