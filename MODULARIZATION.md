# Godfather Backend & CLI Modularization

This document describes the modularized structure of the Godfather backend and CLI.

## Backend Structure

### Overview
The backend has been modularized into separate concerns for better maintainability, testability, and scalability.

### Directory Structure

```
backend/
├── app.py                  # Legacy monolithic application (deprecated)
├── app_new.py             # New modular application entry point
├── file_manager.py        # File operations utility
├── requirements.txt
├── Dockerfile
│
├── api/                   # API Routes (Blueprints)
│   ├── __init__.py
│   ├── auth_routes.py    # Authentication endpoints
│   ├── pod_routes.py     # Pod management endpoints
│   ├── discord_routes.py # Discord integration endpoints
│   ├── ssh_routes.py     # SSH key endpoints
│   └── file_routes.py    # File management endpoints
│
├── config/               # Configuration
│   ├── __init__.py
│   ├── settings.py      # Environment-based settings
│   └── database.py      # Database connections
│
├── services/            # Business Logic
│   ├── auth_service.py   # Authentication & authorization
│   ├── pod_service.py    # Pod operations
│   ├── ssh_service.py    # SSH key management
│   └── discord_service.py # Discord API operations
│
├── middleware/          # Middleware
│   ├── __init__.py
│   └── auth.py          # Authentication decorators
│
└── utils/               # Utilities
    ├── __init__.py
    └── logger.py        # Logging configuration
```

### Module Descriptions

#### API Routes (`api/`)
Flask Blueprints that define HTTP endpoints:
- **auth_routes.py**: User authentication and verification
- **pod_routes.py**: Pod CRUD operations, access control
- **discord_routes.py**: Discord member management
- **ssh_routes.py**: SSH key retrieval
- **file_routes.py**: File operations on pods

#### Services (`services/`)
Business logic separated from route handlers:
- **auth_service.py**: Token verification, Discord ID lookup, user storage
- **pod_service.py**: RunPod API interactions, pod lifecycle management
- **ssh_service.py**: SSH key generation, storage, and retrieval
- **discord_service.py**: Discord API operations, role checking

#### Middleware (`middleware/`)
Request processing middleware:
- **auth.py**: Authentication decorators (`@require_auth`, `@require_token`)

#### Configuration (`config/`)
Centralized configuration:
- **settings.py**: Environment variable management
- **database.py**: MongoDB connection and collections

#### Utilities (`utils/`)
Shared utilities:
- **logger.py**: Logging setup and configuration

### Migration Plan

To migrate from `app.py` to `app_new.py`:

1. Test the new modular application:
   ```bash
   python backend/app_new.py
   ```

2. Update Docker and deployment configs to use `app_new.py`

3. Once verified, rename:
   ```bash
   mv backend/app.py backend/app_old.py
   mv backend/app_new.py backend/app.py
   ```

### Benefits

1. **Separation of Concerns**: Each module has a single responsibility
2. **Testability**: Services can be unit tested independently
3. **Maintainability**: Easier to locate and fix issues
4. **Scalability**: Easy to add new features without modifying existing code
5. **Reusability**: Services can be used by multiple routes

## CLI Structure

### Overview
The CLI has been modularized into separate components for authentication, pod management, and SSH connections.

### Directory Structure

```
cli/
└── godfather_cli/
    ├── __init__.py
    ├── cli.py              # Legacy monolithic CLI (deprecated)
    ├── cli_new.py         # New modular CLI entry point
    ├── auth.py            # Authentication module
    ├── pod_manager.py     # Pod operations module
    └── ssh_connector.py   # SSH connection module
```

### Module Descriptions

#### CLI Entry Point (`cli_new.py`)
Main application that coordinates other modules:
- Interactive menu
- Command-line argument parsing
- Component initialization

#### Authentication (`auth.py`)
**Class: `CLIAuthenticator`**
- Token storage and retrieval
- Login/logout operations
- Token verification
- Configuration management

#### Pod Management (`pod_manager.py`)
**Class: `PodManager`**
- Fetch available pods
- List pods with formatting
- Interactive pod selection
- Get connection information

#### SSH Connection (`ssh_connector.py`)
**Class: `SSHConnector`**
- Fetch SSH keys from API
- Save keys with correct permissions
- Establish SSH connections
- Handle connection errors

### Migration Plan

To migrate from `cli.py` to `cli_new.py`:

1. Test the new modular CLI:
   ```bash
   python -m godfather_cli.cli_new list
   ```

2. Update `pyproject.toml` to use the new entry point:
   ```toml
   [project.scripts]
   godfather = "godfather_cli.cli_new:main"
   ```

3. Reinstall the package:
   ```bash
   cd cli
   pip install -e .
   ```

4. Once verified, rename:
   ```bash
   mv cli/godfather_cli/cli.py cli/godfather_cli/cli_old.py
   mv cli/godfather_cli/cli_new.py cli/godfather_cli/cli.py
   ```

### Benefits

1. **Modularity**: Each component handles one aspect
2. **Testability**: Components can be tested in isolation
3. **Maintainability**: Easier to understand and modify
4. **Reusability**: Components can be used by other tools
5. **Extensibility**: Easy to add new features

## Testing

### Backend Testing

```python
# Test services independently
from services.auth_service import AuthService
from services.pod_service import PodService

# Test auth service
user_data = AuthService.verify_clerk_token(token)
discord_id = AuthService.get_discord_id_from_clerk(clerk_id)

# Test pod service
pods = PodService.get_all_pods()
pod = PodService.get_pod(pod_id)
```

### CLI Testing

```python
# Test CLI components
from godfather_cli.auth import CLIAuthenticator
from godfather_cli.pod_manager import PodManager

# Test authenticator
auth = CLIAuthenticator(api_base, config_dir)
auth.authenticate()

# Test pod manager
pm = PodManager(api_base)
pods = pm.get_public_pods(token)
```

## Future Improvements

### Backend
- [ ] Add database models with SQLAlchemy/MongoEngine
- [ ] Implement caching layer (Redis)
- [ ] Add API versioning
- [ ] Implement rate limiting
- [ ] Add comprehensive error handling
- [ ] Add API documentation with Swagger/OpenAPI
- [ ] Implement background task queue (Celery)

### CLI
- [ ] Add command history
- [ ] Implement tab completion
- [ ] Add colored output
- [ ] Implement progress bars for long operations
- [ ] Add configuration file support
- [ ] Implement plugin system
- [ ] Add alias support for pods

## Contributing

When adding new features:

1. **Backend**: 
   - Add business logic to appropriate service
   - Create route handler in appropriate blueprint
   - Use middleware for cross-cutting concerns

2. **CLI**:
   - Add functionality to appropriate module
   - Update CLI entry point to expose new features
   - Maintain separation of concerns

## Questions?

Contact the AI Society development team for assistance with the modular architecture.
