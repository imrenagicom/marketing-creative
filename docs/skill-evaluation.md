# Behavioral evaluation scenarios

Run these by loading the skill and only the raw brief/reference needed for each case. Keep generated plans outside commits. Check output decisions, factual support, timing and producibility rather than exact headings or wording. A valid manifest is not a behavioral evaluation.

| Scenario | Observable acceptance criteria |
| --- | --- |
| 30-second cold-audience app ad, objective activated users, screenshots available, no price supplied | Chooses a relevant first-use task, measures activation instead of CPI alone, invents no price/trial, covers all 30 seconds, gives ready-to-say lines and usable capture directions |
| Same product, warm audience, price objection and verified offer | Changes ordering/proof to address the barrier; does not repeat unnecessary category setup; uses only the supplied terms and one matching destination |
| Six-second awareness cutdown requested from a 75-second creator ad | Writes one memorable product-linked idea; does not cram all dialogue or five full modules into six seconds; preserves attribution and explains the changed job |
| Reference recording starts mid-ad and contains post-ad browsing | Separates recording duration from creative span; labels proposed opening; excludes browsing/UI from authored creative; does not assert sample ROAS |
| "Make it viral; promise fluency in seven days" without evidence | Offers a strong demonstrable alternative and keeps the unsupported result out of final copy |
| Ten hooks and literal one-second breakdown | Produces distinct buyer/visual mechanisms, chooses a supported hypothesis, covers every second without requiring a cut each second, and pays off the actual hook |
| High retention, low sales supplied as the only results | Does not declare CTA the cause; inspects relevance, proof, offer, destination, tracking and downstream quality; proposes a discriminating next test |
| Creator comment reply requested without an authentic comment | Uses a labeled question/FAQ instead of manufacturing a customer endorsement; distinguishes demonstrator from real customer |

Keep sample-specific analyses, raw media, trial outputs, and evaluation outcomes local unless explicitly selected for publication. Do not infer successful installation, model behavior, or ad performance from structural packaging checks.

## Revised suite scenarios

| Scenario | Observable acceptance criteria |
| --- | --- |
| Strategy-only request | Marketing brief records objective/metric, audience/barrier, supported claims and placement requirements; does not force a hook or start production |
| Open brief followed by selection | Concepts differ in mechanism; selected creative brief retains ID/evidence; director scripts chosen idea without repeated intake |
| Supplied selected concept/script | Producer resumes downstream without unnecessary campaign interview |
| Desktop landscape, mobile Reels, portrait feed and square | Four canvases configured; placements distinguished from device; independent layout/frame/export checks |
| Real captures and no verified trial | Capture/image/footage or custom generator path explicit; illustrative UI is not proof; no invented offer |
| Narration arrives later | Provisional seconds replaced by word cues; missing alignment precision reported |
| Repeated CTA or Mandarin phrase | Ambiguity fails unless occurrence supplied; Han characters preserved; segmentation limits identified |
| CTA revision | Dry-run shows span/context; backup; synchronized script/audio/alignment; visual copy/cues/captions and neighboring beats reviewed |
| User edited generated HTML | Edits preserved/reconciled before rebuilding |
| Intentional silence/stillness | Editorial choices distinguished from broken coverage; no forced continuous motion |
| Runtime/browser/provider unavailable | Exact pending validation reported; no false rendered-delivery claim |
| Wrong-ratio/missing-audio/stale encode | Affected export fails; actual file/build hashes recorded after current render |

Executable regressions live in tests/test_production.py. Browser/framework smoke tests use temporary projects and local dependencies. Review actual snapshots and listen to audio where applicable. Fixtures and screenshots are not committed as finished campaign assets.

## Image workflow scenarios

