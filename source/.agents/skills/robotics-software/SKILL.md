---
name: robotics-software
description: Design or review robot sensor/command contracts, freshness, state and safety ownership, reconnect, or bounded shutdown. Use for robotics software boundaries and deterministic non-actuating tests; not ordinary Python or hardware execution permission.
---

# Robotics software boundaries

Start at the owning package's README, actual SDK/transport contract, configuration and active consumers. This is
original project guidance, not a ROS, Dora, Zenoh or robot SDK integration. A robotics selection does not install a
framework, establish a real-time guarantee or authorize physical operations. Keep an existing integration unless
the requested change requires replacing it. For a coherent Python/backend/UI example, read
[the robotics use case](../../references/robotics.md) when designing those combined boundaries.

## Contract-first procedure

1. **Define representation.** Name physical units, coordinate frame, axis directions, handedness, rotation convention,
   valid ranges and conversion ownership. An SDK's body frame is not automatically the UI/map frame. Record timestamp
   clock domain, meaning (capture/receive/send), source identity and sequence/reset semantics. Convert once at the
   adapter boundary and test known vectors; do not silently label vendor values as a different convention.
2. **Define time and freshness.** Set accepted age, ordering/duplicate policy and clock-reset behavior. Use a local
   monotonic clock for elapsed deadlines; timestamps from different processes/devices or simulation are not directly
   comparable without a synchronization/translation contract. Inject the clock in policy tests; handle replay pause,
   rewind and disconnect without treating old telemetry as current state.
3. **Name authority.** Identify the owner of command admission, domain state, safety arbitration and final actuation.
   A transport handler translates input; it must not become a second authoritative policy or bypass an existing
   stop/interlock. Carry device/request identity and any owner epoch, execution generation or lease required by the
   actual contract; reject commands from expired owners and stale sessions.
4. **Bound lifecycle.** Give I/O operations deadlines, queues finite capacity and an explicit overload policy. Telemetry
   coalescing and command dropping are different decisions. On reconnect, re-establish identity/ownership and freshness
   before accepting new commands; do not replay actuation automatically. Owned tasks and resources need bounded
   shutdown, partial-startup cleanup and cancellation semantics. Cancelling a waiter cannot prove a thread, device or
   remote action stopped; report an uncertain outcome and reconcile authoritative state before retrying a side effect.
5. **Define observable results.** Distinguish rejected, admitted/queued, executing, succeeded, failed and unknown only
   where supported by the real protocol. A queued ACK is not physical completion. Preserve correlation, deadline,
   idempotency and terminal-result semantics across the Python agent, API and UI; do not fabricate a terminal success.
6. **Verify without actuation.** Use deterministic fakes and recorded/replayed fixtures for conversions, malformed or
   out-of-range values, drop, duplicate, reorder, stale data, clock reset, owner expiry, reconnect, cancellation and
   cleanup failure. Cover existing consumers and changed adapter behavior, not just an import or happy-path ACK.
   A fake validates policy's use of a contract, not the physical adapter or hardware itself.

## Completion and safety

Report the changed contracts/owners, software gate output, uncertainties and omitted checks. Automated gates stay
non-actuating: no physical serial/bus opens, hardware-connected broker writes, movement, firing, recovery or flashing.
Physical operations require separately scoped, recorded human approval and the owning system's safety procedure.
Static checks, software tests, replay, simulation and builds do not establish physical completion or hardware safety.

Keep policy pure where useful, inject concrete I/O collaborators, and share only contracts with actual consumers.
Do not create empty domain layers, generic robot interfaces or one framework per language simply to fill a template.

## References, not implicit platform choices

- [Python monotonic clock](https://docs.python.org/3.10/library/time.html#time.monotonic) documents elapsed-time
  measurement; cross-device timestamp comparison still needs a separate synchronization contract.
- [ROS clock/time design](https://design.ros2.org/articles/clock_and_time.html) illustrates steady, system and simulated
  clock domains. Its pause/jump concerns are useful without requiring ROS dependencies.
- [REP-103 at a pinned revision](https://github.com/ros-infrastructure/rep/blob/6fbda48350825b28aec74609b29c7ee18c8e619a/rep-0103.rst)
  is a reference convention for units and frames, not proof of a vendor SDK's actual representation.
