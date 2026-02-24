"""kvmboi - Python library for controlling GL.iNet Comet KVM (PiKVM-compatible) devices."""

from .client import KVMClient
from .async_client import AsyncKVMClient
from .exceptions import KVMError, AuthError, APIError, ConnectionError, NotConnectedError

__all__ = [
    "KVMClient",
    "AsyncKVMClient",
    "KVMError",
    "AuthError",
    "APIError",
    "ConnectionError",
    "NotConnectedError",
]
