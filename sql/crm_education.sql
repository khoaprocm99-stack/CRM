-- ============================================================
--  CRM GIÁO DỤC - Trung tâm Đào tạo
--  Đồ án môn Cơ sở Ứng dụng HTTT - Nhóm 07 - NLU 2024
-- ============================================================

CREATE DATABASE IF NOT EXISTS crm_edu CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE crm_edu;

-- ── 1. Nhân viên (Giảng viên / Tư vấn / Quản lý) ──────────
CREATE TABLE Staff (
    StaffID     INT PRIMARY KEY AUTO_INCREMENT,
    FullName    VARCHAR(100) NOT NULL,
    Email       VARCHAR(100) UNIQUE,
    Phone       VARCHAR(20),
    Department  VARCHAR(50),   -- Sales / Teaching / Admin / Support
    Role        VARCHAR(50),   -- Tư vấn viên / Giảng viên / Trưởng nhóm / Quản lý
    HireDate    DATE,
    Status      VARCHAR(20) DEFAULT 'Active'
);

-- ── 2. Khóa học ────────────────────────────────────────────
CREATE TABLE Courses (
    CourseID    INT PRIMARY KEY AUTO_INCREMENT,
    CourseName  VARCHAR(150) NOT NULL,
    Category    VARCHAR(50),   -- Lập trình / Ngoại ngữ / Kỹ năng / Thiết kế / Kinh doanh
    Level       VARCHAR(30),   -- Cơ bản / Trung cấp / Nâng cao
    Duration    INT,           -- Số buổi học
    Fee         DECIMAL(12,2), -- Học phí
    Description TEXT,
    Status      VARCHAR(20) DEFAULT 'Active'
);

-- ── 3. Lớp học ─────────────────────────────────────────────
CREATE TABLE Classes (
    ClassID         INT PRIMARY KEY AUTO_INCREMENT,
    CourseID        INT NOT NULL,
    ClassName       VARCHAR(100),  -- Ví dụ: Python K01 - Sáng T2T4T6
    TeacherID       INT,           -- FK -> Staff
    StartDate       DATE,
    EndDate         DATE,
    Schedule        VARCHAR(100),  -- Lịch học: T2T4T6 7:30-9:30
    Room            VARCHAR(50),
    MaxStudents     INT DEFAULT 30,
    CurrentStudents INT DEFAULT 0,
    Status          VARCHAR(20) DEFAULT 'Upcoming', -- Upcoming/Ongoing/Completed/Cancelled
    FOREIGN KEY (CourseID)   REFERENCES Courses(CourseID),
    FOREIGN KEY (TeacherID)  REFERENCES Staff(StaffID)
);

-- ── 4. Học viên ────────────────────────────────────────────
CREATE TABLE Students (
    StudentID   INT PRIMARY KEY AUTO_INCREMENT,
    FullName    VARCHAR(100) NOT NULL,
    Email       VARCHAR(100) UNIQUE,
    Phone       VARCHAR(20),
    DOB         DATE,
    Gender      VARCHAR(10),
    Address     TEXT,
    Source      VARCHAR(50),   -- Website / Facebook / Referral / Walk-in / Zalo
    AssignedTo  INT,           -- FK -> Staff (Tư vấn viên phụ trách)
    Status      VARCHAR(20) DEFAULT 'Prospect', -- Prospect/Enrolled/Studying/Graduated/Dropped
    Notes       TEXT,
    CreatedAt   DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (AssignedTo) REFERENCES Staff(StaffID)
);

-- ── 5. Đăng ký học (thay Opportunities) ────────────────────
CREATE TABLE Enrollments (
    EnrollmentID INT PRIMARY KEY AUTO_INCREMENT,
    StudentID    INT NOT NULL,
    ClassID      INT NOT NULL,
    StaffID      INT,           -- Tư vấn viên xử lý
    EnrollDate   DATE,
    Status       VARCHAR(30) DEFAULT 'Pending',
                                -- Pending/Confirmed/Studying/Completed/Dropped/Refunded
    TotalFee     DECIMAL(12,2),
    Discount     DECIMAL(12,2) DEFAULT 0,
    FinalFee     DECIMAL(12,2),
    Notes        TEXT,
    CreatedAt    DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (StudentID) REFERENCES Students(StudentID),
    FOREIGN KEY (ClassID)   REFERENCES Classes(ClassID),
    FOREIGN KEY (StaffID)   REFERENCES Staff(StaffID)
);