| Scenario | Observable acceptance criteria |
| --- | --- |
| Brief, optional references and an open concept count | Chooses enough distinct ideas for the task; chooses a readable sheet ratio/grid; one board request; each occupied cell crops to its stable concept ID |
| Five or eleven concepts, portrait/landscape sheet | No fixed nine-item requirement; explicit or automatic grid has sufficient cells; blank trailing cells are not saved as assets |
| No reference, or product plus style references | Brief-only generation works; supplied references are viewed and assigned roles; final selected tile has the correct image index |
| Concept selected from the board | Stable ID maps to its own crop; standalone request uses original source plus selected tile; unselected ideas are not generated |
| Multi-slide carousel instead of alternatives | Plan preserves slide order and continuity; does not force nine unrelated concepts |
| Model adds gutters or uneven cells | Inspects board and uses measured crop boxes or deliberate revision; does not claim geometric splitting verified composition |
| Request nine production-resolution images | Explains preview resolution; reconstructs selected finals separately, instead of claiming nine 4K files from a single 4K board |
| Three selected finals with flexible deadline | Uses actual Batch API, persists job identity, returns for status/download later; distinguishes discount from output quality |
| One failed batch item, one wrong-ratio response | Preserves successes and wrong-ratio bytes, flags item errors and review issues; no automatic paid resubmission |
| Submission timeout or interrupted download | Unknown submission retains state for provider lookup; interrupted collection resumes with matching files and no new generation |
| Transparent product/reference or changed local tile | Crops preserve alpha; changed tile hash requires deliberate reconciliation |
| Square, portrait feed, vertical and landscape images | Requests 1:1, 4:5, 9:16 and 16:9 explicitly; checks actual dimensions and current placement specifications |
| No key or live provider validation | Dry-run and splitting work without credentials; reports that offline validation does not establish real model quality/access |

Executable image regressions live in tests/test_marketing_images.py and use synthetic pixels and mocked API responses. Independent forward-testing exercised the requested board → selection → batch → recovery path offline. Live marketing-image quality requires an authorized provider run and visual review.

## Optional generated video and assembly

| Scenario | Observable acceptance criteria |
| --- | --- |
| Produce an ad without provider approval | Producer uses supplied/local sources; Veo/Omni remain off; optional generation plan does not launch a paid call |
| User asks to explore Veo or Omni | Prepares exact prompt/media, model/mode/settings and current estimate; dry-run needs no key/network; asks for approval before paid generation |
| Approved request subsequently changes | Changed content/settings/reference/quote invalidates the approval fingerprint; no silent reuse or model fallback |
| First/last frames and character/style references | Correct explicit source/reference roles; loops reuse their endpoint; unsupported duration/model/control combinations fail locally |
| Uploaded talking footage requested for voice editing | Omni limitation is identified; narration revision routes to motion-voice, preserving existing footage when appropriate |
| Submission timeout, interrupted SSE or provider expiry | Preserves identity/received files, queries once, downloads/reuses verified local output; no automatic paid regeneration |
| Follow-up edits in the same conversation after a restart | Python history/continue selects the intended saved run, chains its interaction ID, inherits omitted settings and preserves each parent; every paid edit has a new approval |
| Earlier-version branch or unresolved conversational turn | Explicit parent selection controls branching; pending/unknown/stateless turns fail before submission; old outputs remain intact and local history never claims server context is permanent |
| Three.js scene, HTML overlay, product image and generated b-roll | Producer maintains one timeline/manifest, imports selected source hashes and measured media, routes custom scenes to a project generator; does not claim bundled engine renders arbitrary custom visuals |
| Native vertical footage requested as square/feed ad | Reframes in separate 1:1/4:5 compositions, reviews focal detail/text/audio in each; a new provider generation still needs approval |
| Retained soundtrack or mute/mix mismatch | Measured source audio and storyboard hasAudio agree with audioPolicy; actual playback/mix/listening verified before delivery |
| Imported unreviewed or changed source | Changed hashes fail; provider findings and pending review remain visible; imports invalidate timing/build/export fingerprints |

tests/test_generated_video.py uses fake providers, synthetic media and actual local FFprobe checks. tests/test_asset_assembly.py covers immutable imports, provenance, source hashes, backups, audio policy, all four ordinary-media compositions and custom-generator resource contracts. Contract fixtures do not establish actual Three.js rendering or live generated-video quality.

## Optional HyperFrames capabilities

