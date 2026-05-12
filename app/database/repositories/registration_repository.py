"""
app/database/repositories/registration_repository.py
RegistrationRepository — đăng ký, check-in, attendance tracking
Gọi trực tiếp Stored Procedures sp_register_guest, sp_guest_checkin
"""

from __future__ import annotations
from app.database.base import BaseRepository
from app.database.schemas import ProcedureResult


class RegistrationRepository(BaseRepository):
    """
    Repository cho bảng Registrations.
    Đây là bảng trung gian M:N giữa Events và Guests.
    """

    # ── READ ────────────────────────────────────────────────

    @staticmethod
    def get_by_event(event_id: int) -> list[dict]:
        """Danh sách đăng ký của một sự kiện, kèm thông tin khách."""
        return BaseRepository.execute_query("""
            SELECT r.registration_id,
                   g.guest_id, g.guest_name, g.email, g.phone_number,
                   r.registration_date, r.attendance_status, r.checkin_time
            FROM Registrations r
            JOIN Guests g ON r.guest_id = g.guest_id
            WHERE r.event_id = :eid
            ORDER BY g.guest_name
        """, {"eid": event_id})

    @staticmethod
    def get_pending_checkin(event_id: int) -> list[dict]:
        """Khách đã đăng ký nhưng chưa check-in (attendance_status = Registered)."""
        return BaseRepository.execute_query("""
            SELECT r.registration_id, g.guest_id, g.guest_name,
                   g.email, g.phone_number, r.registration_date
            FROM Registrations r
            JOIN Guests g ON r.guest_id = g.guest_id
            WHERE r.event_id = :eid AND r.attendance_status = 'Registered'
            ORDER BY g.guest_name
        """, {"eid": event_id})

    @staticmethod
    def get_all(limit: int = 100) -> list[dict]:
        """Tất cả đăng ký, có JOIN để hiển thị tên sự kiện và khách."""
        return BaseRepository.execute_query("""
            SELECT r.registration_id, e.event_name, g.guest_name,
                   g.email, r.registration_date, r.attendance_status, r.checkin_time
            FROM Registrations r
            JOIN Events e ON r.event_id = e.event_id
            JOIN Guests g ON r.guest_id = g.guest_id
            ORDER BY r.registration_date DESC
            LIMIT :lim
        """, {"lim": limit})

    @staticmethod
    def get_one(event_id: int, guest_id: int) -> dict | None:
        """Lấy một bản ghi đăng ký theo (event_id, guest_id)."""
        return BaseRepository.execute_query("""
            SELECT r.*, e.event_name, g.guest_name
            FROM Registrations r
            JOIN Events e ON r.event_id = e.event_id
            JOIN Guests g ON r.guest_id = g.guest_id
            WHERE r.event_id = :eid AND r.guest_id = :gid
        """, {"eid": event_id, "gid": guest_id}, fetch="one")

    @staticmethod
    def get_safe_list(event_id: int) -> list[dict]:
        """Danh sách đăng ký đã mask thông tin nhạy cảm (cho checkin_staff)."""
        return BaseRepository.execute_query("""
            SELECT r.registration_id AS reg_id, e.event_name, e.start_time, g.guest_id, g.guest_name,
                   CONCAT(LEFT(g.email, 2), '***', SUBSTRING_INDEX(g.email, '@', -1)) AS email_hint,
                   r.registration_date, r.attendance_status, r.checkin_time
            FROM Registrations r
            JOIN Events e ON r.event_id = e.event_id
            JOIN Guests g ON r.guest_id = g.guest_id
            WHERE r.event_id = :eid
        """, {"eid": event_id})

    # ── REGISTER (gọi Stored Procedure) ─────────────────────

    @staticmethod
    def register(event_id: int, guest_id: int) -> ProcedureResult:
        """
        Đăng ký khách tham dự — gọi sp_register_guest.
        Procedure tự kiểm tra: trùng lặp, status, max_capacity.

        Returns:
            ProcedureResult với .success và .message
        """
        raw = BaseRepository.call_procedure("sp_register_guest", [event_id, guest_id])
        return ProcedureResult.from_raw(raw)

    # ── CHECK-IN (gọi Stored Procedure) ─────────────────────

    @staticmethod
    def checkin(event_id: int, guest_id: int) -> ProcedureResult:
        """
        Check-in khách — gọi sp_guest_checkin.
        Cập nhật attendance_status → Attended + ghi checkin_time = NOW().

        Returns:
            ProcedureResult với .success và .message
        """
        raw = BaseRepository.call_procedure("sp_guest_checkin", [event_id, guest_id])
        return ProcedureResult.from_raw(raw)

    # ── UPDATE STATUS ────────────────────────────────────────

    @staticmethod
    def mark_noshow_bulk(event_id: int) -> int:
        """Đánh dấu No-show tất cả khách Registered của một sự kiện."""
        return BaseRepository.execute_dml("""
            UPDATE Registrations
            SET attendance_status = 'No-show'
            WHERE event_id = :eid AND attendance_status = 'Registered'
        """, {"eid": event_id})

    @staticmethod
    def update_status(
        event_id: int, guest_id: int, status: str
    ) -> int:
        """Cập nhật attendance_status thủ công."""
        return BaseRepository.execute_dml("""
            UPDATE Registrations
            SET attendance_status = :status
            WHERE event_id = :eid AND guest_id = :gid
        """, {"status": status, "eid": event_id, "gid": guest_id})

    # ── DELETE ──────────────────────────────────────────────

    @staticmethod
    def cancel(event_id: int, guest_id: int) -> int:
        """Hủy đăng ký (xóa dòng)."""
        return BaseRepository.execute_dml("""
            DELETE FROM Registrations
            WHERE event_id = :eid AND guest_id = :gid
        """, {"eid": event_id, "gid": guest_id})

    @staticmethod
    def cancel_by_id(registration_id: int) -> int:
        """Hủy đăng ký theo registration_id."""
        return BaseRepository.execute_dml(
            "DELETE FROM Registrations WHERE registration_id = :rid",
            {"rid": registration_id},
        )

    # ── STATS ───────────────────────────────────────────────

    @staticmethod
    def count_by_event(event_id: int) -> dict:
        """Thống kê nhanh theo trạng thái cho một sự kiện."""
        row = BaseRepository.execute_query("""
            SELECT
                COUNT(*)                                         AS total,
                SUM(attendance_status = 'Registered')            AS registered,
                SUM(attendance_status = 'Attended')              AS attended,
                SUM(attendance_status = 'No-show')               AS noshow,
                ROUND(SUM(attendance_status='Attended')
                      / NULLIF(COUNT(*),0) * 100, 2)            AS rate_pct
            FROM Registrations
            WHERE event_id = :eid
        """, {"eid": event_id}, fetch="one")
        return row or {}
