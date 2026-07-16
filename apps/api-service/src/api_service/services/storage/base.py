from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class StoredObject:
    bucket: str
    key: str
    url: str
    content_type: str
    size_bytes: int


class ObjectStorageService(Protocol):
    def upload_bytes(
        self,
        *,
        key: str,
        payload: bytes,
        content_type: str,
    ) -> StoredObject:
        """Upload a blob and return its stable storage reference."""
        ...
