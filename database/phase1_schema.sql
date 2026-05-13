-- ============================================================
--  EVENT MANAGEMENT SYSTEM — GIAI ĐOẠN 1
--  Phiên bản mở rộng: 6 bảng, thuộc tính nâng cao
--  NEU — DATCOM Lab | Project 14
-- ============================================================

DROP DATABASE IF EXISTS event_management;
CREATE DATABASE event_management
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE event_management;


-- ============================================================
-- BẢNG 1: VENUES
-- Mở rộng: capacity, availability_status
-- ============================================================
CREATE TABLE Venues (
    venue_id            INT           NOT NULL AUTO_INCREMENT,
    venue_name          VARCHAR(100)  NOT NULL,
    address             VARCHAR(200)  NOT NULL,
    capacity            INT           NOT NULL DEFAULT 0,
    availability_status ENUM(
                            'Available',    -- Sẵn sàng
                            'Booked',       -- Đã được đặt
                            'Maintenance'   -- Đang bảo trì
                        ) NOT NULL DEFAULT 'Available',
    phone_number        VARCHAR(15)   NULL,

    CONSTRAINT pk_venues    PRIMARY KEY (venue_id),
    CONSTRAINT chk_capacity CHECK (capacity >= 0)
);


-- ============================================================
-- BẢNG 2: ORGANIZERS
-- ============================================================
CREATE TABLE Organizers (
    organizer_id        INT          NOT NULL AUTO_INCREMENT,
    organizer_name      VARCHAR(150) NOT NULL,
    address             VARCHAR(200) NOT NULL,
    phone_number        VARCHAR(15)  NOT NULL,
    email               VARCHAR(100) NULL,
    department          VARCHAR(100) NULL,
    bank_name           VARCHAR(100) NULL,
    bank_account_number VARCHAR(50)  NULL,
    bank_account_name   VARCHAR(150) NULL,

    CONSTRAINT pk_organizers   PRIMARY KEY (organizer_id),
    CONSTRAINT uq_org_email    UNIQUE (email)
);


-- ============================================================
-- BẢNG 3: EVENTS
-- Mở rộng: start_time, end_time, status (4 giá trị),
--          organizer_id (FK mới), max_capacity
-- ============================================================
CREATE TABLE Events (
    event_id        INT          NOT NULL AUTO_INCREMENT,
    event_name      VARCHAR(150) NOT NULL,
    start_time      DATETIME     NOT NULL,
    end_time        DATETIME     NOT NULL,
    venue_id        INT          NOT NULL,
    organizer_id    INT          NOT NULL,
    status          ENUM(
                      'Draft',        -- Đang soạn thảo
                      'Scheduled',    -- Đã lên lịch
                      'Full',         -- Hết chỗ
                      'Completed',    -- Đã kết thúc
                      'Cancelled'     -- Đã hủy
                  ) NOT NULL DEFAULT 'Draft',
    max_capacity    INT          NULL,   -- NULL = không giới hạn
    description     TEXT         NULL,
    category        VARCHAR(50)    NULL DEFAULT 'Khác',
    ticket_price    DECIMAL(15, 2) NOT NULL DEFAULT 0.00,
    image_url       VARCHAR(500)   NULL,
    event_type      VARCHAR(50)    DEFAULT 'Conference',
    target_audience VARCHAR(50)    DEFAULT 'All',
    is_private      BOOLEAN        DEFAULT FALSE,
    access_code     VARCHAR(50)    DEFAULT NULL,
    ticket_tiers    JSON           NULL,
    custom_fields   JSON           NULL,

    CONSTRAINT pk_events         PRIMARY KEY (event_id),
    CONSTRAINT fk_event_venue    FOREIGN KEY (venue_id)
        REFERENCES Venues(venue_id)
        ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT fk_event_org      FOREIGN KEY (organizer_id)
        REFERENCES Organizers(organizer_id)
        ON DELETE RESTRICT ON UPDATE CASCADE,
    CONSTRAINT chk_time_order    CHECK (end_time > start_time)
);


