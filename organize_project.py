import os
import shutil

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def move_file(src, dst):
    src_path = os.path.normpath(os.path.join(BASE_DIR, src))
    dst_path = os.path.normpath(os.path.join(BASE_DIR, dst))
    if os.path.exists(src_path):
        os.makedirs(os.path.dirname(dst_path), exist_ok=True)
        if os.path.exists(dst_path):
            os.remove(dst_path) # Ghi đè nếu đã tồn tại bản cũ
        shutil.move(src_path, dst_path)
        print(f"✅ Đã di chuyển: {src} -> {dst}")

def move_dir(src, dst):
    src_path = os.path.normpath(os.path.join(BASE_DIR, src))
    dst_path = os.path.normpath(os.path.join(BASE_DIR, dst))
    if os.path.exists(src_path) and src_path != dst_path:
        os.makedirs(dst_path, exist_ok=True)
        for item in os.listdir(src_path):
            s = os.path.join(src_path, item)
            d = os.path.join(dst_path, item)
            if os.path.isdir(s):
                move_dir(s, d) # Đệ quy gộp thư mục
            else:
                if os.path.exists(d):
                    os.remove(d)
                shutil.move(s, d)
        try:
            os.rmdir(src_path)
            print(f"✅ Đã gộp thư mục: {src} -> {dst}")
        except OSError:
            pass

def delete_file(target):
    target_path = os.path.normpath(os.path.join(BASE_DIR, target))
    if os.path.exists(target_path):
        os.remove(target_path)
        print(f"🗑️ Đã xóa tệp thừa: {target}")

def main():
    print("🚀 Bắt đầu sắp xếp và CHỮA LỖI cấu trúc dự án...")

    # 1. Tạo các thư mục gốc
    for d in ["app", "frontend_web", "frontend_cli", "database"]:
        os.makedirs(os.path.join(BASE_DIR, d), exist_ok=True)

    # 2. KHÔI PHỤC TẦNG APP (Khắc phục lỗi ModuleNotFoundError)
    print("\n📦 Phục hồi cấu trúc cốt lõi 'app/'...")
    move_file("backend/models.py", "app/models.py")
    move_file("backend/schemas.py", "app/database/schemas.py")
    move_file("backend/db_manager.py", "app/database/db_manager.py")
    move_file("backend/base.py", "app/database/base.py")
    move_file("backend/__init__.py", "app/database/__init__.py")
    move_dir("backend/repositories", "app/database/repositories")
    move_file("backend/config.py", "app/config.py")
    move_file("backend/auth_models.py", "app/database/auth_models.py")
    
    # Trả các tệp UI và CLI bị di chuyển sai về vị trí cũ
    move_dir("frontend_web/ui", "app/ui")
    move_file("frontend_cli/utils.py", "app/cli/utils.py")

    # 3. DỌN DẸP RÁC
    print("\n🧹 Dọn dẹp tệp thừa...")
    delete_file("frontend_web/streamlit_app_old.py")
    delete_file("frontend_web/pages/5_Su_Kien_Cong_Khai.py")
    delete_file("frontend_web/pages/6_Ve_Cua_Toi.py")
    delete_file("frontend_web/pages/7_Quan_Ly_Tai_Khoan.py")

    # Xóa thư mục backend nếu nó đã rỗng
    backend_path = os.path.join(BASE_DIR, "backend")
    if os.path.exists(backend_path) and not os.listdir(backend_path):
        os.rmdir(backend_path)
        print("🗑️ Đã xóa thư mục 'backend' (đã gộp chung vào 'app').")

    # 4. TỔ CHỨC FRONTEND WEB
    print("\n🌐 Sắp xếp lại Frontend Web...")
    move_file("Home.py", "frontend_web/Home.py")
    move_dir("pages", "frontend_web/pages")
    
    print("\n🔢 Cập nhật số thứ tự các trang Sidebar...")
    move_file("frontend_web/pages/8_Sự_Kiện_Công_Khai.py", "frontend_web/pages/7_Sự_Kiện_Công_Khai.py")
    move_file("frontend_web/pages/9_Vé_Của_Tôi.py", "frontend_web/pages/8_Vé_Của_Tôi.py")
    move_file("frontend_web/pages/11_Kết_Nối_&_Tương_Tác.py", "frontend_web/pages/9_Kết_Nối_&_Tương_Tác.py")

    print("\n🎉 Hoàn tất! Các file đã về đúng vị trí đồng bộ với mã nguồn.")
    print("💡 Hãy chạy: streamlit run frontend_web/Home.py để thưởng thức!")

if __name__ == "__main__":
    main()