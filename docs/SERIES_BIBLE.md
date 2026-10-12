# חתול בהמתנה — Series Bible & Production Runbook

This file is the single source of truth for producing new episodes. A production agent reads it first.

## The show
- Channel: "חתול בהמתנה" — handle @hatul.bahamtana on TikTok, Instagram, YouTube (Facebook page pending).
- Owner: Gabi. Every episode goes to Gabi for approval before anything is published. Never publish yourself.
- Format: 10–12 s vertical (1080x1920, 30 fps), Hebrew captions, no voice-over. Text lives in speech bubbles and captions. (Was 13–18 s; shortened after ep1 data, see Growth playbook.)
- Tone: deadpan Israeli bureaucracy comedy. The cat always loses, in an escalating, specific, recognisable way.
- Season 1 arc (Gabi, 2026-10-07): from episode 3 the cat slowly gives in. Sharit, the clerk at window 3, plants the idea ("תירגע, חמוד" + something rolled); in episode 4 he breaks and comes back completely chill. From then on bureaucracy can't hurt him because he no longer cares. Keep it funny and gradual.

## Characters
- The cat (unnamed): orange tabby, cobweb on the left ear. Pre-ep4: tense, hopeful, loses. Chill mode (from ep4 cold open / ep4 7.6 s on): `lid≈0.56, red=1.0, mouth='goofy'` (or `'munch'` while eating), slow head sway to the beat, snack bag in the left paw, lazy one-paw taps, slooow blinks, says "וואלה." / "סבבה.".
- שרית (Sharit) — clerk at window 3 of "הבנק שלי" (sharit.py). Invented character, not based on anyone real. Big dark curls, gold hoops, blue bank blouse with name tag "שרית", heavy purple eyelids, permanently red eyes, lazy half smile, one-finger typing, always munching from an orange snack bag. Catchphrases: "שנייה, מותק." · "אוי… איזה חמוד אתה." · "תירגע, חמוד". Goes "on a 5-minute break" and returns in a little cloud.

