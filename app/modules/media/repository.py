from __future__ import annotations

from pathlib import Path


class MediaRepository:
    def __init__(self, base_dir: str) -> None:
        self.base_path = Path(base_dir)
        self.base_path.mkdir(parents=True, exist_ok=True)

    def save_bytes(self, file_name: str, content: bytes) -> str:
        file_path = self.base_path / file_name
        file_path.write_bytes(content)
        return str(file_path).replace("\\", "/")

