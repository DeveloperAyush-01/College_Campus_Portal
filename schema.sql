CREATE DATABASE IF NOT EXISTS college_campus_portal_cloud CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE college_campus_portal_cloud;

CREATE TABLE IF NOT EXISTS users (
 id INT AUTO_INCREMENT PRIMARY KEY,
 username VARCHAR(120) NOT NULL UNIQUE,
 password_hash VARCHAR(255) NOT NULL,
 role ENUM('admin','teacher','student') NOT NULL,
 full_name VARCHAR(180) NOT NULL,
 email VARCHAR(180) UNIQUE,
 phone VARCHAR(30),
 branch VARCHAR(80), year_no INT, semester VARCHAR(30), roll_no VARCHAR(60) UNIQUE,
 enrollment_no VARCHAR(80) UNIQUE,
 device_hash VARCHAR(128),
 profile_image VARCHAR(255), bio TEXT, designation VARCHAR(180), qualification VARCHAR(255),
 active TINYINT(1) DEFAULT 1,
 registration_status ENUM('reserved','pending','active','rejected') DEFAULT 'active',
 created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
 last_login DATETIME NULL
);

CREATE TABLE IF NOT EXISTS subjects (
 id INT AUTO_INCREMENT PRIMARY KEY,
 branch VARCHAR(80) NOT NULL, year_no INT NOT NULL, semester VARCHAR(30) NOT NULL,
 subject_code VARCHAR(30), subject_name VARCHAR(180) NOT NULL,
 UNIQUE KEY uq_subject (branch,year_no,semester,subject_name), INDEX idx_subject_scope(branch,year_no,semester)
);
CREATE TABLE IF NOT EXISTS teacher_subjects (
 id INT AUTO_INCREMENT PRIMARY KEY, teacher_id INT NOT NULL, subject_id INT NOT NULL,
 UNIQUE KEY uq_teacher_subject(teacher_id,subject_id),
 FOREIGN KEY(teacher_id) REFERENCES users(id) ON DELETE CASCADE,
 FOREIGN KEY(subject_id) REFERENCES subjects(id) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS attendance (
 id BIGINT AUTO_INCREMENT PRIMARY KEY, student_id INT NOT NULL, subject_id INT NOT NULL, attendance_date DATE NOT NULL,
 status ENUM('present','absent','late') NOT NULL DEFAULT 'present', marked_by INT NULL, source VARCHAR(30) DEFAULT 'teacher',
 UNIQUE KEY uq_attendance(student_id,subject_id,attendance_date), INDEX idx_att_student(student_id), INDEX idx_att_subject(subject_id),
 FOREIGN KEY(student_id) REFERENCES users(id) ON DELETE CASCADE, FOREIGN KEY(subject_id) REFERENCES subjects(id) ON DELETE CASCADE,
 FOREIGN KEY(marked_by) REFERENCES users(id) ON DELETE SET NULL
);
CREATE TABLE IF NOT EXISTS qr_sessions (
 id BIGINT AUTO_INCREMENT PRIMARY KEY, token_hash VARCHAR(128) NOT NULL UNIQUE, subject_id INT NOT NULL, teacher_id INT NOT NULL,
 valid_from DATETIME NOT NULL, valid_until DATETIME NOT NULL, active TINYINT(1) DEFAULT 1,
 FOREIGN KEY(subject_id) REFERENCES subjects(id) ON DELETE CASCADE, FOREIGN KEY(teacher_id) REFERENCES users(id) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS posts (
 id BIGINT AUTO_INCREMENT PRIMARY KEY,
 post_type ENUM('note','notice','timetable','circular','activity','form') NOT NULL,
 title VARCHAR(255) NOT NULL, body TEXT, file_path VARCHAR(500), file_type VARCHAR(80), image_path VARCHAR(500),
 branch VARCHAR(80), year_no INT, semester VARCHAR(30), subject_id INT, created_by INT NOT NULL, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
 INDEX idx_posts_audience(branch,year_no,semester), FOREIGN KEY(subject_id) REFERENCES subjects(id) ON DELETE SET NULL, FOREIGN KEY(created_by) REFERENCES users(id) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS complaints (
 id BIGINT AUTO_INCREMENT PRIMARY KEY, student_id INT NOT NULL, category VARCHAR(100) NOT NULL, subject VARCHAR(255) NOT NULL, message TEXT NOT NULL,
 status ENUM('open','in_progress','resolved','rejected') DEFAULT 'open', admin_reply TEXT,
 created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
 INDEX idx_complaint_status(status), FOREIGN KEY(student_id) REFERENCES users(id) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS help_requests (
 id BIGINT AUTO_INCREMENT PRIMARY KEY, student_id INT NOT NULL, teacher_id INT, subject_id INT, message TEXT NOT NULL,
 status ENUM('open','answered','closed') DEFAULT 'open', reply TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
 FOREIGN KEY(student_id) REFERENCES users(id) ON DELETE CASCADE, FOREIGN KEY(teacher_id) REFERENCES users(id) ON DELETE SET NULL, FOREIGN KEY(subject_id) REFERENCES subjects(id) ON DELETE SET NULL
);
CREATE TABLE IF NOT EXISTS notifications (
 id BIGINT AUTO_INCREMENT PRIMARY KEY, user_id INT NULL, title VARCHAR(255) NOT NULL, message TEXT NOT NULL,
 kind VARCHAR(40) DEFAULT 'info', link VARCHAR(500), is_read TINYINT(1) DEFAULT 0, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
 INDEX idx_notif_user(user_id,is_read,created_at), FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS security_events (
 id BIGINT AUTO_INCREMENT PRIMARY KEY, user_id INT NULL, username VARCHAR(120), event_type VARCHAR(60) NOT NULL,
 ip_address VARCHAR(64), user_agent VARCHAR(500), created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
 INDEX idx_security_created(created_at), FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE SET NULL
);
CREATE TABLE IF NOT EXISTS password_resets (
 id BIGINT AUTO_INCREMENT PRIMARY KEY, user_id INT NOT NULL, token_hash VARCHAR(128) NOT NULL,
 expires_at DATETIME NOT NULL, used_at DATETIME NULL, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
 UNIQUE KEY uq_reset_token(token_hash), FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS otp_codes (
 id BIGINT AUTO_INCREMENT PRIMARY KEY, user_id INT NOT NULL, purpose VARCHAR(40) NOT NULL, code_hash VARCHAR(128) NOT NULL,
 expires_at DATETIME NOT NULL, attempts INT DEFAULT 0, used_at DATETIME NULL, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
 INDEX idx_otp_user(user_id,purpose,expires_at), FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS assignments (
 id BIGINT AUTO_INCREMENT PRIMARY KEY, title VARCHAR(255) NOT NULL, description TEXT, file_path VARCHAR(500), due_at DATETIME NULL,
 branch VARCHAR(80) NOT NULL, year_no INT NOT NULL, semester VARCHAR(30) NOT NULL, subject_id INT NOT NULL, created_by INT NOT NULL,
 created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, FOREIGN KEY(subject_id) REFERENCES subjects(id) ON DELETE CASCADE, FOREIGN KEY(created_by) REFERENCES users(id) ON DELETE CASCADE,
 INDEX idx_assignment_scope(branch,year_no,semester)
);
CREATE TABLE IF NOT EXISTS assignment_submissions (
 id BIGINT AUTO_INCREMENT PRIMARY KEY, assignment_id BIGINT NOT NULL, student_id INT NOT NULL, file_path VARCHAR(500),
 note TEXT, submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, marks DECIMAL(6,2) NULL, max_marks DECIMAL(6,2) DEFAULT 100, feedback TEXT,
 status ENUM('submitted','graded','late') DEFAULT 'submitted', UNIQUE KEY uq_submission(assignment_id,student_id),
 FOREIGN KEY(assignment_id) REFERENCES assignments(id) ON DELETE CASCADE, FOREIGN KEY(student_id) REFERENCES users(id) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS results (
 id BIGINT AUTO_INCREMENT PRIMARY KEY, student_id INT NOT NULL, subject_id INT NOT NULL, exam_type VARCHAR(80) NOT NULL,
 marks DECIMAL(7,2) NOT NULL, max_marks DECIMAL(7,2) NOT NULL DEFAULT 100, grade VARCHAR(10), remarks VARCHAR(255), published TINYINT(1) DEFAULT 1,
 created_by INT NULL, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
 UNIQUE KEY uq_result(student_id,subject_id,exam_type), FOREIGN KEY(student_id) REFERENCES users(id) ON DELETE CASCADE,
 FOREIGN KEY(subject_id) REFERENCES subjects(id) ON DELETE CASCADE, FOREIGN KEY(created_by) REFERENCES users(id) ON DELETE SET NULL
);
CREATE TABLE IF NOT EXISTS events (
 id BIGINT AUTO_INCREMENT PRIMARY KEY, title VARCHAR(255) NOT NULL, description TEXT, event_date DATE NOT NULL, start_time TIME NULL, end_time TIME NULL,
 venue VARCHAR(255), event_type VARCHAR(80) DEFAULT 'General', created_by INT NOT NULL, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
 FOREIGN KEY(created_by) REFERENCES users(id) ON DELETE CASCADE, INDEX idx_event_date(event_date)
);
CREATE TABLE IF NOT EXISTS notification_log (
 id BIGINT AUTO_INCREMENT PRIMARY KEY, user_id INT NULL, channel ENUM('email','whatsapp','sms') NOT NULL, recipient VARCHAR(255), subject VARCHAR(255), message TEXT,
 status VARCHAR(40) NOT NULL, error_message TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE SET NULL
);

-- Fresh-install feature tables. Everything below is part of the final schema.
CREATE TABLE IF NOT EXISTS infrastructure_images (
 id BIGINT AUTO_INCREMENT PRIMARY KEY,
 title VARCHAR(255) NOT NULL,
 file_path VARCHAR(500) NOT NULL,
 uploaded_by INT NOT NULL,
 created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
 FOREIGN KEY(uploaded_by) REFERENCES users(id) ON DELETE CASCADE
);
CREATE TABLE IF NOT EXISTS site_content (
 content_key VARCHAR(100) PRIMARY KEY,
 title VARCHAR(255), body TEXT,
 updated_by INT NULL,
 updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
 FOREIGN KEY(updated_by) REFERENCES users(id) ON DELETE SET NULL
);
CREATE TABLE IF NOT EXISTS tourism_places (
 id BIGINT AUTO_INCREMENT PRIMARY KEY,
 name VARCHAR(180) NOT NULL UNIQUE,
 description TEXT NOT NULL,
 image_path VARCHAR(500),
 address VARCHAR(500),
 source_url VARCHAR(500),
 sort_order INT DEFAULT 0
);

INSERT INTO site_content(content_key,title,body) VALUES
('about_college','Government Polytechnic College, Jaunpur','Government Polytechnic College, Jaunpur is a government technical education institute at Jagdishpur, Jaunpur, Uttar Pradesh. This portal presents student services, academics, attendance, events, digital identity and campus information in one place.'),
('admin_instagram','Admin Instagram','https://www.instagram.com/silent.killer_x_07?stkn=c3B3N2kybDIwb3p2'),
('admin_whatsapp','Admin WhatsApp','9935840560'),
('team_name','Team Name','DIGITAL DYNAMOS'),
('portal_login_image','Portal Login Image','/static/assets/login-cover.png'),
('portal_banner_image','Portal Banner Image','/static/assets/portal-banner.png')
ON DUPLICATE KEY UPDATE title=VALUES(title), body=VALUES(body);

INSERT IGNORE INTO tourism_places(name,description,image_path,address,source_url,sort_order) VALUES
('Shahi Qila','A historic fort in Jaunpur associated with the Sharqi period, known for its monumental gateways and river-side setting.','https://commons.wikimedia.org/wiki/Special:Redirect/file/FortJaunpur.jpg','Shahi Qila Road, Jaunpur, Uttar Pradesh 222001, India','https://commons.wikimedia.org/wiki/File:FortJaunpur.jpg',1),
('Atala Masjid','A landmark 15th-century mosque in Jaunpur and one of the best-known examples of the city’s Sharqi architectural heritage.','https://commons.wikimedia.org/wiki/Special:Redirect/file/Atala_Masjid_Jaunpur.JPG','Atala Masjid Road, Jaunpur, Uttar Pradesh 222001, India','https://commons.wikimedia.org/wiki/File:Atala_Masjid_Jaunpur.JPG',2),
('Shahi Bridge','The historic stone bridge over the Gomti is an iconic Jaunpur structure and a popular heritage/photo stop.','https://commons.wikimedia.org/wiki/Special:Redirect/file/Shahi_bridge.jpg','Shahi Bridge, Gomti River, Jaunpur, Uttar Pradesh 222001, India','https://commons.wikimedia.org/wiki/File:Shahi_bridge.jpg',3),
('Jama Masjid, Jaunpur','A grand historic mosque near the Shahi Qila complex, notable for its large gateway and medieval architecture.','https://commons.wikimedia.org/wiki/Special:Redirect/file/Jaunpur_Jama_Masjid.jpg','Jama Masjid, Shahi Qila area, Jaunpur, Uttar Pradesh 222001, India','https://commons.wikimedia.org/wiki/File:Jaunpur_Jama_Masjid.jpg',4),
('Lal Darwaza Masjid','A historic mosque in Jaunpur connected with the city’s Sharqi-era architectural landscape.','https://commons.wikimedia.org/wiki/Special:Redirect/file/Lal_Darwaza_Masjid_01.jpg','Lal Darwaza, Jaunpur, Uttar Pradesh 222001, India','https://commons.wikimedia.org/wiki/File:Lal_Darwaza_Masjid_01.jpg',5),
('Heritage Walk','A suggested old-city heritage walk connecting historic architecture, markets and Gomti-side landmarks.','https://commons.wikimedia.org/wiki/Special:Redirect/file/Shahi_bridge.jpg','Old Jaunpur heritage area, Jaunpur, Uttar Pradesh, India','https://commons.wikimedia.org/wiki/File:Shahi_bridge.jpg',6);
