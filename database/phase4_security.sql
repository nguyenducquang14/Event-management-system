-- ============================================================
--  GIAI ĐOẠN 4: BẢO MẬT VÀ QUẢN TRỊ CƠ SỞ DỮ LIỆU
--  Event Management System — NEU DATCOM Lab | Project 14
--  Nguyên tắc: Least Privilege + RBAC + Column-level Security
--  Chạy sau phase1_schema.sql và phase3_advanced_objects.sql
-- ============================================================

USE event_management;


-- ============================================================
-- PHẦN 1: ROLE-BASED ACCESS CONTROL (RBAC)
-- Tạo Role trước, gán quyền cho Role, rồi gán Role cho User
-- Nguyên tắc "Least Privilege": mỗi role chỉ có đúng quyền
-- tối thiểu cần thiết để thực hiện công việc của mình
-- ============================================================

-- Xóa users cũ nếu tồn tại (để chạy lại script không bị lỗi)
DROP USER IF EXISTS 'coordinator'@'localhost';
DROP USER IF EXISTS 'checkin_staff_user'@'localhost';
DROP USER IF EXISTS 'finance_user'@'localhost';
DROP USER IF EXISTS 'readonly_user'@'localhost';

-- Xóa roles cũ nếu tồn tại
DROP ROLE IF EXISTS 'event_manager';
DROP ROLE IF EXISTS 'checkin_staff';
DROP ROLE IF EXISTS 'finance_officer';
DROP ROLE IF EXISTS 'readonly_viewer';

FLUSH PRIVILEGES;


-- ────────────────────────────────────────────────────────────
-- ROLE 1: event_manager (Ban tổ chức — quyền cao nhất)
-- Có thể quản lý toàn bộ sự kiện, địa điểm, tài chính
-- KHÔNG có quyền DROP DATABASE, ALTER TABLE (bảo vệ schema)
-- ────────────────────────────────────────────────────────────
CREATE ROLE 'event_manager';

-- Toàn quyền trên các bảng nghiệp vụ
GRANT SELECT, INSERT, UPDATE, DELETE ON event_management.Events       TO 'event_manager';
GRANT SELECT, INSERT, UPDATE, DELETE ON event_management.Venues       TO 'event_manager';
GRANT SELECT, INSERT, UPDATE, DELETE ON event_management.Organizers   TO 'event_manager';
GRANT SELECT, INSERT, UPDATE, DELETE ON event_management.Finances     TO 'event_manager';
GRANT SELECT, INSERT, UPDATE, DELETE ON event_management.Guests       TO 'event_manager';

-- Đăng ký: tạo mới + cập nhật, không được xóa (bảo toàn lịch sử)
GRANT SELECT, INSERT, UPDATE ON event_management.Registrations TO 'event_manager';

-- Toàn quyền xem Views và gọi Functions
GRANT SELECT ON event_management.v_upcoming_events            TO 'event_manager';
GRANT SELECT ON event_management.v_event_attendance_summary   TO 'event_manager';
GRANT SELECT ON event_management.v_finance_balance            TO 'event_manager';
GRANT SELECT ON event_management.v_guest_activity             TO 'event_manager';
GRANT SELECT ON event_management.v_venue_schedule             TO 'event_manager';
GRANT SELECT ON event_management.v_safe_guests                TO 'event_manager';
GRANT SELECT ON event_management.v_safe_registrations         TO 'event_manager';

-- Gọi Stored Procedures và Functions
GRANT EXECUTE ON PROCEDURE event_management.sp_check_in_guest        TO 'event_manager';
GRANT EXECUTE ON PROCEDURE event_management.sp_add_finance_record    TO 'event_manager';
GRANT EXECUTE ON PROCEDURE event_management.sp_register_guest_safe   TO 'event_manager';
GRANT EXECUTE ON PROCEDURE event_management.sp_mark_event_completed  TO 'event_manager';
GRANT EXECUTE ON PROCEDURE event_management.sp_get_event_report      TO 'event_manager';
GRANT EXECUTE ON FUNCTION  event_management.fn_participation_rate    TO 'event_manager';
GRANT EXECUTE ON FUNCTION  event_management.fn_event_balance         TO 'event_manager';
GRANT EXECUTE ON FUNCTION  event_management.fn_count_registered      TO 'event_manager';
GRANT EXECUTE ON FUNCTION  event_management.fn_slots_remaining       TO 'event_manager';


