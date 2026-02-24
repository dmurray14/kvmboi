from __future__ import annotations

import asyncio
import base64
import json
import socket
import ssl
from typing import Any

import httpx
import websockets
import websockets.asyncio.client

from .exceptions import APIError, AuthError, NotConnectedError
from .hid import AsyncKeyboard, AsyncMouse
from .video import AsyncVideo
from .msd import AsyncMSD
from .atx import AsyncATX


class AsyncKVMClient:
    """Async client for controlling a GL.iNet Comet / PiKVM-compatible KVM device."""

    def __init__(
        self,
        host: str,
        username: str = "admin",
        password: str = "",
        ssl_verify: bool = False,
    ):
        self.host = host.rstrip("/")
        self.username = username
        self.password = password

        # Resolve hostname upfront - mDNS (.local) doesn't work in daemon threads on macOS
        try:
            self._resolved_ip = socket.gethostbyname(self.host)
        except socket.gaierror:
            self._resolved_ip = self.host

        self._ssl_context: ssl.SSLContext | bool
        if ssl_verify:
            self._ssl_context = True
        else:
            ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            self._ssl_context = ctx

        self._http = httpx.AsyncClient(
            base_url=f"https://{self.host}",
            verify=False if not ssl_verify else True,
            auth=(username, password),
            timeout=30.0,
        )

        self._ws: websockets.asyncio.client.ClientConnection | None = None
        self._ws_lock = asyncio.Lock()
        self._token: str | None = None

        self.keyboard = AsyncKeyboard(self)
        self.mouse = AsyncMouse(self)
        self.video = AsyncVideo(self)
        self.msd = AsyncMSD(self)
        self.atx = AsyncATX(self)

    @property
    def base_url(self) -> str:
        return f"https://{self.host}"

    async def _api_get(self, path: str, **params: Any) -> dict:
        resp = await self._http.get(f"/api/{path}", params=params or None)
        return self._check_response(resp)

    async def _api_post(self, path: str, params: dict | None = None, data: Any = None, content: bytes | None = None, **kwargs: Any) -> dict:
        resp = await self._http.post(
            f"/api/{path}",
            params=params,
            data=data,
            content=content,
            **kwargs,
        )
        return self._check_response(resp)

    async def _api_get_bytes(self, path: str, **params: Any) -> bytes:
        resp = await self._http.get(f"/api/{path}", params=params or None)
        if resp.status_code == 401:
            raise AuthError("Authentication failed")
        resp.raise_for_status()
        return resp.content

    def _check_response(self, resp: httpx.Response) -> dict:
        if resp.status_code == 401:
            raise AuthError("Authentication failed")
        if resp.status_code == 403:
            raise AuthError("Forbidden")
        resp.raise_for_status()
        body = resp.json()
        if not body.get("ok"):
            result = body.get("result", {})
            raise APIError(
                result.get("error", "UnknownError"),
                result.get("error_msg", "Unknown error"),
            )
        return body.get("result", {})

    async def _ensure_token(self) -> str:
        if self._token:
            return self._token
        resp = await self._http.post(
            "/api/auth/login",
            data={"user": self.username, "passwd": self.password},
        )
        body = resp.json()
        if not body.get("ok"):
            raise AuthError("Login failed")
        self._token = body["result"]["token"]
        return self._token

    async def _ensure_ws(self) -> websockets.asyncio.client.ClientConnection:
        async with self._ws_lock:
            if self._ws is not None:
                try:
                    await self._ws.ping()
                    return self._ws
                except Exception:
                    self._ws = None

            creds = base64.b64encode(f"{self.username}:{self.password}".encode()).decode()
            uri = f"wss://{self._resolved_ip}/api/ws?stream=0"
            self._ws = await websockets.asyncio.client.connect(
                uri,
                ssl=self._ssl_context if isinstance(self._ssl_context, ssl.SSLContext) else None,
                additional_headers={"Authorization": f"Basic {creds}"},
            )
            # Drain initial state messages
            try:
                for _ in range(20):
                    msg = await asyncio.wait_for(self._ws.recv(), timeout=0.5)
                    data = json.loads(msg)
                    if data.get("event_type") == "streamer":
                        # Last burst message typically
                        break
            except asyncio.TimeoutError:
                pass

            return self._ws

    async def ws_send(self, event_type: str, event: dict) -> None:
        ws = await self._ensure_ws()
        await ws.send(json.dumps({"event_type": event_type, "event": event}))

    async def info(self) -> dict:
        return await self._api_get("info")

    async def streamer_info(self) -> dict:
        return await self._api_get("streamer")

    async def close(self) -> None:
        if self._ws:
            await self._ws.close()
            self._ws = None
        await self._http.aclose()

    async def __aenter__(self) -> AsyncKVMClient:
        return self

    async def __aexit__(self, *exc: Any) -> None:
        await self.close()
