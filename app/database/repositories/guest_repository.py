"""
app/database/repositories/guest_repository.py
GuestRepository — toàn bộ thao tác CSDL liên quan đến bảng Guests
"""

from __future__ import annotations
from app.database.base import BaseRepository
from app.database.schemas import GuestCreate


class GuestRepository(BaseRepository):
    """
    Repository cho bảng Guests.
    Bảo mật: các hàm trả về dữ liệu đầy đủ chỉ được gọi bởi event_manager.
    Tầng CLI/Streamlit nên gọi get_safe() cho nhân viên check-in.
    """

    # ── READ ────────────────────────────────────────────────

    @staticmethod
    def get_all(page: int = 1, page_size: int = 50) -> dict:
        """Lấy danh sách khách mời có phân trang."""
        sql = """
            SELECT guest_id, guest_name, email, phone_number, address, created_at
            FROM Guests
            ORDER BY guest_name
        """
        return BaseRepository.paginate(sql, page=page, page_size=page_size)

    @staticmethod
    def get_by_id(guest_id: int) -> dict | None:
        """Lấy chi tiết một khách mời theo ID."""
        return BaseRepository.execute_query(
            "SELECT * FROM Guests WHERE guest_id = :gid",
            {"gid": guest_id},
            fetch="one",
        )

    @staticmethod
    def get_by_email(email: str) -> dict | None:
        """Tìm khách theo email (unique lookup)."""
        return BaseRepository.execute_query(
            "SELECT * FROM Guests WHERE email = :email",
            {"email": email.lower().strip()},
            fetch="one",
        )

    @staticmethod
    def search(keyword: str) -> list[dict]:
        """Tìm kiếm khách theo tên hoặc email."""
        like = f"%{keyword}%"
        return BaseRepository.execute_query("""
            SELECT guest_id, guest_name, email, phone_number
            FROM Guests
            WHERE guest_name LIKE :kw OR email LIKE :kw
            ORDER BY guest_name
        """, {"kw": like})

    @staticmethod
    def get_safe() -> list[dict]:
        """
        Trả về danh sách khách ĐÃ MASK thông tin nhạy cảm.
        Dùng cho checkin_staff — không lộ email/SĐT đầy đủ.
        """
        return BaseRepository.execute_query(
            "SELECT guest_id, guest_name, email_masked, phone_masked FROM v_safe_guests"
        )

    @staticmethod
    def get_activity(limit: int = 10) -> list[dict]:
        """Top khách tích cực từ view_guest_activity."""
        return BaseRepository.execute_query("""
            SELECT * FROM v_guest_activity
            ORDER BY total_registrations DESC
            LIMIT :lim
        """, {"lim": limit})

    @staticmethod
    def get_events_of_guest(guest_id: int) -> list[dict]:
        """Tất cả sự kiện mà một khách đã đăng ký."""
        return BaseRepository.execute_query("""
            SELECT e.event_id, e.event_name, e.start_time, e.status,
                   r.attendance_status, r.checkin_time, r.registration_date
            FROM Registrations r
            JOIN Events e ON r.event_id = e.event_id
            WHERE r.guest_id = :gid
            ORDER BY e.start_time DESC
        """, {"gid": guest_id})

    # ── CREATE ──────────────────────────────────────────────

    @staticmethod
    def create(data: GuestCreate) -> int:
        """
        Thêm khách mời mới.

        Returns:
            guest_id của khách vừa tạo

        Raises:
            RepositoryError: Nếu email đã tồn tại (UNIQUE constraint)
        """
        BaseRepository.execute_dml("""
            INSERT INTO Guests (guest_name, email, phone_number, address)
            VALUES (:guest_name, :email, :phone_number, :address)
        """, data.model_dump())

        row = BaseRepository.execute_query("SELECT LAST_INSERT_ID() AS id", fetch="one")
        return int(row["id"]) if row else 0

    # ── UPDATE ──────────────────────────────────────────────

    @staticmethod
    def update(guest_id: int, data: GuestCreate) -> int:
        """Cập nhật thông tin khách mời. Returns rowcount."""
        params = data.model_dump()
        params["guest_id"] = guest_id
        return BaseRepository.execute_dml("""
            UPDATE Guests
            SET guest_name   = :guest_name,
                email        = :email,
                phone_number = :phone_number,
                address      = :address
            WHERE guest_id = :guest_id
        """, params)

    # ── DELETE ──────────────────────────────────────────────

    @staticmethod
    def delete(guest_id: int) -> int:
        """Xóa khách mời (cascade xóa Registrations)."""
        return BaseRepository.execute_dml(
            "DELETE FROM Guests WHERE guest_id = :gid", {"gid": guest_id}
        )

    # ── STATS ───────────────────────────────────────────────

    @staticmethod
    def count() -> int:
        """Tổng số khách mời trong hệ thống."""
        row = BaseRepository.execute_query(
            "SELECT COUNT(*) AS total FROM Guests", fetch="one"
        )
        return int(row["total"]) if row else 0
