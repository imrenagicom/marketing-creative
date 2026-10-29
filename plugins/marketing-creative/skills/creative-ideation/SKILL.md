---
name: creative-ideation
description: Deprecated Marketing Creative skill for creative concepts from a marketing brief. For new work use Video Studio's director for video directions, or marketing-image-board (marketing-images plugin) for image concepts. Use this only to resume or revise an existing Marketing Creative project.
---

# Creative Ideation

> **Deprecated.** Marketing Creative is being retired in favour of Video Studio and Marketing Images. For new work, use Video Studio's `$director` for video directions, or `$marketing-image-board` (marketing-images plugin) for image concepts. Use this skill only to resume or revise an existing Marketing Creative project, and keep that project's files intact.

Read `MARKETING_BRIEF.md` or its supplied equivalent. If it is incomplete, infer noncritical details explicitly and use `$marketing-brief` (optional marketing-performance plugin; use the supplied brief or establish the necessary strategic facts directly if unavailable) only for strategic gaps that affect the concepts. Do not repeat answered intake.

## Develop ideas, not skins

Read [concept-contract.md](references/concept-contract.md). For an open assignment, offer a small set of genuinely different ideas, usually three. A demonstration, a barrier reversal and a character story can be different concepts; three slogans on the same scene sequence are variations.

Each concept ties audience tension to product mechanism, visible evidence and a clear action. Include the opening words/first frame, story progression, product attribution, proof, ending, production needs, format adaptations and test hypothesis. Do not invent customer experience or proof.

For image posts, carousels or static ads, use `$marketing-image-board` (marketing-images plugin) to visualize ideas in one generated contact sheet with optional references. Choose a useful concept count and sheet/grid ratio for the brief, keeping every concept separately croppable. Keep this optional for text-only ideation. Selected image concepts go to `$marketing-image-producer` for standalone or discounted asynchronous batch finals; video concepts continue through the director.

Use [concept structures](../motion-art-director/references/concepts.md) for options, [hooks](../ad-video-director/references/hooks.md) for openings, and [reference analysis](../ad-video-director/references/reference-analysis.md) when supplied references matter. Borrow communication and motion principles; ground identity and claims in this product. Do not assume the reference's performance.

## Selection and handoff

Recommend a direction and state its tradeoffs. If the user wants options, stop at the requested selection point. If the user selects a concept or authorizes autonomous selection, develop it directly without another approval gate. Existing authorization persists.

Record alternatives in `CONCEPTS.md` and the selected direction in `CREATIVE_BRIEF.md` when saving is authorized. Give the selection a stable ID. Pass both briefs to [ad-video-director](../ad-video-director/SKILL.md) for the exact script; production begins through [motion-video-producer](../motion-video-producer/SKILL.md) only when requested.
