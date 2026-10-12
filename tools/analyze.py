#!/usr/bin/env python3
"""
analyze.py — deterministic analytics for "חתול בהמתנה".

Agents never estimate numbers in prose: they export the dashboard collections to JSON and run this,
then write the resulting docs back to the dashboard (collection "analysis").

Usage:
  # 1) export (ArtifactData list ... out_dir=<EXPORT>) the collections:
  #    episodes, metrics, history, predictions, accounts (accounts is optional)
  # 2) run:
  python3 tools/analyze.py <EXPORT> --out <OUT> [--now 2026-10-12T21:30:00+03:00]
  # 3) write <OUT>/analysis/*.json to the dashboard: collection "analysis", doc_id = file name (set, file_path)
  #    and paste <OUT>/report.md into the run summary / message.

Output docs
  analysis/ep<N>   one per episode that has any metrics (n >= 100 for specials: doc id = ep<n>)
  analysis/summary totals, platform mix, leaderboards, funnel, data gaps, diagnosis of the channel,
                   last_7d (views gained per platform from history, account/follower change from accounts)
Every number carries its source metrics doc + measured_at. Nothing is invented: a missing field stays missing.
"""
import argparse, glob, json, os, statistics
from datetime import datetime, timedelta, timezone

IL = timezone(timedelta(hours=3))  # Israel (IDT). Close enough for day buckets; Oct 25 → +02:00 handled by --now/ISO strings.
PLATFORMS = ["tiktok", "youtube", "instagram", "facebook"]

# Thresholds (Growth playbook §A/§G). Kept here so every agent uses the same numbers.
HOOK = {  # "the first seconds hold" per platform
    "tiktok":    ("retention", 30.0),        # avg watch % of length (no 3-s metric on TikTok)
    "youtube":   ("stayed_to_watch", 50.0),  # YT Studio "stayed to watch" (opposite of swiped away)
    "instagram": ("view_rate_3s", 40.0),     # IGRE28: % of views that lasted > 3 s
    "facebook":  ("retention", 30.0),
}
REQUIRED = {  # fields each platform's API can give; a missing one is a data gap to fix
    "tiktok": ("views", "avg_watch_sec", "retention", "completion_rate", "shares", "for_you_pct"),
    "youtube": ("views", "avg_watch_sec", "stayed_to_watch", "shares"),
    "instagram": ("views", "avg_watch_sec", "retention", "view_rate_3s", "shares", "saved"),
    "facebook": ("views", "avg_watch_sec", "retention"),
}
MIN_N = 100          # below this a platform result is "too early / not judgeable"
RET_GOOD = 50.0      # avg watch % that counts as "people stay"


def load_dir(root, coll):
    out = {}
    for f in glob.glob(os.path.join(root, coll, "*.json")):
        d = json.load(open(f, encoding="utf8"))
        out[os.path.basename(f)[:-5]] = d.get("data", d)
    return out


def num(x):
    try:
        return None if x is None or x == "" else float(x)
    except (TypeError, ValueError):
        return None


def r(x, nd=1):
    return None if x is None else round(x, nd)


def pub_time(ep):
    for k in ("posted_at", "published_at"):
        if ep.get(k):
            try:
                return datetime.fromisoformat(ep[k])
            except ValueError:
                pass
    if ep.get("publish_on"):
        return datetime.fromisoformat(ep["publish_on"] + "T20:30:00+03:00")
    return None


def per_1k(a, views):
    a, views = num(a), num(views)
    if a is None or not views:
        return None
    return a / views * 1000


