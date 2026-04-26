"""
app/cli/registration_menu.py
Quản lý đăng ký & check-in — gọi Stored Procedures từ Giai đoạn 1
"""

import questionary
from sqlalchemy import text
from app.config import get_db, engine
from app.cli.utils import (
    console, print_table, success, error, info, warning, pause, prompt_int
)


def _row2dict(row) -> dict:
    return dict(row._mapping)


# ── Gọi Stored Procedure qua raw connection ──────────────────
def _call_proc(proc_name: str, in_params: list) -> str:
    """
    Gọi SP có OUT parameter (chuỗi kết quả).
    Trả về chuỗi kết quả từ OUT parameter.
    """
    conn = engine.raw_connection()
    try:
        cur = conn.cursor()
        cur.callproc(proc_name, in_params + [""])   # "" là placeholder cho OUT
        # Lấy OUT param bằng SELECT @_<proc>_<idx>
        out_idx = len(in_params)
        cur.execute(f"SELECT @_{proc_name}_{out_idx}")
        row = cur.fetchone()
        conn.commit()
        return row[0] if row else "Không rõ kết quả."
    except Exception as e:
        conn.rollback()
        return f"ERROR: {e}"
    finally:
        cur.close()
        conn.close()


# ── Xem danh sách đăng ký ────────────────────────────────────
def list_registrations():
    console.rule("[bold cyan]Danh sách đăng ký[/bold cyan]")
    event_id = prompt_int("Lọc theo Event ID (Enter xem tất cả)", allow_empty=True)

    with get_db() as db:
        if event_id:
            rows = db.execute(text("""
                SELECT r.registration_id AS "Reg ID",
                       e.event_name AS "Sự kiện",
                       g.guest_name AS "Khách",
                       g.email AS "Email",
                       r.registration_date AS "Ngày ĐK",
                       r.attendance_status AS "Trạng thái",
                       r.checkin_time AS "Check-in"
                FROM Registrations r
                JOIN Events e ON r.event_id = e.event_id
                JOIN Guests g ON r.guest_id = g.guest_id
                WHERE r.event_id = :eid
                ORDER BY g.guest_name
            """), {"eid": event_id}).fetchall()
        else:
            rows = db.execute(text("""
                SELECT r.registration_id AS "Reg ID",
                       e.event_name AS "Sự kiện",
                       g.guest_name AS "Khách",
                       r.registration_date AS "Ngày ĐK",
                       r.attendance_status AS "Trạng thái"
                FROM Registrations r
                JOIN Events e ON r.event_id = e.event_id
                JOIN Guests g ON r.guest_id = g.guest_id
                ORDER BY r.registration_date DESC
                LIMIT 50
            """)).fetchall()

    print_table([_row2dict(r) for r in rows], "Danh sách đăng ký")
    pause()


# ── Đăng ký khách (gọi sp_register_guest) ───────────────────
def register_guest():
    console.rule("[bold green]Đăng ký khách tham dự sự kiện[/bold green]")

    # Hiển thị sự kiện upcoming để chọn
    with get_db() as db:
        events = db.execute(text("""
            SELECT event_id AS ID, event_name AS "Tên",
                   DATE_FORMAT(start_time,'%d/%m/%Y') AS "Ngày",
                   status AS "Trạng thái", max_capacity AS "Sức chứa"
            FROM Events
            WHERE status IN ('Draft','Scheduled')
            ORDER BY start_time
        """)).fetchall()
    print_table([_row2dict(r) for r in events], "Sự kiện có thể đăng ký", style="blue")

    event_id = prompt_int("Event ID")
    guest_id = prompt_int("Guest ID")

    console.print(f"\n  Đang gọi [bold]sp_register_guest({event_id}, {guest_id})[/bold]...")
    result = _call_proc("sp_register_guest", [event_id, guest_id])

    if result and result.startswith("OK"):
        success(result)
    else:
        error(result or "Không nhận được phản hồi từ database.")

    pause()


