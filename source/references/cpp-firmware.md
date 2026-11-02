# C++ firmware criteria

Read this reference only for a selected C++ firmware component. It complements the shared
[engineering criteria](engineering.md); it is not a board configuration, firmware runtime or deployment recipe.
Python, TypeScript and ordinary Rust components do not inherit firmware-specific requirements.

## Select the real target

- Record the component, MCU/board/revision, framework/SDK/RTOS, toolchain, language standard and explicit build/test
  environment before implementation. A host compiler does not establish target language support, ABI or driver behavior.
- If PlatformIO is used, inspect the selected environment, inheritance, source filters, extra scripts and every consuming
  variant. Always select the intended environment explicitly; a template must not choose a real device by default.
- Preserve pinned versions, lock ownership, error conventions, exceptions/RTTI settings and existing libraries. C++20,
  heap allocation, CMake, PlatformIO, an RTOS and a specific board are choices, not universal firmware prerequisites.
- Resolve pins, voltage, output polarity, peripheral ownership, calibration and boot/reset behavior from a reviewed
  hardware profile. Historical bench values and another product's protocol are not defaults for a new component.

## Ownership and responsibility

| Responsibility | Owns | Keep outside |
| --- | --- | --- |
| Product controller/policy | State transitions, command admission, invariants, deadlines, safe state | Driver register details and a second storage implementation |
| Driver/transport adapter | Peripheral lifetime, bounded I/O, encoding/decoding, explicit failures | Product command policy and authoritative safety decisions |
| Persistence mechanism | Resource lifetime, keyed reads/writes, error reporting | Automatic erase/migration and policy for accepting configuration |
| Composition/entrypoint | Configuration, safe initialization, wiring, shutdown | Hidden state transitions or unbounded reconnect work |
| Host tooling | Offline protocol fixtures and separately authorized operations | Replacement of device-local interlocks |

Use concrete composition and small deterministic functions before adding interfaces, tasks or frameworks. Share a
mechanism after real consumers demonstrate reuse; do not make a mega common driver or empty architectural layer.
SRP means one coherent reason to change, not a class per function or a universal file-length limit.

Follow the owning component's formatter and established names. For a new C++ component, use descriptive `snake_case`
files, `PascalCase` types and consistent operation/predicate names; keep units such as `timeoutMs` explicit unless the
type supplies them. Do not repeat the entire package/transport name in every identifier. External wire/storage keys and
public names remain compatibility contracts, not opportunities for blanket recasing.

## Lifetime, bounds and errors

- Keep one explicit resource owner; use scoped lifetime/RAII where acquisition and release have meaning. Non-owning
  pointers/references are valid when lifetime, bounds and synchronization are established. Do not force shared ownership
  or heap wrappers around statically owned peripherals. Resource owners must not become accidentally copyable.
- Destructors must not throw. Check acquisition, allocation, parsing, transfer and persistence results through the
  existing status/error policy. Cleanup is not evidence of a successful write, durable save or safe shutdown.
- Preserve fixed capacities, null termination, callback-buffer lifetime, length/range rejection and overflow reporting.
  Validate before casts, indexing, copies or effects; a view such as `span` neither owns storage nor validates its lifetime.
- Respect actual allocation support and resource budgets. Avoid new unbounded per-tick allocations and large stack
  locals; do not mandate a whole-project zero-allocation rewrite without evidence and scope.
- Persisted keys, schema/version validation, partial-save failure and power-loss behavior are contracts. Several writes
  do not imply a transaction; routine erase/reprovision is not a repair for an unexplained failure.

Read [memory-safety-patterns](../skills/memory-safety-patterns/SKILL.md) for ownership and resource examples. Its host,
Rust and newer-standard excerpts are conditional references, not instructions to upgrade a firmware toolchain.

## Time, concurrency and protocols

- Preserve the actual main-loop/callback priority, local safety work, bounded processing and safe-state behavior on
  every error/return path. Network reconnect, logging, storage or retries cannot silently consume a critical deadline.
- Use the target clock's wrap-safe elapsed/deadline convention with bounded intervals. Cover rollover, timeout, duplicate
  and stale commands, partial frames, maximum lengths and saturation where relevant.
- Add a task/queue only for a demonstrated timing or concurrency need. State its owner, lifetime, capacity, overload
  policy, shutdown and synchronization. Check allocation, admission and completion separately; queued is not executed.
- `volatile` is not atomicity, ordering or cross-core synchronization. Use the selected SDK's matching task/ISR APIs;
  single-core interrupt masking is not multicore exclusion. Keep ISR work bounded and free of blocking, heap, logs and I/O.
- RTOS ports differ in stack units, scheduler lifecycle and critical-section APIs. ESP-IDF byte units and framework-owned
  startup are ESP-specific; they must not become rules for vanilla FreeRTOS or another MCU.
- Keep protocol byte order, framing, version, validation, retry/dedup, freshness and ACK meaning explicit. A timeout does
  not prove no side effect; an ACK, hash or build does not prove physical completion.

Read only the relevant [embedded-systems topic reference](../skills/embedded-systems/SKILL.md#reference-guide) for
peripherals, RTOS, power, protocols or constrained memory. No task, driver, watchdog or diagnostic hook is mandatory.

## Verification and hardware boundary

1. Guidance changes: parse metadata and check references, provenance, licenses, conflicts and complete-file whitespace.
2. Behavior fixes: observe a meaningful failing offline assertion at a production-code seam; make the smallest repair
   and run the selected software checks. Refactors first characterize preserved behavior.
3. Target changes: build the explicit selected environment and affected variants; inspect relevant size/map artifacts.
   Native tests do not prove target ABI, timing, stack headroom, pin polarity or electrical safety.
4. Deployment and physical behavior: require separately scoped target-specific authorization and observed evidence.
   Tests/CI must not upload/flash, open live serial/buses, contact hardware-connected brokers or actuate devices.

Boot, reset, serial-open, provisioning, sleep/wake and deployment can themselves change outputs. Inspect that behavior
and obtain approval covering it or verify physical output isolation before an authorized device operation. Preserve
safe initialization, interlocks, calibrated limits, recovery markers and no automatic replay of saved actuator commands.
Keep deployment/rollback evidence separate from approval to move or actuate. Never log credentials or provision secrets.

Independent review is required for meaningful protocol, concurrency, safety or shared-resource changes. Report exact
environments/consumers, observed checks, omissions, compatibility risk and rollback; do not imply physical success.

## Official references

- [C++ Core Guidelines](https://isocpp.github.io/CppCoreGuidelines/CppCoreGuidelines): resource ownership, lifetime,
  interfaces and concurrency; examples still depend on the selected language standard and runtime.
- [PlatformIO environments](https://docs.platformio.org/en/latest/projectconf/sections/env/index.html): relevant only
  when that component adopts PlatformIO, not permission to install it or select a board.
- [ESP-IDF FreeRTOS](https://docs.espressif.com/projects/esp-idf/en/stable/esp32/api-reference/system/freertos.html):
  relevant only for ESP targets; use documentation matching the installed SDK/RTOS implementation.
