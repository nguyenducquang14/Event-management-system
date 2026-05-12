import os
from contextlib import contextmanager
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Tải các biến môi trường từ tệp .env (nếu có)
load_dotenv()

DB_USER = os.getenv("DB_USER", "avnadmin")
DB_PASSWORD = os.getenv("DB_PASSWORD", "") 
DB_HOST = os.getenv("DB_HOST", "mysql-321e57ce-nguyenducquang1220444-2eb3.i.aivencloud.com")
DB_PORT = os.getenv("DB_PORT", "23932")
DB_NAME = os.getenv("DB_NAME", "defaultdb")

# Chuỗi kết nối SQLAlchemy cho MySQL
DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}?charset=utf8mb4"
)

# --- Cấu hình kết nối SSL tới Aiven ---
# Đường dẫn tới tệp chứng chỉ Aiven CA. Mặc định là 'ca.pem' ở thư mục gốc của dự án.
# Bạn có thể thay đổi bằng cách đặt biến môi trường AIVEN_CA_PATH.
AIVEN_CA_PATH = os.getenv("AIVEN_CA_PATH", "ca.pem")

ssl_args = {}
if 'aivencloud' in DB_HOST:
    # Aiven yêu cầu kết nối bảo mật SSL.
    # Cung cấp đường dẫn tới tệp ca.pem để xác thực chứng chỉ của server.
    ssl_args = {'ssl': {'ca': AIVEN_CA_PATH}}

# Khởi tạo Engine
engine = create_engine(DATABASE_URL, pool_pre_ping=True, pool_recycle=3600, connect_args=ssl_args)

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