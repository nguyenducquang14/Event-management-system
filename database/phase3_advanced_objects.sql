-- ============================================================
--  GIAI ĐOẠN 3: ĐỐI TƯỢNG CƠ SỞ DỮ LIỆU NÂNG CAO
--  Event Management System — NEU DATCOM Lab | Project 14
--  Chạy sau Phase1_fixed.sql
--  ĐÃ SỬA: Stored procedure tránh INSERT khi trạng thái không hợp lệ
-- ============================================================

USE event_management;

-- ============================================================
-- HELPER: Xóa index an toàn (MySQL không hỗ trợ DROP INDEX IF EXISTS)
-- ============================================================

DROP PROCEDURE IF EXISTS sp_drop_index_safe;

DELIMITER $$
CREATE PROCEDURE sp_drop_index_safe(IN tbl VARCHAR(64), IN idx VARCHAR(64))
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.statistics
        WHERE table_schema = DATABASE()
          AND table_name   = tbl
          AND index_name   = idx
    ) THEN
        SET @sql = CONCAT('DROP INDEX `', idx, '` ON `', tbl, '`');
        PREPARE stmt FROM @sql;
        EXECUTE stmt;
        DEALLOCATE PREPARE stmt;
    END IF;
END$$
DELIMITER ;

-- Gọi procedure để xóa index cũ
CALL sp_drop_index_safe('Events',        'idx_events_start_time');
CALL sp_drop_index_safe('Events',        'idx_events_status');
CALL sp_drop_index_safe('Events',        'idx_events_organizer');
CALL sp_drop_index_safe('Guests',        'idx_guests_email');
CALL sp_drop_index_safe('Guests',        'idx_guests_name');
CALL sp_drop_index_safe('Registrations', 'idx_registrations_event_guest');
CALL sp_drop_index_safe('Registrations', 'idx_registrations_attendance');
CALL sp_drop_index_safe('Finances',      'idx_finances_event_type');
CALL sp_drop_index_safe('Finances',      'idx_finances_date');
CALL sp_drop_index_safe('Venues',        'idx_venues_status');

DROP PROCEDURE IF EXISTS sp_drop_index_safe;

-- ============================================================
-- PHẦN 1: INDEXES
-- ============================================================

CREATE INDEX idx_events_start_time         ON Events(start_time);
CREATE INDEX idx_events_status             ON Events(status);
CREATE INDEX idx_events_organizer          ON Events(organizer_id);
CREATE INDEX idx_guests_email              ON Guests(email);
CREATE INDEX idx_guests_name               ON Guests(guest_name);
CREATE INDEX idx_registrations_event_guest ON Registrations(event_id, guest_id);
CREATE INDEX idx_registrations_attendance  ON Registrations(attendance_status);
CREATE INDEX idx_finances_event_type       ON Finances(event_id, type);
CREATE INDEX idx_finances_date             ON Finances(transaction_date);
CREATE INDEX idx_venues_status             ON Venues(availability_status);

-- ============================================================
-- PHẦN 2: VIEWS
-- ============================================================

DROP VIEW IF EXISTS v_upcoming_events;
DROP VIEW IF EXISTS v_event_attendance_summary;
DROP VIEW IF EXISTS v_finance_balance;
DROP VIEW IF EXISTS v_guest_activity;
DROP VIEW IF EXISTS v_venue_schedule;
DROP VIEW IF EXISTS v_safe_guests;
DROP VIEW IF EXISTS v_safe_registrations;

CREATE VIEW v_upcoming_events AS
SELECT
    e.event_id,
    e.event_name,
    e.start_time,
    e.end_time,
    TIMESTAMPDIFF(MINUTE, e.start_time, e.end_time) AS duration_minutes,
    v.venue_name,
    v.capacity                                        AS venue_capacity,
    e.max_capacity,
    o.organizer_name,
    e.status,
    CASE
        WHEN e.max_capacity IS NULL THEN NULL
        ELSE e.max_capacity - (
            SELECT COUNT(*) FROM Registrations r WHERE r.event_id = e.event_id
        )
    END AS slots_remaining