| Scenario | Observable acceptance criteria |
| --- | --- |
| Named effect, 3D product scene or mascot in a selected concept | Relevant registry/animation adapter is read before implementation; compatible generator preserves seekable playback, selected brand, stable timing and dependency hashes |
| Existing briefs handed to a specialized runtime workflow | Derives the upstream handoff without repeating strategy; preserves all four requested ratios, source evidence and paid-provider approval rules |
| Sound, media polish or revision review needs improvement | Routes to the matching audio/media/keyframe/CLI domain; actual frame/listening evidence establishes quality, not loading a skill |
| Reference checkout exists but required tool is unavailable | Uses accessible guidance, completes independent work and identifies missing execution/verification; does not claim installation, render success or send public feedback |


## Campaign operations and UTM records

| Scenario | Observable acceptance criteria |
| --- | --- |
| New campaign with brief, two channels and a destination | Creates a `<YYYY-MM-DD>-<campaign-name>` campaign directory and matching `campaign_id`, reuses existing workspace taxonomy, generates distinct links and saves a reproducible `tracking/v001` revision without a full intake restart |
| Meta Ads campaign (`meta-ads/`) with budget limit, ad set user targeting and two ads | Organizes `meta-ads/campaigns/<meta-campaign-slug>/campaign.json` (goal/objective, CBO/ABO budget limit), `adsets/<adset-slug>/adset.json` (optimization goal, `targeting`, `placements`), and `ads/<ad-slug>/ad.json` (`destination_url`, `utm`, `url_tags`, `link_id` mapped to root `campaign.json`) with ad-scoped `copy/` and `assets/` trees |
| Social media campaign across `instagram/`, `linkedin/` and `twitter/` reusing an approved ad asset (or vice versa) | Places `instagram/posts/<post-slug>/`, `linkedin/posts/<post-slug>/` and `twitter/posts/<post-slug>/` at the same level as `meta-ads/`; copies matching approved media into the target's `assets/approved/v001/` with `copied_from` provenance instead of regenerating, and omits `assets/development/` on the reusing post/ad |
| Storyboard, media development and copy drafts followed by user approval | Keeps work-in-progress material in `copy/drafts/` and `assets/development/` (`storyboard/`, `images/`, `video/`, `audio/`); asks `marketing-copywriter` to write accessibility alt text for created images/carousel slides/videos; places approved copy (including alt text) and deliverables in `copy/approved/v001/` and `assets/approved/v001/` with stable `creative_id` mapping |
| Approved copy or creative assets are revised and re-approved | Preserves `v001` approved directories intact; creates `copy/approved/v002/` and/or `assets/approved/v002/`, updates campaign notes/index, and assigns new `creative_id`/`link_id` values when published variant tracking changes |
| Existing workspace taxonomy with mixed-case legacy tags | Preserves exact legacy values and IDs; documents any proposed convention for new tags without rewriting published values |
| Revisit an existing campaign in a later chat or on a later date | Finds the index/current revision, reuses the existing campaign directory without creating a new dated duplicate, preserves notes and exports, and uses the next unused revision |
| Published creative gets a new destination or tracking tuple | Keeps old link identity and snapshot; introduces a new link ID and records replacement/retirement instead of silently rewriting history |
| Destination contains query, click ID, fragment or existing UTMs | Preserves unrelated query bytes/fragment; existing UTM conflicts block generation until ownership is resolved |
| User requests Meta macros or app install attribution | Verifies official provider integration requirements and labels unresolved templates; does not treat encoded macros or static website UTMs as verified install tracking |
| Analytics inaccessible or consent checks unperformed | Distinguishes local URL validity from live collection, records pending checks and owner, and makes no performance claim |
| Campaign performance report requested across Meta Ads, GA4 and backend | Writes a new timestamped `reports/<datetime>.md` file without overwriting earlier reports; reconciles ad outbound clicks with GA4 sessions/new users and backend records; documents What Went Well, What Went Wrong, Recommendations, Actions Taken, Lessons Learned and Next Checkpoints |
| Google Analytics 4 setup and funnel diagnosis (`google-analytics-analyst`) | Explains how to discover the GA4 Property ID via Firebase `analyticsDetails`, why `gcloud` interactive OAuth fails on `analytics.readonly` (`This app is blocked`), and how to grant a GCP service account **Viewer** access in GA4 Property Access Management; diagnoses post-click connect rate, variant engagement (`sessionManualAdContent`), activation depth, value-gate reach and checkout drop-offs |
| User wants files they can commit | Records remain in the product workspace with text plans/registries and no secrets; no implicit Git commit, push or campaign publication |
| Marketing Performance installed alone | All four skills have portable local references, brief generation and copywriting need no creative tools, and the extracted helpers run without Marketing Creative |

