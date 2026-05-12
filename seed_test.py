"""
Script tự động tạo dữ liệu mẫu (Admin, Organizer, Guest) để test hệ thống
Mật khẩu chung cho tất cả tài khoản test là: 123456
"""
import os
import json
import getpass
import urllib.parse
from dotenv import load_dotenv
load_dotenv(override=True)  # Ép tải và ghi đè các biến môi trường từ file .env

# Kiểm tra biến môi trường DB_PASSWORD (phải khớp với tên biến trong app/config.py)
if not os.getenv("DB_PASSWORD") and not os.getenv("DATABASE_URL"):
    print("⚠️ Không tìm thấy biến DB_PASSWORD trong file .env")
    # Yêu cầu nhập mật khẩu an toàn từ Terminal (không lộ mật khẩu lên màn hình và git)
    db_pass = getpass.getpass("🔑 Vui lòng nhập mật khẩu Database (sẽ bị ẩn khi gõ): ").strip()
    os.environ["DB_PASSWORD"] = urllib.parse.quote_plus(db_pass)

from sqlalchemy import text
from app.config import get_db
from app.database.auth_models import register_user

test_users = [
    # --- TÀI KHOẢN ADMIN ---
    ("admin_test", "123456", "Quản trị viên Hệ thống", "admin_test@example.com", "Admin"),
    
    # --- TÀI KHOẢN BAN TỔ CHỨC (ORGANIZER) ---
    ("org01", "123456", "Ban tổ chức sự kiện IT", "org01@example.com", "Organizer"),
    ("org02", "123456", "CLB Âm nhạc NEU", "org02@example.com", "Organizer"),
    ("org03", "123456", "Phòng Hành chính - Sự kiện", "org03@example.com", "Organizer"),

    # --- TÀI KHOẢN KHÁCH THAM DỰ (GUEST) ---
    ("guest01", "123456", "Nguyễn Văn An", "guest01@example.com", "Guest"),
    ("guest02", "123456", "Trần Thị Bình", "guest02@example.com", "Guest"),
    ("guest03", "123456", "Lê Hoàng Cường", "guest03@example.com", "Guest"),
    ("guest04", "123456", "Phạm Thu Dung", "guest04@example.com", "Guest"),
    ("guest05", "123456", "Hoàng Ngọc Em", "guest05@example.com", "Guest"),
    ("guest06", "123456", "Vũ Đức Phong", "guest06@example.com", "Guest"),
    ("guest07", "123456", "Đặng Thị Giang", "guest07@example.com", "Guest"),
    ("guest08", "123456", "Bùi Xuân Hải", "guest08@example.com", "Guest"),
    ("guest09", "123456", "Đỗ Minh In", "guest09@example.com", "Guest"),
    ("guest10", "123456", "Ngô Quốc Khánh", "guest10@example.com", "Guest"),
]

