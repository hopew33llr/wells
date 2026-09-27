"""تولید خروجی HTML چندکاناله با ظاهر شبیه اپ تلگرام (دسکتاپ) + تم futuristic.

خروجی کاملاً آفلاین و تک‌فایلی است (بدون هیچ منبع خارجی)، شامل:
- ستون کناری با فهرست کانال‌ها (مثل لیست چت‌های تلگرام) برای پرش سریع بین کانال‌ها
- نمای پیام‌ها با حباب‌های شبیه تلگرام
- جست‌وجو و فیلتر نوع پیام + جست‌وجوی کانال در ستون کناری
- لایت‌باکس تصاویر، دکمهٔ بازگشت به بالا، و طراحی واکنش‌گرا برای موبایل
"""

from __future__ import annotations

import html
import os
from datetime import datetime, timezone
from typing import Optional
from zoneinfo import ZoneInfo

TEHRAN = ZoneInfo("Asia/Tehran")
MIME_MAP = {
    ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png",
    ".gif": "image/gif", ".webp": "image/webp", ".bmp": "image/bmp",
    ".mp4": "video/mp4", ".mov": "video/quicktime", ".webm": "video/webm",
    ".mkv": "video/x-matroska", ".ogg": "audio/ogg", ".mp3": "audio/mpeg",
    ".m4a": "audio/mp4", ".wav": "audio/wav", ".pdf": "application/pdf",
    ".zip": "application/zip", ".rar": "application/x-rar-compressed",
    ".doc": "application/msword", ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ".xls": "application/vnd.ms-excel", ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    ".ppt": "application/vnd.ms-powerpoint", ".pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    ".txt": "text/plain",
}
IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp"}
VIDEO_EXTS = {".mp4", ".mov", ".webm", ".mkv", ".avi"}
AUDIO_EXTS = {".mp3", ".m4a", ".aac", ".flac", ".wav", ".ogg", ".oga"}
FILE_ICONS = {
    ".pdf": "PDF", ".doc": "DOC", ".docx": "DOC", ".xls": "XLS",
    ".xlsx": "XLS", ".ppt": "PPT", ".pptx": "PPT", ".zip": "ZIP",
    ".rar": "RAR", ".txt": "TXT",
}
WEEKDAYS_FA = ["دوشنبه", "سه‌شنبه", "چهارشنبه", "پنجشنبه", "جمعه", "شنبه", "یکشنبه"]
MONTHS_FA = [
    "ژانویه", "فوریه", "مارس", "آوریل", "مه", "ژوئن",
    "ژوئیه", "اوت", "سپتامبر", "اکتبر", "نوامبر", "دسامبر",
]


def _mime(path: str) -> str:
    return MIME_MAP.get(os.path.splitext(path)[1].lower(), "application/octet-stream")


def _local(value: object) -> Optional[datetime]:
    if not isinstance(value, datetime):
        return None
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(TEHRAN)


def _format_time(value: object) -> str:
    local = _local(value)
    if not local:
        return html.escape(str(value or ""))
    return f"{local:%H:%M}"


def _day_key(value: object) -> str:
    local = _local(value)
    if not local:
        return "نامشخص"
    return f"{local.year:04d}-{local.month:02d}-{local.day:02d}"


def _day_label(value: object) -> str:
    local = _local(value)
    if not local:
        return "نامشخص"
    today = datetime.now(TEHRAN).date()
    delta = (local.date() - today).days
    if delta == 0:
        return "امروز"
    if delta == -1:
        return "دیروز"
    return f"{local.day} {MONTHS_FA[local.month - 1]} {local.year}"


def _format_size(value: int) -> str:
    if not value:
        return ""
    if value < 1024 * 1024:
        return f"{value / 1024:.1f} KB"
    if value < 1024 * 1024 * 1024:
        return f"{value / (1024 * 1024):.1f} MB"
    return f"{value / (1024 * 1024 * 1024):.1f} GB"


