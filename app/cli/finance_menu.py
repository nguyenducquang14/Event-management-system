"""
app/cli/finance_menu.py
Quản lý tài chính sự kiện (Income / Expense)
Gọi sp_add_finance + fn_event_balance từ database Giai đoạn 1
"""

import questionary
from sqlalchemy import text
from app.config import get_db, engine
from app.cli.utils import (
    console, print_table, success, error, info, warning, pause,
    prompt_int, prompt_float,
)


def _row2dict(row) -> dict:
    return dict(row._mapping)


def _call_sp_add_finance(event_id, ftype, amount, description, created_by) -> str:
    """Gọi sp_add_finance và lấy OUT parameter."""
    conn = engine.raw_connection()
    try:
        cur = conn.cursor()
        cur.callproc("sp_add_finance", [event_id, ftype, amount, description, created_by, ""])
        cur.execute("SELECT @_sp_add_finance_5")
        row = cur.fetchone()
        conn.commit()
        return row[0] if row else "Không rõ kết quả."
    except Exception as e:
        conn.rollback()
        return f"ERROR: {e}"
    finally:
        cur.close()
        conn.close()


# ── Xem tài chính theo sự kiện ───────────────────────────────
def list_finances():
    console.rule("[bold green]Báo cáo tài chính[/bold green]")
    event_id = prompt_int("Lọc theo Event ID (Enter xem tất cả)", allow_empty=True)

    with get_db() as db:
        if event_id:
            rows = db.execute(text("""
                SELECT f.finance_id AS ID,
                       e.event_name AS "Sự kiện",
                       f.type AS "Loại",
                       FORMAT(f.amount, 0) AS "Số tiền (VND)",
                       f.description AS "Mô tả",
                       f.transaction_date AS "Ngày"
                FROM Finances f
                JOIN Events e ON f.event_id = e.event_id
                WHERE f.event_id = :eid
                ORDER BY f.transaction_date
            """), {"eid": event_id}).fetchall()

            # Tổng thu - chi qua function
            balance = db.execute(
                text("SELECT fn_event_balance(:eid) AS balance"), {"eid": event_id}
            ).fetchone()
            bal = float(balance.balance) if balance and balance.balance else 0
        else:
            rows = db.execute(text("SELECT * FROM view_finance_report LIMIT 100")).fetchall()
            balance = None
            bal = None

    print_table([_row2dict(r) for r in rows], "Tài chính sự kiện", style="green")

    if bal is not None:
        color = "green" if bal >= 0 else "red"
        sign  = "+" if bal >= 0 else ""
        console.print(
            f"\n  [bold]Số dư ròng sự kiện #{event_id}:[/bold] "
            f"[bold {color}]{sign}{bal:,.0f} VND[/bold {color}]\n"
        )
    pause()


# ── Thêm thu nhập ────────────────────────────────────────────
def add_income():
    console.rule("[bold green]Ghi nhận THU NHẬP[/bold green]")
    _add_transaction("Income")


# ── Thêm chi phí ─────────────────────────────────────────────
def add_expense():
    console.rule("[bold red]Ghi nhận CHI PHÍ[/bold red]")
    _add_transaction("Expense")


