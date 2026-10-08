"""Sync protocol serializer.

Scaffold placeholder — sync serialization logic to be implemented later.
"""

from __future__ import annotations


class SyncEventSerializer:
    """Placeholder serializer for sync events."""

    def __init__(self) -> None:
        pass

    def encode(self, obj: object) -> bytes:
        raise NotImplementedError

    def decode(self, data: bytes) -> object:
        raise NotImplementedError
