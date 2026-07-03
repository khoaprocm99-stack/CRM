-- ============================================================
-- Thêm bảng Users vào crm_db
-- Chạy file này trong MySQL Shell hoặc phpMyAdmin
-- ============================================================

USE crm_db;

-- Tạo bảng Users
CREATE TABLE IF NOT EXISTS Users (
    UserID      INT PRIMARY KEY AUTO_INCREMENT,
    Username    VARCHAR(50) UNIQUE NOT NULL,
    Password    VARCHAR(100) NOT NULL,   -- lưu plain text (đơn giản cho bài tập)
    Role        VARCHAR(20) NOT NULL DEFAULT 'employee', -- admin / employee / guest
    EmployeeID  INT,                     -- liên kết với nhân viên (nếu có)
    FullName    VARCHAR(100),
    Status      VARCHAR(20) DEFAULT 'Active',
    CreatedAt   DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (EmployeeID) REFERENCES Employees(EmployeeID)
);

-- Tài khoản mặc định
INSERT IGNORE INTO Users (Username, Password, Role, FullName) VALUES
('admin',  'admin123', 'admin',    'Quản trị viên'),
('guest',  'guest123', 'guest',    'Khách');

-- Tạo tài khoản cho từng nhân viên (bỏ qua nếu đã tồn tại)
INSERT IGNORE INTO Users (Username, Password, Role, EmployeeID, FullName)
SELECT 
    LOWER(REPLACE(SUBSTRING_INDEX(Email, '@', 1), '.', '_')) AS Username,
    '123456' AS Password,
    'employee' AS Role,
    EmployeeID,
    FullName
FROM Employees;