-- ============================================================
-- BẢNG 4: GUESTS
-- ============================================================
CREATE TABLE Guests (
    guest_id         INT          NOT NULL AUTO_INCREMENT,
    guest_name       VARCHAR(100) NOT NULL,
    email            VARCHAR(100) NOT NULL,
    phone_number     VARCHAR(15)  NULL,
    address          VARCHAR(200) NULL,
    created_at       TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    is_public        BOOLEAN      DEFAULT TRUE,
    job_title        VARCHAR(150) NULL,
    company          VARCHAR(150) NULL,
    gender           VARCHAR(20)  NULL,
    dob              DATE         NULL,
    bio              TEXT         NULL,
    linkedin_url     VARCHAR(255) NULL,
    services_offered VARCHAR(255) NULL,
    buying_intent    VARCHAR(255) NULL,
    is_verified      BOOLEAN      DEFAULT FALSE,
    kyc_status       VARCHAR(50)  DEFAULT 'Unverified',
    portfolio_url    VARCHAR(500) NULL,
    video_url        VARCHAR(500) NULL,

    CONSTRAINT pk_guests       PRIMARY KEY (guest_id),
    CONSTRAINT uq_guest_email  UNIQUE (email)
);


-- ============================================================
-- BẢNG 5: REGISTRATIONS
-- Mở rộng: attendance_status (Registered/Attended/No-show)
-- Quan hệ M:N giữa Events và Guests
-- ============================================================
CREATE TABLE Registrations (
    registration_id   INT  NOT NULL AUTO_INCREMENT,
    event_id          INT  NOT NULL,
    guest_id          INT  NOT NULL,
    registration_date DATE NOT NULL DEFAULT (CURRENT_DATE),
    attendance_status ENUM(
                          'Registered', 'Attended', 'No-show', 'Refund Requested', 'Refunded'
                      ) NOT NULL DEFAULT 'Registered',
    checkin_time      DATETIME NULL,     -- Thời điểm check-in thực tế
    ticket_count      INT          DEFAULT 1,
    ticket_type       VARCHAR(50)  DEFAULT 'Standard',
    vat_company       VARCHAR(150) NULL,
    vat_tax_code      VARCHAR(50)  NULL,
    group_details     JSON         NULL,

    CONSTRAINT pk_registrations   PRIMARY KEY (registration_id),
    CONSTRAINT uq_event_guest     UNIQUE (event_id, guest_id),
    CONSTRAINT fk_reg_event       FOREIGN KEY (event_id)
        REFERENCES Events(event_id)
        ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT fk_reg_guest       FOREIGN KEY (guest_id)
        REFERENCES Guests(guest_id)
        ON DELETE CASCADE ON UPDATE CASCADE
);


-- ============================================================
-- BẢNG 6: FINANCES (BỔ SUNG)
-- Theo dõi thu chi theo từng sự kiện
-- Đáp ứng yêu cầu demo "adding income, managing expenses"
-- ============================================================
CREATE TABLE Finances (
    finance_id       INT            NOT NULL AUTO_INCREMENT,
    event_id         INT            NOT NULL,
    type             ENUM(
                         'Income',   -- Thu: phí đăng ký, tài trợ
                         'Expense'   -- Chi: địa điểm, in ấn, catering
                     ) NOT NULL,
    amount           DECIMAL(15, 2) NOT NULL,
    description      VARCHAR(200)   NULL,
    transaction_date DATE           NOT NULL DEFAULT (CURRENT_DATE),
    created_by       INT            NULL,    -- organizer_id tham chiếu mềm

    CONSTRAINT pk_finances      PRIMARY KEY (finance_id),
    CONSTRAINT fk_fin_event     FOREIGN KEY (event_id)
        REFERENCES Events(event_id)
        ON DELETE CASCADE ON UPDATE CASCADE,
    CONSTRAINT chk_amount       CHECK (amount > 0)
);


-- ============================================================
-- BẢNG 7: FEEDBACKS (BỔ SUNG)
-- Lưu trữ đánh giá, khảo sát của khách hàng sau sự kiện
-- ============================================================
CREATE TABLE Feedbacks (
    feedback_id       INT AUTO_INCREMENT PRIMARY KEY,
    event_id          INT NOT NULL,
    guest_id          INT NOT NULL,
    rating            INT NOT NULL,
    comment           TEXT NULL,
    created_at        TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    rating_content    INT NULL,
    rating_logistics  INT NULL,
    nps_score         INT NULL,
    comment_liked     TEXT NULL,
    comment_improve   TEXT NULL,
    future_topics     TEXT NULL,
    details_json      JSON NULL,
    FOREIGN KEY (event_id) REFERENCES Events(event_id) ON DELETE CASCADE,
    FOREIGN KEY (guest_id) REFERENCES Guests(guest_id) ON DELETE CASCADE
);

