from __future__ import annotations

from pathlib import Path

from app.modules.media.schemas import MediaItemOut


class MediaRepository:
    def __init__(self, base_dir: str) -> None:
        self.base_path = Path(base_dir)
        self.base_path.mkdir(parents=True, exist_ok=True)

    def save_bytes(self, file_name: str, content: bytes) -> str:
        file_path = self.base_path / file_name
        file_path.write_bytes(content)
        return str(file_path).replace("\\", "/")

    def list_recent(self, limit: int = 20) -> list[MediaItemOut]:
        files = [item for item in self.base_path.iterdir() if item.is_file()]
        files.sort(key=lambda f: f.stat().st_mtime, reverse=True)
        selected = files[: max(1, limit)]
        return [
            MediaItemOut(
                name=item.name,
                size=item.stat().st_size,
                path=str(item).replace("\\", "/"),
            )
            for item in selected
        ]
