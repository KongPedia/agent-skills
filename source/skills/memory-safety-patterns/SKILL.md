---
name: memory-safety-patterns
description: >
  Use for native C/C++ ownership, RAII, lifetimes, buffer bounds, cleanup or memory-safety failures.
  Includes conditional Rust/C examples; not a requirement for ordinary Python or web work.
---

# Memory Safety Patterns

Cross-language patterns for memory-safe programming including RAII, ownership, smart pointers, and resource management.

## C++ and firmware applicability

Use this skill only for a component with native-resource or ownership concerns. Read the owning component's actual
build/environment and [firmware criteria](../../references/cpp-firmware.md) when firmware is selected. Examples are
independent design excerpts, not a complete application or authorization to change compiler flags, dependencies,
watchdogs, device state or hardware. Keep the selected C/C++ standard, allocation/error conventions and existing owners.
Host tools, Rust, throwing heap-backed examples, C++20 `std::span` and `std::shared_mutex` are not firmware requirements.
Use supported target facilities instead of changing the toolchain to fit an example. Non-owning pointers/references are
valid when lifetime, bounds and synchronization are explicit; prefer RAII for ownership, not forced shared ownership.
Destructors cannot report operational success: expose acquisition/write/close failures through the owning API's policy.

## When to Use This Skill

- Writing memory-safe systems code
- Managing resources (files, sockets, memory)
- Preventing use-after-free and leaks
- Implementing RAII patterns
- Choosing between languages for safety
- Debugging memory issues

## Core Concepts

### 1. Memory Bug Categories

| Bug Type             | Description                      | Prevention        |
| -------------------- | -------------------------------- | ----------------- |
| **Use-after-free**   | Access freed memory              | Ownership, RAII   |
| **Double-free**      | Free same memory twice           | Smart pointers    |
| **Memory leak**      | Never free memory                | RAII, GC          |
| **Buffer overflow**  | Write past buffer end            | Bounds checking   |
| **Dangling pointer** | Pointer to freed memory          | Lifetime tracking |
| **Data race**        | Concurrent unsynchronized access | Ownership, Sync   |

### 2. Safety Spectrum

Ownership, checked access and garbage collection address different failure classes; there is no total language-safety
ordering. RAII/GC alone do not establish valid bounds, safe foreign calls, synchronization or deterministic device cleanup.
Evaluate the actual lifetime and concurrency contract, including unsafe/native boundaries and target resource limits.

## Detailed patterns and worked examples

Read [references/details.md](references/details.md) when selecting a language-specific ownership, bounds or
synchronization pattern; the overview alone does not establish example applicability.

## Best Practices

### Do's

- **Prefer RAII** - Tie resource lifetime to scope
- **Use ownership deliberately** - RAII for owned resources; explicit lifetimes for non-owning pointers
- **Understand ownership** - Know who owns what
- **Check bounds** - Use safe access methods
- **Use existing supported tools** - AddressSanitizer, Valgrind or Miri only in their compatible host/software lane

### Don'ts

- **Don't leave ownership ambiguous** - Raw pointers may be non-owning views; document lifetime and bounds
- **Don't return local references** - Dangling pointer
- **Don't ignore compiler warnings** - They catch bugs
- **Don't use `unsafe` carelessly** - In Rust, minimize it
- **Don't assume thread safety** - Be explicit

## Debugging Tools

The following are host examples, not a request to install tools, change firmware flags or use a nightly toolchain.
Use only the existing authorized software lane; sanitizers and Miri are not target or hardware evidence.

```bash
# AddressSanitizer (Clang/GCC)
clang++ -fsanitize=address -g source.cpp

# Valgrind
valgrind --leak-check=full ./program

# Rust Miri (undefined behavior detector)
cargo +nightly miri run

# ThreadSanitizer
clang++ -fsanitize=thread -g source.cpp
```
