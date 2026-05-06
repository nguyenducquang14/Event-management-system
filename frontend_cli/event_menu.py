"""
app/cli/event_menu.py
Quản lý sự kiện — CRUD + xem View từ database
"""

import questionary
from sqlalchemy import text
from app.config import get_db
from app.models import Event, Venue, Organizer
from app.cli.utils import (
    console, print_table, success, error, info, warning, pause, prompt_int
)
from app.cli.auth_utils import requires_permission


# ── Helper: chuyển row proxy → dict ─────────────────────────
def _row2dict(row) -> dict:
    return dict(row._mapping)


# ── Xem danh sách sự kiện ────────────────────────────────────
def list_events():
    console.rule("[bold cyan]Danh sách sự kiện[/bold cyan]")
    with get_db() as db:
        rows = db.execute(text("""
            SELECT e.event_id      AS ID,
                   e.event_name    AS "Tên sự kiện",
                   DATE_FORMAT(e.start_time,'%d/%m/%Y %H:%i') AS "Bắt đầu",
                   DATE_FORMAT(e.end_time,  '%d/%m/%Y %H:%i') AS "Kết thúc",
                   v.venue_name    AS "Địa điểm",
                   e.status        AS "Trạng thái",
                   e.max_capacity  AS "Sức chứa"
            FROM Events e
            JOIN Venues v ON e.venue_id = v.venue_id
            ORDER BY e.start_time
        """)).fetchall()
    print_table([_row2dict(r) for r in rows], "Tất cả sự kiện")
    pause()


def list_upcoming():
    console.rule("[bold blue]Sự kiện sắp diễn ra[/bold blue]")
    with get_db() as db:
        rows = db.execute(text("SELECT * FROM view_upcoming_events")).fetchall()
    print_table([_row2dict(r) for r in rows], "Upcoming events", style="blue")
    pause()


# ── Xem chi tiết ─────────────────────────────────────────────
def view_event_detail():
    event_id = prompt_int("Nhập Event ID")
    with get_db() as db:
        row = db.execute(text("""
            SELECT e.*,
                   v.venue_name, v.address AS venue_address, v.capacity AS venue_capacity,
                   o.organizer_name,
                   fn_attendance_rate(e.event_id) AS attendance_pct,
                   fn_event_balance(e.event_id)   AS net_balance
            FROM Events e
            JOIN Venues v     ON e.venue_id     = v.venue_id
            JOIN Organizers o ON e.organizer_id = o.organizer_id
            WHERE e.event_id = :eid
        """), {"eid": event_id}).fetchone()

    if not row:
        error(f"Không tìm thấy sự kiện #{event_id}")
    else:
        d = _row2dict(row)
        print_table([d], f"Chi tiết sự kiện #{event_id}")
    pause()


# ── Tạo sự kiện mới ─────────────────────────────────────────
def create_event():
    console.rule("[bold green]Tạo sự kiện mới[/bold green]")

    # Hiển thị danh sách venue và organizer để chọn
    with get_db() as db:
        venues = db.execute(text(
            "SELECT venue_id, venue_name, capacity, availability_status FROM Venues ORDER BY venue_id"
        )).fetchall()
        organizers = db.execute(text(
            "SELECT organizer_id, organizer_name FROM Organizers ORDER BY organizer_id"
        )).fetchall()

    print_table([_row2dict(r) for r in venues], "Danh sách địa điểm", style="magenta")
    print_table([_row2dict(r) for r in organizers], "Danh sách ban tổ chức", style="yellow")

    try:
        name     = console.input("  [cyan]Tên sự kiện[/cyan]: ").strip()
        start    = console.input("  [cyan]Bắt đầu (YYYY-MM-DD HH:MM)[/cyan]: ").strip()
        end      = console.input("  [cyan]Kết thúc (YYYY-MM-DD HH:MM)[/cyan]: ").strip()
        vid      = prompt_int("Venue ID")
        oid      = prompt_int("Organizer ID")
        status   = questionary.select("Trạng thái ban đầu:",
                       choices=["Draft", "Scheduled"]).ask()
        max_cap  = prompt_int("Sức chứa tối đa (Enter = không giới hạn)", allow_empty=True)
        desc     = console.input("  [cyan]Mô tả (Enter để bỏ qua)[/cyan]: ").strip() or None

        if not questionary.confirm("Xác nhận tạo sự kiện?").ask():
            info("Đã hủy.")
            pause()
            return

        with get_db() as db:
            db.execute(text("""
                INSERT INTO Events (event_name, start_time, end_time, venue_id,
                                    organizer_id, status, max_capacity, description)
                VALUES (:name, :start, :end, :vid, :oid, :status, :cap, :desc)
            """), {
                "name": name, "start": start, "end": end,
                "vid": vid, "oid": oid, "status": status,
                "cap": max_cap, "desc": desc,
            })
        success(f"Đã tạo sự kiện '{name}' thành công!")

    except Exception as e:
        error(f"Lỗi khi tạo sự kiện: {e}")

    pause()


