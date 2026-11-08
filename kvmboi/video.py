from __future__ import annotations

import asyncio
import io
import time
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .async_client import AsyncKVMClient


class AsyncVideo:
    """Video/screenshot capture from the KVM device."""

    def __init__(self, client: AsyncKVMClient):
        self._client = client

    async def screenshot(self, save_to: str | Path | None = None) -> bytes:
        """Capture a JPEG screenshot of the current KVM screen.

        Works on both firmware generations: a real JPEG from
        streamer/snapshot when the KVM still serves one, otherwise the first
        frame decoded from the H.264 stream.

        Args:
            save_to: Optional file path to save the JPEG. Returns bytes regardless.

        Returns:
            JPEG image bytes.
        """
        data = await self._client._api_get_bytes("streamer/snapshot")
        if data[:2] != b"\xff\xd8":
            # Newer Comet firmware (RV1126 H.264 encoder) has no JPEG path:
            # streamer/snapshot returns whatever H.264 unit was encoded last
            # (usually an undecodable P-frame) while still claiming
            # image/jpeg. Decode a real frame from the live stream instead.
            data = await self._h264_frame_as_jpeg()
        if save_to is not None:
            Path(save_to).write_bytes(data)
        return data

    async def _h264_frame_as_jpeg(self, timeout: float = 15.0, idle: float = 0.5) -> bytes:
        """First decodable frame of /streamer/stream?mode=snapshot, as JPEG.

        That stream always opens with SPS + PPS + an IDR frame. The H.264
        parser emits a frame only once the next one starts, and a static
        screen may produce no next frame, so after `idle` seconds without
        bytes the parser and decoder are flushed. Needs PyAV and Pillow
        (`pip install kvmboi[screenshot]`).
        """
        try:
            import av
        except ImportError as e:  # pragma: no cover - environment dependent
            raise RuntimeError(
                "this KVM serves H.264 only; screenshots need `pip install av pillow`"
            ) from e
        codec = av.CodecContext.create("h264", "r")
        deadline = time.monotonic() + timeout

        def decode(packets):
            for packet in packets:
                for frame in codec.decode(packet):
                    return frame
            return None

        async with self._client._http.stream(
            "GET", "/streamer/stream", params={"mode": "snapshot"}, timeout=timeout
        ) as resp:
            resp.raise_for_status()
            chunks = resp.aiter_bytes()
            while time.monotonic() < deadline:
                try:
                    chunk = await asyncio.wait_for(chunks.__anext__(), idle)
                except (asyncio.TimeoutError, StopAsyncIteration):
                    chunk = None
                if chunk:
                    frame = decode(codec.parse(chunk))
                else:  # stream paused (static screen) or ended: flush
                    frame = decode(codec.parse(None))
                    if frame is None:
                        for frame in codec.decode(None):
                            break
                        else:
                            frame = None
                if frame is not None:
                    buf = io.BytesIO()
                    frame.to_image().save(buf, format="JPEG", quality=85)
                    return buf.getvalue()
        raise TimeoutError(f"no decodable H.264 frame within {timeout}s")

    async def streamer_info(self) -> dict:
        """Get current video streamer state (resolution, fps, encoder, etc)."""
        return await self._client._api_get("streamer")