FROM Events e
JOIN Venues     v ON e.venue_id     = v.venue_id
JOIN Organizers o ON e.organizer_id = o.organizer_id
WHERE e.start_time >= NOW()
  AND e.status IN ('Draft', 'Scheduled')
ORDER BY e.start_time;

CREATE VIEW v_event_attendance_summary AS
SELECT
    e.event_id,
    e.event_name,
    DATE_FORMAT(e.start_time, '%d/%m/%Y %H:%i') AS event_date,
    e.status,
    o.organizer_name,
    COUNT(r.registration_id)                          AS total_registered,
    COALESCE(SUM(r.attendance_status = 'Attended'),  0) AS total_attended,
    COALESCE(SUM(r.attendance_status = 'No-show'),   0) AS total_noshow,
    COALESCE(SUM(r.attendance_status = 'Registered'),0) AS total_pending,
    ROUND(
        COALESCE(SUM(r.attendance_status = 'Attended'), 0)
        / NULLIF(COUNT(r.registration_id), 0) * 100,
    2) AS participation_rate_pct
FROM Events e
JOIN Organizers o       ON e.organizer_id = o.organizer_id
LEFT JOIN Registrations r ON e.event_id   = r.event_id
GROUP BY e.event_id, e.event_name, e.start_time, e.status, o.organizer_name;

CREATE VIEW v_finance_balance AS
SELECT
    e.event_id,
    e.event_name,
    e.status,
    COALESCE(SUM(CASE WHEN f.type = 'Income'  THEN f.amount END), 0) AS total_income,
    COALESCE(SUM(CASE WHEN f.type = 'Expense' THEN f.amount END), 0) AS total_expense,
    COALESCE(SUM(CASE WHEN f.type = 'Income'  THEN f.amount END), 0)
    - COALESCE(SUM(CASE WHEN f.type = 'Expense' THEN f.amount END), 0) AS net_balance,
    COUNT(f.finance_id) AS total_transactions
FROM Events e
LEFT JOIN Finances f ON e.event_id = f.event_id
GROUP BY e.event_id, e.event_name, e.status;

CREATE VIEW v_guest_activity AS
SELECT
    g.guest_id,
    g.guest_name,
    g.email,
    g.phone_number,
    COUNT(r.registration_id)                              AS total_registrations,
    COALESCE(SUM(r.attendance_status = 'Attended'),  0)  AS total_attended,
    COALESCE(SUM(r.attendance_status = 'No-show'),   0)  AS total_noshow,
    ROUND(
        COALESCE(SUM(r.attendance_status = 'Attended'), 0)
        / NULLIF(COUNT(r.registration_id), 0) * 100,
    1) AS personal_rate_pct,
    MAX(r.registration_date) AS last_registration
FROM Guests g
LEFT JOIN Registrations r ON g.guest_id = r.guest_id
GROUP BY g.guest_id, g.guest_name, g.email, g.phone_number;

CREATE VIEW v_venue_schedule AS
SELECT
    v.venue_id,
    v.venue_name,
    v.capacity,
    v.availability_status,
    COUNT(e.event_id)                    AS total_events_hosted,
    COALESCE(SUM(e.status='Completed'),0) AS completed_events,
    COALESCE(SUM(e.status='Scheduled'),0) AS upcoming_events,
    MAX(e.start_time)                    AS last_event_date,
    ROUND(AVG(
        (SELECT COUNT(*) FROM Registrations r WHERE r.event_id = e.event_id)
        / NULLIF(v.capacity, 0) * 100
    ), 1) AS avg_fill_rate_pct
FROM Venues v
LEFT JOIN Events e ON v.venue_id = e.venue_id
GROUP BY v.venue_id, v.venue_name, v.capacity, v.availability_status;

CREATE VIEW v_safe_guests AS
SELECT
    guest_id,
    guest_name,
    CONCAT(LEFT(email, 3), '***@', SUBSTRING_INDEX(email, '@', -1)) AS email_masked,
    CONCAT('*******', RIGHT(phone_number, 3))                        AS phone_masked,
    '*** PROTECTED ***'                                               AS address