-- ── 6. Thanh toán học phí ──────────────────────────────────
CREATE TABLE Payments (
    PaymentID    INT PRIMARY KEY AUTO_INCREMENT,
    EnrollmentID INT NOT NULL,
    StudentID    INT NOT NULL,
    Amount       DECIMAL(12,2) NOT NULL,
    PaymentDate  DATE,
    Method       VARCHAR(30),  -- Tiền mặt / Chuyển khoản / Thẻ
    Note         VARCHAR(200),
    CreatedBy    INT,          -- FK -> Staff
    CreatedAt    DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (EnrollmentID) REFERENCES Enrollments(EnrollmentID),
    FOREIGN KEY (StudentID)    REFERENCES Students(StudentID),
    FOREIGN KEY (CreatedBy)    REFERENCES Staff(StaffID)
);

-- ── 7. Lịch sử tư vấn (thay Interactions) ─────────────────
CREATE TABLE Consultations (
    ConsultID   INT PRIMARY KEY AUTO_INCREMENT,
    StudentID   INT NOT NULL,
    StaffID     INT NOT NULL,
    Type        VARCHAR(30),   -- Gọi điện / Gặp mặt / Zalo / Email / Demo
    Subject     VARCHAR(200),
    Notes       TEXT,
    Result      VARCHAR(50),   -- Quan tâm / Cần suy nghĩ / Đã đăng ký / Không quan tâm
    NextAction  VARCHAR(200),  -- Hành động tiếp theo
    ConsultedAt DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (StudentID) REFERENCES Students(StudentID),
    FOREIGN KEY (StaffID)   REFERENCES Staff(StaffID)
);

-- ── 8. Phản hồi / Khiếu nại (thay SupportTickets) ─────────
CREATE TABLE Feedbacks (
    FeedbackID  INT PRIMARY KEY AUTO_INCREMENT,
    StudentID   INT NOT NULL,
    StaffID     INT,
    ClassID     INT,
    Type        VARCHAR(30) DEFAULT 'Feedback', -- Feedback / Complaint / Request
    Subject     VARCHAR(200) NOT NULL,
    Content     TEXT,
    Priority    VARCHAR(20) DEFAULT 'Medium',
    Status      VARCHAR(30) DEFAULT 'Open',     -- Open/Processing/Resolved/Closed
    Response    TEXT,
    CreatedAt   DATETIME DEFAULT CURRENT_TIMESTAMP,
    ResolvedAt  DATETIME,
    FOREIGN KEY (StudentID) REFERENCES Students(StudentID),
    FOREIGN KEY (StaffID)   REFERENCES Staff(StaffID),
    FOREIGN KEY (ClassID)   REFERENCES Classes(ClassID)
);

-- ── 9. Tài khoản người dùng ────────────────────────────────
CREATE TABLE Users (
    UserID      INT PRIMARY KEY AUTO_INCREMENT,
    Username    VARCHAR(50) UNIQUE NOT NULL,
    Password    VARCHAR(100) NOT NULL,
    Role        VARCHAR(20) DEFAULT 'employee',
    StaffID     INT,
    FullName    VARCHAR(100),
    Status      VARCHAR(20) DEFAULT 'Active',
    CreatedAt   DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (StaffID) REFERENCES Staff(StaffID)
);

