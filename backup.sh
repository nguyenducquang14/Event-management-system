#!/bin/bash
# ============================================================
#  BACKUP SCRIPT — Event Management System (Linux/macOS)
#  Cài vào crontab: 0 2 * * * /path/to/backup.sh
#  Chạy: bash backup.sh
# ============================================================

DB_USER="root"
DB_PASS="yourpassword"
DB_NAME="event_management"
BACKUP_DIR="$HOME/Backup/EventManagement"
LOG_FILE="$BACKUP_DIR/backup_log.txt"

# Tạo thư mục backup
mkdir -p "$BACKUP_DIR"

# Timestamp: event_management_20250615_020000.sql
TIMESTAMP=$(date '+%Y%m%d_%H%M%S')
BACKUP_FILE="$BACKUP_DIR/event_management_$TIMESTAMP.sql"

echo "============================================"
echo " Bắt đầu backup: $(date)"
echo " File: $BACKUP_FILE"
echo "============================================"

# Backup toàn bộ database
mysqldump \
    -u "$DB_USER" \
    -p"$DB_PASS" \
    --databases "$DB_NAME" \
    --routines \
    --triggers \
    --events \
    --single-transaction \
    --quick \
    > "$BACKUP_FILE"

# Kiểm tra kết quả
if [ $? -eq 0 ]; then
    echo "[THÀNH CÔNG] Backup: $BACKUP_FILE"
    echo "$(date) | SUCCESS | $BACKUP_FILE" >> "$LOG_FILE"
    # Nén file backup
    gzip "$BACKUP_FILE"
    echo "Đã nén thành: $BACKUP_FILE.gz"
else
    echo "[LỖI] Backup thất bại!"
    echo "$(date) | FAILED  | $BACKUP_FILE" >> "$LOG_FILE"
    exit 1
fi

# Xóa backup cũ hơn 30 ngày
find "$BACKUP_DIR" -name "*.sql.gz" -mtime +30 -delete
echo "Đã xóa backup cũ hơn 30 ngày."

# Ghi log vào MySQL (nếu muốn)
# mysql -u "$DB_USER" -p"$DB_PASS" "$DB_NAME" \
#   -e "CALL sp_backup_log('$BACKUP_FILE.gz','Full','Success','Cron job 2AM');"

echo "Hoàn tất. Xem log: $LOG_FILE"
