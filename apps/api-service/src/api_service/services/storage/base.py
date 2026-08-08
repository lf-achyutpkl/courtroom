from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping, Protocol


@dataclass(frozen=True)
class StoredObject:
    bucket: str
    key: str
    url: str
    content_type: str
    size_bytes: int


@dataclass(frozen=True)
class PrivateObjectMetadata:
    bucket: str
    key: str
    content_type: str
    size_bytes: int
    checksum: str | None = None


@dataclass(frozen=True)
class PresignedUpload:
    url: str
    required_headers: Mapping[str, str]
    expires_in_seconds: int


class ObjectStorageService(Protocol):
    def upload_bytes(
        self, *, key: str, payload: bytes, content_type: str
    ) -> StoredObject:
        """Upload blob and return its stable storage reference."""
        ...

    def create_private_upload(
        self, *, key: str, content_type: str, expires_in_seconds: int
    ) -> PresignedUpload:
        """Authorize a direct, private browser upload without sharing credentials."""
        ...

    def get_private_metadata(self, *, key: str) -> PrivateObjectMetadata | None:
        """Return metadata for a private object, or None when it is absent."""
        ...

    def download_private_bytes(self, *, key: str) -> bytes:
        """Download a private object using worker credentials."""
        ...