FROM Guests;

CREATE VIEW v_safe_registrations AS
SELECT
    r.registration_id,
    r.event_id,
    e.event_name,
    e.start_time,
    g.guest_id,
    g.guest_name,
    CONCAT(LEFT(g.email, 2), '***', SUBSTRING_INDEX(g.email, '@', -1)) AS email_hint,
    r.registration_date,
    r.attendance_status,
    r.checkin_time
FROM Registrations r
JOIN Events e ON r.event_id = e.event_id
JOIN Guests g ON r.guest_id = g.guest_id;

-- ============================================================
-- PHẦN 3: USER DEFINED FUNCTIONS
-- ============================================================

DROP FUNCTION IF EXISTS fn_participation_rate;
DROP FUNCTION IF EXISTS fn_event_balance;
DROP FUNCTION IF EXISTS fn_count_registered;
DROP FUNCTION IF EXISTS fn_slots_remaining;

DELIMITER $$

CREATE FUNCTION fn_participation_rate(p_event_id INT)
RETURNS DECIMAL(5,2) READS SQL DATA DETERMINISTIC
BEGIN
    DECLARE v_total    INT DEFAULT 0;
    DECLARE v_attended INT DEFAULT 0;
    SELECT COUNT(*) INTO v_total    FROM Registrations WHERE event_id = p_event_id;
    SELECT COALESCE(SUM(attendance_status='Attended'),0)
           INTO v_attended FROM Registrations WHERE event_id = p_event_id;
    IF v_total = 0 THEN RETURN 0.00; END IF;
    RETURN ROUND(v_attended / v_total * 100, 2);
END$$

CREATE FUNCTION fn_event_balance(p_event_id INT)
RETURNS DECIMAL(15,2) READS SQL DATA DETERMINISTIC
BEGIN
    DECLARE v_income  DECIMAL(15,2) DEFAULT 0.00;
    DECLARE v_expense DECIMAL(15,2) DEFAULT 0.00;
    SELECT COALESCE(SUM(amount),0.00) INTO v_income
    FROM Finances WHERE event_id = p_event_id AND type = 'Income';
    SELECT COALESCE(SUM(amount),0.00) INTO v_expense
    FROM Finances WHERE event_id = p_event_id AND type = 'Expense';
    RETURN v_income - v_expense;
END$$

CREATE FUNCTION fn_count_registered(p_event_id INT)
RETURNS INT READS SQL DATA DETERMINISTIC
BEGIN
    DECLARE v_count INT DEFAULT 0;
    SELECT COUNT(*) INTO v_count FROM Registrations WHERE event_id = p_event_id;
    RETURN v_count;
END$$

CREATE FUNCTION fn_slots_remaining(p_event_id INT)
RETURNS INT READS SQL DATA DETERMINISTIC
BEGIN
    DECLARE v_max_cap    INT DEFAULT NULL;
    DECLARE v_registered INT DEFAULT 0;
    SELECT max_capacity INTO v_max_cap FROM Events WHERE event_id = p_event_id;
    IF v_max_cap IS NULL THEN RETURN NULL; END IF;
    SELECT COUNT(*) INTO v_registered FROM Registrations WHERE event_id = p_event_id;
    RETURN v_max_cap - v_registered;
END$$

DELIMITER ;

-- ============================================================
-- PHẦN 4: STORED PROCEDURES (đã sửa lỗi)
-- ============================================================

DROP PROCEDURE IF EXISTS sp_check_in_guest;
DROP PROCEDURE IF EXISTS sp_add_finance_record;
DROP PROCEDURE IF EXISTS sp_register_guest_safe;
DROP PROCEDURE IF EXISTS sp_mark_event_completed;
DROP PROCEDURE IF EXISTS sp_get_event_report;

DELIMITER $$

