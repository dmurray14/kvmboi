from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .async_client import AsyncKVMClient


class AsyncKeyboard:
    """Keyboard control via WebSocket HID events."""

    def __init__(self, client: AsyncKVMClient):
        self._client = client

    async def press(self, key: str) -> None:
        """Press and release a single key. Uses web key names like 'KeyA', 'Enter', 'ControlLeft'."""
        await self._client.ws_send("key", {"key": key, "state": True})
        await asyncio.sleep(0.02)
        await self._client.ws_send("key", {"key": key, "state": False})

    async def hold(self, key: str) -> None:
        """Hold a key down (send key press without release)."""
        await self._client.ws_send("key", {"key": key, "state": True})

    async def release(self, key: str) -> None:
        """Release a held key."""
        await self._client.ws_send("key", {"key": key, "state": False})

    async def shortcut(self, *keys: str) -> None:
        """Press a key combination (e.g. shortcut('ControlLeft', 'KeyC')).

        Presses all keys in order, then releases in reverse order.
        """
        for key in keys:
            await self._client.ws_send("key", {"key": key, "state": True})
            await asyncio.sleep(0.02)
        await asyncio.sleep(0.05)
        for key in reversed(keys):
            await self._client.ws_send("key", {"key": key, "state": False})
            await asyncio.sleep(0.02)

    async def type(self, text: str, keymap: str = "en-us") -> None:
        """Type text string using the HID print endpoint."""
        await self._client._api_post(
            "hid/print",
            data=text,
            params={"limit": 0, "keymap": keymap},
        )


class AsyncMouse:
    """Mouse control via WebSocket HID events."""

    def __init__(self, client: AsyncKVMClient):
        self._client = client

    async def move(self, x: int, y: int) -> None:
        """Move mouse to absolute coordinates."""
        await self._client.ws_send("mouse_move", {"to": {"x": x, "y": y}})

    async def click(self, x: int | None = None, y: int | None = None, button: str = "left") -> None:
        """Click at coordinates. If x/y omitted, clicks at current position."""
        if x is not None and y is not None:
            await self.move(x, y)
            await asyncio.sleep(0.05)
        await self._client.ws_send("mouse_button", {"button": button, "state": True})
        await asyncio.sleep(0.05)
        await self._client.ws_send("mouse_button", {"button": button, "state": False})

    async def right_click(self, x: int | None = None, y: int | None = None) -> None:
        """Right-click at coordinates."""
        await self.click(x, y, button="right")

    async def middle_click(self, x: int | None = None, y: int | None = None) -> None:
        """Middle-click at coordinates."""
        await self.click(x, y, button="middle")

    async def double_click(self, x: int | None = None, y: int | None = None) -> None:
        """Double-click at coordinates."""
        await self.click(x, y)
        await asyncio.sleep(0.1)
        await self.click(x, y)

    async def scroll(self, delta_x: int = 0, delta_y: int = 0) -> None:
        """Scroll the mouse wheel. Negative delta_y = scroll up."""
        await self._client.ws_send("mouse_wheel", {"delta": {"x": delta_x, "y": delta_y}})

    async def drag(self, from_x: int, from_y: int, to_x: int, to_y: int, button: str = "left", steps: int = 10) -> None:
        """Drag from one point to another."""
        await self.move(from_x, from_y)
        await asyncio.sleep(0.05)
        await self._client.ws_send("mouse_button", {"button": button, "state": True})
        await asyncio.sleep(0.05)

        for i in range(1, steps + 1):
            t = i / steps
            x = int(from_x + (to_x - from_x) * t)
            y = int(from_y + (to_y - from_y) * t)
            await self.move(x, y)
            await asyncio.sleep(0.02)

        await self._client.ws_send("mouse_button", {"button": button, "state": False})

    async def relative_move(self, delta_x: int, delta_y: int) -> None:
        """Move mouse by relative offset."""
        await self._client.ws_send("mouse_relative", {"delta": {"x": delta_x, "y": delta_y}})
