# hatul-media

Finished episodes of "חתול בהמתנה" (@hatul.bahamtana), hosted here so publishing tools can fetch them by URL.

- `episodes/` — final watermarked MP4s (1080x1920, 30 fps, H.264 ≤4.5 Mbps, AAC 128k/48 kHz, faststart)
- `queue.json` — the publishing queue read by the Make scenario "חתול בהמתנה — פרסום"

## Publishing queue

The Make scenario runs Sun / Tue / Thu at 20:30 Israel time. It reads
`https://raw.githubusercontent.com/PrimeAiSaaS/hatul-media/main/queue.json`
and publishes every item whose `publish_on` is today and `approved` is true,
to Instagram Reels, the Facebook page (Reel) and YouTube (Shorts).

Only add an item after Gabi has approved the episode.

```json
{
  "items": [
    {
      "episode": 3,
      "publish_on": "2026-10-11",
      "approved": true,
      "video_url": "https://cdn.jsdelivr.net/gh/PrimeAiSaaS/hatul-media@<commit>/episodes/ep3_branch_wm.mp4",
      "caption": "post caption for Instagram + Facebook, with hashtags",
      "yt_title": "YouTube title (max 100 chars, no < or >) #shorts",
      "yt_description": "YouTube description"
    }
  ]
}
```

Rules
- `video_url` must be a jsDelivr URL pinned to a commit (`@<commit>`), never `@main` (cached) and never raw.githubusercontent.com (wrong content-type for Instagram).
- After the scenario has posted an item, remove it from `items` (or set `approved` to false) so it is never posted twice.