def _render_media(message: dict) -> str:
    path = message.get("media_path")
    if not path or not os.path.exists(path):
        if message.get("media_skipped"):
            return '<div class="skipped">⚠️ فایل بزرگ‌تر از سقف مجاز است</div>'
        return ""
    rel = html.escape(message.get("media_rel_path") or f"media/{os.path.basename(path)}")
    media_type = message.get("media_type", "")
    extension = os.path.splitext(path)[1].lower()
    if media_type == "image" or extension in IMAGE_EXTS:
        return f'<a class="bubble-media image-link" href="{rel}" target="_blank"><img class="media-image" src="{rel}" loading="lazy" alt=""></a>'
    if media_type == "video" or extension in VIDEO_EXTS:
        poster = message.get("media_poster", "")
        poster_attr = f' poster="{html.escape(poster)}"' if poster else ""
        return (
            f'<div class="bubble-media"><video class="media-video" controls preload="metadata"{poster_attr}>'
            f'<source src="{rel}" type="{_mime(path)}">مرورگر شما ویدئو را پشتیبانی نمی‌کند.</video></div>'
        )
    if media_type == "audio" or extension in AUDIO_EXTS:
        name = html.escape(message.get("media_name") or os.path.basename(path))
        return f'<div class="audio"><div class="media-label">🎧 {name}</div><audio controls preload="metadata" src="{rel}"></audio></div>'
    name = html.escape(message.get("media_name") or os.path.basename(path))
    label = FILE_ICONS.get(extension, "FILE")
    size = _format_size(int(message.get("media_size", 0) or os.path.getsize(path)))
    return (
        f'<a class="document" href="{rel}" download="{name}"><span class="file-icon">{label}</span>'
        f'<span class="file-copy"><b>{name}</b><small>{size}</small></span><span class="download">⭳</span></a>'
    )


def _render_message(message: dict, index: int) -> str:
    text = html.escape(message.get("text", "") or "").replace("\n", "<br>")
    reactions = "".join(
        f'<span class="reaction">{html.escape(str(item.get("emoji", "")))} {item.get("count", 0)}</span>'
        for item in message.get("reactions", [])
    )
    media_html = _render_media(message)
    has_media = bool(media_html) and "skipped" not in media_html
    text_html = f'<div class="bubble-text">{text}</div>' if text else ""
    if not media_html and not text:
        text_html = '<div class="bubble-text empty">رسانه یا متن قابل نمایش نیست</div>'
    type_name = "متن" if not message.get("media_type") else message.get("media_type")
    views = int(message.get("views", 0) or 0)
    views_html = f'<span class="views">👁 {views:,}</span>' if views else ""
    bubble_class = "bubble media-bubble" if has_media and not text else "bubble"
    return (
        f'<div class="msg-row" data-search="{html.escape((message.get("text", "") or "").casefold())}" '
        f'data-type="{html.escape(str(type_name))}" id="message-{index}">'
        f'<div class="{bubble_class}">'
        f'{media_html}{text_html}'
        f'<div class="meta"><span class="reactions">{reactions}</span>{views_html}'
        f'<span class="time">{_format_time(message.get("date"))}<span class="tick">✓✓</span></span></div>'
        f'</div></div>'
    )


def _render_channel(channel: dict, index: int) -> str:
    name = html.escape(channel.get("name", ""))
    username = html.escape(channel.get("username", ""))
    avatar = channel.get("avatar_rel_path", "")
    avatar_html = (
        f'<img class="avatar" src="{html.escape(avatar)}" alt="">'
        if avatar
        else f'<div class="avatar fallback">{html.escape((name or "?")[:1])}</div>'
    )
    messages = channel.get("messages", [])

    rows: list[str] = []
    last_day: Optional[str] = None
    for message_index, message in enumerate(messages):
        day_key = _day_key(message.get("date"))
        if day_key != last_day:
            rows.append(
                f'<div class="day-sep" data-search="" data-type="__day__">'
                f'<span>{_day_label(message.get("date"))}</span></div>'
            )
            last_day = day_key
        rows.append(_render_message(message, index * 100000 + message_index))
    messages_html = "".join(rows) or "<div class=\"empty-state small\">پیامی برای این کانال نیست.</div>"

    handle = f'<span>@{username}</span> · ' if username else ""
    return (
        f'<section class="channel" data-channel="{name}" id="channel-{index}">'
        f'<header class="chat-header">{avatar_html}<div class="chat-header-copy"><h2>{name}</h2>'
        f'<p>{handle}{len(messages)} پیام</p></div>'
        f'<a class="channel-link" href="#channel-{index}" aria-label="لینک کانال">#</a></header>'
        f'<div class="feed">{messages_html}</div></section>'
    )