CREATE PROCEDURE sp_check_in_guest(
    IN  p_event_id INT,
    IN  p_guest_id INT,
    OUT p_result   VARCHAR(255)
)
BEGIN
    DECLARE v_status VARCHAR(20) DEFAULT NULL;
    SELECT attendance_status INTO v_status
    FROM Registrations WHERE event_id = p_event_id AND guest_id = p_guest_id;

    IF v_status IS NULL THEN
        SET p_result = 'ERROR: Khách chưa đăng ký sự kiện này.';
    ELSEIF v_status = 'Attended' THEN
        SET p_result = 'ERROR: Khách đã check-in trước đó.';
    ELSE
        UPDATE Registrations
        SET attendance_status = 'Attended', checkin_time = NOW()
        WHERE event_id = p_event_id AND guest_id = p_guest_id;
        SET p_result = CONCAT('SUCCESS: Check-in thành công lúc ',
                              DATE_FORMAT(NOW(), '%H:%i:%s %d/%m/%Y'));
    END IF;
END$$

CREATE PROCEDURE sp_add_finance_record(
    IN  p_event_id    INT,
    IN  p_type        ENUM('Income','Expense'),
    IN  p_amount      DECIMAL(15,2),
    IN  p_description VARCHAR(200),
    OUT p_result      VARCHAR(255)
)
BEGIN
    DECLARE v_event_exists INT DEFAULT 0;
    SELECT COUNT(*) INTO v_event_exists FROM Events WHERE event_id = p_event_id;

    IF v_event_exists = 0 THEN
        SET p_result = 'ERROR: Sự kiện không tồn tại.';
    ELSEIF p_amount <= 0 THEN
        SET p_result = 'ERROR: Số tiền phải lớn hơn 0.';
    ELSE
        INSERT INTO Finances (event_id, type, amount, description, transaction_date)
        VALUES (p_event_id, p_type, p_amount, p_description, CURRENT_DATE);
        SET p_result = CONCAT('SUCCESS: Đã ghi ', p_type, ' ',
                              FORMAT(p_amount,0), ' VND. Số dư mới: ',
                              FORMAT(fn_event_balance(p_event_id),0), ' VND.');
    END IF;
END$$

-- PROCEDURE ĐÃ SỬA: dùng LEAVE để đảm bảo không INSERT khi trạng thái không hợp lệ
CREATE PROCEDURE sp_register_guest_safe(
    IN  p_event_id INT,
    IN  p_guest_id INT,
    OUT p_result   VARCHAR(255)
)
proc_label: BEGIN
    DECLARE v_already_reg  INT DEFAULT 0;
    DECLARE v_event_status VARCHAR(20);
    DECLARE v_slots        INT DEFAULT NULL;

    SELECT COUNT(*) INTO v_already_reg
    FROM Registrations WHERE event_id = p_event_id AND guest_id = p_guest_id;

    IF v_already_reg > 0 THEN
        SET p_result = 'ERROR: Khách đã đăng ký sự kiện này rồi.';
        LEAVE proc_label;
    END IF;

    SELECT status INTO v_event_status FROM Events WHERE event_id = p_event_id;

    IF v_event_status IN ('Completed','Cancelled') THEN
        SET p_result = 'ERROR: Sự kiện đã kết thúc hoặc bị hủy.';
        LEAVE proc_label;
    ELSEIF v_event_status = 'Full' THEN
        SET p_result = 'ERROR: Sự kiện đã hết chỗ.';
        LEAVE proc_label;
    END IF;

    SET v_slots = fn_slots_remaining(p_event_id);
    IF v_slots IS NOT NULL AND v_slots <= 0 THEN
        SET p_result = 'ERROR: Sự kiện đã hết chỗ (capacity đầy).';
        LEAVE proc_label;
    END IF;

    INSERT INTO Registrations (event_id, guest_id, registration_date, attendance_status)
    VALUES (p_event_id, p_guest_id, CURRENT_DATE, 'Registered');

    SET p_result = CONCAT('SUCCESS: Đăng ký thành công. ',
        CASE WHEN v_slots IS NULL THEN 'Không giới hạn chỗ.'
             ELSE CONCAT('Còn ', v_slots-1, ' chỗ trống.') END);
