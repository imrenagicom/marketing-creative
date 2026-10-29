# Images for a marketing campaign

Every board and final image is a creative for a marketing campaign: an image ad, a carousel slide, a social post, or a still for a campaign video. The campaign workspace belongs to `campaign-manager` (marketing-performance plugin). These skills read it, work inside it and file approved images back into it. They never publish, never change ad accounts, and never edit `campaign.json`, `ad.json` or `post.json`.

## Find the campaign first

Look for the campaign directory before planning: the one the user names, or `marketing/campaigns/<YYYY-MM-DD>-<campaign-name>/`, identified by its `README.md` and `campaign.json`. Find which ads or posts need images, for example `meta-ads/campaigns/<c>/adsets/<s>/ads/<ad>/` or `instagram/posts/<post>/`.

- **Campaign exists:** take the brief, audience, offer, approved claims and evidence from `docs/MARKETING_BRIEF.md`. Take ideas from `docs/plans/CREATIVE_IDEAS.md`. Take format, CTA, approved copy and required ratios from each deliverable's `ad.json` or `post.json` and its `copy/approved/vNNN/`. Use product, logo and talent images from the campaign as references.
- **No campaign yet:** offer to set one up with `$campaign-manager`. If the user wants the images alone, use a separate work directory and say the images are not filed to a campaign.

## Where the work lives

| What | Where |
| --- | --- |
| Image plan | `<ad-or-post>/assets/development/images/image-plan.json`. Never name it `campaign.json`: that file is campaign-manager's link plan at the campaign root |
| Boards and cropped tiles | `<ad-or-post>/assets/development/images/board-vN/`, `tiles-vN/` |
| Final runs (single or batch) | `<ad-or-post>/assets/development/images/final-<id>-vN/` or `finals-vN/` |
| Approved deliverables | `<ad-or-post>/assets/approved/vNNN/images/` plus `assets.json` |

When one board explores options for several ads or posts, keep it with the first deliverable. The others reference its path rather than generating a second board.

## Hand off approved images

After the user approves the finals, copy the chosen files from the run directory into the next unused `<ad-or-post>/assets/approved/vNNN/images/`, never over an earlier revision. Write `assets.json` there with:

- the `campaign_id` and creative ID
- each file with its slide order, ratio, actual dimensions and sha256
- the source run directory with its model and request hash
- the selected concept IDs
- the review notes, and who approved it and when

Then:

1. Write alt text for each image (one per slide for carousels) with `$marketing-copywriter`, in the deliverable's `copy/drafts/`, then promote it to `copy/approved/vNNN/`.
2. Ask `$campaign-manager` to point `approved_assets_revision` at the new revision and keep `creative_id` and `utm_content` aligned with it.
3. For another ad or post that uses the same image, copy it from the approved revision and record the source path and hash. Never regenerate it.

For a campaign video, keep the reviewed still in the ad's approved images. The video's continuity bible or keyframes can then use it as a reference (`$studio-producer`, video-studio plugin).

Filing an image is not publishing, and a successful generation is not proof that the image works as an ad. Measure performance with campaign-manager's reports.
