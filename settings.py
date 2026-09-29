import os
from dotenv import load_dotenv

load_dotenv()

class PortalSettings:
    SECRET_KEY = os.getenv("SECRET_KEY", "replace-me-before-production")
    MYSQL_HOST = os.getenv("MYSQL_HOST", "127.0.0.1")
    MYSQL_PORT = int(os.getenv("MYSQL_PORT", "3306"))
    MYSQL_USER = os.getenv("MYSQL_USER", "root")
    MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "")
    MYSQL_DATABASE = os.getenv("MYSQL_DATABASE", "college_campus_portal_cloud")
    MAX_CONTENT_LENGTH = int(os.getenv("MAX_CONTENT_LENGTH", str(16 * 1024 * 1024)))
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_NAME = os.getenv("SESSION_COOKIE_NAME", "college_campus_portal_session_v3")
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = os.getenv("SESSION_COOKIE_SECURE", "0") == "1"
    PERMANENT_SESSION_LIFETIME = 60 * 60 * 8

    # Email: Brevo API is preferred on free hosts because HTTPS works where
    # outbound SMTP ports may be restricted. SMTP remains available locally.
    BREVO_API_KEY = os.getenv("BREVO_API_KEY", "")
    SMTP_HOST = os.getenv("SMTP_HOST", "")
    SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USER = os.getenv("SMTP_USER", "")
    SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
    SMTP_FROM = os.getenv("SMTP_FROM", os.getenv("SMTP_USER", ""))
    SMTP_FROM_NAME = os.getenv("SMTP_FROM_NAME", "College Campus Portal")

    TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID", "")
    TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN", "")
    TWILIO_SMS_FROM = os.getenv("TWILIO_SMS_FROM", "")
    TWILIO_MESSAGING_SERVICE_SID = os.getenv("TWILIO_MESSAGING_SERVICE_SID", "")
    TWILIO_WHATSAPP_FROM = os.getenv("TWILIO_WHATSAPP_FROM", "")


    PORTAL_DISPLAY_NAME = "College Campus Portal"
    PORTAL_DEVELOPER = "AYUSH KUMAR PATEL"
    PORTAL_INSTAGRAM = "https://www.instagram.com/silent.killer_x_07?stkn=c3B3N2kybDIwb3p2"
    PORTAL_PHONE = "9935840560"
