"""
app/cli/advanced_demo.py
Demo & kiểm thử toàn bộ đối tượng nâng cao Giai đoạn 3
Gọi: python -m app.cli.advanced_demo  (hoặc chọn từ menu)
"""

import questionary
from sqlalchemy import text
from rich.table import Table
from rich.panel import Panel
from rich.columns import Columns
from rich import box

from app.config import get_db, engine
from app.cli.utils import console, print_table, success, error, info, warning, pause


def _row2dict(row) -> dict:
    return dict(row._mapping)


def _call_proc(proc_name: str, in_params: list) -> str:
    """Gọi Stored Procedure có OUT parameter, trả về chuỗi kết quả."""
    conn = engine.raw_connection()
    try:
        cur = conn.cursor()
        cur.callproc(proc_name, in_params + [""])
        out_idx = len(in_params)
        cur.execute(f"SELECT @_{proc_name}_{out_idx}")
        row = cur.fetchone()
        conn.commit()
        return row[0] if row else "—"
    except Exception as e:
        conn.rollback()
        return f"ERROR: {e}"
    finally:
        cur.close()
        conn.close()


# ════════════════════════════════════════════════════════════
# 1. DEMO INDEXES
# ════════════════════════════════════════════════════════════
def demo_indexes():
    console.rule("[bold cyan]DEMO: INDEXES — Kiểm tra EXPLAIN[/bold cyan]")

    queries = {
        "Lọc sự kiện theo thời gian + status (dùng idx_events_start_time)":
            "EXPLAIN SELECT event_id, event_name FROM Events WHERE start_time >= NOW() AND status='Scheduled'",
        "Tìm khách theo email (dùng idx_guests_email)":
            "EXPLAIN SELECT * FROM Guests WHERE email = 'an.nguyen@email.com'",
        "Tra cứu đăng ký (composite idx_registrations_event_guest)":
            "EXPLAIN SELECT * FROM Registrations WHERE event_id = 1 AND guest_id = 1",
        "Lọc tài chính theo loại (idx_finances_event_type)":
            "EXPLAIN SELECT SUM(amount) FROM Finances WHERE event_id=1 AND type='Income'",
    }

    with get_db() as db:
        for desc, sql in queries.items():
            console.print(f"\n  [yellow]{desc}[/yellow]")
            rows = db.execute(text(sql)).fetchall()
            print_table([_row2dict(r) for r in rows], "", style="yellow")

    info("type=ref/range: index đang được sử dụng  |  type=ALL: full scan (không tốt)")
    pause()


# ════════════════════════════════════════════════════════════
# 2. DEMO VIEWS
# ════════════════════════════════════════════════════════════
def demo_views():
    console.rule("[bold blue]DEMO: VIEWS — 5 khung nhìn báo cáo[/bold blue]")

    views = {
        "v_upcoming_events":           ("Sự kiện sắp diễn ra", "blue"),
        "v_event_attendance_summary":  ("Thống kê tham dự",    "cyan"),
        "v_finance_balance":           ("Số dư tài chính",     "green"),
        "v_guest_activity":            ("Hoạt động khách mời", "magenta"),
        "v_venue_schedule":            ("Lịch địa điểm",       "yellow"),
    }

    choice = questionary.select(
        "Chọn View muốn xem:",
        choices=list(views.keys()) + ["Xem tất cả"]
    ).ask()

    selected = list(views.keys()) if choice == "Xem tất cả" else [choice]

    with get_db() as db:
        for view_name in selected:
            title, style = views[view_name]
            rows = db.execute(text(f"SELECT * FROM {view_name}")).fetchall()
            print_table([_row2dict(r) for r in rows], title, style=style)

    pause()


# ════════════════════════════════════════════════════════════
# 3. DEMO USER DEFINED FUNCTIONS
# ════════════════════════════════════════════════════════════
def demo_functions():
    console.rule("[bold green]DEMO: USER DEFINED FUNCTIONS[/bold green]")

    with get_db() as db:
        # Lấy tất cả sự kiện có dữ liệu
        events = db.execute(text(
            "SELECT event_id, event_name FROM Events ORDER BY event_id"
        )).fetchall()

        rows = []
        for ev in events:
            eid = ev.event_id
            rate = db.execute(text(f"SELECT fn_participation_rate({eid}) AS r")).fetchone().r
            bal  = db.execute(text(f"SELECT fn_event_balance({eid}) AS b")).fetchone().b
            cnt  = db.execute(text(f"SELECT fn_count_registered({eid}) AS c")).fetchone().c
            slots = db.execute(text(f"SELECT fn_slots_remaining({eid}) AS s")).fetchone().s

            rows.append({
                "Event ID":           eid,
                "Tên sự kiện":        ev.event_name[:35],
                "fn_participation_rate": f"{float(rate) if rate else 0:.1f}%",
                "fn_event_balance":   f"{float(bal):+,.0f}" if bal else "0",
                "fn_count_registered": cnt or 0,
                "fn_slots_remaining": str(slots) if slots is not None else "∞ (không giới hạn)",
            })

    print_table(rows, "Kết quả 4 User Defined Functions trên tất cả sự kiện", style="green")

    # Gọi function riêng lẻ theo ID
    event_id = questionary.text("Nhập Event ID để xem chi tiết (Enter bỏ qua):").ask()
    if event_id and event_id.isdigit():
        eid = int(event_id)
        with get_db() as db:
            rate  = db.execute(text(f"SELECT fn_participation_rate({eid}) AS r")).fetchone().r
            bal   = db.execute(text(f"SELECT fn_event_balance({eid}) AS b")).fetchone().b
            slots = db.execute(text(f"SELECT fn_slots_remaining({eid}) AS s")).fetchone().s

        r_color = "green" if (rate or 0) >= 70 else ("yellow" if (rate or 0) >= 40 else "red")
        b_color = "green" if (bal or 0) >= 0 else "red"
        console.print(Panel(
            f"  [bold]Tỉ lệ tham dự  :[/bold] [{r_color}]{float(rate or 0):.2f}%[/{r_color}]\n"
            f"  [bold]Số dư tài chính:[/bold] [{b_color}]{float(bal or 0):+,.0f} VND[/{b_color}]\n"
            f"  [bold]Chỗ còn trống  :[/bold] {'∞' if slots is None else slots}",
            title=f"Function results — Event #{eid}",
            border_style="green",
        ))

    pause()


