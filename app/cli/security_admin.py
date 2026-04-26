"""
app/cli/security_admin.py
Quản trị bảo mật & backup — Giai đoạn 4
Demo RBAC, Column-level Security, Backup/Recovery
"""

import os
import subprocess
import platform
from datetime import datetime
from pathlib import Path

import questionary
from sqlalchemy import text
from rich.table import Table
from rich.panel import Panel
from rich import box

from app.config import get_db, engine
from app.cli.utils import (
    console, print_table, success, error, info, warning, pause
)


# ════════════════════════════════════════════════════════════
# 1. DEMO RBAC — hiển thị quyền từng role
# ════════════════════════════════════════════════════════════
def demo_rbac():
    console.rule("[bold cyan]DEMO: RBAC — Role-Based Access Control[/bold cyan]")

    # Bảng tổng hợp quyền hạn
    rbac_matrix = [
        {
            "Vai trò":        "event_manager",
            "User":           "coordinator",
            "Bảng có quyền":  "Events, Venues, Organizers, Guests, Finances (CRUD)",
            "Registrations":  "SELECT, INSERT, UPDATE",
            "Views":          "Tất cả",
            "SP/Function":    "Tất cả",
            "Bị chặn":        "DROP, ALTER, CREATE",
        },
        {
            "Vai trò":        "checkin_staff",
            "User":           "checkin_staff_user",
            "Bảng có quyền":  "Registrations (chỉ 2 cột: attendance_status, checkin_time)",
            "Registrations":  "UPDATE (2 cols)",
            "Views":          "v_safe_guests, v_safe_registrations",
            "SP/Function":    "sp_check_in_guest",
            "Bị chặn":        "Email, Phone, Address của Guests",
        },
        {
            "Vai trò":        "finance_officer",
            "User":           "finance_user",
            "Bảng có quyền":  "Finances (SELECT/INSERT/UPDATE), Events (SELECT)",
            "Registrations":  "KHÔNG có",
            "Views":          "v_finance_balance, v_event_attendance_summary",
            "SP/Function":    "sp_add_finance_record, fn_event_balance",
            "Bị chặn":        "Guests, Registrations, DELETE",
        },
        {
            "Vai trò":        "readonly_viewer",
            "User":           "readonly_user",
            "Bảng có quyền":  "KHÔNG có (chỉ qua Views)",
            "Registrations":  "KHÔNG có",
            "Views":          "v_upcoming_events, v_venue_schedule (SELECT only)",
            "SP/Function":    "KHÔNG có",
            "Bị chặn":        "Tất cả INSERT/UPDATE/DELETE",
        },
    ]

    print_table(rbac_matrix, "Ma trận phân quyền RBAC — Least Privilege", style="cyan")

    # Kiểm tra users trong MySQL
    console.print("\n  [dim]Kiểm tra users trong MySQL...[/dim]")
    try:
        with get_db() as db:
            rows = db.execute(text("""
                SELECT user, host, account_locked, password_expired,
                       password_lifetime
                FROM mysql.user
                WHERE user IN ('coordinator','checkin_staff_user','finance_user','readonly_user')
            """)).fetchall()
        if rows:
            print_table(
                [dict(r._mapping) for r in rows],
                "Users trong MySQL", style="blue"
            )
        else:
            warning("Chưa tạo users. Chạy phase4_security.sql trước.")
    except Exception as e:
        warning(f"Không đủ quyền xem mysql.user: {e}")

    pause()


