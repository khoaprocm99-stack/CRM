-- ============================================================
--  CRM DATABASE SCHEMA
--  Đồ án môn Cơ sở Ứng dụng HTTT - Nhóm 07 - NLU 2024
--  Chủ đề: Hệ thống Quản trị Quan hệ Khách hàng (CRM)
-- ============================================================
    
CREATE DATABASE IF NOT EXISTS crm_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE crm_db;

-- -------------------------------------------------------
-- 1. Bảng Employees (Nhân viên kinh doanh / hỗ trợ)
-- -------------------------------------------------------
CREATE TABLE Employees (
    EmployeeID   INT PRIMARY KEY AUTO_INCREMENT,
    FullName     VARCHAR(100) NOT NULL,
    Email        VARCHAR(100) UNIQUE,
    Phone        VARCHAR(20),
    Department   VARCHAR(50),        -- Sales / Support / Marketing
    Role         VARCHAR(50),        -- Nhân viên / Trưởng nhóm / Quản lý
    HireDate     DATE,
    Status       VARCHAR(20) DEFAULT 'Active'
);

-- -------------------------------------------------------
-- 2. Bảng Customers (Khách hàng)
-- -------------------------------------------------------
CREATE TABLE Customers (
    CustomerID   INT PRIMARY KEY AUTO_INCREMENT,
    FullName     VARCHAR(100) NOT NULL,
    Email        VARCHAR(100) UNIQUE,
    Phone        VARCHAR(20),
    Company      VARCHAR(100),
    Segment      VARCHAR(50),        -- SMB / Enterprise / Startup
    Source       VARCHAR(50),        -- Website / Referral / Event / Social
    AssignedTo   INT,                -- FK -> Employees
    CreatedAt    DATETIME DEFAULT CURRENT_TIMESTAMP,
    Status       VARCHAR(20) DEFAULT 'Active',
    FOREIGN KEY (AssignedTo) REFERENCES Employees(EmployeeID)
);

-- -------------------------------------------------------
-- 3. Bảng Products (Sản phẩm / Dịch vụ CRM)
-- -------------------------------------------------------
CREATE TABLE Products (
    ProductID    INT PRIMARY KEY AUTO_INCREMENT,
    ProductName  VARCHAR(100) NOT NULL,
    Category     VARCHAR(50),        -- CRM / Analytics / Integration / Support
    Price        DECIMAL(15,2),
    Description  TEXT,
    Status       VARCHAR(20) DEFAULT 'Active'
);

-- -------------------------------------------------------
-- 4. Bảng Opportunities (Cơ hội bán hàng - Sales Pipeline)
-- -------------------------------------------------------
CREATE TABLE Opportunities (
    OpportunityID  INT PRIMARY KEY AUTO_INCREMENT,
    CustomerID     INT NOT NULL,
    EmployeeID     INT NOT NULL,
    ProductID      INT,
    Title          VARCHAR(200),
    Stage          VARCHAR(50),      -- Lead / Qualified / Proposal / Negotiation / Closed Won / Closed Lost
    Value          DECIMAL(15,2),    -- Giá trị hợp đồng dự kiến (VND)
    Probability    INT,              -- Xác suất chốt deal (%)
    CreatedAt      DATETIME DEFAULT CURRENT_TIMESTAMP,
    ExpectedClose  DATE,
    ClosedAt       DATETIME,
    Notes          TEXT,
    FOREIGN KEY (CustomerID)  REFERENCES Customers(CustomerID),
    FOREIGN KEY (EmployeeID)  REFERENCES Employees(EmployeeID),
    FOREIGN KEY (ProductID)   REFERENCES Products(ProductID)
);

-- -------------------------------------------------------
-- 5. Bảng Interactions (Lịch sử tương tác với khách hàng)
-- -------------------------------------------------------
CREATE TABLE Interactions (
    InteractionID  INT PRIMARY KEY AUTO_INCREMENT,
    CustomerID     INT NOT NULL,
    EmployeeID     INT NOT NULL,
    Type           VARCHAR(50),      -- Email / Call / Meeting / Demo / Chat
    Subject        VARCHAR(200),
    Notes          TEXT,
    InteractedAt   DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (CustomerID) REFERENCES Customers(CustomerID),
    FOREIGN KEY (EmployeeID) REFERENCES Employees(EmployeeID)
);