-- ============================================================
-- INDEXES
-- ============================================================
CREATE INDEX idx_event_start    ON Events(start_time);
CREATE INDEX idx_event_status   ON Events(status);
CREATE INDEX idx_event_venue    ON Events(venue_id);
CREATE INDEX idx_event_org      ON Events(organizer_id);
CREATE INDEX idx_guest_email    ON Guests(email);
CREATE INDEX idx_reg_event      ON Registrations(event_id);
CREATE INDEX idx_reg_guest      ON Registrations(guest_id);
CREATE INDEX idx_reg_status     ON Registrations(attendance_status);
CREATE INDEX idx_fin_event      ON Finances(event_id);
CREATE INDEX idx_fin_type       ON Finances(type);
CREATE INDEX idx_fin_date       ON Finances(transaction_date);
CREATE INDEX idx_venue_status   ON Venues(availability_status);
CREATE INDEX idx_feedback_event_guest ON Feedbacks(event_id, guest_id);


-- ============================================================
-- DỮ LIỆU MẪU
-- ============================================================

-- Venues (10 dòng)
INSERT INTO Venues (venue_name, address, capacity, availability_status, phone_number) VALUES
('Hội trường A — NEU',        '207 Giải Phóng, Hai Bà Trưng, HN',   500, 'Available',   '024 3628 0280'),
('Phòng hội thảo B2 — NEU',   '207 Giải Phóng, Hai Bà Trưng, HN',    80, 'Booked',      '024 3628 0281'),
('Trung tâm Melia Hà Nội',    '44B Lý Thường Kiệt, Hoàn Kiếm, HN',  600, 'Available',   '024 3934 3343'),
('Khách sạn Lotte Hà Nội',    '54 Liễu Giai, Ba Đình, HN',           450, 'Available',   '024 3333 1000'),
('Cung Văn hóa Lao Động',     '91 Trần Hưng Đạo, Hoàn Kiếm, HN',    800, 'Available',   '024 3822 3842'),
('Phòng Đào tạo C — FPT',     'Khu CNC Hòa Lạc, Thạch Thất, HN',   150, 'Maintenance', '024 7300 5588'),
('Trung tâm Hội nghị QG',     '57 Phạm Hùng, Nam Từ Liêm, HN',     3000, 'Booked',      '024 3771 5000'),
('Hội trường ĐH Bách Khoa',   '1 Đại Cồ Việt, Hai Bà Trưng, HN',   300, 'Available',   '024 3869 2008'),
('Nhà Văn hóa Thanh Niên',    '47 Đinh Tiên Hoàng, Hoàn Kiếm, HN', 200, 'Available',   '024 3825 8822'),
('Phòng hội thảo Sheraton',   '11 Xuân Diệu, Tây Hồ, HN',           120, 'Available',   '024 3719 9000');

-- Organizers (10 dòng)
INSERT INTO Organizers (organizer_name, address, phone_number, email, department) VALUES
('Khoa Công nghệ Thông tin — NEU',  '207 Giải Phóng, HN', '024 3628 0282', 'it@neu.edu.vn',              'Đào tạo'),
('Câu lạc bộ DATCOM',               '207 Giải Phóng, HN', '0912 345 678',  'datcom@neu.edu.vn',          'Sinh viên'),
('Phòng Công tác Sinh viên — NEU',  '207 Giải Phóng, HN', '024 3628 0290', 'ctsv@neu.edu.vn',            'Hành chính'),
('Viện Đào tạo Quốc tế — NEU',      '207 Giải Phóng, HN', '024 3628 0295', 'international@neu.edu.vn',   'Đào tạo QT'),
('Hội Sinh viên NEU',               '207 Giải Phóng, HN', '0934 567 890',  'hoisinhvien@neu.edu.vn',     'Đoàn thể'),
('Công ty TNHH FPT Software',       '17 Duy Tân, CG, HN', '024 7300 7300', 'event@fpt.com.vn',           'Marketing'),
('VietnamWorks HR Solutions',       '189 Giảng Võ, BD, HN','024 3776 2121', 'hr@vietnamworks.com',        'Nhân sự'),
('Tổ chức AIESEC Việt Nam',         '4 Đinh Lễ, HK, HN',  '096 789 0123',  'vn@aiesec.net',              'Phát triển'),
('Phòng GD&ĐT Q. Hai Bà Trưng',    '220 Phố Huế, HBT, HN','024 3974 3083','hbt@gd.edu.vn',              'Giáo dục'),
('Ban Tổ chức Techfest 2025',       '1 Đại Cồ Việt, HN',  '024 3869 2000', 'techfest@most.gov.vn',       'KH&CN');

