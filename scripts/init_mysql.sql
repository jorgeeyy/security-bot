-- MySQL Database Initialization
CREATE DATABASE IF NOT EXISTS security_bot;

USE security_bot;

CREATE TABLE IF NOT EXISTS attacks (
    id INT AUTO_INCREMENT PRIMARY KEY,
    ip VARCHAR(45) NOT NULL,
    threat_type VARCHAR(100) NOT NULL,
    details TEXT,
    path VARCHAR(255),
    user_agent TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX (ip),
    INDEX (threat_type)
);

-- Optional: IP Whitelist for admins/authorized bots
CREATE TABLE IF NOT EXISTS whitelist (
    ip VARCHAR(45) PRIMARY KEY,
    reason VARCHAR(255),
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
