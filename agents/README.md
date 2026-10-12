# Agents — "חתול בהמתנה"

Five cloud scheduled tasks (no computer needed, auto-approve). IDs and schedules: `agents/full/meta.json`.
The live prompt of each task is the file listed there under `agents/full/`.

| Agent | When (Israel) | Prompt | What it does |
|---|---|---|---|
| production | daily 09:53 | `production_v2.md` | Builds the next episode, prediction gate (§J), pushes the clean mp4 + stories, sets the episode to `review` |
| sync | daily 18:52 | `sync_v2.md` | Moves `approved` episodes into `queue.json` (Make publishes IG/FB/YT at 20:30) and schedules TikTok via Metricool |
| data | daily 21:12 | `data_v3.md` | Metricool → `metrics/*`, `history/*`, `accounts/*`; runs `tools/analyze.py` → `analysis/*`; judges experiments; `insights/latest` |
| ops | daily 21:47 | `ops_v1.md` | Checks every agent ran, today's publish, the next 3 days are approved and queued, data is fresh; one safe retry; writes `audit/*`; messages Gabi only when he must act |
| weekly | Saturday 18:57 | `weekly_v3.md` | Topic research (Grok X scan + news) → `ideas/*`, weekly analysis (`analysis/summary.last_7d`, audience), decisions, experiments, bible update, weekly audit |

## Rules for changing an agent
1. Edit or add `agents/full/<agent>_vN.md` (full text, not an addendum).
2. `update_trigger` with the full text. Never delete and recreate a task (it loses its history).
3. Update `meta.json`, `PROJECT_CONTEXT.md` and the project docs `agents/*.md`.

## Numbers
Agents never estimate numbers. Raw values come from Metricool / the Drive sheet with `source` + `measured_at`; everything derived (rates per 1,000, vs-median, 1d/3d/7d checkpoints, 7-day window, §G diagnosis, data gaps) comes from `tools/analyze.py`.

Older files (`*_addendum.md`, `APPLY.md`, `PASTE_FULL.md`, `*_current.md`) are history from when the tasks were bound to Gabi's computer.