-- ── 10. Nhật ký hoạt động ──────────────────────────────────
CREATE TABLE ActivityLog (
    LogID       INT PRIMARY KEY AUTO_INCREMENT,
    Username    VARCHAR(50),
    FullName    VARCHAR(100),
    Action      VARCHAR(50),
    Module      VARCHAR(50),
    Description TEXT,
    IPAddress   VARCHAR(45),
    CreatedAt   DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================
-- DỮ LIỆU MẪU
-- ============================================================

-- Nhân viên
INSERT INTO Staff (FullName, Email, Phone, Department, Role, HireDate) VALUES
('Nguyễn Thị Lan',    'lan.nguyen@edu.vn',   '0901111111', 'Sales',    'Tư vấn viên',  '2022-01-10'),
('Trần Văn Minh',     'minh.tran@edu.vn',    '0902222222', 'Sales',    'Tư vấn viên',  '2022-03-15'),
('Lê Hoàng Phúc',    'phuc.le@edu.vn',      '0903333333', 'Teaching', 'Giảng viên',   '2021-06-01'),
('Phạm Thị Hoa',     'hoa.pham@edu.vn',     '0904444444', 'Teaching', 'Giảng viên',   '2021-09-01'),
('Đỗ Minh Quân',     'quan.do@edu.vn',      '0905555555', 'Admin',    'Quản lý',      '2020-01-01'),
('Vũ Thị Thu',       'thu.vu@edu.vn',       '0906666666', 'Support',  'Tư vấn viên',  '2023-02-01');

-- Khóa học
INSERT INTO Courses (CourseName, Category, Level, Duration, Fee, Description) VALUES
('Lập trình Python cơ bản',        'Lập trình', 'Cơ bản',   30, 3500000,  'Học Python từ đầu, phù hợp người mới bắt đầu'),
('Lập trình Web với Flask',         'Lập trình', 'Trung cấp',40, 5000000,  'Xây dựng web app với Python Flask và MySQL'),
('Data Science với Python',         'Lập trình', 'Nâng cao', 50, 7000000,  'Phân tích dữ liệu, Machine Learning cơ bản'),
('Tiếng Anh giao tiếp A1-A2',      'Ngoại ngữ', 'Cơ bản',   60, 4000000,  'Tiếng Anh giao tiếp cho người mất gốc'),
('IELTS Foundation',                'Ngoại ngữ', 'Trung cấp',80, 8500000,  'Luyện thi IELTS từ 4.5 lên 6.0'),
('Kỹ năng thuyết trình',           'Kỹ năng',   'Cơ bản',   20, 2500000,  'Tự tin trình bày trước đám đông'),
('Microsoft Office nâng cao',       'Tin học',   'Trung cấp',24, 2000000,  'Word, Excel, PowerPoint chuyên nghiệp'),
('Thiết kế đồ họa với Photoshop',  'Thiết kế',  'Cơ bản',   36, 4500000,  'Thiết kế poster, banner, ảnh sản phẩm');

-- Lớp học
INSERT INTO Classes (CourseID, ClassName, TeacherID, StartDate, EndDate, Schedule, Room, MaxStudents, CurrentStudents, Status) VALUES
(1, 'Python K01 - Tối T2T4T6', 3, '2025-06-02', '2025-07-18', 'T2T4T6 18:00-20:00', 'Phòng 101', 20, 15, 'Ongoing'),
(1, 'Python K02 - Sáng T7CN',  3, '2025-07-05', '2025-08-31', 'T7CN 8:00-10:30',    'Phòng 101', 20, 8,  'Upcoming'),
(2, 'Flask Web K01 - Tối T3T5',4, '2025-06-10', '2025-08-05', 'T3T5 18:30-20:30',   'Phòng 102', 15, 10, 'Ongoing'),
(4, 'Anh văn A1 - Sáng T2T4T6',4, '2025-06-02', '2025-08-29', 'T2T4T6 7:30-9:00',   'Phòng 201', 25, 20, 'Ongoing'),
(5, 'IELTS K05 - Tối T2T4',    3, '2025-07-01', '2025-10-01', 'T2T4 19:00-21:00',   'Phòng 202', 15, 5,  'Upcoming'),
(6, 'Thuyết trình K03',        4, '2025-06-15', '2025-07-06', 'CN 8:00-12:00',       'Phòng 301', 30, 22, 'Ongoing'),
(7, 'Office K08 - Chiều T7',   3, '2025-06-07', '2025-07-26', 'T7 13:00-16:00',     'Phòng 102', 20, 18, 'Ongoing'),
(3, 'Data Science K01',        4, '2025-08-01', '2025-10-30', 'T3T5T7 18:00-20:30', 'Phòng 103', 12, 0,  'Upcoming');

-- Học viên
INSERT INTO Students (FullName, Email, Phone, DOB, Gender, Source, AssignedTo, Status, Notes) VALUES
('Nguyễn Quang Huy',  'huy.nq@gmail.com',    '0911111111', '2003-05-10', 'Nam', 'Facebook',  1, 'Studying',  'Học tốt, cần hỗ trợ bài tập'),
('Trần Thị Bảo Châu', 'chau.ttb@gmail.com',  '0922222222', '2002-08-22', 'Nữ',  'Website',   1, 'Studying',  NULL),
('Lê Văn Đức',        'duc.lv@gmail.com',     '0933333333', '2001-12-01', 'Nam', 'Referral',  2, 'Enrolled',  'Giới thiệu từ bạn'),
('Phạm Ngọc Hà',      'ha.pn@gmail.com',      '0944444444', '2004-03-15', 'Nữ',  'Zalo',      2, 'Prospect',  'Đang cân nhắc khóa IELTS'),
('Hoàng Minh Tuấn',   'tuan.hm@gmail.com',    '0955555555', '2000-07-20', 'Nam', 'Walk-in',   1, 'Studying',  NULL),
('Vũ Thị Lan Anh',    'lanh.vt@gmail.com',    '0966666666', '2003-11-08', 'Nữ',  'Facebook',  6, 'Graduated', 'Đã hoàn thành Python K01 cũ'),
('Đỗ Quốc Bảo',       'bao.dq@gmail.com',     '0977777777', '2002-04-25', 'Nam', 'Website',   2, 'Studying',  NULL),
('Bùi Thị Mai',       'mai.bt@gmail.com',      '0988888888', '2001-09-14', 'Nữ',  'Referral',  1, 'Prospect',  'Quan tâm Office + Thuyết trình'),
('Ngô Văn Thắng',     'thang.nv@gmail.com',   '0999999999', '2003-02-28', 'Nam', 'Zalo',      6, 'Enrolled',  NULL),
('Cao Thị Hồng',      'hong.ct@gmail.com',     '0910000000', '2000-06-18', 'Nữ',  'Facebook',  2, 'Dropped',   'Nghỉ do bận công việc');

-- Đăng ký học
INSERT INTO Enrollments (StudentID, ClassID, StaffID, EnrollDate, Status, TotalFee, Discount, FinalFee, Notes) VALUES
(1, 1, 1, '2025-05-28', 'Studying',   3500000, 0,      3500000, NULL),
(2, 1, 1, '2025-05-30', 'Studying',   3500000, 350000, 3150000, 'Giảm 10% học viên mới'),
(3, 3, 2, '2025-06-08', 'Confirmed',  5000000, 0,      5000000, NULL),
(5, 4, 1, '2025-05-25', 'Studying',   4000000, 0,      4000000, NULL),
(6, 1, 1, '2025-01-10', 'Completed',  3500000, 0,      3500000, 'Đã hoàn thành'),
(7, 3, 2, '2025-06-09', 'Studying',   5000000, 500000, 4500000, 'Giảm 10% thanh toán sớm'),
(9, 7, 6, '2025-06-05', 'Studying',   2000000, 0,      2000000, NULL),
(1, 6, 1, '2025-06-10', 'Studying',   2500000, 250000, 2250000, 'Combo 2 khóa giảm 10%');

-- Thanh toán
INSERT INTO Payments (EnrollmentID, StudentID, Amount, PaymentDate, Method, Note, CreatedBy) VALUES
(1, 1, 3500000, '2025-05-28', 'Chuyển khoản', 'Đóng đủ 100%', 1),
(2, 2, 1575000, '2025-05-30', 'Tiền mặt',    'Đóng 50% đợt 1', 1),
(2, 2, 1575000, '2025-06-15', 'Chuyển khoản','Đóng 50% đợt 2', 1),
(3, 3, 2500000, '2025-06-08', 'Tiền mặt',    'Đóng 50% đợt 1', 2),
(4, 5, 4000000, '2025-05-25', 'Chuyển khoản','Đóng đủ 100%', 1),
(6, 7, 4500000, '2025-06-09', 'Thẻ',         'Đóng đủ 100%', 2),
(7, 9, 1000000, '2025-06-05', 'Tiền mặt',    'Đóng 50% đợt 1', 6),
(8, 1, 2250000, '2025-06-10', 'Chuyển khoản','Đóng đủ 100%', 1);

-- Lịch sử tư vấn
INSERT INTO Consultations (StudentID, StaffID, Type, Subject, Notes, Result, NextAction, ConsultedAt) VALUES
(1, 1, 'Zalo',      'Tư vấn khóa Python cho người mới',    'Học viên không có nền tảng lập trình, muốn học Python để xin việc', 'Đã đăng ký',     NULL,                        '2025-05-25 09:00:00'),
(2, 1, 'Gặp mặt',  'Tư vấn trực tiếp tại trung tâm',      'Đến xem cơ sở vật chất, quan tâm Python và Flask',                 'Đã đăng ký',     NULL,                        '2025-05-28 14:00:00'),
(4, 2, 'Gọi điện', 'Tư vấn khóa IELTS',                   'Học viên muốn thi IELTS 6.0 trong 6 tháng',                        'Cần suy nghĩ',   'Gọi lại sau 3 ngày',        '2025-06-01 10:30:00'),
(4, 2, 'Zalo',     'Follow up IELTS Foundation',           'Gửi lịch khai giảng và ưu đãi early bird',                         'Quan tâm',       'Mời đến demo class',         '2025-06-04 11:00:00'),
(8, 1, 'Gọi điện', 'Tư vấn combo Office + Thuyết trình',  'Quan tâm 2 khóa, hỏi về giảm giá combo',                           'Cần suy nghĩ',   'Gửi báo giá combo',         '2025-06-05 15:00:00'),
(10,2, 'Gặp mặt',  'Xử lý học viên xin nghỉ học',         'Lý do bận việc, hỏi về chính sách bảo lưu',                        'Không quan tâm', 'Hoàn phí theo quy định',    '2025-06-08 09:30:00'),
(3, 2, 'Email',    'Xác nhận lịch học Flask Web',          'Gửi thông tin lớp, phòng học và tài liệu chuẩn bị',               'Đã đăng ký',     NULL,                        '2025-06-07 08:00:00'),
(9, 6, 'Zalo',     'Tư vấn khóa Office',                   'Cần học Excel nâng cao để làm kế toán',                            'Đã đăng ký',     NULL,                        '2025-06-03 16:00:00');

-- Phản hồi
INSERT INTO Feedbacks (StudentID, StaffID, ClassID, Type, Subject, Content, Priority, Status, Response) VALUES
(1, 3, 1, 'Feedback',  'Giảng viên giảng rất dễ hiểu',         'Mong trung tâm mở thêm lớp nâng cao', 'Low',    'Closed',   'Cảm ơn phản hồi, sẽ mở Python nâng cao trong Q3'),
(5, 4, 4, 'Complaint', 'Máy lạnh phòng 201 bị hỏng',           'Học rất nóng, khó tập trung',          'High',   'Resolved', 'Đã sửa máy lạnh ngày 05/06'),
(2, 1, 1, 'Request',   'Xin tài liệu học thêm',                 'Muốn có thêm bài tập về nhà',          'Medium', 'Resolved', 'Đã gửi tài liệu qua email'),
(7, 2, 3, 'Feedback',  'Lớp Flask rất thực tế',                 'Nội dung bài giảng sát với công việc', 'Low',    'Closed',   'Cảm ơn phản hồi tích cực'),
(9, 6, 7, 'Complaint', 'Lịch học bị thay đổi không báo trước', 'Tuần trước đổi phòng không thông báo', 'High',   'Processing','Đang xem xét và cải thiện quy trình thông báo');

-- Tài khoản
INSERT INTO Users (Username, Password, Role, FullName) VALUES
('admin',     'admin123', 'admin',    'Quản trị viên'),
('guest',     'guest123', 'guest',    'Khách');

INSERT INTO Users (Username, Password, Role, StaffID, FullName)
SELECT
    LOWER(REPLACE(SUBSTRING_INDEX(Email,'@',1),'.','_')),
    '123456', 'employee', StaffID, FullName
FROM Staff;