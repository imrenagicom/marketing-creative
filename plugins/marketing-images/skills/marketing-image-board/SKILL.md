---
name: marketing-image-board
description: Explore marketing image concepts in a flexible tiled Gemini contact sheet, with optional reference images, then crop individual previews. Use for low-cost Instagram post, ad or carousel ideation before final generation.
---

# Marketing Image Board

Use the marketing brief and any supplied reference images to explore distinct image assets in ONE generated image. A board is a set of marketing options or carousel slides, not necessarily a chronological video storyboard. Reference images are optional; use them when available to guide product identity, brand, characters or style.

Read supplied references using available image-viewing tools and identify each one's role. Preserve the actual product, brand and supported claims. Read supplied briefs/concepts rather than repeating strategy intake; when the underlying ideas are missing, draft them first: each concept ties the audience's tension to visible product proof and a clear action, and differs in idea rather than palette. Use `$marketing-brief` (marketing-performance plugin) when the campaign strategy itself is missing.

## Plan the cells

Read [board-workflow.md](references/board-workflow.md). Choose how many concepts are useful for the request, then write a factual brief, visual direction, optional references and one stable ID/prompt/exact copy per concept. The [campaign example](assets/campaign.example.json) illustrates one possible layout; adapt its count, ratios and references.

Choose a sheet ratio and rows/columns that keep each concept readable and independently croppable. Square, portrait, landscape and panoramic sheets are supported. Specify grid dimensions/ratio or omit them for automatic packing from concept count and intended ratios. A 3×3 square is only one option. Unused trailing cells stay blank and are excluded from crops. Keep gutters, labels and shared objects outside the cells; vary the underlying concepts and composition rather than only palette.

## Generate once, split locally

Use the [Gemini helper](../marketing-image-producer/scripts/gemini_images.py), defaulting to Nano Banana 2.1 as verified in the [API reference](../marketing-image-producer/references/gemini-api.md). Run board dry-run to check request count, reference and dimensions without a key or paid request. The actual board command makes ONE generateContent call, regardless of cell count.

Use [split_board.py](scripts/split_board.py) to crop the returned sheet into PNG previews with stable IDs and crop metadata. Equal-grid splitting assumes the model followed the grid; inspect the whole board before trusting crops. If it did not, supply measured crop boxes or revise deliberately. Do not auto-regenerate a paid board in a retry loop.

## Review and selection

Show the original board and relevant cropped previews. Review concept separation, product fidelity, text, claims, brand consistency, grid edges and each placement's framing. Mark actual review notes and selected IDs in the campaign work directory. Splitting does not mark tiles reviewed.

Inspect actual crop dimensions: more tiles mean fewer pixels per concept. Do not market crops as production-resolution files. Hand selected IDs, available original references, plan and tile directory to [marketing-image-producer](../marketing-image-producer/SKILL.md) for full-quality regeneration. Preserve selection; do not generate all finals merely because they appeared on the board.

Use existing authorization for generation. Creating a brief or plan alone does not authorize a paid call. Credentials belong in the external environment, never the plan or skill.
