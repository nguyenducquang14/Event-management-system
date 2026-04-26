@echo off
:: ============================================================
::  BACKUP SCRIPT — Event Management System
::  Chạy bằng: backup.bat
::  Lên lịch: Windows Task Scheduler lúc 2:00 AM hàng ngày
::  Đặt file này trong thư mục gốc project
:: ============================================================

:: Cấu hình — sửa theo máy của bạn
set DB_USER=root
set DB_PASS=yourpassword
set DB_NAME=event_management
set MYSQL_BIN=C:\Program Files\MySQL\MySQL Server 8.0\bin
set BACKUP_DIR=D:\Backup\EventManagement

:: Tạo thư mục backup nếu chưa có
if not exist "%BACKUP_DIR%" mkdir "%BACKUP_DIR%"

:: Tên file theo ngày giờ: event_management_20250615_020000.sql
set TIMESTAMP=%date:~-4,4%%date:~-10,2%%date:~-7,2%_%time:~0,2%%time:~3,2%%time:~6,2%
set TIMESTAMP=%TIMESTAMP: =0%
set BACKUP_FILE=%BACKUP_DIR%\event_management_%TIMESTAMP%.sql

echo ============================================================
echo  Bắt đầu backup: %date% %time%
echo  File: %BACKUP_FILE%
echo ============================================================

:: Backup toàn bộ database (schema + data)
"%MYSQL_BIN%\mysqldump.exe" ^
    -u %DB_USER% ^
    -p%DB_PASS% ^
    --databases %DB_NAME% ^
    --routines ^
    --triggers ^
    --events ^
    --single-transaction ^
    --quick ^
    > "%BACKUP_FILE%"

:: Kiểm tra kết quả
if %ERRORLEVEL% == 0 (
    echo [THÀNH CÔNG] Backup hoàn tất: %BACKUP_FILE%
    echo %date% %time% | SUCCESS | %BACKUP_FILE% >> "%BACKUP_DIR%\backup_log.txt"
) else (
    echo [LỖI] Backup thất bại! Kiểm tra kết nối MySQL.
    echo %date% %time% | FAILED  | %BACKUP_FILE% >> "%BACKUP_DIR%\backup_log.txt"
)

:: Xóa backup cũ hơn 30 ngày (tiết kiệm dung lượng)
forfiles /p "%BACKUP_DIR%" /s /m *.sql /d -30 /c "cmd /c del @path" 2>nul

echo Hoàn tất. Xem log tại: %BACKUP_DIR%\backup_log.txt
