// crowd_humor_scan.js — חתול בהמתנה: סריקת תגובות ברילסים/שורטס של אחרים (קריאה בלבד)
// Runs inside the built-in browser, in a tab on the matching site, via javascript_tool.
// Paste the whole file, then call one of the functions at the end of the same snippet.
// Never likes, follows, comments or sends anything. Pauses between requests.
// Copy of the project doc claude/crowd_humor_scan.js (11.11), so fresh-session runs can read it from the repo.

const sleep = ms => new Promise(r => setTimeout(r, ms));
const IG_APP = '936619743392459';
const B64 = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_';
const igId = sc => { let id = 0n; for (const c of sc) id = id * 64n + BigInt(B64.indexOf(c)); return String(id); };
const igGet = async path => {
  const r = await fetch(path, { headers: { 'x-ig-app-id': IG_APP }, credentials: 'include' });
  const t = await r.text();
  try { return { status: r.status, json: JSON.parse(t) }; } catch (e) { return { status: r.status, json: null, text: t.slice(0, 80) }; }
};

// Instagram, on https://www.instagram.com — recent reels of one account.
// returns {account, status, reels:[{code,url,taken_at,views,likes,comments,caption}]}
async function igRecentReels(username, max = 6) {
  const p = await igGet(`/api/v1/users/web_profile_info/?username=${encodeURIComponent(username)}`);
  const user = p.json && p.json.data && p.json.data.user;
  if (!user) return { account: username, status: p.status, error: 'profile not readable', reels: [] };
  await sleep(1500);
  const f = await igGet(`/api/v1/feed/user/${user.id}/?count=12`);
  const items = (f.json && f.json.items) || [];
  const reels = items.filter(i => i.product_type === 'clips').slice(0, max).map(i => ({
    code: i.code, url: `https://www.instagram.com/reel/${i.code}/`, taken_at: i.taken_at,
    views: i.play_count || i.ig_play_count || null, likes: i.like_count, comments: i.comment_count,
    caption: ((i.caption && i.caption.text) || '').slice(0, 160)
  }));
  return { account: username, status: f.status, followers: user.edge_followed_by && user.edge_followed_by.count, reels };
}

// Instagram — top-level comments of one reel/post (up to `pages` pages of ~15), sorted by likes.
// returns {code, status, total, comments:[{likes, replies, text, user}]}
async function igComments(code, pages = 3) {
  const id = igId(code); let min = null; const out = []; let status = 0, total = null;
  for (let i = 0; i < pages; i++) {
    const q = `/api/v1/media/${id}/comments/?can_support_threading=true&permalink_enabled=false` + (min ? `&min_id=${encodeURIComponent(min)}` : '');
    const r = await igGet(q); status = r.status; if (!r.json) break;
    total = r.json.comment_count;
    for (const c of r.json.comments || []) out.push({ likes: c.comment_like_count || 0, replies: c.child_comment_count || 0, text: c.text, user: c.user && c.user.username });
    min = r.json.next_min_id; if (!min) break; await sleep(2000);
  }
  out.sort((a, b) => b.likes - a.likes);
  return { code, status, total, comments: out.slice(0, 40) };
}

// Instagram keyword grid (fallback when no account list) — call on the keyword page after it loads.
function igGridCodes() {
  return [...new Set([...document.querySelectorAll('a[href*="/reel/"],a[href*="/p/"]')].map(a => a.getAttribute('href').split('/').filter(Boolean)[1]))];
}

// YouTube, on https://www.youtube.com — Shorts of a channel (handle like "@name") or a search.
async function ytShortsOfChannel(handle, max = 6) {
  const r = await fetch(`/${handle.replace(/^@?/, '@')}/shorts`); const h = await r.text();
  const ids = [...new Set([...h.matchAll(/"videoId":"([\w-]{11})"/g)].map(m => m[1]))].slice(0, max);
  return { handle, status: r.status, ids };
}
async function ytSearchShorts(q, max = 6) {
  const r = await fetch(`/results?search_query=${encodeURIComponent(q)}&sp=EgIYAQ%253D%253D`); const h = await r.text();
  const ids = [...new Set([...h.matchAll(/"videoId":"([\w-]{11})"/g)].map(m => m[1]))].slice(0, max);
  return { q, status: r.status, ids };
}

// YouTube — title, views and the first page (~20) of top comments with likes, sorted by likes.
async function ytComments(videoId) {
  const r = await fetch(`/watch?v=${videoId}`); const h = await r.text();
  const m = h.match(/var ytInitialData = (\{.*?\});<\/script>/s); if (!m) return { videoId, status: r.status, error: 'no initial data', comments: [] };
  const d = JSON.parse(m[1]);
  const title = (h.match(/<title>(.*?)<\/title>/) || [])[1];
  const views = (h.match(/"viewCount":"(\d+)"/) || [])[1];
  const channel = (h.match(/"ownerChannelName":"(.*?)"/) || [])[1];
  let tok = null;
  const walk = o => { if (tok || !o || typeof o !== 'object') return; if (o.continuationCommand && o.continuationCommand.request === 'CONTINUATION_REQUEST_TYPE_WATCH_NEXT') tok = o.continuationCommand.token; for (const k in o) walk(o[k]); };
  try { walk(d.contents.twoColumnWatchNextResults.results.results.contents.filter(c => c.itemSectionRenderer)); } catch (e) {}
  if (!tok) return { videoId, title, views, channel, error: 'comments off or not found', comments: [] };
  await sleep(1200);
  const rr = await fetch('/youtubei/v1/next?prettyPrint=false', { method: 'POST', headers: { 'content-type': 'application/json' }, body: JSON.stringify({ context: ytcfg.get('INNERTUBE_CONTEXT'), continuation: tok }) });
  const j = await rr.json(); const out = [];
  const num = s => { if (!s) return 0; s = s.replace(/[^\d.KMאלף]/g, ''); const n = parseFloat(s) || 0; return /K|אלף/.test(s) ? Math.round(n * 1000) : /M/.test(s) ? Math.round(n * 1e6) : n; };
  const w2 = o => { if (!o || typeof o !== 'object') return; if (o.commentEntityPayload) { const p = o.commentEntityPayload; out.push({ likes: num(p.toolbar && p.toolbar.likeCountNotliked), replies: num(p.toolbar && p.toolbar.replyCount), text: p.properties && p.properties.content && p.properties.content.content, user: p.author && p.author.displayName }); } for (const k in o) w2(o[k]); };
  w2(j); out.sort((a, b) => b.likes - a.likes);
  return { videoId, url: `https://www.youtube.com/shorts/${videoId}`, title, views: views ? +views : null, channel, status: rr.status, comments: out.slice(0, 40) };
}
