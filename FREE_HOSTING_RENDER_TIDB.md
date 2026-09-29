# Free Hosting Guide — Render + TiDB Cloud Starter

This project is a Flask + MySQL-compatible application. For a free test deployment, use:

- **Render Free Web Service** for Flask.
- **TiDB Cloud Starter** for the MySQL-compatible database.

Render's Free web service can run Python apps, but its free datastore offering is Postgres rather than managed MySQL. This project uses MySQL Connector/Python and a MySQL schema, so TiDB Cloud Starter is the practical free MySQL-compatible option.

## 1. Push the project to GitHub

Upload the contents of this project folder to a GitHub repository. Do **not** upload `.env` or any real passwords/API keys.

## 2. Create the free TiDB Cloud database

1. Create a TiDB Cloud Starter instance.
2. Keep the spending limit at `0` if you want to remain within the free quota.
3. Enable the public endpoint.
4. Create/set the database password.
5. From **Connect**, copy the host, port, username and database name.
6. Run `schema.sql` in the TiDB SQL Editor.
7. Run `seed_data.py` only after the database connection variables are configured locally, or import the required seed SQL/data using the database console.

## 3. Create the Render Web Service

Use these values:

- Runtime: **Python 3**
- Build Command: `pip install -r requirements.txt`
- Start Command: `gunicorn portal:app --workers 1 --threads 4 --timeout 120`
- Health Check Path: `/healthz`
- Plan: **Free**

## 4. Add Render Environment Variables

Set these from the TiDB connection dialog:

```text
SECRET_KEY=<long-random-secret>
MYSQL_HOST=<tidb-host>
MYSQL_PORT=4000
MYSQL_USER=<tidb-user>
MYSQL_PASSWORD=<tidb-password>
MYSQL_DATABASE=<tidb-database>
MYSQL_SSL_VERIFY=1
MYSQL_SSL_IDENTITY=1
MYSQL_SSL_CA=/etc/ssl/certs/ca-certificates.crt
SESSION_COOKIE_SECURE=1
```

For OTP email on Render Free, configure the Brevo HTTPS API variables from `.env.example`; SMTP ports 25/465/587 are restricted on Render Free.

## 5. Important free-tier limitation

Render Free web services use an ephemeral filesystem. Uploaded files/images saved inside `uploads/` can disappear after a restart, redeploy or spin-down. The database remains external, but uploaded media should eventually be moved to object storage or another persistent storage solution if the portal is used seriously.

## 6. First login and testing

After deployment:

1. Open the generated `https://<your-service>.onrender.com` URL.
2. Check `/healthz` first.
3. Test login, Management, About College, events, complaints, attendance and ID-card pages.
4. Change all demo passwords before sharing the public URL.

## 7. Updating the website later

Push the updated files to the connected GitHub branch. Render automatically creates a new deployment from the latest commit. Keep database schema changes separate and run the required SQL migration before using new database fields.
