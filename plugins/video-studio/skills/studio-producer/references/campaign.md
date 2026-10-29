# Videos for a marketing campaign

Every Video Studio video is a creative for a marketing campaign: an explainer, an ad or a story-led film that serves one or more of the campaign's ads or posts. The campaign workspace belongs to `campaign-manager` (marketing-performance plugin). Video Studio reads it, works inside it and files approved videos back into it. It never publishes, never changes ad accounts, and never edits `campaign.json`, `ad.json` or `post.json`.

## Find the campaign first

Before `studio.py init`, look for the campaign directory: the one the user names, or `marketing/campaigns/<YYYY-MM-DD>-<campaign-name>/` in the workspace, identified by its `README.md` and `campaign.json`. Find which ads or posts the video is for, for example `meta-ads/campaigns/<c>/adsets/<s>/ads/<ad>/` or `instagram/posts/<post>/`.

- **Campaign exists:** read `docs/MARKETING_BRIEF.md`, `docs/plans/` (`CREATIVE_IDEAS.md`, `CROSS_PLATFORM.md`) and each deliverable's `ad.json` or `post.json`. They give the objective, audience, offer, approved claims and evidence, CTA, destination and required ratios. Each ad set's `placements.required_ratios` decides the project's `--formats`.
- **No campaign yet:** offer to set one up with `$campaign-manager`. If the user wants the video alone, continue without one and say the video is not filed to a campaign. Do not invent a brief: ask for the facts the direction depends on.

Do not repeat intake for anything the brief already settles.

## Where the project lives

Create the project inside the main deliverable's development folder, as a versioned run directory:

```text
<campaign>/<ad-or-post>/assets/development/video/<YYYY-MM-DD>-<video-slug>/
```

Then link it:

```sh
python3 <studio-producer>/scripts/studio.py init <project> --title "…" --formats 9x16,4x5 [--language en|id]
python3 <studio-producer>/scripts/campaign.py link <project> --campaign <campaign-dir> \
  --deliverable meta-ads/campaigns/launch/adsets/broad/ads/demo-video [--deliverable instagram/posts/launch-reel]
```

`project.json` then records `campaign {dir, id, deliverables[]}`: the campaign directory relative to the project, its `campaign_id`, and the ads and posts this video serves. `studio.py status` reports the link and whether the brief was found.

## What the campaign changes in each stage

| Stage | Campaign input |
| --- | --- |
| director | Objective, audience tension, offer and CTA shape the hook and the options. The CTA and the destination's promise end the video. |
| scriptwriter | Only claims the brief supports, in its approved wording. Prices, offers and testimonials are checked, never invented. |
| shot-designer, motion-designer | Every canvas a placement requires, each composed for that placement. Captions and CTAs stay inside its safe area. |
| continuity-bible, keyframe-generator | Real product, brand and talent references from the campaign's assets come before generated stand-ins. |
| editor, qc-reviewer | Deliveries per required ratio, with loudness and captions suited to sound-off feeds. |

## Hand off the approved video

After final QC passes and the user has approved the render, file it:

```sh
python3 <studio-producer>/scripts/campaign.py handoff <project> --deliverable <ad-or-post> --note "User approved v3 in chat"
```

This copies the finished deliveries into the next unused `<ad-or-post>/assets/approved/vNNN/video/`. Earlier revisions are never overwritten. Alongside them it writes `assets.json` with the `campaign_id`, creative ID, render version, file hashes, the QC report's hash, the checks people still have to do, and the approval note. It refuses a render whose QC failed, a deliverable the project wasn't linked to, or a missing approval note.

Then:

1. Write alt text and a thumbnail description for the video with `$marketing-copywriter`, in the deliverable's `copy/drafts/`, then promote it to `copy/approved/vNNN/`.
2. Ask `$campaign-manager` to point the deliverable's `approved_assets_revision` at the new revision and update its tracking (`creative_id`, `utm_content`).
3. For another ad or post using the same video, run `handoff` for that deliverable as well, or copy it the way campaign-manager describes. Never regenerate a video to reuse it.

Handing off is not publishing, and a QC pass doesn't measure ad performance. Measure performance afterwards with campaign-manager's reports.
