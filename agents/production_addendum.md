## 6א. שער חיזוי (Growth playbook §J בספר)
- הקובץ שנדחף למאגר הוא הנקי: episodes/epN_<slug>_clean.mp4 (שלב 4 ב-Production checklist), לא _wm.
- אחרי הדחיפה: media_import_url מ-jsDelivr (@commit), ואז virality_predictor (action create, params {"model":"virality_predictor","medias":[{"role":"video","id":<media_id>}]}), jobs_wait עד שמסתיים. אם נכשל: נסה שוב פעם אחת; אם הקובץ ארוך מ-13 ש׳, נתח חיתוך של 12 ש׳.
- חלץ את המספרים ב-sandbox_exec של Higgsfield (הפקודה בסעיף §J), וכתוב predictions/ep<N> לפי הסכמה.
- hook_score מתחת ל-30: תיקון אחד שמותר לפי §A, רינדור, חיזוי שוב, ושומרים את הגרסה הטובה יותר. בהודעה לגבי: הציון הכללי וההוק (לפני/אחרי אם תיקנת).
## 8. בקרה ויומן (§K, חובה בסוף כל ריצה)
runs/<YYYYMMDD-HHMM>-production + tasks/production (triggerId trig_01WTkwFNwrRswy1mdVxqLnss, when "ב׳ ד׳ ו׳ 09:53"). returned: {episode, file, commit, prediction: {overall, hook}, tiktok_draft}. checks: contact sheet נבדק, הקובץ במאגר ו-jsDelivr מחזיר וידאו, predictions נכתב, מסמך הפרק ב-review.
