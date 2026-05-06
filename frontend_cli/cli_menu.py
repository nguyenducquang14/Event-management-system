"""
app/cli/main.py
Menu chính — điều hướng toàn bộ ứng dụng CLI
"""

import questionary
from app.cli.event_menu        import event_menu
from app.cli.guest_menu        import guest_menu
from app.cli.registration_menu import registration_menu
from app.cli.finance_menu      import finance_menu
from app.cli.report_menu       import report_menu
from app.cli.utils             import console
from app.cli.auth_cli          import render_login_screen
from app.cli.auth_utils        import clear_current_token
from app.config                import get_db


def main_menu():
    while True:
        console.print()
        choice = questionary.select(
            "Chọn chức năng:",
            choices=[
                "L.  Đăng nhập hệ thống",
                "O.  Đăng xuất",
                "1.  Quản lý Sự kiện",
                "2.  Quản lý Khách mời",
                "3.  Đăng ký & Check-in",
                "4.  Quản lý Tài chính (Income / Expense)",
                "5.  Báo cáo & Thống kê  →  Xuất Excel",
                "6.  Demo Giai đoạn 3  →  Advanced DB Objects",
                "7.  Bảo mật & Quản trị →  RBAC + Backup",
                "0.  Thoát",
            ]
        ).ask()

        if not choice or choice.startswith("0"):
            console.print("\n[dim]  Tạm biệt! Hẹn gặp lại.[/dim]\n")
            break
        elif choice.startswith("L"):
            with get_db() as db:
                render_login_screen(db)
        elif choice.startswith("O"): clear_current_token()
        elif choice.startswith("1"): event_menu()
        elif choice.startswith("2"): guest_menu()
        elif choice.startswith("3"): registration_menu()
        elif choice.startswith("4"): finance_menu()
        elif choice.startswith("5"): report_menu()
        elif choice.startswith("6"):
            from app.cli.advanced_demo import advanced_demo_menu
            advanced_demo_menu()
        elif choice.startswith("7"):
            from app.cli.security_admin import security_admin_menu
            security_admin_menu()
