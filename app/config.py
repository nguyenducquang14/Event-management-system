import os
from contextlib import contextmanager
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Tải các biến môi trường từ tệp .env (nếu có)
load_dotenv()

DB_USER = os.getenv("DB_USER", "root")
DB_PASS = os.getenv("DB_PASS", "")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "3306")
DB_NAME = os.getenv("DB_NAME", "event_management")

# Chuỗi kết nối SQLAlchemy cho MySQL
DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}?charset=utf8mb4"

# Khởi tạo Engine
engine = create_engine(DATABASE_URL, pool_pre_ping=True, pool_recycle=3600)

# Khởi tạo Session Factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@contextmanager
def get_db():
    """Cung cấp database session an toàn qua context manager."""
    db = SessionLocal()
    try:
        yield db
        db.commit()  # Tự động commit các thao tác (DML)
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()