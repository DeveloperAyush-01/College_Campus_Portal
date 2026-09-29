USE college_campus_portal_cloud;
ALTER TABLE tourism_places ADD COLUMN IF NOT EXISTS address VARCHAR(500) NULL AFTER image_path;
INSERT INTO site_content(content_key,title,body) VALUES
('admin_instagram','Admin Instagram','https://www.instagram.com/silent.killer_x_07?stkn=c3B3N2kybDIwb3p2'),
('admin_whatsapp','Admin WhatsApp','9935840560'),
('team_name','Team Name','DIGITAL DYNAMOS')
ON DUPLICATE KEY UPDATE body=VALUES(body),title=VALUES(title);
UPDATE tourism_places SET image_path='https://commons.wikimedia.org/wiki/Special:Redirect/file/FortJaunpur.jpg',address='Shahi Qila Road, Jaunpur, Uttar Pradesh 222001, India',source_url='https://commons.wikimedia.org/wiki/File:FortJaunpur.jpg' WHERE name='Shahi Qila';
UPDATE tourism_places SET image_path='https://commons.wikimedia.org/wiki/Special:Redirect/file/Atala_Masjid_Jaunpur.JPG',address='Atala Masjid Road, Jaunpur, Uttar Pradesh 222001, India',source_url='https://commons.wikimedia.org/wiki/File:Atala_Masjid_Jaunpur.JPG' WHERE name='Atala Masjid';
UPDATE tourism_places SET image_path='https://commons.wikimedia.org/wiki/Special:Redirect/file/Shahi_bridge.jpg',address='Shahi Bridge, Gomti River, Jaunpur, Uttar Pradesh 222001, India',source_url='https://commons.wikimedia.org/wiki/File:Shahi_bridge.jpg' WHERE name='Shahi Bridge';
UPDATE tourism_places SET image_path='https://commons.wikimedia.org/wiki/Special:Redirect/file/Jaunpur_Jama_Masjid.jpg',address='Jama Masjid, Shahi Qila area, Jaunpur, Uttar Pradesh 222001, India',source_url='https://commons.wikimedia.org/wiki/File:Jaunpur_Jama_Masjid.jpg' WHERE name='Jama Masjid, Jaunpur';
UPDATE tourism_places SET image_path='https://commons.wikimedia.org/wiki/Special:Redirect/file/Lal_Darwaza_Masjid_01.jpg',address='Lal Darwaza, Jaunpur, Uttar Pradesh 222001, India',source_url='https://commons.wikimedia.org/wiki/File:Lal_Darwaza_Masjid_01.jpg' WHERE name='Lal Darwaza Masjid';
UPDATE tourism_places SET image_path='https://commons.wikimedia.org/wiki/Special:Redirect/file/Shahi_bridge.jpg',address='Shahi Bridge, Gomti River, Jaunpur, Uttar Pradesh 222001, India',source_url='https://commons.wikimedia.org/wiki/File:Shahi_bridge.jpg' WHERE name LIKE '%Heritage Walk%';
