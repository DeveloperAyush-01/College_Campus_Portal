# Fresh Installation — College Campus Portal (Render, no Aiven)

This package does **not** require Aiven. The app is Flask + MySQL and uses the `MYSQL_*` environment variables, so you can connect Render to any MySQL-compatible cloud database you actually create.

## Step 1 — Drop the old local database
Open MySQL:

```sql
DROP DATABASE IF EXISTS college_campus_portal_cloud;
```

Or open `00_FRESH_INSTALL_DROP_OLD_DB.sql` in MySQL Workbench and execute it.

> This is destructive. Do this only if you want a completely fresh local installation.

## Step 2 — Create a fresh database

```sql
CREATE DATABASE college_campus_portal_cloud CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE college_campus_portal_cloud;
```

## Step 3 — Import the project schema
Run `schema.sql` in the new database.

## Step 4 — Seed demo/admin data
Copy `.env.example` to `.env`, put your local MySQL password in `MYSQL_PASSWORD`, then run:

```bash
python seed_data.py
```

## Step 5 — Run locally first

```bash
python portal.py
```

Open `http://127.0.0.1:5001`.

## Step 6 — Render deployment
Push this project to GitHub and deploy the web service on Render with:

```text
Build: pip install -r requirements.txt
Start: gunicorn portal:app --workers 2 --threads 4 --timeout 120
Health: /healthz
```

### Database
Render needs a reachable MySQL-compatible cloud database. **Do not put `your-mysql-host` in production.** In Render → Environment add:

- `MYSQL_HOST`
- `MYSQL_PORT` = `3306`
- `MYSQL_USER`
- `MYSQL_PASSWORD`
- `MYSQL_DATABASE` = `college_campus_portal_cloud`
- `SECRET_KEY` (strong random value)
- `SESSION_COOKIE_SECURE` = `1`

The project has no Aiven-specific code.

### Important
Do not run local `schema.sql` against the cloud database unless you intend to initialize that cloud database. For a brand-new Render database, import `schema.sql` once, then run `seed_data.py` with the cloud database variables if you want the demo/admin data.


## Latest fixes
- AI Assistant is removed from the UI and application route.
- Student photo upload + teacher-only student ID editing.
- Student camera QR attendance.
- Teacher quick actions for Attendance, Assignments and Publish.
- Teacher resource edit/delete and assignment validation.
- Student submission status and file preservation on updates.
- Admin bulk OTP-device reset with Select All/Clear All.
- Automatic current date/day display.
