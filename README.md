# CRM Web Application
## Đồ án môn Cơ sở Ứng dụng HTTT — Nhóm 07 — NLU 2024

---

## HƯỚNG DẪN CHẠY

### Bước 1: Cài đặt MySQL
Đảm bảo MySQL đang chạy trên máy. Dùng XAMPP, WAMP, hoặc MySQL Server.

### Bước 2: Tạo database
Mở MySQL Workbench / phpMyAdmin / terminal, chạy file SQL:

```bash
mysql -u root -p < sql/crm_schema.sql
```

Hoặc mở phpMyAdmin → Import → chọn file `sql/crm_schema.sql`

### Bước 3: Cấu hình kết nối
Mở `app.py`, sửa phần DB_CONFIG:

```python
DB_CONFIG = {
    'host':     'localhost',
    'user':     'root',
    'password': 'MẬT_KHẨU_MYSQL_CỦA_BẠN',  # <-- sửa ở đây
    'database': 'crm_db',
}
```

### Bước 4: Cài thư viện Python
```bash
pip install -r requirements.txt
```

### Bước 5: Chạy ứng dụng
```bash
python app.py
```

### Bước 6: Mở trình duyệt
Truy cập: http://127.0.0.1:5000

---

## CẤU TRÚC DỰ ÁN

```
crm_app/
├── app.py                  ← Flask application chính
├── requirements.txt        ← Thư viện Python cần cài
├── sql/
│   └── crm_schema.sql      ← Schema CSDL + dữ liệu mẫu
└── templates/
    ├── base.html           ← Layout chung (sidebar, navbar)
    ├── index.html          ← Dashboard tổng quan
    ├── customers.html      ← Danh sách khách hàng
    ├── customer_detail.html← Chi tiết khách hàng (360°)
    ├── customer_form.html  ← Form thêm/sửa khách hàng
    ├── opportunities.html  ← Sales Pipeline
    ├── opportunity_form.html← Form cơ hội bán hàng
    ├── interactions.html   ← Lịch sử tương tác
    ├── interaction_form.html← Form ghi nhận tương tác
    ├── tickets.html        ← Danh sách ticket hỗ trợ
    ├── ticket_form.html    ← Form tạo ticket
    └── employees.html      ← Danh sách nhân viên
```

---

## CHỨC NĂNG

| Module | Chức năng |
|--------|-----------|
| Dashboard | Thống kê tổng quan, pipeline, tương tác gần đây |
| Khách hàng | Thêm/sửa/xóa, xem hồ sơ 360°, lọc theo phân khúc |
| Cơ hội bán hàng | Sales Pipeline, theo dõi giai đoạn deal |
| Tương tác | Ghi lịch sử email, gọi điện, họp, demo |
| Ticket hỗ trợ | Quản lý yêu cầu, đánh dấu giải quyết |
| Nhân viên | Danh sách nhân viên và hiệu suất |

---

## SƠ ĐỒ ERD (tóm tắt)

Employees ──< Customers ──< Opportunities
                    |──< Interactions
                    |──< SupportTickets
Products ──────────< Opportunities
