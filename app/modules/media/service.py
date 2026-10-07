from __future__ import annotations

from pathlib import Path
from uuid import uuid4

from fastapi import HTTPException, UploadFile, status

from app.core.config import settings
from app.modules.media.repository import MediaRepository
from app.modules.media.schemas import MediaUploadResult


class MediaService:
    def __init__(self) -> None:
        self.repository = MediaRepository(settings.media_dir)
        self.allowed_extensions = {
            extension.strip().lower()
            for extension in settings.media_allowed_extensions.split(",")
            if extension.strip()
        }
        self.allowed_mime_types = {
            mime.strip().lower()
            for mime in settings.media_allowed_mime_types.split(",")
            if mime.strip()
        }

    async def upload_file(self, file: UploadFile) -> MediaUploadResult:
        if not file.filename:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail="File name is required.",
            )

        sanitized_name = Path(file.filename).name
        extension = Path(sanitized_name).suffix.lower().lstrip(".")
        content_type = (file.content_type or "").lower()

        if extension not in self.allowed_extensions:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail=f"File extension '.{extension}' is not allowed.",
            )

        if content_type not in self.allowed_mime_types:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail=f"MIME type '{content_type}' is not allowed.",
            )

        content = await file.read()
        size = len(content)
        if size > settings.media_max_size_bytes:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail=f"File exceeds max size of {settings.media_max_size_bytes} bytes.",
            )

        stored_name = f"{uuid4().hex}_{sanitized_name}"
        stored_path = self.repository.save_bytes(stored_name, content)

        return MediaUploadResult(
            original_name=sanitized_name,
            stored_name=stored_name,
            content_type=content_type,
            size=size,
            path=stored_path,
        )

