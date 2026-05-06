"""
app/database/repositories/organizer_repo.py
OrganizerRepository — Quản trị sự kiện dành riêng cho Ban Tổ Chức (có kiểm tra Owner)
"""

from app.database.base import BaseRepository

class OrganizerRepository:
    """
    Repository riêng cho vai trò Organizer.
    Mọi thao tác thay đổi dữ liệu đều phải kèm owner_id (organizer_id) để đảm bảo quyền sở hữu.
    """

    @staticmethod
    def get_or_create_organizer(email: str, name: str) -> int:
        """Tìm organizer theo email, nếu chưa có thì khởi tạo mới để map với User Auth"""
        org = BaseRepository.execute_query(
            "SELECT organizer_id FROM Organizers WHERE email = :email", 
            {"email": email}, fetch="one"
        )
        if org:
            return org["organizer_id"]
        
        # Khởi tạo mới hồ sơ Organizer
        BaseRepository.execute_dml(
            "INSERT INTO Organizers (organizer_name, address, phone_number, email, department) VALUES (:name, 'N/A', 'N/A', :email, 'External')",
            {"name": name, "email": email}
        )
        new_org = BaseRepository.execute_query("SELECT LAST_INSERT_ID() AS id", fetch="one")
        return new_org["id"]

    @staticmethod
    def create_event(organizer_id: int, event_data: dict) -> bool:
        """Khởi tạo sự kiện mới, gán chủ sở hữu"""
        BaseRepository.execute_dml("""
            INSERT INTO Events (event_name, start_time, end_time, venue_id, organizer_id, status)
            VALUES (:name, :start_time, :end_time, :venue_id, :owner_id, 'Draft')
        """, {
            "name": event_data['name'],
            "start_time": event_data['start_time'],
            "end_time": event_data['end_time'],
            "venue_id": event_data['venue_id'],
            "owner_id": organizer_id
        })
        return True

    @staticmethod
    def get_my_events(organizer_id: int) -> list[dict]:
        """Chỉ lấy các sự kiện do chính Organizer này tạo"""
        return BaseRepository.execute_query("""
            SELECT e.*, v.venue_name
            FROM Events e
            JOIN Venues v ON e.venue_id = v.venue_id
            WHERE e.organizer_id = :owner_id
            ORDER BY e.start_time DESC
        """, {"owner_id": organizer_id})

    @staticmethod
    def cancel_event(organizer_id: int, event_id: int) -> bool:
        """Hủy sự kiện (chỉ thành công nếu là chủ sở hữu)"""
        BaseRepository.execute_dml("""
            UPDATE Events SET status = 'Cancelled' 
            WHERE event_id = :event_id AND organizer_id = :owner_id
        """, {"event_id": event_id, "owner_id": organizer_id})
        return True

    @staticmethod
    def get_event_guests(organizer_id: int, event_id: int) -> list[dict]:
        """Lấy danh sách khách của một sự kiện (có kiểm tra quyền sở hữu)"""
        return BaseRepository.execute_query("""
            SELECT r.registration_id, r.attendance_status, g.guest_id, g.guest_name, g.email
            FROM Registrations r
            JOIN Guests g ON r.guest_id = g.guest_id
            JOIN Events e ON r.event_id = e.event_id
            WHERE r.event_id = :event_id AND e.organizer_id = :owner_id
            ORDER BY g.guest_name
        """, {"event_id": event_id, "owner_id": organizer_id})

    @staticmethod
    def check_in_guest(organizer_id: int, registration_id: int) -> bool:
        """Đánh dấu điểm danh (Chỉ điểm danh được nếu là sự kiện của mình)"""
        reg = BaseRepository.execute_query("""
            SELECT r.registration_id 
            FROM Registrations r
            JOIN Events e ON r.event_id = e.event_id
            WHERE r.registration_id = :reg_id AND e.organizer_id = :owner_id
        """, {"reg_id": registration_id, "owner_id": organizer_id}, fetch="one")

        if reg:
            BaseRepository.execute_dml("UPDATE Registrations SET attendance_status = 'Attended', checkin_time = NOW() WHERE registration_id = :reg_id", {"reg_id": registration_id})
            return True
        return False

    @staticmethod
    def get_all_venues() -> list[dict]:
        """Lấy danh sách hội trường/địa điểm khả dụng"""
        return BaseRepository.execute_query("SELECT * FROM Venues ORDER BY venue_name")