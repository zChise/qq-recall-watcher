import asyncio
import json
import time
from pathlib import Path
from typing import Optional

import uvicorn

from core.buffer import BufferedMessage, MessageBuffer
from core.downloader import download_media_segment
from core.storage import get_unread_count, init_db, save_recalled
from core.ws_client import NapCatClient
from web.server import app, push_event

# ── Config ────────────────────────────────────────────────────────────────────

_cfg       = json.loads(Path("config.json").read_text(encoding="utf-8"))
NAPCAT_WS  = _cfg.get("napcat_ws", "ws://127.0.0.1:3001")
WEB_PORT   = _cfg.get("web_port", 8080)
BUFFER_SEC = _cfg.get("buffer_minutes", 2) * 60
MONITORED  = _cfg.get("monitored", "all")

buffer = MessageBuffer(ttl_seconds=BUFFER_SEC)

# ── Helpers ───────────────────────────────────────────────────────────────────

def _int(val) -> Optional[int]:
    try:
        return int(val)
    except (TypeError, ValueError):
        return None


def _should_monitor(data: dict) -> bool:
    if MONITORED == "all":
        return True
    return (_int(data.get("group_id")) in MONITORED or
            _int(data.get("user_id"))  in MONITORED)


def _extract_url(seg: dict) -> Optional[str]:
    d = seg.get("data", {})
    url = d.get("url") or d.get("file", "")
    if isinstance(url, str) and (url.startswith("http") or url.startswith("file:///")):
        return url
    return None


def _build_final_content(msg: BufferedMessage) -> list:
    result = []
    for i, seg in enumerate(msg.content):
        s = dict(seg)
        s["data"] = dict(s.get("data", {}))
        local = msg.downloaded_files.get(str(i))
        if local:
            s["data"]["local_file"] = Path(local).name
        result.append(s)
    return result

# ── Download task ─────────────────────────────────────────────────────────────

EXT_MAP = {"image": ".jpg", "video": ".mp4", "record": ".amr", "audio": ".amr"}

async def _download_seg(msg: BufferedMessage, index: int, seg_type: str, url: str):
    ext  = EXT_MAP.get(seg_type, "")
    path = await download_media_segment(url, msg.msg_id, index, ext)
    if path:
        msg.downloaded_files[str(index)] = path

# ── Event handlers ────────────────────────────────────────────────────────────

async def on_message(data: dict):
    if not _should_monitor(data):
        return
    msg_id = _int(data.get("message_id"))
    if not msg_id:
        return

    sender   = data.get("sender", {})
    segments = data.get("message", [])

    msg = BufferedMessage(
        msg_id      = msg_id,
        chat_type   = data.get("message_type", "group"),
        group_id    = _int(data.get("group_id")),
        group_name  = data.get("group_name", ""),
        user_id     = _int(data.get("user_id")) or 0,
        sender_name = sender.get("card") or sender.get("nickname", "未知"),
        content     = segments,
        timestamp   = time.time(),
    )

    for i, seg in enumerate(segments):
        url = _extract_url(seg)
        if url:
            task = asyncio.create_task(_download_seg(msg, i, seg.get("type", ""), url))
            msg.media_tasks.append(task)

    await buffer.add(msg)


async def on_recall(data: dict):
    msg_id = _int(data.get("message_id"))
    if not msg_id:
        return

    msg = await buffer.pop(msg_id)
    if not msg:
        print(f"[recall] msg_id={msg_id} not in buffer (expired or missed)")
        return

    pending = [t for t in msg.media_tasks if not t.done()]
    if pending:
        await asyncio.wait(pending, timeout=5)

    final_content = _build_final_content(msg)
    save_recalled(msg, final_content, time.time())

    unread = get_unread_count()
    await push_event("new_recall", {
        "sender_name": msg.sender_name,
        "unread": unread,
    })
    chat = msg.group_name or (f"群{msg.group_id}" if msg.group_id else "私聊")
    print(f"[recall] {msg.sender_name} @ {chat} | unread={unread}")

# ── Background cleanup ────────────────────────────────────────────────────────

async def _cleanup_loop():
    while True:
        await asyncio.sleep(30)
        n = await buffer.cleanup()
        if n:
            print(f"[buffer] purged {n} expired messages")

# ── Entry point ───────────────────────────────────────────────────────────────

async def main():
    init_db()
    loop = asyncio.get_running_loop()
    def _suppress_win64(loop, ctx):
        exc = ctx.get("exception")
        if isinstance(exc, OSError) and getattr(exc, "winerror", None) == 64:
            return
        loop.default_exception_handler(ctx)
    loop.set_exception_handler(_suppress_win64)
    token  = _cfg.get("token", "")
    client = NapCatClient(NAPCAT_WS, on_message, on_recall, token=token)
    server = uvicorn.Server(
        uvicorn.Config(app, host="127.0.0.1", port=WEB_PORT, log_level="warning")
    )
    print(f"[✓] Web UI → http://127.0.0.1:{WEB_PORT}")
    await asyncio.gather(client.run(), server.serve(), _cleanup_loop())


if __name__ == "__main__":
    asyncio.run(main())
