import asyncio
import os
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class BufferedMessage:
    msg_id:           int
    chat_type:        str            # 'group' or 'private'
    group_id:         Optional[int]
    group_name:       str
    user_id:          int
    sender_name:      str
    content:          list
    timestamp:        float
    media_tasks:      List[asyncio.Task] = field(default_factory=list)
    downloaded_files: Dict[str, str]    = field(default_factory=dict)


class MessageBuffer:
    def __init__(self, ttl_seconds: int = 120):
        self.ttl = ttl_seconds
        self._data: Dict[int, BufferedMessage] = {}
        self._lock = asyncio.Lock()

    async def add(self, msg: BufferedMessage):
        async with self._lock:
            self._data[msg.msg_id] = msg

    async def pop(self, msg_id: int) -> Optional[BufferedMessage]:
        async with self._lock:
            return self._data.pop(msg_id, None)

    async def cleanup(self) -> int:
        now = time.time()
        async with self._lock:
            expired = [
                mid for mid, msg in self._data.items()
                if now - msg.timestamp > self.ttl
            ]
            for mid in expired:
                msg = self._data.pop(mid)
                for task in msg.media_tasks:
                    if not task.done():
                        task.cancel()
                for path in msg.downloaded_files.values():
                    try:
                        os.remove(path)
                    except OSError:
                        pass
        return len(expired)
