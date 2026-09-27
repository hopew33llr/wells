from __future__ import annotations
import html, os
from datetime import datetime, timezone
from typing import Optional
try:
    from zoneinfo import ZoneInfo
    TEHRAN = ZoneInfo("Asia/Tehran")
except Exception:
    TEHRAN = timezone.utc

MIME_MAP = {
    ".jpg":"image/jpeg",".jpeg":"image/jpeg",".png":"image/png",".gif":"image/gif",
    ".webp":"image/webp",".bmp":"image/bmp",".mp4":"video/mp4",".mov":"video/quicktime",
    ".webm":"video/webm",".mkv":"video/x-matroska",".ogg":"audio/ogg",".mp3":"audio/mpeg",
    ".m4a":"audio/mp4",".wav":"audio/wav",".pdf":"application/pdf",".zip":"application/zip",
}
IMAGE_EXTS = {".jpg",".jpeg",".png",".gif",".webp",".bmp"}
VIDEO_EXTS = {".mp4",".mov",".webm",".mkv",".avi"}
AUDIO_EXTS = {".mp3",".m4a",".aac",".flac",".wav",".ogg",".oga"}
FILE_ICONS = {
    ".pdf":"PDF",".doc":"DOC",".docx":"DOC",".xls":"XLS",".xlsx":"XLS",
    ".ppt":"PPT",".pptx":"PPT",".zip":"ZIP",".rar":"RAR",".txt":"TXT",
}
MONTHS_FA = ["ژانویه","فوریه","مارس","آوریل","مه","ژوئن","ژوئیه","اوت","سپتامبر","اکتبر","نوامبر","دسامبر"]

def _local(v):
    if not isinstance(v, datetime): return None
    if v.tzinfo is None: v = v.replace(tzinfo=timezone.utc)
    try: return v.astimezone(TEHRAN)
    except Exception: return v

def _fmt_time(v):
    d = _local(v)
    return f"{d:%H:%M}" if d else ""

def _day_key(v):
    d = _local(v)
    return f"{d.year}-{d.month:02d}-{d.day:02d}" if d else "x"

def _day_label(v):
    d = _local(v)
    if not d: return "نامشخص"
    today = datetime.now(TEHRAN).date()
    delta = (d.date() - today).days
    if delta == 0: return "امروز"
    if delta == -1: return "دیروز"
    return f"{d.day} {MONTHS_FA[d.month-1]} {d.year}"

def _fmt_size(b):
    if not b: return ""
    if b < 1048576: return f"{b/1024:.1f} KB"
    if b < 1073741824: return f"{b/1048576:.1f} MB"
    return f"{b/1073741824:.1f} GB"

def _mime(p):
    return MIME_MAP.get(os.path.splitext(p)[1].lower(), "application/octet-stream")

def _media(msg):
    path = msg.get("media_path")
    if not path or not os.path.exists(path):
        if msg.get("media_skipped"):
            return '<p class="skipped">⚠️ فایل بزرگ‌تر از سقف مجاز است</p>'
        return ""
    rel = html.escape(msg.get("media_rel_path") or f"media/{os.path.basename(path)}")
    mt = msg.get("media_type","")
    ext = os.path.splitext(path)[1].lower()
    if mt=="image" or ext in IMAGE_EXTS:
        return f'<a href="{rel}" target="_blank"><img class="post-img" src="{rel}" loading="lazy" alt=""></a>'
    if mt=="video" or ext in VIDEO_EXTS:
        return f'<video class="post-video" controls preload="metadata"><source src="{rel}" type="{_mime(path)}"></video>'
    if mt=="audio" or ext in AUDIO_EXTS:
        name = html.escape(msg.get("media_name") or os.path.basename(path))
        return f'<div class="post-audio"><span>🎧 {name}</span><audio controls src="{rel}"></audio></div>'
    name = html.escape(msg.get("media_name") or os.path.basename(path))
    lbl = FILE_ICONS.get(ext,"FILE")
    size = _fmt_size(int(msg.get("media_size",0) or os.path.getsize(path)))
    return (f'<a class="post-doc" href="{rel}" download="{name}">'
            f'<span class="doc-icon">{lbl}</span>'
            f'<span class="doc-info"><b>{name}</b><small>{size}</small></span>'
            f'<span class="doc-dl">⭳</span></a>')