def _add_transaction(ftype: str):
    """Hàm chung ghi nhận thu hoặc chi, gọi sp_add_finance."""
    # Hiển thị danh sách sự kiện
    with get_db() as db:
        events = db.execute(text("""
            SELECT event_id AS ID, event_name AS "Tên sự kiện",
                   status AS "Trạng thái"
            FROM Events ORDER BY start_time DESC LIMIT 20
        """)).fetchall()
    print_table([_row2dict(r) for r in events], "Chọn sự kiện", style="cyan")

    event_id = prompt_int("Event ID")
    amount   = prompt_float(f"Số tiền {'thu' if ftype=='Income' else 'chi'} (VND)")
    desc     = console.input("  [cyan]Mô tả giao dịch[/cyan]: ").strip()
    org_id   = prompt_int("Organizer ID (người ghi nhận, Enter bỏ qua)", allow_empty=True)

    icon  = "💰" if ftype == "Income" else "💸"
    color = "green" if ftype == "Income" else "red"
    console.print(
        f"\n  {icon} Ghi nhận [{color}]{ftype}[/{color}]: "
        f"[bold]{amount:,.0f} VND[/bold] cho sự kiện #{event_id}"
    )
    console.print(f"  Mô tả: {desc}")

    if not questionary.confirm("Xác nhận ghi nhận?").ask():
        info("Đã hủy.")
        pause()
        return

    console.print(f"\n  Đang gọi [bold]sp_add_finance({event_id}, {ftype}, {amount}, ...)[/bold]...")
    result = _call_sp_add_finance(event_id, ftype, amount, desc, org_id)

    if result and result.startswith("OK"):
        success(result)
        # Hiển thị số dư mới
        with get_db() as db:
            bal = db.execute(
                text("SELECT fn_event_balance(:eid) AS b"), {"eid": event_id}
            ).fetchone()
        if bal and bal.b is not None:
            b = float(bal.b)
            color = "green" if b >= 0 else "red"
            console.print(f"  Số dư mới: [bold {color}]{b:+,.0f} VND[/bold {color}]")
    else:
        error(result or "Lỗi không xác định.")

    pause()


# ── Tổng hợp thu-chi tất cả sự kiện ─────────────────────────
def finance_summary():
    console.rule("[bold cyan]Tổng hợp tài chính tất cả sự kiện[/bold cyan]")
    with get_db() as db:
        rows = db.execute(text("""
            SELECT event_name AS "Sự kiện",
                   FORMAT(total_income,  0) AS "Tổng thu (VND)",
                   FORMAT(total_expense, 0) AS "Tổng chi (VND)",
                   FORMAT(net_balance,   0) AS "Số dư (VND)",
                   attendance_rate_pct      AS "Tỉ lệ tham dự %"
            FROM view_event_summary
            ORDER BY net_balance DESC
        """)).fetchall()
    print_table([_row2dict(r) for r in rows], "Tổng hợp tài chính", style="green")
    pause()


# ── Xóa giao dịch ────────────────────────────────────────────
def delete_finance():
    fin_id = prompt_int("Nhập Finance ID cần xóa")
    with get_db() as db:
        row = db.execute(
            text("SELECT * FROM Finances WHERE finance_id = :fid"),
            {"fid": fin_id}
        ).fetchone()

    if not row:
        error("Không tìm thấy giao dịch.")
        pause()
        return

    r = _row2dict(row)
    console.print(f"\n  Loại    : [bold]{r['type']}[/bold]")
    console.print(f"  Số tiền : {float(r['amount']):,.0f} VND")
    console.print(f"  Mô tả   : {r['description']}\n")

    if not questionary.confirm("Xác nhận xóa giao dịch?").ask():
        info("Đã hủy.")
        pause()
        return

    try:
        with get_db() as db:
            db.execute(
                text("DELETE FROM Finances WHERE finance_id = :fid"), {"fid": fin_id}
            )
        success(f"Đã xóa giao dịch #{fin_id}.")
    except Exception as e:
        error(f"Lỗi: {e}")
    pause()


# ── Menu ─────────────────────────────────────────────────────
def finance_menu():
    while True:
        choice = questionary.select(
            "Quản lý tài chính (Income / Expense):",
            choices=[
                "1. Xem tài chính theo sự kiện",
                "2. Ghi nhận THU NHẬP (Income)  [gọi sp_add_finance]",
                "3. Ghi nhận CHI PHÍ (Expense)  [gọi sp_add_finance]",
                "4. Tổng hợp thu-chi tất cả sự kiện",
                "5. Xóa giao dịch",
                "← Quay lại menu chính",
            ]
        ).ask()

        if not choice or choice.startswith("←"):
            break
        elif choice.startswith("1"): list_finances()
        elif choice.startswith("2"): add_income()
        elif choice.startswith("3"): add_expense()
        elif choice.startswith("4"): finance_summary()
        elif choice.startswith("5"): delete_finance()
