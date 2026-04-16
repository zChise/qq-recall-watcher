import asyncio
import json
from typing import Callable

import websockets


class NapCatClient:
    def __init__(self, ws_url: str, on_message: Callable, on_recall: Callable, token: str = ""):
        self.ws_url = ws_url
        self.token  = token
        self._on_message = on_message
        self._on_recall  = on_recall

    async def run(self):
        url = self.ws_url
        if self.token:
            sep = "&" if "?" in url else "?"
            url = f"{url}{sep}access_token={self.token}"
        while True:
            try:
                print(f"[ws] connecting → {self.ws_url}")
                async with websockets.connect(url, ping_interval=20) as ws:
                    print("[ws] connected")
                    async for raw in ws:
                        try:
                            await self._dispatch(json.loads(raw))
                        except Exception as e:
                            print(f"[ws] dispatch error: {e}")
            except Exception as e:
                print(f"[ws] disconnected: {e} — retry in 5s")
                await asyncio.sleep(5)

    async def _dispatch(self, data: dict):
        post_type = data.get("post_type")
        if post_type == "message":
            print(f"[debug] message: id={data.get('message_id')} from={data.get('user_id')} type={data.get('message_type')}")
            await self._on_message(data)
        elif post_type == "notice":
            print(f"[debug] notice: {data.get('notice_type')} | msg_id={data.get('message_id')} | raw={data}")
            if data.get("notice_type") in ("group_recall", "friend_recall"):
                await self._on_recall(data)
        elif post_type not in ("meta_event", None):
            print(f"[debug] unhandled post_type={post_type}")