def _render_sidebar_item(channel: dict, index: int) -> str:
    name = html.escape(channel.get("name", "") or "بدون‌نام")
    username = channel.get("username", "") or ""
    avatar = channel.get("avatar_rel_path", "")
    avatar_html = (
        f'<img class="side-avatar" src="{html.escape(avatar)}" alt="">'
        if avatar
        else f'<div class="side-avatar fallback">{html.escape((name or "?")[:1])}</div>'
    )
    count = len(channel.get("messages", []))
    subtitle = f"@{html.escape(username)}" if username else f"{count} پیام"
    search_key = html.escape(f"{name} {username}".casefold())
    return (
        f'<a class="side-item" href="#channel-{index}" data-target="channel-{index}" data-search="{search_key}">'
        f'{avatar_html}'
        f'<span class="side-copy"><b>{name}</b><small>{subtitle}</small></span>'
        f'<span class="side-count">{count}</span>'
        f'</a>'
    )


def generate_html(
    channel_name: Optional[str] = None,
    channel_avatar_path: Optional[str] = None,
    messages: Optional[list] = None,
    msg_count: int = 0,
    *,
    channels: Optional[list[dict]] = None,
) -> str:
    if channels is None:
        channels = [{
            "name": channel_name or "",
            "avatar_rel_path": "media/avatar.jpg" if channel_avatar_path else "",
            "messages": messages or [],
        }]
    title = html.escape(channel_name or (channels[0].get("name", "") if channels else "Archive"))
    channel_html = "".join(_render_channel(channel, index) for index, channel in enumerate(channels))
    sidebar_html = "".join(_render_sidebar_item(channel, index) for index, channel in enumerate(channels))
    total_messages = sum(len(channel.get("messages", [])) for channel in channels)
    return f"""<!doctype html>
<html lang="fa" dir="rtl">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="color-scheme" content="dark">
<title>{title}</title>
<style>
:root{{
  --bg:#05070b;--bg-grid:#ffffff08;--panel:#0c111a;--panel-2:#111826;--in-bubble:#101825;
  --line:#1b2434;--text:#e8edf5;--muted:#7e8ca1;
  --accent:#22d3ee;--accent-2:#3b82f6;--accent-soft:#22d3ee22;
  --tick:#3fd0a0;--radius:15px;--shadow:0 8px 26px #00000060;
  --glow:0 0 0 1px #22d3ee2e, 0 0 24px #22d3ee1f;
}}
*{{box-sizing:border-box}}
html{{scroll-behavior:smooth}}
::-webkit-scrollbar{{width:9px;height:9px}}
::-webkit-scrollbar-track{{background:transparent}}
::-webkit-scrollbar-thumb{{background:#1e2a3c;border-radius:8px}}
::-webkit-scrollbar-thumb:hover{{background:var(--accent-2)}}
body{{
  margin:0;height:100vh;color:var(--text);
  font-family:Vazirmatn,"Segoe UI",Tahoma,sans-serif;
  background-color:var(--bg);
  background-image:
    radial-gradient(circle at 12% 0%,#0d2230 0,transparent 42%),
    radial-gradient(circle at 100% 100%,#0a1c2c 0,transparent 40%),
    repeating-linear-gradient(90deg,var(--bg-grid) 0 1px,transparent 1px 64px),
    repeating-linear-gradient(0deg,var(--bg-grid) 0 1px,transparent 1px 64px);
  overflow:hidden;
}}
.app-shell{{display:flex;height:100vh;max-width:1400px;margin:0 auto;border-inline:1px solid var(--line)}}

.sidebar{{width:300px;flex:none;background:var(--panel);border-left:1px solid var(--line);
  display:flex;flex-direction:column;min-height:0}}
.side-head{{padding:16px 14px 12px;border-bottom:1px solid var(--line);flex:none}}
.brand{{display:flex;align-items:center;gap:12px;margin-bottom:12px}}
.brand-mark{{width:38px;height:38px;border-radius:11px;display:grid;place-items:center;
  background:linear-gradient(145deg,var(--accent),var(--accent-2));font-size:18px;font-weight:900;
  color:#03141c;flex:none;box-shadow:var(--glow)}}
.brand h1{{margin:0;font-size:15px;letter-spacing:-.2px}}
.brand small{{display:block;color:var(--muted);font-size:11px;margin-top:2px}}
.side-search-wrap{{position:relative}}
.side-search{{width:100%;background:var(--panel-2);border:1px solid var(--line);border-radius:10px;
  color:var(--text);padding:9px 34px 9px 12px;outline:none;font-size:12.5px;font-family:inherit;transition:.2s}}
.side-search:focus{{border-color:var(--accent);box-shadow:0 0 0 3px var(--accent-soft)}}
.side-search-wrap .search-icon{{position:absolute;right:11px;top:8px;color:var(--muted);font-size:14px}}

.side-list{{flex:1;overflow-y:auto;padding:6px}}
.side-item{{display:flex;align-items:center;gap:10px;padding:9px 8px;border-radius:11px;text-decoration:none;
  color:var(--text);margin-bottom:2px;transition:.15s;border:1px solid transparent}}
.side-item:hover{{background:var(--panel-2)}}
.side-item.active{{background:var(--panel-2);border-color:var(--accent-soft);box-shadow:inset 2px 0 0 var(--accent)}}
.side-item.filtered-out{{display:none}}
.side-avatar{{width:38px;height:38px;border-radius:11px;object-fit:cover;flex:none;border:1px solid #ffffff14}}
.side-avatar.fallback{{display:grid;place-items:center;background:linear-gradient(145deg,var(--accent),var(--accent-2));
  font-size:16px;font-weight:800;color:#03141c}}
.side-copy{{min-width:0;flex:1}}
.side-copy b{{display:block;font-size:12.5px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}}
.side-copy small{{display:block;color:var(--muted);font-size:10.5px;margin-top:2px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}}
.side-count{{color:var(--muted);font-size:10px;background:var(--panel);border:1px solid var(--line);
  border-radius:10px;padding:2px 7px;flex:none}}

.content{{flex:1;min-width:0;display:flex;flex-direction:column;min-height:0}}
.topbar{{flex:none;position:relative;z-index:20;padding:12px clamp(14px,3vw,32px);background:var(--panel);
  border-bottom:1px solid var(--line);box-shadow:var(--shadow)}}
.topbar::after{{content:"";position:absolute;left:0;right:0;bottom:-1px;height:1px;
  background:linear-gradient(90deg,transparent,var(--accent),transparent);opacity:.6}}
.topbar-inner{{display:flex;align-items:center;gap:14px;justify-content:space-between}}
.count{{color:var(--muted);font-size:12px;white-space:nowrap}}
.menu-toggle{{display:none;background:var(--panel-2);border:1px solid var(--line);color:var(--accent);
  width:34px;height:34px;border-radius:9px;font-size:15px;cursor:pointer;flex:none}}

.toolbar{{flex:none;padding:12px clamp(14px,3vw,32px) 0;display:grid;grid-template-columns:1fr auto;gap:10px}}
.search-wrap{{position:relative}}
.search{{width:100%;background:var(--panel);border:1px solid var(--line);border-radius:20px;color:var(--text);
  padding:11px 40px 11px 14px;outline:none;font-size:13px;font-family:inherit;transition:.2s}}
.search:focus{{border-color:var(--accent);box-shadow:0 0 0 3px var(--accent-soft)}}
.search-icon{{position:absolute;right:14px;top:11px;color:var(--muted);font-size:15px}}
.filters{{display:flex;gap:6px;align-items:center}}
.filter{{cursor:pointer;border:1px solid var(--line);background:var(--panel);color:var(--muted);
  border-radius:16px;padding:9px 12px;font-size:11px;font-family:inherit;transition:.15s}}
.filter.active,.filter:hover{{background:var(--accent);color:#04141c;border-color:var(--accent)}}

.summary{{flex:none;padding:10px clamp(14px,3vw,32px) 0;color:var(--muted);font-size:11px}}
.summary strong{{color:var(--accent)}}

.scroll-area{{flex:1;overflow-y:auto;padding:14px clamp(10px,3vw,26px) 30px}}
.channel{{max-width:760px;margin:18px auto 0}}
.chat-header{{display:flex;gap:12px;align-items:center;padding:10px 14px;background:var(--panel);
  border-bottom:1px solid var(--line);border-radius:13px 13px 0 0;position:sticky;top:0;z-index:6;box-shadow:var(--shadow)}}
.avatar{{width:44px;height:44px;border-radius:13px;object-fit:cover;flex:none;border:1px solid #ffffff14}}
.avatar.fallback{{display:grid;place-items:center;background:linear-gradient(145deg,var(--accent),var(--accent-2));
  font-size:19px;font-weight:800;color:#03141c}}
.chat-header-copy{{min-width:0;flex:1}}
.chat-header h2{{font-size:15px;margin:0 0 3px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}}
.chat-header p{{margin:0;color:var(--muted);font-size:11.5px}}
.channel-link{{color:var(--accent);text-decoration:none;font-size:16px;padding:6px 9px;border-radius:8px}}
.channel-link:hover{{background:var(--panel-2)}}

.feed{{background:var(--bg);padding:14px 8px 22px;display:flex;flex-direction:column;gap:2px;
  border-radius:0 0 13px 13px;border:1px solid var(--line);border-top:none}}

.day-sep{{display:flex;justify-content:center;margin:14px 0 10px}}
.day-sep span{{background:var(--panel-2);border:1px solid var(--line);color:var(--muted);font-size:11.5px;
  padding:5px 14px;border-radius:12px}}

.msg-row{{display:flex;justify-content:flex-end;padding:0 4px;margin:2px 0}}
.bubble{{
  position:relative;max-width:74%;background:var(--in-bubble);border:1px solid #ffffff0d;
  border-radius:var(--radius) var(--radius) 4px var(--radius);
  padding:7px 10px 6px 8px;box-shadow:0 2px 6px #00000040;transition:box-shadow .15s;
}}
.bubble:hover{{box-shadow:0 2px 6px #00000040, 0 0 0 1px var(--accent-soft)}}
.bubble::after{{
  content:"";position:absolute;bottom:0;left:-7px;width:14px;height:16px;background:var(--in-bubble);
  -webkit-mask:radial-gradient(circle at top left,transparent 14px,#000 14.5px);
  mask:radial-gradient(circle at top left,transparent 14px,#000 14.5px);
}}
.bubble-text{{font-size:14.5px;line-height:1.65;word-break:break-word;white-space:pre-wrap;padding:2px 3px 0}}
.bubble-text.empty{{color:var(--muted);font-style:normal}}
.bubble-media{{border-radius:9px;overflow:hidden;background:#060a10;margin-bottom:2px}}
.media-image{{display:block;width:100%;max-height:420px;object-fit:cover;cursor:zoom-in;border-radius:9px}}
.media-video{{display:block;width:100%;max-height:420px;border-radius:9px;background:#03060a}}
.media-bubble{{padding-bottom:4px}}
.audio{{background:var(--panel-2);border-radius:9px;padding:10px;color:var(--muted);font-size:11px;margin:2px 0}}
.audio audio{{display:block;width:100%;margin-top:8px}}
.document{{display:flex;align-items:center;gap:10px;background:var(--panel-2);border-radius:9px;padding:9px;
  color:var(--text);text-decoration:none;margin:2px 0;border:1px solid var(--line)}}
.file-icon{{width:38px;height:38px;border-radius:9px;background:linear-gradient(145deg,var(--accent),var(--accent-2));
  display:grid;place-items:center;font-size:9px;font-weight:800;color:#03141c;flex:none}}
.file-copy{{min-width:0;flex:1}}
.file-copy b{{display:block;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;font-size:12.5px}}
.file-copy small{{display:block;color:var(--muted);margin-top:3px}}
.download{{color:var(--accent);font-size:18px}}
.skipped{{color:var(--muted);font-size:12px;padding:8px 2px}}

.meta{{display:flex;align-items:center;justify-content:flex-end;gap:8px;margin-top:2px;padding:0 2px}}
.reactions:empty{{display:none}}
.reactions{{display:flex;gap:4px;flex-wrap:wrap}}
.reaction{{background:var(--accent-soft);border:1px solid var(--line);border-radius:10px;padding:1px 7px;
  font-size:10.5px;color:#bff3ff}}
.views{{color:var(--muted);font-size:10.5px}}
.time{{color:var(--muted);font-size:10.5px;display:inline-flex;align-items:center;gap:3px}}
.tick{{color:var(--tick);font-size:10px;letter-spacing:-1px}}

.empty-state{{max-width:720px;margin:50px auto;text-align:center;color:var(--muted);padding:30px}}
.empty-state.small{{margin:20px auto;padding:14px;font-size:12.5px}}
.top{{position:fixed;left:20px;bottom:20px;border:1px solid var(--line);background:var(--panel);
  color:var(--accent);width:40px;height:40px;border-radius:50%;cursor:pointer;font-size:17px;box-shadow:var(--shadow);z-index:15}}

.lightbox{{position:fixed;inset:0;background:#000000ee;z-index:40;display:grid;place-items:center;padding:20px;cursor:zoom-out}}
.lightbox img{{max-width:96vw;max-height:94vh;object-fit:contain;border-radius:10px;box-shadow:0 20px 80px #000}}

@media(max-width:900px){{
  .app-shell{{flex-direction:column;height:100vh}}
  .menu-toggle{{display:inline-flex;align-items:center;justify-content:center}}
  .sidebar{{position:fixed;inset:0 20% 0 0;z-index:50;transform:translateX(105%);transition:transform .25s ease;
    border-left:none;box-shadow:0 0 40px #000}}
  .sidebar.open{{transform:translateX(0)}}
  .content{{width:100%}}
  .bubble{{max-width:88%}}
  .channel{{margin-top:14px}}
}}
</style>
</head>
<body>
<div class="app-shell">
  <aside class="sidebar" id="sidebar">
    <div class="side-head">
      <div class="brand"><div class="brand-mark">✦</div><div><h1>آرشیو پیام‌ها</h1><small>{len(channels)} کانال · {total_messages} پیام</small></div></div>
      <div class="side-search-wrap"><span class="search-icon">⌕</span><input id="sideSearch" class="side-search" type="search" placeholder="جست‌وجوی کانال..." aria-label="جست‌وجوی کانال"></div>
    </div>
    <nav class="side-list" id="sideList">{sidebar_html or '<div class="empty-state small">کانالی موجود نیست.</div>'}</nav>
  </aside>
  <main class="content" id="content">
    <header class="topbar">
      <div class="topbar-inner">
        <button class="menu-toggle" id="menuToggle" aria-label="فهرست کانال‌ها">☰</button>
        <div class="count">زمان‌ها به وقت تهران · {len(channels)} کانال · {total_messages} پیام</div>
      </div>
    </header>
    <div class="toolbar">
      <div class="search-wrap"><span class="search-icon">⌕</span><input class="search" id="search" type="search" placeholder="جست‌وجو در پیام‌ها..." aria-label="جست‌وجو"></div>
      <div class="filters">
        <button class="filter active" data-filter="all">همه</button>
        <button class="filter" data-filter="متن">متن</button>
        <button class="filter" data-filter="image">عکس</button>
        <button class="filter" data-filter="video">ویدئو</button>
      </div>
    </div>
    <div class="summary" id="summary">نمایش <strong>{total_messages}</strong> پیام از <strong>{len(channels)}</strong> کانال</div>
    <div class="scroll-area" id="scrollArea">
      {channel_html or '<div class="empty-state">پیامی برای نمایش وجود ندارد.</div>'}
    </div>
    <button class="top" id="top" aria-label="بازگشت به بالا">↑</button>
  </main>
</div>
<script>
const search=document.getElementById("search"), filters=[...document.querySelectorAll(".filter")],
      channels=[...document.querySelectorAll(".channel")], summary=document.getElementById("summary"),
      sideSearch=document.getElementById("sideSearch"), sideItems=[...document.querySelectorAll(".side-item")],
      sidebar=document.getElementById("sidebar"), menuToggle=document.getElementById("menuToggle"),
      scrollArea=document.getElementById("scrollArea");
let active="all";

function apply(){{
  const q=(search.value||"").trim().toLocaleLowerCase();
  let visible=0,visibleChannels=0;
  channels.forEach(ch=>{{
    let shown=0;
    const channelName=(ch.dataset.channel||"").toLocaleLowerCase();
    ch.querySelectorAll(".msg-row").forEach(row=>{{
      const okType=active==="all"||row.dataset.type===active;
      const okText=!q||channelName.includes(q)||(row.dataset.search||"").includes(q);
      const visibleRow=okType&&okText;
      row.hidden=!visibleRow;
      if(visibleRow)shown++;
    }});
    ch.querySelectorAll(".day-sep").forEach(sep=>{{
      let node=sep.nextElementSibling,hasVisible=false;
      while(node&&!node.classList.contains("day-sep")){{
        if(!node.hidden){{hasVisible=true;break}}
        node=node.nextElementSibling;
      }}
      sep.hidden=!hasVisible;
    }});
    ch.hidden=!shown;
    if(shown)visibleChannels++;
    visible+=shown;
  }});
  summary.innerHTML=`نمایش <strong>${{visible}}</strong> پیام از <strong>${{visibleChannels}}</strong> کانال`;
}}
search.addEventListener("input",apply);
filters.forEach(btn=>btn.addEventListener("click",()=>{{filters.forEach(x=>x.classList.remove("active"));btn.classList.add("active");active=btn.dataset.filter;apply()}}));

document.getElementById("top").addEventListener("click",()=>scrollArea.scrollTo({{top:0,behavior:"smooth"}}));

document.addEventListener("click",event=>{{
  const image=event.target.closest(".media-image");
  if(!image)return;
  event.preventDefault();
  const layer=document.createElement("div");
  layer.className="lightbox";
  const copy=document.createElement("img");
  copy.src=image.src;
  layer.appendChild(copy);
  layer.onclick=()=>layer.remove();
  document.body.appendChild(layer);
}});

if(sideSearch){{
  sideSearch.addEventListener("input",()=>{{
    const q=(sideSearch.value||"").trim().toLocaleLowerCase();
    sideItems.forEach(item=>{{
      const ok=!q||(item.dataset.search||"").includes(q);
      item.classList.toggle("filtered-out",!ok);
    }});
  }});
}}

if(menuToggle){{
  menuToggle.addEventListener("click",()=>sidebar.classList.toggle("open"));
  sideItems.forEach(item=>item.addEventListener("click",()=>sidebar.classList.remove("open")));
}}

if("IntersectionObserver" in window && channels.length){{
  const byId=Object.fromEntries(sideItems.map(item=>[item.dataset.target,item]));
  const observer=new IntersectionObserver(entries=>{{
    entries.forEach(entry=>{{
      const item=byId[entry.target.id];
      if(!item)return;
      if(entry.isIntersecting)item.classList.add("active");
      else item.classList.remove("active");
    }});
  }},{{root:scrollArea,rootMargin:"-40% 0px -55% 0px",threshold:0}});
  channels.forEach(ch=>observer.observe(ch));
}}
</script>
</body>
</html>"""
