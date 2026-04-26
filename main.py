"""
main.py — Entry point của Event Management System
Chạy: python main.py
"""

import sys
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

console = Console()


def banner():
    title = Text()
    title.append("EVENT MANAGEMENT SYSTEM\n", style="bold cyan")
    title.append("NEU — DATCOM Lab | Project 14\n", style="dim")
    title.append("MySQL + SQLAlchemy + Rich CLI", style="italic dim")
    console.print(Panel(title, border_style="cyan", padding=(1, 4)))


def main():
    banner()

    # Kiểm tra kết nối database
    console.print("[dim]  Đang kết nối database...[/dim]")
    from app.config import test_connection
    if not test_connection():
        console.print(
            "[bold red]  Không thể kết nối MySQL.[/bold red]\n"
            "  Kiểm tra file [bold].env[/bold] và đảm bảo MySQL đang chạy.\n"
        )
        sys.exit(1)

    console.print("[green]  Kết nối database thành công![/green]\n")

    from app.cli.main import main_menu
    main_menu()


if __name__ == "__main__":
    main()
