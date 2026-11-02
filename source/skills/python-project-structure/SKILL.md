---
name: python-project-structure
description: Python project organization, module architecture, and public API design. Use when setting up projects, reorganizing module responsibilities, defining package boundaries, or planning directory layouts.
---

# Python Project Structure & Module Architecture

Design well-organized Python projects with clear module boundaries, explicit public interfaces, and maintainable directory structures. Good organization makes code discoverable and changes predictable.

## When to Use This Skill

- Starting a new Python project from scratch
- Reorganizing an existing codebase for clarity
- Defining supported module and package public APIs
- Deciding between flat and nested directory structures
- Determining test file placement strategies
- Creating reusable library packages

## Core Concepts

### 1. Module Cohesion

Group related code that changes together. A module should have a single, clear purpose.

### 2. Explicit Interfaces

Document public package boundaries and use explicit exports when useful. `__all__` controls wildcard imports; it does not prevent access to other names or create a privacy boundary.

### 3. Flat Hierarchies

Prefer shallow directory structures. Add depth only for genuine sub-domains.

### 4. Consistent Conventions

Apply naming and organization patterns uniformly across the project.

## Quick Start

```
myproject/
├── src/
│   └── myproject/
│       ├── __init__.py
│       ├── services/
│       ├── models/
│       └── api/
├── tests/
├── pyproject.toml
└── README.md
```

## Fundamental Patterns

### Pattern 1: One Concept Per File

Each file should focus on a single concept or closely related set of functions. Consider splitting when a file:

- Handles multiple unrelated responsibilities
- Grows difficult to understand or test; line count is an investigation signal, not a splitting rule
- Contains classes that change for different reasons

```python
# Good: Focused files
# user_service.py - User business logic
# user_repository.py - User data access
# user_models.py - User data structures

# Avoid: Kitchen sink files
# user.py - Contains service, repository, models, utilities...
```

### Pattern 2: Explicit Public APIs with `__all__`

Use `__all__` where an explicit wildcard-export surface is useful, particularly at a package boundary. Do not add it to every module mechanically; unlisted names remain accessible through normal imports.

```python
# mypackage/services/__init__.py
from .user_service import UserService
from .order_service import OrderService
from .exceptions import ServiceError, ValidationError

__all__ = [
    "UserService",
    "OrderService",
    "ServiceError",
    "ValidationError",
]

# Omitted helpers are excluded from wildcard imports, not made inaccessible.
# from .internal_helpers import _validate_input  # Not exported
```

### Pattern 3: Flat Directory Structure

Prefer minimal nesting. Deep hierarchies make imports verbose and navigation difficult.

```
# Preferred: Flat structure
project/
├── api/
│   ├── routes.py
│   └── middleware.py
├── services/
│   ├── user_service.py
│   └── order_service.py
├── models/
│   ├── user.py
│   └── order.py
└── utils/
    └── validation.py

# Avoid: Deep nesting
project/core/internal/services/impl/user/
```

Add sub-packages only when there's a genuine sub-domain requiring isolation.

### Pattern 4: Test File Organization

Choose one approach and apply it consistently throughout the project.

**Option A: Colocated Tests**

```
src/
├── user_service.py
├── test_user_service.py
├── order_service.py
└── test_order_service.py
```

Benefits: Tests live next to the code they verify. Easy to see coverage gaps.

**Option B: Parallel Test Directory**

```
src/
├── services/
│   ├── user_service.py
│   └── order_service.py
tests/
├── services/
│   ├── test_user_service.py
│   └── test_order_service.py
```

Benefits: Clean separation between production and test code. Standard for larger projects.

## Advanced Patterns

### Pattern 5: Package Initialization

Use `__init__.py` to provide a clean public interface for package consumers.

```python
# mypackage/__init__.py
"""MyPackage - A library for doing useful things."""

from .core import MainClass, HelperClass
from .exceptions import PackageError, ConfigError
from .config import Settings

__all__ = [
    "MainClass",
    "HelperClass",
    "PackageError",
    "ConfigError",
    "Settings",
]

__version__ = "1.0.0"
```

Consumers can then import directly from the package:

```python
from mypackage import MainClass, Settings
```

### Pattern 6: Layered Architecture

Organize code by architectural layer for clear separation of concerns.

```
myapp/
├── api/           # HTTP handlers, request/response
│   ├── routes/
│   └── middleware/
├── services/      # Business logic
├── repositories/  # Data access
├── models/        # Domain entities
├── schemas/       # API schemas (Pydantic)
└── config/        # Configuration
```

Each layer should only depend on layers below it, never above.

### Pattern 7: Domain-Driven Structure

For complex applications, organize by business domain rather than technical layer.

```
ecommerce/
├── users/
│   ├── models.py
│   ├── services.py
│   ├── repository.py
│   └── api.py
├── orders/
│   ├── models.py
│   ├── services.py
│   ├── repository.py
│   └── api.py
└── shared/
    ├── database.py
    └── exceptions.py
```

## File and Module Naming

### Conventions

- Use `snake_case` for all file and module names: `user_repository.py`
- Avoid abbreviations that obscure meaning: `user_repository.py` not `usr_repo.py`
- Match class names to file names: `UserService` in `user_service.py`

### Import Style

Use absolute imports for cross-package clarity. Explicit relative imports within a package are also valid; match the
owning package's convention and test installed-package imports rather than relying on the current working directory:

```python
# Preferred: Absolute imports
from myproject.services import UserService
from myproject.models import User

# Valid within a package when consistent with its convention
from ..services import UserService
from . import models
```

Either import style can need changes when modules move; preserve the supported consumer-facing surface.

## Best Practices Summary

1. **Keep files cohesive** - Split independent responsibilities, not a numeric line-count threshold
2. **Document supported public interfaces** - Use `__all__` only when its wildcard-export semantics help
3. **Prefer flat structures** - Add depth only for genuine sub-domains
4. **Use consistent package imports** - Prefer clear cross-package imports; explicit relative imports remain valid
5. **Be consistent** - Apply patterns uniformly across the project
6. **Match names to content** - File names should describe their purpose
7. **Separate concerns** - Keep layers distinct and dependencies flowing one direction
8. **Document your structure** - Include a README explaining the organization