-- -------------------------------------------------------
-- 6. Bảng SupportTickets (Phiếu hỗ trợ khách hàng)
-- -------------------------------------------------------
CREATE TABLE SupportTickets (
    TicketID     INT PRIMARY KEY AUTO_INCREMENT,
    CustomerID   INT NOT NULL,
    EmployeeID   INT,
    Subject      VARCHAR(200) NOT NULL,
    Description  TEXT,
    Priority     VARCHAR(20) DEFAULT 'Medium', -- Low / Medium / High / Critical
    Status       VARCHAR(30) DEFAULT 'Open',   -- Open / In Progress / Resolved / Closed
    CreatedAt    DATETIME DEFAULT CURRENT_TIMESTAMP,
    ResolvedAt   DATETIME,
    FOREIGN KEY (CustomerID) REFERENCES Customers(CustomerID),
    FOREIGN KEY (EmployeeID) REFERENCES Employees(EmployeeID)
);

-- ============================================================
-- DỮ LIỆU MẪU (INSERT INTO)
-- ============================================================

-- Nhân viên
INSERT INTO Employees (FullName, Email, Phone, Department, Role, HireDate) VALUES
('Nguyễn Văn An',    'an.nguyen@crm.vn',    '0901111111', 'Sales',     'Nhân viên',  '2022-03-01'),
('Trần Thị Bình',    'binh.tran@crm.vn',    '0902222222', 'Sales',     'Trưởng nhóm','2021-06-15'),
('Lê Hoàng Cường',   'cuong.le@crm.vn',     '0903333333', 'Support',   'Nhân viên',  '2023-01-10'),
('Phạm Minh Đức',    'duc.pham@crm.vn',     '0904444444', 'Marketing', 'Nhân viên',  '2022-09-20'),
('Hoàng Thị Em',     'em.hoang@crm.vn',     '0905555555', 'Support',   'Trưởng nhóm','2020-11-05');

-- Sản phẩm
INSERT INTO Products (ProductName, Category, Price, Description) VALUES
('CRM Starter',      'CRM',         5000000,  'Gói CRM cơ bản cho doanh nghiệp nhỏ, tối đa 5 người dùng'),
('CRM Professional', 'CRM',        15000000,  'Gói CRM chuyên nghiệp, không giới hạn người dùng, tích hợp email'),
('CRM Enterprise',   'CRM',        40000000,  'Gói CRM doanh nghiệp lớn, AI + Big Data + API đầy đủ'),
('Analytics Add-on', 'Analytics',   8000000,  'Mô-đun phân tích nâng cao, dashboard tùy chỉnh'),
('Integration Pack', 'Integration', 6000000,  'Tích hợp ERP, kế toán, eCommerce qua API');

-- Khách hàng
INSERT INTO Customers (FullName, Email, Phone, Company, Segment, Source, AssignedTo) VALUES
('Nguyễn Quốc Hùng',  'hung@techvn.com',    '0911111111', 'TechVN JSC',         'SMB',        'Website',  1),
('Lê Thị Mai',         'mai@retail360.vn',   '0922222222', 'Retail 360',         'SMB',        'Referral', 1),
('Trần Văn Sơn',       'son@bigcorp.vn',     '0933333333', 'BigCorp Vietnam',    'Enterprise', 'Event',    2),
('Phạm Thanh Hà',      'ha@startup.io',      '0944444444', 'StartupIO',          'Startup',    'Social',   2),
('Đỗ Minh Tuấn',       'tuan@manufact.vn',   '0955555555', 'Manufact VN',        'Enterprise', 'Website',  2),
('Vũ Thị Lan',         'lan@smeshop.vn',     '0966666666', 'SME Shop',           'SMB',        'Referral', 1),
('Bùi Đức Thắng',      'thang@fintech.vn',   '0977777777', 'FinTech Solutions',  'Startup',    'Social',   4),
('Ngô Thanh Xuân',     'xuan@distributor.vn','0988888888', 'VN Distributor Co.', 'Enterprise', 'Event',    2);

