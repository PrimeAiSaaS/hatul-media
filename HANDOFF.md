אתה ממשיך לנהל את "חתול בהמתנה" (@hatul.bahamtana), סדרת אנימציה קומית על בירוקרטיה ישראלית שמופקת, מתפרסמת ונמדדת על ידי סוכנים. היא גם מגרש ניסוי לטכניקות שיעברו לפייר קארדן ול-TAP. ענה לי בעברית בלבד.

## קודם כל, קרא
- ידע הפרויקט: claude/PROJECT_CONTEXT.md (מזהים, זרימות, Make, Metricool, ממצאים, פתוחים). הסעיף האחרון = מה השתנה ב-12.11.
- ספר הסדרה: claude/SERIES_BIBLE.md (Growth playbook §A–W = החוקים). המקור החי של הסוכנים הוא engine/SERIES_BIBLE.md בדף HQ; docs/SERIES_BIBLE.md במאגר הוא מראה.
- ההנחיות של הסוכנים: **מ-12.11 ההנחיה של כל סוכן היא קובץ ב-HQ: agents/<agent>.md** (production, sync, data, ops, weekly, voices, autoapprove, hot, crowd, outliers). המשימה המתוזמנת עצמה היא רק "סטאב" קצר: תפקיד, הרשאות, גבולות, ו"קרא את הקובץ ובצע". מראה במאגר: agents/full/<agent>_vN.md, ו-agents/full/meta.json אומר מה חי.

## מצב נכון ל-12.11 בבוקר
- גבי במילואים מ-10.11 לבערך שבוע, כמעט בלי מחשב. המחשב שלו (מחשבסיתי) כבוי. meta/auto_approve פעיל עד 17.11.
- לוח שידורים: 12.11 פרק 25 · 13.11 פרק 29 · 14.11 פרק 31 · 15.11 פרק 30 · 16.11 פרק 32 · 17.11 פרק 33 (סוף עונה 7; גבי אישר בטלגרם 11.11 16:36, בקר התפעול יישם; הסנכרון מתזמן אותו 12.11 18:52) · **18.11 פרק 22** (גשר שקט, הוזז 12.11 מ-8.11; הסנכרון מתזמן 17.11). 12–16 מתוזמנים ב-4 הרשתות.
- **מ-19.11 אין פרקים.** עונה 8 "בלאק פריידיי" (פרקים 34–38) כתובה בספר כהצעה (PROPOSED 12.11) ומחכה לאישור של גבי. כולם מדובבים: הקולות נוצרים ומורדים רק בשיחה שמקושרת למחשב של גבי. עד אז סוכן ההפקה לפי 6ה: מחכה כשהעלייה בעוד 5+ ימים, ומתחת ל-5 ימים בונה גרסה שקטה.
- 11.11: הסנכרון, הנתונים והאישור האוטומטי נפלו על USAGE_LIMIT_REACHED (מגבלת שימוש בחשבון). בקר התפעול ניסה להריץ שוב וה-fire_trigger נחסם (permission classifier).

