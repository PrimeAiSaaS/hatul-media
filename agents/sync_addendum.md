## 5. בקרה ויומן (חובה בסוף כל ריצה, גם אם משהו נכשל או שלא היה שינוי)
בלוח הבקרה, עם ArtifactData:
1. set ל-runs/<YYYYMMDD-HHMM>-sync (השעה בשעון ישראל), data: {task: "sync", name: "סוכן סנכרון", at: "<ISO עם +03:00>", status: "ok" / "warn" / "failed", summary: "<שורה אחת בעברית>", returned: {queue_items, newly_queued: [..], marked_posted: [..], unqueued: [..], commit: "<hash קצר או null>"}, checks: [{name: "כל video_url בתור מחזיר וידאו", ok, note}, {name: "כל פרק approved עם תאריך עתידי נמצא בתור", ok, note}, {name: "אין בתור פרק שכבר עלה", ok, note}]}.
2. tasks/sync: get ואז update עם if_version (אם לא קיים: set) עם {name: "סוכן סנכרון", when: "כל יום 18:52", lastRunAt, lastStatus, lastNote, nextRun: "<ISO UTC>", triggerId: "trig_01AnctU5d7pN4UAFnCgk7gjX"}.
3. פרק שהסטטוס שלו posted, או שאחת הפלטפורמות שלו כבר live, לא נכנס לתור בשום מקרה (מונע פרסום כפול). קובץ ברירת מחדל: epN_*_clean.mp4 (ורק אם אין, _wm.mp4).
אל תמציא מספרים ב-returned: רק מה שבאמת עשית.
