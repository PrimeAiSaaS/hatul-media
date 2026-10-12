## שינויים בסעיף 2 (בניית התור) — 12.10
- פריט בתור כולל עכשיו טקסט נפרד לכל פלטפורמה, מתוך מסמך הפרק בלוח:
  {"episode", "publish_on", "approved": true, "video_url", "caption": caption (אינסטגרם), "caption_fb": caption_fb (פייסבוק; אם ריק — caption), "yt_title", "yt_description": השדה yt_description של הפרק (אם ריק — caption + "\n\nחתול בהמתנה: פרק חדש כל יום ב-20:30.\n\n#shorts #חתולבהמתנה")}.
- הקובץ: repo_file של הפרק. אם אין, ברירת המחדל היא epN_*_clean.mp4 (ורק אם אין clean, _wm.mp4). פרקים מיוחדים (n ≥ 100) נכנסים לתור בדיוק כמו פרקים רגילים.
- פרק שהסטטוס שלו posted, או שאחת הפלטפורמות שלו כבר live, לא נכנס לתור בשום מקרה (מונע פרסום כפול).
- התרחיש ב-Make רץ כל יום ב-20:30, כך שיש פרסום כל יום.

## 5. בקרה ויומן (חובה בסוף כל ריצה, גם אם משהו נכשל או שלא היה שינוי)
בלוח הבקרה, עם ArtifactData:
1. set ל-runs/<YYYYMMDD-HHMM>-sync (השעה בשעון ישראל), data: {task: "sync", name: "סוכן סנכרון", at: "<ISO עם +03:00>", status: "ok" / "warn" / "failed", summary: "<שורה אחת בעברית>", returned: {queue_items, newly_queued: [..], marked_posted: [..], unqueued: [..], commit: "<hash קצר או null>"}, checks: [{name: "כל video_url בתור מחזיר וידאו", ok, note}, {name: "כל פרק approved עם תאריך עתידי נמצא בתור", ok, note}, {name: "אין בתור פרק שכבר עלה", ok, note}, {name: "יש פרק לכל אחד מ-3 הימים הקרובים", ok, note}]}.
2. tasks/sync: get ואז update עם if_version (אם לא קיים: set) עם {name: "סוכן סנכרון", when: "כל יום 18:52", lastRunAt, lastStatus, lastNote, nextRun: "<ISO UTC>", triggerId: "trig_01AnctU5d7pN4UAFnCgk7gjX"}.
3. אם באחד מ-3 הימים הקרובים אין פרק מאושר בתור, כתוב לגבי שורה אחת: איזה יום ריק ואיזה פרק מחכה לאישור שלו.
אל תמציא מספרים ב-returned: רק מה שבאמת עשית.