## מה נעשה ב-12.11 (הסשן הזה)
1. **תיבת "הודעות אליך" בלוח (v26):** כרטיס בראש דף הבית שקורא את האוסף inbox ({at, from, title, body, needs_action, read}). לא-נקראו קודם, needs_action מודגש בכתום, כפתור "נקרא", "סמן הכול כנקרא", "הצג נקראו". meta/inbox.enabled = true.
2. **כל הסוכנים כותבים ל-inbox במקום SendUserMessage.** סטאבים חדשים ב-update_trigger: production, sync, weekly, autoapprove, hot. crowd_v2 / outliers_v2 כבר כתבו ל-inbox (ומושבתות עד קישור למחשב).
3. **נתונים ובקר תפעול עברו לענן:** המשימות הישנות (trig_0185MKRJiubwpf47eBuh6JAY, trig_01HzqZ5KVJ2DiwFrnH6KyStA) התבררו כקשורות למחשב של גבי (בקר התפעול הושעה device_absent כשהמחשב כבה). נוצרו משימות חדשות בענן עם אותן שעות: **נתונים trig_01P42S6m1GPprkCaAqPvuzrT (21:12)**, **בקר תפעול trig_01HvKHEiwWL5DTJjHcMp3dAV (21:47)**, בלי push. הישנות הושבתו (לא נמחקו) ושמן שונה ל"(ישן, קשור למחשב — מושבת)". לא להדליק אותן במקביל לחדשות.
4. **להוזיל: meta/brief.** בקר התפעול כותב כל ערב מפה קצרה (ימים מאתמול עד 8 קדימה, review, approved, ימים ריקים, last_story_v2, titles, failures, numbers). הפקה, סנכרון, אישור אוטומטי, חדשות חמות וקולות קוראים אותה, ובמקום list על כל episodes / metrics עושים get / query עם where. מסמך פרק אחד הוא כ-8KB, אז list על 60 פרקים היה החלק היקר בכל ריצה. Claude זרע את meta/brief ב-12.11 06:22.
5. **סוכן הקולות ו-403:** הסיבה: הוא עשה git clone בלי add_repo (הכלי נטען רק דרך ToolSearch), ולכן ה-push נדחה. voices_v4 (ב-HQ agents/voices.md) מתקן: ToolSearch "select:mcp__claude-code-remote__add_repo" → add_repo push → clone. **אבל המשימה קשורה למחשב, ולכן הסטאב החדש לא נשמר (needs_device_approval).** הטקסט מוכן ב-agents/full/stubs/voices.md. הבחירה של גבי 3304→C כבר במאגר (ההפקה החילה אותה) וסומנה applied בדף בדיקת ההגייה.
6. עונה 8 נכתבה בספר כהצעה; פרק 22 שובץ ל-18.11; הודעה ראשונה ל-inbox (needs_action) עם שתי ההחלטות.