# ════════════════════════════════════════════════════════════
# 4. DEMO STORED PROCEDURES
# ════════════════════════════════════════════════════════════
def demo_procedures():
    console.rule("[bold magenta]DEMO: STORED PROCEDURES[/bold magenta]")

    proc = questionary.select(
        "Chọn Stored Procedure muốn demo:",
        choices=[
            "sp_check_in_guest         — Check-in khách",
            "sp_add_finance_record     — Ghi thu/chi",
            "sp_register_guest_safe    — Đăng ký an toàn",
            "sp_mark_event_completed   — Kết thúc sự kiện",
            "sp_get_event_report       — Báo cáo theo kỳ",
        ]
    ).ask()

    if proc.startswith("sp_check_in_guest"):
        console.print("\n  Gọi: [bold cyan]sp_check_in_guest(event_id, guest_id, @result)[/bold cyan]")
        eid = int(questionary.text("Event ID:").ask())
        gid = int(questionary.text("Guest ID:").ask())
        result = _call_proc("sp_check_in_guest", [eid, gid])
        _print_proc_result(result, "sp_check_in_guest")

    elif proc.startswith("sp_add_finance_record"):
        console.print("\n  Gọi: [bold cyan]sp_add_finance_record(event_id, type, amount, desc, @result)[/bold cyan]")
        eid   = int(questionary.text("Event ID:").ask())
        ftype = questionary.select("Loại:", choices=["Income", "Expense"]).ask()
        amt   = float(questionary.text("Số tiền (VND):").ask())
        desc  = questionary.text("Mô tả:").ask()
        result = _call_proc("sp_add_finance_record", [eid, ftype, amt, desc])
        _print_proc_result(result, "sp_add_finance_record")

    elif proc.startswith("sp_register_guest_safe"):
        console.print("\n  Gọi: [bold cyan]sp_register_guest_safe(event_id, guest_id, @result)[/bold cyan]")
        eid = int(questionary.text("Event ID:").ask())
        gid = int(questionary.text("Guest ID:").ask())
        result = _call_proc("sp_register_guest_safe", [eid, gid])
        _print_proc_result(result, "sp_register_guest_safe")

    elif proc.startswith("sp_mark_event_completed"):
        console.print("\n  Gọi: [bold cyan]sp_mark_event_completed(event_id, @result)[/bold cyan]")
        eid = int(questionary.text("Event ID:").ask())
        if questionary.confirm(f"Xác nhận kết thúc Event #{eid}? (No-show tất cả Registered)").ask():
            result = _call_proc("sp_mark_event_completed", [eid])
            _print_proc_result(result, "sp_mark_event_completed")

    elif proc.startswith("sp_get_event_report"):
        console.print("\n  Gọi: [bold cyan]sp_get_event_report(from_date, to_date)[/bold cyan]")
        fd = questionary.text("Từ ngày (YYYY-MM-DD):").ask()
        td = questionary.text("Đến ngày (YYYY-MM-DD):").ask()
        conn = engine.raw_connection()
        try:
            cur = conn.cursor()
            cur.callproc("sp_get_event_report", [fd, td])
            for rs in cur.stored_results():
                rows = [dict(zip([d[0] for d in rs.description], r)) for r in rs.fetchall()]
                print_table(rows, f"Báo cáo {fd} → {td}", style="cyan")
        finally:
            cur.close(); conn.close()

    pause()


def _print_proc_result(result: str, proc_name: str):
    if result.startswith("SUCCESS"):
        success(f"[{proc_name}]  {result}")
    elif result.startswith("ERROR"):
        error(f"[{proc_name}]  {result}")
    else:
        info(result)