def checkpoints(history, ep_n, platform, t_pub):
    """views at +1d / +3d / +7d from the daily history docs (nearest snapshot on or after the target day)."""
    series = []
    for date, h in history.items():
        for row in h.get("rows", []):
            if row.get("episode") == ep_n and row.get("platform") == platform and num(row.get("views")) is not None:
                series.append((date, num(row["views"])))
    series.sort()
    out = {"series": [{"date": d, "views": int(v)} for d, v in series]}
    if not t_pub or not series:
        return out
    for label, days in (("views_1d", 1), ("views_3d", 3), ("views_7d", 7)):
        target = (t_pub + timedelta(days=days)).date().isoformat()
        hit = next((v for d, v in series if d >= target), None)
        if hit is not None:
            out[label] = int(hit)
    if len(series) >= 2:
        (d0, v0), (d1, v1) = series[-2], series[-1]
        gap = max(1, (datetime.fromisoformat(d1) - datetime.fromisoformat(d0)).days)
        out["views_per_day_recent"] = r((v1 - v0) / gap, 1)
    return out


def diagnose(platform, m):
    """§G diagnosis order: fix only the FIRST failing step."""
    views = num(m.get("views"))
    if views is None:
        return {"step": "no_data", "text": "אין נתונים"}
    if views < MIN_N:
        return {"step": "too_early_or_distribution", "text": f"פחות מ-{MIN_N} צפיות: אי אפשר לשפוט (או שהפלטפורמה כמעט לא מפיצה)"}
    key, thr = HOOK[platform]
    hook_val = num(m.get(key))
    if hook_val is None and platform == "tiktok":
        hook_val = num(m.get("retention"))
    if hook_val is None:
        return {"step": "hook_unknown", "text": f"חסר {key}: אי אפשר לבדוק את הפתיחה"}
    if hook_val < thr:
        return {"step": "hook", "text": f"הפתיחה מאבדת אנשים: {key} {r(hook_val)} מתחת ל-{thr}"}
    ret = num(m.get("retention"))
    if ret is not None and ret < RET_GOOD and platform != "youtube":
        return {"step": "pacing", "text": f"עוברים את הפתיחה אבל נושרים באמצע: צפייה ממוצעת {r(ret)}%"}
    shares = num(m.get("shares")) or 0
    if shares == 0:
        return {"step": "share_trigger", "text": "צופים עד הסוף אבל לא משתפים: צריך טריגר שיתוף/תיוג"}
    return {"step": "topic_ceiling", "text": "החזקה ושיתוף טובים: להגדיל את הנושא (כאב גדול יותר)"}


def flat_nums(d, prefix=""):
    """numeric leaves of a nested dict as {"instagram.followers": 12, ...}"""
    out = {}
    for k, v in (d or {}).items():
        key = f"{prefix}{k}"
        if isinstance(v, dict):
            out.update(flat_nums(v, key + "."))
        elif num(v) is not None and not isinstance(v, bool):
            out[key] = num(v)
    return out


def window(history, accounts, now, days=7):
    """What happened in the last `days` days: views gained per platform/episode (history snapshots)
    and account changes (first vs last accounts doc in the window). Weekly agent reads this."""
    end = now.astimezone(IL).date()
    start = end - timedelta(days=days)
    s_iso, e_iso = start.isoformat(), end.isoformat()
    # latest snapshot per (episode, platform) at or before a date
    def snap(upto):
        out = {}
        for date in sorted(history):
            if date > upto:
                break
            for row in history[date].get("rows", []):
                v = num(row.get("views"))
                if v is not None and row.get("episode") is not None and row.get("platform") in PLATFORMS:
                    out[(int(row["episode"]), row["platform"])] = v
        return out
    a, b = snap(s_iso), snap(e_iso)
    gained, by_plat = [], {p: 0 for p in PLATFORMS}
    for key, v_end in b.items():
        g = v_end - a.get(key, 0)
        if g > 0:
            by_plat[key[1]] += g
            gained.append({"episode": key[0], "platform": key[1], "views_gained": int(g), "views_end": int(v_end)})
    gained.sort(key=lambda x: -x["views_gained"])
    out = {"from": s_iso, "to": e_iso, "views_gained": {p: int(v) for p, v in by_plat.items()},
           "views_gained_total": int(sum(by_plat.values())), "top_gainers": gained[:5],
           "history_days": len([d for d in history if s_iso < d <= e_iso])}
    acc = sorted(d for d in accounts if s_iso <= d <= e_iso)
    if acc:
        f, l = flat_nums(accounts[acc[0]]), flat_nums(accounts[acc[-1]])
        out["accounts"] = {"first": acc[0], "last": acc[-1], "days": len(acc),
                           "change": {k: r(l[k] - f[k], 1) for k in l if k in f and l[k] != f[k]},
                           "last_values": l}
    fol = [(d, history[d].get("followers")) for d in sorted(history) if s_iso <= d <= e_iso and history[d].get("followers")]
    if fol:
        f, l = flat_nums(fol[0][1]), flat_nums(fol[-1][1])
        out["followers"] = {"first": fol[0][0], "last": fol[-1][0], "start": f, "end": l,
                            "change": {k: r(l[k] - f[k], 0) for k in l if k in f}}
    return out


