"""
app/database/repositories/finance_repository.py
FinanceRepository — quản lý thu chi, báo cáo tài chính
Gọi sp_add_finance_record, fn_event_balance
"""

from __future__ import annotations
from decimal import Decimal
from app.database.base import BaseRepository
from app.database.schemas import FinanceCreate, ProcedureResult


class FinanceRepository(BaseRepository):
    """
    Repository cho bảng Finances.
    Tích hợp Views v_finance_balance, view_finance_report
    và Stored Procedure sp_add_finance_record.
    """

    # ── READ ────────────────────────────────────────────────

    @staticmethod
    def get_by_event(event_id: int) -> list[dict]:
        """Tất cả giao dịch của một sự kiện."""
        return BaseRepository.execute_query("""
            SELECT finance_id, type, amount, description, transaction_date
            FROM Finances
            WHERE event_id = :eid
            ORDER BY transaction_date DESC
        """, {"eid": event_id})

    @staticmethod
    def get_all_report() -> list[dict]:
        """Toàn bộ giao dịch kèm tên sự kiện — từ view_finance_report."""
        return BaseRepository.execute_query(
            "SELECT * FROM view_finance_report"
        )

    @staticmethod
    def get_balance_all() -> list[dict]:
        """Số dư thu-chi từng sự kiện — từ v_finance_balance."""
        return BaseRepository.execute_query(
            "SELECT * FROM v_finance_balance ORDER BY net_balance DESC"
        )

    @staticmethod
    def get_balance_by_event(event_id: int) -> dict | None:
        """Số dư tài chính một sự kiện cụ thể."""
        return BaseRepository.execute_query("""
            SELECT * FROM v_finance_balance WHERE event_id = :eid
        """, {"eid": event_id}, fetch="one")

    @staticmethod
    def get_by_type(event_id: int, finance_type: str) -> list[dict]:
        """Lấy tất cả Income hoặc Expense của một sự kiện."""
        return BaseRepository.execute_query("""
            SELECT finance_id, amount, description, transaction_date, created_by
            FROM Finances
            WHERE event_id = :eid AND type = :ftype
            ORDER BY transaction_date DESC
        """, {"eid": event_id, "ftype": finance_type})

    @staticmethod
    def get_period_report(from_date: str, to_date: str) -> list[dict]:
        """Báo cáo tài chính theo khoảng thời gian."""
        return BaseRepository.execute_query("""
            SELECT e.event_name, f.type, SUM(f.amount) AS total_amount,
                   f.transaction_date
            FROM Finances f
            JOIN Events e ON f.event_id = e.event_id
            WHERE f.transaction_date BETWEEN :fd AND :td
            GROUP BY e.event_id, e.event_name, f.type, f.transaction_date
            ORDER BY f.transaction_date
        """, {"fd": from_date, "td": to_date})

    # ── CREATE (gọi Stored Procedure) ────────────────────────

    @staticmethod
    def add_income(
        event_id: int,
        amount: float,
        description: str,
        created_by: int | None = None,
    ) -> ProcedureResult:
        """
        Ghi nhận thu nhập — gọi sp_add_finance_record với type='Income'.

        Returns:
            ProcedureResult với .success, .message (bao gồm số dư mới)
        """
        raw = BaseRepository.call_procedure(
            "sp_add_finance_record",
            [event_id, "Income", float(amount), description]
        )
        return ProcedureResult.from_raw(raw)

    @staticmethod
    def add_expense(
        event_id: int,
        amount: float,
        description: str,
        created_by: int | None = None,
    ) -> ProcedureResult:
        """
        Ghi nhận chi phí — gọi sp_add_finance_record với type='Expense'.

        Returns:
            ProcedureResult với .success, .message
        """
        raw = BaseRepository.call_procedure(
            "sp_add_finance_record",
            [event_id, "Expense", float(amount), description]
        )
        return ProcedureResult.from_raw(raw)

    @staticmethod
    def add(data: FinanceCreate) -> int:
        """Thêm giao dịch trực tiếp (bypass procedure, dùng cho import/bulk)."""
        BaseRepository.execute_dml("""
            INSERT INTO Finances (event_id, type, amount, description, transaction_date, created_by)
            VALUES (:event_id, :type, :amount, :description, :transaction_date, :created_by)
        """, data.model_dump())
        row = BaseRepository.execute_query("SELECT LAST_INSERT_ID() AS id", fetch="one")
        return int(row["id"]) if row else 0

    # ── DELETE ──────────────────────────────────────────────

    @staticmethod
    def delete(finance_id: int) -> int:
        """Xóa một giao dịch tài chính."""
        return BaseRepository.execute_dml(
            "DELETE FROM Finances WHERE finance_id = :fid",
            {"fid": finance_id},
        )

    # ── STATS (gọi UDF) ──────────────────────────────────────

    @staticmethod
    def get_net_balance(event_id: int) -> float:
        """Số dư ròng."""
        sql = """
            SELECT (SELECT COALESCE(SUM(amount), 0) FROM Finances WHERE event_id = :eid AND type = 'Income') - 
                   (SELECT COALESCE(SUM(amount), 0) FROM Finances WHERE event_id = :eid AND type = 'Expense') AS result
        """
        row = BaseRepository.execute_query(sql, {"eid": event_id}, fetch="one")
        return float(row["result"]) if row else 0.0

    @staticmethod
    def get_total_income_all() -> float:
        """Tổng thu toàn hệ thống."""
        row = BaseRepository.execute_query(
            "SELECT COALESCE(SUM(amount),0) AS total FROM Finances WHERE type='Income'",
            fetch="one",
        )
        return float(row["total"]) if row else 0.0

    @staticmethod
    def get_total_expense_all() -> float:
        """Tổng chi toàn hệ thống."""
        row = BaseRepository.execute_query(
            "SELECT COALESCE(SUM(amount),0) AS total FROM Finances WHERE type='Expense'",
            fetch="one",
        )
        return float(row["total"]) if row else 0.0
