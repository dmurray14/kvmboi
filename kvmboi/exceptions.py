class KVMError(Exception):
    """Base exception for kvmboi."""


class AuthError(KVMError):
    """Authentication failed."""


class ConnectionError(KVMError):
    """Could not connect to KVM device."""


class APIError(KVMError):
    """KVM API returned an error."""

    def __init__(self, error: str, message: str):
        self.error = error
        self.message = message
        super().__init__(f"{error}: {message}")


class NotConnectedError(KVMError):
    """WebSocket not connected."""
