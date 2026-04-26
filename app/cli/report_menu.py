"""
app/cli/report_menu.py
Báo cáo & Thống kê — xuất Excel bằng pandas + openpyxl
Tích hợp view_event_summary, view_finance_report, view_venue_usage
"""

import os
from datetime import datetime
import questionary
import pandas as pd
from sqlalchemy import text
from app.config import get_db, engine
from app.cli.utils import (
    console, print_table, print_stat_cards, success, error,
    info, warning, pause, prompt_int,
)


def _row2dict(row) -> dict:
    return dict(row._mapping)


EXPORT_DIR = "exports"
os.makedirs(EXPORT_DIR, exist_ok=True)


# ── Dashboard tổng quan ──────────────────────────────────────
def dashboard():
    console.rule("[bold cyan]TỔNG QUAN HỆ THỐNG[/bold cyan]")
    with get_db() as db:
        stats_raw = db.execute(text("""
            SELECT
                (SELECT COUNT(*) FROM Events)                                        AS total_events,
                (SELECT COUNT(*) FROM Events WHERE status IN ('Draft','Scheduled'))  AS upcoming_events,
                (SELECT COUNT(*) FROM Guests)                                        AS total_guests,
                (SELECT COUNT(*) FROM Registrations)                                 AS total_registrations,
                (SELECT COUNT(*) FROM Registrations WHERE attendance_status='Attended') AS total_attended,
                (SELECT COALESCE(SUM(amount),0) FROM Finances WHERE type='Income')  AS total_income,
                (SELECT COALESCE(SUM(amount),0) FROM Finances WHERE type='Expense') AS total_expense
        """)).fetchone()

    s = _row2dict(stats_raw)
    s["net_balance"] = float(s["total_income"]) - float(s["total_expense"])
    s["total_income"]  = float(s["total_income"])
    s["total_expense"] = float(s["total_expense"])

    print_stat_cards(s)
    pause()


# ── Thống kê sự kiện ─────────────────────────────────────────
def event_summary():
    console.rule("[bold blue]Thống kê sự kiện[/bold blue]")
    with get_db() as db:
        rows = db.execute(text("""
            SELECT event_name AS "Sự kiện",
                   DATE_FORMAT(start_time,'%d/%m/%Y') AS "Ngày",
                   status AS "Trạng thái",
                   total_registered AS "Đăng ký",
                   total_attended   AS "Tham dự",
                   total_noshow     AS "No-show",
                   CONCAT(attendance_rate_pct,'%') AS "Tỉ lệ",
                   FORMAT(total_income, 0)  AS "Thu (VND)",
                   FORMAT(total_expense,0)  AS "Chi (VND)",
                   FORMAT(net_balance, 0)   AS "Số dư (VND)"
            FROM view_event_summary
            ORDER BY start_time
        """)).fetchall()
    print_table([_row2dict(r) for r in rows], "Tổng hợp sự kiện", style="blue")
    pause()


# ── Báo cáo theo khoảng thời gian ────────────────────────────
def report_by_date():
    console.rule("[bold yellow]Báo cáo theo khoảng thời gian[/bold yellow]")
    from_d = console.input("  [cyan]Từ ngày (YYYY-MM-DD)[/cyan]: ").strip()
    to_d   = console.input("  [cyan]Đến ngày (YYYY-MM-DD)[/cyan]: ").strip()

    with get_db() as db:
        rows = db.execute(text("""
            SELECT event_name AS "Sự kiện",
                   DATE_FORMAT(start_time,'%d/%m/%Y %H:%i') AS "Bắt đầu",
                   status AS "Trạng thái",
                   total_registered AS "Đăng ký",
                   total_attended AS "Tham dự",
                   CONCAT(attendance_rate_pct,'%') AS "Tỉ lệ",
                   FORMAT(net_balance,0) AS "Số dư (VND)"
            FROM view_event_summary
            WHERE DATE(start_time) BETWEEN :fd AND :td
            ORDER BY start_time
        """), {"fd": from_d, "td": to_d}).fetchall()

    print_table([_row2dict(r) for r in rows], f"Sự kiện từ {from_d} đến {to_d}", style="yellow")
    pause()


