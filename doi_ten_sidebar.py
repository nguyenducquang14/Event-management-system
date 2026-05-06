"""
Script tự động đổi tên các file trong thư mục pages sang Tiếng Việt có dấu.
"""
import os

# Đường dẫn tới thư mục pages
base_dir = os.path.join("frontend_web", "pages")

renames = {
    "1_events.py": "1_Quản_lý_Sự_kiện.py",
    "2_Dashboard_Ban_To_Chuc.py": "2_Dashboard_Ban_Tổ_Chức.py",
    "2_guests.py": "3_Khách_mời.py",
    "3_registrations.py": "4_Đăng_ký_và_Check_in.py",
    "4_finance.py": "5_Tài_chính.py",
    "5_reports.py": "6_Báo_cáo_Thống_kê.py",
    "7_Sự_Kiện_Công_Khai.py": "7_Cổng_Sự_Kiện.py",
    "8_Vé_Của_Tôi.py": "8_Quản_Lý_Đăng_Ký.py",
    "9_Kết_Nối_&_Tương_Tác.py": "9_Kết_Nối_Đối_Tác.py",
    "10_Quản_Lý_Tài_Khoản.py": "10_Hồ_Sơ_Doanh_Nghiệp.py",
    "11_Đánh_Giá_&_Tài_Liệu.py": "11_Báo_Cáo_&_Tài_Liệu.py"
}

def rename_files():
    print("🚀 Bắt đầu đổi tên các file Sidebar sang Tiếng Việt có dấu...")
    for old_name, new_name in renames.items():
        old_path = os.path.join(base_dir, old_name)
        new_path = os.path.join(base_dir, new_name)
        
        if os.path.exists(old_path):
            os.rename(old_path, new_path)
            print(f"✅ Đã đổi tên: {old_name} -> {new_name}")
            
if __name__ == "__main__":
    rename_files()
    print("🎉 Hoàn tất! Vui lòng khởi động lại (Restart) server Streamlit để cập nhật menu.")