-- Events (10 dòng) — bổ sung các trường dữ liệu mới
INSERT INTO Events (event_name, start_time, end_time, venue_id, organizer_id, status, max_capacity, description, category, ticket_price, image_url, event_type, target_audience, is_private, access_code) VALUES
('Hội thảo Trí tuệ Nhân tạo 2025',         '2025-06-15 08:00:00', '2025-06-15 17:00:00', 1,  1,  'Scheduled',  400, 'Xu hướng AI tại Việt Nam.', 'Công nghệ', 50000.00, 'https://images.unsplash.com/photo-1535223289827-42f1e9919769?w=800', 'Conference', 'Specialist / Staff', TRUE, 'VIP2026'),
('Tech Talk NEU — Mùa 3',                   '2025-07-01 14:00:00', '2025-07-01 17:00:00', 2,  2,  'Draft',       70, 'Diễn đàn công nghệ sinh viên.', 'Công nghệ', 0.00, 'https://images.unsplash.com/photo-1542744173-8e7e53415bb0?w=800', 'Workshop', 'All', FALSE, NULL),
('Ngày hội Việc làm IT 2025',               '2025-07-20 08:30:00', '2025-07-20 16:30:00', 3,  7,  'Scheduled',  500, '50+ doanh nghiệp tuyển dụng.', 'Công nghệ', 0.00, 'https://images.unsplash.com/photo-1556761175-5973dc0f32e7?w=800', 'Trade Show', 'All', FALSE, NULL),
('Workshop Python cho người mới',           '2025-05-10 09:00:00', '2025-05-10 12:00:00', 2,  2,  'Completed',   60, 'Python từ cơ bản đến nâng cao.', 'Giáo dục', 100000.00, 'https://images.unsplash.com/photo-1555949963-ff9fe0c870eb?w=800', 'Workshop', 'All', FALSE, NULL),
('Seminar An ninh Mạng 2025',               '2025-05-25 13:30:00', '2025-05-25 17:00:00', 1,  1,  'Completed',  300, 'Mối đe dọa mạng năm 2025.', 'Công nghệ', 50000.00, 'https://images.unsplash.com/photo-1526628953301-3e589a6a8b74?w=800', 'Conference', 'Specialist / Staff', FALSE, NULL),
('Gala Kỷ niệm 65 năm NEU',                 '2025-08-15 17:00:00', '2025-08-15 21:00:00', 5,  3,  'Scheduled',  700, 'Lễ kỷ niệm 65 năm thành lập NEU.', 'Giải trí', 0.00, 'https://images.unsplash.com/photo-1514525253161-7a46d19cd819?w=800', 'Networking', 'All', FALSE, NULL),
('Cuộc thi CodeStorm — DATCOM',             '2025-09-05 08:00:00', '2025-09-05 18:00:00', 8,  2,  'Draft',      200, 'Thi lập trình thuật toán.', 'Công nghệ', 0.00, 'https://images.unsplash.com/photo-1587620962725-abab7fe55159?w=800', 'Workshop', 'All', FALSE, NULL),
('Diễn đàn Kinh tế Cấp cao',               '2025-06-30 08:00:00', '2025-06-30 17:00:00', 7,  10, 'Full',      2000, 'Chuyển đổi số từ tập đoàn lớn.', 'Khác', 2000000.00, 'https://images.unsplash.com/photo-1560439514-4e28943a15ac?w=800', 'Conference', 'C-level / Executive', TRUE, 'VIP2026'),
('Khóa học Data Science Thực chiến',        '2025-07-15 09:00:00', '2025-07-16 17:00:00', 6,  6,  'Scheduled',  120, '2 ngày phân tích dữ liệu & ML.', 'Giáo dục', 1500000.00, 'https://images.unsplash.com/photo-1551288049-bebda4e38f71?w=800', 'Workshop', 'Specialist / Staff', FALSE, NULL),
('Lễ tốt nghiệp Khóa 62 — NEU',            '2025-06-05 07:30:00', '2025-06-05 11:30:00', 5,  3,  'Completed', 1500, 'Lễ trao bằng khóa 62.', 'Giáo dục', 0.00, 'https://images.unsplash.com/photo-1523050854058-8df90110c9f1?w=800', 'Networking', 'All', FALSE, NULL);

