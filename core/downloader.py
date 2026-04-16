import asyncio
import hashlib
import os
import shutil
from pathlib import Path
from typing import Optional
from urllib.parse import unquote

import aiofiles
import aiohttp

MEDIA_DIR = Path("data/media")

# QQ CDN 需要这些 header 才肯给文件
_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Referer": "https://qq.com",
}


async def download_media_segment(url: str, msg_id: int, index: int, ext: str = "") -> Optional[str]:
    MEDIA_DIR.mkdir(parents=True, exist_ok=True)

    # NapCat 有时直接给本地文件路径 file:///C:/...
    if url.startswith("file:///"):
        return _copy_local(url, msg_id, index, ext)

    url_hash = hashlib.md5(url.encode()).hexdigest()[:8]
    filename = f"{msg_id}_{index}_{url_hash}{ext}"
    filepath = MEDIA_DIR / filename

    if filepath.exists():
        return str(filepath)

    try:
        # 视频可能很大，超时设 5 分钟
        timeout = aiohttp.ClientTimeout(total=300)
        async with aiohttp.ClientSession(timeout=timeout, headers=_HEADERS) as session:
            async with session.get(url) as resp:
                if resp.status == 200:
                    size = 0
                    async with aiofiles.open(filepath, "wb") as f:
                        async for chunk in resp.content.iter_chunked(65536):
                            await f.write(chunk)
                            size += len(chunk)
                    print(f"[dl] {filename} ({size // 1024} KB)")
                    return str(filepath)
                else:
                    print(f"[dl] HTTP {resp.status} | {url[:80]}")
    except asyncio.CancelledError:
        filepath.unlink(missing_ok=True)
        raise
    except Exception as e:
        print(f"[dl] failed: {e} | {url[:80]}")
    return None


def _copy_local(url: str, msg_id: int, index: int, ext: str) -> Optional[str]:
    # file:///C:/path/to/file.mp4  →  C:\path\to\file.mp4
    raw = unquote(url[8:])
    src = Path(raw.replace("/", os.sep))
    if not src.exists():
        print(f"[dl] local file not found: {src}")
        return None
    actual_ext = src.suffix or ext
    url_hash = hashlib.md5(url.encode()).hexdigest()[:8]
    dst = MEDIA_DIR / f"{msg_id}_{index}_{url_hash}{actual_ext}"
    shutil.copy2(src, dst)
    print(f"[dl] copied local: {dst.name}")
    return str(dst)
