זו שיחה בפרויקט "חתול בהמתנה". ענה בעברית.

1. קרא את מסמך ידע הפרויקט: https://raw.githubusercontent.com/PrimeAiSaaS/hatul-media/main/PROJECT_CONTEXT.md

2. העבר לפרויקט הזה את 4 המשימות המתוזמנות של חתול בהמתנה. לכל אחת, צור משימה מתוזמנת חדשה (create_trigger) בפרויקט הזה, עם אותו שם ואותו תזמון, model claude-opus-5-5, והפעלה אוטומטית. ההנחיה המלאה של כל משימה = התוכן המדויק של הקובץ שלה (תעתיק אותו מילה במילה, בלי לקצר):
   - "חתול בהמתנה: הפקת פרק" · CRON_TZ=Asia/Jerusalem 53 9 * * * · https://raw.githubusercontent.com/PrimeAiSaaS/hatul-media/main/agents/full/production_v2.md
   - "חתול בהמתנה: סנכרון תור הפרסום" · CRON_TZ=Asia/Jerusalem 52 18 * * * · https://raw.githubusercontent.com/PrimeAiSaaS/hatul-media/main/agents/full/sync_v2.md
   - "חתול בהמתנה: סוכן נתונים" · CRON_TZ=Asia/Jerusalem 12 21 * * * · https://raw.githubusercontent.com/PrimeAiSaaS/hatul-media/main/agents/full/data_v2.md
   - "חתול בהמתנה: סיכום שבועי ושיפור" · CRON_TZ=Asia/Jerusalem 57 18 * * 6 · https://raw.githubusercontent.com/PrimeAiSaaS/hatul-media/main/agents/full/weekly_v2.md
   המשימות רצות בענן (לא צריכות את המחשב). הן צריכות את החיבורים Higgsfield, Make, Google Drive ו-Claude Docs.

3. רק אחרי שכל 4 החדשות נוצרו והן מופיעות ב-list_triggers עם התזמון הנכון, מחק את 4 הישנות: trig_01WTkwFNwrRswy1mdVxqLnss, trig_01AnctU5d7pN4UAFnCgk7gjX, trig_01YHZQp6p1QPxZirXtkAZ5hw, trig_01C1LQMstEw3rfURCFvJi7yM. אם משהו נכשל ביצירה, אל תמחק את הישנה של אותה משימה.

4. בלוח הבקרה (https://claude.ai/artifact/7rqyo9sn63GdhoBQaoqRnB, כלי ArtifactData) עדכן במסמכים tasks/production, tasks/sync, tasks/data, tasks/weekly את השדה triggerId למזהה החדש (get ואז update עם if_version).

5. סיים בטבלה: שם, מזהה חדש, תזמון, הריצה הבאה, ומה נמחק.
