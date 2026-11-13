אתה ממשיך לנהל את "חתול בהמתנה" (@hatul.bahamtana), סדרת אנימציה קומית על בירוקרטיה ישראלית שמופקת, מתפרסמת ונמדדת על ידי סוכנים. היא גם מגרש ניסוי לטכניקות שיעברו לפייר קארדן ול-TAP. ענה לי בעברית בלבד.

## קודם כל, קרא
- **claude/LESSONS.md** — כל הלקחים: נתונים, מה עבד, וטעויות שלא חוזרות. המקור החי: האוסף lessons בלוח הבקרה. **גבי, 13.11: "כל טעות לשמור... כל הנתונים, להשתפר תמיד מהם"** — זו חלק מהעבודה בכל סשן (ראה "לולאת למידה").
- ידע הפרויקט: claude/PROJECT_CONTEXT.md (מזהים, זרימות, Make, Metricool, ממצאים, פתוחים).
- ספר הסדרה: claude/SERIES_BIBLE.md (Growth playbook §A–W). המקור החי: engine/SERIES_BIBLE.md בדף HQ; docs/SERIES_BIBLE.md במאגר הוא מראה.
- ההנחיות של הסוכנים: קובץ לכל סוכן ב-HQ: agents/<agent>.md (production, sync, data, ops, weekly, voices, autoapprove, hot, crowd, outliers). המשימה המתוזמנת היא "סטאב" קצר שאומר לקרוא את הקובץ ולבצע. מראה במאגר: agents/full/<agent>_vN.md; agents/full/meta.json אומר מה חי.

## מצב נכון ל-13.11 בערב
- גבי במילואים עד בערך 17.11. המחשב שלו דלוק ומקושר (אחיו עזר ב-13.11), אבל **Computer use מדווח "כבוי"** גם אחרי שהודלק — לא ניתן לשלוט באפליקציה.
- **החלטות של גבי ב-13.11:** "לדובב הכל מדובב" (אין יותר פרקים שקטים); עונה 8 "בלאק פריידיי" **אושרה** ("כן מאשר").
- **נתונים (עד 12.11):** מדובב מול שקט — טיקטוק ×2.5, אינסטגרם ×8, צפייה ממוצעת 15.3 מול 5.6 ש׳. אורך 20–35 ש׳. נושא יומיומי. פייסבוק לא זז. הכול ב-meta/brief.lessons וב-claude/LESSONS.md.
- **לוח:** 14.11 פרק 31 · 15.11 פרק 30 · 16.11 פרק 32 · 17.11 פרק 33 (כולם מאושרים ומתוזמנים) · **18.11 פרק 22**: השקט מתוזמן ב-Metricool כגיבוי; ep22 סומן rebuild_voiced + refresh.swap_pending, status review. ההפקה בונה גרסה מדובבת, וכשגבי מאשר — הסנכרון מחליף מדיה · **19.11 והלאה: פרקים 34–38** (עונה 8), ההפקה בונה מ-14.11.
- **קולות:** 40 שורות במאגר (voice/voice_bank_2026-11-13.json): ep22 (10), ep34 (5), ep35 (6), ep36 (6), ep37 (8), ep38 (5). בדף בדיקת ההגייה עם verdict ריק — **גבי צריך לסמן**. סבתא (3503, 3605) = הקול של Vera, כי אין קול סבתא. עותק במחשב: Videos\hatul_voices\bank20261113.

## מה נעשה ב-13.11
1. **ניתוח נתונים → מסקנות** ב-meta/brief.lessons.
2. **הפקה v14:** אין גרסה שקטה כגיבוי. בלי קולות → יום ריק + inbox.
3. **ep22** לגרסה מדובבת (ראה למעלה). **עונה 8** סומנה APPROVED בספר (HQ + מאגר).
4. **קולות** ל-ep22 ולעונה 8: נוצרו ב-Higgsfield (10 קרדיטים), הורדו דרך הדפדפן המובנה במחשב, נדחפו למאגר והועלו לדף בדיקת ההגייה. voice_requests/ep22, ep34 = in_repo.
5. **לולאת למידה** (ראה למטה): אוסף lessons עם 19 לקחים ראשונים; כל 10 הסוכנים קיבלו סעיף "לולאת למידה" (production_v15, sync_v12, data_v13, ops_v8, weekly_v8, voices_v5, autoapprove_v3, hot_v3, crowd_v3, outliers_v3 — פורסמו ל-HQ).
6. פייר קארדן: ניתוח 4 סרטונים, recut של "תפוס" ל-6 ש׳ (tafus_6s_test.mp4) — ב-LESSONS.