END proc_label$$

CREATE PROCEDURE sp_mark_event_completed(
    IN  p_event_id INT,
    OUT p_result   VARCHAR(255)
)
BEGIN
    DECLARE v_noshow_count INT DEFAULT 0;
    DECLARE v_event_name   VARCHAR(150);
    SELECT event_name INTO v_event_name FROM Events WHERE event_id = p_event_id;

    IF v_event_name IS NULL THEN
        SET p_result = 'ERROR: Sự kiện không tồn tại.';
    ELSE
        UPDATE Registrations SET attendance_status = 'No-show'
        WHERE event_id = p_event_id AND attendance_status = 'Registered';
        SET v_noshow_count = ROW_COUNT();
        UPDATE Events SET status = 'Completed' WHERE event_id = p_event_id;
        SET p_result = CONCAT('SUCCESS: Sự kiện "', v_event_name, '" đã hoàn thành. ',
                              v_noshow_count, ' khách No-show. Tỉ lệ: ',
                              fn_participation_rate(p_event_id), '%.');
    END IF;
END$$

CREATE PROCEDURE sp_get_event_report(IN p_from_date DATE, IN p_to_date DATE)
BEGIN
    SELECT e.event_id,
           e.event_name,
           DATE_FORMAT(e.start_time, '%d/%m/%Y %H:%i') AS start_time,
           e.status,
           v.venue_name,
           o.organizer_name,
           fn_count_registered(e.event_id)   AS total_registered,
           fn_participation_rate(e.event_id) AS participation_rate_pct,
           fn_event_balance(e.event_id)      AS net_balance_vnd
    FROM Events e
    JOIN Venues     v ON e.venue_id     = v.venue_id
    JOIN Organizers o ON e.organizer_id = o.organizer_id
    WHERE DATE(e.start_time) BETWEEN p_from_date AND p_to_date
    ORDER BY e.start_time;
END$$

DELIMITER ;

-- ============================================================
-- PHẦN 5: TRIGGERS (đã chuẩn hóa)
-- ============================================================

DROP TRIGGER IF EXISTS trg_check_capacity_before_register;
DROP TRIGGER IF EXISTS trg_auto_set_full_status;
DROP TRIGGER IF EXISTS trg_restore_scheduled_on_cancel;
DROP TRIGGER IF EXISTS trg_prevent_duplicate_registration;
DROP TRIGGER IF EXISTS trg_log_checkin_timestamp;

DELIMITER $$

CREATE TRIGGER trg_check_capacity_before_register
BEFORE INSERT ON Registrations
FOR EACH ROW
BEGIN
    DECLARE v_max_cap   INT DEFAULT NULL;
    DECLARE v_current   INT DEFAULT 0;
    DECLARE v_ev_status VARCHAR(20);

    SELECT max_capacity, status INTO v_max_cap, v_ev_status
    FROM Events WHERE event_id = NEW.event_id;

    IF v_ev_status IN ('Completed','Cancelled') THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'TRG_ERR: Không thể đăng ký sự kiện đã kết thúc/hủy.';
    END IF;

    IF v_max_cap IS NOT NULL THEN
        SELECT COUNT(*) INTO v_current FROM Registrations WHERE event_id = NEW.event_id;
        IF v_current >= v_max_cap THEN
            SIGNAL SQLSTATE '45000'
            SET MESSAGE_TEXT = 'TRG_ERR: Sự kiện đã đạt max_capacity. Đăng ký bị từ chối.';
        END IF;
    END IF;
END$$

CREATE TRIGGER trg_auto_set_full_status
AFTER INSERT ON Registrations
FOR EACH ROW
BEGIN
    DECLARE v_max_cap INT DEFAULT NULL;
    DECLARE v_current INT DEFAULT 0;
    SELECT max_capacity INTO v_max_cap FROM Events WHERE event_id = NEW.event_id;
    IF v_max_cap IS NOT NULL THEN
        SELECT COUNT(*) INTO v_current FROM Registrations WHERE event_id = NEW.event_id;
        IF v_current >= v_max_cap THEN
            UPDATE Events SET status = 'Full'
            WHERE event_id = NEW.event_id AND status IN ('Draft','Scheduled');
        END IF;
    END IF;