-- Guests (10 dòng)
INSERT INTO Guests (guest_name, email, phone_number, address, job_title, company) VALUES
('Nguyễn Văn An',    'an.nguyen@email.com',          '0901 234 567', '45 Phố Huế, Hai Bà Trưng, HN', 'CEO', 'TechCorp'),
('Trần Thị Bình',    'binh.tran@gmail.com',           '0912 345 678', '12 Nguyễn Trãi, Thanh Xuân, HN', 'Marketing Manager', 'AdSolutions'),
('Lê Minh Cường',    'cuong.le@neu.edu.vn',           '0923 456 789', '207 Giải Phóng, HN', 'Sinh viên', 'Đại học Kinh tế Quốc dân'),
('Phạm Thị Dung',    'dung.pham@student.neu.edu.vn',  '0934 567 890', '78 Bạch Mai, Hai Bà Trưng, HN', 'Sinh viên', 'Đại học Kinh tế Quốc dân'),
('Hoàng Văn Em',     'em.hoang@fpt.com.vn',           '0945 678 901', '17 Duy Tân, Cầu Giấy, HN', 'Software Engineer', 'FPT Software'),
('Vũ Thị Phương',    'phuong.vu@gmail.com',           '0956 789 012', '33 Kim Mã, Ba Đình, HN', 'HR Specialist', 'VietnamWorks'),
('Đỗ Quang Giáp',    'giap.do@techco.vn',             '0967 890 123', '56 Láng Hạ, Đống Đa, HN', 'Project Manager', 'TechCo'),
('Ngô Thị Hoa',      'hoa.ngo@yahoo.com',             '0978 901 234', '89 Trần Duy Hưng, Cầu Giấy, HN', 'Freelancer', NULL),
('Bùi Đức Hùng',     'hung.bui@microsoft.com',        '0989 012 345', '25 Xuân Thủy, Cầu Giấy, HN', 'Cloud Architect', 'Microsoft Vietnam'),
('Lý Thị Kim Oanh',  'oanh.ly@gmail.com',             '0990 123 456', '101 Nguyễn Chí Thanh, Đống Đa, HN', 'Accountant', 'KPMG');

-- Registrations (10 dòng) — dùng attendance_status mới
INSERT INTO Registrations (event_id, guest_id, registration_date, attendance_status, checkin_time) VALUES
(1, 1, '2025-05-01', 'Registered', NULL),
(1, 2, '2025-05-02', 'Registered', NULL),
(1, 3, '2025-05-03', 'Registered', NULL),
(2, 4, '2025-05-10', 'Registered', NULL),
(2, 5, '2025-05-11', 'Registered', NULL),
(4, 6, '2025-04-20', 'Attended',   '2025-05-10 09:05:00'),
(4, 7, '2025-04-21', 'Attended',   '2025-05-10 09:12:00'),
(5, 8, '2025-04-25', 'Attended',   '2025-05-25 13:35:00'),
(5, 9, '2025-04-26', 'No-show',    NULL),
(10,10, '2025-05-15', 'Attended',  '2025-06-05 07:45:00');

-- Finances (10 dòng) — thu chi theo sự kiện
INSERT INTO Finances (event_id, type, amount, description, transaction_date, created_by) VALUES
(1, 'Income',  50000000.00, 'Tài trợ từ FPT Software',             '2025-05-15', 1),
(1, 'Income',  12000000.00, 'Phí đăng ký 400 đại biểu x 30k',    '2025-05-20', 1),
(1, 'Expense', 25000000.00, 'Thuê hội trường Hội trường A',        '2025-05-10', 1),
(1, 'Expense',  8000000.00, 'In ấn tài liệu, banner, backdrop',   '2025-06-01', 1),
(1, 'Expense',  6500000.00, 'Catering — coffee break & lunch',    '2025-06-10', 1),
(4, 'Income',   3600000.00, 'Phí tham gia 60 sinh viên x 60k',   '2025-04-30', 2),
(4, 'Expense',  1200000.00, 'Thuê phòng B2 half-day',             '2025-04-25', 2),
(4, 'Expense',   500000.00, 'Nước uống và snack',                 '2025-05-08', 2),
(6, 'Income', 150000000.00, 'Ngân sách NEU cấp cho sự kiện',      '2025-07-01', 3),
(6, 'Expense', 80000000.00, 'Thuê Cung Văn hóa Lao Động',         '2025-07-15', 3);


-- ============================================================
-- VIEWS MỞ RỘNG
-- ============================================================

-- View 1: Sự kiện sắp tới (dùng start_time)
CREATE VIEW view_upcoming_events AS
SELECT
    e.event_id,
    e.event_name,
    DATE_FORMAT(e.start_time, '%d/%m/%Y %H:%i') AS start_time,
    DATE_FORMAT(e.end_time,   '%d/%m/%Y %H:%i') AS end_time,
    TIMESTAMPDIFF(MINUTE, e.start_time, e.end_time) AS duration_min,
    v.venue_name,
    v.capacity   AS venue_capacity,
    e.max_capacity,
    o.organizer_name,
    e.status
