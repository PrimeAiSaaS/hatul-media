## 5א. חיזוי מול מציאות (§J)
לכל predictions/ep<N> שהפרק שלו עלה לפני 24 שעות לפחות: update עם if_version של actual = {measured_at, by_platform: {instagram: {views, retention}, tiktok: {views, retention, completion_rate}, youtube: {views, retention, stayed_to_watch}, facebook: {views}}} מתוך metrics. רק ממלאים; הכיול של הסוכן השבועי.
## 6ב. פרסום ובוט התגובות
- runs/<YYYYMMDD>-2030-publish + tasks/publish: status ok אם יש בגיליון שורות מהיום ואין publish_error; failed אם יש publish_error (עם הפלטפורמה והסיבה); warn אם אין שורות מהיום (Make לא רץ).
- tasks/comments: אם בשורות instagram_comments מהיום יש תשובות של hatul.bahamtana, הבוט עובד (ok). אם יש תגובות צופים מהיום ואין אף תשובה שלנו: warn "הבוט לא ענה". אם אין תגובות: אל תשנה.
## 6ג. בקרה ויומן (§K, חובה בסוף כל ריצה)
runs/<YYYYMMDD-HHMM>-data + tasks/data (triggerId trig_01YHZQp6p1QPxZirXtkAZ5hw, when "כל ערב 21:12"). returned: {metrics_written, history_doc, comments_added, ideas_added, verdicts, predictions_updated}. checks: לכל פרק שעלה יש מדידה מהיום, צפיות לא ירדו לעומת history, retention בין 0 ל-100 (חוץ מלופ ביוטיוב), meta/data_sync נכתב.
