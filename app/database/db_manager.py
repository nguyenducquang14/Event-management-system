"""
app/database/db_manager.py
DatabaseManager — Facade tổng hợp tất cả Repository

Đây là điểm duy nhất mà Streamlit và CLI cần import.
Không cần biết Repository nào đằng sau — chỉ cần gọi db.events.get_all()

Ví dụ sử dụng:
    from app.database import DatabaseManager
    db = DatabaseManager()

    events  = db.events.get_all()
    balance = db.finances.get_net_balance(event_id=1)
    result  = db.registrations.checkin(event_id=1, guest_id=3)
    print(result.success, result.message)
"""

from __future__ import annotations
import logging
from decimal import Decimal

from app.database.repositories import (
    EventRepository,
    GuestRepository,
    RegistrationRepository,
    FinanceRepository,
)
from app.database.schemas import DashboardStats
from app.database.base import BaseRepository

logger = logging.getLogger(__name__)


class DatabaseManager:
    """
    Facade Pattern: một đầu vào duy nhất cho tầng database.

    Attributes:
        events:        EventRepository
        guests:        GuestRepository
        registrations: RegistrationRepository
        finances:      FinanceRepository
    """

    def __init__(self):
        self.events        = EventRepository()
        self.guests        = GuestRepository()
        self.registrations = RegistrationRepository()
        self.finances      = FinanceRepository()

    # ════════════════════════════════════════════════════════
    # DASHBOARD — query tổng hợp dùng cho trang chính
    # ════════════════════════════════════════════════════════

    def get_dashboard_stats(self) -> DashboardStats:
        """
        Truy vấn một lần, trả về toàn bộ số liệu tổng quan.
        Dùng cho Streamlit dashboard và CLI summary.
        """
        row = BaseRepository.execute_query("""
            SELECT
                (SELECT COUNT(*) FROM Events)                                           AS total_events,
                (SELECT COUNT(*) FROM Events WHERE status IN ('Draft','Scheduled'))     AS upcoming_events,
                (SELECT COUNT(*) FROM Guests)                                           AS total_guests,
                (SELECT COUNT(*) FROM Registrations)                                    AS total_registrations,
                (SELECT COUNT(*) FROM Registrations WHERE attendance_status='Attended') AS total_attended,
                (SELECT COALESCE(SUM(amount),0) FROM Finances WHERE type='Income')     AS total_income,
                (SELECT COALESCE(SUM(amount),0) FROM Finances WHERE type='Expense')    AS total_expense
        """, fetch="one")

        if not row:
            return DashboardStats(
                total_events=0, upcoming_events=0, total_guests=0,
                total_registrations=0, total_attended=0,
                total_income=Decimal(0), total_expense=Decimal(0), net_balance=Decimal(0),
            )

        income  = Decimal(str(row["total_income"]))
        expense = Decimal(str(row["total_expense"]))
        return DashboardStats(
            total_events        = int(row["total_events"]),
            upcoming_events     = int(row["upcoming_events"]),
            total_guests        = int(row["total_guests"]),
            total_registrations = int(row["total_registrations"]),
            total_attended      = int(row["total_attended"]),
            total_income        = income,
            total_expense       = expense,
            net_balance         = income - expense,
        )

    # ════════════════════════════════════════════════════════
    # SHORTCUT METHODS — các thao tác hay dùng nhất
    # ════════════════════════════════════════════════════════

    def register_guest(self, event_id: int, guest_id: int):
        """Shortcut: đăng ký khách qua sp_register_guest."""
        return self.registrations.register(event_id, guest_id)

    def checkin_guest(self, event_id: int, guest_id: int):
        """Shortcut: check-in khách qua sp_guest_checkin."""
        return self.registrations.checkin(event_id, guest_id)

    def add_income(self, event_id: int, amount: float, description: str, created_by: int | None = None):
        """Shortcut: ghi thu nhập qua sp_add_finance_record."""
        return self.finances.add_income(event_id, amount, description, created_by)

    def add_expense(self, event_id: int, amount: float, description: str, created_by: int | None = None):
        """Shortcut: ghi chi phí qua sp_add_finance_record."""
        return self.finances.add_expense(event_id, amount, description, created_by)

    def complete_event(self, event_id: int):
        """Shortcut: kết thúc sự kiện qua sp_mark_event_completed."""
        return self.events.mark_completed(event_id)

    def get_event_report(self, from_date: str, to_date: str) -> list[dict]:
        """Shortcut: báo cáo sự kiện theo kỳ qua sp_event_report."""
        return self.events.get_by_date_range(from_date, to_date)