FROM Events e
JOIN Venues     v ON e.venue_id     = v.venue_id
JOIN Organizers o ON e.organizer_id = o.organizer_id
WHERE e.start_time >= NOW()
  AND e.status IN ('Draft', 'Scheduled')
ORDER BY e.start_time;

-- View 2: Tổng hợp thống kê sự kiện + tài chính
CREATE VIEW view_event_summary AS
SELECT
    e.event_id,
    e.event_name,
    e.start_time,
    e.status,
    v.venue_name,
    COUNT(DISTINCT r.registration_id)                             AS total_registered,
    SUM(r.attendance_status = 'Attended')                        AS total_attended,
    SUM(r.attendance_status = 'No-show')                         AS total_noshow,
    ROUND(SUM(r.attendance_status='Attended')
          / NULLIF(COUNT(r.registration_id),0) * 100, 2)        AS attendance_rate_pct,
    COALESCE(SUM(CASE WHEN f.type='Income'  THEN f.amount END),0) AS total_income,
    COALESCE(SUM(CASE WHEN f.type='Expense' THEN f.amount END),0) AS total_expense,
    COALESCE(SUM(CASE WHEN f.type='Income'  THEN f.amount END),0)
    - COALESCE(SUM(CASE WHEN f.type='Expense' THEN f.amount END),0) AS net_balance
FROM Events e
JOIN Venues v              ON e.venue_id = v.venue_id
LEFT JOIN Registrations r  ON e.event_id = r.event_id
LEFT JOIN Finances f       ON e.event_id = f.event_id
GROUP BY e.event_id, e.event_name, e.start_time, e.status, v.venue_name;

-- View 3: Báo cáo tài chính tổng hợp
CREATE VIEW view_finance_report AS
SELECT
    e.event_id,
    e.event_name,
    f.type,
    f.amount,
    f.description,
    f.transaction_date,
    o.organizer_name
FROM Finances f
JOIN Events     e ON f.event_id     = e.event_id
JOIN Organizers o ON e.organizer_id = o.organizer_id
ORDER BY f.transaction_date DESC;

-- View 4: Thống kê địa điểm
CREATE VIEW view_venue_usage AS
SELECT
    v.venue_id,
    v.venue_name,
    v.capacity,
    v.availability_status,
    COUNT(e.event_id) AS total_events,
    SUM(e.status = 'Completed') AS completed_events
FROM Venues v
LEFT JOIN Events e ON v.venue_id = e.venue_id
GROUP BY v.venue_id, v.venue_name, v.capacity, v.availability_status;


-- ============================================================
-- USER DEFINED FUNCTIONS
-- ============================================================
DELIMITER $$

CREATE FUNCTION fn_attendance_rate(p_event_id INT)
RETURNS DECIMAL(5,2)
READS SQL DATA DETERMINISTIC
BEGIN
    DECLARE v_total   INT DEFAULT 0;
    DECLARE v_attended INT DEFAULT 0;
    SELECT COUNT(*) INTO v_total
    FROM Registrations WHERE event_id = p_event_id;
    SELECT SUM(attendance_status = 'Attended') INTO v_attended
    FROM Registrations WHERE event_id = p_event_id;
    IF v_total = 0 THEN RETURN 0.00; END IF;
    RETURN ROUND(v_attended / v_total * 100, 2);
END$$

CREATE FUNCTION fn_event_balance(p_event_id INT)
RETURNS DECIMAL(15,2)
READS SQL DATA DETERMINISTIC
BEGIN
    DECLARE v_income  DECIMAL(15,2) DEFAULT 0;
    DECLARE v_expense DECIMAL(15,2) DEFAULT 0;
    SELECT COALESCE(SUM(amount),0) INTO v_income
    FROM Finances WHERE event_id = p_event_id AND type = 'Income';
    SELECT COALESCE(SUM(amount),0) INTO v_expense
    FROM Finances WHERE event_id = p_event_id AND type = 'Expense';
    RETURN v_income - v_expense;
END$$

CREATE FUNCTION fn_total_guests(p_event_id INT)
RETURNS INT
READS SQL DATA DETERMINISTIC
BEGIN
    DECLARE v_count INT;
    SELECT COUNT(*) INTO v_count
    FROM Registrations
    WHERE event_id = p_event_id
      AND attendance_status != 'No-show';
    RETURN v_count;
END$$

DELIMITER ;


-- ============================================================
-- STORED PROCEDURES
-- ============================================================
DELIMITER $$