## Voices (approved by Gabi 10.10 — for voiced/long-form videos; Shorts stay caption-only unless Gabi asks)
- Engine: Higgsfield `generate_audio`, model `text2speech_v2`, variant `elevenlabs`, voice_type `preset`. Hebrew works natively. Cost ≈ 0.3 credits per line (~45 credits for a 10-min script). Credits ALWAYS need Gabi's approval per batch (preflight with get_cost first).
- The cat: Benji — voice_id e6f9b893-51b1-51d3-afe9-9e0482cb7ac1 (Gabi: "כן ככה" — use as is, no pitch change).
- Sharit: Delia — voice_id 1550321e-7f5b-526e-b001-02328b03e9bc.
- Chill-cat mode (Gabi 10.10): after the cat's off-screen "chill" moment, his voice switches to a slow, lazy, stretched, cat-like funny voice (same Benji character, slower and lower, drawn-out vowels, lazy "מיאוווו", long pauses). Style reference from Gabi: the lazy, wise, smoky drawl of the hookah caterpillar type — very slow, low, a little raspy, every word weighed, sentences that trail off into "ממממ...". Take the style only, never imitate a specific actor's voice. The switch itself IS the hint: smoking is never shown, heard or named, and the dialogue never uses ג'וינט/גראס/וויד/סטלן. Settled 10.10 (Gabi: "זה כבר יותר טוב"): Benji on text2speech_v2/elevenlabs with NO speed or pitch change; the lazy feel is written into the text — "וואלה...", ellipses, a "חחח...", losing the thread ("רגע, איפה הייתי?"), drifting to a random thought ("אילת... יש שם ים...").
- Rejected: model seed_audio (even when cloning Benji) — it does not speak real Hebrew (Gabi 10.10: "שידבר עברית"). Hebrew lines ONLY via text2speech_v2 / elevenlabs. The chill mood comes from the text (natural pace, a giggle, losing the thread: "רגע, איפה הייתי?"), not from slowing the audio down — slowed audio was "too much" (Gabi).
- Voiced videos, Gabi's notes on sp1 v1 (10.10: "תוריד את המוזיקה, פחות משעמם, יותר קולע, ובשנייה הראשונה משהו שיתפוס"): NO music bed in voiced videos (SFX and stings only, a very low room tone is fine); pauses inside lines ≤0.18 s (Sharit's "שנייה, מותק..." and chill lines ≤0.35 s), gaps between lines ≈0.1 s; open with a cold open of the loudest/funniest line (sp1: "סבתא שלי גרה באילת!!" + impact + dun-dun) then a ◀◀ rewind "2 דקות קודם"; snap-zoom on every cut; end with a whip so the loop lands back on the cold open.
- Rejected: code-synthesised "cat language" babble (Gabi: "גרוע"). Never use it.
- Audio bridge (works, 10.10): the cloud workspace cannot reach Higgsfield result URLs (cloudfront blocked), and neither can the device shell. Route: in Gabi's built-in browser pane (any open tab), javascript fetch() each result_url → blob → <a download> click; the files land in Gabi's ~/Downloads as *.tmp (the pane does not finalize names), so match them by byte size, copy them with the device shell to ~/Videos/hatul_voices/lineNN.mp3, then device_stage_files into the workspace. Gabi approved this download route for voiced videos (10.10). Needs the device linked; leave the .tmp files (deleting needs Gabi's permission).
- Voiced pipeline (sp1.py is the template): voice/sp1_prep.py decodes the lines, tightens pauses (normal ≤0.3 s, Sharit's "שנייה, מותק..." and chill lines ≤0.5 s), saves a 30 fps talk envelope; the episode builds its timeline from the real line lengths, flaps the mouths from the envelope, shows subtitles (cat white, Sharit pink, y≈1450) because most viewers watch muted, and ducks the music under the voices.

## Reaction pack (built 11.10 from Gabi's 48 h bonus credits)
- 13 green-screen clips of the cat (Kling v3.0 std, 5 s, 9:16, 720x1280, 24 fps, silent, 7.5 credits each), all from the start frame repo assets/react/cat_green_neutral.png (Higgsfield media 1dc9214e-259c-4cc2-9511-944759ac71ac). Background is flat chroma green (0,177,64) → key it out with ffmpeg chromakey. Kling adds a few tabby stripes; acceptable for inserts. Clips often idle ~1–2 s before the action: trim to the action.
- Job ids (download the result_url through the browser-pane bridge): shock 1491e860-5875-4f01-919d-8775c85d860c · laugh d5e7acca-7a34-4ec3-aaa9-2828a6958e01 · facepalm 4c25ab63-87b0-4d14-890b-be42149daa3c · chill nod f32e5758-678d-4670-90e0-c755f47d920b · eye-roll 93cc94a3-aef2-4bd3-8621-f3da9664a092 · crying a8fd755c-e42d-4b92-85ae-fe96c620cd54 · furious/steam 310f407d-53c5-4e5b-970d-45a76105acbc · clapping 2bb415f6-8c69-4c75-afd6-646b558358fb · side-eye 395b5a71-81ee-4796-91a0-9f222ee86548 · thumbs-up 06a5b7c1-e538-4561-9c87-73fa9e8fb55e · jaw-drop 01c3784f-9ff7-4cc3-ac48-8de82c7a5be6 · impatient foot-tap dd0bdc78-1c04-46b9-8e1c-d212f4283271 · falls asleep waiting 015dd8bb-13ad-494e-866d-d8762ccc36ad.
- react1.py = the "החתול מגיב" template (11.10): download the pack into out/react/hatul_react_NN_<name>.mp4, then each beat = a phone notification card sliding in (ding + buzz) + one keyed clip window (start/length per clip, trimmed to the action; the shock action starts at 3.2 s), punch-in per beat, beat counter "N/8", per-reaction SFX (sting, ticks, snore, kettle whistle, sigh, slap, slide-whistle, wah-wah), no voice, no music, whip-out loop. Frame 1 must already show the card + the reaction.
- Uses: "החתול מגיב" reaction videos, cutaway gags inside voiced specials and the long YouTube video. Browser-pane downloads now finalize with their real file name in ~/Downloads (11.10).

## Kling-animated voiced episodes (sp2 template, 11.10 — Gabi: "תשתמש בקרדיטים, קולות ודמויות, שיהיה מושקע")
- Pipeline: sp2_frames.py renders caption-free start frames in our own style (ep1 desk world + router prop; Sharit at a call-center desk with a headset) → push to repo assets/<ep>/ → media_import_url via jsDelivr → Kling v3.0 **pro** image-to-video, 5 s, 9:16, sound off (8.75 credits/shot; std is 7.5) → download through the browser-pane bridge → sp2.py edits: per-shot segments (start/dur/speed), code-made phone UI shots, cold open + ◀◀ rewind, snap-zoom per cut, x64 overlays, subtitles colored by speaker, whip-out loop.
- Kling prompt prefix that worked: "Flat 2D vector cartoon animation in exactly the same art style as the start image… Static locked camera… do not add or change any text. The action starts in the first second; snappy, exaggerated cartoon acting." Kling adds a few tabby stripes to the cat; text signs survive. Retry submissions that return a preset recommendation with declined_preset_id.
- Extra voices: IVR = Vera (0c51919f-0756-5f8d-8169-026a339d8fd7, sped up atempo 1.25), call-center rep = Celine (57ccb351-84d7-54ba-afd4-26b566ca6023). Anything heard through the phone gets a telephone filter (bandpass 320–3200 Hz + soft clip).
- Budget reference: sp2 = 10 pro shots (87.5) + 16 voice lines (~2.5) ≈ 90 credits for 52 s.
- Dashboard limit: asset uploads max 20 MB → upload a 720p preview (~2.2 Mbps); the full file lives in the repo.

## Content rule — cannabis (hint level only)
Gabi chose hint-level (2026-10-07) because TikTok removes/limits drug depiction and Meta/YouTube cut reach. Allowed: a rolled paper inside a note, a white cloud/white-out, red half-closed eyes, goofy grin, munchies/snacks, lo-fi groove, smoke wisps drifting in from off-screen, "הפסקה של 5 דקות". Never: lighting, a lit tip, inhaling/exhaling on screen, bongs/pipes, the leaf symbol, or the words ג'וינט / גראס / וויד / סטלן in captions, titles or hashtags (on-screen jokes stay implicit).
- Posting days: Sun / Tue / Thu at 20:00 (TikTok) and 20:30 (Instagram), Israel time.

## Running gags (use at least 2 per episode)
1. The queue number only goes UP (486 → 487 → 488 ...). Next value: see Episode log.
2. The wilted plant — wilts a bit more every episode; revives only in the season finale.
3. Cobweb on the cat's left ear (strand to the nearest wall object).
4. Fast-forward x64 overlay (scanlines + "x64" badge) whenever time passes.
5. Rule of three: two failures, the third fails in a surprising way.
6. Closing caption "כל. פעם. מחדש." or a variation.
8. Sharit's "שנייה, מותק." + her snack bag (from ep3).
9. Chill-cat gags (from ep4): sloooow blink, head sways to the beat, crunch-munch, "וואלה." while everything around him collapses or succeeds.
7. Callback to the previous episode's last beat — but never as a calm opening shot; it must be in motion from frame 1 (see Growth playbook §A).

## Growth playbook (GABZI Factory constitution + IPC course, adapted to this series)
This section overrides older rules in this file when they conflict. It improves episode by episode: rules are born from field data, not theory.

### A. The first second decides everything
- Frame 1 is never a calm establishing shot. Open in motion, mid-conflict. Two proven-shape options:
  1. Cold open / flash-forward: 0.5–0.8 s of the episode's worst moment (the slam, the 487, the faceplant) with a caption like "...ואז זה קרה", then cut to the start.
  2. Start mid-action: the cat is already slamming the receiver / the shutter is already falling.
- First visual change (cut, snap zoom, sound hit) by 1.0 s; a new beat at least every 2 s.
- Hook caption visible from frame 1, top centre: the shared pain in the viewer's words, and it must contain the search keyword of the topic (ביטוח לאומי / הבנק / SMS / פקס / ארנונה). TikTok reads on-screen text in the first 3 s for search (OCR).
- Pain-first: the joke is the pain everyone knows. Name it in the hook; don't explain the setup.
- No intro, logo, title card or establishing beat in the first 2 s — the payoff/conflict is visible immediately. A visual contradiction works well (the board reads 17 while the cat holds 489; the stamp says אושר on a locked account). A sound hit lands in the first second. (Creator research 10.10: a cliff in the first 2 s of the retention curve = hook failure; fix = faster motion, payoff up front, no intro.)

### B. Length and loop
- Target 10–12 s. Cut any beat that doesn't escalate.
- Make the last frame flow back into the first (same framing/pose) so the loop invites a rewatch.
- No separate end card ("המשך יבוא", "פרק N: …" on a still frame): it is a dead frame that breaks the loop. A retention tail climbing past 100% is the loop signal the Shorts feed rewards. Put the next-episode teaser as a short text over the final action, in the caption, or in a pinned comment.

### C. Captions per platform (rewritten 12.10 — every platform gets its own text)
Every episode doc carries five text fields. The sync agent copies them into queue.json; Make maps caption → Instagram, caption_fb → Facebook (falls back to caption), yt_title/yt_description → YouTube. TikTok is uploaded by hand from caption_tiktok.
- caption (Instagram Reels): line 1 = the hook as a question, with the topic keyword (Instagram search reads captions) and max 1 emoji; 2–3 short lines; ONE CTA; then max 3 hashtags on the last line: #חתולבהמתנה + topic + 1 broad. Regular episodes use the comment-bot CTA "רוצים מספר בתור? הגיבו ״תור״ 👇" unless the episode's experiment is a CTA test (then the experiment's CTA).
- caption_fb (Facebook page): 6–10 short lines of storytelling (what happened, in order, with the punchline withheld), ends with a question CTA (the "תור" bot is Instagram-only, so never use the תור CTA here), 1 hashtag (#חתולבהמתנה), no links.
- yt_title: ≤ 60 chars, keyword first, "| חתול בהמתנה" (+ "פרק N" for numbered episodes), ends with #shorts, no < or >.
- yt_description: line 1 = one keyword sentence about what happens; line 2 = the question CTA; blank line; "חתול בהמתנה: פרק חדש כל יום ב-20:30."; blank line; exactly 3 hashtags: #shorts #חתולבהמתנה #<topic> (YouTube shows the first 3 above the title).
- caption_tiktok: 1–2 lines, the hook question with the keyword in the first words (TikTok search), + 3–5 hashtags.
- Never name a real person or a private company (the bank is "הבנק שלי"; "חברת האינטרנט שלי"); the cannabis rule applies to every field.

### D. Velocity engine (first 60 minutes)
- Every episode ships with velocity_replies: 3 ready human replies in different tones (warm / self-deprecating cat / teaser for next episode), for Gabi to use when the first comments arrive. Reply to every comment in the first hour; pin the funniest viewer comment.

### E. Comment mining
- Viewer comments are raw material: recurring complaints become future episodes and callbacks. Season 2 topic comes from comments. When Gabi forwards comments, log them in the episode note.

### F. Content mix
- Episodes are the "trendy/entertainment" pillar. Every ~5th post can be BTS ("איך סוכן AI מפיק את החתול") — only with Gabi's approval. No hard sell in this channel for now.

### G. One experiment per episode
- Each new episode follows all current rules and changes exactly ONE variable (e.g. cold open vs mid-action, 10 s vs 12 s, question caption vs statement). Write it in the episode doc as experiment: {variable, hypothesis}.
- The data agent compares the episode at 24 h against the baseline (median of earlier episodes on the same platform): avg watch % of length, completion %, shares, follows. Verdict: keep / drop / inconclusive (n < 100 views = inconclusive).
- Rules that win twice are promoted into "Proven rules" below, with the evidence.
- Measurement notes (weekly review 2026-10-10): YouTube's "stayed to watch" (ep1 84.6%) is the swipe-away rate, NOT avg watch % — never compare it with Instagram/TikTok avg watch. Facebook ep1 13.1% is 3-s views / views, also not avg watch. Instagram is the only platform with automatic avg watch time, so it is the default verdict platform; TikTok/Facebook count only when Gabi's 24 h screenshots exist.
- Update (2026-10-10 evening): YouTube Shorts is now the biggest distributor (ep2: 34 → 572 views in one day, ~46% of all season views). YouTube joins Instagram as a verdict platform when n ≥ 100. Use two YouTube metrics from YT Studio: opening = stayed_to_watch (ep2 baseline 17.8%; 82.2% swiped away), ending = avg view duration % (ep2 baseline 93.3% = 14 s of 15, likely includes loop rewatches). Opening experiments (cold_open, hook_question, opening_type) are judged first on TikTok avg watch % and YouTube stayed_to_watch.
- Queued experiments for season 2 (weekly review 2026-10-10; eps 3–5 keep the experiments already set):
  - ep6 `share_cta`: caption ends with a tag prompt ("תייגו את מי ש...") instead of the comment question. Hypothesis: shares > 0 (season so far: 0 shares on ~540 views, target ≥ 1 per 100).
  - ep7 `length_10s`: 10 s cut instead of 12 s, same structure. Hypothesis: higher avg watch % and completion (ep2 at 15 s: Instagram viewers stayed 9.6 s, TikTok 3.7 s).
  - ep8 `opening_type`: decided by ep4's cold_open verdict — if keep, test start-mid-action against it; if drop/inconclusive, repeat cold_open once more.

- Diagnosis order (research 10.10, fix only the FIRST failing step, one variable at a time): 1) shown in feed ≈ 0 → distribution/topic; 2) high swipe-away → hook (first 2 s); 3) viewers stay past 2 s but retention slides → pacing, cut dead frames, move the reveal earlier; 4) retention strong but views stall → topic ceiling, aim the same format at a bigger proven pain. We are at step 2 (YouTube ep2: 17.8% stayed, 93% avg view). So while YouTube stayed_to_watch < 50%, opening experiments take priority: if ep3/ep4 do not lift it, move `opening_type` ahead of `share_cta`.
- Varying the hook between episodes matters: platforms throttle repetitive openings. Never reuse the exact opening shot + caption pattern twice in a row.

