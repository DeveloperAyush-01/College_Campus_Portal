# College Campus Portal

A standalone Flask + MySQL full-stack portal for Government Polytechnic College, Jaunpur. The website is branded **College Campus Portal** and is packaged as a separate project so it can run beside another local Flask portal without sharing its database or cookies.

## 1. What is included

- Student / Teacher / Admin authentication
- Real OTP delivery: Brevo email API, Gmail/SMTP fallback, Twilio SMS and Twilio WhatsApp
- OTP hashing, expiry, attempt limits and device binding
- Student search/edit, Teacher student edit
- Attendance search by name/roll/username + QR attendance
- Notes, notices, circulars, activities, timetable and forms with edit/delete controls
- Events with edit/delete controls
- Admin-only About College editing
- Admin-only shared login/banner image replacement/reset
- Infrastructure upload/remove + image zoom viewer
- PNG/PDF/print Student ID with QR verification
- Assignments, submissions, grading, results, complaints and notifications
- Jaunpur Tourism section
- Study search sources: NPTEL, SWAYAM, MIT OCW, Khan Academy, MDN, GeeksforGeeks
- Optional OpenAI-compatible model endpoint for a self-hosted/open-source LLM
- Render deployment configuration and health check

## 2. Local Windows setup

1. Install Python 3.12+ and MySQL 8+.
2. Extract this ZIP into a new folder, for example:
   `C:\College_Campus_Portal_Cloud`
3. Open VS Code in that folder.
4. Create a virtual environment:
   `python -m venv .venv`
5. Activate it:
   `.venv\Scripts\activate`
6. Install packages:
   `python -m pip install -r requirements.txt`
7. Copy `.env.example` to `.env` and set your MySQL password.
8. In MySQL run `schema.sql`.
9. Run `python seed_data.py`.
10. Start:
   `python portal.py`
11. Open:
   `http://127.0.0.1:5001`

## 3. Side-by-side with the older portal

The portal uses a separate default database: `college_campus_portal_cloud`, a separate session cookie: `college_campus_portal_session_v3`, a separate device cookie: `college_portal_device`, and local port `5001`. The older portal can continue on its own port/database. MySQL itself can remain on port `3306`; different databases are enough for isolation.

## 4. Demo credentials

- Admin: `admin` / `Admin@123`
- Teachers: `teacher01` … `teacher31` / `Teacher@123`
- Seeded students: `Student@123`

Change demo passwords before public use.

## 5. Real email OTP on Render

Render Free web services can be unable to send outbound SMTP on ports commonly used for SMTP. Therefore this project supports Brevo's HTTPS transactional-email API as the preferred cloud method. Create a Brevo account, verify the sender, create an SMTP/API key, and set `BREVO_API_KEY` plus `SMTP_FROM` in Render Environment Variables. The app calls Brevo over HTTPS.

For local Gmail SMTP instead, use a Gmail App Password rather than the normal Gmail password and configure `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`, and `SMTP_FROM`.

## 6. Real SMS + WhatsApp OTP

Create a Twilio account and configure `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, and either `TWILIO_SMS_FROM` or `TWILIO_MESSAGING_SERVICE_SID`. For WhatsApp configure `TWILIO_WHATSAPP_FROM`. During Twilio trial, only verified recipient numbers can receive test messages. Production WhatsApp/SMS requires the provider's required sender/compliance setup.

## 7. Render deployment — recommended

### A. Create the GitHub repository
1. Create a new GitHub repository named `college-campus-portal`.
2. Upload all files from this project folder. Do not upload `.env`.
3. Commit and push to `main`.

### B. Create the database
The application is MySQL-based. Render documents that a custom MySQL service can be run on Render with a persistent disk, but that is not the same as Render's free managed Postgres offering. For a genuinely free web-service test, use a MySQL-compatible external provider that gives you a free plan/credits, or use a paid/persistent Render MySQL service. Put its host, user, password, port and database name into Render Environment Variables.

### C. Deploy the Flask web service
1. Open Render Dashboard.
2. `New` → `Web Service`.
3. Connect the GitHub repository.
4. Service name: `college-campus-portal` (the website itself displays **College Campus Portal**).
5. Runtime: Python.
6. Build Command: `pip install -r requirements.txt`.
7. Start Command: `gunicorn portal:app --workers 2 --threads 4 --timeout 120`.
8. Health Check Path: `/healthz`.
9. Choose Free for testing if available in your workspace.
10. Add Environment Variables from `.env.example`.
11. Deploy.

### D. Initialize the cloud database
Run the SQL in your cloud MySQL console: `schema.sql`, then run `python seed_data.py` locally with the cloud DB variables OR import the seeded database using your database provider's SQL console.

### E. Public URL
Render gives the service a public `onrender.com` URL and supports custom domains. The service should be opened only after the database and environment variables are configured.

## 8. Vercel / Railway

**Vercel:** Flask can run on Vercel's Python runtime, but this project has persistent uploads, MySQL and long-lived server behavior, so Render/Railway is the simpler deployment target.

**Railway:** Railway directly supports Flask, GitHub deployment and MySQL-style database services. Use the same `gunicorn portal:app` start command and environment variables.

## 9. Important cloud-storage note

A free web service may have an ephemeral filesystem. Uploaded notes/images should therefore not be treated as permanent cloud storage unless you attach persistent storage or move uploads to an object-storage service. The database stores the file path, while the application currently saves files locally. For a public production deployment, use persistent disk/object storage for uploaded media.

## 10. Admin controls

After logging in as Admin, open Management. You will find:
- Student/User Search and Edit
- User activation and device reset
- About College Edit
- Shared Login/Banner Image Replace/Reset
- Event Edit/Delete
- Note/Notice/Activity Edit/Delete
- Infrastructure management

## 11. Contact

Developer/contact phone: **9935840560**. The same number can be used for WhatsApp delivery after it is configured as an approved WhatsApp sender/recipient according to the provider rules.

Instagram: `https://www.instagram.com/silent.killer_x_07?stkn=c3B3N2kybDIwb3p2`

## 12. Security checklist before public launch

- Replace all demo passwords.
- Generate a long random `SECRET_KEY`.
- Configure real email/SMS/WhatsApp OTP and disable demo mode by verifying delivery.
- Use HTTPS (`SESSION_COOKIE_SECURE=1`).
- Do not commit `.env` or provider secrets.
- Use persistent/object storage for uploads.
- Back up MySQL.
- Test Admin/Teacher permissions before sharing the URL.


## V7 UI and management upgrades
- Team branding: DIGITAL DYNAMOS with styled gradient typography.
- Admin contact management for Instagram, WhatsApp and team name.
- Account Settings for all roles.
- Admin-only permanent deletion of teacher/student accounts.
- Teacher help-request detail/reply workflow from notification links.
- Teacher attendance record deletion with permission checks.
- Student assignment uploads explicitly support PDF/images and common document formats.
- Jaunpur Tourism cards include location addresses, map links and Wikimedia Commons open-source image references.
- Wikimedia image licenses are retained on the source/reference links; verify attribution requirements before public redistribution.
- For an existing database, run `UPGRADE_V7.sql` once before using the new tourism address/contact fields. For a completely fresh install, use `00_FRESH_INSTALL_DROP_OLD_DB.sql`, then `schema.sql`; see `FRESH_INSTALL_RENDER_NO_AIVEN.md`.


### Database provider note
This project has no Aiven dependency. Render only needs the MySQL connection values in Environment Variables (`MYSQL_HOST`, `MYSQL_PORT`, `MYSQL_USER`, `MYSQL_PASSWORD`, `MYSQL_DATABASE`).
