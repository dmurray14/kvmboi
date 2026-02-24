from __future__ import annotations

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

        Args:
            save_to: Optional file path to save the JPEG. Returns bytes regardless.

        Returns:
            JPEG image bytes.
        """
        data = await self._client._api_get_bytes("streamer/snapshot")
        if save_to is not None:
            Path(save_to).write_bytes(data)
        return data

    async def streamer_info(self) -> dict:
        """Get current video streamer state (resolution, fps, encoder, etc)."""
        return await self._client._api_get("streamer")