# ── Check-in (gọi sp_guest_checkin) ─────────────────────────
def checkin_guest():
    console.rule("[bold yellow]Check-in khách tham dự[/bold yellow]")

    event_id = prompt_int("Event ID")

    # Hiển thị khách chưa check-in
    with get_db() as db:
        rows = db.execute(text("""
            SELECT r.registration_id AS "Reg ID",
                   g.guest_id AS "Guest ID",
                   g.guest_name AS "Tên khách",
                   g.email AS "Email",
                   r.attendance_status AS "Trạng thái"
            FROM Registrations r
            JOIN Guests g ON r.guest_id = g.guest_id
            WHERE r.event_id = :eid AND r.attendance_status = 'Registered'
            ORDER BY g.guest_name
        """), {"eid": event_id}).fetchall()

    if not rows:
        info("Không có khách nào cần check-in (tất cả đã Attended hoặc No-show).")
        pause()
        return

    print_table([_row2dict(r) for r in rows], "Khách chưa check-in", style="yellow")
    guest_id = prompt_int("Guest ID cần check-in")

    console.print(f"\n  Đang gọi [bold]sp_guest_checkin({event_id}, {guest_id})[/bold]...")
    result = _call_proc("sp_guest_checkin", [event_id, guest_id])

    if result and result.startswith("OK"):
        success(result)
    else:
        error(result or "Không nhận được phản hồi.")

    pause()


# ── Đánh dấu No-show hàng loạt ──────────────────────────────
def mark_noshow():
    console.rule("[bold red]Đánh dấu No-show[/bold red]")
    event_id = prompt_int("Event ID")

    with get_db() as db:
        rows = db.execute(text("""
            SELECT COUNT(*) AS cnt FROM Registrations
            WHERE event_id = :eid AND attendance_status = 'Registered'
        """), {"eid": event_id}).fetchone()

    count = rows.cnt if rows else 0
    if count == 0:
        info("Không có khách nào ở trạng thái Registered.")
        pause()
        return

    warning(f"Sẽ đánh dấu {count} khách là No-show (sự kiện đã qua).")
    if not questionary.confirm("Xác nhận?").ask():
        info("Đã hủy.")
        pause()
        return

    try:
        with get_db() as db:
            db.execute(text("""
                UPDATE Registrations
                SET attendance_status = 'No-show'
                WHERE event_id = :eid AND attendance_status = 'Registered'
            """), {"eid": event_id})
        success(f"Đã đánh dấu {count} khách là No-show.")
    except Exception as e:
        error(f"Lỗi: {e}")
    pause()


# ── Hủy đăng ký ─────────────────────────────────────────────
def cancel_registration():
    reg_id = prompt_int("Nhập Registration ID cần hủy")

    with get_db() as db:
        row = db.execute(text("""
            SELECT r.*, g.guest_name, e.event_name
            FROM Registrations r
            JOIN Guests g ON r.guest_id = g.guest_id
            JOIN Events  e ON r.event_id = e.event_id
            WHERE r.registration_id = :rid
        """), {"rid": reg_id}).fetchone()

    if not row:
        error("Không tìm thấy đăng ký.")
        pause()
        return

    console.print(f"\n  Khách    : [bold]{row.guest_name}[/bold]")
    console.print(f"  Sự kiện  : {row.event_name}")
    console.print(f"  Trạng thái: {row.attendance_status}\n")

    if not questionary.confirm("Xác nhận hủy đăng ký?").ask():
        info("Đã hủy.")
        pause()
        return

    try:
        with get_db() as db:
            db.execute(text(
                "DELETE FROM Registrations WHERE registration_id = :rid"
            ), {"rid": reg_id})
        success(f"Đã hủy đăng ký #{reg_id}.")
    except Exception as e:
        error(f"Lỗi: {e}")
    pause()


# ── Menu ─────────────────────────────────────────────────────
def registration_menu():
    while True:
        choice = questionary.select(
            "Đăng ký & Check-in:",
            choices=[
                "1. Xem danh sách đăng ký",
                "2. Đăng ký khách tham dự  [gọi sp_register_guest]",
                "3. Check-in khách          [gọi sp_guest_checkin]",
                "4. Đánh dấu No-show hàng loạt",
                "5. Hủy đăng ký",
                "← Quay lại menu chính",
            ]
        ).ask()

        if not choice or choice.startswith("←"):
            break
        elif choice.startswith("1"): list_registrations()
        elif choice.startswith("2"): register_guest()
        elif choice.startswith("3"): checkin_guest()
        elif choice.startswith("4"): mark_noshow()
        elif choice.startswith("5"): cancel_registration()
