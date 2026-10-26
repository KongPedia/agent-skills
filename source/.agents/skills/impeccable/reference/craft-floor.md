> Modified for Project Blueprints: instruction-only adaptation; upstream runtime automation is not installed.

# Craft floor

Load this after the direction is settled. The pinned brief and committed visual world take precedence over stylistic examples throughout this file, including upstream bans. Accessibility, safety and verification remain governed by the repository. No design hook or automatic detector is installed; these are manual judgment/check prompts, not permission to redesign.

## Verify

Each of these is a check on the built result, not an intention. Run them together in each batched look at the render, not as separate screenshot trips; the checks share one render.

- **Contrast:** body and placeholder text ≥4.5:1, large text ≥3:1. On colored surfaces prefer secondary text harmonized with that hue or foreground, while retaining the approved palette and measured contrast.
- **Depth:** shadows carry an offset and a soft blur. A zero-offset colored halo is decoration.
- **Spacing:** tight groups, generous separation, more space above a heading than below it. Read the computed values.
- **Type:** readable prose measure (often 65–75ch), balanced headings and clear scale/weight steps. Use existing type tokens; compact data and labels need not follow prose dimensions. Run the real copy at every breakpoint and fix what overflows.
- **Motion:** where justified, use coherent, interruptible state feedback, not scattered effects. Operate surfaces may need no decorative motion. Respect reduced motion and measured performance before using costly effects.
- **States:** hover, disabled, loading, error, empty. Plus real content, working controls, responsive composition, keyboard focus.
- **Browser surfaces:** the parts you did not draw still carry the design. Text selection, the caret, custom scrollbars, focus rings, underline offset, and the numerals in tabular data all ship with browser defaults that belong to no design system. Check their usability and harmony with the approved system. Native defaults are valid, especially on Operate surfaces; do not replace affordances merely for visual novelty.
- **Copy:** the product's own language. Controls name their action; errors name the problem and the recovery.
- **Coverage:** every brief requirement present and findable within seconds.

## Investigate unreasoned defaults

These patterns can reveal unreasoned defaults. Confirm product impact before changing them; legitimate labels, density, containment and tactical status visuals may be intentional. None of these stylistic examples overrides the brief or authorizes expanding scope.

Page scaffolds:

- Same-size cards of icon plus heading plus text as the page structure. Investigate whether nested containment clarifies actual hierarchy or merely repeats a template.
- The hero-metric template: big number, small label, supporting stats, accent.
- A redundant kicker or eyebrow above a heading. Remove it only when it adds no distinct task/status context; preserve meaningful metadata and approved operator labels.
- Section numbers (01 / 02 / 03) unless the sequence itself carries information the reader needs.
- A modal for a task that needs neither interruption nor protected focus.

Surface habits:

- Gradient text. Emphasis comes from weight or size.
- Glass and blur as decoration rather than as a specific effect.
- A colored `border-left` or `border-right` above 1px on cards, list items, callouts, or alerts.
- Hard offset shadows (`box-shadow: 4px 4px 0`) outside a world that is actually neobrutalist. The zero-blur block shadow is a costume, not a depth system; a world that did not choose it never earns it as a default.
- Sparklines, progress rings, and soft-shadowed rounded rectangles standing in for content.
- Monospace as a costume for "technical" rather than for code, data, or measurement.
- A system display face (Impact, Arial Black, the platform sans) as the display voice of an own-world page. Respect existing approved fonts; source a new face only within an authorized design change, with licensing and loading behavior checked.
- Unicode glyphs or emoji standing in for an icon system. Icons are drawn, from a real library or authored SVG, in one consistent stroke and weight.
- Geometric masks standing in for organic contours. A circle, polygon, or radial-gradient cutout approximating a photographic subject's edge is the cheap version of the effect and reads worse than omitting it. Derive an alpha matte from the actual image, or produce a cut-out asset.
- Light or dark picked by category. Pick it from the use scene: who, where, under what ambient light.

- Tracking stops at -0.04em. -0.02 to -0.03em usually reads better.
- Declare elevation once, border or shadow. A 1px border under a wide soft shadow is the ghost card. Use the project's corner/elevation tokens; do not impose a 12–16px radius on an established system.
- Real illustration or none. Sketch-style SVG scenes, `loose-sketch` / `doodle` class names, and `feTurbulence` grain read as amateur. This bans SVG imitating pictures, never SVG doing geometry: crisp vector shapes, diagrams, animated linework, and shader-driven effects remain first-class media. A shaded, perspectived, or figure-bearing illustration is a picture even in line-art style; geometry means shapes a session can specify exactly.
- Backgrounds are surfaces, textured only from the subject's world. `repeating-linear-gradient` stripes and two-axis grid overlays need an actual canvas, map, blueprint, or measuring tool under them.
- Claims and configuration come from supplied truth; label illustrative values honestly. Naming a concept and then ironizing it is not a claim.

The floor holds the mechanics; it never picks the direction. With every check green, spend the page on the committed world, and when torn between refined and committed, commit.