-- Cơ hội bán hàng
INSERT INTO Opportunities (CustomerID, EmployeeID, ProductID, Title, Stage, Value, Probability, ExpectedClose, Notes) VALUES
(1, 1, 1, 'TechVN - Triển khai CRM Starter',          'Proposal',     5000000,   60, '2025-07-15', 'Khách hàng đã demo, đang chờ phê duyệt ngân sách'),
(2, 1, 1, 'Retail360 - CRM cho chuỗi bán lẻ',         'Qualified',    5000000,   40, '2025-08-01', 'Cần tích hợp với phần mềm POS hiện tại'),
(3, 2, 3, 'BigCorp - CRM Enterprise toàn công ty',     'Negotiation', 40000000,   75, '2025-07-30', 'Đang đàm phán điều khoản SLA'),
(4, 2, 1, 'StartupIO - Gói Starter dùng thử',          'Lead',         5000000,   20, '2025-09-01', 'Mới tiếp cận qua LinkedIn'),
(5, 2, 3, 'Manufact VN - CRM + Analytics',             'Proposal',    48000000,   55, '2025-07-20', 'Bundle CRM Enterprise + Analytics Add-on'),
(6, 1, 2, 'SME Shop - Nâng cấp lên Professional',      'Closed Won',  15000000,  100, '2025-06-01', 'Đã ký hợp đồng 12 tháng'),
(7, 4, 2, 'FinTech - CRM Professional',                'Qualified',   15000000,   50, '2025-08-15', 'Yêu cầu bảo mật cao, tuân thủ PDPD'),
(8, 2, 3, 'VN Distributor - Enterprise rollout',       'Closed Lost',  40000000,    0, '2025-05-30', 'Khách hàng chọn Salesforce');

-- Cập nhật thời gian đóng cho deal đã kết thúc
UPDATE Opportunities SET ClosedAt = '2025-06-01 10:00:00' WHERE OpportunityID = 6;
UPDATE Opportunities SET ClosedAt = '2025-05-30 15:00:00' WHERE OpportunityID = 8;

-- Lịch sử tương tác
INSERT INTO Interactions (CustomerID, EmployeeID, Type, Subject, Notes, InteractedAt) VALUES
(1, 1, 'Call',    'Gọi giới thiệu sản phẩm CRM Starter',    'Khách hàng quan tâm, hẹn demo vào tuần sau',         '2025-05-10 09:30:00'),
(1, 1, 'Meeting', 'Demo CRM Starter tại văn phòng TechVN',   'Demo thành công, khách hàng hài lòng với tính năng', '2025-05-20 14:00:00'),
(3, 2, 'Email',   'Gửi đề xuất CRM Enterprise cho BigCorp',  'Đính kèm báo giá và case study',                    '2025-05-15 08:00:00'),
(3, 2, 'Meeting', 'Họp đàm phán hợp đồng với BigCorp',       'Thảo luận SLA 99.9% uptime và điều khoản bảo mật',  '2025-06-01 10:00:00'),
(6, 1, 'Call',    'Tư vấn nâng cấp gói cho SME Shop',        'Khách đồng ý nâng cấp lên Professional',             '2025-05-28 11:00:00'),
(4, 2, 'Chat',    'Trả lời câu hỏi qua Zalo',                'Giải đáp thắc mắc về giới hạn người dùng',           '2025-06-03 16:30:00'),
(7, 4, 'Demo',    'Demo bảo mật CRM cho FinTech',            'Nhấn mạnh MFA, RBAC, tuân thủ Nghị định 13/2023',   '2025-06-05 09:00:00'),
(2, 1, 'Email',   'Gửi tài liệu tích hợp POS cho Retail360', 'Tài liệu API tích hợp KiotViet',                    '2025-06-07 08:30:00');

-- Phiếu hỗ trợ
INSERT INTO SupportTickets (CustomerID, EmployeeID, Subject, Description, Priority, Status, ResolvedAt) VALUES
(6, 3, 'Không đăng nhập được vào hệ thống',    'Lỗi "Invalid credentials" sau khi đổi mật khẩu',            'High',     'Resolved', '2025-06-02 10:00:00'),
(6, 3, 'Yêu cầu xuất báo cáo tùy chỉnh',      'Cần export báo cáo pipeline theo tháng ra Excel',           'Medium',   'Closed',   '2025-06-05 14:00:00'),
(1, 3, 'Câu hỏi về tích hợp email marketing', 'Hỏi cách kết nối Mailchimp với CRM Starter',                 'Low',      'Resolved', '2025-06-08 09:00:00'),
(3, 5, 'Yêu cầu đào tạo nhân viên',           'BigCorp cần 2 buổi training cho 30 nhân viên sử dụng CRM',   'Medium',   'Open',     NULL),
(7, 5, 'Audit log không hiển thị đủ',          'Cần xem lịch sử truy cập theo từng user trong 90 ngày',     'High',     'In Progress', NULL);
