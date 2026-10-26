# Design It Twice

When the user wants to explore alternative interfaces for a chosen deepening candidate, use this comparison pattern. Native parallel sub-agents are useful only for independent, bounded alternatives that justify their cost. Based on "Design It Twice" (Ousterhout): your first idea is unlikely to be the best.

Uses the vocabulary in [SKILL.md](SKILL.md): **module**, **interface**, **seam**, **adapter**, **leverage**.

## Process

### 1. Frame the problem space

Before spawning sub-agents, write a user-facing explanation of the problem space for the chosen candidate:

- The constraints any new interface would need to satisfy
- The dependencies it would rely on, and which category they fall into (see [DEEPENING.md](DEEPENING.md))
- A rough illustrative code sketch to ground the constraints, not a proposal, just a way to make the constraints concrete

State this briefly, then continue the authorized design work; do not add a new approval handoff.

### 2. Compare alternatives proportionately

For a small change, compare alternatives directly. When independent exploration materially helps and delegation is available, use the smallest useful set of native sub-agents. Each explores a **meaningfully different** interface; no minimum agent count is required.

For delegated alternatives, prompt each sub-agent with a separate owned technical brief (file paths, coupling details, dependency category from [DEEPENING.md](DEEPENING.md), what sits behind the seam). The brief is independent of the user-facing problem-space explanation in Step 1. Give each agent a different design constraint:

- Minimal surface: "Minimize caller knowledge while preserving every required contract. Maximise leverage per entry point."
- Flexible surface: "Maximise flexibility: support many use cases and extension."
- Common caller: "Optimise for the most common caller: make the default case trivial."
- Cross-seam design (if applicable): "Design around ports & adapters for cross-seam dependencies."

Include the relevant [SKILL.md](SKILL.md) concepts and existing project vocabulary from [engineering criteria](../../references/engineering.md#naming-interfaces-and-package-ownership); there is no required GLOSSARY.md. Preserve assigned ownership, current contracts and tests; other agents may be editing nearby files.

Each sub-agent outputs:

1. Interface (types, methods, params, plus invariants, ordering, error modes)
2. Usage example showing how callers use it
3. What the implementation hides behind the seam
4. Dependency strategy and adapters (see [DEEPENING.md](DEEPENING.md))
5. Trade-offs: where leverage is high, where it's thin

### 3. Present and compare

Present designs sequentially so the user can absorb each one, then compare them in prose. Contrast by **depth** (leverage at the interface), **locality** (where change concentrates), and **seam placement**.

After comparing, give your own recommendation: which design you think is strongest and why. If elements from different designs would combine well, propose a hybrid. Be opinionated: the user wants a strong read, not a menu.
