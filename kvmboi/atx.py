from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .async_client import AsyncKVMClient


class AsyncATX:
    """ATX power control for the target machine."""

    def __init__(self, client: AsyncKVMClient):
        self._client = client

    async def status(self) -> dict:
        """Get current ATX/power state (power LED, HDD LED)."""
        return await self._client._api_get("atx")

    async def short_press(self) -> dict:
        """Short press the power button (normal power on/off)."""
        return await self._client._api_post(
            "atx/click",
            params={"button": "power"},
        )

    async def long_press(self) -> dict:
        """Long press the power button (force power off)."""
        return await self._client._api_post(
            "atx/click",
            params={"button": "power_long"},
        )

    async def reset(self) -> dict:
        """Press the reset button."""
        return await self._client._api_post(
            "atx/click",
            params={"button": "reset"},
        )
