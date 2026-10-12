עדכן את ההנחיות של 4 המשימות המתוזמנות של "חתול בהמתנה". לכל אחת: הוסף לסוף ההנחיה הקיימת את הטקסט שמתחת לכותרת שלה, בלי למחוק כלום. סעיפים שמתחילים ב"שינויים" גוברים על מה שכתוב לפניהם. אל תשנה שעות, שמות או הגדרות אחרות. בסוף, הראה לי לכל משימה שהעדכון נשמר.

=== חתול בהמתנה: סנכרון תור הפרסום (trig_01AnctU5d7pN4UAFnCgk7gjX) ===
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

=== חתול בהמתנה: סוכן נתונים (trig_01YHZQp6p1QPxZirXtkAZ5hw) ===
## 5א. חיזוי מול מציאות (§J)
לכל predictions/ep<N> שהפרק שלו עלה לפני 24 שעות לפחות: update עם if_version של actual = {measured_at, by_platform: {instagram: {views, retention}, tiktok: {views, retention, completion_rate}, youtube: {views, retention, stayed_to_watch}, facebook: {views}}} מתוך metrics. רק ממלאים; הכיול של הסוכן השבועי.
## 6ב. פרסום ובוט התגובות
- runs/<YYYYMMDD>-2030-publish + tasks/publish: status ok אם יש בגיליון שורות מהיום ואין publish_error; failed אם יש publish_error (עם הפלטפורמה והסיבה); warn אם אין שורות מהיום (Make לא רץ).
- tasks/comments: אם בשורות instagram_comments מהיום יש תשובות של hatul.bahamtana, הבוט עובד (ok). אם יש תגובות צופים מהיום ואין אף תשובה שלנו: warn "הבוט לא ענה". אם אין תגובות: אל תשנה.
## 6ג. בקרה ויומן (§K, חובה בסוף כל ריצה)
runs/<YYYYMMDD-HHMM>-data + tasks/data (triggerId trig_01YHZQp6p1QPxZirXtkAZ5hw, when "כל ערב 21:12"). returned: {metrics_written, history_doc, comments_added, ideas_added, verdicts, predictions_updated}. checks: לכל פרק שעלה יש מדידה מהיום, צפיות לא ירדו לעומת history, retention בין 0 ל-100 (חוץ מלופ ביוטיוב), meta/data_sync נכתב.

=== חתול בהמתנה: הפקת פרק (trig_01WTkwFNwrRswy1mdVxqLnss) ===
## שינויים — 12.10 (קצב יומי, טקסט לכל פלטפורמה, סטוריז)
- הסוכן רץ עכשיו כל יום. publish_on של הפרק = היום הפנוי הראשון בלוח שהוא לפחות יומיים קדימה (§L בספר). פרק 10 (יום הבחירות) נשאר ב-27.10.
- בסעיף 4 (כיתובים): במקום ההנחיה הישנה, כתוב את חמשת השדות לפי §C בספר: caption (אינסטגרם, עם CTA אחד ועד 3 האשטגים), caption_fb (פייסבוק, 6–10 שורות סיפור, בלי CTA של "תור"), yt_title, yt_description (עם "פרק חדש כל יום ב-20:30" ו-3 האשטגים), caption_tiktok.
- בסעיף 6: הקובץ שנדחף למאגר הוא הנקי, episodes/epN_<slug>_clean.mp4 (שלב 4 ב-Production checklist), לא _wm. repo_file מצביע עליו.
- סטוריז (§M): אחרי הדחיפה, הרץ במאגר `python3 tools/story_kit.py episodes/<file> stories/ep<N> "<שאלת ההוק>"` ודחוף את stories/ep<N> באותו commit. בהודעה לגבי: שורה אחת שהסטוריז מוכנים בתיקייה stories/ep<N> במאגר.

## 6א. שער חיזוי (§J)
- אחרי הדחיפה: media_import_url מ-jsDelivr (@commit), virality_predictor (action create, params {"model":"virality_predictor","medias":[{"role":"video","id":<media_id>}]}), jobs_wait עד הסוף. נכשל: נסה שוב פעם אחת; קובץ ארוך מ-13 ש׳: נתח חיתוך של 12 ש׳.
- חלץ את המספרים ב-sandbox_exec של Higgsfield (הפקודה ב-§J), וכתוב predictions/ep<N>.
- hook_score מתחת ל-30: תיקון אחד לפי §A, רינדור, חיזוי שוב, שומרים את הטובה יותר. בהודעה לגבי: הכללי וההוק.

## 8. בקרה ויומן (§K, חובה בסוף כל ריצה)
runs/<YYYYMMDD-HHMM>-production + tasks/production (triggerId trig_01WTkwFNwrRswy1mdVxqLnss, when "כל יום 09:53"). returned: {episode, file, commit, publish_on, prediction: {overall, hook}, stories: true/false, tiktok_draft}. checks: contact sheet נבדק, הקובץ במאגר ו-jsDelivr מחזיר וידאו, predictions נכתב, 5 שדות הטקסט מלאים, סטוריז במאגר, מסמך הפרק ב-review.

=== חתול בהמתנה: סיכום שבועי ושיפור (trig_01C1LQMstEw3rfURCFvJi7yM) ===
## שינוי בסעיף 0 (מחקר) — 12.10
- יש עכשיו פרק כל יום, אז בחר 5 נושאים בשבוע (לא 2) וכתוב 5 מסמכי ideas.

## 2א. כיול החיזוי (§J)
קרא predictions ו-metrics. לכל פרק עם 100+ צפיות בפלטפורמה, השווה את hook_score למדד הפתיחה (טיקטוק: צפייה ממוצעת %, יוטיוב: stayed_to_watch) ואת overall לצפייה הממוצעת. מ-3 פרקים ומעלה: מתאם דירוג (Spearman) והאם הכיוון נכון. כתוב meta/prediction_calibration {updated_at, n_episodes_with_field_data, summary, rules[], table[]}. פחות מ-3 פרקים: "עוד מוקדם", ושמור את הכללים הקיימים. כלל עובר ל-§I רק אחרי 3 פרקים שמסכימים עם השטח.

## 2ב. בקרת סוכנים (§K)
קרא tasks/* ו-runs/* של 7 הימים האחרונים. לכל סוכן (production, sync, publish, data, weekly, comments): רץ בזמן, אין failed בלי הסבר, ה-checks עוברים, ובדיקה מדגמית של מספר אחד מול המקור. כתוב audit/latest {at, items: [{agent, ok, note}]}. מחק runs/* מעל 30 יום. כל כישלון נכנס לדו"ח לגבי. בדוק גם שהיה פרסום בכל אחד מ-7 הימים (§L).

## 5. בקרה ויומן (חובה בסוף כל ריצה)
runs/<YYYYMMDD-HHMM>-weekly + tasks/weekly (triggerId trig_01C1LQMstEw3rfURCFvJi7yM, when "שבת 18:57").
