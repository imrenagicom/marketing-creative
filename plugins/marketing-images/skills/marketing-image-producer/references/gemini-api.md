# Gemini integration register

Verified against Google's official documentation on **2026-10-15**:

| Concern | Choice / owning source |
| --- | --- |
| Default model | Nano Banana 2.1, stable ID gemini-nano-banana-2.1; [model page](https://ai.google.dev/gemini-api/docs/models/gemini-nano-banana-2.1), [release notes](https://ai.google.dev/gemini-api/docs/changelog) |
| Image/edit capability | Text plus source-image parts, output image; [image generation guide](https://ai.google.dev/gemini-api/docs/image-generation) |
| Reference/ratio flexibility | References are optional; up to fourteen image inputs including selected tile; default model supports fourteen documented ratios. Same image guide lists the limits and resolution tables. |
| API choice | generateContent remains supported; using its shared request shape keeps synchronous and batch inputs equivalent; [Interactions overview](https://ai.google.dev/gemini-api/docs/interactions-overview) |
| Batch support | Model lists Batch API supported; [batch guide](https://ai.google.dev/gemini-api/docs/batch-api) |
| Batch price | Published at half equivalent standard input/output pricing; [pricing](https://ai.google.dev/gemini-api/docs/pricing) |
| REST resource shapes | batchGenerateContent returns a long-running Operation; [Batch REST reference](https://ai.google.dev/api/batch-api) |
| File transport | Resumable JSONL upload and batch result download; [Files API guide](https://ai.google.dev/gemini-api/docs/files) |

The image guide recommends Interactions for new interactive applications; Batch currently uses generateContent only. This helper intentionally uses the supported common API and does not pretend background Interactions are discounted batch jobs.

REST uses model path /v1beta/models/<id>:generateContent, imageConfig.aspectRatio/imageSize and responseModalities TEXT/IMAGE. Source images use inlineData.mimeType/data. Batch entries carry metadata.key; file-backed JSONL uses key/request. Operation responses can nest inlinedResponses.inlinedResponses or provide responsesFile; SDK-shaped fixtures are supported as a compatibility path. State can be BATCH_STATE_* or JOB_STATE_*; neither is treated as proof all items succeeded.

No latest alias is guessed. Refresh this register and tests when changing the default model or API contract; --model allows deliberate choices and account availability can differ. Do not silently fall back after model-access errors.

No provider code samples or generated media are copied into this skill. Offline tests use synthetic PNGs and mocked REST responses. They establish payloads, crop geometry, state handling and decoding, not actual model adherence or image quality. A live run still requires the configured API project, billing/access and authorized spend; reference images are optional.
