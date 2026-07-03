USE crm_db;

CREATE TABLE IF NOT EXISTS ActivityLog (
    LogID       INT PRIMARY KEY AUTO_INCREMENT,
    Username    VARCHAR(50),
    FullName    VARCHAR(100),
    Action      VARCHAR(50),    -- CREATE / UPDATE / DELETE / LOGIN / LOGOUT
    Module      VARCHAR(50),    -- Customer / Opportunity / Ticket...
    Description TEXT,
    IPAddress   VARCHAR(45),
    CreatedAt   DATETIME DEFAULT CURRENT_TIMESTAMP
);