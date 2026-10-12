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