### H. Working targets (update as data comes in)
- Avg watch ≥ 50% of length · completion ≥ 25% · ≥ 1 share per 100 views · follows > 0 per episode.
- Interim milestones (2026-10-10, week 1: TikTok 24.7% avg watch / ~7% completion; every episode-platform pair under 200 views): TikTok avg watch ≥ 35% and completion ≥ 12% by ep5 · YouTube stayed_to_watch ≥ 30% by ep5 (ep2: 17.8%) · ≥ 100 views per episode on at least 2 platforms so verdicts count (met by ep2 on 10.10: YouTube 572, TikTok 215). The main targets stay; still 0 shares and 0 follows on ~1,250 views.

- External reference ranges (creator-reported, not official; compare to our own baseline first): YouTube Shorts viewed-vs-swiped 70–79% = working, 80%+ = strong; avg % viewed for Shorts under 35 s 80–90% = working, 90%+ (looping past 100%) = strong. Ours (ep2): 17.8% stayed / 93% viewed → the content holds, the first second doesn't.

### I. Proven rules (field evidence)
- 2026-10-06 · ep1 TikTok (63 views at first read; 149 views by 7.10): 2 s static opening → avg watch 3.2 s of 13 s (24.6%), completion 6.45%, 0 shares, 0 follows. → Rule: no static opening (§A).
- 2026-10-09 · ep2 TikTok (54 views, replication of the static opening): avg watch 3.7 s of 15 s (24.7%), completion 7.69%, most viewers gone at 0:01. Same result twice → "no static opening" confirmed (n < 100 on ep2, so it is a replication, not a new verdict). ep3 was rebuilt (v2) with an in-motion opening.
- 2026-10-10 (evening update) · the two static openings now both pass n ≥ 100 on TikTok: ep1 159 views / 24.6%, ep2 215 views / 24.7%, completion 6.45% / 7.69%. YouTube ep2 (572 views): 82.2% swiped away in the opening. "No static opening" stands as a proven rule on two counted samples.