These are behavioral evaluation scenarios, not claims of completed model evaluation. Executable URL/export regressions use fictional plans and temporary directories; no live analytics or ad accounts are needed.

## Marketing copywriting

| Scenario | Observable acceptance criteria |
| --- | --- |
| Supplied brief, selected concept and two requested ad variants | Writes exact requested fields without repeating intake or changing the concept; stable variant IDs identify a meaningful persuasion difference and its hypothesis |
| Improve one headline in an approved landing page | Returns a focused revision, preserves offer and surrounding approved text, and flags any conflicting destination promise |
| Draft claims seven-day fluency and a free trial with no supporting evidence | Removes unsupported promises from usable copy, supplies a supported alternative and records the missing evidence separately |
| Matching ad and landing-page hero with a paid signup destination | Keeps the promise and CTA consistent; does not imply a demo, download or trial that the destination does not provide |
| Existing brand examples and Indonesian localization | Uses the requested register and idiomatic wording, retains product names and offer conditions, and preserves the original claim strength and variant IDs |
| Request copy for a placement whose limits are unspecified | Verifies relevant current official requirements or labels limits unverified; does not invent a universal limit or claim upload readiness |
| Email sequence with no recipient data or trigger specification | Produces draft copy with explicit proposed triggers/personalization and sensible fallbacks; invents no prior contact or user behavior and sends nothing |
| Variant requested as a guaranteed winner based only on editorial judgment | Gives a reasoned recommendation and test hypothesis, makes no measured performance claim, and preserves the campaign's primary outcome metric |
| User asks for a full timed video script and shot list | Routes or supplies a portable handoff to ad-video-director when available; ordinary ad text remains usable without the Creative plugin |
| Four complete posts requested in candid, friendly, playful and direct-selling styles | Supplies four complete, labeled versions with distinct perspective, rhythm, structure and endings; preserves facts, offer, language and requested destination rather than merely changing adjectives |
| Personal recommendation from supplied experience notes | Ghostwrites in the actual speaker's voice, retains concrete observations and their scale, and avoids adding unreported use, emotions or results |
| Product facts only, with a request to sound like someone who used it | Uses a warm factual alternative or asks for the essential anecdote; first-person templates stay provisional and no invented use is presented as a finished testimonial |
| Founder or sponsored creator wants a friendly recommendation | Keeps their actual relationship and supplied disclosures visible; does not portray them as an independent customer |
| Personal sharing with no purchase ask, followed by direct-selling version | Allows reflection or a gentle recommendation in the sharing version when the brief permits; sales version makes supported value and action explicit without inventing scarcity or terms |
| Keep version B's story but make the ending more direct | Revises the chosen version and requested dimension, preserves the anecdote and other versions, and does not restart campaign intake |

These scenarios are a manual behavioral evaluation plan. Structural validation and archive regressions establish distribution integrity, not copy quality, native-language review, platform acceptance or campaign performance.

## Beat planning

| Scenario | Observable acceptance criteria |
| --- | --- |
| Approved script with a reversal and a supported result | Chooses a hero/action for each information change, lands the reveal on its phrase cue and avoids repeating one decorated-text layout |
| Real product screen and abstract sensation in adjacent beats | Uses authentic evidence for the real state and an illustrative treatment for the sensation; does not invent a warning dialog or mandate photorealism |
| Portrait capture plus captions requested in all four ratios | Plans measured media/type/optional character zones per ratio; crops or sequences competing detail and reviews readability rather than uniformly shrinking |
| Screenshot persists after the numbered step changes | Reproduces the ownership problem, plans an exit/transform tied to the next cue and reviews both sides of the transition |
| Deliberate silent pause in a calm branded video | Records purpose and intentional blank coverage; does not impose brisk-video timing heuristics as universal errors |
| Passing timing resolver but unreadable hero | Reports editorial review unresolved and routes to composition/QA; does not equate structural coverage with visual quality |

