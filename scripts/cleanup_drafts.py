from __future__ import annotations

from app.core.db import SessionLocal
from app.modules.drafts.repository import DraftRepository
from app.modules.drafts.service import DraftService


def main() -> None:
    db = SessionLocal()
    try:
        service = DraftService(DraftRepository(db))
        deleted = service.cleanup_expired()
        print(f"Deleted {deleted} expired drafts")
    finally:
        db.close()


if __name__ == "__main__":
    main()