-- ────────────────────────────────────────────────────────────
-- ROLE 2: checkin_staff (Nhân viên check-in tại cổng sự kiện)
-- Chỉ xem danh sách và cập nhật trạng thái check-in
-- KHÔNG thấy Email, SĐT, Địa chỉ của khách (GDPR-like)
-- ────────────────────────────────────────────────────────────
CREATE ROLE 'checkin_staff';

-- Chỉ xem qua Views an toàn (không trực tiếp vào bảng Guests)
GRANT SELECT ON event_management.v_upcoming_events          TO 'checkin_staff';
GRANT SELECT ON event_management.v_event_attendance_summary TO 'checkin_staff';
GRANT SELECT ON event_management.v_safe_guests              TO 'checkin_staff';
GRANT SELECT ON event_management.v_safe_registrations       TO 'checkin_staff';

-- Chỉ cập nhật đúng 2 cột liên quan check-in (Column-level Grant)
GRANT UPDATE (attendance_status, checkin_time)
    ON event_management.Registrations TO 'checkin_staff';

-- Chỉ gọi procedure check-in (không được đăng ký hay xóa)
GRANT EXECUTE ON PROCEDURE event_management.sp_check_in_guest TO 'checkin_staff';


-- ────────────────────────────────────────────────────────────
-- ROLE 3: finance_officer (Nhân viên tài chính)
-- Quản lý thu-chi, xem báo cáo tài chính
-- KHÔNG thấy thông tin cá nhân khách mời
-- ────────────────────────────────────────────────────────────
CREATE ROLE 'finance_officer';

-- Xem báo cáo tài chính và sự kiện
GRANT SELECT ON event_management.v_finance_balance          TO 'finance_officer';
GRANT SELECT ON event_management.v_event_attendance_summary TO 'finance_officer';
GRANT SELECT ON event_management.v_upcoming_events          TO 'finance_officer';
GRANT SELECT ON event_management.Events                     TO 'finance_officer';

-- Quản lý thu chi
GRANT SELECT, INSERT, UPDATE ON event_management.Finances TO 'finance_officer';

-- Gọi procedure và function tài chính
GRANT EXECUTE ON PROCEDURE event_management.sp_add_finance_record TO 'finance_officer';
GRANT EXECUTE ON PROCEDURE event_management.sp_get_event_report   TO 'finance_officer';
GRANT EXECUTE ON FUNCTION  event_management.fn_event_balance      TO 'finance_officer';


-- ────────────────────────────────────────────────────────────
-- ROLE 4: readonly_viewer (Khách / Xem báo cáo công khai)
-- Chỉ đọc Views công khai, không có quyền ghi bất kỳ đâu
-- ────────────────────────────────────────────────────────────
CREATE ROLE 'readonly_viewer';

GRANT SELECT ON event_management.v_upcoming_events          TO 'readonly_viewer';
GRANT SELECT ON event_management.v_event_attendance_summary TO 'readonly_viewer';
GRANT SELECT ON event_management.v_venue_schedule           TO 'readonly_viewer';


-- ============================================================
-- PHẦN 2: TẠO USER VÀ GÁN ROLE
-- ============================================================

-- User 1: coordinator — Event Manager (toàn quyền nghiệp vụ)
CREATE USER 'coordinator'@'localhost'
    IDENTIFIED BY 'Coord@2025!'
    PASSWORD EXPIRE INTERVAL 90 DAY    -- Hết hạn mật khẩu sau 90 ngày
    FAILED_LOGIN_ATTEMPTS 5            -- Khóa sau 5 lần sai mật khẩu
    PASSWORD_LOCK_TIME 1;              -- Khóa 1 ngày
