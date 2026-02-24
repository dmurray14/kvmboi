from __future__ import annotations

import asyncio
import threading
from pathlib import Path
from typing import Any

from .async_client import AsyncKVMClient


class _EventLoopThread:
    """Runs a persistent asyncio event loop in a background thread."""

    def __init__(self):
        self._loop = asyncio.new_event_loop()
        self._thread = threading.Thread(target=self._loop.run_forever, daemon=True)
        self._thread.start()

    def run(self, coro):
        return asyncio.run_coroutine_threadsafe(coro, self._loop).result()

    def stop(self):
        self._loop.call_soon_threadsafe(self._loop.stop)
        self._thread.join(timeout=5)


class _SyncKeyboard:
    def __init__(self, async_kb, loop: _EventLoopThread):
        self._async = async_kb
        self._loop = loop

    def press(self, key: str) -> None:
        """Press and release a single key."""
        self._loop.run(self._async.press(key))

    def hold(self, key: str) -> None:
        """Hold a key down."""
        self._loop.run(self._async.hold(key))

    def release(self, key: str) -> None:
        """Release a held key."""
        self._loop.run(self._async.release(key))

    def shortcut(self, *keys: str) -> None:
        """Press a key combination (e.g. shortcut('ControlLeft', 'KeyC'))."""
        self._loop.run(self._async.shortcut(*keys))

    def type(self, text: str, keymap: str = "en-us") -> None:
        """Type a text string."""
        self._loop.run(self._async.type(text, keymap))


class _SyncMouse:
    def __init__(self, async_mouse, loop: _EventLoopThread):
        self._async = async_mouse
        self._loop = loop

    def move(self, x: int, y: int) -> None:
        """Move mouse to absolute coordinates."""
        self._loop.run(self._async.move(x, y))

    def click(self, x: int | None = None, y: int | None = None, button: str = "left") -> None:
        """Click at coordinates."""
        self._loop.run(self._async.click(x, y, button))

    def right_click(self, x: int | None = None, y: int | None = None) -> None:
        """Right-click at coordinates."""
        self._loop.run(self._async.right_click(x, y))

    def middle_click(self, x: int | None = None, y: int | None = None) -> None:
        """Middle-click at coordinates."""
        self._loop.run(self._async.middle_click(x, y))

    def double_click(self, x: int | None = None, y: int | None = None) -> None:
        """Double-click at coordinates."""
        self._loop.run(self._async.double_click(x, y))

    def scroll(self, delta_x: int = 0, delta_y: int = 0) -> None:
        """Scroll the mouse wheel."""
        self._loop.run(self._async.scroll(delta_x, delta_y))

    def drag(self, from_x: int, from_y: int, to_x: int, to_y: int, button: str = "left", steps: int = 10) -> None:
        """Drag from one point to another."""
        self._loop.run(self._async.drag(from_x, from_y, to_x, to_y, button, steps))

    def relative_move(self, delta_x: int, delta_y: int) -> None:
        """Move mouse by relative offset."""
        self._loop.run(self._async.relative_move(delta_x, delta_y))


class _SyncVideo:
    def __init__(self, async_video, loop: _EventLoopThread):
        self._async = async_video
        self._loop = loop

    def screenshot(self, save_to: str | Path | None = None) -> bytes:
        """Capture a JPEG screenshot."""
        return self._loop.run(self._async.screenshot(save_to))

    def streamer_info(self) -> dict:
        """Get video streamer state."""
        return self._loop.run(self._async.streamer_info())


class _SyncMSD:
    def __init__(self, async_msd, loop: _EventLoopThread):
        self._async = async_msd
        self._loop = loop

    def status(self) -> dict:
        return self._loop.run(self._async.status())

    def list_images(self) -> dict:
        return self._loop.run(self._async.list_images())

    def upload(self, file_path: str | Path, image_name: str | None = None) -> dict:
        return self._loop.run(self._async.upload(file_path, image_name))

    def upload_url(self, url: str, image_name: str | None = None) -> dict:
        return self._loop.run(self._async.upload_url(url, image_name))

    def set_image(self, image_name: str, cdrom: bool = True) -> dict:
        return self._loop.run(self._async.set_image(image_name, cdrom))

    def connect(self) -> dict:
        return self._loop.run(self._async.connect())

    def disconnect(self) -> dict:
        return self._loop.run(self._async.disconnect())

    def remove_image(self, image_name: str) -> dict:
        return self._loop.run(self._async.remove_image(image_name))


class _SyncATX:
    def __init__(self, async_atx, loop: _EventLoopThread):
        self._async = async_atx
        self._loop = loop

    def status(self) -> dict:
        return self._loop.run(self._async.status())

    def short_press(self) -> dict:
        return self._loop.run(self._async.short_press())

    def long_press(self) -> dict:
        return self._loop.run(self._async.long_press())

    def reset(self) -> dict:
        return self._loop.run(self._async.reset())


class KVMClient:
    """Synchronous client for controlling a GL.iNet Comet / PiKVM-compatible KVM device.

    Usage:
        kvm = KVMClient("your-kvm.local", password="your-password")
        kvm.screenshot("/tmp/screen.jpg")
        kvm.keyboard.type("hello")
        kvm.mouse.click(500, 300)
        kvm.close()
    """

    def __init__(
        self,
        host: str,
        username: str = "admin",
        password: str = "",
        ssl_verify: bool = False,
    ):
        self._loop = _EventLoopThread()
        self._async_client = AsyncKVMClient(
            host=host,
            username=username,
            password=password,
            ssl_verify=ssl_verify,
        )
        self.keyboard = _SyncKeyboard(self._async_client.keyboard, self._loop)
        self.mouse = _SyncMouse(self._async_client.mouse, self._loop)
        self.video = _SyncVideo(self._async_client.video, self._loop)
        self.msd = _SyncMSD(self._async_client.msd, self._loop)
        self.atx = _SyncATX(self._async_client.atx, self._loop)

    def screenshot(self, save_to: str | Path | None = None) -> bytes:
        """Convenience: capture a JPEG screenshot."""
        return self.video.screenshot(save_to)

    def info(self) -> dict:
        """Get full system info."""
        return self._loop.run(self._async_client.info())

    def streamer_info(self) -> dict:
        """Get video streamer state."""
        return self._loop.run(self._async_client.streamer_info())

    def close(self) -> None:
        """Close all connections."""
        self._loop.run(self._async_client.close())
        self._loop.stop()

    def __enter__(self) -> KVMClient:
        return self

    def __exit__(self, *exc: Any) -> None:
        self.close()