-- Đăng ký khách tham dự
CREATE PROCEDURE sp_register_guest(
    IN  p_event_id INT,
    IN  p_guest_id INT,
    OUT p_result   VARCHAR(200)
)
BEGIN
    DECLARE v_exists      INT DEFAULT 0;
    DECLARE v_max_cap     INT DEFAULT NULL;
    DECLARE v_current     INT DEFAULT 0;
    DECLARE v_status      VARCHAR(20);

    SELECT COUNT(*) INTO v_exists
    FROM Registrations
    WHERE event_id = p_event_id AND guest_id = p_guest_id;

    IF v_exists > 0 THEN
        SET p_result = 'ERROR: Khách đã đăng ký sự kiện này rồi.';
    ELSE
        SELECT status, max_capacity INTO v_status, v_max_cap
        FROM Events WHERE event_id = p_event_id;

        IF v_status IN ('Completed','Cancelled') THEN
            SET p_result = 'ERROR: Sự kiện đã kết thúc hoặc bị hủy.';
        ELSE
            IF v_max_cap IS NOT NULL THEN
                SELECT COUNT(*) INTO v_current
                FROM Registrations WHERE event_id = p_event_id;
                IF v_current >= v_max_cap THEN
                    UPDATE Events SET status = 'Full' WHERE event_id = p_event_id;
                    SET p_result = 'ERROR: Sự kiện đã hết chỗ.';
                ELSE
                    INSERT INTO Registrations (event_id, guest_id, registration_date, attendance_status)
                    VALUES (p_event_id, p_guest_id, CURRENT_DATE, 'Registered');
                    SET p_result = 'OK: Đăng ký thành công.';
                END IF;
            ELSE
                INSERT INTO Registrations (event_id, guest_id, registration_date, attendance_status)
                VALUES (p_event_id, p_guest_id, CURRENT_DATE, 'Registered');
                SET p_result = 'OK: Đăng ký thành công.';
            END IF;
        END IF;
    END IF;
END$$

-- Check-in và cập nhật attendance_status = 'Attended'
CREATE PROCEDURE sp_guest_checkin(
    IN  p_event_id INT,
    IN  p_guest_id INT,
    OUT p_result   VARCHAR(200)
)
BEGIN
    DECLARE v_status VARCHAR(20);
    SELECT attendance_status INTO v_status
    FROM Registrations
    WHERE event_id = p_event_id AND guest_id = p_guest_id;

    IF v_status IS NULL THEN
        SET p_result = 'ERROR: Khách chưa đăng ký sự kiện này.';
    ELSEIF v_status = 'Attended' THEN
        SET p_result = 'ERROR: Khách đã check-in rồi.';
    ELSE
        UPDATE Registrations
        SET attendance_status = 'Attended', checkin_time = NOW()
        WHERE event_id = p_event_id AND guest_id = p_guest_id;
        SET p_result = 'OK: Check-in thành công. Trạng thái: Attended.';
    END IF;
END$$

-- Ghi nhận thu/chi cho sự kiện
CREATE PROCEDURE sp_add_finance(
    IN  p_event_id    INT,
    IN  p_type        ENUM('Income','Expense'),
    IN  p_amount      DECIMAL(15,2),
    IN  p_description VARCHAR(200),
    IN  p_created_by  INT,
    OUT p_result      VARCHAR(200)
)
BEGIN
    IF p_amount <= 0 THEN
        SET p_result = 'ERROR: Số tiền phải lớn hơn 0.';
    ELSE
        INSERT INTO Finances (event_id, type, amount, description, transaction_date, created_by)
        VALUES (p_event_id, p_type, p_amount, p_description, CURRENT_DATE, p_created_by);
        SET p_result = CONCAT('OK: Ghi nhận ', p_type, ' ', FORMAT(p_amount,0), ' VND thành công.');
    END IF;
END$$

-- Báo cáo sự kiện theo khoảng thời gian
CREATE PROCEDURE sp_event_report(IN p_from DATE, IN p_to DATE)
BEGIN
    SELECT event_name, start_time, status, venue_name,
           total_registered, total_attended, attendance_rate_pct,
           total_income, total_expense, net_balance
    FROM view_event_summary
    WHERE DATE(start_time) BETWEEN p_from AND p_to
    ORDER BY start_time;
END$$

DELIMITER ;


-- ============================================================
-- TRIGGERS
-- ============================================================
DELIMITER $$