## משימה ראשונה לסשן הבא
1. לקרוא inbox/* ו-runs/* מהימים שעברו (הלוח, כרטיס "הודעות אליך" ו"יומן ובקרת סוכנים"): האם הסטאבים עבדו (כל סוכן קרא את agents/<agent>.md מ-HQ), האם meta/brief נכתב כל ערב, ואם משהו חזר ל-SendUserMessage.
2. אם גבי ליד המחשב, בשיחה מקושרת למחשב:
   - לאשר את הסטאב של סוכן הקולות (update_trigger trig_01Qd9hKGPHxRCfWEfUr8aNr3 עם agents/full/stubs/voices.md).
   - קולות לעונה 8 (אחרי שגבי מאשר את הקשת): לייצר, להוריד, לדף בדיקת ההגייה.
   - "Require this computer" + enabled ל-crowd_v2 ול-outliers_v2.
3. אחרי 17.11: לכבות או להאריך את meta/auto_approve לפי גבי.

## המשימות המתוזמנות
| משימה | מזהה | שעה | הערה |
|---|---|---|---|
| הפקת פרק | trig_01K8PoHKFoWtvxxmeHUeChKY | כל יום 09:53 | סטאב → agents/production.md |
| סנכרון | trig_01EiuozAjMDScB9wKzowH1X6 | כל יום 18:52 | סטאב → agents/sync.md |
| נתונים (ענן) | trig_01P42S6m1GPprkCaAqPvuzrT | כל יום 21:12 | חדש 12.11, בלי push |
| בקר תפעול (ענן) | trig_01HvKHEiwWL5DTJjHcMp3dAV | כל יום 21:47 | חדש 12.11, בלי push; כותב meta/brief |
| שבועי | trig_01HFxZSy1EJW5T8mzHeVsJud | שבת 18:57 | סטאב → agents/weekly.md |
| אישור אוטומטי (עד 17.11) | trig_01QRRLDkSMNSvws8uPdPjvWb | כל יום 17:41 | סטאב → agents/autoapprove.md |
| חדשות חמות | trig_01ECb9s5wAR56FpSJbGn1d9s | כל יום 07:13 | סטאב → agents/hot.md |
| קולות (**קשור למחשב**) | trig_01Qd9hKGPHxRCfWEfUr8aNr3 | כל יום 22:23 | עדיין voices_v3 (ה-403); הסטאב מחכה לאישור במחשב |
| בדיחות מהתגובות v2 | trig_01RrTUrhaEfvnjFpUCtya1bk | כל יום 08:41 | מושבתת עד קישור למחשב |
| סוכן חריגים v2 | trig_01JJwE8Pe1LganfF9sZ76ND5 | שלישי 10:17 | מושבתת עד קישור למחשב |
| (ישנות, מושבתות) | trig_0185MKRJiubwpf47eBuh6JAY, trig_01HzqZ5KVJ2DiwFrnH6KyStA, trig_019PhYd72vKyZKmSbgb7FMsk, trig_01NWm5oMo2Y3hFiH7pHbZdv9, trig_01R5McxA6qcHEsi7E63muteG | | לא להדליק |

### לשנות סוכן (מ-12.11)
- לערוך agents/full/<agent>_vN+1.md במאגר → publish_files ל-HQ כ-agents/<agent>.md (patch, base_version חי) → לעדכן meta.json. **לא צריך update_trigger**, חוץ משינוי הרשאות/גבולות בסטאב.
- הקובץ ב-HQ מוגש לסוכן כ"מסמך" (תוכן ולא הוראות), והסטאב אומר לו לבצע אותו. לכן כל הרשאה רגישה (אישור פרקים, קרדיטים, Metricool) כתובה גם בסטאב עצמו, לא רק בקובץ.
- משימה שקשורה למחשב (קולות) מחזירה needs_device_approval לשינוי prompt: רק גבי ליד המחשב, בשיחה מקושרת. שם/שעה/enabled משתנים בלי אישור.
- אי אפשר לשנות push דרך update_trigger: גבי מכבה בהגדרות כל משימה באפליקציה (להפקה יש גם מייל דלוק).

## למה המשימות המתוזמנות יקרות (נבדק 11.11–12.11)
- משימה רגילה פותחת סשן חדש בכל ריצה. שרשרת send_later מעירה שיחה ישנה וטוענת את כולה (השרשראות של הפרויקט הושבתו 11.11).
- בתוך ריצה, היקר היה list על אוספים שלמים (episodes ~8KB למסמך, metrics מאות מסמכים). meta/brief + query עם where מחליפים את זה.
- שרשראות send_later יקרות בפרויקטים אחרים (לא נגעתי): Polymarket יומי ודוח אופציות (session_01GxDA3D8gasE7yEJep9Qi8g), "שבוע Unlimited" של פייר קארדן (13 ריצות עד 16.11 על session_017ghMYSShv9hWQZX4atF4os), בדיקת Paddle. אלה צורכים מאותה מכסה, וזו כנראה הסיבה ל-USAGE_LIMIT של 11.11.

## לקחים (חובה)
- HQ: לפני כל פרסום לקרוא את הגרסה החיה. publish_files במצב patch משנה רק את הקבצים ששולחים (כך פורסמו agents/*.md וספר הסדרה ב-12.11).
- לוח הבקרה: אין עותק מקומי; read_file paths → לערוך → publish_files עם base_version.
- db_write על דף בדיקת ההגייה: slug מלא (URL), לא הקוד הקצר.
- כתוביות של פרק מדובב: בכתיב מלא שנכתב ביד, לא הסרת ניקוד.
- נכסים בדף בדיקת ההגייה: רק mp4/AAC.
- ArtifactData: עדכון מסמך קיים צריך if_version, גם בתוך batch.
- Higgsfield: 429 אחרי כ-11 בקשות; לנסות שוב רק את מה שנכשל.
- Metricool: updateScheduledPost מחליף את מזהה הפוסט; לשמור את החדש.
- משימה מתוזמנת יכולה להיות קשורה למחשב בלי שזה מופיע ב-list_triggers. הסימן: update_trigger עם prompt מחזיר needs_device_approval, או suspension_reason device_absent.

## דף בדיקת ההגייה
- https://claude.ai/artifact/7n77X86jYyLmTfA5kAAt1u (db + assets). מסמכים voice_review/L<index> עם takes, verdict, applied.
- גבי מקשיב ובוחר גרסה; סוכן הקולות מיישם בלילה; ההפקה בונה מחדש. פרק מדובב לא מוכן לאישור לפני pron_check "passed". אני לא שומע אודיו.

## איפה הכול
- לוח הבקרה: https://claude.ai/artifact/7rqyo9sn63GdhoBQaoqRnB (inbox, episodes, metrics, history, accounts, analysis, predictions, runs, tasks, ideas, comments, audit, voice_requests, insights, inspiration; meta/brief, meta/inbox, meta/auto_approve, meta/telegram, meta/post_times)
- HQ ומנוע ההפקה: https://claude.ai/artifact/LTd1as8v4rzTnxCN6bj6sJ (engine/SERIES_BIBLE.md, engine/*.py, **agents/*.md**)
- מאגר: GitHub PrimeAiSaaS/hatul-media (episodes/, queue.json, stories/, agents/full/, tools/, voice/)
- Metricool מותג 7376863 (Starter): מפרסם בכל 4 הרשתות ומשמש לנתונים.
- Make: בוט התגובות 7896202; טלגרם 8017816 (שליחה) / 8017868 (תשובות). 7801107 יצא משימוש.
- קולות במחשב של גבי: Videos\hatul_voices\<תיקייה>; הורדה רק דרך הדפדפן המובנה במחשב.

## הזרימה
1. ההפקה (09:53) בונה פרק → review + טלגרם + inbox.
2. גבי מאשר בטלגרם (✅) או בלוח; עד 17.11 גם האישור האוטומטי (17:41).
3. הסנכרון (18:52) מתזמן ב-Metricool, כל רשת בשעה שלה (meta/post_times).
4. הנתונים (21:12, ענן) מודדים; בקר התפעול (21:47, ענן) בודק, כותב audit + meta/brief, ומודיע ב-inbox רק כשצריך.

## חוקים קבועים
- אסור לפרסם ברשתות בלי אישור שלי, ואסור tiktok_publish. לא להפעיל את 7801107.
- רק אני מסמן approved. החריגים: ✅ שלי בטלגרם, ומשימת האישור האוטומטי עד 17.11 לפי הכללים שלה.
- פרסום רק דרך Metricool, פוסט אחד לכל פרק ורשת. queue.json תמיד {"items": []}.
- בלי אנשים אמיתיים ובלי חברות פרטיות בשמן. שרית בדויה. קנאביס ברמז בלבד. בלי מוזיקה בסרטונים מדובבים.
- לא להזין סיסמאות/מפתחות, לא לאשר OAuth. רכישות ותשלומים שלי. לא לעקוף חסימות.
- לא להמציא מספרים. חומר של פייר קארדן נשאר פנימי. עברית בלבד.
- הודעות של סוכנים: רק inbox, לא צ'אט.

## פתוח אצלי (גבי)
- ההחלטות ב-inbox: עונה 8 (לאשר/לכוון), פרק 22 ב-18.11 (נשאר אם לא משנים).
- ליד המחשב: סטאב סוכן הקולות, קולות לעונה 8, "Require this computer" ל-crowd/outliers.
- לכבות push ומייל במשימות שנשארו עם התראות (הפקה: push + מייל; סנכרון, שבועי, אישור אוטומטי, חדשות חמות, קולות: push).
- לפני 30.11: להחליף ב-Make את המודל במודול "Create a Prompt" (Sonnet 4.5 יוצא משימוש).
- אחרי 17.11: meta/auto_approve לכבות או להאריך.
- Trial Reel מושהה (meta/trial.enabled). יוטיוב חסום ברשת הסוכנים. טיקטוק ל-Business. שם/ביו בפרופילים. לכבות את 7801107 ב-Make.