### L. Cadence: one post every day (since 12.10, Gabi)
- One post a day at 20:30 on Instagram, Facebook and YouTube (Make scenario 7801107 runs daily), TikTok by hand from the drafts.
- The production agent runs every day at 09:53 and builds one episode per run; publish_on = the first free day in the calendar that is at least 2 days ahead (time for Gabi's approval). Specials and reaction videos fill gaps.
- Week of 13–18.10: Tue 13 ep4 · Wed 14 מגיב 1 · Thu 15 ep5 · Fri 16 מיוחד 1 · Sat 17 מיוחד 2 · Sun 18 ep6 · from Mon 19 season 2 daily (ep7 → 19.10, ep8 → 20.10, ep9 → 21.10). ep10 (יום הבחירות) stays on Tue 27.10, election day; 22–26.10 are filled by new episodes the production agent writes (approved ideas first).
- The weekly agent proposes 5 ideas a week (not 2) so the daily pipeline never runs dry.
- YouTube long-form (since 12.10): once a week a 16:9 compilation of the week's posts (blurred sides, a red title card per episode, chapters in the description) goes to YouTube as a regular video. First one: long/hatul_season1_full.mp4 (season 1 + 3 specials, 3:12), upload after 17.10. Gabi uploads it in YouTube Studio (title, description and chapters in long/<name>.txt).
- Profiles (12.10): YouTube channel description + links (Instagram, TikTok, Facebook) and the Facebook page bio + links (Instagram, YouTube, TikTok) are set. Instagram links, the Instagram bio and the TikTok bio are edited by Gabi in the apps.

### M. Stories (since 12.10)
- Every post gets a story kit: `python3 tools/story_kit.py <clean mp4> stories/<key> "<question>"` in the hatul-media repo → story_teaser.mp4 (first 8 s inside the story safe zone, tag "פרק חדש עולה היום בערב") + story_poll.png (question on top, empty middle for a poll sticker). Commit it with the episode.
- Story publishing is manual: Make and the Instagram/Facebook APIs used here cannot post stories, and poll/link stickers can only be added in the app. Gabi posts (or schedules in Meta Business Suite → Planner, which schedules to Instagram and Facebook stories together): the teaser at ~18:00, the poll frame with a poll sticker after the post, and a one-tap "share reel to story" right after 20:30.
- Copies for Gabi land on his computer in Videos\hatul_stories\<date> - <label>\.

### J. Prediction gate (Higgsfield Virality Predictor, since 12.10) — production, data and weekly agents follow this
- What it is: `virality_predictor` (Higgsfield MCP, action create, params {"model":"virality_predictor","medias":[{"role":"video","id":<media_id>}]}). No credits are charged. It returns a dashboard HTML; the numbers are in its `"scores":{overall_score, brain_engagement, hook_score (0–3 s), viral_potential, sustain, peak_second}` JSON and the per-second attention curve `"global_scores_by_frame":[...]`. The result_url comes from `jobs_wait` (the HTML is ~6 MB). The cloud shell cannot reach it; extract the numbers in the Higgsfield sandbox (`sandbox_exec`, it has internet):
  `curl -sf --max-time 60 "<result_url>" -o vx.html && python3 -c "import re,json;t=open('vx.html').read();s=re.search(r'\"scores\"\s*:\s*(\{[^}]*\})',t).group(1);c=re.search(r'\"global_scores_by_frame\"\s*:\s*(\[[^\]]*\])',t).group(1);print(json.dumps({'scores':json.loads(s),'curve':[round(x,4) for x in json.loads(c)]}))"`
- Limits found 12.10: video ≤ ~13 s works reliably (12–13 s files passed; every 15 s file failed, even re-encoded); max 2 jobs at once; a job can sit in progress 10+ minutes. For long videos analyse a 12 s cut of the opening (analysis/<key>_first12.mp4 in the repo, 720p).
- It does NOT understand Hebrew speech (its captions track showed "Thanks for watching!" over ep1). Treat it as a visual-attention model: it judges motion, faces, cuts and contrast, not the joke.
- Baseline (cartoon episodes, 12.10): overall 42–47, hook 24–33, sustain 92–100, peak at the last second (the loop) on ep4/5/6, at 6 s on ep1. The model scores every episode's first 3 s as the weakest part, which matches the field data (YouTube ep2: 82.2% swiped away; TikTok: most viewers gone at 0:01).
- Gate for the production agent (step "before review"): run the predictor on the clean render. If hook_score < 30, try ONE fix that §A already allows (stronger motion or a bigger visual contradiction in 0–1 s, a sound hit at 0.0–0.3 s, a bigger hook caption), re-render, re-run, and keep the better version. Never ship a version only because it scored higher if it breaks a series rule. Write predictions/ep<N> to the dashboard (schema below) and say both scores in the message to Gabi.
- Calibration: the predictor is a hypothesis, not a verdict. Field data decides. The data agent fills predictions/ep<N>.actual at 24 h; the weekly agent compares and rewrites meta/prediction_calibration {updated_at, summary, rules[]}. Promote a prediction rule into §I only after it agrees with field data on ≥ 3 episodes with n ≥ 100.
- Schema predictions/<key>: {key, kind: "episode"|"reference", n (episodes only), label, file, media_id, job_id, analyzed_at, duration, scores{overall_score, brain_engagement, hook_score, viral_potential, sustain, peak_second}, curve[], note, actual?{measured_at, by_platform{instagram/tiktok/youtube: {views, retention, stayed_to_watch?}}}}.

### K. Control & logging (EVERY agent, EVERY run — since 12.10; binding even if your task prompt does not mention it yet)
- Each scheduled agent ends EVERY run (also when something failed or there was nothing to do) with two dashboard writes:
  1. `set` runs/<YYYYMMDD-HHMM>-<agent> (Israel time) {task: <agent id>, name, at: ISO +03:00, status: "ok" | "warn" | "failed", summary: one Hebrew line, returned: {the counts it produced, e.g. metrics_written, docs_updated, items_queued, ideas_added}, checks: [{name, ok, note}]}.
  2. `update` tasks/<agent> (get first for if_version; `set` if missing) {name, when, lastRunAt, lastStatus, lastNote, nextRun, triggerId}.
- Agent ids: production, sync, data, weekly (scheduled tasks), publish (the Make scenario: the data agent writes its run from the sheet rows and publish_error rows), comments (the Make comment bot 7896202: the data agent records whether replies appeared).
- Checks are about the agent's own output, not about effort: e.g. the data agent checks "every posted episode has a metrics doc measured today or yesterday", "no metric value went down vs history" (views never fall), "retention ≤ 100 except YouTube loop"; the sync agent checks "every queue item's video_url returns a video"; the production agent checks "contact sheet reviewed", "file in repo", "prediction written".
- Numbers written to the dashboard always carry source and measured_at. Never invent a number; a missing value stays missing.
- Weekly audit (weekly agent): read tasks/* and runs/* of the last 7 days and write audit/latest {at, items: [{agent, ok, note}]}: ok = ran on schedule (no gap > 1.1 × cadence + 3 h), no unexplained "failed", checks passing, and spot-check one returned number per agent against its source (sheet row, repo file, platform page). Report failures to Gabi. Delete runs/* older than 30 days.
- The dashboard's home "הסוכנים" card and the stats "יומן ובקרת סוכנים" card read these docs; an agent with no run inside its cadence turns red ("באיחור").

## Visual rules
- Hook caption from frame 1, top centre (y≈250), white Rubik 900 with black stroke; contains the topic keyword (§A).
- Bottom CTA (yellow) at y≈1720: next episode name, e.g. "פרק 5: סוף עונה".
- Keep important things away from the bottom 20% and the right edge (platform UI).
- Real organisations may be named in captions as satire (ביטוח לאומי), but the bank is always the generic "הבנק שלי". No real logos, no real people.

## Engine (files in this bundle)
- make_video.py — episode 1 + the shared engine: cat head (draw_head), receiver, paws, plant, papers, desk set, captions (caption_layer), paste_center, vignette/scanlines, audio helpers (hold_music, phone_line, tone, add, filters). K=2 supersampling, coordinates in 1080x1920 units.
- ep2.py — phone close-up shots (render_screen), red lock screen, SMS banners, receiver pick-up.
- ep4.py (v2) — cold-open structure (story-time remap), drawer + flying retro props (floppy, walkman, Nokia, remote), fax machine sprite (tray, output page, LCD, verdict badge), steam from the ears, note close-up callback, full-screen cloud white-out transition, chill-cat state (snack bag, sway, music notes, lingering smoke), modem screech / boing / sad trombone / lo-fi groove (kick, rim, hats, bass, soft chords, vinyl crackle).
- sp1.py — voiced special #1 (תעודת זהות בלי תור): population-office lobby (ep3 lobby + plaque + "ללא תור!" paper on the ticket machine, board 0 → 490), ID-card prop (id_card), envelope close-up (address אילת + "350 ק״מ" sticky), clerk-POV cat poses (pleading with the card on the glass / conspiracy paw / paws-on-cheeks shock), Sharit exit + break sign + cloud white-out, chill duo, lip-flap from voice envelopes, subtitles, music ducking. voice/sp1_prep.py prepares the lines.
- ep6.py — season 2 opener: envelope flight + catch + rip (envelope_sprite, env_flight, speed_lines; loop = a second envelope flying into the frame-0 pose), voter-notice card close-up (notice_card, red circle, sticky "350 ק״מ"), chill cat on the phone in the ep1 desk world (hold bubble 13 → 490 under x64, three answers), plant starts wilting again.
- ep5.py — season finale: reuses ep3 lobby/office (import ep3 as E3), big ticket with number, rubber stamp + "אושר" imprint close-up with confetti, duo two-shot at window 3 (Sharit scaled 0.78 behind glass + cat at the counter, both sway to the groove), plant revive + bloom, phone SMS close-up (lock screen + notification card), loop end = frame 0 pose.
- ep3.py (v2) — lobby set (number board with LED glow, ticket machine, standing cat with feet), lobby fast-forward; Sharit's side of window 3 from the customer POV (office set: filing cabinet, "שירות עם חיוך" poster, monitor; glass + counter + slot; "בהפסקה" hanging sign; empty spinning chair); clerk-window POV of the cat; pink note close-up ("תירגע, חמוד" + rolled paper). The roller-shutter code is in git history (ep3_v1).
- sharit.py — Sharit (draw(st, frame) → 700x900 layer, head centre (350,300); st: lid, red, look, mouth lazy/talk/munch/grin, rot, blink, blush, hand_l/hand_r, finger, snack), snack_bag(), bubble(), smoke() (soft drifting puffs; draw smoke on its own layer — an ImageDraw rectangle on the same layer overwrites it).
- make_video.draw_head extras: st['red'] (0..1 bloodshot eyes), mouth 'goofy' and 'munch'.
- watermark.py — burns the handle pill into finished mp4s → *_wm.mp4.
- covers.py — cover per episode (badge "פרק N", title plate, series pill). Edit the EPISODES list.
- profile_pic.py, yt_banner.py — brand assets (done).
- fonts/Rubik[wght].ttf, fonts/Heebo[wght].ttf. In the artifact bundle they are published as engine/fonts/Rubik-wght.ttf and engine/fonts/Heebo-wght.ttf — rename them back to the bracket names after download (the code loads 'fonts/Rubik[wght].ttf').
- profile/profile_yellow.png (used by watermark.py as the icon).

Typical new episode = new file epN.py copied from the closest existing episode, new sets/props drawn with the same helpers, same CAPTIONS / camera / audio structure.

## Production checklist (per episode)
1. `python3 epN.py test t1 t2 ...` → look at out/epN_contact.png. Check: Hebrew reads right-to-left, nothing overlaps the captions, no stray shapes, gags visible.
2. Fix, re-test, then `python3 epN.py render`.
3. Loudness: `ffmpeg -i out/epN.mp4 -c:v copy -af loudnorm=I=-15:TP=-1.5:LRA=11 -c:a aac -b:a 192k ...` (target mean ≈ -19 dB).
4. Platform file = CLEAN (no handle pill): re-encode out/epN.mp4 with the watermark.py encoder settings but no overlay → episodes/epN_<slug>_clean.mp4, and point the dashboard doc's repo_file at it. Reason (11.10): Facebook's Reels insights for ep2 flagged "content quality: Reels with watermarks perform worse" (−), so Meta treats our own handle pill as a watermark. `watermark.py` (→ _wm.mp4) is kept only for files Gabi shares by hand outside our own accounts.
4a. Prediction gate (§J): push the clean file, import it to Higgsfield from jsDelivr, run virality_predictor, write predictions/ep<N>. hook_score < 30 → one §A fix, re-render, re-run, keep the better one.
5. Add the episode to covers.py EPISODES (a frame time with no caption on screen) → out/covers/cover_epN.png.
6. Send Gabi: the _wm.mp4, the cover, and the ready-to-paste post caption (1 question line + 3–5 Hebrew hashtags) + the YouTube title.
7. Update the Episode log below and republish the bundle.

## Publishing pipeline (TikTok, via Higgsfield)
The cloud workspace cannot upload to Higgsfield directly (network policy), so videos go through GitHub:
1. Attach the repo: `add_repo` owner PrimeAiSaaS, repo hatul-media, access push. Clone it (`git clone --depth 1 https://github.com/PrimeAiSaaS/hatul-media /home/claude/hatul-media`).
2. Copy `out/epN_..._wm.mp4` to `episodes/`, commit (end the message with the Co-Authored-By / Claude-Session lines the session asks for), `git fetch origin main`, push to main. Note the new commit hash.
3. `media_import_url` with `https://cdn.jsdelivr.net/gh/PrimeAiSaaS/hatul-media@<commit>/episodes/<file>.mp4`, type video. (raw.githubusercontent.com is rejected: wrong content-type.) The first fetch can time out while jsDelivr warms up — retry once.
4. Higgsfield asset URL = `https://d2ol7oe51mr4n9.cloudfront.net/user_3Ei78lFsofonGhFuVbT8LEWNxTa/<media_id>.mp4`.
5. `tiktok_prepare_publish`: connector_id 57f1eb24-7b39-4a3b-a8b4-33145f3d1bbe, mode UPLOAD_TO_DRAFT, media_type VIDEO, video_url from step 4, title = the post caption, is_aigc true. Gabi submits the form himself; the video lands in his TikTok drafts and he schedules it there. Never call tiktok_publish.

## Publishing pipeline (Instagram, Facebook, YouTube — automatic)
- Control room (dashboard): https://claude.ai/artifact/7rqyo9sn63GdhoBQaoqRnB. Its database collection `episodes` (docs ep1…epN: n, title, status script/production/review/approved/posted, publish_on, caption, yt_title, note, queued, platforms) is the source of truth for approvals. Gabi approves by dragging an episode to "מאושר לפרסום". Only Gabi sets `approved`.
- Sync agent (scheduled task, daily 18:52 Israel): copies approved episodes with a future date into `queue.json` in PrimeAiSaaS/hatul-media (jsDelivr URL pinned to the video's commit), marks them `queued`, and marks past ones `posted`.
- Make scenario 7801107 "חתול בהמתנה — פרסום" (daily 20:30 Israel, active): reads queue.json from raw GitHub and, for items with publish_on = today and approved = true, posts an Instagram Reel, a Facebook Page Reel and a YouTube Short (category Comedy, not made for kids). Each platform is an independent router route.
- Make connections: hatul.bahamtana Instagram (11635958), hatul.bahamtana Facebook (11636265, page 1418076608047856), hatul.bahamtana YouTube (11636533, channel UCvv9MKhiECOjEQIxHSMQe1A). Make is on the Free plan: 2 active scenarios, 1,000 operations/month (≈3 ops per idle day, ≈8 per publish).
- Video files must be platform-safe: H.264 ≤4.5 Mbps, AAC 128k/48 kHz, faststart (the watermark.py encoder settings). Repo file names: epN_<slug>_clean.mp4 (no watermark, since 11.10; ep3/ep4 switched the same day, queue.json updated).
- Never run the Make scenario yourself and never publish directly; the dashboard's "פרסם עכשיו" button is Gabi's.
- Comment bot: Make scenario 7896202 "חתול בהמתנה — עונה לתגובות (Claude)" (instant Instagram NewComment → Claude Haiku in the cat's voice → reply under the comment; skips our own account, thread replies and anything unsafe with SKIP). The "תור" gag: a viewer who comments "תור" gets a personal queue number. Captions since ep4 end with "רוצים מספר בתור? הגיבו ״תור״ 👇". Status 12.10: tested OK, waiting for Gabi to upgrade Make to Core, set it to Immediately, save and turn it on. Facebook/YouTube comment routes come later.

## Data pipeline (metrics → learnings)
- The same Make scenario (daily 20:30) first runs two data routes: YouTube (playlistItems of uploads playlist UUvv9MKhiECOjEQIxHSMQe1A → videos statistics) and Instagram (List posts → Get post insights for posts from the last 14 days). Each writes one row to the Google Sheet "חתול בהמתנה — נתונים" (1hOpEIHr7uAPXiFUkUa2kAxmbf0_qBgFbfwp_YtZNhMI): date, platform, tab-separated lines per post.
- Data agent (scheduled task, daily 21:12 Israel): reads the sheet, writes dashboard docs metrics/ep<N>-<platform> and history/<date>, and writes insights/latest {summary, best_episode, recommendations}.
- The production agent reads insights/latest before each episode and applies the recommendations that fit the script.
- Facebook and TikTok views are not collected yet (no API route in the current connections).
- Episode 1 on YouTube is videoId jgaE3ocq0Os (uploaded manually, title without "פרק 1").

## Episode log
| # | Title | File | Queue number shown | Status |
|---|---|---|---|---|
| 1 | ביטוח לאומי | make_video.py → cat_on_hold.mp4 (repo: ep1_national_insurance_wm.mp4) | 486 | posted Tue 6.10 |
| 2 | קוד ה-SMS | ep2.py → ep2_bank_sms.mp4 (repo: ep2_bank_sms_wm.mp4) | 487 | posted Thu 8.10 (all 4 platforms) |
| 3 | הסניף (v3, Sharit) | ep3.py → ep3_branch.mp4 (repo: ep3_branch_v3_clean.mp4, 11.7 s, no end card — §B) | ticket 847 | posted Mon 12.10 09:37 (IG + YT by Gabi's manual Make run after the YouTube reconnect; FB and TikTok uploaded by hand) |
| 4 | הפקס (v3, he breaks) | ep4.py → ep4_fax.mp4 (repo: ep4_fax_v3_clean.mp4 = v2 + the "הגיבו: תור" CTA from 5.5 s) | 488 (fax badge) | approved, queued, post Tue 13.10 · prediction: overall 43, hook 26 |
| 5 | סוף עונה | ep5.py → ep5_finale.mp4 (repo: ep5_finale_clean.mp4, 12.10) | ticket 489 | in review, post Thu 15.10 · prediction: overall 42, hook 24 |
| מיוחד 1 | תעודת זהות בלי תור (voiced, from the Grok X scan) | sp1.py → sp1_id.mp4 (repo: v2 sp1_id_card_v2_wm.mp4, 35.6 s, no music + cold open; v1 sp1_id_card_wm.mp4; dashboard doc ep100, label "מיוחד") | 490 (he takes a ticket anyway) | v2 in review 10.10, no date yet: Gabi picks the day |
| מיוחד 2 | חברת האינטרנט שלי (Kling pro + 4 voices, 52.7 s) | sp2.py → sp2_internet.mp4 (repo: sp2_internet_wm.mp4; dashboard doc ep102, label "מיוחד 2") | — | in review 11.10, no date yet |
| מגיב 1 | הודעות שכל ישראלי מכיר (reaction pack, 23.9 s) | react1.py → react1.mp4 (repo: react1_messages_wm.mp4; dashboard doc ep101, label "מגיב 1") | — | in review 11.10, no date yet |
| 6 | ההודעה לבוחר (season 2 opener) | ep6.py → ep6_voter.mp4 (repo: ep6_voter_notice_clean.mp4, re-rendered from ep6.py and pushed by Claude 12.10, commit 1ac7934; dashboard doc ep6) | 490 | in review, post Sun 18.10 · prediction: overall 47, hook 33 (best hook so far) |

Next queue number: 491.

## Scripts for the next episodes
### Episode 3 — הסניף (v2, built 7.10) — for reference
- 0–1 lobby, paw already on the button, caption "בסניף. קיבלתי 847." · 1–2.2 x64 "שעתיים אחרי..." board rolls 12→846 · 2.2 847! hop.
- 2.8–5.3 Sharit (customer POV): ticket slides in, she munches, types with one finger, looks up "שנייה, מותק.", leaves; "בהפסקה" sign drops, chair keeps spinning.
- 5.3–7 cat at the window, x64 "הפסקה של 5 דקות"; a wisp drifts in, "רגע... מה זה הריח הזה?"
- 7–9 she slides back in a little cloud, redder eyes, snack bag, lazy groove: "אוי... איזה חמוד אתה." and slides a pink note through the slot.
- 9–10.4 note close-up: "תירגע, חמוד ♥ — שרית" + a rolled paper. 10.4–12 cat stares, pupils tiny → big, slow blush. "המשך יבוא..." · bottom "פרק 4: הפקס". Experiment: baseline-plus (in-motion opening; first episode with a second character).

### Episode 4 — הפקס (v2, built 7.10) — for reference
- Experiment = cold open (flash-forward), unchanged: 0–0.7 the chill cat nodding, the 4th fax going through, "...ואז זה קרה".
- 0.7–1.7 call "שלחו לנו את הטופס בפקס." + slam · 1.7–2.4 "פקס? שנת 2026." · 2.4–3.6 drawer, retro props, fax found.
- 3.85 / 4.65 / 5.45 three attempts, all "שגיאת שידור" ("ניסיון 1/2/3..."); breaking point: squish mouth, twitch, steam from the ears, sad trombone.
- 6.4–7.3 Sharit's note (callback) "שרית אמרה להירגע..." · 7.3–7.95 cloud white-out + little cough.
- 7.6–12 chill: "5 דקות אחרי...", snacks, sway, lo-fi groove; "ניסיון 4..." lazy tap → "התקבל בהצלחה" — he barely notices: "וואלה." → badge "מספרך בתור: 488". "כל. פעם. מחדש." · bottom "פרק 5: סוף עונה".

### Episode 5 — סוף עונה (built 9.10, 12 s) — as built: 0–3 lobby (paw already pressing, ticket 489, laugh, x64 cut off by the ding, board 17→489), 3–4.3 Sharit waves "חמוד!" and raises the stamp, 4.3–5.1 stamp close-up "אושר" + confetti, 5.1–7 duo + plant blooms, 7–8.2 SMS close-up, 8.2–10.4 slow blink, shrug, "סבבה.", "סוף עונה 1.", 10.4–12 back to the lobby pose of frame 0 (loop). Experiment: hook_question ("מי עוד מחכה בסניף הבנק?"). Original script:
- Growth playbook applied: open in motion, keyword in the hook caption ("בסניף" or "הבנק"), experiment chosen from ep4's verdict (keep the cold open if it won, otherwise test start-mid-action). Content rule above applies.
- 0–1.5: the chill cat strolls back into the branch eating from the snack bag; takes ticket 489 and laughs at it. Caption "חוזר לסניף. רגוע."
- 1.5–4: board jumps straight to 489 — Sharit pressed it for him and waves "חמוד!". (Insider deal; the regular customers behind him freeze, x64 stops.)
- 4–7: window 3: Sharit stamps the form in one second "אושר" — confetti, the account is released. The plant revives and blooms (season finale gag). Caption "סוף סוף."
- 7–10: they share the snack bag, lazy groove, both sway in sync. Phone buzz: SMS "נדרש אימות דו-שלבי. החשבון ננעל." Cat reads it, slow blink, shrugs: "סבבה." and keeps munching — bureaucracy can't touch him anymore.
- 10–13: freeze on the two of them, "סוף עונה 1." Bottom: "על מה העונה הבאה? כתבו בתגובות".
- caption: open with "ארנונה, ביטוח רכב או חברת הסלולר?" — the season 2 vote.

### Season 2 arc — "הכתובת" (written 12.10 by the production agent; default topic until the ep5 vote is in)
The chill cat (from ep4) vs. one thread that runs through every system: his registered address is still grandma's in Eilat. Each episode opens where the last ended, next-episode name as text over the final action or in the caption/pinned comment (§B). Built from the approved ideas first (2026-10-10-1 ההודעה לבוחר, 2026-10-10-2 הקצבה של ה-12). Elections are 27.10: keep it neutral — no parties, candidates or real people, only the bureaucratic pain. The ep5 vote (ארנונה / ביטוח רכב / חברת הסלולר) can still re-steer eps 8–10: Gabi decides.
- Ep 6 — ההודעה לבוחר (Sun 18.10, built 12.10, queue 490). Envelope flies in, chill cat catches + rips it; the notice: polling station in Eilat, 350 km. Calls to move it: x64 to 490, "מאוחר מדי לשינוי." / "תצביע בקלפי שלך." / "רוצה שנשלח לך הודעה נוספת?" — "סבבה." A second envelope flies in = frame 1. Experiment: share_cta (queued).
- Ep 7 — הקצבה של ה-12 (Mon 19.10, queue 491). Opens on the phone: bank app balance 0.00, calendar says 20. ביטוח לאומי: "הכסף נשלח ב-12." — to the account on file... grandma's. Rule of three on the IVR (press 1, press 2, press 3 = back to the main menu). Hook keyword: ביטוח לאומי. Experiment: length_10s (queued).
- Ep 8 — ארנונה (Tue 20.10, queue 492). Grandma calls: an arnona bill in HIS name arrived at her place in Eilat. The cat at the municipality window; Sharit is there now ("העבירו אותי, מותק"). Experiment: opening_type per ep4's cold_open verdict (queued).
- Ep 9 — שינוי כתובת (Wed 21.10, queue 493). To change the address he needs proof of address; the proof is the arnona bill; the bill is at the old address. A perfect loop — the episode literally loops. Sharit stamps something anyway.
- Ep 10 — יום הבחירות (Tue 27.10, queue 494, arc finale). He drives 350 km to vote, snack bag on the dashboard; the queue at the polling station; grandma is the one sitting at the polling table. Neutral: no ballots of real parties shown, just the envelope. The plant (wilting again since ep6) gets watered by grandma.

### After episode 5 (kept for reference)
Season 2 topic = the option with the most comments (ask Gabi which won; default ארנונה). Write a 5-episode arc in the same structure (each episode opens where the last ended; the next episode's name appears as text over the final action, never as a separate end card — §B), add it here, then build episode 6.