# ════════════════════════════════════════════════════════════
# 2. DEMO COLUMN-LEVEL SECURITY — Views an toàn
# ════════════════════════════════════════════════════════════
def demo_column_security():
    console.rule("[bold yellow]DEMO: Column-level Security — Ẩn thông tin nhạy cảm[/bold yellow]")

    console.print(Panel(
        "[bold]Nguyên tắc:[/bold]\n"
        "  Nhân viên check-in [bold red]KHÔNG[/bold red] được xem Email, SĐT, Địa chỉ của khách.\n"
        "  Họ chỉ thấy dữ liệu qua [bold green]v_safe_guests[/bold green] và "
        "[bold green]v_safe_registrations[/bold green].",
        border_style="yellow",
        title="Column-level Security",
    ))

    try:
        with get_db() as db:
            # Dữ liệu GỐC (chỉ root/coordinator mới thấy)
            raw = db.execute(text("""
                SELECT guest_id, guest_name, email, phone_number, address
                FROM Guests LIMIT 4
            """)).fetchall()

            # Dữ liệu ĐÃ MASK (checkin_staff thấy qua View)
            masked = db.execute(text("""
                SELECT guest_id, guest_name, email_masked, phone_masked, address
                FROM v_safe_guests LIMIT 4
            """)).fetchall()

        console.print("\n  [bold red]Dữ liệu gốc[/bold red] (chỉ role event_manager mới thấy):")
        print_table([dict(r._mapping) for r in raw], "", style="red")

        console.print("  [bold green]Dữ liệu đã mask[/bold green] (checkin_staff thấy qua v_safe_guests):")
        print_table([dict(r._mapping) for r in masked], "", style="green")

    except Exception as e:
        error(f"Lỗi: {e}")

    # So sánh v_safe_registrations
    try:
        with get_db() as db:
            rows = db.execute(text("""
                SELECT reg_id, event_name, guest_name, email_hint,
                       attendance_status, checkin_time
                FROM v_safe_registrations LIMIT 5
            """)).fetchall()
        console.print("\n  [bold green]v_safe_registrations[/bold green] — Dành cho checkin_staff:")
        print_table([dict(r._mapping) for r in rows], "", style="green")
    except Exception as e:
        error(f"Lỗi xem v_safe_registrations: {e}")

    pause()


# ════════════════════════════════════════════════════════════
# 3. KIỂM TRA GRANT — Xem quyền của user cụ thể
# ════════════════════════════════════════════════════════════
def check_user_grants():
    console.rule("[bold blue]Kiểm tra quyền của User[/bold blue]")

    user = questionary.select(
        "Chọn user cần kiểm tra:",
        choices=[
            "coordinator",
            "checkin_staff_user",
            "finance_user",
            "readonly_user",
        ]
    ).ask()

    try:
        with get_db() as db:
            rows = db.execute(text(f"SHOW GRANTS FOR '{user}'@'localhost'")).fetchall()

        console.print(f"\n  [bold]GRANTS cho '{user}'@'localhost':[/bold]")
        for r in rows:
            line = list(r)[0]
            color = "green" if "GRANT" in line and "REVOKE" not in line else "red"
            console.print(f"    [{color}]{line}[/{color}]")

    except Exception as e:
        error(f"Không xem được grants: {e}")
        warning("Cần chạy phase4_security.sql trước để tạo users.")

    pause()


# ════════════════════════════════════════════════════════════
# 4. BACKUP — Chạy mysqldump từ Python
# ════════════════════════════════════════════════════════════
def run_backup():
    console.rule("[bold green]Backup Database — mysqldump[/bold green]")

    # Đọc config từ .env
    from dotenv import load_dotenv
    load_dotenv()

    db_user = os.getenv("DB_USER", "root")
    db_pass = os.getenv("DB_PASS", "")
    db_host = os.getenv("DB_HOST", "localhost")
    db_name = os.getenv("DB_NAME", "event_management")

    # Thư mục backup
    backup_dir = Path("backup_files")
    backup_dir.mkdir(exist_ok=True)

    backup_type = questionary.select(
        "Loại backup:",
        choices=[
            "Full (schema + data + routines + triggers)",
            "Schema only (chỉ cấu trúc, không có data)",
            "Data only (chỉ dữ liệu, không có schema)",
        ]
    ).ask()

    ts       = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = backup_dir / f"event_management_{backup_type.split()[0].lower()}_{ts}.sql"

    # Xây dựng lệnh mysqldump
    cmd = [
        "mysqldump",
        f"-u{db_user}",
        f"-p{db_pass}" if db_pass else "-p",
        f"-h{db_host}",
    ]

    if "Full" in backup_type:
        cmd += ["--routines", "--triggers", "--events", "--single-transaction"]
    elif "Schema" in backup_type:
        cmd += ["--no-data", "--routines", "--triggers"]
    elif "Data" in backup_type:
        cmd += ["--no-create-info", "--skip-triggers"]

    cmd += ["--databases", db_name, "--result-file", str(filename)]

    console.print(f"\n  Đang thực hiện backup...\n  Lệnh: [dim]{' '.join(cmd[:5])} ...[/dim]")

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)

        if result.returncode == 0:
            size_kb = filename.stat().st_size // 1024
            success(
                f"Backup thành công!\n"
                f"  File  : {filename.absolute()}\n"
                f"  Kích thước: {size_kb} KB"
            )

            # Ghi log vào MySQL
            btype_enum = "Full" if "Full" in backup_type else ("Schema" if "Schema" in backup_type else "Data")
            try:
                with get_db() as db:
                    db.execute(text("""
                        CALL sp_backup_log(:file, :btype, 'Success', :note)
                    """), {
                        "file": str(filename),
                        "btype": btype_enum,
                        "note": f"Backup từ Python CLI, kích thước: {size_kb} KB",
                    })
            except Exception:
                pass  # Bỏ qua nếu stored procedure chưa tồn tại

        else:
            error(f"Backup thất bại!\n  {result.stderr[:300]}")

    except FileNotFoundError:
        error("Không tìm thấy lệnh 'mysqldump'. Kiểm tra MySQL đã thêm vào PATH chưa.")
        info("Thay vào đó, chạy file backup.bat (Windows) hoặc backup.sh (Linux/macOS).")
    except subprocess.TimeoutExpired:
        error("Backup timeout sau 120 giây. Database quá lớn hoặc kết nối chậm.")
    except Exception as e:
        error(f"Lỗi không xác định: {e}")

    pause()