# ── Cập nhật trạng thái ──────────────────────────────────────
def update_event_status():
    event_id = prompt_int("Nhập Event ID cần cập nhật")
    status = questionary.select(
        "Chọn trạng thái mới:",
        choices=["Draft", "Scheduled", "Full", "Completed", "Cancelled"]
    ).ask()

    try:
        with get_db() as db:
            rows = db.execute(text(
                "UPDATE Events SET status = :s WHERE event_id = :eid"
            ), {"s": status, "eid": event_id}).rowcount
        if rows:
            success(f"Cập nhật trạng thái sự kiện #{event_id} → {status}")
        else:
            error("Không tìm thấy sự kiện.")
    except Exception as e:
        error(f"Lỗi: {e}")
    pause()


# ── Cập nhật thông tin ───────────────────────────────────────
def update_event():
    event_id = prompt_int("Nhập Event ID cần sửa")
    with get_db() as db:
        row = db.execute(
            text("SELECT * FROM Events WHERE event_id = :eid"),
            {"eid": event_id}
        ).fetchone()

    if not row:
        error("Không tìm thấy sự kiện.")
        pause()
        return

    ev = _row2dict(row)
    console.print(f"\n  Tên hiện tại   : [bold]{ev['event_name']}[/bold]")
    console.print(f"  Bắt đầu        : {ev['start_time']}")
    console.print(f"  Kết thúc       : {ev['end_time']}\n")

    name  = console.input(f"  Tên mới (Enter giữ nguyên): ").strip() or ev["event_name"]
    start = console.input(f"  Bắt đầu mới (Enter giữ): ").strip() or str(ev["start_time"])
    end   = console.input(f"  Kết thúc mới (Enter giữ): ").strip() or str(ev["end_time"])
    desc  = console.input(f"  Mô tả mới (Enter giữ): ").strip() or ev.get("description", "")

    try:
        with get_db() as db:
            db.execute(text("""
                UPDATE Events
                SET event_name=:name, start_time=:start, end_time=:end, description=:desc
                WHERE event_id=:eid
            """), {"name": name, "start": start, "end": end, "desc": desc, "eid": event_id})
        success("Cập nhật thông tin sự kiện thành công!")
    except Exception as e:
        error(f"Lỗi: {e}")
    pause()


# ── Xóa sự kiện ─────────────────────────────────────────────
@requires_permission("delete_event")
def delete_event(current_user=None):
    if current_user:
        info(f"Tài khoản [bold cyan]{current_user.get('username')}[/bold cyan] đang thực hiện quyền [bold yellow]delete_event[/bold yellow].")
        
    event_id = prompt_int("Nhập Event ID cần xóa")
    with get_db() as db:
        row = db.execute(
            text("SELECT event_name FROM Events WHERE event_id = :eid"),
            {"eid": event_id}
        ).fetchone()

    if not row:
        error("Không tìm thấy sự kiện.")
        pause()
        return

    warning(f"Sẽ xóa: {row.event_name} và toàn bộ đăng ký + tài chính liên quan!")
    if not questionary.confirm("Chắc chắn xóa?").ask():
        info("Đã hủy.")
        pause()
        return

    try:
        with get_db() as db:
            db.execute(text("DELETE FROM Events WHERE event_id = :eid"), {"eid": event_id})
        success(f"Đã xóa sự kiện #{event_id}.")
    except Exception as e:
        error(f"Lỗi: {e}")
    pause()


# ── Menu chính ───────────────────────────────────────────────
def event_menu():
    while True:
        choice = questionary.select(
            "Quản lý sự kiện:",
            choices=[
                "1. Xem tất cả sự kiện",
                "2. Sự kiện sắp diễn ra",
                "3. Xem chi tiết sự kiện",
                "4. Tạo sự kiện mới",
                "5. Cập nhật thông tin sự kiện",
                "6. Cập nhật trạng thái",
                "7. Xóa sự kiện",
                "← Quay lại menu chính",
            ]
        ).ask()

        if not choice or choice.startswith("←"):
            break
        elif choice.startswith("1"): list_events()
        elif choice.startswith("2"): list_upcoming()
        elif choice.startswith("3"): view_event_detail()
        elif choice.startswith("4"): create_event()
        elif choice.startswith("5"): update_event()
        elif choice.startswith("6"): update_event_status()
        elif choice.startswith("7"): delete_event()
