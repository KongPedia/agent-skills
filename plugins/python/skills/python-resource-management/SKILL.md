---
name: python-resource-management
description: Python resource management with context managers, cleanup patterns, and streaming. Use when managing connections, file handles, implementing cleanup logic, or building streaming responses with accumulated state.
---

# Python Resource Management

Manage resources deterministically using context managers. Resources like database connections, file handles, and network sockets should be released reliably, even when exceptions occur.

## When to Use This Skill

- Managing database connections and connection pools
- Working with file handles and I/O
- Implementing custom context managers
- Building streaming responses with state
- Handling nested resource cleanup
- Creating async context managers

## Core Concepts

### 1. Context Managers

The `with` statement invokes the context manager's exit protocol after successful entry, including when the body raises.
Actual release depends on that implementation; inspect its acquisition and cleanup behavior.

### 2. Protocol Methods

`__enter__`/`__exit__` for sync, `__aenter__`/`__aexit__` for async resource management.

### 3. Cleanup After Successful Entry

After successful `__enter__`, `__exit__` runs when the block exits normally or by exception. If entry fails, that
manager's exit method is not invoked: handle partial acquisition inside entry, or register each acquired resource
with an `ExitStack`/`AsyncExitStack`. The analogous rule applies to async entry/exit. Cleanup is not a guarantee against
abrupt process termination or a failing closer; preserve independent cleanup and report cleanup failures.
See [the Python with statement](https://docs.python.org/3.10/reference/compound_stmts.html#the-with-statement).

### 4. Exception Handling

Return `True` from `__exit__` to suppress exceptions, `False` to propagate them.

## Quick Start

```python
from contextlib import contextmanager

@contextmanager
def managed_resource():
    resource = acquire_resource()
    try:
        yield resource
    finally:
        resource.cleanup()

with managed_resource() as r:
    r.do_work()
```

## Fundamental Patterns

### Pattern 1: Class-Based Context Manager

Implement the context manager protocol for complex resources.

```python
class DatabaseConnection:
    """Database connection with automatic cleanup."""

    def __init__(self, dsn: str) -> None:
        self._dsn = dsn
        self._conn: Connection | None = None

    def connect(self) -> None:
        """Establish database connection."""
        self._conn = psycopg.connect(self._dsn)

    def close(self) -> None:
        """Close connection if open."""
        if self._conn is not None:
            self._conn.close()
            self._conn = None

    def __enter__(self) -> "DatabaseConnection":
        """Enter context: connect and return self."""
        self.connect()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        """After successful entry, close the connection when the block exits."""
        self.close()

# Usage with context manager (preferred)
with DatabaseConnection(dsn) as db:
    result = db.execute(query)

# Manual management when needed
db = DatabaseConnection(dsn)
db.connect()
try:
    result = db.execute(query)
finally:
    db.close()
```

### Pattern 2: Async Context Manager

For async resources, implement the async protocol.

```python
class AsyncDatabasePool:
    """Async database connection pool."""

    def __init__(self, dsn: str, min_size: int = 1, max_size: int = 10) -> None:
        self._dsn = dsn
        self._min_size = min_size
        self._max_size = max_size
        self._pool: asyncpg.Pool | None = None

    async def __aenter__(self) -> "AsyncDatabasePool":
        """Create connection pool."""
        self._pool = await asyncpg.create_pool(
            self._dsn,
            min_size=self._min_size,
            max_size=self._max_size,
        )
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        """Close all connections in pool."""
        if self._pool is not None:
            await self._pool.close()

    async def execute(self, query: str, *args) -> list[dict]:
        """Execute query using pooled connection."""
        async with self._pool.acquire() as conn:
            return await conn.fetch(query, *args)

# Usage
async with AsyncDatabasePool(dsn) as pool:
    users = await pool.execute("SELECT * FROM users WHERE active = $1", True)
```

### Pattern 3: Using @contextmanager Decorator

Simplify context managers with the decorator for straightforward cases.

```python
from contextlib import contextmanager, asynccontextmanager
import time
import structlog

logger = structlog.get_logger()

@contextmanager
def timed_block(name: str):
    """Time a block of code."""
    start = time.perf_counter()
    try:
        yield
    finally:
        elapsed = time.perf_counter() - start
        logger.info(f"{name} completed", duration_seconds=round(elapsed, 3))

# Usage
with timed_block("data_processing"):
    process_large_dataset()

@asynccontextmanager
async def database_transaction(conn: AsyncConnection):
    """Manage database transaction."""
    await conn.execute("BEGIN")
    try:
        yield conn
        await conn.execute("COMMIT")
    except BaseException:
        await conn.execute("ROLLBACK")
        raise

# Usage
async with database_transaction(conn) as tx:
    await tx.execute("INSERT INTO users ...")
    await tx.execute("INSERT INTO audit_log ...")
```

This transaction sketch includes cancellation in rollback attempts; a real driver still needs bounded cleanup,
its own transaction API and explicit handling when rollback fails or the commit outcome is unknown.

### Pattern 4: Independent Resource Release

After successful entry, attempt each resource's cleanup even when another closer fails. `ExitStack` runs registered
callbacks in reverse order and propagates cleanup failures rather than silently treating them as success.

```python
from contextlib import ExitStack

class FileProcessor:
    """Process a file with owned cleanup attempts."""

    def __init__(self, path: str) -> None:
        self._path = path
        self._file: IO | None = None
        self._temp_files: list[Path] = []

    def __enter__(self) -> "FileProcessor":
        self._file = open(self._path, "r")
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        """Attempt independent cleanup; propagate failure."""
        with ExitStack() as cleanup:
            for temp_file in self._temp_files:
                cleanup.callback(temp_file.unlink, missing_ok=True)
            if self._file is not None:
                cleanup.callback(self._file.close)

        # Return None/False to propagate any exception
```

## Detailed worked examples and patterns

Detailed sections (starting with `## Advanced Patterns`) live in `references/details.md`. Read that file when the navigation summary above is insufficient.

## Best Practices Summary

1. **Give resources one cleanup owner** - Prefer context managers for scoped ownership
2. **Handle entry and exit failures** - Exit follows successful entry; partial startup needs its own cleanup
3. **Don't suppress unexpectedly** - Return `False` unless suppression is intentional
4. **Use @contextmanager** - For simple resource patterns
5. **Expose only useful lifecycle operations** - Manual management is optional, not a required second API
6. **Use ExitStack** - For dynamic numbers of resources
7. **Accumulate efficiently** - List + join, not string concatenation
8. **Measure the relevant diagnostic gap** - Time-to-first-byte can matter for streaming
9. **Document behavior** - Especially exception suppression
10. **Test cleanup paths** - Verify resources are released on errors