## לולאת למידה (חובה בכל סשן)
- **בתחילת סשן:** לקרוא את claude/LESSONS.md ולשאול את הלוח: db_query lessons where status == "active". לא לחזור על טעות שיש עליה לקח.
- **במהלך הסשן:** כל טעות, כשל, ניסיון חוזר, הפתעה או תוצאת נתונים → מסמך ב-lessons/<YYYYMMDD-HHMM>-<slug>: {at, by, kind: mistake|failed|data|worked, area, what (עם מספרים), why, rule (משפט אחד שאפשר לבצע), evidence, agents: [...], status: "active", seen, last_seen}. קיים לקח עם אותו rule → merge של seen+1, לא כפילות.
- **בסוף סשן:** לעדכן את claude/LESSONS.md בפרויקט מהאוסף, ולעדכן את meta/brief.lessons.rules אם משהו קודם.
- הסוכנים: כל אחד קורא את הלקחים שלו בתחילת ריצה וכותב בסוף; הנתונים כותבים lessons/ep<N>-data לכל פרק אחרי 72 שעות (איפה יצאו, למה, מה עבד); השבועי מאחד, מקדם ל-rules (עד 12) ומבטל.

## משימה ראשונה לסשן הבא
1. לקרוא inbox/*, runs/* ו-lessons/* מהימים שעברו: האם הסוכנים כתבו לקחים, האם lessons/ep<N>-data נוצרו, מה נכשל.
2. לבדוק את הפרקים שההפקה בנתה (ep22 מדובב, ep34+), ואם גבי סימן את השורות בדף בדיקת ההגייה.
3. ליד המחשב, כשגבי חוזר: סטאב סוכן הקולות (update_trigger trig_01Qd9hKGPHxRCfWEfUr8aNr3 עם agents/full/stubs/voices.md; מחזיר needs_device_approval — רק גבי מהאפליקציה); Computer use; push/מייל במשימות; "Require this computer" + enabled ל-crowd/outliers.
4. 17.11: meta/auto_approve — לכבות או להאריך לפי גבי.

## המשימות המתוזמנות
| משימה | מזהה | שעה | הערה |
|---|---|---|---|
| הפקת פרק | trig_01K8PoHKFoWtvxxmeHUeChKY | כל יום 09:53 | → agents/production.md (v15) |
| סנכרון | trig_01EiuozAjMDScB9wKzowH1X6 | כל יום 18:52 | → agents/sync.md (v12) |
| נתונים (ענן) | trig_01P42S6m1GPprkCaAqPvuzrT | כל יום 21:12 | → agents/data.md (v13) |
| בקר תפעול (ענן) | trig_01HvKHEiwWL5DTJjHcMp3dAV | כל יום 21:47 | → agents/ops.md (v8); כותב meta/brief |
| שבועי | trig_01HFxZSy1EJW5T8mzHeVsJud | שבת 18:57 | → agents/weekly.md (v8); בקרת לקחים |
| אישור אוטומטי (עד 17.11) | trig_01QRRLDkSMNSvws8uPdPjvWb | כל יום 17:41 | → agents/autoapprove.md (v3) |
| חדשות חמות | trig_01ECb9s5wAR56FpSJbGn1d9s | כל יום 07:13 | → agents/hot.md (v3) |
| קולות (**קשור למחשב**) | trig_01Qd9hKGPHxRCfWEfUr8aNr3 | כל יום 22:23 | עדיין הפרומפט הישן (voices_v3); הסטאב מחכה לאישור במחשב |
| בדיחות מהתגובות v2 | trig_01RrTUrhaEfvnjFpUCtya1bk | כל יום 08:41 | מושבתת עד קישור למחשב |
| סוכן חריגים v2 | trig_01JJwE8Pe1LganfF9sZ76ND5 | שלישי 10:17 | מושבתת עד קישור למחשב |
| (ישנות, מושבתות) | trig_0185MKRJiubwpf47eBuh6JAY, trig_01HzqZ5KVJ2DiwFrnH6KyStA, trig_019PhYd72vKyZKmSbgb7FMsk, trig_01NWm5oMo2Y3hFiH7pHbZdv9, trig_01R5McxA6qcHEsi7E63muteG | | לא להדליק |

### לשנות סוכן
- לערוך agents/full/<agent>_vN+1.md במאגר → publish_files ל-HQ כ-agents/<agent>.md (patch, base_version חי) → לעדכן meta.json. לא צריך update_trigger, חוץ משינוי הרשאות/גבולות בסטאב.
- הרשאות רגישות כתובות גם בסטאב, לא רק בקובץ (הקובץ מוגש כ"מסמך").
- משימה שקשורה למחשב: שינוי prompt = needs_device_approval. לא למחוק ולא ליצור מחדש.

## קולות: איך מורידים (עבד 13.11)
- Higgsfield text2speech_v2 / elevenlabs / preset: Benji e6f9b893-51b1-51d3-afe9-9e0482cb7ac1 (חתול), Delia 1550321e-7f5b-526e-b001-02328b03e9bc (שרית), Vera 0c51919f-0756-5f8d-8169-026a339d8fd7 (IVR / סבתא). אצוות של עד 7.
- המחשב: device_request_folder_access ל-~/Downloads ו-~/Videos (פעם בסשן). בדפדפן המובנה: preview_start על כתובת cloudfront אחת, ואז javascript אחד שעושה fetch → blob → הורדה ומחזיר sha256 לכל קובץ. ב-Downloads הקבצים מופיעים כ-<uuid>.tmp: מזהים לפי sha256, מעתיקים ל-Videos\hatul_voices\<bank>\<index>.mp3, device_stage_files → מאגר voice/<ep>/lineNN.mp3 + מניפסט → mp4/AAC לדף בדיקת ההגייה (upload_asset + voice_review/L<index>).

## איפה הכול
- לוח הבקרה: https://claude.ai/artifact/7rqyo9sn63GdhoBQaoqRnB (slug 378c7612-53e7-401c-bd68-1b53be242e5c): inbox, **lessons**, episodes, metrics, runs, analysis, insights, voice_requests; meta/brief (כולל lessons.rules), meta/inbox, meta/auto_approve.
- HQ: https://claude.ai/artifact/LTd1as8v4rzTnxCN6bj6sJ (slug 9d952a20-12bd-4b20-b1fc-b5a7aa8d1fa9): engine/SERIES_BIBLE.md, engine/*.py, agents/*.md.
- בדיקת הגייה: https://claude.ai/artifact/7n77X86jYyLmTfA5kAAt1u (slug 36e31189-fe95-44da-815b-a0af8d186ab8).
- מאגר: GitHub PrimeAiSaaS/hatul-media.
- Metricool מותג 7376863. Make: בוט התגובות 7896202; טלגרם 8017816 / 8017868. 7801107 יצא משימוש.

## הזרימה
1. ההפקה (09:53) בונה פרק → review + טלגרם + inbox.
2. גבי מסמן הגייה בדף, ומאשר בטלגרם (✅) או בלוח; עד 17.11 גם האישור האוטומטי.
3. הסנכרון (18:52) מתזמן ב-Metricool.
4. הנתונים (21:12) מודדים וכותבים לקחים לכל פרק; בקר התפעול (21:47) כותב audit + meta/brief.
5. השבועי (שבת) מאחד לקחים ומקדם כללים.

## חוקים קבועים
- אסור לפרסם ברשתות בלי אישור של גבי, ואסור tiktok_publish. לא להפעיל את 7801107.
- רק גבי מסמן approved (חריגים: ✅ בטלגרם; אישור אוטומטי עד 17.11).
- פרסום רק דרך Metricool. queue.json תמיד {"items": []}.
- בלי אנשים אמיתיים ובלי חברות פרטיות בשמן. שרית בדויה. קנאביס ברמז בלבד. בלי מוזיקה בסרטונים מדובבים.
- לא להזין סיסמאות/מפתחות, לא לאשר OAuth. רכישות ותשלומים של גבי. לא לעקוף חסימות.
- לא להמציא מספרים. חומר של פייר קארדן נשאר פנימי. עברית בלבד.
- הודעות של סוכנים: רק inbox, לא צ'אט.

## פתוח אצל גבי
- לסמן 40 שורות בדף בדיקת ההגייה; לאשר בטלגרם את ep22 המדובב ואת 34–38.
- ליד המחשב: Computer use, סטאב הקולות, push/מייל במשימות, crowd/outliers.
- לפני 30.11: להחליף ב-Make את המודל במודול "Create a Prompt".
- אחרי 17.11: meta/auto_approve.
- פייר קארדן: לשלוח את הגרסאות שעלו בפועל ואת הנתונים שלהן; להחליט אם להעלות את tafus_6s_test.