GRANT 'event_manager' TO 'coordinator'@'localhost';

-- User 2: checkin_staff_user — Nhân viên check-in
CREATE USER 'checkin_staff_user'@'localhost'
    IDENTIFIED BY 'Staff@2025!'
    PASSWORD EXPIRE INTERVAL 90 DAY
    FAILED_LOGIN_ATTEMPTS 5
    PASSWORD_LOCK_TIME 1;
GRANT 'checkin_staff' TO 'checkin_staff_user'@'localhost';

-- User 3: finance_user — Nhân viên tài chính
CREATE USER 'finance_user'@'localhost'
    IDENTIFIED BY 'Finance@2025!'
    PASSWORD EXPIRE INTERVAL 90 DAY
    FAILED_LOGIN_ATTEMPTS 5
    PASSWORD_LOCK_TIME 1;
GRANT 'finance_officer' TO 'finance_user'@'localhost';

-- User 4: readonly_user — Xem báo cáo công khai
CREATE USER 'readonly_user'@'localhost'
    IDENTIFIED BY 'Read@2025!'
    PASSWORD EXPIRE INTERVAL 180 DAY
    FAILED_LOGIN_ATTEMPTS 3
    PASSWORD_LOCK_TIME 2;
GRANT 'readonly_viewer' TO 'readonly_user'@'localhost';

-- Kích hoạt role mặc định ngay khi đăng nhập
SET DEFAULT ROLE ALL TO
    'coordinator'@'localhost',
    'checkin_staff_user'@'localhost',
    'finance_user'@'localhost',
    'readonly_user'@'localhost';

FLUSH PRIVILEGES;

-- Kiểm tra users và roles
SELECT user, host, account_locked, password_expired
FROM mysql.user
WHERE user IN ('coordinator','checkin_staff_user','finance_user','readonly_user');


-- ============================================================
-- PHẦN 3: BẢO MẬT LỚP DỮ LIỆU — VIEWS AN TOÀN
-- Column-level Security: ẩn Email, Phone, Address
-- ============================================================

-- View an toàn 1: Danh sách khách — KHÔNG có thông tin liên hệ
-- Dùng cho checkin_staff: chỉ thấy tên, không thấy email/SĐT
CREATE OR REPLACE VIEW v_safe_guests AS
SELECT
    guest_id,
    guest_name,
    -- Ẩn email: chỉ hiện 3 ký tự đầu + *** + domain
    CONCAT(
        LEFT(email, 3), '***@',
        SUBSTRING_INDEX(email, '@', -1)
    )                                    AS email_masked,
    -- Ẩn SĐT: chỉ hiện 3 số cuối
    CONCAT('*******', RIGHT(phone_number, 3)) AS phone_masked,
    '*** PROTECTED ***'                  AS address
FROM Guests;

-- View an toàn 2: Danh sách đăng ký — không hiện thông tin nhạy cảm
-- Dùng cho checkin_staff khi scan danh sách tại cổng
CREATE OR REPLACE VIEW v_safe_registrations AS
SELECT
    r.registration_id    AS reg_id,
    e.event_name,
    e.start_time,
    g.guest_id,
    g.guest_name,
    -- Chỉ mask email nhẹ để staff có thể xác minh nếu cần
    CONCAT(LEFT(g.email, 2), '***', SUBSTRING_INDEX(g.email, '@', -1)) AS email_hint,
    r.registration_date,
    r.attendance_status,
    r.checkin_time
FROM Registrations r
JOIN Events e ON r.event_id = e.event_id
JOIN Guests g ON r.guest_id = g.guest_id;

-- View tài chính an toàn: ẩn tên người tạo (chỉ hiện department)
CREATE OR REPLACE VIEW v_safe_finance AS
SELECT
    f.finance_id,
    e.event_name,
    f.type,
    f.amount,
    f.description,
    f.transaction_date,
    o.department        AS created_by_dept
