CREATE DATABASE IF NOT EXISTS college_campus_portal_cloud CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE college_campus_portal_cloud;

-- Run schema.sql first. This migration adds the new V2 feature tables/columns.
ALTER TABLE notification_log MODIFY COLUMN channel ENUM('email','whatsapp','sms') NOT NULL;
ALTER TABLE users ADD COLUMN IF NOT EXISTS device_hash VARCHAR(128);
ALTER TABLE users ADD COLUMN IF NOT EXISTS profile_image VARCHAR(255);

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
 source_url VARCHAR(500),
 sort_order INT DEFAULT 0
);

INSERT INTO site_content(content_key,title,body) VALUES
('about_college','Government Polytechnic College, Jaunpur','Government Polytechnic College, Jaunpur is a government technical education institute at Jagdishpur, Jaunpur, Uttar Pradesh. This portal presents student services, academics, attendance, events, digital identity and campus information in one place.')
ON DUPLICATE KEY UPDATE title=VALUES(title);

INSERT IGNORE INTO tourism_places(name,description,image_path,source_url,sort_order) VALUES
('Shahi Qila','A historic fort in Jaunpur associated with the Sharqi period, known for its monumental gateways and river-side setting.','/static/assets/tourism/shahi-qila.jpg','https://en.wikipedia.org/wiki/Shahi_Fort,_Jaunpur',1),
('Atala Masjid','A landmark 15th-century mosque in Jaunpur and one of the best-known examples of the city’s Sharqi architectural heritage.','/static/assets/tourism/atala-masjid.jpg','https://en.wikipedia.org/wiki/Atala_Masjid',2),
('Shahi Bridge','The historic stone bridge over the Gomti is an iconic Jaunpur structure and a popular heritage/photo stop.','/static/assets/tourism/shahi-bridge.jpg','https://en.wikipedia.org/wiki/Shahi_Bridge',3),
('Jama Masjid, Jaunpur','A grand historic mosque near the Shahi Qila complex, notable for its large gateway and medieval architecture.','/static/assets/tourism/jama-masjid.jpg','https://en.wikipedia.org/wiki/Jama_Masjid,_Jaunpur',4),
('Lal Darwaza Masjid','A historic mosque in Jaunpur connected with the city’s Sharqi-era architectural landscape.','/static/assets/tourism/lal-darwaza-masjid.jpg','https://en.wikipedia.org/wiki/Lal_Darwaza_Masjid',5),
('Atripatra / Heritage Walk','A campus-friendly local heritage exploration idea covering old-city architecture, markets and Gomti-side landmarks.','/static/assets/tourism/heritage-walk.jpg','https://en.wikipedia.org/wiki/Jaunpur,_Uttar_Pradesh',6);

