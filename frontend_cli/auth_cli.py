"""
app/cli/auth_cli.py
Giao diện dòng lệnh (CLI) cho chức năng Đăng nhập.
"""
from rich.console import Console
from rich.prompt import Prompt
from rich.panel import Panel

from app.database.auth_models import login_user

console = Console()

def render_login_screen(db_session):
    console.print(Panel.fit("[bold blue]ĐĂNG NHẬP HỆ THỐNG QUẢN LÝ SỰ KIỆN[/bold blue]", border_style="blue"))
    
    # Nhập liệu an toàn trên Terminal
    username = Prompt.ask("[bold green]Username[/bold green]")
    password = Prompt.ask("[bold green]Password[/bold green]", password=True) # Che mật khẩu
    
    with console.status("[bold yellow]Đang xác thực...", spinner="dots"):
        # Gọi hàm logic ở tầng Backend
        result = login_user(db_session, username, password)
        
    if result["success"]:
        user_name = result["user_info"]["name"]
        role_str = ", ".join(result["user_info"]["roles"])
        
        console.print(f"\n[bold green]✓ Đăng nhập thành công![/bold green]")
        console.print(f"Xin chào [bold cyan]{user_name}[/bold cyan] ({role_str})")
        
        # Lưu token vào file ẩn để duy trì phiên đăng nhập cho các lệnh tiếp theo
        with open(".auth_session", "w") as f:
            f.write(result["token"])
            
        # TRẢ VỀ TOKEN ĐỂ SỬ DỤNG CHO CÁC LỆNH TIẾP THEO
        return result["token"]
    else:
        console.print(f"\n[bold red]✗ Lỗi: {result['error']}[/bold red]")
        return None