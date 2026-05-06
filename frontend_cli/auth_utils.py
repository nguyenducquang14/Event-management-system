import jwt
import os
from functools import wraps

from app.cli.utils import console

SECRET_KEY = os.getenv("SECRET_KEY", "chuoi_khoa_mac_dinh_cho_moi_truong_dev")

# Hàm phụ trợ: Đọc token từ file ẩn lưu trên máy tính
def get_current_token():
    try:
        with open(".auth_session", "r") as f:
            return f.read().strip()
    except FileNotFoundError:
        return None

# Hàm phụ trợ: Xóa token (Đăng xuất)
def clear_current_token():
    if os.path.exists(".auth_session"):
        os.remove(".auth_session")
        console.print("\n[bold green]✓ Đã đăng xuất hệ thống thành công![/bold green]")
    else:
        console.print("\n[bold yellow]ℹ Bạn chưa đăng nhập![/bold yellow]")

# Decorator chính: Kiểm tra Quyền (Permission)
def requires_permission(required_permission):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            token = get_current_token()
            if not token:
                console.print("\n[bold red]✗ Lỗi 401: Bạn chưa đăng nhập hoặc phiên đã hết hạn![/bold red]")
                return
            
            try:
                # 1. Giải mã token
                decoded_payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
                user_roles = decoded_payload.get("roles", [])
                user_permissions = decoded_payload.get("permissions", [])
                
                # 2. Logic kiểm tra quyền có Bypass cho Admin
                is_admin = "Admin" in user_roles or "all_access" in user_permissions
                has_permission = required_permission in user_permissions

                if not is_admin and not has_permission:
                    console.print(f"\n[bold red]✗ Lỗi 403: Cấm truy cập! Bạn cần quyền '{required_permission}'.[/bold red]")
                    return
                
                # 3. Ép thông tin user vào kwargs để hàm lõi có thể sử dụng
                kwargs['current_user'] = decoded_payload
                return func(*args, **kwargs)
                
            except (jwt.ExpiredSignatureError, jwt.InvalidTokenError):
                console.print("\n[bold red]✗ Token không hợp lệ hoặc đã hết hạn. Vui lòng đăng nhập lại![/bold red]")
        return wrapper
    return decorator