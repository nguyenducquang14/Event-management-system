"""
app/config.py
Quản lý kết nối cơ sở dữ liệu với SQLAlchemy 2.0
"""

import os
from contextlib import contextmanager
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from dotenv import load_dotenv

load_dotenv()

# ── Cấu hình kết nối ────────────────────────────────────────
DB_USER = os.getenv("DB_USER", "root")
DB_PASS = os.getenv("DB_PASS", "")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_NAME = os.getenv("DB_NAME", "event_management")

DATABASE_URL = (
    f"mysql+mysqlconnector://{DB_USER}:{DB_PASS}@{DB_HOST}/{DB_NAME}"
    "?charset=utf8mb4"
)

engine = create_engine(
    DATABASE_URL,
    echo=False,           # Bật True để debug SQL
    pool_pre_ping=True,   # Kiểm tra kết nối trước khi dùng
    pool_recycle=3600,    # Tái tạo connection sau 1 giờ
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


# ── Context manager tiện lợi ────────────────────────────────
@contextmanager
def get_db():
    """Dùng: with get_db() as db: ..."""
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def test_connection() -> bool:
    """Kiểm tra kết nối database khi khởi động."""
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception as e:
        print(f"[LỖI KẾT NỐI] {e}")
        return False

# Export cho Data Access Layer
__all__ = ["engine", "get_db", "SessionLocal", "Base", "test_connection", "DATABASE_URL"]