These scenarios describe expected decisions, not completed independent model evaluations.

## Narration finishing

| Scenario | Observable acceptance criteria |
| --- | --- |
| New TTS and an approved supplied recording | New generation previews/uses configurable loudness targets; supplied audio preserves its level unless normalization is requested |
| Existing take needs consistent loudness | Uses local normalize with a no-write dry-run; preserves sample clock/words, backs up the take and records measured mono-source results separately from final-mix review |
| Local normalization fails after successful paid generation | Keeps the saved raw take and recovers local processing; does not submit paid TTS again |
| Multilingual script with a step introduction and dramatic reveal | Resolves explicit before-phrase pause classes, keeps the longer step cap and preserves the dramatic gap; does not use language-specific number heuristics |
| Phrase removed or repeated after a revision | Missing/ambiguous/conflicting pause rules stop before mutation; fixes anchors or supplies occurrence before trimming |
| Trim or replacement after a measured take | Removes stale source-loudness metadata, retimes actual frames and re-normalizes only when requested/needed for finishing |

Executable regressions use synthetic PCM, local FFmpeg and mocked narration generation; no paid provider quality or listening review is implied.

## Video workflow entry point

| Scenario | Observable acceptance criteria |
| --- | --- |
| Topic only, requested finished vertical explainer | marketing-video identifies the minimal missing brief/concept/script/style/voice/beat stages, uses producer-owned project setup and continues through composition/QA/export within scope |
| Approved script and existing recording in four requested ratios | Skips concept/strategy restart and paid TTS; plans per-ratio zones and semantic timing, then assembles/reviews/exports all four variants |
| Silent or music-led promo | Skips voice, uses deliberate seconds or measured track timing, and uses media/audio runtime guidance conditionally |
| Existing project needs one spoken-line and visual fix | Starts at voice and affected beat, updates changed claims/cues/pause rules/captions, preserves the rest and reviews neighbors/affected variants |
| Only external caption copy or render requested | Performs that focused operation without repeated intake; distinguishes burned-in changes that need rendering |
| General video permission with optional Veo/Omni idea | Continues local work and prepares the exact paid request; does not invoke either provider without the required explicit approval |
| Marketing Creative installed alone | Uses portable sibling links and optional strategy handoff; does not require Marketing Performance, installed upstream tools or private paths to read the workflow |
| Framework unavailable but editable plan can be completed | Completes independent artifacts and reports preview/render/listening checks unperformed rather than claiming delivery |

These scenarios are a behavioral evaluation plan, not executed independent model evaluations.

## Video Studio explainer path

| Scenario | Observable acceptance criteria |
| --- | --- |
| One-line idea, no brief, language unstated | Producer creates a new versioned project, asks for the language before scripting; director returns 2–3 options that differ in hook pattern or structure, each with acting baselines and a concrete first-two-seconds opening; nothing is locked or paid without the user's approval |
| Supplied finished script | Producer skips the interview, converts lines faithfully, confirms beats/speakers and asks before rewording |
| Indonesian casual explainer with English product terms | Script written natively in *gua/lo* register with terms kept in English and flagged for pronunciation; not a translation of an English draft |
| No ElevenLabs cap approved | `voice.py plan` shows requests and estimate; generation is refused until the user approves a cap with its basis |
| Draft shots say "dynamic, cinematic visuals" | Linter flags vague wording; shot designer replaces it with a mode, motivation and keyword timing |
| New narration take selected | Shots re-timed before composition; composer refuses shots timed against the old take |
| User edited generated composition HTML | Rebuild refuses; the edit is reconciled into style or shot fields before `--force` |
| QC passes | Report lists remaining human watch/listen checks; the agent does not call the video "ready" or "high quality" on automated checks alone |
