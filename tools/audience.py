#!/usr/bin/env python3
"""Audience analysis for חתול בהמתנה: where viewers leave, what holds them, how followers grow.

Usage:
  python3 tools/audience.py <export_dir> --out <out_dir> [--now ISO]

<export_dir> has one folder per dashboard collection (episodes, metrics, accounts, arc), each with
<doc_id>.json files, exactly as ArtifactData list/out_dir writes them (same input as analyze.py).
Writes <out_dir>/analysis/audience_dropoff.json (doc for the dashboard) and prints a Markdown report.
Numbers only come from the export; nothing is estimated. Groups with fewer than 2 episodes are
reported as "n<2" and never used for a conclusion.
"""
import argparse, glob, json, os, statistics
from datetime import datetime, timedelta, timezone

MIN_VIEWS = 100        # below this a platform result is not judged
MIN_AGE_H = 72         # Reels/TikTok judged at 72 h (§O7)
HOLD_GOOD = 55.0       # Instagram 3-second hold that, so far, comes with ~10x reach
VOICED = {100, 102, 103, 104}
REACTION = {101}


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


def med(xs):
    xs = [x for x in xs if x is not None]
    return round(statistics.median(xs), 1) if xs else None


def spearman(x, y):
    pairs = [(a, b) for a, b in zip(x, y) if a is not None and b is not None]
    if len(pairs) < 4:
        return None
    def ranks(v):
        order = sorted(range(len(v)), key=lambda i: v[i]); r = [0] * len(v)
        for k, i in enumerate(order):
            r[i] = k
        return r
    rx, ry = ranks([p[0] for p in pairs]), ranks([p[1] for p in pairs])
    n = len(pairs); mx, my = sum(rx) / n, sum(ry) / n
    num_ = sum((a - mx) * (b - my) for a, b in zip(rx, ry))
    den = (sum((a - mx) ** 2 for a in rx) * sum((b - my) ** 2 for b in ry)) ** 0.5
    return round(num_ / den, 2) if den else None


def parse_t(s):
    try:
        t = datetime.fromisoformat(str(s).replace("Z", "+00:00"))
        return t if t.tzinfo else t.replace(tzinfo=timezone(timedelta(hours=2)))
    except Exception:
        return None


