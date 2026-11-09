(prompt of scheduled task trig_01QRRLDkSMNSvws8uPdPjvWb "חתול בהמתנה: אישור אוטומטי (שבוע מילואים)", daily 17:41 Asia/Jerusalem, created 9.11 22:24 at Gabi's request; see the saved prompt in the task — this file mirrors it in summary)
- Authority: Gabi 9.11 22:02 "אני לא אהיה שבוע במחשב אני צריך שהכל יהיה אוטומטי" → "אישור אוטומטי לשבוע". meta/auto_approve {enabled, until: 2026-11-17}.
- Approves an episode only if: status review; publish_on in [tomorrow, until]; video_url + repo_file; rebuild_voiced not true; no voice_text_changed; voiced → pron_check "passed"; no hold note from Gabi; no other approved episode that day.
- Never publishes/schedules (sync does), never spends credits, never touches approved/posted episodes.
- Logs runs/<ts>-autoapprove and tasks/autoapprove; messages Gabi when it approves something or a day in the next 3 is empty.
