## שינוי בסעיף 0 (מחקר) — 12.10
- יש עכשיו פרק כל יום, אז בחר 5 נושאים בשבוע (לא 2) וכתוב 5 מסמכי ideas.

## 2א. כיול החיזוי (§J)
קרא predictions ו-metrics. לכל פרק עם 100+ צפיות בפלטפורמה, השווה את hook_score למדד הפתיחה (טיקטוק: צפייה ממוצעת %, יוטיוב: stayed_to_watch) ואת overall לצפייה הממוצעת. מ-3 פרקים ומעלה: מתאם דירוג (Spearman) והאם הכיוון נכון. כתוב meta/prediction_calibration {updated_at, n_episodes_with_field_data, summary, rules[], table[]}. פחות מ-3 פרקים: "עוד מוקדם", ושמור את הכללים הקיימים. כלל עובר ל-§I רק אחרי 3 פרקים שמסכימים עם השטח.

## 2ב. בקרת סוכנים (§K)
קרא tasks/* ו-runs/* של 7 הימים האחרונים. לכל סוכן (production, sync, publish, data, weekly, comments): רץ בזמן, אין failed בלי הסבר, ה-checks עוברים, ובדיקה מדגמית של מספר אחד מול המקור. כתוב audit/latest {at, items: [{agent, ok, note}]}. מחק runs/* מעל 30 יום. כל כישלון נכנס לדו"ח לגבי. בדוק גם שהיה פרסום בכל אחד מ-7 הימים (§L).

## 5. בקרה ויומן (חובה בסוף כל ריצה)
runs/<YYYYMMDD-HHMM>-weekly + tasks/weekly (triggerId trig_01C1LQMstEw3rfURCFvJi7yM, when "שבת 18:57").