# ════════════════════════════════════════════════════════════
# 5. RECOVERY — Hướng dẫn restore
# ════════════════════════════════════════════════════════════
def guide_recovery():
    console.rule("[bold red]Hướng dẫn Recovery[/bold red]")

    console.print(Panel(
        "[bold]Bước 1[/bold] — Chọn file backup cần phục hồi:\n"
        "  [cyan]ls backup_files/[/cyan]\n\n"
        "[bold]Bước 2[/bold] — Restore bằng mysql command:\n"
        "  [cyan]mysql -u root -p < backup_files/event_management_full_20250615.sql[/cyan]\n\n"
        "[bold]Bước 3[/bold] — Hoặc dùng MySQL Workbench:\n"
        "  Server → Data Import → Import from Self-Contained File\n\n"
        "[bold]Bước 4[/bold] — Kiểm tra sau restore:\n"
        "  [cyan]SELECT COUNT(*) FROM Events;[/cyan]\n"
        "  [cyan]SELECT COUNT(*) FROM Guests;[/cyan]\n"
        "  [cyan]SHOW TABLES;[/cyan]",
        title="Recovery Guide",
        border_style="red",
    ))

    # Hiển thị danh sách file backup hiện có
    backup_dir = Path("backup_files")
    if backup_dir.exists():
        files = sorted(backup_dir.glob("*.sql"), reverse=True)
        if files:
            console.print("\n  [bold]Các file backup hiện có:[/bold]")
            rows = []
            for f in files[:10]:
                stat = f.stat()
                rows.append({
                    "File": f.name,
                    "Kích thước": f"{stat.st_size // 1024} KB",
                    "Ngày tạo": datetime.fromtimestamp(stat.st_mtime).strftime("%d/%m/%Y %H:%M"),
                })
            print_table(rows, "Danh sách backup", style="yellow")
        else:
            info("Chưa có file backup nào. Chạy 'Backup Database' trước.")
    else:
        info("Thư mục backup_files chưa tồn tại.")

    # Thực hiện restore nếu user muốn
    do_restore = questionary.confirm(
        "Bạn muốn restore từ file backup ngay bây giờ?"
    ).ask()

    if do_restore:
        from dotenv import load_dotenv
        load_dotenv()
        db_user = os.getenv("DB_USER", "root")
        db_pass = os.getenv("DB_PASS", "")
        db_host = os.getenv("DB_HOST", "localhost")

        sql_file = questionary.path("Chọn file .sql cần restore:").ask()
        if not sql_file or not Path(sql_file).exists():
            error("File không tồn tại.")
        else:
            warning("CẢNH BÁO: Restore sẽ ghi đè dữ liệu hiện tại!")
            if questionary.confirm("Chắc chắn muốn restore?").ask():
                cmd = ["mysql", f"-u{db_user}", f"-p{db_pass}", f"-h{db_host}"]
                try:
                    with open(sql_file, "r", encoding="utf-8") as f:
                        result = subprocess.run(cmd, stdin=f, capture_output=True, text=True, timeout=300)
                    if result.returncode == 0:
                        success(f"Restore thành công từ: {sql_file}")
                    else:
                        error(f"Restore thất bại: {result.stderr[:200]}")
                except Exception as e:
                    error(f"Lỗi: {e}")

    pause()