def seed_events_data(db):
    print("\n🚀 Đang khởi tạo dữ liệu Sự kiện...")
    
    # Thêm cột phân loại (Tách riêng try-except để an toàn)
    try:
        db.execute(text("ALTER TABLE Events ADD COLUMN category VARCHAR(50) DEFAULT 'Khác'"))
    except Exception:
        pass 
        
    # Thêm cột giá vé (Tách riêng)
    try:
        db.execute(text("ALTER TABLE Events ADD COLUMN ticket_price DECIMAL(10,0) DEFAULT 0"))
    except Exception:
        pass # Bỏ qua nếu cột đã tồn tại

    # Thêm cột hình ảnh (Tách riêng)
    try:
        db.execute(text("ALTER TABLE Events ADD COLUMN image_url VARCHAR(500) DEFAULT NULL"))
    except Exception:
        pass

    # 1. Tạo Địa điểm (Venues đa dạng)
    venues = [
        ('Hội trường A - NEU', '207 Giải Phóng, Hà Nội', 500),
        ('Phòng Lab 502', 'Tòa nhà A1 - NEU', 60),
        ('Sân vận động Ký túc xá', 'Khuôn viên KTX NEU', 1500),
        
        ('Trung tâm Triển lãm VN', 'Giảng Võ, Hà Nội', 2000),
        ('Phòng Hội thảo VIP', 'Khách sạn Melia Hà Nội', 200)
    ]
    v_ids = []
    for v_name, v_addr, v_cap in venues:
        venue = db.execute(text("SELECT venue_id FROM Venues WHERE venue_name = :name"), {"name": v_name}).fetchone()
        if not venue:
            db.execute(text("INSERT INTO Venues (venue_name, address, capacity, availability_status) VALUES (:name, :addr, :cap, 'Available')"), {"name": v_name, "addr": v_addr, "cap": v_cap})
            venue = db.execute(text("SELECT venue_id FROM Venues WHERE venue_name = :name"), {"name": v_name}).fetchone()
        v_ids.append(venue.venue_id)

    # 2. Tạo nhiều Ban tổ chức (Organizer) BẰNG HÀM CHUẨN CỦA HỆ THỐNG
    from app.database.repositories.organizer_repo import OrganizerRepository
    org_repo = OrganizerRepository()

    orgs = [
        ('Ban tổ chức sự kiện IT', 'org01@example.com', '207 Giải Phóng, Hà Nội', '0123456789'),
        ('CLB Âm nhạc NEU', 'org02@example.com', 'Nhà Văn hóa NEU', '0987654321'),
        ('Phòng Hành chính - Sự kiện', 'org03@example.com', 'Tòa nhà A1', '0243123456')
    ]
    org_ids = []
    for org_name, org_email, org_addr, org_phone in orgs:
        owner_id = org_repo.get_or_create_organizer(org_email, org_name)
        org_ids.append(owner_id)
        try:
            db.execute(text("UPDATE Organizers SET address = :addr, phone_number = :phone WHERE organizer_id = :oid"), 
                       {"addr": org_addr, "phone": org_phone, "oid": owner_id})
        except Exception:
            pass

    # Dọn dẹp các Emoji cũ trong cơ sở dữ liệu để tránh bị hiển thị 2 icon
    emojis = ["🔥 ", "🚀 ", "🎵 ", "🎨 ", "🌐 ", "🗣️ ", "💼 ", "🎭 ", "📈 ", "🎤 "]
    for e in emojis:
        db.execute(text("UPDATE Events SET event_name = REPLACE(event_name, :e, '')"), {"e": e})

    # 3. Tạo Sự kiện (Dùng thời gian động NOW() để luôn Đang diễn ra/Sắp tới)
    events_data = [
        {
            "name": "[HOT] Hội thảo AI & Data Science 2026",
            "desc": "Sự kiện ĐANG DIỄN RA. Khám phá tương lai của Trí tuệ nhân tạo và Dữ liệu lớn.",
            "start": "DATE_SUB(NOW(), INTERVAL 1 HOUR)",  # Bắt đầu cách đây 1 tiếng
            "end": "DATE_ADD(NOW(), INTERVAL 3 HOUR)",    # Kết thúc sau 3 tiếng nữa
            "status": "Scheduled",
            "cap": 200,
            "category": "Công nghệ",
            "price": 0,
            "v_id": v_ids[0],
            "org_idx": 0
        },
        {
            "name": "Workshop Lập trình Web với Streamlit",
            "desc": "Sự kiện SẮP DIỄN RA. Hướng dẫn xây dựng Dashboard nhanh chóng.",
            "start": "DATE_ADD(NOW(), INTERVAL 1 DAY)",   # Ngày mai
            "end": "DATE_ADD(NOW(), INTERVAL 1 DAY) + INTERVAL 4 HOUR",
            "status": "Scheduled",
            "cap": 60,
            "category": "Giáo dục",
            "price": 50000,
            "v_id": v_ids[1],
            "org_idx": 0
        },
        {
            "name": "Đêm nhạc Giao lưu NEU",
            "desc": "Đêm nhạc hoành tráng dành cho sinh viên.",
            "start": "DATE_ADD(NOW(), INTERVAL 3 DAY)",
            "end": "DATE_ADD(NOW(), INTERVAL 3 DAY) + INTERVAL 3 HOUR",
            "status": "Scheduled",
            "cap": 1500,
            "category": "Giải trí",
            "price": 100000,
            "v_id": v_ids[2],
            "org_idx": 1
        },
        {
            "name": "Triển lãm Nghệ thuật Đương đại",
            "desc": "Trưng bày các tác phẩm nghệ thuật xuất sắc của sinh viên.",
            "start": "DATE_ADD(NOW(), INTERVAL 2 DAY)",
            "end": "DATE_ADD(NOW(), INTERVAL 2 DAY) + INTERVAL 8 HOUR",
            "status": "Scheduled",
            "cap": 300,
            "category": "Nghệ thuật",
            "price": 0,
            "v_id": v_ids[3],
            "org_idx": 1
        },
        {
            "name": "Hội nghị Blockchain & Web3",
            "desc": "Cập nhật xu hướng công nghệ chuỗi khối mới nhất.",
            "start": "DATE_ADD(NOW(), INTERVAL 5 DAY)",
            "end": "DATE_ADD(NOW(), INTERVAL 5 DAY) + INTERVAL 6 HOUR",
            "status": "Scheduled",
            "cap": 200,
            "category": "Công nghệ",
            "price": 250000,
            "v_id": v_ids[4],
            "org_idx": 0
        },
        {
            "name": "Lớp học Kỹ năng Thuyết trình",
            "desc": "Nâng cao sự tự tin khi nói trước đám đông.",
            "start": "DATE_ADD(NOW(), INTERVAL 4 DAY)",
            "end": "DATE_ADD(NOW(), INTERVAL 4 DAY) + INTERVAL 3 HOUR",
            "status": "Scheduled",
            "cap": 60,
            "category": "Giáo dục",
            "price": 0,
            "v_id": v_ids[1],
            "org_idx": 2
        },
        {
            "name": "Ngày hội Việc làm & Tuyển dụng",
            "desc": "Kết nối sinh viên và các doanh nghiệp hàng đầu.",
            "start": "DATE_ADD(NOW(), INTERVAL 7 DAY)",
            "end": "DATE_ADD(NOW(), INTERVAL 7 DAY) + INTERVAL 8 HOUR",
            "status": "Scheduled",
            "cap": 2000,
            "category": "Khác",
            "price": 0,
            "v_id": v_ids[3],
            "org_idx": 2
        },
        {
            "name": "Nhạc kịch: Giấc mơ tuổi thanh xuân",
            "desc": "Vở nhạc kịch đầy cảm xúc do CLB Nghệ thuật biểu diễn.",
            "start": "DATE_ADD(NOW(), INTERVAL 10 DAY)",
            "end": "DATE_ADD(NOW(), INTERVAL 10 DAY) + INTERVAL 3 HOUR",
            "status": "Full",
            "cap": 500,
            "category": "Nghệ thuật",
            "price": 150000,
            "v_id": v_ids[0],
            "org_idx": 1
        },
        {
            "name": "Bootcamp Huấn luyện Khởi nghiệp",
            "desc": "Chương trình huấn luyện chuyên sâu cho các startup.",
            "start": "DATE_ADD(NOW(), INTERVAL 14 DAY)",
            "end": "DATE_ADD(NOW(), INTERVAL 14 DAY) + INTERVAL 48 HOUR",
            "status": "Scheduled",
            "cap": 200,
            "category": "Giáo dục",
            "price": 1500000,
            "v_id": v_ids[4],
            "org_idx": 0
        },
        {
            "name": "Giao lưu Thần tượng Âm nhạc 2026",
            "desc": "Sự kiện siêu HOT đang diễn ra, gặp gỡ các nghệ sĩ nổi tiếng.",
            "start": "DATE_SUB(NOW(), INTERVAL 2 HOUR)",
            "end": "DATE_ADD(NOW(), INTERVAL 2 HOUR)",
            "status": "Scheduled",
            "cap": 1500,
            "category": "Giải trí",
            "price": 500000,
            "v_id": v_ids[2],
            "org_idx": 1
        },
        {
            "name": "Sự kiện Đã kết thúc: Lễ trao giải NEU 2025",
            "desc": "Sự kiện đã kết thúc, dùng để test chức năng đánh giá và tải tài liệu.",
            "start": "DATE_ADD(NOW(), INTERVAL 10 DAY)", # Đặt tạm ở tương lai để bypass trigger kiểm tra thời gian
            "end": "DATE_ADD(NOW(), INTERVAL 10 DAY) + INTERVAL 4 HOUR",
            "status": "Scheduled",
            "cap": 500,
            "category": "Khác",
            "price": 0,
            "v_id": v_ids[0],
            "org_idx": 2
        },
        {
            "name": "Khóa đào tạo An toàn Thông tin",
            "desc": "Khóa học nội bộ về nhận thức và bảo mật dữ liệu.",
            "start": "DATE_ADD(NOW(), INTERVAL 20 DAY)",
            "end": "DATE_ADD(NOW(), INTERVAL 20 DAY) + INTERVAL 4 HOUR",
            "status": "Scheduled",
            "cap": 100,
            "category": "Công nghệ",
            "price": 0,
            "v_id": v_ids[1],
            "org_idx": 2
        },
        {
            "name": "Diễn đàn Kinh tế 2026",
            "desc": "Giao lưu cùng các chuyên gia kinh tế hàng đầu.",
            "start": "DATE_ADD(NOW(), INTERVAL 15 DAY)",
            "end": "DATE_ADD(NOW(), INTERVAL 15 DAY) + INTERVAL 4 HOUR",
            "status": "Scheduled",
            "cap": 500,
            "category": "Khác",
            "price": 0,
            "v_id": v_ids[0],
            "org_idx": 2
        },
        {
            "name": "Live Concert: Giai điệu Thanh Xuân",
            "desc": "Concert ngoài trời cực đỉnh.",
            "start": "DATE_ADD(NOW(), INTERVAL 18 DAY)",
            "end": "DATE_ADD(NOW(), INTERVAL 18 DAY) + INTERVAL 5 HOUR",
            "status": "Scheduled",
            "cap": 1500,
            "category": "Giải trí",
            "price": 200000,
            "v_id": v_ids[2],
            "org_idx": 1
        },
        {
            "name": "Tech Talk: Tương lai của AI",
            "desc": "Thảo luận về AGI và tự động hóa.",
            "start": "DATE_SUB(NOW(), INTERVAL 2 DAY)",
            "end": "DATE_SUB(NOW(), INTERVAL 2 DAY) + INTERVAL 3 HOUR",
            "status": "Completed",
            "cap": 100,
            "category": "Công nghệ",
            "price": 50000,
            "v_id": v_ids[4],
            "org_idx": 0
        },
        {
            "name": "Khóa học Phát triển Kỹ năng Lãnh đạo",
            "desc": "Trang bị kỹ năng quản lý cho sinh viên.",
            "start": "DATE_ADD(NOW(), INTERVAL 25 DAY)",
            "end": "DATE_ADD(NOW(), INTERVAL 25 DAY) + INTERVAL 4 HOUR",
            "status": "Scheduled",
            "cap": 60,
            "category": "Giáo dục",
            "price": 0,
            "v_id": v_ids[1],
            "org_idx": 2
        }
    ]

    for ev in events_data:
        o_id = org_ids[ev['org_idx']]
        existing_ev = db.execute(text("SELECT event_id FROM Events WHERE event_name = :name"), {"name": ev["name"]}).fetchone()
        if not existing_ev:
            db.execute(text(f"""
                INSERT INTO Events (event_name, description, start_time, end_time, venue_id, organizer_id, max_capacity, status, category, ticket_price)
                VALUES (:name, :desc, {ev['start']}, {ev['end']}, :v_id, :o_id, :cap, :status, :cat, :price)
            """), {
                "name": ev["name"], "desc": ev["desc"],
                "v_id": ev["v_id"], "o_id": o_id, "cap": ev["cap"], "status": ev["status"], "cat": ev["category"], "price": ev["price"]
            })
        else:
            db.execute(text(f"""
                UPDATE Events 
                SET start_time = {ev['start']}, end_time = {ev['end']}, status = :status, category = :cat, ticket_price = :price, venue_id = :v_id, organizer_id = :o_id, max_capacity = :cap, image_url = NULL
                WHERE event_name = :name
            """), {"name": ev["name"], "status": ev["status"], "cat": ev["category"], "price": ev["price"], "v_id": ev["v_id"], "o_id": o_id, "cap": ev["cap"]})
    
    print("✅ Đã tạo các Sự kiện mẫu (Đang diễn ra & Sắp diễn ra)!")

    # 4. Tự động thêm Guest và Đăng ký vé cho tất cả Guest
    import random
    guest_list = [
        ("guest01@example.com", "Nguyễn Văn An", "Sinh viên", "Đại học Kinh tế Quốc dân", "0912345678"),
        ("guest02@example.com", "Trần Thị Bình", "Chuyên viên Marketing", "Tập đoàn Viettel", "0987654321"),
        ("guest03@example.com", "Lê Hoàng Cường", "Lập trình viên", "FPT Software", "0901234567"),
        ("guest04@example.com", "Phạm Thu Dung", "Giám đốc Nhân sự", "Vingroup", "0934567890"),
        ("guest05@example.com", "Hoàng Ngọc Em", "Sinh viên", "Đại học Bách Khoa", "0945678901"),
        ("guest06@example.com", "Vũ Đức Phong", "Kỹ sư Dữ liệu", "VNPT", "0967890123"),
        ("guest07@example.com", "Đặng Thị Giang", "Trưởng phòng IT", "MobiFone", "0978901234"),
        ("guest08@example.com", "Bùi Xuân Hải", "Sinh viên", "Học viện Bưu chính", "0989012345"),
        ("guest09@example.com", "Đỗ Minh In", "Nhà thiết kế", "Freelance", "0990123456"),
        ("guest10@example.com", "Ngô Quốc Khánh", "Nghiên cứu sinh", "ĐHQGHN", "0910987654")
    ]
    
    # Cập nhật schema Guests, Registrations, Feedbacks
    for col, col_type in [("job_title", "VARCHAR(150)"), ("company", "VARCHAR(150)"), ("gender", "VARCHAR(20)"), ("dob", "DATE")]:
        try:
            db.execute(text(f"ALTER TABLE Guests ADD COLUMN {col} {col_type}"))
        except Exception:
            pass

    try:
        db.execute(text("ALTER TABLE Registrations ADD COLUMN group_details JSON"))
    except Exception:
        pass

    try:
        db.execute(text("""
            CREATE TABLE IF NOT EXISTS Feedbacks (
                feedback_id INT AUTO_INCREMENT PRIMARY KEY,
                event_id INT NOT NULL,
                guest_id INT NOT NULL,
                rating INT NOT NULL,
                comment TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (event_id) REFERENCES Events(event_id) ON DELETE CASCADE,
                FOREIGN KEY (guest_id) REFERENCES Guests(guest_id) ON DELETE CASCADE
            )
        """))
    except Exception:
        pass

    for col, col_type in [("rating_content", "INT"), ("rating_logistics", "INT"), ("nps_score", "INT"), ("comment_liked", "TEXT"), ("comment_improve", "TEXT"), ("future_topics", "TEXT"), ("details_json", "JSON")]:
        try:
            db.execute(text(f"ALTER TABLE Feedbacks ADD COLUMN {col} {col_type}"))
        except Exception:
            pass

    guest_ids = []
    for email, name, job, comp, phone in guest_list:
        gender = random.choice(["Nam", "Nữ", "Khác"])
        dob = f"{random.randint(1980, 2005)}-{random.randint(1, 12):02d}-{random.randint(1, 28):02d}"
        g = db.execute(text("SELECT guest_id FROM Guests WHERE email = :email"), {"email": email}).fetchone()
        if not g:
            db.execute(text("INSERT INTO Guests (guest_name, email, job_title, company, phone_number, gender, dob) VALUES (:name, :email, :job, :comp, :phone, :gender, :dob)"), 
                       {"name": name, "email": email, "job": job, "comp": comp, "phone": phone, "gender": gender, "dob": dob})
            g = db.execute(text("SELECT guest_id FROM Guests WHERE email = :email"), {"email": email}).fetchone()
        else:
            db.execute(text("UPDATE Guests SET job_title = :job, company = :comp, phone_number = :phone, gender = :gender, dob = :dob WHERE email = :email"), 
                       {"job": job, "comp": comp, "phone": phone, "gender": gender, "dob": dob, "email": email})
        guest_ids.append(g.guest_id)
        
    print("✅ Đã tạo Khách mời (Guests) cùng thông tin Công ty & Chức danh!")

    # Xử lý sinh Đăng ký & Tài chính cho tất cả sự kiện
    all_events = db.execute(text("SELECT event_id, status, ticket_price, event_name, end_time, max_capacity FROM Events")).fetchall()
    for ev in all_events:
        eid = ev.event_id
        price = float(ev.ticket_price)
        status = ev.status
        event_name = ev.event_name
        orig_end = ev.end_time
        orig_cap = ev.max_capacity
        
        # Tạm thời bypass trigger (Trạng thái, Thời gian kết thúc và Sức chứa) để tránh lỗi CHECK constraint
        db.execute(text("UPDATE Events SET status = 'Scheduled', end_time = DATE_ADD(GREATEST(NOW(), start_time), INTERVAL 1 DAY), max_capacity = 99999 WHERE event_id = :eid"), {"eid": eid})

        # Sinh 5-9 đăng ký ngẫu nhiên
        num_regs = random.randint(5, 9)
        selected_guests = random.sample(guest_ids, num_regs)
        
        for gid in selected_guests:
            guest_name_row = db.execute(text("SELECT guest_name, email FROM Guests WHERE guest_id = :gid"), {"gid": gid}).fetchone()
            g_name = guest_name_row.guest_name if guest_name_row else "Unknown"
            g_email = guest_name_row.email if guest_name_row else ""
            referrals = ["Facebook", "Website", "Bạn bè giới thiệu", "LinkedIn", "Email Marketing"]
            group_details_json = json.dumps([{"name": g_name, "email": g_email, "custom": {"Bạn biết đến sự kiện qua đâu?": random.choice(referrals)}}], ensure_ascii=False)

            reg = db.execute(text("SELECT registration_id FROM Registrations WHERE event_id = :eid AND guest_id = :gid"), {"eid": eid, "gid": gid}).fetchone()
            att = 'Registered'
            if status == 'Completed' or event_name == 'Sự kiện Đã kết thúc: Lễ trao giải NEU 2025':
                att = 'Attended' if random.random() > 0.25 else 'No-show'

            if not reg:
                db.execute(text("INSERT INTO Registrations (event_id, guest_id, attendance_status, group_details) VALUES (:eid, :gid, :att, :g_details)"), 
                           {"eid": eid, "gid": gid, "att": att, "g_details": group_details_json})
            else:
                db.execute(text("UPDATE Registrations SET group_details = :g_details, attendance_status = :att WHERE registration_id = :rid"), 
                           {"g_details": group_details_json, "att": att, "rid": reg.registration_id})
                           
            if att == 'Attended':
                fb = db.execute(text("SELECT feedback_id FROM Feedbacks WHERE event_id = :eid AND guest_id = :gid"), {"eid": eid, "gid": gid}).fetchone()
                if not fb:
                    details = {"Chất lượng nội dung": "Cực kỳ thiết thực và giá trị", "Kỹ năng thuyết trình": "Thu hút, làm chủ sân khấu tốt"}
                    db.execute(text("INSERT INTO Feedbacks (event_id, guest_id, rating, rating_content, rating_logistics, nps_score, comment, comment_liked, comment_improve, future_topics, details_json) VALUES (:eid, :gid, :rating, 4, 5, 9, 'Sự kiện rất tốt!', 'Nội dung hay', 'Nên dài hơn', 'Chủ đề tương lai', :details)"), {"eid": eid, "gid": gid, "rating": random.choice([4, 5]), "details": json.dumps(details, ensure_ascii=False)})

        # Sinh Tài chính
        fin_count = db.execute(text("SELECT COUNT(*) as count FROM Finances WHERE event_id = :eid"), {"eid": eid}).fetchone().count
        if fin_count == 0:
            base_income = (price * num_regs) if price > 0 else 0
            sponsor_income = random.randint(5, 50) * 1000000
            db.execute(text("INSERT INTO Finances (event_id, type, amount, description) VALUES (:eid, 'Income', :amount, :desc)"), 
                       {"eid": eid, "amount": base_income + sponsor_income, "desc": "Doanh thu bán vé & Tài trợ sự kiện"})
            
            num_expenses = random.randint(1, 3)
            expense_descs = ["Thuê địa điểm và setup sân khấu", "Chi phí Catering & Teabreak", "In ấn tài liệu và Marketing", "Quà tặng diễn giả và khách mời"]
            for i in range(num_expenses):
                exp_amount = random.randint(2, 15) * 500000
                db.execute(text("INSERT INTO Finances (event_id, type, amount, description) VALUES (:eid, 'Expense', :amount, :desc)"), 
                           {"eid": eid, "amount": exp_amount, "desc": expense_descs[i]})

        # Phục hồi trạng thái, thời gian kết thúc và sức chứa ban đầu
        db.execute(text("UPDATE Events SET status = :status, end_time = :orig_end, max_capacity = :orig_cap WHERE event_id = :eid"), {"status": status, "orig_end": orig_end, "orig_cap": orig_cap, "eid": eid})

    # Trả sự kiện về quá khứ và cập nhật thành Completed sau khi đã thêm khách xong
    db.execute(text("""
        UPDATE Events 
        SET status = 'Completed',
            start_time = DATE_SUB(NOW(), INTERVAL 10 DAY),
            end_time = DATE_SUB(NOW(), INTERVAL 10 DAY) + INTERVAL 4 HOUR
        WHERE event_name = 'Sự kiện Đã kết thúc: Lễ trao giải NEU 2025'
    """))
    db.commit()

    print("✅ Đã sinh dữ liệu Đăng ký (Registrations) & Tài chính (Finances) cực kỳ phong phú cho tất cả sự kiện!")

def seed_all_test_data():
    with get_db() as db:
        from app.database.auth_models import User, hash_password
        for username, password, fullname, email, role in test_users:
            # Gọi hàm register_user để tạo user và phân quyền tự động
            res = register_user(db, username, password, fullname, email, role)
            if res["success"]:
                print(f"✅ Đã tạo thành công [{role}]: {username} - {fullname}")
            else:
                print(f"⚠️ Đã tồn tại [{role}] {username}. Đang Reset mật khẩu về '{password}'...")
                user = db.query(User).filter_by(username=username).first()
                if user:
                    user.password_hash = hash_password(password)
                    db.commit()
                    print(f"   => Đã cập nhật lại mật khẩu cho {username}!")
                
        # Gọi hàm tạo dữ liệu sự kiện
        seed_events_data(db)

if __name__ == "__main__":
    print("🚀 Đang khởi tạo bộ dữ liệu test tổng hợp...")
    seed_all_test_data()
    print("🎉 Hoàn tất!")