def _render_msg(msg, idx):
    text = html.escape(msg.get("text","") or "").replace("\n","<br>")
    media = _media(msg)
    if not media and not text:
        text = '<span class="empty-msg">پیام بدون محتوا</span>'
    views = int(msg.get("views",0) or 0)
    v_html = f'<span class="stat">👁 {views:,}</span>' if views else ""
    reacts = "".join(
        f'<span class="react">{html.escape(str(r.get("emoji","")))} {r.get("count",0)}</span>'
        for r in msg.get("reactions",[])
    )
    mt = msg.get("media_type","") or "متن"
    return (
        f'<article class="post" data-s="{html.escape((msg.get("text","") or "").casefold())}" '
        f'data-t="{html.escape(str(mt))}" id="m{idx}">'
        f'{media}'
        f'{"<p class=post-text>"+text+"</p>" if text else ""}'
        f'<footer class="post-foot">'
        f'<span class="reacts">{reacts}</span>'
        f'<span class="stats">{v_html}<span class="time">{_fmt_time(msg.get("date"))} <span class="ticks">✓✓</span></span></span>'
        f'</footer></article>'
    )

def _render_channel(ch, ci):
    name = html.escape(ch.get("name",""))
    uname = html.escape(ch.get("username","") or "")
    av = ch.get("avatar_rel_path","")
    av_html = (f'<img class="ch-av" src="{html.escape(av)}" alt="">' if av
               else f'<div class="ch-av fallback">{html.escape((name or "?")[:1])}</div>')
    msgs = ch.get("messages",[])
    rows, last = [], None
    for mi, m in enumerate(msgs):
        dk = _day_key(m.get("date"))
        if dk != last:
            rows.append(f'<div class="day-div" data-s="" data-t="__"><span>{_day_label(m.get("date"))}</span></div>')
            last = dk
        rows.append(_render_msg(m, ci*100000+mi))
    feed = "".join(rows) or '<p class="no-posts">پیامی برای نمایش نیست.</p>'
    sub = f'@{uname}' if uname else f'{len(msgs)} پیام'
    return (
        f'<section class="ch-section" id="ch{ci}" data-ch="{name}">'
        f'<div class="ch-head">'
        f'{av_html}'
        f'<div class="ch-head-info"><h2>{name}</h2><p>{sub}</p></div>'
        f'</div>'
        f'<div class="ch-feed">{feed}</div>'
        f'</section>'
    )

def _side_item(ch, ci):
    name = html.escape(ch.get("name","") or "بدون‌نام")
    uname = html.escape(ch.get("username","") or "")
    av = ch.get("avatar_rel_path","")
    av_html = (f'<img class="s-av" src="{html.escape(av)}" alt="">' if av
               else f'<div class="s-av fallback">{html.escape((name or "?")[:1])}</div>')
    cnt = len(ch.get("messages",[]))
    sub = f'@{uname}' if uname else f'{cnt} پیام'
    sk = html.escape(f'{name} {uname}'.casefold())
    return (
        f'<a class="s-item" href="#ch{ci}" data-target="ch{ci}" data-sk="{sk}">'
        f'{av_html}'
        f'<span class="s-info"><b>{name}</b><small>{sub}</small></span>'
        f'<span class="s-cnt">{cnt}</span>'
        f'</a>'
    )

