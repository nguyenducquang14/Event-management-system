"""
app/database/repositories/event_repository.py
EventRepository — toàn bộ thao tác CSDL liên quan đến bảng Events và Views sự kiện
"""

from __future__ import annotations
from typing import Optional
from app.database.base import BaseRepository
from app.database.schemas import (
    EventCreate, EventRead, EventSummary, ProcedureResult
)


class EventRepository(BaseRepository):
    """
    Repository cho bảng Events.
    Kế thừa BaseRepository → dùng execute_query / execute_dml / call_procedure.
    """

    # ── READ ────────────────────────────────────────────────

    @staticmethod
    def get_all(status_filter: str | None = None) -> list[dict]:
        """Lấy tất cả sự kiện, tùy chọn lọc theo status."""
        sql = """
            SELECT e.event_id, e.event_name,
                   e.start_time, e.end_time,
                   v.venue_name, o.organizer_name,
                   e.status, e.max_capacity,
                   (SELECT COUNT(*) FROM Registrations WHERE event_id = e.event_id) AS current_registered,
                   COALESCE(e.max_capacity - (SELECT COUNT(*) FROM Registrations WHERE event_id = e.event_id), 99999) AS slots_remaining
            FROM Events e
            JOIN Venues     v ON e.venue_id     = v.venue_id
            JOIN Organizers o ON e.organizer_id = o.organizer_id
        """
        params: dict = {}
        if status_filter:
            sql += " WHERE e.status = :status"
            params["status"] = status_filter
        sql += " ORDER BY e.start_time"
        return BaseRepository.execute_query(sql, params)

    @staticmethod
    def get_by_id(event_id: int) -> dict | None:
        """Lấy chi tiết một sự kiện theo ID."""
        return BaseRepository.execute_query("""
            SELECT e.*,
                   v.venue_name, v.address AS venue_address, v.capacity AS venue_capacity,
                   o.organizer_name, o.email AS organizer_email,
                   COALESCE((SELECT COUNT(*) FROM Registrations WHERE event_id = e.event_id AND attendance_status = 'Attended') / NULLIF((SELECT COUNT(*) FROM Registrations WHERE event_id = e.event_id), 0) * 100, 0) AS attendance_rate_pct,
                   (SELECT COALESCE(SUM(amount), 0) FROM Finances WHERE event_id = e.event_id AND type = 'Income') - (SELECT COALESCE(SUM(amount), 0) FROM Finances WHERE event_id = e.event_id AND type = 'Expense') AS net_balance,
                   (SELECT COUNT(*) FROM Registrations WHERE event_id = e.event_id) AS current_registered,
                   COALESCE(e.max_capacity - (SELECT COUNT(*) FROM Registrations WHERE event_id = e.event_id), 99999) AS slots_remaining
            FROM Events e
            JOIN Venues     v ON e.venue_id     = v.venue_id
            JOIN Organizers o ON e.organizer_id = o.organizer_id
            WHERE e.event_id = :eid
        """, {"eid": event_id}, fetch="one")

    @staticmethod
    def get_upcoming() -> list[dict]:
        """Lấy sự kiện sắp diễn ra từ View v_upcoming_events."""
        return BaseRepository.execute_query("SELECT * FROM view_upcoming_events")

    @staticmethod
    def get_summary() -> list[dict]:
        """Tổng hợp thống kê từng sự kiện (view_event_summary)."""
        return BaseRepository.execute_query("SELECT * FROM view_event_summary ORDER BY start_time")

    @staticmethod
    def search(keyword: str) -> list[dict]:
        """Tìm kiếm sự kiện theo tên."""
        return BaseRepository.execute_query("""
            SELECT event_id, event_name, start_time, status, max_capacity
            FROM Events
            WHERE event_name LIKE :kw
            ORDER BY start_time
        """, {"kw": f"%{keyword}%"})

    @staticmethod
    def get_by_date_range(from_date: str, to_date: str) -> list[dict]:
        """Lấy sự kiện trong khoảng thời gian — gọi sp_event_report."""
        return BaseRepository.call_procedure_resultset(
            "sp_event_report", [from_date, to_date]
        )

    # ── CREATE ──────────────────────────────────────────────

    @staticmethod
    def create(data: EventCreate) -> int:
        """
        Tạo sự kiện mới.

        Returns:
            ID của sự kiện vừa tạo (LAST_INSERT_ID)
        """
        BaseRepository.execute_dml("""
            INSERT INTO Events
                (event_name, start_time, end_time, venue_id, organizer_id,
                 status, max_capacity, description)
            VALUES
                (:event_name, :start_time, :end_time, :venue_id, :organizer_id,
                 :status, :max_capacity, :description)
        """, data.model_dump())

        row = BaseRepository.execute_query("SELECT LAST_INSERT_ID() AS id", fetch="one")
        return int(row["id"]) if row else 0

    # ── UPDATE ──────────────────────────────────────────────

    @staticmethod
    def update(event_id: int, data: EventCreate) -> int:
        """Cập nhật thông tin sự kiện. Returns rowcount."""
        params = data.model_dump()
        params["event_id"] = event_id
        return BaseRepository.execute_dml("""
            UPDATE Events
            SET event_name   = :event_name,
                start_time   = :start_time,
                end_time     = :end_time,
                venue_id     = :venue_id,
                organizer_id = :organizer_id,
                max_capacity = :max_capacity,
                description  = :description
            WHERE event_id = :event_id
        """, params)

    @staticmethod
    def update_status(event_id: int, status: str) -> int:
        """Cập nhật trạng thái sự kiện."""
        return BaseRepository.execute_dml(
            "UPDATE Events SET status = :s WHERE event_id = :eid",
            {"s": status, "eid": event_id}
        )

    # ── DELETE ──────────────────────────────────────────────

    @staticmethod
    def delete(event_id: int) -> int:
        """Xóa sự kiện (cascade xóa Registrations và Finances)."""
        return BaseRepository.execute_dml(
            "DELETE FROM Events WHERE event_id = :eid", {"eid": event_id}
        )

    # ── BUSINESS LOGIC (gọi UDF) ─────────────────────────────

    @staticmethod
    def get_attendance_rate(event_id: int) -> float:
        """Tỉ lệ tham dự (%)."""
        sql = """
            SELECT COALESCE((SELECT COUNT(*) FROM Registrations WHERE event_id = :eid AND attendance_status = 'Attended') / 
                   NULLIF((SELECT COUNT(*) FROM Registrations WHERE event_id = :eid), 0) * 100, 0) AS result
        """
        row = BaseRepository.execute_query(sql, {"eid": event_id}, fetch="one")
        return float(row["result"]) if row else 0.0

    @staticmethod
    def get_net_balance(event_id: int) -> float:
        """Số dư tài chính."""
        sql = """
            SELECT (SELECT COALESCE(SUM(amount), 0) FROM Finances WHERE event_id = :eid AND type = 'Income') - 
                   (SELECT COALESCE(SUM(amount), 0) FROM Finances WHERE event_id = :eid AND type = 'Expense') AS result
        """
        row = BaseRepository.execute_query(sql, {"eid": event_id}, fetch="one")
        return float(row["result"]) if row else 0.0

    @staticmethod
    def mark_completed(event_id: int) -> ProcedureResult:
        """Kết thúc sự kiện qua sp_mark_event_completed."""
        raw = BaseRepository.call_procedure("sp_mark_event_completed", [event_id])
        return ProcedureResult.from_raw(raw)
