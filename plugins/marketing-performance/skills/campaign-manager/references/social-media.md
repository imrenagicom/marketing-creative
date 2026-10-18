# Social media campaign structure (`instagram`, `linkedin`, `twitter`)

Under `<YYYY-MM-DD>-<campaign-name>/`, place organic or channel-specific social media campaign folders at the same top level as `meta-ads/`:

- `instagram/`
- `linkedin/`
- `twitter/`

Each social media platform folder organizes individual posts, reels, stories, carousels, articles, or threads under `posts/<post-slug>/`. Every `<post-slug>/` directory owns its post metadata (`post.json`), copy/caption drafts and approved revisions (`copy/`), and creative asset development and approved revisions (`assets/`):

```text
<YYYY-MM-DD>-<campaign-name>/
  campaign.json                          # canonical campaign-wide link plan
  tracking/
    v001/
      campaign.json
      utm-links.csv
      UTM_PLAN.md
  meta-ads/                              # paid Meta Ads hierarchy (campaigns -> adsets -> ads)
    ...
  instagram/
    README.md                            # optional channel notes, handle, bio-link or grid strategy
    posts/
      <post-slug>/
        post.json                        # format, status, schedule, optional link/UTM mapping, active revisions
        copy/
          drafts/                        # working captions, hooks, reel/story text, hashtags, alt text
          approved/
            v001/                        # approved caption, overlay copy, hashtags, and CTA notes
            v002/
        assets/
          development/
            storyboard/                  # concepts, reel/carousel scripts, visual direction, beat sheets
            images/                      # references, contact sheets, cropped tiles, slide renders
            video/                       # reel/story video projects, Veo/Omni runs, draft renders/QA
            audio/                       # voiceover takes, alignment, music/SFX
          approved/
            v001/                        # approved deliverable revision ready to publish
              MANIFEST.md                # or assets.json: creative_id, ratios, slide order, file hashes
              images/                    # approved feed/carousel/story image deliverables (1:1, 4:5, 9:16)
              video/                     # approved reel/story/feed video deliverables
              audio/                     # approved standalone audio when needed
            v002/
  linkedin/
    README.md                            # optional company page / personal profile strategy notes
    posts/
      <post-slug>/
        post.json
        copy/
          drafts/                        # working post copy, opening hook, document/slide copy, first comment
          approved/
            v001/
        assets/
          development/
            storyboard/
            images/
            video/
            audio/
          approved/
            v001/
              MANIFEST.md
              images/
              video/
              audio/
  twitter/
    README.md                            # optional X/Twitter handle and thread/cadence notes
    posts/
      <post-slug>/
        post.json
        copy/
          drafts/                        # working single-post drafts, thread tweets, reply CTA, alt text
          approved/
            v001/
        assets/
          development/
            storyboard/
            images/
            video/
            audio/
          approved/
            v001/
              MANIFEST.md
              images/
              video/
              audio/
```

Create only the social platform directories (`instagram/`, `linkedin/`, `twitter/`) and `<post-slug>/` folders that the campaign actually uses or that the user asks to scaffold.

## Social post specification (`<platform>/posts/<post-slug>/post.json`)

Each social post directory includes a `post.json` file that binds the post's format, schedule, and optional tracked link (`link_id` in root `campaign.json`) to its active approved copy/caption revision (`copy/approved/vNNN`) and approved creative asset revision (`assets/approved/vNNN`):

```json
{
  "schema_version": 1,
  "platform": "linkedin",
  "post_slug": "founder-workflow-breakdown",
  "name": "Founder Workflow Breakdown | Carousel + Demo Link",
  "status": "planned",
  "format": "carousel",
  "link_id": "linkedin-founder-workflow-v1",
  "destination_url": "https://example.com/start?lang=id#demo",
  "utm": {
    "utm_source": "linkedin",
    "utm_medium": "organic_social",
    "utm_campaign": "taskapp-activation-id-2026q4",
    "utm_id": "2026-10-18-example-taskapp-activation",
    "utm_content": "founder-workflow-carousel"
  },
  "url": "https://example.com/start?lang=id&utm_source=linkedin&utm_medium=organic_social&utm_campaign=taskapp-activation-id-2026q4&utm_id=2026-10-18-example-taskapp-activation&utm_content=founder-workflow-carousel#demo",
  "approved_copy_revision": "copy/approved/v001",
  "approved_assets_revision": "assets/approved/v001",
  "schedule": {
    "publish_at": "2026-10-20T09:00:00+07:00",
    "timezone": "Asia/Jakarta"
  }
}
```

- `platform`: `"instagram"`, `"linkedin"`, or `"twitter"`, matching the top-level platform folder name.
- `post_slug`: lowercase hyphenated slug matching the `<post-slug>` folder name.
- `format`: `"single_image"`, `"carousel"`, `"video"`, `"reel"`, `"story"`, `"text"`, `"thread"`, `"document"`, or `"article"`.
- `status`: `"planned"`, `"paused"`, `"active"`, `"published"`, `"archived"`, or `"retired"`.
- **Tracked links (`link_id`, `destination_url`, `utm`, `url`):**
  - When the post includes an outbound campaign link (in the post body, first comment, thread reply, story link sticker, or bio link), add a link entry in root `campaign.json` with `"platform": "<platform>"` and `"post": "<post-slug>"`, and set `link_id`, `destination_url`, `utm`, and optional `url` in `post.json` to match.
  - When a social post has no outbound link (pure in-feed engagement or brand content), omit `link_id`, `destination_url`, `utm`, and `url`.
- `approved_copy_revision` and `approved_assets_revision`: point to the active `vNNN` directories inside this post's `copy/approved/` and `assets/approved/` trees. For text-only posts (`format: "text"` or `"thread"` without media), `approved_assets_revision` may be omitted.
- **Cross-platform asset reuse:** When the same approved visual deliverable is published across multiple social platforms (for example, an image or vertical video shared on `instagram`, `linkedin`, and `twitter`), each platform's `<post-slug>/` keeps its own platform-tailored `copy/approved/vNNN/` (caption, character limits, hashtags, thread structure) and may either store platform-specific exports in its own `assets/approved/vNNN/` or reference the sibling post's `assets/approved/vNNN` path in `post.json`.
- Optional `schedule` (`publish_at`, `timezone`), `account_handle`, `remote_post_id`, and `notes`.

## Copy/caption and asset conventions per social platform

- **Instagram (`instagram/posts/<post-slug>/`):**
  - `copy/`: feed/reel caption (opening hook line before truncation, body, CTA, hashtag block), on-screen/overlay text per slide or beat, story sticker/link text, and accessibility alt text.
  - `assets/`: `4:5` or `1:1` single images and ordered carousel slides (`slide-01.png`, `slide-02.png`, ...), `9:16` Reels and Stories video/images, and cover/thumbnail frames.
- **LinkedIn (`linkedin/posts/<post-slug>/`):**
  - `copy/`: opening lines before the "see more" fold, full post body, slide/document headlines when using a PDF/carousel post, first-comment link copy when links are placed in comments, and alt text.
  - `assets/`: `1:1`, `4:5`, or `16:9` images/videos, multi-slide carousel/document exports, and thumbnail frames.
- **Twitter / X (`twitter/posts/<post-slug>/`):**
  - `copy/`: single post copy (within current character limits) or numbered thread posts (`01/ ...`, `02/ ...`), follow-up reply with the tracked link when keeping links out of the root post, and image/video alt text.
  - `assets/`: `16:9`, `1:1`, or `9:16` images, multi-image sets (up to four images per post), and video/GIF clips.
