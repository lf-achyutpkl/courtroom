from __future__ import annotations

from functools import cached_property

from .base import ObjectStorageService, StoredObject


class R2ObjectStorageService(ObjectStorageService):
    def __init__(
        self,
        *,
        bucket_name: str,
        endpoint_url: str,
        access_key_id: str,
        secret_access_key: str,
        public_base_url: str,
        region_name: str = "auto",
    ) -> None:
        self.bucket_name = bucket_name
        self.endpoint_url = endpoint_url
        self.access_key_id = access_key_id
        self.secret_access_key = secret_access_key
        self.public_base_url = public_base_url.rstrip("/")
        self.region_name = region_name

    @cached_property
    def _client(self):
        import boto3
        from botocore.client import Config

        session = boto3.session.Session()
        return session.client(
            "s3",
            endpoint_url=self.endpoint_url,
            aws_access_key_id=self.access_key_id,
            aws_secret_access_key=self.secret_access_key,
            region_name=self.region_name,
            config=Config(signature_version="s3v4"),
        )

    def upload_bytes(
        self,
        *,
        key: str,
        payload: bytes,
        content_type: str,
    ) -> StoredObject:
        self._client.put_object(
            Bucket=self.bucket_name,
            Key=key,
            Body=payload,
            ContentType=content_type,
        )
        return StoredObject(
            bucket=self.bucket_name,
            key=key,
            url=f"{self.public_base_url}/{key}",
            content_type=content_type,
            size_bytes=len(payload),
        )