def fmt_of(n, ep):
    if ep.get("format"):
        return ep["format"]
    if n in VOICED:
        return "voiced"
    if n in REACTION:
        return "reaction"
    if n and n >= 200:
        return "arc"
    return "story_v2" if ep.get("story_v2") else "regular"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("export"); ap.add_argument("--out", required=True); ap.add_argument("--now")
    a = ap.parse_args()
    now = parse_t(a.now) if a.now else datetime.now(timezone.utc)
    eps = {}
    for k, e in load_dir(a.export, "episodes").items():
        if e.get("n") is not None:
            eps[int(e["n"])] = e
    mets = load_dir(a.export, "metrics")
    accs = load_dir(a.export, "accounts")
    arc = load_dir(a.export, "arc").get("current", {})

    rows = {}
    for m in mets.values():
        n = m.get("episode"); p = m.get("platform")
        if n is None or p is None or p == "instagram_trial":
            continue
        n = int(n); ep = eps.get(n, {})
        r = rows.setdefault(n, {"n": n, "title": ep.get("title"), "label": ep.get("label"), "publish_on": ep.get("publish_on"),
                                 "format": fmt_of(n, ep), "hook_a": (ep.get("trial") or {}).get("hook_a"),
                                 "hook_formula": ep.get("hook_formula"), "experiment": (ep.get("experiment") or {}).get("variable"),
                                 "story_score": (ep.get("story") or {}).get("score"), "break_type": (ep.get("story") or {}).get("break_type"),
                                 "platforms": {}})
        views = num(m.get("views")); aw = num(m.get("avg_watch_sec")); ret = num(m.get("retention"))
        dur = num(m.get("duration_sec")) or (round(aw / (ret / 100), 1) if aw and ret else None)
        hold = num(m.get("view_rate_3s"))
        if hold is None and p == "youtube":
            hold = num(m.get("stayed_to_watch"))
        if hold is None and p == "facebook" and num(m.get("views_3s")) and views:
            hold = round(100 * num(m["views_3s"]) / views, 1)
        pub = parse_t(m.get("published_at"))
        age_h = round((now - pub).total_seconds() / 3600) if pub else None
        sh = num(m.get("shares"))
        r["platforms"][p] = {
            "views": views, "hold_3s": hold, "retention": ret, "avg_watch_sec": aw, "duration_sec": dur,
            "leave_sec": (round(min(aw, dur), 1) if aw and dur else aw), "shares": sh,
            "shares_per_1k": (round(1000 * sh / views, 2) if sh is not None and views else None),
            "follows": num(m.get("follows")), "comments": num(m.get("comments")), "age_h": age_h,
            "judgeable": bool(views and views >= MIN_VIEWS and age_h is not None and age_h >= MIN_AGE_H),
        }

    out = {"measured_at": now.isoformat(timespec="minutes"), "by_platform": {}, "groups": {}, "episodes": [], "followers": {}, "notes": []}

    for p in ("instagram", "tiktok", "youtube", "facebook"):
        js = [r for r in rows.values() if r["platforms"].get(p, {}).get("judgeable")]
        pv = [r["platforms"][p] for r in js]
        reg = [r["platforms"][p] for r in js if r["format"] in ("regular", "story_v2")]
        d = {"n_judgeable": len(js), "median_views": med(x["views"] for x in pv),
             "median_hold_3s": med(x["hold_3s"] for x in pv), "median_retention": med(x["retention"] for x in pv),
             "median_leave_sec_regular": med(x["leave_sec"] for x in reg),
             "median_duration_regular": med(x["duration_sec"] for x in reg),
             "spearman_hold_vs_views": spearman([x["hold_3s"] for x in pv], [x["views"] for x in pv]),
             "spearman_retention_vs_views": spearman([x["retention"] for x in pv], [x["views"] for x in pv])}
        if p == "instagram":
            hi = [r for r in js if r["platforms"][p]["hold_3s"] is not None and r["platforms"][p]["hold_3s"] >= HOLD_GOOD]
            lo = [r for r in js if r["platforms"][p]["hold_3s"] is not None and r["platforms"][p]["hold_3s"] < HOLD_GOOD]
            d["hold_split"] = {"threshold": HOLD_GOOD,
                               "high": {"episodes": sorted(r["n"] for r in hi), "median_views": med(r["platforms"][p]["views"] for r in hi),
                                        "median_leave_sec": med(r["platforms"][p]["leave_sec"] for r in hi)},
                               "low": {"episodes": sorted(r["n"] for r in lo), "median_views": med(r["platforms"][p]["views"] for r in lo),
                                       "median_leave_sec": med(r["platforms"][p]["leave_sec"] for r in lo)}}
        out["by_platform"][p] = d

    def group(key):
        g = {}
        for r in rows.values():
            v = r.get(key)
            if v is None:
                continue
            for p in ("instagram", "tiktok"):
                x = r["platforms"].get(p)
                if x and x["judgeable"]:
                    g.setdefault(str(v), {}).setdefault(p, []).append(x)
        res = {}
        for v, byp in g.items():
            res[v] = {p: {"n": len(xs), "median_views": med(x["views"] for x in xs), "median_hold_3s": med(x["hold_3s"] for x in xs),
                          "median_retention": med(x["retention"] for x in xs), "median_leave_sec": med(x["leave_sec"] for x in xs),
                          "conclusive": len(xs) >= 2} for p, xs in byp.items()}
        return res
    for key in ("format", "hook_formula", "break_type", "experiment"):
        out["groups"][key] = group(key)

    # episodes that lose the viewer before the middle (Instagram, the network with full retention data)
    for r in sorted(rows.values(), key=lambda r: r["n"]):
        ig = r["platforms"].get("instagram", {})
        flag = None
        if ig.get("judgeable") and ig.get("leave_sec") and ig.get("duration_sec"):
            # strong = most of the episode watched, or 12+ seconds of watch time on a long (voiced) episode
            if ig["leave_sec"] >= 0.7 * ig["duration_sec"] or ig["leave_sec"] >= 12:
                flag = "strong"
            elif ig["leave_sec"] < 0.5 * ig["duration_sec"]:
                flag = "early_exit"
        out["episodes"].append({**r, "ig_flag": flag})

    # followers per network: latest value and change over 7 days
    hist = sorted(accs.values(), key=lambda d: str(d.get("date", "")))
    def series(net, field):
        s = []
        for d in hist:
            v = num((d.get(net) or {}).get(field))
            if v is not None:
                s.append((d.get("date"), v))
        return s
    for net, field in (("tiktok", "followers"), ("youtube", "subscribers"), ("instagram", "followers"), ("facebook", "page_followers")):
        s = series(net, field)
        if not s and net == "instagram" and (arc.get("manual") or {}).get("instagram"):
            mv = arc["manual"]["instagram"]
            s = [(str(mv.get("at", ""))[:10], num(mv.get("value")))]
        if s:
            last_d, last_v = s[-1]
            wk = [v for d, v in s if d and last_d and d <= (datetime.fromisoformat(last_d) - timedelta(days=7)).date().isoformat()]
            out["followers"][net] = {"value": last_v, "as_of": last_d, "change_7d": (last_v - wk[-1]) if wk else None,
                                     "source": "manual (Gabi)" if net == "instagram" and not series(net, field) else "metricool"}
    tot = sum(v["value"] for v in out["followers"].values() if v.get("value") is not None)
    views = sum((x.get("views") or 0) for r in rows.values() for x in r["platforms"].values())
    out["followers"]["total"] = tot
    out["followers"]["per_1k_views"] = round(1000 * tot / views, 2) if views else None
    ig_f = out["followers"].get("instagram")
    if ig_f and ig_f.get("as_of") and ig_f["as_of"] < (now - timedelta(days=7)).date().isoformat():
        out["notes"].append(f"Instagram followers are a manual value from {ig_f['as_of']}: ask Gabi for today's number.")

    os.makedirs(os.path.join(a.out, "analysis"), exist_ok=True)
    json.dump(out, open(os.path.join(a.out, "analysis", "audience_dropoff.json"), "w", encoding="utf8"), ensure_ascii=False, indent=1)

    # report
    L = ["# Audience report", f"measured_at {out['measured_at']} · judged = ≥{MIN_VIEWS} views and ≥{MIN_AGE_H} h", ""]
    for p, d in out["by_platform"].items():
        L.append(f"## {p}: n={d['n_judgeable']} · median views {d['median_views']} · hold3s {d['median_hold_3s']} · retention {d['median_retention']} · "
                 f"regular episodes leave at {d['median_leave_sec_regular']} s of {d['median_duration_regular']} s · "
                 f"spearman hold→views {d['spearman_hold_vs_views']}, retention→views {d['spearman_retention_vs_views']}")
        if d.get("hold_split"):
            hs = d["hold_split"]
            L.append(f"- hold ≥{hs['threshold']}%: eps {hs['high']['episodes']} median views {hs['high']['median_views']}, leave {hs['high']['median_leave_sec']} s")
            L.append(f"- hold <{hs['threshold']}%: eps {hs['low']['episodes']} median views {hs['low']['median_views']}, leave {hs['low']['median_leave_sec']} s")
    for key, g in out["groups"].items():
        if not g:
            continue
        L.append(f"## by {key}")
        for v, byp in sorted(g.items()):
            L.append(f"- {v}: " + " · ".join(f"{p} n={x['n']} views {x['median_views']} hold {x['median_hold_3s']} leave {x['median_leave_sec']}s{'' if x['conclusive'] else ' (n<2)'}" for p, x in byp.items()))
    L.append("## Instagram exit flags")
    for e in out["episodes"]:
        if e["ig_flag"]:
            ig = e["platforms"]["instagram"]
            L.append(f"- ep {e['n']} {e['title']}: {e['ig_flag']} · leaves at {ig['leave_sec']} s of {ig['duration_sec']} s · hold {ig['hold_3s']} · views {ig['views']}")
    L.append("## Followers")
    for net, v in out["followers"].items():
        L.append(f"- {net}: {v}")
    for n_ in out["notes"]:
        L.append(f"- NOTE: {n_}")
    print("\n".join(L))


if __name__ == "__main__":
    main()
