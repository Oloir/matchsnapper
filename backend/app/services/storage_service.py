import asyncio
import io
from uuid import UUID

import boto3
from PIL import Image

from app.config import settings


def _build_s3():
    kwargs = dict(
        aws_access_key_id=settings.aws_access_key_id,
        aws_secret_access_key=settings.aws_secret_access_key,
        region_name=settings.aws_region,
    )
    if settings.aws_endpoint_url:
        kwargs["endpoint_url"] = settings.aws_endpoint_url
    return boto3.client("s3", **kwargs)


class StorageService:
    def __init__(self):
        self._s3 = _build_s3()

    @staticmethod
    def _process_image(data: bytes) -> bytes:
        with Image.open(io.BytesIO(data)) as img:
            img = img.convert("RGB")
            w, h = img.size
            side = min(w, h)
            left, top = (w - side) // 2, (h - side) // 2
            img = img.crop((left, top, left + side, top + side))
            img = img.resize((256, 256), Image.LANCZOS)
            buf = io.BytesIO()
            img.save(buf, format="JPEG", quality=85)
            return buf.getvalue()

    def _put(self, key: str, data: bytes) -> str:
        self._s3.put_object(
            Bucket=settings.aws_bucket_name,
            Key=key,
            Body=data,
            ContentType="image/jpeg",
        )
        if settings.aws_endpoint_url:
            return f"{settings.aws_endpoint_url}/{settings.aws_bucket_name}/{key}"
        return f"https://{settings.aws_bucket_name}.s3.{settings.aws_region}.amazonaws.com/{key}"

    def _remove(self, key: str) -> None:
        self._s3.delete_object(Bucket=settings.aws_bucket_name, Key=key)

    async def upload_avatar(self, user_id: UUID, data: bytes) -> str:
        loop = asyncio.get_running_loop()
        processed = await loop.run_in_executor(None, self._process_image, data)
        key = f"avatars/{user_id}.jpg"
        return await loop.run_in_executor(None, self._put, key, processed)

    async def delete_avatar(self, user_id: UUID) -> None:
        loop = asyncio.get_running_loop()
        key = f"avatars/{user_id}.jpg"
        await loop.run_in_executor(None, self._remove, key)


storage_service = StorageService()
