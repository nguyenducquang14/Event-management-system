"""
app/cli/utils.py
Tiện ích hiển thị dùng chung cho toàn bộ CLI (Rich)
"""

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich import box
from typing import List, Dict, Any

console = Console()


# ── Bảng dữ liệu ────────────────────────────────────────────
def print_table(
    rows: List[Dict[str, Any]],
    title: str = "",
    style: str = "cyan",
) -> None:
    """In danh sách dict dưới dạng bảng Rich đẹp."""
    if not rows:
        console.print("[yellow]  (Không có dữ liệu)[/yellow]")
        return

    tbl = Table(
        title=title,
        box=box.ROUNDED,
        header_style=f"bold {style}",
        border_style=style,
        show_lines=True,
    )

    for col in rows[0].keys():
        tbl.add_column(str(col), overflow="fold")

    for row in rows:
        tbl.add_row(*[str(v) if v is not None else "—" for v in row.values()])

    console.print(tbl)
    console.print(f"[dim]  Tổng: {len(rows)} dòng[/dim]\n")


# ── Panel thông báo ──────────────────────────────────────────
def success(msg: str) -> None:
    console.print(Panel(f"[bold green]✓  {msg}[/bold green]", border_style="green"))


def error(msg: str) -> None:
    console.print(Panel(f"[bold red]✗  {msg}[/bold red]", border_style="red"))


def info(msg: str) -> None:
    console.print(f"[cyan]ℹ  {msg}[/cyan]")


def warning(msg: str) -> None:
    console.print(f"[yellow]⚠  {msg}[/yellow]")


# ── Dashboard card ───────────────────────────────────────────
def print_stat_cards(stats: Dict[str, Any]) -> None:
    """In các thẻ số liệu tổng quan."""
    from rich.columns import Columns

    cards = []
    icons = {
        "total_events":        ("📅", "cyan"),
        "upcoming_events":     ("🔜", "blue"),
        "total_guests":        ("👥", "magenta"),
        "total_registrations": ("📋", "yellow"),
        "total_attended":      ("✅", "green"),
        "total_income":        ("💰", "green"),
        "total_expense":       ("💸", "red"),
        "net_balance":         ("📊", "cyan"),
    }
    labels = {
        "total_events":        "Tổng sự kiện",
        "upcoming_events":     "Sắp diễn ra",
        "total_guests":        "Tổng khách",
        "total_registrations": "Tổng đăng ký",
        "total_attended":      "Đã tham dự",
        "total_income":        "Tổng thu (VND)",
        "total_expense":       "Tổng chi (VND)",
        "net_balance":         "Số dư (VND)",
    }
    for key, val in stats.items():
        icon, color = icons.get(key, ("•", "white"))
        label = labels.get(key, key)
        display = f"{val:,.0f}" if isinstance(val, (int, float)) and abs(val) >= 1000 else str(val)
        cards.append(Panel(
            f"[bold {color}]{display}[/bold {color}]",
            title=f"{icon} {label}",
            border_style=color,
            width=22,
        ))

    console.print(Columns(cards))


# ── Input helpers ────────────────────────────────────────────
def prompt_int(label: str, allow_empty: bool = False) -> int | None:
    """Nhập số nguyên có kiểm tra."""
    while True:
        val = console.input(f"  [cyan]{label}[/cyan]: ").strip()
        if allow_empty and val == "":
            return None
        try:
            return int(val)
        except ValueError:
            warning("Vui lòng nhập số nguyên.")


def prompt_float(label: str) -> float | None:
    """Nhập số thực có kiểm tra."""
    while True:
        val = console.input(f"  [cyan]{label}[/cyan]: ").strip()
        try:
            n = float(val)
            if n <= 0:
                warning("Giá trị phải lớn hơn 0.")
                continue
            return n
        except ValueError:
            warning("Vui lòng nhập số hợp lệ.")


def pause() -> None:
    console.input("\n  [dim]Nhấn Enter để tiếp tục...[/dim]")