FROM Finances f
JOIN Events     e ON f.event_id     = e.event_id
JOIN Organizers o ON e.organizer_id = o.organizer_id;

-- Kiểm tra views bảo mật (ĐÃ SỬA LỖI: alias "rows" đặt trong backtick)
SELECT 'v_safe_guests'        AS view_name, COUNT(*) AS `rows` FROM v_safe_guests        UNION ALL
SELECT 'v_safe_registrations' AS view_name, COUNT(*) AS `rows` FROM v_safe_registrations UNION ALL
SELECT 'v_safe_finance'       AS view_name, COUNT(*) AS `rows` FROM v_safe_finance;

-- Demo: So sánh dữ liệu gốc vs dữ liệu đã mask
SELECT guest_id, guest_name, email, phone_number  FROM Guests         LIMIT 3;  -- Raw (chỉ root mới thấy)
SELECT guest_id, guest_name, email_masked, phone_masked FROM v_safe_guests LIMIT 3;  -- Masked (staff thấy)


-- ============================================================
-- PHẦN 4: KIỂM TRA RBAC — Mô phỏng từng vai trò
-- ============================================================

-- Kiểm tra quyền của từng user
SHOW GRANTS FOR 'coordinator'@'localhost';
SHOW GRANTS FOR 'checkin_staff_user'@'localhost';
SHOW GRANTS FOR 'finance_user'@'localhost';
SHOW GRANTS FOR 'readonly_user'@'localhost';

-- Bảng tổng hợp quyền hạn từng role
SELECT
    'event_manager'    AS role_name,
    'Events, Venues, Organizers, Guests, Finances (CRUD), Registrations (no DELETE)' AS tables_access,
    'Tất cả Views + Procedures + Functions'   AS additional,
    'DROP, ALTER, CREATE'                      AS denied
UNION ALL
SELECT
    'checkin_staff',
    'Registrations.attendance_status + checkin_time (UPDATE only)',
    'v_safe_guests, v_safe_registrations (SELECT)',
    'Trực tiếp vào bảng Guests, Email, Phone, Address'
UNION ALL
SELECT
    'finance_officer',
    'Finances (SELECT/INSERT/UPDATE), Events (SELECT)',
    'v_finance_balance, sp_add_finance_record, fn_event_balance',
    'Guests, Registrations, DROP/DELETE'
UNION ALL
SELECT
    'readonly_viewer',
    'KHÔNG có quyền ghi bất kỳ đâu',
    'v_upcoming_events, v_event_attendance_summary, v_venue_schedule',
    'Tất cả INSERT/UPDATE/DELETE';


-- ============================================================
-- PHẦN 5: STORED PROCEDURE BACKUP (Backup trong MySQL)
-- ============================================================

DROP PROCEDURE IF EXISTS sp_backup_log;

DELIMITER $$

-- Procedure ghi log backup (metadata)
-- mysqldump thực tế chạy từ command line / Python subprocess
CREATE PROCEDURE sp_backup_log(
    IN  p_backup_file    VARCHAR(300),
    IN  p_backup_type    ENUM('Full','Schema','Data'),
    IN  p_status         ENUM('Success','Failed'),
    IN  p_notes          VARCHAR(500)
)
BEGIN
    -- Tạo bảng log nếu chưa có
    CREATE TABLE IF NOT EXISTS backup_log (
        log_id       INT          NOT NULL AUTO_INCREMENT PRIMARY KEY,
        backup_time  DATETIME     NOT NULL DEFAULT NOW(),
        backup_file  VARCHAR(300) NOT NULL,
        backup_type  ENUM('Full','Schema','Data') NOT NULL,
        status       ENUM('Success','Failed')      NOT NULL,
        file_size_kb INT          NULL,
        notes        VARCHAR(500) NULL
    );

    INSERT INTO backup_log (backup_file, backup_type, status, notes)
    VALUES (p_backup_file, p_backup_type, p_status, p_notes);

    SELECT CONCAT(
        p_status, ': Đã ghi log backup. File: ', p_backup_file,
        ' | Thời gian: ', DATE_FORMAT(NOW(), '%d/%m/%Y %H:%i:%s')
    ) AS result;