-- Tự động cập nhật status = 'Full' khi đạt max_capacity
CREATE TRIGGER trg_auto_full_status
AFTER INSERT ON Registrations
FOR EACH ROW
BEGIN
    DECLARE v_max_cap INT;
    DECLARE v_current INT;

    SELECT max_capacity INTO v_max_cap
    FROM Events WHERE event_id = NEW.event_id;

    IF v_max_cap IS NOT NULL THEN
        SELECT COUNT(*) INTO v_current
        FROM Registrations WHERE event_id = NEW.event_id;

        IF v_current >= v_max_cap THEN
            UPDATE Events SET status = 'Full'
            WHERE event_id = NEW.event_id AND status = 'Scheduled';
        END IF;
    END IF;
END$$

-- Tự động cập nhật availability_status của Venue
DELIMITER $$
CREATE TRIGGER trg_update_venue_availability
AFTER INSERT ON Registrations
FOR EACH ROW
BEGIN
    DECLARE v_venue_id INT;
    DECLARE v_venue_cap INT;
    DECLARE v_current_booked INT;

    SELECT venue_id INTO v_venue_id FROM Events WHERE event_id = NEW.event_id;
    SELECT capacity INTO v_venue_cap FROM Venues WHERE venue_id = v_venue_id;

    -- Chỉ đếm registrations của những event đang diễn ra / chưa kết thúc tại venue này
    SELECT COUNT(*) INTO v_current_booked
    FROM Registrations r
    JOIN Events e ON r.event_id = e.event_id
    WHERE e.venue_id = v_venue_id 
      AND r.attendance_status != 'No-show'
      AND e.status NOT IN ('Completed', 'Cancelled');

    IF v_current_booked >= v_venue_cap THEN
        UPDATE Venues SET availability_status = 'Booked' 
        WHERE venue_id = v_venue_id;
    END IF;
END$$
DELIMITER ;

DELIMITER $$

-- Ngăn đăng ký sự kiện đã kết thúc
CREATE TRIGGER trg_block_past_registration
BEFORE INSERT ON Registrations
FOR EACH ROW
BEGIN
    DECLARE v_status    VARCHAR(20);
    DECLARE v_end_time  DATETIME;

    SELECT status, end_time INTO v_status, v_end_time
    FROM Events WHERE event_id = NEW.event_id;

    IF v_end_time < NOW() OR v_status IN ('Completed','Cancelled') THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Không thể đăng ký sự kiện đã kết thúc hoặc bị hủy.';
    END IF;
END$$

DELIMITER ;


-- ============================================================
-- PHÂN QUYỀN & BẢO MẬT (ĐÃ TỐI ƯU - COLUMN LEVEL + VIEW)
-- ============================================================

CREATE USER IF NOT EXISTS 'coordinator'@'localhost' IDENTIFIED BY 'Coord@2025!';
GRANT ALL PRIVILEGES ON event_management.* TO 'coordinator'@'localhost';

-- ==================== REGISTRATION STAFF ====================
CREATE USER IF NOT EXISTS 'reg_staff'@'localhost' IDENTIFIED BY 'Staff@2025!';

-- Chỉ cho phép xem qua View (ẩn email, phone_number của khách)
GRANT SELECT ON event_management.view_upcoming_events TO 'reg_staff'@'localhost';
GRANT SELECT ON event_management.view_event_summary TO 'reg_staff'@'localhost';

-- Chỉ được UPDATE 2 cột cần thiết trên bảng Registrations
GRANT UPDATE (attendance_status, checkin_time) 
    ON event_management.Registrations TO 'reg_staff'@'localhost';

-- ==================== FINANCE OFFICER ====================
CREATE USER IF NOT EXISTS 'finance_officer'@'localhost' IDENTIFIED BY 'Finance@2025!';

-- Chỉ cho phép xem báo cáo tài chính qua View
GRANT SELECT ON event_management.view_finance_report TO 'finance_officer'@'localhost';
GRANT SELECT ON event_management.view_event_summary TO 'finance_officer'@'localhost';

-- Cho phép ghi nhận thu/chi
GRANT INSERT, UPDATE 
    ON event_management.Finances TO 'finance_officer'@'localhost';

FLUSH PRIVILEGES;


-- ============================================================
-- KIỂM TRA
-- ============================================================
SELECT * FROM view_upcoming_events;
SELECT * FROM view_event_summary;
SELECT * FROM view_finance_report LIMIT 10;
SELECT fn_attendance_rate(4)  AS attendance_pct;
SELECT fn_event_balance(1)    AS net_balance_vnd;
CALL sp_event_report('2025-06-01','2025-09-30');

-- ============================================================
-- END OF SCRIPT — GIAI ĐOẠN 1
-- ============================================================