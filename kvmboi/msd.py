from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .async_client import AsyncKVMClient


class AsyncMSD:
    """Virtual media (Mass Storage Device) control."""

    def __init__(self, client: AsyncKVMClient):
        self._client = client

    async def status(self) -> dict:
        """Get current MSD state including connected image and storage info."""
        return await self._client._api_get("msd")

    async def list_images(self) -> dict[str, Any]:
        """List available images in storage."""
        result = await self.status()
        return result.get("storage", {}).get("images", {})

    async def upload(self, file_path: str | Path, image_name: str | None = None) -> dict:
        """Upload an ISO/image file to the KVM storage.

        Args:
            file_path: Local path to the image file.
            image_name: Name to store as (defaults to filename).
        """
        path = Path(file_path)
        name = image_name or path.name
        data = path.read_bytes()
        return await self._client._api_post(
            "msd/write",
            params={"image": name},
            content=data,
            headers={"Content-Type": "application/octet-stream"},
        )

    async def upload_url(self, url: str, image_name: str | None = None) -> dict:
        """Download an image from a URL to the KVM storage.

        Args:
            url: HTTP(S) URL to download from.
            image_name: Name to store as (derived from URL if omitted).
        """
        params = {"url": url}
        if image_name:
            params["image"] = image_name
        return await self._client._api_post("msd/write_remote", params=params)

    async def set_image(self, image_name: str, cdrom: bool = True) -> dict:
        """Set the active image and drive mode.

        Args:
            image_name: Name of image in storage.
            cdrom: True for CD-ROM mode, False for flash drive mode.
        """
        return await self._client._api_post(
            "msd/set_params",
            params={"image": image_name, "cdrom": int(cdrom)},
        )

    async def connect(self) -> dict:
        """Connect the virtual drive to the target machine."""
        return await self._client._api_post(
            "msd/set_connected",
            params={"connected": 1},
        )

    async def disconnect(self) -> dict:
        """Disconnect the virtual drive from the target machine."""
        return await self._client._api_post(
            "msd/set_connected",
            params={"connected": 0},
        )

    async def remove_image(self, image_name: str) -> dict:
        """Delete an image from storage."""
        return await self._client._api_post(
            "msd/remove",
            params={"image": image_name},
        )
