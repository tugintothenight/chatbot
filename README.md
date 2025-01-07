# Django Project README

## **Hướng dẫn chạy dự án**
1. **Khởi động server**:
   - Lệnh chạy server:
     ```bash
     python manage.py runserver
     ```
     - Nếu muốn chỉ định cổng khác (ví dụ: 8080), dùng lệnh:
       ```bash
       python manage.py runserver 8080
       ```
     - Nếu không chỉ định cổng, cổng mặc định là `8000`.

2. **Tạo file migration** (khi có thay đổi trong models):
   ```bash
   python manage.py makemigrations
   ```
3. **Áp dụng migration** (tạo bảng trong cơ sở dữ liệu):
   ```bash
   python manage.py migrate
   ```
