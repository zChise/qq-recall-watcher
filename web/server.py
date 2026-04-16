import asyncio
import json
from pathlib import Path
from typing import List, Optional

from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles

from core.storage import get_chat_list, get_messages, get_unread_count, mark_read, mark_all_read

app = FastAPI()
_subscribers: List[asyncio.Queue] = []

_MIME = {
    ".jpg":  "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png":  "image/png",
    ".gif":  "image/gif",
    ".webp": "image/webp",
    ".mp4":  "video/mp4",
    ".webm": "video/webm",
    ".mp3":  "audio/mpeg",
    ".ogg":  "audio/ogg",
    ".amr":  "audio/amr",
    ".silk": "audio/silk",
}


async def push_event(event_type: str, data: dict):
    payload = f"event: {event_type}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"
    for q in list(_subscribers):
        try:
            q.put_nowait(payload)
        except asyncio.QueueFull:
            pass


@app.get("/api/unread")
def api_unread():
    return {"count": get_unread_count()}


@app.get("/api/chats")
def api_chats():
    return get_chat_list()


@app.get("/api/messages")
def api_messages(page: int = 1,
                 group_id: Optional[int] = None,
                 user_id:  Optional[int] = None):
    return get_messages(page, group_id=group_id, user_id=user_id)


@app.post("/api/read/{msg_id}")
def api_mark_read(msg_id: int):
    mark_read(msg_id)
    return {"ok": True}


@app.post("/api/read-all")
def api_mark_all_read(group_id: Optional[int] = None, user_id: Optional[int] = None):
    mark_all_read(group_id=group_id, user_id=user_id)
    return {"ok": True}


@app.get("/api/media/{filename}")
def api_media(filename: str):
    path = Path("data/media") / filename
    if not path.exists():
        return JSONResponse({"error": "not found"}, status_code=404)
    ext        = path.suffix.lower()
    media_type = _MIME.get(ext, "application/octet-stream")
    return FileResponse(path, media_type=media_type)


@app.get("/events")
async def sse():
    q: asyncio.Queue = asyncio.Queue(maxsize=50)
    _subscribers.append(q)

    async def stream():
        try:
            yield "data: {\"type\":\"connected\"}\n\n"
            while True:
                try:
                    msg = await asyncio.wait_for(q.get(), timeout=25)
                    yield msg
                except asyncio.TimeoutError:
                    yield ": heartbeat\n\n"
        finally:
            try:
                _subscribers.remove(q)
            except ValueError:
                pass

    return StreamingResponse(
        stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


app.mount("/", StaticFiles(directory="web/static", html=True))