# ════════════════════════════════════════════════════════════
# 6. HIỂN THỊ BACKUP LOG
# ════════════════════════════════════════════════════════════
def view_backup_log():
    console.rule("[bold]Lịch sử Backup[/bold]")
    try:
        with get_db() as db:
            rows = db.execute(text("""
                SELECT log_id AS ID,
                       DATE_FORMAT(backup_time,'%d/%m/%Y %H:%i') AS 'Thời gian',
                       backup_file AS 'File',
                       backup_type AS 'Loại',
                       status AS 'Kết quả',
                       notes AS 'Ghi chú'
                FROM backup_log
                ORDER BY backup_time DESC
                LIMIT 20
            """)).fetchall()
        print_table([dict(r._mapping) for r in rows], "Lịch sử backup", style="cyan")
    except Exception as e:
        warning(f"Bảng backup_log chưa tồn tại hoặc lỗi: {e}")
        info("Chạy phase4_security.sql để tạo bảng backup_log và stored procedure.")
    pause()


# ════════════════════════════════════════════════════════════
# 7. PERFORMANCE REPORT
# ════════════════════════════════════════════════════════════
def performance_report():
    console.rule("[bold magenta]Thống kê hiệu suất Database[/bold magenta]")
    try:
        with get_db() as db:
            # Kích thước bảng
            size_rows = db.execute(text("""
                SELECT table_name AS 'Bảng',
                       table_rows AS 'Số dòng',
                       ROUND(data_length / 1024, 1) AS 'Data (KB)',
                       ROUND(index_length / 1024, 1) AS 'Index (KB)',
                       ROUND((data_length + index_length) / 1024, 1) AS 'Tổng (KB)'
                FROM information_schema.tables
                WHERE table_schema = 'event_management'
                  AND table_type = 'BASE TABLE'
                ORDER BY (data_length + index_length) DESC
            """)).fetchall()
            print_table([dict(r._mapping) for r in size_rows], "Kích thước bảng", style="magenta")

            # Số lượng indexes
            idx_rows = db.execute(text("""
                SELECT table_name AS 'Bảng', COUNT(*) AS 'Số Index'
                FROM information_schema.statistics
                WHERE table_schema = 'event_management'
                GROUP BY table_name ORDER BY COUNT(*) DESC
            """)).fetchall()
            print_table([dict(r._mapping) for r in idx_rows], "Số lượng Index mỗi bảng", style="blue")

    except Exception as e:
        error(f"Lỗi: {e}")
    pause()


# ════════════════════════════════════════════════════════════
# MENU CHÍNH
# ════════════════════════════════════════════════════════════
def security_admin_menu():
    while True:
        choice = questionary.select(
            "Bảo mật & Quản trị (Giai đoạn 4):",
            choices=[
                "1. RBAC Matrix    — Xem ma trận phân quyền",
                "2. Column Security — Demo ẩn Email/Phone/Address",
                "3. User Grants    — Kiểm tra quyền của user cụ thể",
                "4. Backup DB      — Chạy mysqldump",
                "5. Recovery Guide — Hướng dẫn restore",
                "6. Backup Log     — Lịch sử backup",
                "7. Performance    — Thống kê kích thước & index",
                "← Quay lại",
            ]
        ).ask()

        if not choice or choice.startswith("←"):
            break
        elif choice.startswith("1"): demo_rbac()
        elif choice.startswith("2"): demo_column_security()
        elif choice.startswith("3"): check_user_grants()
        elif choice.startswith("4"): run_backup()
        elif choice.startswith("5"): guide_recovery()
        elif choice.startswith("6"): view_backup_log()
        elif choice.startswith("7"): performance_report()


if __name__ == "__main__":
    security_admin_menu()
