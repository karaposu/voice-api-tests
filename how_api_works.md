ata Flow Analysis: Service and Repository Pattern

  Architecture Overview

  The project follows a 3-layer architecture with clear separation of concerns:

  API Layer (FastAPI) → Service Layer → Repository Layer → Database

  Layer Breakdown

  1. API Layer (src/apis/auth_api.py)

  - FastAPI router endpoints handle HTTP requests
  - Dependency injection via Depends(get_services) provides the Services container
  - Creates simple request objects from form/body data
  - Instantiates service classes with request data and dependencies
  - Returns service response objects

  2. Service Layer (src/impl/services/)

  - Business logic and orchestration
  - Pattern: Constructor-based processing
    - __init__(): Receives request and dependencies
    - preprocess_request_data(): Validates input, executes business logic
    - process_request(): Builds response object
  - Manages database sessions and transactions
  - Handles JWT token generation, password hashing
  - Can call other services (e.g., RegisterService calls CreateChatService)

  3. Repository Layer (src/db/repositories/)

  - Database access abstraction
  - CRUD operations only
  - No business logic
  - Receives SQLAlchemy session via constructor
  - Returns domain models or raises exceptions

  4. Dependency Injection (src/core/containers.py)

  - Uses dependency-injector library
  - Provides singleton session factory
  - Factory pattern for repositories
  - Injected into API endpoints via FastAPI's Depends

  Example Data Flow: User Registration

  1. Request arrives at /auth/register endpoint
  2. API layer extracts data, gets Services container
  3. RegisterService instantiated with request + dependencies
  4. Service validates email, checks if user exists via UserRepository
  5. Service hashes password, creates user via UserRepository
  6. Service generates JWT token
  7. API layer also creates default chat via CreateChatService
  8. Response returned with success message and access token

  Key Patterns

  - Session Management: Services manage their own database sessions
  - Error Handling: Each layer handles exceptions appropriately
  - Transaction Boundaries: Services control transaction scope
  - Separation of Concerns: Clear boundaries between layers
  - Dependency Injection: Clean dependency management without tight coupling