# ── Top khách tham dự nhiều nhất ─────────────────────────────
def top_guests():
    limit = prompt_int("Hiển thị top bao nhiêu khách (mặc định 10)", allow_empty=True) or 10
    with get_db() as db:
        rows = db.execute(text("""
            SELECT g.guest_id AS ID, g.guest_name AS "Họ tên", g.email AS "Email",
                   COUNT(r.event_id)                               AS "Tổng đăng ký",
                   SUM(r.attendance_status='Attended')             AS "Đã tham dự",
                   SUM(r.attendance_status='No-show')              AS "No-show",
                   ROUND(SUM(r.attendance_status='Attended')
                         / COUNT(r.event_id) * 100, 1)            AS "Tỉ lệ %"
            FROM Guests g
            JOIN Registrations r ON g.guest_id = r.guest_id
            GROUP BY g.guest_id, g.guest_name, g.email
            ORDER BY `Tổng đăng ký` DESC
            LIMIT :lim
        """), {"lim": limit}).fetchall()

    print_table([_row2dict(r) for r in rows], f"Top {limit} khách tích cực", style="magenta")
    pause()


# ── Tỉ lệ tham dự một sự kiện ────────────────────────────────
def attendance_rate():
    event_id = prompt_int("Nhập Event ID")
    with get_db() as db:
        rate = db.execute(
            text("SELECT fn_attendance_rate(:eid) AS rate"), {"eid": event_id}
        ).fetchone()
        event = db.execute(
            text("SELECT event_name FROM Events WHERE event_id = :eid"), {"eid": event_id}
        ).fetchone()

    if not rate:
        error("Không tìm thấy sự kiện.")
    else:
        r = float(rate.rate) if rate.rate else 0
        name = event.event_name if event else f"Event #{event_id}"
        color = "green" if r >= 70 else ("yellow" if r >= 40 else "red")
        console.print(
            f"\n  Sự kiện : [bold]{name}[/bold]"
            f"\n  Tỉ lệ tham dự: [bold {color}]{r}%[/bold {color}]\n"
        )
    pause()


# ── Thống kê địa điểm ────────────────────────────────────────
def venue_usage():
    console.rule("[bold magenta]Thống kê địa điểm[/bold magenta]")
    with get_db() as db:
        rows = db.execute(text("""
            SELECT venue_name AS "Địa điểm", capacity AS "Sức chứa",
                   availability_status AS "Trạng thái",
                   total_events AS "Tổng sự kiện",
                   completed_events AS "Đã hoàn thành"
            FROM view_venue_usage
            ORDER BY total_events DESC
        """)).fetchall()
    print_table([_row2dict(r) for r in rows], "Sử dụng địa điểm", style="magenta")
    pause()


