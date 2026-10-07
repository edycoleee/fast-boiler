from __future__ import annotations

import os
import shutil
from pathlib import Path

TEST_DB_PATH = Path("data") / "test_app.db"
TEST_MEDIA_DIR = Path("data") / "test_uploads"

os.environ["APP_ENV"] = "test"
os.environ["DB_URL"] = f"sqlite:///{TEST_DB_PATH.as_posix()}"
os.environ["MEDIA_DIR"] = TEST_MEDIA_DIR.as_posix()
os.environ["MEDIA_MAX_SIZE_BYTES"] = "64"
os.environ["MEDIA_ALLOWED_EXTENSIONS"] = "txt,png,pdf"
os.environ["MEDIA_ALLOWED_MIME_TYPES"] = "text/plain,image/png,application/pdf"

if TEST_DB_PATH.exists():
    TEST_DB_PATH.unlink()
if TEST_MEDIA_DIR.exists():
    shutil.rmtree(TEST_MEDIA_DIR)