# ════════════════════════════════════════════════════════════
# 5. DEMO TRIGGERS
# ════════════════════════════════════════════════════════════
def demo_triggers():
    console.rule("[bold red]DEMO: TRIGGERS — Kiểm tra tự động[/bold red]")

    trigger_info = [
        {
            "Tên trigger":   "trg_check_capacity_before_register",
            "Thời điểm":    "BEFORE INSERT",
            "Bảng":         "Registrations",
            "Mục đích":     "Chặn đăng ký khi max_capacity đầy",
        },
        {
            "Tên trigger":   "trg_auto_set_full_status",
            "Thời điểm":    "AFTER INSERT",
            "Bảng":         "Registrations",
            "Mục đích":     "Tự động đặt Events.status = 'Full'",
        },
        {
            "Tên trigger":   "trg_restore_scheduled_on_cancel",
            "Thời điểm":    "AFTER DELETE",
            "Bảng":         "Registrations",
            "Mục đích":     "Khôi phục 'Scheduled' khi hủy đăng ký",
        },
        {
            "Tên trigger":   "trg_prevent_duplicate_registration",
            "Thời điểm":    "BEFORE INSERT",
            "Bảng":         "Registrations",
            "Mục đích":     "Ngăn đăng ký trùng lặp, thông báo rõ",
        },
        {
            "Tên trigger":   "trg_log_checkin_timestamp",
            "Thời điểm":    "BEFORE UPDATE",
            "Bảng":         "Registrations",
            "Mục đích":     "Ghi checkin_time khi status → Attended",
        },
    ]

    print_table(trigger_info, "5 Triggers đã triển khai", style="red")

    demo = questionary.select(
        "Chọn demo trigger:",
        choices=[
            "Demo 1: Thử đăng ký khi đã Full (trg_check_capacity_before_register)",
            "Demo 2: Đăng ký trùng lặp (trg_prevent_duplicate_registration)",
            "Demo 3: Auto Full → Restore Scheduled",
            "Bỏ qua",
        ]
    ).ask()

    if "Demo 1" in demo:
        console.print("\n  Thiết lập Event #2 với max_capacity=1 và thêm 1 người...")
        with get_db() as db:
            db.execute(text("UPDATE Events SET max_capacity=1 WHERE event_id=2"))
            # Đảm bảo có ít nhất 1 đăng ký
            try:
                db.execute(text(
                    "INSERT IGNORE INTO Registrations (event_id,guest_id,registration_date) VALUES (2,1,CURRENT_DATE)"
                ))
            except Exception:
                pass

        console.print("  Thử đăng ký Guest #2 vào Event #2 (đã đầy chỗ)...")
        result = _call_proc("sp_register_guest_safe", [2, 2])
        _print_proc_result(result, "trigger demo")
        info("Trigger trg_check_capacity_before_register đã chặn insert thành công!")

        # Khôi phục
        with get_db() as db:
            db.execute(text("UPDATE Events SET max_capacity=70 WHERE event_id=2"))

    elif "Demo 2" in demo:
        console.print("\n  Kiểm tra đăng ký trùng: Guest #1 vào Event #1 (đã tồn tại)...")
        result = _call_proc("sp_register_guest_safe", [1, 1])
        _print_proc_result(result, "trigger demo")

    elif "Demo 3" in demo:
        console.print("\n  Xem trạng thái Event #2 trước và sau khi xóa đăng ký...")
        with get_db() as db:
            before = db.execute(text(
                "SELECT status, fn_count_registered(event_id) AS dang_ky FROM Events WHERE event_id=2"
            )).fetchone()
            console.print(f"  Trước: status={before.status}, đăng ký={before.dang_ky}")

            db.execute(text(
                "DELETE FROM Registrations WHERE event_id=2 AND guest_id=1"
            ))

            after = db.execute(text(
                "SELECT status, fn_count_registered(event_id) AS dang_ky FROM Events WHERE event_id=2"
            )).fetchone()
            console.print(f"  Sau  : status={after.status}, đăng ký={after.dang_ky}")
        success("Trigger trg_restore_scheduled_on_cancel đã khôi phục trạng thái!")

    pause()


# ════════════════════════════════════════════════════════════
# 6. MENU TỔNG HỢP
# ════════════════════════════════════════════════════════════
def advanced_demo_menu():
    while True:
        choice = questionary.select(
            "Demo Giai đoạn 3 — Advanced Objects:",
            choices=[
                "1. Indexes     — EXPLAIN query performance",
                "2. Views       — 5 khung nhìn báo cáo",
                "3. Functions   — 4 UDF tính toán",
                "4. Procedures  — 5 Stored Procedures",
                "5. Triggers    — 5 triggers tự động",
                "← Quay lại",
            ]
        ).ask()

        if not choice or choice.startswith("←"):
            break
        elif choice.startswith("1"): demo_indexes()
        elif choice.startswith("2"): demo_views()
        elif choice.startswith("3"): demo_functions()
        elif choice.startswith("4"): demo_procedures()
        elif choice.startswith("5"): demo_triggers()


if __name__ == "__main__":
    advanced_demo_menu()
