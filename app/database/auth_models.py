import hashlib
import uuid
from sqlalchemy import Column, Integer, String, Table, ForeignKey
from sqlalchemy.orm import declarative_base, relationship

# Khởi tạo Base riêng cho Auth để không xung đột với các bảng nghiệp vụ chính
Base = declarative_base()

# Bảng trung gian nhiều-nhiều giữa Users và Roles
user_roles = Table(
    'user_roles', Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id', ondelete="CASCADE"), primary_key=True),
    Column('role_id', Integer, ForeignKey('roles.id', ondelete="CASCADE"), primary_key=True)
)

class Role(Base):
    __tablename__ = 'roles'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), unique=True, nullable=False)

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String(50), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(100), nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    
    roles = relationship('Role', secondary=user_roles, backref='users', lazy="joined")

def hash_password(password: str) -> str:
    """Băm mật khẩu bằng SHA-256 (nên dùng bcrypt/argon2 cho production)."""
    return hashlib.sha256(password.encode('utf-8')).hexdigest()

def seed_data(db_session):
    """Khởi tạo các quyền cơ bản và tài khoản admin mặc định."""
    default_roles = ['Admin', 'Organizer', 'Staff', 'Guest']
    for role_name in default_roles:
        if not db_session.query(Role).filter_by(name=role_name).first():
            db_session.add(Role(name=role_name))
    
    # Tạo tài khoản admin mặc định nếu chưa có
    if not db_session.query(User).filter_by(username='admin').first():
        admin_role = db_session.query(Role).filter_by(name='Admin').first()
        admin_user = User(
            username='admin',
            password_hash=hash_password('admin123'),
            full_name='Quản trị viên Hệ thống',
            email='admin@datcom.neu.vn',
            roles=[admin_role] if admin_role else []
        )
        db_session.add(admin_user)
        
    try:
        db_session.commit()
    except Exception:
        db_session.rollback()

def login_user(db_session, username, password):
    """Xác thực người dùng khi đăng nhập."""
    user = db_session.query(User).filter_by(username=username).first()
    
    if not user or user.password_hash != hash_password(password):
        return {"success": False, "error": "Sai tên đăng nhập hoặc mật khẩu!"}
    
    return {
        "success": True,
        "token": str(uuid.uuid4()),
        "user_info": {
            "name": user.full_name,
            "email": user.email,
            "roles": [r.name for r in user.roles]
        }
    }

def register_user(db_session, username, password, fullname, email, role_assign):
    """Đăng ký tài khoản người dùng mới."""
    if db_session.query(User).filter_by(username=username).first():
        return {"success": False, "error": "Tên đăng nhập đã tồn tại!"}
    if db_session.query(User).filter_by(email=email).first():
        return {"success": False, "error": "Địa chỉ Email đã được sử dụng!"}
        
    role = db_session.query(Role).filter_by(name=role_assign).first()
    new_user = User(username=username, password_hash=hash_password(password), full_name=fullname, email=email)
    if role:
        new_user.roles.append(role)
        
    db_session.add(new_user)
    db_session.commit()
    return {"success": True, "message": "Đăng ký tài khoản thành công!"}