# ── XUẤT EXCEL ───────────────────────────────────────────────
def export_excel():
    console.rule("[bold green]Xuất báo cáo Excel[/bold green]")

    sheets = questionary.checkbox(
        "Chọn sheet muốn xuất:",
        choices=[
            questionary.Choice("Tổng hợp sự kiện",   checked=True),
            questionary.Choice("Báo cáo tài chính",   checked=True),
            questionary.Choice("Danh sách khách mời", checked=True),
            questionary.Choice("Thống kê địa điểm",   checked=True),
            questionary.Choice("Danh sách đăng ký",   checked=False),
        ]
    ).ask()

    if not sheets:
        info("Không có sheet nào được chọn.")
        pause()
        return

    ts       = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = os.path.join(EXPORT_DIR, f"event_report_{ts}.xlsx")

    queries = {
        "Tổng hợp sự kiện": """
            SELECT event_name AS 'Sự kiện', start_time AS 'Bắt đầu',
                   status AS 'Trạng thái', total_registered AS 'Đăng ký',
                   total_attended AS 'Tham dự', attendance_rate_pct AS 'Tỉ lệ %',
                   total_income AS 'Thu (VND)', total_expense AS 'Chi (VND)',
                   net_balance AS 'Số dư (VND)'
            FROM view_event_summary ORDER BY start_time
        """,
        "Báo cáo tài chính": """
            SELECT event_name AS 'Sự kiện', type AS 'Loại',
                   amount AS 'Số tiền (VND)', description AS 'Mô tả',
                   transaction_date AS 'Ngày', organizer_name AS 'Người ghi'
            FROM view_finance_report
        """,
        "Danh sách khách mời": """
            SELECT guest_id AS 'ID', guest_name AS 'Họ tên',
                   email AS 'Email', phone_number AS 'Điện thoại', address AS 'Địa chỉ'
            FROM Guests ORDER BY guest_name
        """,
        "Thống kê địa điểm": """
            SELECT venue_name AS 'Địa điểm', capacity AS 'Sức chứa',
                   availability_status AS 'Trạng thái',
                   total_events AS 'Tổng sự kiện', completed_events AS 'Đã hoàn thành'
            FROM view_venue_usage ORDER BY total_events DESC
        """,
        "Danh sách đăng ký": """
            SELECT e.event_name AS 'Sự kiện', g.guest_name AS 'Khách',
                   g.email AS 'Email', r.registration_date AS 'Ngày ĐK',
                   r.attendance_status AS 'Trạng thái'
            FROM Registrations r
            JOIN Events e ON r.event_id = e.event_id
            JOIN Guests g ON r.guest_id = g.guest_id
            ORDER BY e.event_name, g.guest_name
        """,
    }

    try:
        with pd.ExcelWriter(filename, engine="openpyxl") as writer:
            for sheet_name in sheets:
                sql = queries.get(sheet_name)
                if not sql:
                    continue
                console.print(f"  Đang xuất sheet: [cyan]{sheet_name}[/cyan]...")
                df = pd.read_sql(sql, engine)

                df.to_excel(writer, sheet_name=sheet_name[:31], index=False)

                # Tự động điều chỉnh độ rộng cột
                ws = writer.sheets[sheet_name[:31]]
                for col in ws.columns:
                    max_len = max(
                        (len(str(cell.value)) if cell.value else 0 for cell in col),
                        default=10
                    )
                    ws.column_dimensions[col[0].column_letter].width = min(max_len + 4, 50)

        success(f"Đã xuất báo cáo: [bold]{filename}[/bold]")
        info(f"Mở file tại: {os.path.abspath(filename)}")

    except Exception as e:
        error(f"Lỗi xuất Excel: {e}")

    pause()


# ── Menu ─────────────────────────────────────────────────────
def report_menu():
    while True:
        choice = questionary.select(
            "Báo cáo & Thống kê:",
            choices=[
                "1. Dashboard tổng quan hệ thống",
                "2. Thống kê tất cả sự kiện",
                "3. Báo cáo theo khoảng thời gian",
                "4. Top khách tham dự nhiều nhất",
                "5. Tỉ lệ tham dự một sự kiện   [fn_attendance_rate]",
                "6. Thống kê sử dụng địa điểm",
                "7. Xuất báo cáo Excel (.xlsx)  [pandas + openpyxl]",
                "← Quay lại menu chính",
            ]
        ).ask()

        if not choice or choice.startswith("←"):
            break
        elif choice.startswith("1"): dashboard()
        elif choice.startswith("2"): event_summary()
        elif choice.startswith("3"): report_by_date()
        elif choice.startswith("4"): top_guests()
        elif choice.startswith("5"): attendance_rate()
        elif choice.startswith("6"): venue_usage()
        elif choice.startswith("7"): export_excel()
