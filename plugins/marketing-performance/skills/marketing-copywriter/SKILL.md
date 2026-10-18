---
name: marketing-copywriter
description: Write or revise marketing copy for ads, landing pages, email, and social posts in distinct tones and styles, from personal experience sharing to direct selling. Use for exact wording, multiple versions, and localization; full video scripting and shot direction belong to ad-video-director.
---

# Marketing Copywriter

Turn the supplied strategy or draft into usable copy that connects a specific audience's situation to a supported benefit. Match the requested feel and purpose, whether sharing something useful, building trust or asking for a purchase. Scale the work to the requested deliverable; a headline edit does not require a campaign plan.

## Establish the writing context

Read the supplied brief, selected concept, draft, product evidence and brand examples first. Preserve the objective, audience, offer, destination, approved terminology and creative direction unless the user asks to change them. For revisions, identify what needs improvement and retain effective wording and unrelated approved decisions.

Resolve the channel/placement, audience and awareness, language, desired action, supported value proposition, offer terms and voice only as far as they affect the requested copy. Ask about material gaps; otherwise draft with stated assumptions. Missing evidence should narrow the claim, not become invented proof. When broader strategy is requested or materially missing, use [marketing-brief](../marketing-brief/SKILL.md); a supplied equivalent is sufficient.

## Choose the voice and selling intensity

For multiple tones, styles or feels, read [voice-and-style.md](references/voice-and-style.md). Honor named styles and the requested count; for an open exploration, choose a useful small set of clearly different approaches. Separate who is speaking, their attitude, the writing structure, intended emotional feel and how directly the copy sells. Personal and sales-oriented voices can coexist; do not make every version sound like the same advertisement with different adjectives.

Ghostwrite firsthand copy from the actual speaker's supplied experiences, observations and vocabulary. Keep their relationship to the product clear; a founder, customer and sponsored creator are different speakers. Do not invent use, discovery, emotions, outcomes or independent endorsements. Without an anecdote, write warmly from known product facts or ask for the missing experience when firsthand narration is essential. A proposed first-person template must remain visibly provisional until the speaker confirms it. Never imply that the assistant used the product.

For personal sharing, let a concrete situation, useful detail and honest reflection carry the message; a recommendation can be gentle and a purchase CTA can be absent when the purpose permits. For direct selling, make the supported value, proof, actual offer and next action explicit. Respect an existing conversion objective while changing the voice; do not silently remove a required CTA or invent urgency to make a sales version stronger.

## Build the message

Choose the reader's main barrier or motivation, the relevant product mechanism, the evidence that supports it and any next action appropriate to the purpose. Lead with the part most useful in that buying situation. Use concrete outcomes and distinctive product details; show how a feature helps instead of merely renaming it as a benefit. Treat copywriting formulas as optional scaffolding, not mandatory sections.

Keep factual claims traceable to supplied or checked sources. For consequential claims, record the claim, evidence and permitted wording in concise notes outside the final copy. Do not invent customer quotes, usage statistics, comparisons, guarantees, prices, free trials, scarcity or deadlines. Qualifiers and material offer conditions must remain visible where needed to understand the promise. Label missing evidence in review notes; provide a supported alternative rather than putting unsupported assertions into ready-to-use copy.

Match the user's brand examples and requested language. Prefer natural phrasing to literal translation; preserve product names, amounts, eligibility, claim strength and CTA meaning. Avoid assuming a person's sensitive traits in direct-address ad copy. Do not present editorial review as platform-policy approval.

## Adapt and refine

Read the relevant section of [channel-copy.md](references/channel-copy.md) for ads/social, landing pages, email or localization. Deliver exact fields for the requested surface, keeping internal rationale separate. Match the CTA to what actually happens at the destination. Apply supplied limits; if platform-specific limits or requirements matter and are not supplied, verify current official documentation and record its date/source, or mark them unverified. Do not invent universal character limits or claim upload readiness without checking them.

When variants are requested, keep the offer and facts constant unless those are the stated test variable. For style exploration, label each version with a stable ID and a short voice/style/feel description, then supply the complete requested copy. Make the differences audible in perspective, rhythm, detail, structure and CTA intensity, not just the labels. For performance tests, identify a meaningful changed variable and state the hypothesis. Recommend a candidate based on audience fit and evidence, without claiming it will win. Distinguish a controlled copy test from exploring several different directions.

Review the promise against its payoff, factual support, speaker authenticity, voice, readability, CTA/destination and requested constraints. Check that requested styles actually differ and that personal versions have not drifted into generic sales pitches. Preserve important terms when shortening. For a small edit, return the improved copy and only the material explanation; larger assignments can include a recommended version, alternatives and unresolved evidence or limits.

## Deliver and hand off

Return copy in chat unless saving is requested or already part of the task. When saving inside a campaign workspace, follow [campaign-manager](../campaign-manager/SKILL.md)'s `<YYYY-MM-DD>-<campaign-name>/` layout (and for Meta ads, `meta/campaigns/<meta-campaign-slug>/adsets/<adset-slug>/ads/<ad-slug>/`): place working drafts, voice/style explorations and editorial notes in `copy/drafts/`, and save user-approved copy revisions in versioned directories (`copy/approved/v001/`, `copy/approved/v002/`, and so on) without overwriting earlier approved versions or `tracking/` exports. Keep copy out of the installed plugin. Include enough channel, audience, language and revision context for another writer or publisher to use it. Keep placeholders visibly provisional and separate unresolved notes from ready-to-use fields.

For tagged destinations or campaign records, use [campaign-manager](../campaign-manager/SKILL.md) when requested; retain existing URLs and align `ad.json`, `creative_id` and `utm_content` mappings with the approved copy revision. For a full timed video script or shot plan, hand the chosen wording and brief to `$ad-video-director` from the optional marketing-creative plugin when available, or supply a portable handoff. Ordinary copywriting works with Marketing Performance alone. Writing copy does not itself authorize publishing, sending email, changing ad accounts, buying media or generating paid assets.