def analyze(export, now):
    episodes = load_dir(export, "episodes")
    metrics = load_dir(export, "metrics")
    history = load_dir(export, "history")
    preds_raw = load_dir(export, "predictions")
    # predictions are keyed ep<N> / sp1 / sp2 / react1: index them by their n field
    preds = {f"ep{int(d['n'])}": d for d in preds_raw.values() if num(d.get("n")) is not None}
    accounts = load_dir(export, "accounts")

    by_ep = {}
    for doc_id, m in metrics.items():
        n = m.get("episode")
        p = m.get("platform")
        if n is None or p not in PLATFORMS:
            continue
        by_ep.setdefault(int(n), {})[p] = (doc_id, m)

    # platform medians (for relative scores)
    med = {}
    for p in PLATFORMS:
        for k in ("views", "retention", "view_rate_3s", "stayed_to_watch", "avg_watch_sec"):
            vals = [num(by_ep[n][p][1].get(k)) for n in by_ep if p in by_ep[n]]
            vals = [v for v in vals if v is not None]
            if vals:
                med[(p, k)] = statistics.median(vals)

    docs, gaps = {}, []
    for n in sorted(by_ep):
        ep = episodes.get(f"ep{n}", {})
        t_pub = pub_time(ep)
        age_h = r((now - t_pub).total_seconds() / 3600, 1) if t_pub else None
        plats, total_views, total_likes, total_comments, total_shares, total_follows = {}, 0, 0, 0, 0, 0
        for p, (doc_id, m) in by_ep[n].items():
            t_p = t_pub
            if m.get("published_at"):  # per-platform publish time written by the data agent (Metricool date-with-time)
                try:
                    t_p = datetime.fromisoformat(m["published_at"])
                except ValueError:
                    pass
            v = num(m.get("views")) or 0
            total_views += v
            total_likes += num(m.get("likes")) or 0
            total_comments += num(m.get("comments")) or 0
            total_shares += num(m.get("shares")) or 0
            total_follows += num(m.get("follows")) or 0
            entry = {
                "source_doc": f"metrics/{doc_id}", "source": m.get("source"), "measured_at": m.get("measured_at"),
                "views": num(m.get("views")), "avg_watch_sec": num(m.get("avg_watch_sec")), "retention": num(m.get("retention")),
                "view_rate_3s": num(m.get("view_rate_3s")), "stayed_to_watch": num(m.get("stayed_to_watch")),
                "completion_rate": num(m.get("completion_rate")), "for_you_pct": num(m.get("for_you_pct")),
                "likes": num(m.get("likes")), "comments": num(m.get("comments")), "shares": num(m.get("shares")),
                "saved": num(m.get("saved")), "follows": num(m.get("follows")),
                "likes_per_1k": r(per_1k(m.get("likes"), m.get("views"))),
                "comments_per_1k": r(per_1k(m.get("comments"), m.get("views"))),
                "shares_per_1k": r(per_1k(m.get("shares"), m.get("views"))),
                "follows_per_1k": r(per_1k(m.get("follows"), m.get("views"))),
            }
            entry = {k: v for k, v in entry.items() if v is not None}
            rel = {}
            for k in ("views", "retention", "view_rate_3s", "stayed_to_watch"):
                if k in entry and med.get((p, k)):
                    rel[k] = r(entry[k] / med[(p, k)], 2)
            if rel:
                entry["vs_platform_median"] = rel
            if t_p:
                entry["published_at"] = t_p.isoformat()
                entry["age_hours"] = r((now - t_p).total_seconds() / 3600, 1)
            entry["checkpoints"] = checkpoints(history, n, p, t_p)
            entry["diagnosis"] = diagnose(p, m)
            missing = [k for k in REQUIRED[p] if num(m.get(k)) is None]
            if missing:
                entry["missing"] = missing
                gaps.append({"episode": n, "platform": p, "missing": missing})
            plats[p] = entry
        pr = preds.get(f"ep{n}") or {}
        doc = {
            "episode": n, "title": ep.get("title"), "published_at": t_pub.isoformat() if t_pub else None,
            "age_hours": age_h, "experiment": ep.get("experiment"),
            "totals": {"views": int(total_views), "likes": int(total_likes), "comments": int(total_comments),
                       "shares": int(total_shares), "follows": int(total_follows),
                       "engagement_per_1k": r(per_1k(total_likes + total_comments + total_shares, total_views))},
            "platforms": plats,
            "prediction": (pr.get("scores") or None),
            "computed_at": now.isoformat(), "tool": "tools/analyze.py",
        }
        if pr.get("scores") and plats:
            # hook score vs field hook metric, per platform (for §J calibration)
            cmp_ = {}
            for p, e in plats.items():
                key = HOOK[p][0]
                if key in e:
                    cmp_[p] = {"field_metric": key, "field": e[key], "hook_score": pr["scores"].get("hook_score")}
            if cmp_:
                doc["prediction_vs_field"] = cmp_
        docs[f"ep{n}"] = doc

    # ---- channel summary
    plat_tot = {p: 0 for p in PLATFORMS}
    for n in by_ep:
        for p, (_, m) in by_ep[n].items():
            plat_tot[p] += num(m.get("views")) or 0
    grand = sum(plat_tot.values())
    leaders = {}
    for p in PLATFORMS:
        for k in ("views", "retention", "view_rate_3s", "stayed_to_watch"):
            cands = [(num(by_ep[n][p][1].get(k)), n) for n in by_ep if p in by_ep[n] and num(by_ep[n][p][1].get(k)) is not None]
            if cands:
                best = max(cands)
                leaders[f"{p}.{k}"] = {"episode": best[1], "value": r(best[0])}
    tl = sum(d["totals"]["likes"] for d in docs.values())
    tc = sum(d["totals"]["comments"] for d in docs.values())
    ts = sum(d["totals"]["shares"] for d in docs.values())
    tf = sum(d["totals"]["follows"] for d in docs.values())
    steps = [e["diagnosis"]["step"] for d in docs.values() for e in d["platforms"].values()]
    judged = [s for s in steps if s not in ("too_early_or_distribution", "no_data", "hook_unknown")]
    channel_step = max(set(judged), key=judged.count) if judged else "too_early_or_distribution"
    acc_latest = {}
    if accounts:
        last = sorted(accounts)[-1]
        acc_latest = {"date": last, **accounts[last]}
    summary = {
        "episodes_measured": len(docs), "total_views": int(grand),
        "platform_views": {p: int(v) for p, v in plat_tot.items()},
        "platform_share_pct": {p: r(v / grand * 100) if grand else None for p, v in plat_tot.items()},
        "totals": {"likes": int(tl), "comments": int(tc), "shares": int(ts), "follows": int(tf),
                   "engagement_per_1k": r(per_1k(tl + tc + ts, grand)), "follows_per_1k": r(per_1k(tf, grand))},
        "leaders": leaders,
        "channel_diagnosis": {"step": channel_step, "counts": {s: steps.count(s) for s in set(steps)}},
        "data_gaps": gaps,
        "accounts_latest": acc_latest or None,
        "last_7d": window(history, accounts, now, 7),
        "computed_at": now.isoformat(), "tool": "tools/analyze.py",
    }
    return docs, summary


