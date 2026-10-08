"""Sync protocol versioning.

Scaffold placeholder — protocol version negotiation logic to be implemented later.
"""

from __future__ import annotations

SYNC_PROTOCOL_VERSION = "1.0.0"


class SyncProtocolVersion:
    """Placeholder for sync protocol version management."""

    CURRENT = SYNC_PROTOCOL_VERSION

    @classmethod
    def is_compatible(cls, remote_version: str) -> bool:
        raise NotImplementedError
