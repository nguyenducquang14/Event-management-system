"""
app/cli/guest_menu.py
Quản lý khách mời — CRUD
"""

import re
import questionary
from sqlalchemy import text
from app.config import get_db
from app.cli.utils import (
    console, print_table, success, error, info, warning, pause, prompt_int
)


def _row2dict(row) -> dict:
    return dict(row._mapping)


def _valid_email(email: str) -> bool:
    return bool(re.match(r"[^@]+@[^@]+\.[^@]+", email))


# ── Danh sách ────────────────────────────────────────────────
def list_guests():
    console.rule("[bold cyan]Danh sách khách mời[/bold cyan]")
    with get_db() as db:
        rows = db.execute(text("""
            SELECT guest_id AS ID, guest_name AS "Họ tên",
                   email AS "Email", phone_number AS "Điện thoại",
                   address AS "Địa chỉ"
            FROM Guests ORDER BY guest_name
        """)).fetchall()
    print_table([_row2dict(r) for r in rows], "Tất cả khách mời")
    pause()


def search_guests():
    kw = console.input("  [cyan]Tìm kiếm (tên hoặc email)[/cyan]: ").strip()
    with get_db() as db:
        rows = db.execute(text("""
            SELECT guest_id AS ID, guest_name AS "Họ tên",
                   email AS "Email", phone_number AS "Điện thoại"
            FROM Guests
            WHERE guest_name LIKE :kw OR email LIKE :kw
            ORDER BY guest_name
        """), {"kw": f"%{kw}%"}).fetchall()
    print_table([_row2dict(r) for r in rows], f"Kết quả tìm '{kw}'", style="yellow")
    pause()


def view_guest_events():
    guest_id = prompt_int("Nhập Guest ID")
    with get_db() as db:
        guest = db.execute(
            text("SELECT guest_name FROM Guests WHERE guest_id = :gid"),
            {"gid": guest_id}
        ).fetchone()
        rows = db.execute(text("""
            SELECT e.event_id AS "Event ID", e.event_name AS "Sự kiện",
                   DATE_FORMAT(e.start_time,'%d/%m/%Y') AS "Ngày",
                   r.attendance_status AS "Trạng thái", r.checkin_time AS "Check-in"
            FROM Registrations r
            JOIN Events e ON r.event_id = e.event_id
            WHERE r.guest_id = :gid
            ORDER BY e.start_time
        """), {"gid": guest_id}).fetchall()

    title = f"Sự kiện của khách #{guest_id}" + (f" — {guest.guest_name}" if guest else "")
    print_table([_row2dict(r) for r in rows], title, style="magenta")
    pause()


# ── Tạo mới ─────────────────────────────────────────────────
def create_guest():
    console.rule("[bold green]Thêm khách mời mới[/bold green]")
    name  = console.input("  [cyan]Họ tên[/cyan]    : ").strip()
    email = console.input("  [cyan]Email[/cyan]     : ").strip()
    phone = console.input("  [cyan]Điện thoại[/cyan]: ").strip()
    addr  = console.input("  [cyan]Địa chỉ[/cyan]  : ").strip()

    if not _valid_email(email):
        error("Email không hợp lệ.")
        pause()
        return

    if not questionary.confirm("Xác nhận thêm?").ask():
        info("Đã hủy.")
        pause()
        return

    try:
        with get_db() as db:
            db.execute(text("""
                INSERT INTO Guests (guest_name, email, phone_number, address)
                VALUES (:name, :email, :phone, :addr)
            """), {"name": name, "email": email, "phone": phone or None, "addr": addr or None})
        success(f"Đã thêm khách mời '{name}'!")
    except Exception as e:
        if "Duplicate" in str(e):
            error("Email đã tồn tại trong hệ thống.")
        else:
            error(f"Lỗi: {e}")
    pause()


# ── Cập nhật ─────────────────────────────────────────────────
def update_guest():
    guest_id = prompt_int("Nhập Guest ID cần sửa")
    with get_db() as db:
        row = db.execute(
            text("SELECT * FROM Guests WHERE guest_id = :gid"),
            {"gid": guest_id}
        ).fetchone()

    if not row:
        error("Không tìm thấy khách mời.")
        pause()
        return

    g = _row2dict(row)
    console.print(f"\n  Tên    : [bold]{g['guest_name']}[/bold]")
    console.print(f"  Email  : {g['email']}")
    console.print(f"  Phone  : {g['phone_number']}\n")

    name  = console.input("  Tên mới (Enter giữ nguyên): ").strip() or g["guest_name"]
    email = console.input("  Email mới (Enter giữ): ").strip() or g["email"]
    phone = console.input("  Phone mới (Enter giữ): ").strip() or g["phone_number"]
    addr  = console.input("  Địa chỉ mới (Enter giữ): ").strip() or g["address"]

    try:
        with get_db() as db:
            db.execute(text("""
                UPDATE Guests
                SET guest_name=:name, email=:email, phone_number=:phone, address=:addr
                WHERE guest_id=:gid
            """), {"name": name, "email": email, "phone": phone, "addr": addr, "gid": guest_id})
        success("Cập nhật thông tin khách mời thành công!")
    except Exception as e:
        error(f"Lỗi: {e}")
    pause()


# ── Xóa ──────────────────────────────────────────────────────
def delete_guest():
    guest_id = prompt_int("Nhập Guest ID cần xóa")
    with get_db() as db:
        row = db.execute(
            text("SELECT guest_name FROM Guests WHERE guest_id = :gid"),
            {"gid": guest_id}
        ).fetchone()

    if not row:
        error("Không tìm thấy khách mời.")
        pause()
        return

    warning(f"Sẽ xóa: {row.guest_name} và toàn bộ lịch sử đăng ký!")
    if not questionary.confirm("Chắc chắn xóa?").ask():
        info("Đã hủy.")
        pause()
        return

    try:
        with get_db() as db:
            db.execute(text("DELETE FROM Guests WHERE guest_id = :gid"), {"gid": guest_id})
        success(f"Đã xóa khách mời #{guest_id}.")
    except Exception as e:
        error(f"Lỗi: {e}")
    pause()


# ── Menu ─────────────────────────────────────────────────────
def guest_menu():
    while True:
        choice = questionary.select(
            "Quản lý khách mời:",
            choices=[
                "1. Xem tất cả khách mời",
                "2. Tìm kiếm khách mời",
                "3. Xem sự kiện của khách",
                "4. Thêm khách mời mới",
                "5. Cập nhật thông tin",
                "6. Xóa khách mời",
                "← Quay lại menu chính",
            ]
        ).ask()

        if not choice or choice.startswith("←"):
            break
        elif choice.startswith("1"): list_guests()
        elif choice.startswith("2"): search_guests()
        elif choice.startswith("3"): view_guest_events()
        elif choice.startswith("4"): create_guest()
        elif choice.startswith("5"): update_guest()
        elif choice.startswith("6"): delete_guest()