END$$

CREATE TRIGGER trg_restore_scheduled_on_cancel
AFTER DELETE ON Registrations
FOR EACH ROW
BEGIN
    DECLARE v_max_cap INT DEFAULT NULL;
    DECLARE v_current INT DEFAULT 0;
    SELECT max_capacity INTO v_max_cap FROM Events WHERE event_id = OLD.event_id;
    IF v_max_cap IS NOT NULL THEN
        SELECT COUNT(*) INTO v_current FROM Registrations WHERE event_id = OLD.event_id;
        IF v_current < v_max_cap THEN
            UPDATE Events SET status = 'Scheduled'
            WHERE event_id = OLD.event_id AND status = 'Full';
        END IF;
    END IF;
END$$

CREATE TRIGGER trg_prevent_duplicate_registration
BEFORE INSERT ON Registrations
FOR EACH ROW
BEGIN
    DECLARE v_exists INT DEFAULT 0;
    SELECT COUNT(*) INTO v_exists FROM Registrations
    WHERE event_id = NEW.event_id AND guest_id = NEW.guest_id;
    IF v_exists > 0 THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'TRG_ERR: Khách đã đăng ký sự kiện này. Không thể đăng ký lại.';
    END IF;
END$$

CREATE TRIGGER trg_log_checkin_timestamp
BEFORE UPDATE ON Registrations
FOR EACH ROW
BEGIN
    IF NEW.attendance_status = 'Attended'
       AND OLD.attendance_status != 'Attended'
       AND NEW.checkin_time IS NULL
    THEN
        SET NEW.checkin_time = NOW();
    END IF;
    IF NEW.attendance_status IN ('Registered','No-show')
       AND OLD.attendance_status = 'Attended'
    THEN
        SET NEW.checkin_time = NULL;
    END IF;
END$$

DELIMITER ;

-- ============================================================
-- PHẦN 6: KIỂM THỬ & DEMO
-- ============================================================

-- (Có thể chạy từng phần để kiểm tra)
-- Demo functions
SELECT event_id, event_name,
       fn_participation_rate(event_id) AS ty_le_tham_du_pct,
       fn_event_balance(event_id)      AS so_du_vnd,
       fn_count_registered(event_id)  AS da_dang_ky,
       fn_slots_remaining(event_id)   AS cho_con_trong
FROM Events ORDER BY event_id;

-- Demo EXPLAIN
EXPLAIN SELECT * FROM Events WHERE start_time >= NOW() AND status = 'Scheduled';
EXPLAIN SELECT * FROM Guests WHERE email = 'an.nguyen@email.com';
EXPLAIN SELECT * FROM Registrations WHERE event_id = 1 AND guest_id = 1;

-- Demo Views
SELECT * FROM v_upcoming_events;
SELECT * FROM v_event_attendance_summary;
SELECT * FROM v_finance_balance;
SELECT * FROM v_guest_activity ORDER BY total_registrations DESC;
SELECT * FROM v_venue_schedule ORDER BY total_events_hosted DESC;

-- Demo Trigger capacity test
UPDATE Events SET max_capacity = 1 WHERE event_id = 2;
CALL sp_register_guest_safe(2, 1, @trig_1); SELECT @trig_1 AS 'Đăng ký 1 (ok)';
CALL sp_register_guest_safe(2, 2, @trig_2); SELECT @trig_2 AS 'Đăng ký 2 (hết chỗ)';

-- Demo Kết thúc sự kiện
CALL sp_mark_event_completed(4, @done); SELECT @done AS 'Kết thúc Event 4';

-- Demo Báo cáo kỳ
CALL sp_get_event_report('2025-01-01','2025-12-31');

-- ============================================================
-- END OF SCRIPT — GIAI ĐOẠN 3
-- ============================================================