def generate_html(channel_name=None, channel_avatar_path=None, messages=None,
                  msg_count=0, *, channels=None):
    if channels is None:
        channels = [{"name": channel_name or "", "avatar_rel_path": "media/avatar.jpg" if channel_avatar_path else "", "messages": messages or []}]
    title = html.escape(channel_name or (channels[0].get("name","") if channels else "Archive"))
    ch_html = "".join(_render_channel(ch, i) for i, ch in enumerate(channels))
    s_html  = "".join(_side_item(ch, i) for i, ch in enumerate(channels))
    total   = sum(len(ch.get("messages",[])) for ch in channels)
    nc = len(channels)

    return f"""<!doctype html>
<html lang="fa" dir="rtl">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<meta name="color-scheme" content="dark">
<title>{title}</title>
<style>
*, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0 }}
:root {{
  --c-bg:       #0d1117;
  --c-surface:  #161b22;
  --c-surface2: #1c2330;
  --c-border:   #21262d;
  --c-text:     #e6edf3;
  --c-muted:    #7d8590;
  --c-accent:   #00bcd4;
  --c-accent2:  #1a7bb5;
  --c-green:    #3fb950;
  --c-bubble:   #172130;
  --r-sm:       10px;
  --r-md:       14px;
  --r-lg:       18px;
  --sidebar-w:  288px;
  --safe-top:   env(safe-area-inset-top,0px);
  --safe-bot:   env(safe-area-inset-bottom,0px);
}}
html, body {{ height: 100%; background: var(--c-bg); color: var(--c-text);
  font-family: Vazirmatn, "Segoe UI", Tahoma, sans-serif; overflow: hidden; }}
::-webkit-scrollbar {{ width: 6px }}
::-webkit-scrollbar-track {{ background: transparent }}
::-webkit-scrollbar-thumb {{ background: var(--c-border); border-radius: 6px }}
::-webkit-scrollbar-thumb:hover {{ background: var(--c-muted) }}

/* ── Layout ── */
.shell {{ display: flex; height: 100vh; height: 100dvh; }}

/* ── Sidebar ── */
.sidebar {{
  width: var(--sidebar-w); flex: none;
  background: var(--c-surface);
  border-inline-start: 1px solid var(--c-border);
  display: flex; flex-direction: column;
  z-index: 200;
}}
.s-head {{
  padding: 14px 12px 10px;
  border-bottom: 1px solid var(--c-border);
  flex: none;
  padding-top: calc(14px + var(--safe-top));
}}
.brand {{ display: flex; align-items: center; gap: 10px; margin-bottom: 12px }}
.brand-icon {{
  width: 36px; height: 36px; border-radius: 10px; flex: none;
  background: linear-gradient(135deg, var(--c-accent), var(--c-accent2));
  display: grid; place-items: center; font-size: 16px; font-weight: 900; color: #03141c;
}}
.brand-copy h1 {{ font-size: 14px; font-weight: 700; letter-spacing: -.2px }}
.brand-copy small {{ color: var(--c-muted); font-size: 11px }}
.s-search-wrap {{ position: relative }}
.s-search {{
  width: 100%; background: var(--c-surface2);
  border: 1px solid var(--c-border); border-radius: 20px;
  color: var(--c-text); font-family: inherit; font-size: 12.5px;
  padding: 8px 34px 8px 12px; outline: none; transition: border-color .18s;
}}
.s-search:focus {{ border-color: var(--c-accent) }}
.s-search-ico {{ position: absolute; right: 11px; top: 9px; color: var(--c-muted); font-size: 13px; pointer-events: none }}
.s-list {{ flex: 1; overflow-y: auto; padding: 6px 4px }}
.s-item {{
  display: flex; align-items: center; gap: 9px;
  padding: 8px 8px; border-radius: var(--r-md);
  text-decoration: none; color: var(--c-text);
  margin-bottom: 1px; transition: background .14s;
  border: 1px solid transparent;
}}
.s-item:hover {{ background: var(--c-surface2) }}
.s-item.active {{
  background: var(--c-surface2);
  border-color: color-mix(in srgb, var(--c-accent) 30%, transparent);
  box-shadow: inset -3px 0 0 var(--c-accent);
}}
.s-item.hidden {{ display: none }}
.s-av {{ width: 40px; height: 40px; border-radius: 12px; object-fit: cover; flex: none }}
.s-av.fallback {{
  display: grid; place-items: center; font-weight: 800; font-size: 16px;
  background: linear-gradient(135deg, var(--c-accent), var(--c-accent2)); color: #03141c;
}}
.s-info {{ min-width: 0; flex: 1 }}
.s-info b {{ display: block; font-size: 12.5px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; font-weight: 600 }}
.s-info small {{ display: block; color: var(--c-muted); font-size: 11px; margin-top: 2px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap }}
.s-cnt {{ font-size: 10px; background: var(--c-accent); color: #03141c; border-radius: 10px; padding: 2px 6px; font-weight: 700; flex: none }}

/* ── Main content ── */
.content {{ flex: 1; min-width: 0; display: flex; flex-direction: column }}

.topbar {{
  flex: none; background: var(--c-surface);
  border-bottom: 1px solid var(--c-border);
  padding: calc(10px + var(--safe-top)) 14px 10px;
  display: flex; align-items: center; gap: 10px;
  position: relative; z-index: 10;
}}
.topbar::after {{
  content:""; position:absolute; bottom:-1px; inset-inline:0;
  height:1px; background:linear-gradient(90deg,transparent,var(--c-accent) 40%,transparent);
  opacity:.5;
}}
.menu-btn {{
  display: none; background: var(--c-surface2); border: 1px solid var(--c-border);
  color: var(--c-accent); width: 36px; height: 36px; border-radius: 9px;
  font-size: 16px; cursor: pointer; flex: none; align-items: center; justify-content: center;
}}
.top-title {{ flex: 1; min-width: 0 }}
.top-title h2 {{ font-size: 14px; font-weight: 700; overflow: hidden; text-overflow: ellipsis; white-space: nowrap }}
.top-title p {{ color: var(--c-muted); font-size: 11px; margin-top: 1px }}

.toolbar {{
  flex: none; background: var(--c-surface);
  border-bottom: 1px solid var(--c-border);
  padding: 10px 14px;
  display: flex; gap: 8px; align-items: center; flex-wrap: wrap;
}}
.q-wrap {{ flex: 1; min-width: 0; position: relative }}
.q-input {{
  width: 100%; background: var(--c-surface2);
  border: 1px solid var(--c-border); border-radius: 20px;
  color: var(--c-text); font-family: inherit; font-size: 13px;
  padding: 9px 36px 9px 12px; outline: none; transition: border-color .18s;
}}
.q-input:focus {{ border-color: var(--c-accent) }}
.q-ico {{ position: absolute; right: 12px; top: 10px; color: var(--c-muted); font-size: 14px; pointer-events: none }}
.filters {{ display: flex; gap: 6px; flex-wrap: wrap }}
.btn-f {{
  border: 1px solid var(--c-border); background: transparent;
  color: var(--c-muted); border-radius: 16px; padding: 7px 13px;
  font-size: 12px; font-family: inherit; cursor: pointer; transition: .15s; white-space: nowrap;
}}
.btn-f.on, .btn-f:hover {{ background: var(--c-accent); color: #03141c; border-color: var(--c-accent); font-weight: 600 }}

.scroll {{ flex: 1; overflow-y: auto; padding: 16px 14px calc(20px + var(--safe-bot)) }}
.info-bar {{ color: var(--c-muted); font-size: 11.5px; margin-bottom: 14px; padding: 0 2px }}
.info-bar b {{ color: var(--c-accent) }}

/* ── Channel section ── */
.ch-section {{ margin-bottom: 28px }}
.ch-head {{
  display: flex; align-items: center; gap: 12px;
  background: var(--c-surface); border: 1px solid var(--c-border);
  border-radius: var(--r-lg) var(--r-lg) 0 0;
  padding: 12px 14px; position: sticky; top: 0; z-index: 5;
}}
.ch-av {{ width: 46px; height: 46px; border-radius: 13px; object-fit: cover; flex: none }}
.ch-av.fallback {{
  display: grid; place-items: center; font-size: 20px; font-weight: 800;
  background: linear-gradient(135deg, var(--c-accent), var(--c-accent2)); color: #03141c;
}}
.ch-head-info {{ min-width: 0 }}
.ch-head-info h2 {{ font-size: 15px; font-weight: 700; overflow: hidden; text-overflow: ellipsis; white-space: nowrap }}
.ch-head-info p {{ color: var(--c-muted); font-size: 11.5px; margin-top: 2px }}
.ch-feed {{
  border: 1px solid var(--c-border); border-top: none;
  border-radius: 0 0 var(--r-lg) var(--r-lg);
  background: var(--c-bg);
  padding: 4px 0 8px;
}}

/* ── Day divider ── */
.day-div {{ display: flex; justify-content: center; padding: 14px 0 8px }}
.day-div span {{
  background: var(--c-surface2); border: 1px solid var(--c-border);
  color: var(--c-muted); font-size: 11px; padding: 4px 14px; border-radius: 12px;
}}

/* ── Post ── */
.post {{
  margin: 3px 10px;
  background: var(--c-bubble);
  border: 1px solid var(--c-border);
  border-radius: var(--r-md);
  overflow: hidden;
  transition: border-color .15s;
}}
.post:hover {{ border-color: color-mix(in srgb, var(--c-accent) 40%, transparent) }}
.post-img {{
  display: block; width: 100%; max-height: 460px;
  object-fit: cover; cursor: zoom-in;
}}
.post-video {{
  display: block; width: 100%; max-height: 460px; background: #000;
}}
.post-audio {{
  display: flex; flex-direction: column; gap: 8px;
  padding: 12px; background: var(--c-surface2);
  color: var(--c-muted); font-size: 12px;
}}
.post-audio audio {{ width: 100% }}
.post-doc {{
  display: flex; align-items: center; gap: 12px;
  padding: 12px; text-decoration: none; color: var(--c-text);
  background: var(--c-surface2);
}}
.doc-icon {{
  width: 40px; height: 40px; border-radius: 10px; flex: none;
  background: linear-gradient(135deg,var(--c-accent),var(--c-accent2));
  display: grid; place-items: center; font-size: 10px; font-weight: 800; color: #03141c;
}}
.doc-info {{ flex: 1; min-width: 0 }}
.doc-info b {{ display: block; font-size: 13px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap }}
.doc-info small {{ color: var(--c-muted); font-size: 11px }}
.doc-dl {{ color: var(--c-accent); font-size: 20px }}
.post-text {{
  padding: 10px 12px 4px;
  font-size: 14.5px; line-height: 1.7;
  word-break: break-word; white-space: pre-wrap;
}}
.empty-msg {{ color: var(--c-muted); font-style: italic }}
.skipped {{ color: var(--c-muted); font-size: 12px; padding: 10px 12px }}
.post-foot {{
  display: flex; align-items: center; justify-content: space-between;
  padding: 6px 12px 8px; gap: 8px;
}}
.reacts {{ display: flex; gap: 5px; flex-wrap: wrap }}
.react {{
  background: color-mix(in srgb, var(--c-accent) 12%, transparent);
  border: 1px solid color-mix(in srgb, var(--c-accent) 25%, transparent);
  border-radius: 10px; padding: 2px 8px; font-size: 11px; color: #aee8f0;
}}
.stats {{ display: flex; align-items: center; gap: 8px; flex-shrink: 0 }}
.stat {{ color: var(--c-muted); font-size: 11px }}
.time {{ color: var(--c-muted); font-size: 11px; display: flex; align-items: center; gap: 3px }}
.ticks {{ color: var(--c-green); font-size: 10px; letter-spacing: -1px }}
.no-posts {{ color: var(--c-muted); text-align: center; padding: 24px; font-size: 13px }}

/* ── Scroll to top ── */
.totop {{
  position: fixed; inset-inline-start: 16px;
  bottom: calc(20px + var(--safe-bot));
  width: 42px; height: 42px; border-radius: 50%;
  background: var(--c-surface2); border: 1px solid var(--c-border);
  color: var(--c-accent); font-size: 18px; cursor: pointer;
  display: grid; place-items: center; box-shadow: 0 4px 16px #00000060;
  z-index: 50; transition: opacity .2s; opacity: 0; pointer-events: none;
}}
.totop.vis {{ opacity: 1; pointer-events: auto }}

/* ── Lightbox ── */
.lbox {{
  position: fixed; inset: 0; background: #000000f0; z-index: 500;
  display: none; place-items: center; padding: 16px; cursor: zoom-out;
}}
.lbox.on {{ display: grid }}
.lbox img {{ max-width: 96vw; max-height: 94vh; object-fit: contain; border-radius: 10px }}

/* ── Backdrop (mobile sidebar) ── */
.backdrop {{
  display: none; position: fixed; inset: 0; z-index: 190;
  background: #00000088; backdrop-filter: blur(2px);
}}
.backdrop.on {{ display: block }}

/* ── Mobile ── */
@media (max-width: 860px) {{
  .menu-btn {{ display: flex }}
  .sidebar {{
    position: fixed; top: 0; bottom: 0;
    /* در RTL، sidebar از سمت راست وارد می‌شود */
    right: 0; left: auto;
    transform: translateX(100%);
    transition: transform .26s cubic-bezier(.4,0,.2,1);
    box-shadow: -4px 0 24px #00000070;
  }}
  .sidebar.open {{ transform: translateX(0) }}
  .post-img, .post-video {{ max-height: 320px }}
  .toolbar {{ gap: 6px }}
  .btn-f {{ padding: 6px 10px; font-size: 11px }}
}}
</style>
</head>
<body>

<div class="shell">

  <!-- Sidebar -->
  <aside class="sidebar" id="sidebar">
    <div class="s-head">
      <div class="brand">
        <div class="brand-icon">✦</div>
        <div class="brand-copy">
          <h1>آرشیو پیام‌ها</h1>
          <small>{nc} کانال · {total} پیام</small>
        </div>
      </div>
      <div class="s-search-wrap">
        <span class="s-search-ico">⌕</span>
        <input id="sSearch" class="s-search" type="search" placeholder="جست‌وجوی کانال...">
      </div>
    </div>
    <div class="s-list" id="sList">{s_html}</div>
  </aside>

  <!-- Main -->
  <main class="content">
    <header class="topbar">
      <button class="menu-btn" id="menuBtn">☰</button>
      <div class="top-title">
        <h2>آرشیو کانال‌ها</h2>
        <p>زمان‌ها به وقت تهران · {nc} کانال · {total} پیام</p>
      </div>
    </header>

    <div class="toolbar">
      <div class="q-wrap">
        <span class="q-ico">⌕</span>
        <input id="qInput" class="q-input" type="search" placeholder="جست‌وجو در پیام‌ها...">
      </div>
      <div class="filters">
        <button class="btn-f on" data-f="all">همه</button>
        <button class="btn-f" data-f="متن">متن</button>
        <button class="btn-f" data-f="image">عکس</button>
        <button class="btn-f" data-f="video">ویدئو</button>
      </div>
    </div>

    <div class="scroll" id="scroll">
      <p class="info-bar" id="infoBar">نمایش <b>{total}</b> پیام از <b>{nc}</b> کانال</p>
      {ch_html}
    </div>
  </main>
</div>

<!-- Backdrop -->
<div class="backdrop" id="backdrop"></div>

<!-- Scroll to top -->
<button class="totop" id="totop" aria-label="بازگشت به بالا">↑</button>

<!-- Lightbox -->
<div class="lbox" id="lbox"><img id="lboxImg" src="" alt=""></div>

<script>
(function(){{
  const sidebar  = document.getElementById('sidebar');
  const backdrop = document.getElementById('backdrop');
  const menuBtn  = document.getElementById('menuBtn');
  const scroll   = document.getElementById('scroll');
  const qInput   = document.getElementById('qInput');
  const infoBar  = document.getElementById('infoBar');
  const sSearch  = document.getElementById('sSearch');
  const totop    = document.getElementById('totop');
  const lbox     = document.getElementById('lbox');
  const lboxImg  = document.getElementById('lboxImg');
  const filters  = [...document.querySelectorAll('.btn-f')];
  const sItems   = [...document.querySelectorAll('.s-item')];
  const posts    = [...document.querySelectorAll('.post')];
  const sections = [...document.querySelectorAll('.ch-section')];

  let activeF = 'all';

  function openSidebar()  {{ sidebar.classList.add('open');  backdrop.classList.add('on'); }}
  function closeSidebar() {{ sidebar.classList.remove('open'); backdrop.classList.remove('on'); }}
  menuBtn.addEventListener('click', openSidebar);
  backdrop.addEventListener('click', closeSidebar);
  sItems.forEach(a => a.addEventListener('click', closeSidebar));

  // Search + filter
  function refilter() {{
    const q = (qInput.value || '').trim().toLocaleLowerCase();
    let vPosts = 0, vSections = 0;
    sections.forEach(sec => {{
      let shown = 0;
      const chName = (sec.dataset.ch || '').toLocaleLowerCase();
      sec.querySelectorAll('.post').forEach(p => {{
        const okT = activeF === 'all' || p.dataset.t === activeF;
        const okQ = !q || chName.includes(q) || (p.dataset.s || '').includes(q);
        p.hidden = !(okT && okQ);
        if (!p.hidden) shown++;
      }});
      sec.querySelectorAll('.day-div').forEach(d => {{
        let sib = d.nextElementSibling, has = false;
        while (sib && !sib.classList.contains('day-div')) {{
          if (!sib.hidden) {{ has = true; break; }} sib = sib.nextElementSibling;
        }}
        d.hidden = !has;
      }});
      sec.hidden = !shown;
      if (shown) {{ vSections++; vPosts += shown; }}
    }});
    infoBar.innerHTML = `نمایش <b>${{vPosts}}</b> پیام از <b>${{vSections}}</b> کانال`;
  }}

  qInput.addEventListener('input', refilter);
  filters.forEach(btn => btn.addEventListener('click', () => {{
    filters.forEach(b => b.classList.remove('on'));
    btn.classList.add('on');
    activeF = btn.dataset.f;
    refilter();
  }}));

  // Sidebar channel search
  sSearch.addEventListener('input', () => {{
    const q = (sSearch.value || '').trim().toLocaleLowerCase();
    sItems.forEach(a => a.classList.toggle('hidden', q ? !(a.dataset.sk || '').includes(q) : false));
  }});

  // Scroll to top button
  scroll.addEventListener('scroll', () => totop.classList.toggle('vis', scroll.scrollTop > 300));
  totop.addEventListener('click', () => scroll.scrollTo({{top:0,behavior:'smooth'}}));

  // Lightbox
  document.addEventListener('click', e => {{
    const img = e.target.closest('.post-img');
    if (img) {{ lboxImg.src = img.src; lbox.classList.add('on'); e.preventDefault(); }}
  }});
  lbox.addEventListener('click', () => {{ lbox.classList.remove('on'); lboxImg.src = ''; }});
  document.addEventListener('keydown', e => {{ if (e.key === 'Escape') lbox.classList.remove('on'); }});

  // Sidebar active highlight on scroll
  if ('IntersectionObserver' in window) {{
    const byId = Object.fromEntries(sItems.map(a => [a.dataset.target, a]));
    new IntersectionObserver(entries => {{
      entries.forEach(e => {{
        const a = byId[e.target.id];
        if (a) a.classList.toggle('active', e.isIntersecting);
      }});
    }}, {{root: scroll, rootMargin: '-30% 0px -60% 0px', threshold: 0}})
    .observe(...sections.length ? sections : [document.body]);
    sections.forEach(s => new IntersectionObserver(entries => {{
      entries.forEach(e => {{
        const a = byId[e.target.id];
        if (a) a.classList.toggle('active', e.isIntersecting);
      }});
    }}, {{root: scroll, rootMargin: '-30% 0px -60% 0px', threshold: 0}}).observe(s));
  }}
}})();
</script>
</body>
</html>"""
