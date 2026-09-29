# FRESH DATABASE INSTALLATION

1. Open MySQL Workbench.
2. Run: DROP DATABASE IF EXISTS college_campus_portal_cloud;
3. Run: CREATE DATABASE college_campus_portal_cloud CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
4. Open schema.sql from this package and Execute All.
5. Do not run database_features.sql, upgrade.sql, UPGRADE_V7.sql, or otp_migration.sql for a brand-new database unless the README specifically asks for a migration.
6. After schema.sql completes without Error 1064/1065, continue to seed_data.py.
