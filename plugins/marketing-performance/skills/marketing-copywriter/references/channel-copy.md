# Channel copy

Read only the section relevant to the deliverable. These are editorial considerations, not current platform specifications. Use the supplied field names and constraints; verify official requirements when actual placement limits matter.

## Ads and organic social

For an ad, distinguish primary text, headline, description, CTA label and any on-image wording. Include only fields used by the requested placement. Keep essential meaning understandable when optional fields are absent or long text is truncated. State the value of taking action before asking for it, and carry the same promise through the destination. Do not insert an unavailable CTA button label.

For social posts, match the reader's context and the requested format. A carousel needs an opening promise, a useful ordered progression and a payoff; it is not a collection of unrelated headline variants. Distinguish captions from text that must fit on the artwork. Use hashtags, emoji or engagement prompts when they suit the brand and assignment, rather than adding them by default. Do not manufacture customer comments, endorsements or personal experience.

Short-form video hooks, overlay lines and post captions fit this skill. Timing the whole script, dialogue, shots and edit cues belongs to Video Studio's scriptwriter and shot-designer (`$studio-producer`). Preserve a supplied concept when refining its lines.

Whenever images, carousel slides, videos or other visual assets are created or attached for an ad or social post, also write concise accessibility alt text for each visual asset (per image, per carousel slide in sequence, or describing the video's visual action and key on-screen text). Describe what is actually shown and any essential text rendered in the artwork without keyword stuffing or inventing unshown details.

For test variants, retain a shared baseline and identify the changed variable, audience and primary success measure from the brief. An objection-led opener and a mechanism-led opener test different arguments; punctuation changes rarely establish a distinct hypothesis. Choose business outcomes appropriate to the campaign, and treat click-through or engagement as diagnostic when they do not establish that outcome. A hypothesis is not a measured performance result.

### Meta Ads (Facebook & Instagram) — Format & Copy Specifications

*(Verified 2026-10-20 against Meta Ads Guide, Meta Business Help Center "Add Multiple Text Options", and Meta Marketing API `v25.0` `AdCreative` / `AdAssetFeedSpec` documentation.)*

#### 1. Core Ad Text Fields & Mobile Truncation Thresholds

| Field | API Field (Single / Multi-Text) | Recommended Visible Budget | Truncation & Placement Behavior | Copywriting Rule |
| :--- | :--- | :--- | :--- | :--- |
| **Primary Text** | `link_data.message` / `video_data.message` or `asset_feed_spec.bodies` (`1–5` options) | **First `80–125` chars** before truncation (`90–500` chars total depending on variant) | Mobile Feed truncates after **~`125` chars** (`"…More"` / `"…Selengkapnya"`). Reels & Stories bottom overlays truncate after **~`55–72` chars**. | Front-load the audience qualifier, hook, or core value proposition in the first `80–125` characters so the ad makes sense without expanding `"…More"`. |
| **Headline** | `link_data.name` / `video_data.title` or `asset_feed_spec.titles` (`1–5` options) | **`25–40` chars** (keep core meaning within **`~27–32` chars**) | Appears bold next to or above the CTA button on Feed; rendered as secondary overlay or omitted on some Story/Reels layouts. | State a crisp value promise, product proof, or action prompt beside the CTA button. Never copy-paste the first sentence of Primary Text or repeat the on-image headline word-for-word. |
| **Description** | `link_data.description` or `asset_feed_spec.descriptions` (`1–5` options, optional) | **`20–30` chars** | Shown beneath the headline only on selected Feed placements; frequently hidden on mobile and vertical placements. | Treat as optional micro-reinforcement (e.g., platform availability or offer terms). Never place essential claims or qualifiers solely in Description. |
| **Call to Action** | `call_to_action.type` | Provider enum (`LEARN_MORE`, `SIGN_UP`, `SUBSCRIBE`, `SHOP_NOW`, `DOWNLOAD`, `GET_OFFER`) | Rendered on the native button or Story/Reels sticker. | Match the actual destination behavior (e.g., use `LEARN_MORE` or `SIGN_UP` when routing to a web app `/app` that also links to mobile apps; use `DOWNLOAD` only when routing directly to an app store or download page). |

#### 2. Multiple Text Optimization (`asset_feed_spec`, up to 5 Options per Field)

For Single Image and Video ads on Meta, Meta Ads Manager and the Marketing API (`asset_feed_spec` with `optimization_type: "DEGREES_OF_FREEDOM"`) support **up to 5 Primary Text options (`bodies`)** and **up to 5 Headline options (`titles`)** on a single creative:

- **Default to 5 Primary Text Options + 3–5 Headline Options**: Unless the user requests a single copy string, provide 5 Primary Text options (`primary_text_options`) and 3–5 Headline options (`headline_options`).
- **Lead with the Strongest Anchor in Option 1 (`bodies[0]`)**: Place the highest-conviction hook in Option 1 (`primary-text.txt` and `primary_text_options[0]`).
- **Diversify the 5 Primary Text Options by Angle and Length** (never just swap synonyms):
  1. **Option 1 — Category / Standard-Shift or Flagship Value Hook** (`300–480` chars): Frames why the solution matters right now (e.g., a new exam/industry standard or complete curriculum shift), followed by `4–5` scannable `•` feature-to-benefit bullets and a clear closing CTA line.
  2. **Option 2 — End-to-End Outcome + Cross-Platform Bridge Hook** (`320–500` chars): Connects beginner-to-advanced progression with explicit platform availability (e.g., Web & iOS App) and structured capability bullets.
  3. **Option 3 — Problem / Friction-Relief Hook** (`300–480` chars): Opens with the audience's main starting friction or confusion (e.g., *"Not sure where to start…?"* / *"Bingung mulai dari mana…?"*) and shows how the product removes that friction step by step.
  4. **Option 4 — Mechanism / Active-Practice Contrast Hook** (`280–450` chars): Contrasts the common ineffective habit (e.g., passive memorization) with the product's active mechanism (e.g., interactive feedback, real-time AI practice, guided workflows).
  5. **Option 5 — Concise Mobile / Reels / Stories Checklist Hook** (`160–280` chars): Ultra-tight 1-sentence opener + compact `✓` checklist + 1-line CTA designed for rapid mobile Feed, Stories, and Reels scanning.
- **Combinatorial Coherence (`bodies[i] × titles[j]`)**: Because Meta dynamically pairs any Primary Text option with any Headline option per impression, verify that **every** Primary Text option reads naturally alongside **every** Headline option without contradiction or verbatim duplication.

#### 3. Best Practices by Creative Format

1. **Single Image Ads (`1:1` / `4:5` Feed & `9:16` Vertical Story / Reels)**:
   - **Visual-to-Copy Division of Labor**: The artwork's on-image headline, badge, and UI screenshot carry the 0–1 second visual stop. The Primary Text must **expand** on the mechanism, modalities, and next step rather than repeating the exact on-image headline verbatim.
   - **Multi-Placement Resilience (`stream`, `story`, `reels`)**: When a vertical (`9:16` or `4:5`) single-image ad runs across Instagram Feed (`stream`), Stories (`story`), and Reels (`reels`), ensure the first `80–125` characters of every Primary Text option stand on their own before truncation, and include at least one concise checklist variant (Option 5) for fast vertical placements.
   - **On-Image Safe Zones**: When writing or revising on-image text for `9:16` (`1080×1920` / `3072×5504`) Stories/Reels creatives, keep essential text out of the top `~14%` (`250 px` on `1080×1920`) and bottom `~20–35%` (`380–670 px`) where profile headers, captions, and CTA stickers overlay the image.

2. **Video Ads (Reels `9:16`, Stories `9:16`, and Feed Video)**:
   - **Complement the 0–3s Audio/Visual Hook**: The opening `80–125` characters of Primary Text should reinforce the video's first-frame problem or promise for sound-off scrollers without repeating the exact spoken first sentence word-for-word.
   - **Summarize Key Proof for Non-Finishers**: Because many converters click before finishing a 30–70s walkthrough video, use scannable middle bullets in the Primary Text to list the core capabilities demonstrated across the video's beats.
   - **Bridge to the Immediate First Action**: End the Primary Text and Headline with the exact low-friction action the viewer can take immediately on the landing page (e.g., choosing a level and starting one practice session).

3. **Carousel Ads (`2–10` Cards, `1:1` Square or `4:5` Portrait)**:
   - **Ad-Level Primary Text (`message`)**: Frame the overarching umbrella promise in the first `80–125` characters and invite the user to swipe through the sequence.
   - **Per-Card Copy (`child_attachments[i]`)**: Every card requires its own distinct **Card Headline (`name`, `25–40` chars, critical `~27–32` chars)** and optional **Card Description (`description`, `20–25` chars)** aligned to that card's visual:
     - **Card 1 (Hook Card)**: Establish the core problem or umbrella value proposition so Card 1 works standalone on first impression.
     - **Cards 2 to N−1 (Ordered Feature / Proof Progression)**: Dedicate each card to one distinct capability, modality, or proof point in a logical progression (e.g., foundation → practice modalities → AI feedback → advanced readiness).
     - **Card N (Payoff & CTA Card)**: Summarize the full-stack payoff, state platform availability, and align the final Card Headline with the CTA button.

#### 4. Campaign Workspace `copy.json` Structure for Meta Ads

When saving approved Meta Ad copy in `copy/approved/vNNN/copy.json` (used with `campaign-manager` and `adsctl meta ads text set` / `adsctl meta creatives create`), store both the primary default fields (`primary_text`, `headline` — matching `primary-text.txt` and `headline.txt`) and the full multi-option arrays (`primary_text_options`, `headline_options`):

```json
{
  "revision": "v001",
  "language": "id",
  "primary_text": "<Option 1 primary text — also written to primary-text.txt>",
  "primary_text_options": [
    "<Option 1 — Anchor / standard-shift hook>",
    "<Option 2 — End-to-end outcome + platform bridge hook>",
    "<Option 3 — Problem / friction-relief hook>",
    "<Option 4 — Mechanism / active-skill hook>",
    "<Option 5 — Concise mobile checklist hook>"
  ],
  "headline": "<Headline 1 — also written to headline.txt>",
  "headline_options": [
    "<Headline 1 — Core value / standard promise (25-40 chars)>",
    "<Headline 2 — Cross-platform completeness promise (25-40 chars)>",
    "<Headline 3 — Direct action / first-step prompt (25-40 chars)>"
  ],
  "call_to_action": "LEARN_MORE"
}
```


## Landing pages

Start from the page's job and entry source. A hero should let the reader identify the product, relevant value and next step. Maintain message continuity with the referring ad or email. Use a subhead for mechanism or necessary qualification rather than repeating the headline.

Order supporting sections around the audience's buying questions: how it works, why to believe it, what it includes, material terms and the relevant objections. Use only sections that help this page. Place proof near the claim it supports; use descriptive product evidence when testimonials or performance data are unavailable. A labeled proposed proof slot is a production note, not permission to fabricate a testimonial.

Supply copy by section and UI field, including button text and necessary helper text. Do not promise a trial, immediate access, a demo or a download unless that is the actual next step. For a single-section revision, preserve the rest of the page and flag any conflicting surrounding promise instead of silently rewriting it.

## Email and lifecycle messages

Distinguish subject, preheader, body and CTA. Let the preheader add useful context instead of duplicating the subject. State the relevance of the message to the recipient's actual relationship or trigger; do not invent a prior conversation, usage event or personal detail to make the email feel familiar.

Keep one primary action for a focused message unless the brief calls for a digest or multiple destinations. Preserve required sender, preference and unsubscribe content supplied by the user. Avoid fake reply/forward subjects and misleading urgency. Writing a draft does not authorize sending it or adding recipients to a sequence.

For a sequence, make each message's trigger, purpose, audience state and CTA explicit. Give the messages distinct useful jobs; do not manufacture a send schedule, offer expiry or behavioral trigger when those decisions are missing. Mark proposed personalization fields and define a sensible fallback. Keep actual recipient data out of reusable examples.

## Localization and transcreation

Use the requested locale, register and brand vocabulary. Adapt idioms and sentence rhythm while preserving the underlying proposition and evidence. Do not strengthen a qualified claim in translation or change currency, pricing, eligibility or legal terms without a supplied approved equivalent.

Keep variant IDs aligned across languages. If a pun or cultural reference cannot retain its meaning, propose an idiomatic alternative and explain the changed nuance outside the copy. Apply and check each language's requested length constraints separately; translated text will not necessarily fit the original artwork. Flag unresolved terminology or native-review needs where they affect confidence, without presenting a translation as audience-tested.
