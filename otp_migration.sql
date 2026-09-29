USE college_campus_portal_cloud;

-- Version 6 OTP/device-login repair for an EXISTING database.
-- Safe to run more than once on MySQL 8+.

SET @has_device = (
  SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS
  WHERE TABLE_SCHEMA = DATABASE()
    AND TABLE_NAME = 'users'
    AND COLUMN_NAME = 'device_hash'
);
SET @sql = IF(
  @has_device = 0,
  'ALTER TABLE users ADD COLUMN device_hash VARCHAR(128) NULL AFTER enrollment_no',
  'SELECT 1'
);
PREPARE stmt FROM @sql;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

CREATE TABLE IF NOT EXISTS otp_codes (
  id BIGINT AUTO_INCREMENT PRIMARY KEY,
  user_id INT NOT NULL,
  purpose VARCHAR(40) NOT NULL,
  code_hash VARCHAR(128) NOT NULL,
  expires_at DATETIME NOT NULL,
  attempts INT DEFAULT 0,
  used_at DATETIME NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  INDEX idx_otp_user(user_id,purpose,expires_at),
  FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
);