END$$

DELIMITER ;

-- Demo ghi log backup
CALL sp_backup_log(
    'D:/Backup/event_management_20250615_0200.sql',
    'Full', 'Success',
    'Backup tự động lúc 2:00 AM bằng Task Scheduler'
);

CALL sp_backup_log(
    'D:/Backup/event_management_schema_20250615.sql',
    'Schema', 'Success',
    'Backup schema trước khi nâng cấp hệ thống'
);


-- ============================================================
-- PHẦN 6: MYSQL EVENT SCHEDULER — Backup tự động trong DB
-- Lưu ý: mysqldump thực tế phải chạy từ ngoài MySQL
--        Event này dùng để ghi log + trigger thông báo
-- ============================================================

-- Bật Event Scheduler
SET GLOBAL event_scheduler = ON;

DROP EVENT IF EXISTS evt_daily_backup_log;

DELIMITER $$

CREATE EVENT evt_daily_backup_log
ON SCHEDULE EVERY 1 DAY
STARTS CONCAT(CURDATE() + INTERVAL 1 DAY, ' 02:00:00')
ON COMPLETION PRESERVE
ENABLE
COMMENT 'Ghi log nhắc nhở backup hàng ngày lúc 2:00 AM'
DO
BEGIN
    CALL sp_backup_log(
        CONCAT('auto_backup_', DATE_FORMAT(NOW(), '%Y%m%d'), '.sql'),
        'Full',
        'Success',
        'Scheduled daily backup reminder'
    );
END$$

DELIMITER ;

-- Kiểm tra events
SHOW EVENTS FROM event_management;


-- ============================================================
-- PHẦN 7: OPTIMIZE & PERFORMANCE
-- ============================================================

-- Phân tích và tối ưu các bảng lớn
ANALYZE TABLE Events;
ANALYZE TABLE Guests;
ANALYZE TABLE Registrations;
ANALYZE TABLE Finances;

-- Kiểm tra trạng thái bảng
CHECK TABLE Events, Guests, Registrations, Finances, Venues;

-- Xem kích thước từng bảng trong database
SELECT
    table_name                                  AS 'Bảng',
    ROUND(data_length / 1024, 2)               AS 'Data (KB)',
    ROUND(index_length / 1024, 2)              AS 'Index (KB)',
    ROUND((data_length + index_length) / 1024, 2) AS 'Tổng (KB)',
    table_rows                                  AS 'Số dòng (ước tính)'
FROM information_schema.tables
WHERE table_schema = 'event_management'
  AND table_type = 'BASE TABLE'
ORDER BY (data_length + index_length) DESC;

-- Xem slow queries (nếu bật slow query log)
-- SHOW VARIABLES LIKE 'slow_query_log%';
-- SHOW VARIABLES LIKE 'long_query_time';


-- ============================================================
-- PHẦN 8: KIỂM THỬ BẢO MẬT CUỐI CÙNG
-- ============================================================

-- Test 1: Xem thông tin khách qua View an toàn (staff nhìn thấy)
SELECT guest_id, guest_name, email_masked, phone_masked
FROM v_safe_guests LIMIT 5;

-- Test 2: Tỉ lệ tham dự qua Function (công khai)
SELECT e.event_name, fn_participation_rate(e.event_id) AS ty_le_pct
FROM Events e ORDER BY e.event_id;

-- Test 3: Số dư tài chính tất cả sự kiện
SELECT e.event_name, fn_event_balance(e.event_id) AS so_du_vnd
FROM Events e ORDER BY e.event_id;

-- Test 4: Kiểm tra backup log
SELECT * FROM backup_log ORDER BY backup_time DESC;

-- ============================================================
-- END OF SCRIPT — GIAI ĐOẠN 4
-- ============================================================