STEP_HE = {"hook": "הפתיחה", "pacing": "קצב באמצע", "share_trigger": "טריגר שיתוף", "topic_ceiling": "תקרת נושא",
           "too_early_or_distribution": "מוקדם/הפצה", "hook_unknown": "חסר מדד פתיחה", "no_data": "אין נתונים"}


def report(docs, summary):
    L = []
    L.append(f"סה״כ {summary['total_views']} צפיות ב-{summary['episodes_measured']} פרקים. "
             + " · ".join(f"{p} {summary['platform_views'][p]} ({summary['platform_share_pct'][p]}%)" for p in PLATFORMS))
    t = summary["totals"]
    L.append(f"לייקים {t['likes']}, תגובות {t['comments']}, שיתופים {t['shares']}, עוקבים מפרקים {t['follows']} "
             f"(מעורבות {t['engagement_per_1k']} ל-1,000 צפיות).")
    L.append(f"אבחון ערוץ (§G): {STEP_HE.get(summary['channel_diagnosis']['step'], summary['channel_diagnosis']['step'])}.")
    for k, d in sorted(docs.items(), key=lambda kv: kv[1]["episode"]):
        parts = []
        for p in PLATFORMS:
            e = d["platforms"].get(p)
            if not e:
                continue
            bits = [f"{int(e['views'])}" if "views" in e else "?"]
            for key, lab in (("retention", "צפ׳"), ("view_rate_3s", "3ש׳"), ("stayed_to_watch", "נשארו")):
                if key in e:
                    bits.append(f"{lab} {r(e[key])}%")
            parts.append(f"{p} " + " ".join(bits) + f" → {STEP_HE.get(e['diagnosis']['step'], '')}")
        L.append(f"פרק {d['episode']} ({d.get('title') or ''}, {d.get('age_hours')} ש׳): " + " | ".join(parts))
    w = summary.get("last_7d") or {}
    if w:
        L.append(f"7 ימים ({w['from']}–{w['to']}): +{w['views_gained_total']} צפיות · "
                 + " · ".join(f"{p} +{w['views_gained'][p]}" for p in PLATFORMS)
                 + (" · עוקבים: " + ", ".join(f"{k} {'+' if v >= 0 else ''}{int(v)}" for k, v in w["followers"]["change"].items()) if w.get("followers") else ""))
    if summary["data_gaps"]:
        L.append("חסר: " + "; ".join(f"פרק {g['episode']} {g['platform']}: {', '.join(g['missing'])}" for g in summary["data_gaps"]))
    return "\n".join(L)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("export")
    ap.add_argument("--out", required=True)
    ap.add_argument("--now")
    a = ap.parse_args()
    now = datetime.fromisoformat(a.now) if a.now else datetime.now(IL)
    docs, summary = analyze(a.export, now)
    os.makedirs(os.path.join(a.out, "analysis"), exist_ok=True)
    for k, d in docs.items():
        json.dump(d, open(os.path.join(a.out, "analysis", f"{k}.json"), "w", encoding="utf8"), ensure_ascii=False, indent=1)
    json.dump(summary, open(os.path.join(a.out, "analysis", "summary.json"), "w", encoding="utf8"), ensure_ascii=False, indent=1)
    rep = report(docs, summary)
    open(os.path.join(a.out, "report.md"), "w", encoding="utf8").write(rep + "\n")
    print(rep)


if __name__ == "__main__":
    main()
