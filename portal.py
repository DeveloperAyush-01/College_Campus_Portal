import os, hashlib, secrets, datetime as dt, time, smtplib, socket, uuid
from email.message import EmailMessage
from functools import wraps
from pathlib import Path
from collections import defaultdict
from urllib.parse import quote
import json, re
import mysql.connector
import qrcode
import requests
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify, send_from_directory, abort
from werkzeug.utils import secure_filename
from werkzeug.security import check_password_hash, generate_password_hash
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas as pdf_canvas
from PIL import Image, ImageDraw, ImageFont
from settings import PortalSettings
from seed_data import TEACHERS, CSE, ELECTRONICS, PHARMACY

app = Flask(__name__)
app.config.from_object(PortalSettings)
BASE = Path(__file__).resolve().parent
UPLOAD_DIRS = {"note": BASE/"uploads/notes", "notice": BASE/"uploads/notices", "timetable": BASE/"uploads/notices", "circular": BASE/"uploads/notices", "activity": BASE/"uploads/notices", "form": BASE/"uploads/forms", "assignment": BASE/"uploads/assignments", "profile": BASE/"uploads/profiles", "infrastructure": BASE/"uploads/infrastructure"}
for p in UPLOAD_DIRS.values(): p.mkdir(parents=True, exist_ok=True)
(BASE/"static/qr").mkdir(parents=True, exist_ok=True)
ALLOWED = {"pdf","png","jpg","jpeg","webp","doc","docx","ppt","pptx","txt","zip"}
LOGIN_BUCKET = defaultdict(list)
V7_SCHEMA_READY = False


def db():
    # Build the connection from environment-backed settings so the same app
    # works with local MySQL and MySQL-compatible cloud databases such as TiDB Cloud.
    cfg = {
        "host": app.config["MYSQL_HOST"],
        "port": app.config["MYSQL_PORT"],
        "user": app.config["MYSQL_USER"],
        "password": app.config["MYSQL_PASSWORD"],
        "database": app.config["MYSQL_DATABASE"],
    }
    # TiDB Cloud Starter requires TLS for public connections. These options are
    # optional, so ordinary local MySQL continues to work unchanged.
    if os.getenv("MYSQL_SSL_VERIFY", "0") == "1":
        cfg["ssl_verify_cert"] = True
        cfg["ssl_verify_identity"] = os.getenv("MYSQL_SSL_IDENTITY", "1") == "1"
        ca_path = os.getenv("MYSQL_SSL_CA", "").strip()
        if ca_path:
            cfg["ssl_ca"] = ca_path
    return mysql.connector.connect(**cfg)

def _db_args(args):
    if args is None: return ()
    if isinstance(args, (tuple, list, dict)): return args
    return (args,)

def one(sql,args=()):
    c=db(); cur=c.cursor(dictionary=True)
    try:
        cur.execute(sql,_db_args(args)); return cur.fetchone()
    finally:
        cur.close(); c.close()

def many(sql,args=()):
    c=db(); cur=c.cursor(dictionary=True)
    try:
        cur.execute(sql,_db_args(args)); return cur.fetchall()
    finally:
        cur.close(); c.close()

def execute(sql,args=()):
    c=db(); cur=c.cursor(); cur.execute(sql,args); c.commit(); last=cur.lastrowid; cur.close(); c.close(); return last

def client_ip(): return request.headers.get("X-Forwarded-For", request.remote_addr or "unknown").split(",")[0].strip()

def local_lan_host():
    override=os.getenv("LAN_HOST", "").strip()
    if override: return override
    host=request.host.split(":",1)[0]
    if host and host not in {"127.0.0.1","localhost","0.0.0.0"} and not host.startswith("::"):
        return host
    try:
        sock=socket.socket(socket.AF_INET,socket.SOCK_DGRAM); sock.connect(("8.8.8.8",80)); ip=sock.getsockname()[0]; sock.close(); return ip
    except Exception:
        try: return socket.gethostbyname(socket.gethostname())
        except Exception: return "127.0.0.1"

def make_lan_url(endpoint, **values):
    port=int(os.getenv("PORT","5001")); return f"http://{local_lan_host()}:{port}"+url_for(endpoint, **values)

def current_device_token():
    token=request.cookies.get("college_portal_device")
    return token or uuid.uuid4().hex+uuid.uuid4().hex

def device_hash(token): return hashlib.sha256((token+app.config["SECRET_KEY"]).encode()).hexdigest()

def bind_device(user_id):
    """Bind the successful OTP login to the current browser/device.
    Returns (ok, token).  Missing/deleted users are handled safely instead
    of causing an HTTP 500 on the OTP verification page.
    """
    token = current_device_token()
    h = device_hash(token)
    u = one("SELECT id, device_hash FROM users WHERE id=%s", (user_id,))
    if not u:
        return False, None
    saved = u.get("device_hash")
    if saved and not secrets.compare_digest(str(saved), h):
        return False, None
    if not saved:
        execute("UPDATE users SET device_hash=%s WHERE id=%s", (h, user_id))
    return True, token

def security_event(event_type, user_id=None, username=None):
    try: execute("INSERT INTO security_events(user_id,username,event_type,ip_address,user_agent) VALUES(%s,%s,%s,%s,%s)",(user_id,username,event_type,client_ip(),request.headers.get("User-Agent","")[:500]))
    except Exception: pass

def ensure_v7_schema():
    """Small self-healing migration for existing local databases."""
    global V7_SCHEMA_READY
    if V7_SCHEMA_READY: return
    try:
        c=db(); cur=c.cursor()
        cur.execute("SELECT COUNT(*) FROM information_schema.columns WHERE table_schema=%s AND table_name='tourism_places' AND column_name='address'",(app.config["MYSQL_DATABASE"],))
        if not cur.fetchone()[0]:
            cur.execute("ALTER TABLE tourism_places ADD COLUMN address VARCHAR(500) NULL AFTER image_path")
        rows=[
            ("admin_instagram","Admin Instagram",DEFAULT_INSTAGRAM),
            ("admin_whatsapp","Admin WhatsApp",DEFAULT_WHATSAPP),
            ("team_name","Team Name",TEAM_NAME),
        ]
        for key,title,body in rows:
            cur.execute("INSERT INTO site_content(content_key,title,body) VALUES(%s,%s,%s) ON DUPLICATE KEY UPDATE title=VALUES(title),body=VALUES(body)",(key,title,body))
        tourism=[
            ("Shahi Qila","https://commons.wikimedia.org/wiki/Special:Redirect/file/FortJaunpur.jpg","Shahi Qila Road, Jaunpur, Uttar Pradesh 222001, India","https://commons.wikimedia.org/wiki/File:FortJaunpur.jpg"),
            ("Atala Masjid","https://commons.wikimedia.org/wiki/Special:Redirect/file/Atala_Masjid_Jaunpur.JPG","Atala Masjid Road, Jaunpur, Uttar Pradesh 222001, India","https://commons.wikimedia.org/wiki/File:Atala_Masjid_Jaunpur.JPG"),
            ("Shahi Bridge","https://commons.wikimedia.org/wiki/Special:Redirect/file/Shahi_bridge.jpg","Shahi Bridge, Gomti River, Jaunpur, Uttar Pradesh 222001, India","https://commons.wikimedia.org/wiki/File:Shahi_bridge.jpg"),
            ("Jama Masjid, Jaunpur","https://commons.wikimedia.org/wiki/Special:Redirect/file/Jaunpur_Jama_Masjid.jpg","Jama Masjid, Shahi Qila area, Jaunpur, Uttar Pradesh 222001, India","https://commons.wikimedia.org/wiki/File:Jaunpur_Jama_Masjid.jpg"),
            ("Lal Darwaza Masjid","https://commons.wikimedia.org/wiki/Special:Redirect/file/Lal_Darwaza_Masjid_01.jpg","Lal Darwaza, Jaunpur, Uttar Pradesh 222001, India","https://commons.wikimedia.org/wiki/File:Lal_Darwaza_Masjid_01.jpg"),
            ("Heritage Walk","https://commons.wikimedia.org/wiki/Special:Redirect/file/Shahi_bridge.jpg","Old Jaunpur heritage area, Jaunpur, Uttar Pradesh, India","https://commons.wikimedia.org/wiki/File:Shahi_bridge.jpg"),
        ]
        for name,image,address,source in tourism:
            cur.execute("UPDATE tourism_places SET image_path=%s,address=%s,source_url=%s WHERE name=%s",(image,address,source,name))
        c.commit(); cur.close(); c.close(); V7_SCHEMA_READY=True
    except Exception:
        try: cur.close(); c.close()
        except Exception: pass

def csrf_token():
    if "csrf" not in session: session["csrf"] = secrets.token_urlsafe(24)
    return session["csrf"]

def media_path(key, default):
    """Return an admin-managed portal image path or its bundled default."""
    try:
        row=one("SELECT body FROM site_content WHERE content_key=%s", (key,))
        return (row.get("body") or default) if row else default
    except Exception:
        return default

def site_value(key, default=""):
    try:
        row=one("SELECT body FROM site_content WHERE content_key=%s", (key,))
        return (row.get("body") or default) if row else default
    except Exception:
        return default

TEAM_NAME = "DIGITAL DYNAMOS"
DEFAULT_INSTAGRAM = "https://www.instagram.com/silent.killer_x_07?stkn=c3B3N2kybDIwb3p2"
DEFAULT_WHATSAPP = "9935840560"

def whatsapp_url(number):
    digits="".join(ch for ch in str(number or "") if ch.isdigit())
    if len(digits)==10: digits="91"+digits
    return "https://wa.me/"+digits if digits else "#"

def validate_csrf():
    if request.method in {"POST","PUT","PATCH","DELETE"}:
        # Login/OTP forms are additionally protected by password/OTP, rate limiting and session state.
        # Exempting them avoids stale-CSRF failures after a local server restart or host/IP change.
        if request.endpoint in {"login", "verify_login_otp"}: return
        token=request.form.get("csrf_token") or request.headers.get("X-CSRFToken")
        expected=session.get("csrf","")
        if not token or not expected or not secrets.compare_digest(token, expected): abort(400,"Invalid CSRF token. Refresh the page and try again.")

@app.before_request
def before_request():
    ensure_v7_schema()
    # Never mark cookies Secure on plain HTTP LAN testing. This fixes sessions/CSRF when opening
    # http://192.168.x.x:PORT from a phone; HTTPS production remains Secure when configured.
    if not request.is_secure:
        app.config["SESSION_COOKIE_SECURE"] = False
    elif os.getenv("SESSION_COOKIE_SECURE", "0") == "1":
        app.config["SESSION_COOKIE_SECURE"] = True
    validate_csrf()

@app.context_processor
def inject():
    uid=session.get("user_id")
    user=one("SELECT * FROM users WHERE id=%s",(uid,)) if uid else None
    unread=one("SELECT COUNT(*) c FROM notifications WHERE user_id=%s AND is_read=0",(uid,))["c"] if uid else 0
    instagram=site_value("admin_instagram", DEFAULT_INSTAGRAM) or DEFAULT_INSTAGRAM
    whatsapp=site_value("admin_whatsapp", DEFAULT_WHATSAPP) or DEFAULT_WHATSAPP
    team=site_value("team_name", TEAM_NAME) or TEAM_NAME
    today=dt.date.today()
    return {"current_user":user,"unread_notifications":unread,"csrf_token":csrf_token(),
            "today_date":today.strftime("%d-%m-%Y"),"today_iso":today.isoformat(),"today_day":today.strftime("%A"),
            "portal_name":"College Campus Portal",
            "portal_developer":app.config.get("PORTAL_DEVELOPER"),
            "portal_instagram":instagram,
            "portal_phone":whatsapp,
            "portal_whatsapp_url":whatsapp_url(whatsapp),
            "team_name":team,
            "portal_media":{
                "login":media_path("portal_login_image","/static/assets/login-cover.png"),
                "banner":media_path("portal_banner_image","/static/assets/portal-banner.png")}}

def login_required(role=None):
    def deco(fn):
        @wraps(fn)
        def wrapper(*a,**kw):
            if not session.get("user_id"): return redirect(url_for("login",next=request.path))
            if role and session.get("role")!=role: return redirect(url_for("dashboard"))
            return fn(*a,**kw)
        return wrapper
    return deco

def notify(user_id,title,message,kind="info",link=None): execute("INSERT INTO notifications(user_id,title,message,kind,link) VALUES(%s,%s,%s,%s,%s)",(user_id,title,message,kind,link))
def notify_many(user_ids,title,message,kind="info",link=None):
    for uid in set(user_ids): notify(uid,title,message,kind,link)

def attendance_pct(student_id,subject_id=None):
    if subject_id: r=one("SELECT COALESCE(ROUND(100*SUM(status='present')/NULLIF(COUNT(*),0),1),0) pct FROM attendance WHERE student_id=%s AND subject_id=%s",(student_id,subject_id))
    else: r=one("SELECT COALESCE(ROUND(100*SUM(status='present')/NULLIF(COUNT(*),0),1),0) pct FROM attendance WHERE student_id=%s",(student_id,))
    return float(r["pct"] or 0)

def create_low_attendance_notifications(student_id,subject_id):
    pct=attendance_pct(student_id,subject_id)
    if pct<75:
        s=one("SELECT subject_name FROM subjects WHERE id=%s",(subject_id,))
        recent=one("SELECT id FROM notifications WHERE user_id=%s AND kind='attendance' AND message LIKE %s AND created_at>=NOW()-INTERVAL 3 DAY LIMIT 1",(student_id,f"%{s['subject_name']}%"))
        if not recent: notify(student_id,"Attendance below 75%",f"Your attendance in {s['subject_name']} is {pct}%. Please attend upcoming classes.","attendance",url_for("student_dashboard")+"#attendance")

def send_email(to,subject,body,user_id=None):
    if not to: return False,"No email address"
    # Preferred for Render/Vercel-style hosts: HTTPS API, no SMTP port required.
    brevo=app.config.get("BREVO_API_KEY","").strip()
    sender=app.config.get("SMTP_FROM","").strip()
    if brevo and sender:
        try:
            payload={"sender":{"email":sender,"name":app.config.get("SMTP_FROM_NAME","College Campus Portal")},"to":[{"email":to}],"subject":subject,"textContent":body}
            r=requests.post("https://api.brevo.com/v3/smtp/email",headers={"api-key":brevo,"accept":"application/json","content-type":"application/json"},json=payload,timeout=15)
            if r.ok:
                if user_id: execute("INSERT INTO notification_log(user_id,channel,recipient,subject,message,status) VALUES(%s,'email',%s,%s,%s,'sent')",(user_id,to,subject,body))
                return True,"sent"
        except Exception:
            pass
    if not (app.config["SMTP_HOST"] and app.config["SMTP_USER"] and app.config["SMTP_PASSWORD"]):
        if user_id: execute("INSERT INTO notification_log(user_id,channel,recipient,subject,message,status) VALUES(%s,'email',%s,%s,%s,'not_configured')",(user_id,to,subject,body))
        return False,"Email provider is not configured"
    try:
        msg=EmailMessage(); msg["Subject"]=subject; msg["From"]=app.config["SMTP_FROM"]; msg["To"]=to; msg.set_content(body)
        with smtplib.SMTP(app.config["SMTP_HOST"],app.config["SMTP_PORT"],timeout=15) as server:
            server.starttls(); server.login(app.config["SMTP_USER"],app.config["SMTP_PASSWORD"]); server.send_message(msg)
        if user_id: execute("INSERT INTO notification_log(user_id,channel,recipient,subject,message,status) VALUES(%s,'email',%s,%s,%s,'sent')",(user_id,to,subject,body))
        return True,"sent"
    except Exception as e:
        if user_id: execute("INSERT INTO notification_log(user_id,channel,recipient,subject,message,status,error_message) VALUES(%s,'email',%s,%s,%s,'failed',%s)",(user_id,to,subject,body,str(e)[:500]))
        return False,str(e)

def normalize_twilio_phone(to):
    value=str(to or "").strip()
    digits="".join(ch for ch in value if ch.isdigit())
    if len(digits)==10: return "+91"+digits
    if value.startswith("+"): return "+"+digits
    return "+"+digits if digits else value

def send_sms(to,body,user_id=None):
    to=normalize_twilio_phone(to)
    sid,token,from_no,service=app.config["TWILIO_ACCOUNT_SID"],app.config["TWILIO_AUTH_TOKEN"],app.config.get("TWILIO_SMS_FROM",""),app.config.get("TWILIO_MESSAGING_SERVICE_SID","")
    if not (sid and token and to and (from_no or service)):
        if user_id: execute("INSERT INTO notification_log(user_id,channel,recipient,subject,message,status) VALUES(%s,'sms',%s,'',%s,'not_configured')",(user_id,to or "",body))
        return False,"Twilio SMS is not configured"
    try:
        data={"To":str(to)}
        if service: data["MessagingServiceSid"]=service
        else: data["From"]=from_no
        data["Body"]=body
        r=requests.post(f"https://api.twilio.com/2010-04-01/Accounts/{sid}/Messages.json",auth=(sid,token),data=data,timeout=15); r.raise_for_status()
        if user_id: execute("INSERT INTO notification_log(user_id,channel,recipient,subject,message,status) VALUES(%s,'sms',%s,'',%s,'sent')",(user_id,to,body))
        return True,"sent"
    except Exception as e:
        if user_id: execute("INSERT INTO notification_log(user_id,channel,recipient,subject,message,status,error_message) VALUES(%s,'sms',%s,'',%s,'failed',%s)",(user_id,to,body,str(e)[:500]))
        return False,str(e)

def send_whatsapp(to,body,user_id=None):
    sid,token,from_no=app.config["TWILIO_ACCOUNT_SID"],app.config["TWILIO_AUTH_TOKEN"],app.config["TWILIO_WHATSAPP_FROM"]
    if not (sid and token and from_no and to):
        if user_id: execute("INSERT INTO notification_log(user_id,channel,recipient,subject,message,status) VALUES(%s,'whatsapp',%s,'',%s,'not_configured')",(user_id,to or "",body))
        return False,"Twilio WhatsApp is not configured"
    phone=normalize_twilio_phone(to)
    to=to if str(to).startswith("whatsapp:") else "whatsapp:"+phone
    try:
        r=requests.post(f"https://api.twilio.com/2010-04-01/Accounts/{sid}/Messages.json",auth=(sid,token),data={"From":from_no,"To":to,"Body":body},timeout=15); r.raise_for_status()
        if user_id: execute("INSERT INTO notification_log(user_id,channel,recipient,subject,message,status) VALUES(%s,'whatsapp',%s,'',%s,'sent')",(user_id,to,body))
        return True,"sent"
    except Exception as e:
        if user_id: execute("INSERT INTO notification_log(user_id,channel,recipient,subject,message,status,error_message) VALUES(%s,'whatsapp',%s,'',%s,'failed',%s)",(user_id,to,body,str(e)[:500]))
        return False,str(e)

def send_user_alert(user,title,message,kind="info",link=None,external=False):
    notify(user["id"],title,message,kind,link)
    if external:
        send_email(user.get("email"),title,message,user["id"])
        send_whatsapp(user.get("phone"),message,user["id"])

def save_upload(file_obj,kind):
    if not file_obj or not file_obj.filename: return None,None
    ext=file_obj.filename.rsplit(".",1)[-1].lower() if "." in file_obj.filename else ""
    if ext not in ALLOWED: raise ValueError("Unsupported file type.")
    filename=f"{secrets.token_hex(6)}_{secure_filename(file_obj.filename)}"; folder=UPLOAD_DIRS[kind]; file_obj.save(folder/filename)
    sub={"note":"notes","notice":"notices","timetable":"notices","circular":"notices","activity":"notices","form":"forms","assignment":"assignments","profile":"profiles", "infrastructure":"infrastructure"}[kind]
    return f"/uploads/{sub}/{filename}",file_obj.mimetype

FACULTY_META={name:{"designation":designation,"qualification":qualification,"email":email,"department":dept} for name,designation,qualification,email,dept in TEACHERS}
GALLERY=[{"file":"campus-front-sunset.jpg","title":"Main College Building"},{"file":"campus-main-green.jpg","title":"Green Campus & Academic Block"},{"file":"campus-entry.jpg","title":"College Entrance"},{"file":"campus-garden.jpg","title":"Campus Garden Courtyard"},{"file":"computer-lab.jpg","title":"Computer Laboratory"}]
CAMPUS_PAGES={"college":("College","About Government Polytechnic College, Jaunpur and its programmes."),"faculty":("Faculty","Faculty and staff directory for the College Campus Portal."),"facilities":("Facilities","Student facilities, academic support and campus services."),"infrastructure":("Infrastructure","Campus buildings, laboratories, workshop, library and managed campus gallery."),"given-in-college":("Given in College","Programmes, branches and academic subjects available through this portal."),"tourism":("Jaunpur Tourism","Heritage places and tourism highlights around Jaunpur.")}
ACADEMIC_STRUCTURES={"CSE":CSE,"Electronics":ELECTRONICS,"Pharmacy":PHARMACY}

@app.route("/healthz")
def healthz(): return jsonify({"status":"ok","service":"College Campus Portal"})

@app.route("/")
def home(): return redirect(url_for("login"))

@app.route("/campus/<section>")
@login_required()
def campus_page(section):
    if section not in CAMPUS_PAGES: abort(404)
    teachers=[{"full_name":n,"designation":d,"qualification":q,"email":e,"branch":dept} for n,d,q,e,dept in TEACHERS]
    about=one("SELECT * FROM site_content WHERE content_key='about_college'")
    infra=many("SELECT i.*,u.full_name uploader FROM infrastructure_images i JOIN users u ON u.id=i.uploaded_by ORDER BY i.created_at DESC")
    tourism=many("SELECT * FROM tourism_places ORDER BY sort_order,name")
    return render_template("campus.html",section=section,page={"title":CAMPUS_PAGES[section][0],"subtitle":CAMPUS_PAGES[section][1]},teachers=teachers,gallery=GALLERY,subjects=ACADEMIC_STRUCTURES,about=about,infra=infra,tourism=tourism)

@app.route("/download/<path:filename>")
@login_required()
def download_file(filename):
    safe=Path(filename)
    if ".." in safe.parts: return "Forbidden",403
    root=BASE/"uploads"
    if not (root/safe).is_file(): return "File not found",404
    return send_from_directory(root,filename,as_attachment=True)

@app.route("/login",methods=["GET","POST"])
def login():
    if request.method=="POST":
        ip=client_ip(); now=time.time(); LOGIN_BUCKET[ip]=[t for t in LOGIN_BUCKET[ip] if now-t<300]
        if len(LOGIN_BUCKET[ip])>=8:
            security_event("login_rate_limited",None,request.form.get("username")); flash("Too many attempts. Please wait 5 minutes.","danger"); return render_template("login.html")
        identifier=request.form.get("username","").strip()
        password=request.form.get("password",""); role=request.form.get("role","student")
        u=one("SELECT * FROM users WHERE (username=%s OR roll_no=%s OR enrollment_no=%s) AND active=1 AND (registration_status IS NULL OR registration_status='active')",(identifier,identifier,identifier))
        if u and u["role"]==role and check_password_hash(u["password_hash"],password):
            if role in {"student","teacher"}:
                code=f"{secrets.randbelow(1000000):06d}"; h=hashlib.sha256(code.encode()).hexdigest(); exp=dt.datetime.now()+dt.timedelta(minutes=10)
                execute("UPDATE otp_codes SET used_at=NOW() WHERE user_id=%s AND purpose='login' AND used_at IS NULL",(u["id"],)); execute("INSERT INTO otp_codes(user_id,purpose,code_hash,expires_at) VALUES(%s,'login',%s,%s)",(u["id"],h,exp))
                session.clear(); session.permanent=True; session["login_otp_user_id"]=u["id"]; session["login_otp_role"]=role; session["login_next"]=request.args.get("next") or url_for("dashboard"); session["csrf"]=secrets.token_urlsafe(24); session["login_demo_otp"]=code
                sent=[]
                ok,_=send_email(u.get("email"),"College Campus Portal login OTP",f"Your login OTP is {code}. It expires in 10 minutes.",u["id"]); sent.append("email") if ok else None
                ok,_=send_whatsapp(u.get("phone"),f"College Campus Portal login OTP: {code}. It expires in 10 minutes.",u["id"]); sent.append("WhatsApp") if ok else None
                ok,_=send_sms(u.get("phone"),f"College Campus Portal login OTP: {code}. It expires in 10 minutes.",u["id"]); sent.append("SMS") if ok else None
                if not sent: flash("OTP generated in demo mode because email/WhatsApp is not configured. Use the OTP shown on the verification screen.","warning")
                else: session.pop("login_demo_otp",None); flash("OTP sent to your registered contact. Enter it to finish login.","success")
                security_event("login_password_verified_waiting_otp",u["id"],identifier); return redirect(url_for("verify_login_otp"))
            session.clear(); session.permanent=True; session["user_id"]=u["id"]; session["role"]=u["role"]; session["csrf"]=secrets.token_urlsafe(24); execute("UPDATE users SET last_login=NOW() WHERE id=%s",(u["id"],)); security_event("login_success",u["id"],identifier); return redirect(request.args.get("next") or url_for("dashboard"))
        LOGIN_BUCKET[ip].append(now); security_event("login_failed",u["id"] if u else None,identifier); flash("Invalid credentials or selected role. Students use their official roll/enrollment number; teachers use their assigned login ID.","danger")
    return render_template("login.html")

@app.route("/verify-login-otp",methods=["GET","POST"])
def verify_login_otp():
    uid=session.get("login_otp_user_id")
    if not uid: return redirect(url_for("login"))
    if request.method=="POST":
        code=request.form.get("otp","").strip(); r=one("SELECT * FROM otp_codes WHERE user_id=%s AND purpose='login' AND used_at IS NULL AND expires_at>NOW() ORDER BY id DESC LIMIT 1",(uid,))
        if not r or r["attempts"]>=5: flash("Login OTP expired or too many attempts. Please log in again.","danger"); return redirect(url_for("login"))
        execute("UPDATE otp_codes SET attempts=attempts+1 WHERE id=%s",(r["id"],))
        if not secrets.compare_digest(hashlib.sha256(code.encode()).hexdigest(),r["code_hash"]): flash("Incorrect login OTP.","danger"); return render_template("verify_otp.html",demo_otp=session.get("login_demo_otp"),login_otp=True)
        execute("UPDATE otp_codes SET used_at=NOW() WHERE id=%s",(r["id"],))
        try:
            ok, token = bind_device(uid)
        except mysql.connector.Error:
            # This normally means an older database was not migrated to the current schema
            # and is missing users.device_hash. Do not expose a 500 page.
            flash("Database update required: run upgrade.sql for Version 6, then restart the server.","danger")
            return redirect(url_for("login"))
        except Exception:
            flash("Could not complete secure login. Please restart Flask and try again.","danger")
            return redirect(url_for("login"))
        if not ok:
            flash("This account is already bound to another device. Ask Admin to reset the device binding before using a new phone/browser.","danger")
            return redirect(url_for("login"))
        u=one("SELECT * FROM users WHERE id=%s",(uid,))
        if not u:
            session.clear()
            flash("Student account no longer exists. Contact Admin.","danger")
            return redirect(url_for("login"))
        nxt=session.get("login_next") or url_for("dashboard")
        role=u["role"]
        session.pop("login_otp_user_id",None); session.pop("login_otp_role",None); session.pop("login_next",None); session.pop("login_demo_otp",None)
        session["user_id"]=uid; session["role"]=role; session["csrf"]=secrets.token_urlsafe(24)
        execute("UPDATE users SET last_login=NOW() WHERE id=%s",(uid,))
        security_event("login_success_otp",uid,u.get("username"))
        resp=redirect(nxt)
        resp.set_cookie("college_portal_device",token,max_age=60*60*24*365,httponly=True,samesite="Lax",secure=app.config["SESSION_COOKIE_SECURE"])
        return resp
    return render_template("verify_otp.html",demo_otp=session.get("login_demo_otp"),login_otp=True)

@app.route("/signup",methods=["GET","POST"])
def signup():
    if request.method=="POST":
        roll=request.form.get("roll_no","").strip().upper(); enrollment=request.form.get("enrollment_no","").strip().upper(); name=request.form.get("full_name","").strip(); email=request.form.get("email","").strip().lower() or None; phone=request.form.get("phone","").strip() or None; branch=request.form.get("branch","").strip(); year=request.form.get("year_no","").strip(); semester=request.form.get("semester","").strip(); pw=request.form.get("password","")
        if len(pw)<10: flash("Password must contain at least 10 characters.","danger"); return render_template("signup.html")
        if not (roll or enrollment) or not name or not branch or not year or not semester: flash("Please fill all required student details.","danger"); return render_template("signup.html")
        reserved=one("SELECT * FROM users WHERE role='student' AND (roll_no=%s OR enrollment_no=%s)",(roll or "",enrollment or ""))
        if not reserved:
            flash("This official Roll/Enrollment number has not been issued by Admin or an authorized Teacher yet.","danger"); return render_template("signup.html")
        if roll and reserved.get("roll_no") and reserved.get("roll_no").upper()!=roll:
            flash("Roll Number does not match the reserved record.","danger"); return render_template("signup.html")
        if enrollment and reserved.get("enrollment_no") and reserved.get("enrollment_no").upper()!=enrollment:
            flash("Enrollment Number does not match the reserved record.","danger"); return render_template("signup.html")
        status=reserved.get("registration_status") or ("active" if reserved.get("active") else "reserved")
        if status not in {"reserved","pending"}:
            flash("This roll number is already activated. Please use it to log in or use Forgot Password / OTP.","warning"); return render_template("signup.html")
        def norm_phone(v): return "".join(ch for ch in str(v or "") if ch.isdigit())[-10:]
        if (reserved.get("full_name") or "").strip().casefold() != name.casefold():
            flash("Name does not match the official record for this roll number. Contact the Admin.","danger"); return render_template("signup.html")
        if (reserved.get("branch") or "") != branch or str(reserved.get("year_no")) != str(year) or str(reserved.get("semester")) != semester:
            flash("Branch, year or semester does not match the official Admin record.","danger"); return render_template("signup.html")
        registered_email=(reserved.get("email") or "").strip().lower()
        registered_phone=norm_phone(reserved.get("phone"))
        if registered_email and (not email or email != registered_email):
            flash("Please use the email already registered by the Admin for this roll number.","danger"); return render_template("signup.html")
        if registered_phone and (not phone or norm_phone(phone) != registered_phone):
            flash("Please use the phone/WhatsApp number already registered by the Admin for this roll number.","danger"); return render_template("signup.html")
        if email and email != registered_email and one("SELECT id FROM users WHERE email=%s AND id<>%s",(email,reserved["id"])):
            flash("This email is already registered.","danger"); return render_template("signup.html")
        final_email=registered_email or email
        final_phone=reserved.get("phone") or phone
        execute("UPDATE users SET username=COALESCE(NULLIF(enrollment_no,''),roll_no),password_hash=%s,email=%s,phone=%s,registration_status='active',active=1 WHERE id=%s",(generate_password_hash(pw),final_email or None,final_phone or None,reserved["id"]))
        security_event("student_account_claimed",reserved["id"],reserved.get("enrollment_no") or reserved.get("roll_no")); flash("Account activated successfully. Your official Roll/Enrollment No. is now your permanent login ID.","success"); return redirect(url_for("login"))
    return render_template("signup.html")

@app.route("/forgot-password",methods=["GET","POST"])
def forgot_password():
    if request.method=="POST":
        identifier=request.form.get("identifier","").strip(); u=one("SELECT * FROM users WHERE (username=%s OR roll_no=%s OR enrollment_no=%s OR email=%s OR phone=%s) AND active=1",(identifier,identifier,identifier,identifier,identifier))
        if u:
            code=f"{secrets.randbelow(1000000):06d}"; h=hashlib.sha256(code.encode()).hexdigest(); exp=dt.datetime.now()+dt.timedelta(minutes=10)
            execute("UPDATE otp_codes SET used_at=NOW() WHERE user_id=%s AND purpose='password_reset' AND used_at IS NULL",(u["id"],)); execute("INSERT INTO otp_codes(user_id,purpose,code_hash,expires_at) VALUES(%s,'password_reset',%s,%s)",(u["id"],h,exp))
            session["otp_user_id"]=u["id"]; session.pop("demo_otp",None); sent=[]
            ok,_=send_email(u.get("email"),"College Campus Portal password reset OTP",f"Your OTP is {code}. It expires in 10 minutes.",u["id"]); sent.append("email") if ok else None
            ok,_=send_whatsapp(u.get("phone"),f"College Campus Portal password reset OTP: {code}. It expires in 10 minutes.",u["id"]); sent.append("WhatsApp") if ok else None
            ok,_=send_sms(u.get("phone"),f"College Campus Portal password reset OTP: {code}. It expires in 10 minutes.",u["id"]); sent.append("SMS") if ok else None
            if not sent: session["demo_otp"]=code; flash("OTP generated in demo mode because email/WhatsApp is not configured. The demo OTP is shown only on this screen.","warning")
            else: flash("OTP sent to the configured contact channel. Enter it below.","success")
            return redirect(url_for("verify_otp"))
        flash("If the account exists, an OTP has been requested.","success")
    return render_template("forgot.html")

@app.route("/verify-otp",methods=["GET","POST"])
def verify_otp():
    uid=session.get("otp_user_id")
    if not uid: return redirect(url_for("forgot_password"))
    if request.method=="POST":
        code=request.form.get("otp","").strip(); r=one("SELECT * FROM otp_codes WHERE user_id=%s AND purpose='password_reset' AND used_at IS NULL AND expires_at>NOW() ORDER BY id DESC LIMIT 1",(uid,))
        if not r or r["attempts"]>=5: flash("OTP expired or too many attempts. Request a new OTP.","danger"); return render_template("verify_otp.html",demo_otp=session.get("demo_otp"))
        execute("UPDATE otp_codes SET attempts=attempts+1 WHERE id=%s",(r["id"],))
        if not secrets.compare_digest(hashlib.sha256(code.encode()).hexdigest(),r["code_hash"]): flash("Incorrect OTP.","danger"); return render_template("verify_otp.html",demo_otp=session.get("demo_otp"))
        execute("UPDATE otp_codes SET used_at=NOW() WHERE id=%s",(r["id"],)); session["otp_verified_user"]=uid; session.pop("demo_otp",None); return redirect(url_for("set_new_password"))
    return render_template("verify_otp.html",demo_otp=session.get("demo_otp"))

@app.route("/set-new-password",methods=["GET","POST"])
def set_new_password():
    uid=session.get("otp_verified_user")
    if not uid: return redirect(url_for("forgot_password"))
    if request.method=="POST":
        pw=request.form.get("password","")
        if len(pw)<10: flash("Use at least 10 characters.","danger"); return render_template("reset.html")
        execute("UPDATE users SET password_hash=%s WHERE id=%s",(generate_password_hash(pw),uid)); security_event("password_reset_completed",uid); session.pop("otp_verified_user",None); session.pop("otp_user_id",None); flash("Password changed successfully. Please log in.","success"); return redirect(url_for("login"))
    return render_template("reset.html")

@app.route("/logout")
def logout(): session.clear(); flash("You have been securely logged out.","success"); return redirect(url_for("login"))
@app.route("/dashboard")
@login_required()
def dashboard(): return redirect(url_for(f"{session['role']}_dashboard"))

@app.route("/admin")
@login_required("admin")
def admin_dashboard():
    stats={"students":one("SELECT COUNT(*) c FROM users WHERE role='student' AND (registration_status IS NULL OR registration_status='active')")["c"],"pending_students":one("SELECT COUNT(*) c FROM users WHERE role='student' AND registration_status='reserved'")["c"],"teachers":one("SELECT COUNT(*) c FROM users WHERE role='teacher'")["c"],"subjects":one("SELECT COUNT(*) c FROM subjects")["c"],"posts":one("SELECT COUNT(*) c FROM posts")["c"],"complaints":one("SELECT COUNT(*) c FROM complaints WHERE status IN ('open','in_progress')")["c"],"low_attendance":one("SELECT COUNT(*) c FROM (SELECT student_id FROM attendance GROUP BY student_id,subject_id HAVING 100*SUM(status='present')/COUNT(*)<75)x")["c"],"assignments":one("SELECT COUNT(*) c FROM assignments")["c"],"events":one("SELECT COUNT(*) c FROM events WHERE event_date>=CURDATE()")["c"]}
    teachers=many("SELECT * FROM users WHERE role='teacher' ORDER BY full_name"); students=many("SELECT id,full_name,username,branch,year_no,semester,roll_no,enrollment_no,email,last_login,active FROM users WHERE role='student' ORDER BY id DESC LIMIT 120")
    analytics=admin_analytics_data(); complaints=many("SELECT c.*,u.full_name student_name,u.roll_no FROM complaints c JOIN users u ON u.id=c.student_id ORDER BY c.updated_at DESC LIMIT 10")
    events=many("SELECT * FROM events ORDER BY event_date DESC LIMIT 12")
    return render_template("admin.html",stats=stats,teachers=teachers,students=students,analytics=analytics,complaints=complaints,events=events)

def admin_analytics_data():
    return {"branch":many("SELECT branch,COUNT(*) count FROM users WHERE role='student' GROUP BY branch ORDER BY branch"),"status":many("SELECT status,COUNT(*) count FROM complaints GROUP BY status"),"attendance":list(reversed(many("SELECT DATE_FORMAT(attendance_date,'%Y-%m') month,ROUND(100*SUM(status='present')/COUNT(*),1) pct FROM attendance GROUP BY month ORDER BY month DESC LIMIT 6"))),"posts":many("SELECT post_type,COUNT(*) count FROM posts GROUP BY post_type")}

@app.route("/admin/analytics")
@login_required("admin")
def admin_analytics(): return render_template("analytics.html",analytics=admin_analytics_data())
@app.route("/admin/complaints")
@login_required("admin")
def admin_complaints(): return render_template("complaints.html",rows=many("SELECT c.*,u.full_name student_name,u.roll_no FROM complaints c JOIN users u ON u.id=c.student_id ORDER BY c.updated_at DESC"))
@app.route("/admin/complaint/<int:cid>",methods=["POST"])
@login_required("admin")
def update_complaint(cid):
    status=request.form.get("status","open"); reply=request.form.get("reply","").strip(); c=one("SELECT * FROM complaints WHERE id=%s",(cid,))
    if not c: abort(404)
    execute("UPDATE complaints SET status=%s,admin_reply=%s WHERE id=%s",(status,reply,cid)); student=one("SELECT * FROM users WHERE id=%s",(c["student_id"],)); send_user_alert(student,"Complaint updated",f"Complaint #{cid} is now {status.replace('_',' ')}."+(f" Admin reply: {reply}" if reply else ""),"complaint",url_for("student_dashboard")+"#complaints",True); flash("Complaint workflow updated.","success"); return redirect(request.referrer or url_for("admin_complaints"))

@app.route("/admin/manage")
@login_required()
def admin_manage():
    q=request.args.get("q","").strip()
    role=request.args.get("role","").strip()
    if session.get("role")=="teacher": role="student"
    if q:
        like=f"%{q}%"
        users=many("SELECT id,username,role,full_name,email,phone,branch,year_no,semester,roll_no,enrollment_no,active,registration_status,created_at FROM users WHERE (full_name LIKE %s OR roll_no LIKE %s OR enrollment_no LIKE %s OR username LIKE %s OR phone LIKE %s) AND (%s='' OR role=%s) ORDER BY role,full_name",(like,like,like,like,like,role,role))
    else:
        users=many("SELECT id,username,role,full_name,email,phone,branch,year_no,semester,roll_no,enrollment_no,active,registration_status,created_at FROM users WHERE (%s='' OR role=%s) ORDER BY role,full_name",(role,role))
    assignments=many("SELECT a.*,s.subject_name,u.full_name teacher_name,(SELECT COUNT(*) FROM assignment_submissions x WHERE x.assignment_id=a.id) submissions FROM assignments a JOIN subjects s ON s.id=a.subject_id JOIN users u ON u.id=a.created_by ORDER BY a.created_at DESC LIMIT 30")
    results=many("SELECT r.*,u.full_name student_name,u.roll_no,s.subject_name FROM results r JOIN users u ON u.id=r.student_id JOIN subjects s ON s.id=r.subject_id ORDER BY r.created_at DESC LIMIT 40")
    if session.get("role")=="teacher":
        posts=many("SELECT p.*,u.full_name creator_name FROM posts p JOIN users u ON u.id=p.created_by WHERE p.created_by=%s ORDER BY p.created_at DESC LIMIT 60",(session["user_id"],))
        events=many("SELECT e.*,u.full_name creator_name FROM events e JOIN users u ON u.id=e.created_by WHERE e.created_by=%s ORDER BY e.event_date DESC,e.start_time DESC LIMIT 60",(session["user_id"],))
    else:
        posts=many("SELECT p.*,u.full_name creator_name FROM posts p JOIN users u ON u.id=p.created_by ORDER BY p.created_at DESC LIMIT 60")
        events=many("SELECT e.*,u.full_name creator_name FROM events e JOIN users u ON u.id=e.created_by ORDER BY e.event_date DESC,e.start_time DESC LIMIT 60")
    about=one("SELECT * FROM site_content WHERE content_key='about_college'")
    return render_template("admin_manage.html",users=users,assignments=assignments,results=results,posts=posts,events=events,about=about,subjects=many("SELECT * FROM subjects ORDER BY branch,year_no,semester,subject_name"))

@app.route("/admin/user",methods=["POST"])
@login_required("admin")
def admin_create_user():
    role=request.form.get("role","student")
    if role not in {"student","teacher"}: role="student"
    roll=request.form.get("roll_no","").strip().upper() if role=="student" else None
    enrollment=request.form.get("enrollment_no","").strip().upper() if role=="student" else None
    username=request.form.get("username","").strip() or (enrollment or roll if role=="student" else "")
    name=request.form.get("full_name","").strip()
    if role=="student" and not (roll or enrollment): flash("Student must have a unique Roll No or Enrollment No.","danger"); return redirect(url_for("admin_manage"))
    if not username or not name: flash("Username/login ID and full name are required.","danger"); return redirect(url_for("admin_manage"))
    if one("SELECT id FROM users WHERE username=%s",(username,)): flash("Username already exists.","danger"); return redirect(url_for("admin_manage"))
    if roll and one("SELECT id FROM users WHERE roll_no=%s",(roll,)): flash("Roll number already exists.","danger"); return redirect(url_for("admin_manage"))
    if enrollment and one("SELECT id FROM users WHERE enrollment_no=%s",(enrollment,)): flash("Enrollment number already exists.","danger"); return redirect(url_for("admin_manage"))
    if role=="student":
        # Student records are reserved by Admin first. The student claims the record through /signup.
        password_hash=generate_password_hash(secrets.token_urlsafe(24))
        active=0; registration_status="reserved"
    else:
        password=request.form.get("password") or "Teacher@123"
        password_hash=generate_password_hash(password); active=1; registration_status="active"
    execute("INSERT INTO users(username,password_hash,role,full_name,email,phone,branch,year_no,semester,roll_no,enrollment_no,designation,qualification,active,registration_status) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",(username,password_hash,role,name,request.form.get("email") or None,request.form.get("phone") or None,request.form.get("branch") or None,int(request.form["year_no"]) if request.form.get("year_no") else None,request.form.get("semester") or None,roll,enrollment,request.form.get("designation") or None,request.form.get("qualification") or None,active,registration_status))
    if role=="student":
        flash(f"Official roll number {roll} reserved. Student must complete first-time signup using the same official details.","success")
    else:
        flash("Teacher account created.","success")
    return redirect(url_for("admin_manage"))

@app.route("/admin/user/<int:uid>/toggle",methods=["POST"])
@login_required("admin")
def toggle_user(uid):
    if uid==session["user_id"]: flash("You cannot deactivate your own admin account.","danger"); return redirect(url_for("admin_manage"))
    execute("UPDATE users SET active=1-active WHERE id=%s",(uid,)); flash("User status changed.","success"); return redirect(url_for("admin_manage"))

@app.route("/admin/user/<int:uid>/reset-device",methods=["POST"])
@login_required("admin")
def reset_device(uid):
    execute("UPDATE users SET device_hash=NULL WHERE id=%s",(uid,)); security_event("device_binding_reset",uid); flash("Device binding reset. The user must complete OTP login on the new device.","success"); return redirect(url_for("admin_manage"))

@app.route("/admin/users/reset-devices",methods=["POST"])
@login_required("admin")
def reset_devices_bulk():
    ids=[]
    for raw in request.form.getlist("user_ids"):
        try: ids.append(int(raw))
        except ValueError: pass
    if not ids:
        flash("Select at least one student or teacher.","danger"); return redirect(url_for("admin_manage"))
    for uid in set(ids):
        u=one("SELECT id,role FROM users WHERE id=%s",(uid,))
        if u and u["role"] in {"student","teacher"}:
            execute("UPDATE users SET device_hash=NULL WHERE id=%s",(uid,)); security_event("device_binding_reset",uid)
    flash(f"OTP device reset completed for {len(set(ids))} selected account(s).","success"); return redirect(url_for("admin_manage"))

@app.route("/social-hub")
@login_required()
def social_hub():
    return render_template("social_hub.html")

@app.route("/admin/contact/reset",methods=["POST"])
@login_required("admin")
def admin_contact_reset():
    for key in ("admin_instagram", "admin_whatsapp", "team_name"):
        execute("DELETE FROM site_content WHERE content_key=%s", (key,))
    flash("Saved contact/team settings were reset to the built-in DIGITAL DYNAMOS defaults.", "success")
    return redirect(url_for("admin_manage")+"#contact")

@app.route("/admin/contact",methods=["POST"])
@login_required("admin")
def admin_contact():
    instagram=request.form.get("instagram","").strip()
    whatsapp=request.form.get("whatsapp","").strip()
    team=request.form.get("team_name","DIGITAL DYNAMOS").strip() or "DIGITAL DYNAMOS"
    if not instagram.startswith("https://www.instagram.com/"):
        flash("Please enter a valid Instagram profile URL.","danger"); return redirect(url_for("admin_manage")+"#contact")
    digits="".join(ch for ch in whatsapp if ch.isdigit())
    if len(digits) not in {10,11,12,13}:
        flash("Please enter a valid WhatsApp number.","danger"); return redirect(url_for("admin_manage")+"#contact")
    for key,title,body in [("admin_instagram","Admin Instagram",instagram),("admin_whatsapp","Admin WhatsApp",whatsapp),("team_name","Team Name",team)]:
        execute("INSERT INTO site_content(content_key,title,body,updated_by) VALUES(%s,%s,%s,%s) ON DUPLICATE KEY UPDATE title=VALUES(title),body=VALUES(body),updated_by=VALUES(updated_by)",(key,title,body,session["user_id"]))
    flash("Contact details and team name updated.","success")
    return redirect(url_for("admin_manage")+"#contact")

@app.route("/management/user/<int:uid>/delete",methods=["POST"])
@login_required("admin")
def delete_user_permanently(uid):
    if uid==session["user_id"]: flash("You cannot permanently delete your own admin account.","danger"); return redirect(url_for("admin_manage"))
    u=one("SELECT id,full_name,role FROM users WHERE id=%s",(uid,))
    if not u: abort(404)
    execute("DELETE FROM users WHERE id=%s",(uid,))
    flash(f"{u['role'].title()} account for {u['full_name']} was permanently deleted.","success")
    return redirect(request.referrer or url_for("admin_manage"))

@app.route("/account",methods=["GET","POST"])
@login_required()
def account_settings():
    if request.method=="POST":
        u=one("SELECT * FROM users WHERE id=%s",(session["user_id"],))
        name=request.form.get("full_name","").strip()
        if not name: flash("Full name is required.","danger"); return redirect(url_for("account_settings"))
        email=request.form.get("email","").strip().lower() or None; phone=request.form.get("phone","").strip() or None
        if email and one("SELECT id FROM users WHERE email=%s AND id<>%s",(email,session["user_id"])): flash("Email already belongs to another account.","danger"); return redirect(url_for("account_settings"))
        path,_=(None,None)
        f=request.files.get("profile_image")
        if f and f.filename:
            try: path,_=save_upload(f,"profile")
            except ValueError as e: flash(str(e),"danger"); return redirect(url_for("account_settings"))
        sql="UPDATE users SET full_name=%s,email=%s,phone=%s"; args=[name,email,phone]
        if path: sql+=",profile_image=%s"; args.append(path)
        new_password=request.form.get("new_password","")
        if new_password:
            if len(new_password)<8: flash("New password must be at least 8 characters.","danger"); return redirect(url_for("account_settings"))
            if not check_password_hash(u["password_hash"],request.form.get("current_password","") ): flash("Current password is incorrect.","danger"); return redirect(url_for("account_settings"))
            sql+=",password_hash=%s"; args.append(generate_password_hash(new_password))
        sql+=" WHERE id=%s"; args.append(session["user_id"]); execute(sql,tuple(args)); flash("Account settings updated.","success"); return redirect(url_for("account_settings"))
    return render_template("account.html",user=one("SELECT * FROM users WHERE id=%s",(session["user_id"],)))

@app.route("/admin/event",methods=["POST"])
@login_required("admin")
def admin_event():
    eid=execute("INSERT INTO events(title,description,event_date,start_time,end_time,venue,event_type,created_by) VALUES(%s,%s,%s,%s,%s,%s,%s,%s)",(request.form["title"],request.form.get("description"),request.form["event_date"],request.form.get("start_time") or None,request.form.get("end_time") or None,request.form.get("venue"),request.form.get("event_type") or "General",session["user_id"]))
    students=many("SELECT * FROM users WHERE role='student' AND active=1"); teachers=many("SELECT * FROM users WHERE role='teacher' AND active=1"); msg=f"{request.form['title']} on {request.form['event_date']} at {request.form.get('venue') or 'college campus'}."
    for u in students+teachers: send_user_alert(u,"New college event",msg,"event",url_for("events_page"),True)
    flash("Event created and portal notifications sent.","success"); return redirect(url_for("admin_manage")+"#events")

@app.route("/events")
@login_required()
def events_page(): return render_template("events.html",events=many("SELECT * FROM events WHERE event_date>=DATE_SUB(CURDATE(),INTERVAL 30 DAY) ORDER BY event_date,start_time"))

@app.route("/admin/result",methods=["POST"])
@login_required("admin")
def admin_result():
    student_id=int(request.form["student_id"]); subject_id=int(request.form["subject_id"]); exam=request.form["exam_type"].strip(); marks=float(request.form["marks"]); max_marks=float(request.form.get("max_marks") or 100); pct=(marks/max_marks*100) if max_marks else 0; grade="A+" if pct>=90 else "A" if pct>=80 else "B" if pct>=70 else "C" if pct>=60 else "D" if pct>=50 else "F"
    execute("INSERT INTO results(student_id,subject_id,exam_type,marks,max_marks,grade,remarks,published,created_by) VALUES(%s,%s,%s,%s,%s,%s,%s,1,%s) ON DUPLICATE KEY UPDATE marks=VALUES(marks),max_marks=VALUES(max_marks),grade=VALUES(grade),remarks=VALUES(remarks),published=1,created_by=VALUES(created_by)",(student_id,subject_id,exam,marks,max_marks,grade,request.form.get("remarks"),session["user_id"]))
    u=one("SELECT * FROM users WHERE id=%s",(student_id,)); send_user_alert(u,"Result published",f"{exam} result for your subject has been published. Marks: {marks}/{max_marks} ({grade}).","result",url_for("student_result"),True); flash("Result saved and student notified.","success"); return redirect(url_for("admin_manage")+"#results")

@app.route("/teacher/student",methods=["POST"])
@login_required("teacher")
def teacher_create_student():
    name=request.form.get("full_name","").strip(); roll=request.form.get("roll_no","").strip().upper() or None; enrollment=request.form.get("enrollment_no","").strip().upper() or None; branch=request.form.get("branch","").strip(); year=request.form.get("year_no") or None; sem=request.form.get("semester","").strip() or None; email=request.form.get("email","").strip().lower() or None; phone=request.form.get("phone","").strip() or None
    if not name or not (roll or enrollment) or not branch or not year or not sem: flash("Name, Roll/Enrollment No, branch, year and semester are required.","danger"); return redirect(url_for("teacher_dashboard")+"#add-student")
    if roll and one("SELECT id FROM users WHERE roll_no=%s",(roll,)): flash("Roll number already exists.","danger"); return redirect(url_for("teacher_dashboard")+"#add-student")
    if enrollment and one("SELECT id FROM users WHERE enrollment_no=%s",(enrollment,)): flash("Enrollment number already exists.","danger"); return redirect(url_for("teacher_dashboard")+"#add-student")
    login_id=enrollment or roll
    if one("SELECT id FROM users WHERE username=%s",(login_id,)): flash("Login ID already exists.","danger"); return redirect(url_for("teacher_dashboard")+"#add-student")
    execute("INSERT INTO users(username,password_hash,role,full_name,email,phone,branch,year_no,semester,roll_no,enrollment_no,active,registration_status) VALUES(%s,%s,'student',%s,%s,%s,%s,%s,%s,%s,%s,0,'reserved')",(login_id,generate_password_hash(secrets.token_urlsafe(24)),name,email,phone,branch,int(year),sem,roll,enrollment))
    flash(f"Student reserved successfully. Login ID: {login_id}. Student must complete first-time signup with the official details.","success"); return redirect(url_for("teacher_dashboard")+"#add-student")

@app.route("/teacher")
@login_required("teacher")
def teacher_dashboard():
    uid=session["user_id"]; teacher=one("SELECT * FROM users WHERE id=%s",(uid,)); subjects=many("SELECT s.* FROM subjects s JOIN teacher_subjects ts ON ts.subject_id=s.id WHERE ts.teacher_id=%s ORDER BY s.branch,s.year_no,s.semester,s.subject_name",(uid,)) or many("SELECT * FROM subjects WHERE branch=%s ORDER BY year_no,semester,subject_name",(teacher["branch"],))
    alerts=many("SELECT s.id,s.full_name,s.roll_no,s.branch,s.year_no,s.semester,ROUND(100*SUM(a.status='present')/COUNT(a.id),1) pct FROM users s JOIN attendance a ON a.student_id=s.id WHERE s.role='student' AND a.subject_id IN (SELECT subject_id FROM teacher_subjects WHERE teacher_id=%s) GROUP BY s.id,s.full_name,s.roll_no,s.branch,s.year_no,s.semester HAVING pct<75 ORDER BY pct ASC LIMIT 30",(uid,))
    posts=many("SELECT * FROM posts WHERE created_by=%s ORDER BY created_at DESC LIMIT 12",(uid,)); events=many("SELECT * FROM events WHERE created_by=%s ORDER BY event_date DESC LIMIT 12",(uid,)); complaints=many("SELECT c.*,u.full_name student_name FROM complaints c JOIN users u ON u.id=c.student_id WHERE u.branch=%s ORDER BY c.updated_at DESC LIMIT 8",(teacher["branch"],)); assignments=many("SELECT a.*,s.subject_name,(SELECT COUNT(*) FROM assignment_submissions x WHERE x.assignment_id=a.id) submissions FROM assignments a JOIN subjects s ON s.id=a.subject_id WHERE a.created_by=%s ORDER BY a.created_at DESC LIMIT 20",(uid,))
    help_requests=many("SELECT h.*,u.full_name student_name,u.roll_no,s.subject_name FROM help_requests h JOIN users u ON u.id=h.student_id LEFT JOIN subjects s ON s.id=h.subject_id WHERE h.teacher_id=%s ORDER BY h.created_at DESC LIMIT 20",(uid,))
    attendance_records=many("SELECT a.id,a.attendance_date,a.status,s.subject_name,u.full_name,u.roll_no FROM attendance a JOIN subjects s ON s.id=a.subject_id JOIN users u ON u.id=a.student_id WHERE a.marked_by=%s ORDER BY a.attendance_date DESC,a.id DESC LIMIT 80",(uid,))
    return render_template("teacher.html",teacher=teacher,subjects=subjects,alerts=alerts,posts=posts,events=events,complaints=complaints,assignments=assignments,help_requests=help_requests,attendance_records=attendance_records)

@app.route("/teacher/profile",methods=["GET","POST"])
@login_required("teacher")
def teacher_profile():
    if request.method=="POST":
        path,_=save_upload(request.files.get("profile_image"),"profile") if request.files.get("profile_image") and request.files.get("profile_image").filename else (None,None)
        sql="UPDATE users SET full_name=%s,email=%s,phone=%s,designation=%s,qualification=%s,bio=%s"; args=[request.form["full_name"],request.form.get("email") or None,request.form.get("phone") or None,request.form.get("designation") or None,request.form.get("qualification") or None,request.form.get("bio") or None]
        if path: sql+=",profile_image=%s"; args.append(path)
        sql+=" WHERE id=%s"; args.append(session["user_id"]); execute(sql,tuple(args)); flash("Faculty profile updated.","success"); return redirect(url_for("teacher_profile"))
    return render_template("faculty_profile.html",teacher=one("SELECT * FROM users WHERE id=%s",(session["user_id"],)))

@app.route("/teacher/roster/<int:subject_id>")
@login_required("teacher")
def teacher_roster(subject_id):
    s=one("SELECT * FROM subjects WHERE id=%s",(subject_id,));
    if not s: return jsonify({"error":"Subject not found"}),404
    if not one("SELECT id FROM teacher_subjects WHERE teacher_id=%s AND subject_id=%s",(session["user_id"],subject_id)):
        teacher=one("SELECT branch FROM users WHERE id=%s",(session["user_id"],))
        if not teacher or teacher.get("branch")!=s.get("branch"): return jsonify({"error":"You are not assigned to this subject"}),403
    q=request.args.get("q","").strip(); like=f"%{q}%"
    rows=many("SELECT id,full_name,roll_no,username FROM users WHERE role='student' AND active=1 AND branch=%s AND year_no=%s AND semester=%s AND (full_name LIKE %s OR roll_no LIKE %s OR username LIKE %s) ORDER BY roll_no,full_name",(s["branch"],s["year_no"],s["semester"],like,like,like))
    for r in rows: r["present_today"]=bool(one("SELECT id FROM attendance WHERE student_id=%s AND subject_id=%s AND attendance_date=CURDATE() AND status='present'",(r["id"],subject_id)))
    return jsonify(rows)

@app.route("/teacher/attendance",methods=["POST"])
@login_required("teacher")
def take_attendance():
    subject_id=int(request.form["subject_id"]); date=request.form.get("attendance_date") or dt.date.today().isoformat(); students=many("SELECT id FROM users WHERE role='student' AND branch=(SELECT branch FROM subjects WHERE id=%s) AND year_no=(SELECT year_no FROM subjects WHERE id=%s) AND semester=(SELECT semester FROM subjects WHERE id=%s)",(subject_id,subject_id,subject_id)); present=set(request.form.getlist("student_id")); subject_name=one("SELECT subject_name FROM subjects WHERE id=%s",(subject_id,))["subject_name"]
    for s in students:
        status="present" if str(s["id"]) in present else "absent"; execute("INSERT INTO attendance(student_id,subject_id,attendance_date,status,marked_by,source) VALUES(%s,%s,%s,%s,%s,'teacher') ON DUPLICATE KEY UPDATE status=VALUES(status),marked_by=VALUES(marked_by),source='teacher'",(s["id"],subject_id,date,status,session["user_id"]))
        if status=="absent": u=one("SELECT * FROM users WHERE id=%s",(s["id"],)); send_user_alert(u,"Attendance marked absent",f"You were marked absent for {subject_name} on {date}.","attendance",url_for("student_dashboard")+"#attendance",True)
        create_low_attendance_notifications(s["id"],subject_id)
    flash("Attendance saved and notifications sent.","success"); return redirect(url_for("teacher_dashboard"))

@app.route("/teacher/qr",methods=["POST"])
@login_required("teacher")
def create_qr():
    subject_id=int(request.form["subject_id"]); now=dt.datetime.now(); until=now+dt.timedelta(minutes=60); raw=secrets.token_urlsafe(32); token_hash=hashlib.sha256(raw.encode()).hexdigest(); execute("UPDATE qr_sessions SET active=0 WHERE teacher_id=%s AND subject_id=%s AND valid_until>NOW()",(session["user_id"],subject_id)); qid=execute("INSERT INTO qr_sessions(token_hash,subject_id,teacher_id,valid_from,valid_until) VALUES(%s,%s,%s,%s,%s)",(token_hash,subject_id,session["user_id"],now,until)); payload=make_lan_url("scan_qr",token=raw); qrcode.make(payload).save(BASE/"static/qr"/f"qr_{qid}.png"); return jsonify({"ok":True,"qr_url":url_for("static",filename=f"qr/qr_{qid}.png"),"scan_url":payload,"valid_until":until.strftime("%Y-%m-%d %H:%M:%S")})

@app.route("/scan/qr/<token>")
@login_required("student")
def scan_qr(token):
    h=hashlib.sha256(token.encode()).hexdigest(); q=one("SELECT q.*,s.branch,s.year_no,s.semester,s.subject_name FROM qr_sessions q JOIN subjects s ON s.id=q.subject_id WHERE q.token_hash=%s AND q.active=1",(h,));
    if not q: return render_template("message.html",title="QR Invalid",message="This QR code is invalid or disabled.")
    now=dt.datetime.now()
    if not(q["valid_from"]<=now<=q["valid_until"]): return render_template("message.html",title="QR Expired",message="This QR code is valid for only 60 minutes.")
    student=one("SELECT * FROM users WHERE id=%s",(session["user_id"],))
    if (student["branch"],student["year_no"],student["semester"])!=(q["branch"],q["year_no"],q["semester"]): return render_template("message.html",title="Wrong Class QR",message="This QR belongs to another branch/year/semester.")
    execute("INSERT INTO attendance(student_id,subject_id,attendance_date,status,marked_by,source) VALUES(%s,%s,CURDATE(),'present',%s,'qr') ON DUPLICATE KEY UPDATE status='present',source='qr',marked_by=VALUES(marked_by)",(student["id"],q["subject_id"],q["teacher_id"])); notify(student["id"],"Attendance recorded",f"Present marked for {q['subject_name']} via QR.","attendance",url_for("student_dashboard")+"#attendance"); return render_template("message.html",title="Attendance Marked ✓",message=f"Present marked for {q['subject_name']}. QR valid until {q['valid_until']}.")

@app.route("/teacher/post",methods=["POST"])
@login_required("teacher")
def teacher_post():
    ptype=request.form.get("post_type","note"); title=request.form.get("title","").strip(); body=request.form.get("body","").strip(); branch=request.form.get("branch") or None; year=request.form.get("year_no") or None; sem=request.form.get("semester") or None; subject_id=request.form.get("subject_id") or None
    if ptype not in {"note","notice","timetable","circular","activity","form"}: ptype="note"
    if subject_id:
        try: subject_id=int(subject_id)
        except ValueError: subject_id=None
    if subject_id and not one("SELECT s.id FROM subjects s LEFT JOIN teacher_subjects ts ON ts.subject_id=s.id AND ts.teacher_id=%s WHERE s.id=%s AND (ts.id IS NOT NULL OR s.branch=(SELECT branch FROM users WHERE id=%s))",(session["user_id"],subject_id,session["user_id"])):
        flash("Selected subject is not assigned to this teacher.","danger"); return redirect(url_for("teacher_dashboard")+"#publish")
    try: path,ftype=save_upload(request.files.get("file"),ptype) if request.files.get("file") and request.files.get("file").filename else (None,None)
    except ValueError as e: flash(str(e),"danger"); return redirect(url_for("teacher_dashboard"))
    execute("INSERT INTO posts(post_type,title,body,file_path,file_type,branch,year_no,semester,subject_id,created_by) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",(ptype,title,body,path,ftype,branch,year,sem,subject_id,session["user_id"]))
    target=many("SELECT * FROM users WHERE role='student' AND active=1 AND (%s IS NULL OR branch=%s) AND (%s IS NULL OR year_no=%s) AND (%s IS NULL OR semester=%s)",(branch,branch,year,year,sem,sem));
    for u in target: send_user_alert(u,f"New {ptype.title()} published",title,"content",url_for("student_dashboard")+"#resources",True)
    flash("Published successfully and notifications sent.","success"); return redirect(url_for("teacher_dashboard"))

@app.route("/teacher/assignment",methods=["POST"])
@login_required("teacher")
def create_assignment():
    subject_id=int(request.form.get("subject_id") or 0)
    subject=one("SELECT s.* FROM subjects s LEFT JOIN teacher_subjects ts ON ts.subject_id=s.id AND ts.teacher_id=%s WHERE s.id=%s AND (ts.id IS NOT NULL OR s.branch=(SELECT branch FROM users WHERE id=%s))",(session["user_id"],subject_id,session["user_id"]))
    if not subject:
        flash("You are not authorized for this subject.","danger"); return redirect(url_for("teacher_dashboard")+"#assignments")
    try: path,_=save_upload(request.files.get("file"),"assignment") if request.files.get("file") and request.files.get("file").filename else (None,None)
    except ValueError as e: flash(str(e),"danger"); return redirect(url_for("teacher_dashboard")+"#assignments")
    aid=execute("INSERT INTO assignments(title,description,file_path,due_at,branch,year_no,semester,subject_id,created_by) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s)",(request.form["title"].strip(),request.form.get("description"),path,request.form.get("due_at") or None,subject["branch"],subject["year_no"],subject["semester"],subject_id,session["user_id"]))
    students=many("SELECT * FROM users WHERE role='student' AND branch=%s AND year_no=%s AND semester=%s AND active=1",(subject["branch"],subject["year_no"],subject["semester"])); msg=f"New assignment: {request.form['title']} for {subject['subject_name']}. Due: {request.form.get('due_at') or 'see portal'}."
    for u in students: send_user_alert(u,"New assignment",msg,"assignment",url_for("student_assignments"),True)
    flash("Assignment created and students notified.","success"); return redirect(url_for("teacher_dashboard"))

@app.route("/teacher/assignment/<int:aid>/submissions")
@login_required("teacher")
def assignment_submissions(aid):
    a=one("SELECT a.*,s.subject_name FROM assignments a JOIN subjects s ON s.id=a.subject_id WHERE a.id=%s AND a.created_by=%s",(aid,session["user_id"]));
    if not a: abort(404)
    rows=many("SELECT x.*,u.full_name,u.roll_no FROM assignment_submissions x JOIN users u ON u.id=x.student_id WHERE x.assignment_id=%s ORDER BY x.submitted_at DESC",(aid,)); return render_template("submissions.html",assignment=a,rows=rows)

@app.route("/teacher/submission/<int:sid>/grade",methods=["POST"])
@login_required("teacher")
def grade_submission(sid):
    row=one("SELECT x.*,a.title,a.created_by,u.id student_id FROM assignment_submissions x JOIN assignments a ON a.id=x.assignment_id JOIN users u ON u.id=x.student_id WHERE x.id=%s AND a.created_by=%s",(sid,session["user_id"]));
    if not row: abort(404)
    marks=float(request.form["marks"]); max_marks=float(request.form.get("max_marks") or row["max_marks"] or 100); execute("UPDATE assignment_submissions SET marks=%s,max_marks=%s,feedback=%s,status='graded' WHERE id=%s",(marks,max_marks,request.form.get("feedback"),sid)); u=one("SELECT * FROM users WHERE id=%s",(row["student_id"],)); send_user_alert(u,"Assignment graded",f"Your assignment '{row['title']}' has been graded: {marks}/{max_marks}.","assignment",url_for("student_assignments"),True); flash("Submission graded.","success"); return redirect(url_for("assignment_submissions",aid=row["assignment_id"]))

@app.route("/student")
@login_required("student")
def student_dashboard():
    uid=session["user_id"]; student=one("SELECT * FROM users WHERE id=%s",(uid,)); attendance=many("SELECT s.id,s.subject_name,COUNT(a.id) total,COALESCE(SUM(a.status='present'),0) present,COALESCE(ROUND(100*SUM(a.status='present')/NULLIF(COUNT(a.id),0),1),0) pct FROM subjects s LEFT JOIN attendance a ON a.subject_id=s.id AND a.student_id=%s WHERE s.branch=%s AND s.year_no=%s AND s.semester=%s GROUP BY s.id,s.subject_name ORDER BY s.subject_name",(uid,student["branch"],student["year_no"],student["semester"])); posts=many("SELECT p.*,u.full_name creator,s.subject_name FROM posts p JOIN users u ON u.id=p.created_by LEFT JOIN subjects s ON s.id=p.subject_id WHERE (p.branch IS NULL OR p.branch=%s) AND (p.year_no IS NULL OR p.year_no=%s) AND (p.semester IS NULL OR p.semester=%s) ORDER BY p.created_at DESC LIMIT 20",(student["branch"],student["year_no"],student["semester"])); teachers=many("SELECT id,full_name,email,branch FROM users WHERE role='teacher' AND active=1 AND (branch=%s OR branch='Applied Science') ORDER BY full_name",(student["branch"],)); complaints=many("SELECT * FROM complaints WHERE student_id=%s ORDER BY updated_at DESC LIMIT 10",(uid)); help_requests=many("SELECT h.*,u.full_name teacher_name FROM help_requests h LEFT JOIN users u ON u.id=h.teacher_id WHERE h.student_id=%s ORDER BY h.created_at DESC LIMIT 10",(uid)); overall=attendance_pct(uid); notifications=many("SELECT * FROM notifications WHERE user_id=%s ORDER BY created_at DESC LIMIT 8",(uid)); assignments=many("SELECT a.*,s.subject_name,x.id submission_id,x.marks,x.max_marks,x.status submission_status,x.feedback FROM assignments a JOIN subjects s ON s.id=a.subject_id LEFT JOIN assignment_submissions x ON x.assignment_id=a.id AND x.student_id=%s WHERE a.branch=%s AND a.year_no=%s AND a.semester=%s ORDER BY a.due_at IS NULL,a.due_at DESC",(uid,student["branch"],student["year_no"],student["semester"])); results=many("SELECT r.*,s.subject_name FROM results r JOIN subjects s ON s.id=r.subject_id WHERE r.student_id=%s AND r.published=1 ORDER BY r.created_at DESC",(uid,))
    return render_template("student.html",student=student,attendance=attendance,posts=posts,teachers=teachers,complaints=complaints,help_requests=help_requests,overall=overall,notifications=notifications,assignments=assignments,results=results)

@app.route("/student/assignment/<int:aid>/submit",methods=["POST"])
@login_required("student")
def submit_assignment(aid):
    a=one("SELECT * FROM assignments WHERE id=%s",(aid,)); student=one("SELECT * FROM users WHERE id=%s",(session["user_id"],));
    if not a or (a["branch"],a["year_no"],a["semester"])!=(student["branch"],student["year_no"],student["semester"]): abort(403)
    try: path,_=save_upload(request.files.get("file"),"assignment") if request.files.get("file") and request.files.get("file").filename else (None,None)
    except ValueError as e: flash(str(e),"danger"); return redirect(url_for("student_assignments"))
    if not path and not request.form.get("note"): flash("Attach a file or write a submission note.","danger"); return redirect(url_for("student_assignments"))
    status="late" if a["due_at"] and dt.datetime.now()>a["due_at"] else "submitted"; execute("INSERT INTO assignment_submissions(assignment_id,student_id,file_path,note,status) VALUES(%s,%s,%s,%s,%s) ON DUPLICATE KEY UPDATE file_path=COALESCE(VALUES(file_path),file_path),note=VALUES(note),submitted_at=NOW(),status=VALUES(status)",(aid,session["user_id"],path,request.form.get("note"),status)); teacher=one("SELECT * FROM users WHERE id=%s",(a["created_by"],)); send_user_alert(teacher,"Assignment submission received",f"{student['full_name']} ({student['roll_no']}) submitted '{a['title']}'.","assignment",url_for("assignment_submissions",aid=aid),True); flash("Assignment submitted successfully.","success"); return redirect(url_for("student_assignments"))

@app.route("/student/assignments")
@login_required("student")
def student_assignments(): return redirect(url_for("student_dashboard")+"#assignments")
@app.route("/student/results")
@login_required("student")
def student_result(): return redirect(url_for("student_dashboard")+"#results")
@app.route("/student/id-card",methods=["GET","POST"])
@login_required("student")
def student_id_card():
    if request.method=="POST":
        f=request.files.get("profile_image")
        if not f or not f.filename:
            flash("Please choose a JPG, PNG or WEBP photo.","danger"); return redirect(url_for("student_id_card"))
        try: path,_=save_upload(f,"profile")
        except ValueError as e: flash(str(e),"danger"); return redirect(url_for("student_id_card"))
        execute("UPDATE users SET profile_image=%s WHERE id=%s",(path,session["user_id"]))
        flash("Student ID photo updated successfully.","success"); return redirect(url_for("student_id_card"))
    student=one("SELECT * FROM users WHERE id=%s",(session["user_id"],))
    if not student: abort(404)
    sig=hashlib.sha256((str(student['id'])+app.config['SECRET_KEY']).encode()).hexdigest()[:32]
    qrcode.make(f"{request.url_root.rstrip('/')}/verify-student/{student['id']}?token={sig}").save(BASE/"static/qr"/f"student_{student['id']}.png")
    return render_template("id_card.html",student=student,qr_url=url_for("static",filename=f"qr/student_{student['id']}.png"))

@app.route("/student/attendance/camera")
@login_required("student")
def student_attendance_camera():
    return render_template("attendance_camera.html")

@app.route("/teacher/student/<int:uid>/id-card",methods=["GET","POST"])
@login_required("teacher")
def teacher_edit_student_id(uid):
    student=one("SELECT * FROM users WHERE id=%s AND role='student'",(uid,))
    if not student: abort(404)
    if request.method=="POST":
        name=request.form.get("full_name","").strip(); roll=request.form.get("roll_no","").strip().upper() or None; enr=request.form.get("enrollment_no","").strip().upper() or None; branch=request.form.get("branch","").strip() or None; year=request.form.get("year_no") or None; sem=request.form.get("semester","").strip() or None; email=request.form.get("email","").strip().lower() or None; phone=request.form.get("phone","").strip() or None
        if not name: flash("Full name is required.","danger"); return redirect(url_for("teacher_edit_student_id",uid=uid))
        for field,val,label in [("email",email,"Email"),("roll_no",roll,"Roll number"),("enrollment_no",enr,"Enrollment number")]:
            if val and one(f"SELECT id FROM users WHERE {field}=%s AND id<>%s",(val,uid)):
                flash(f"{label} already belongs to another user.","danger"); return redirect(url_for("teacher_edit_student_id",uid=uid))
        path=None; f=request.files.get("profile_image")
        if f and f.filename:
            try: path,_=save_upload(f,"profile")
            except ValueError as e: flash(str(e),"danger"); return redirect(url_for("teacher_edit_student_id",uid=uid))
        sql="UPDATE users SET full_name=%s,roll_no=%s,enrollment_no=%s,branch=%s,year_no=%s,semester=%s,email=%s,phone=%s"; args=[name,roll,enr,branch,int(year) if year else None,sem,email,phone]
        if path: sql+=",profile_image=%s"; args.append(path)
        sql+=" WHERE id=%s"; args.append(uid); execute(sql,tuple(args))
        flash("Student ID details and photo updated by teacher.","success"); return redirect(url_for("teacher_edit_student_id",uid=uid))
    return render_template("teacher_student_id_edit.html",student=student)

@app.route("/verify-student/<int:uid>")
def verify_student(uid):
    s=one("SELECT full_name,roll_no,branch,year_no,semester,active FROM users WHERE id=%s AND role='student'",(uid,)); expected=hashlib.sha256((str(uid)+app.config['SECRET_KEY']).encode()).hexdigest()[:32]
    if not s or not secrets.compare_digest(request.args.get('token',''),expected): return render_template("message.html",title="Student verification failed",message="This ID card QR is invalid or not registered.")
    return render_template("message.html",title="Student ID Verification",message=f"{s['full_name']} · Roll No: {s['roll_no']} · {s['branch']} · Year {s['year_no']} · Semester {s['semester']} · {'Active' if s['active'] else 'Inactive'}")

@app.route("/student/complaint",methods=["POST"])
@login_required("student")
def complaint():
    cid=execute("INSERT INTO complaints(student_id,category,subject,message) VALUES(%s,%s,%s,%s)",(session["user_id"],request.form["category"],request.form["subject"],request.form["message"])); admins=many("SELECT * FROM users WHERE role='admin' AND active=1"); student=one("SELECT * FROM users WHERE id=%s",(session["user_id"],));
    for a in admins: send_user_alert(a,"New complaint received",f"Complaint #{cid}: {request.form['subject']} from {student['full_name']}","complaint",url_for("admin_complaints"),True)
    flash(f"Complaint #{cid} submitted and is now Open.","success"); return redirect(url_for("student_dashboard")+"#complaints")

@app.route("/student/help",methods=["POST"])
@login_required("student")
def help_request():
    hid=execute("INSERT INTO help_requests(student_id,teacher_id,subject_id,message) VALUES(%s,%s,%s,%s)",(session["user_id"],request.form.get("teacher_id") or None,request.form.get("subject_id") or None,request.form["message"]));
    if request.form.get("teacher_id"):
        t=one("SELECT * FROM users WHERE id=%s",(int(request.form["teacher_id"]),)); send_user_alert(t,"New student help request",f"Help request #{hid} needs your response.","help",url_for("teacher_help_detail",hid=hid),True)
    flash("Help request sent to the teacher.","success"); return redirect(url_for("student_dashboard")+"#help")

@app.route("/notifications")
@login_required()
def notifications(): return render_template("notifications.html",notifications=many("SELECT * FROM notifications WHERE user_id=%s ORDER BY created_at DESC LIMIT 100",(session["user_id"],)))
@app.route("/notifications/read/<int:nid>",methods=["POST"])
@login_required()
def notification_read(nid): execute("UPDATE notifications SET is_read=1 WHERE id=%s AND user_id=%s",(nid,session["user_id"])); n=one("SELECT link FROM notifications WHERE id=%s AND user_id=%s",(nid,session["user_id"])); return redirect(n["link"] if n and n["link"] else url_for("notifications"))
@app.route("/notifications/read-all",methods=["POST"])
@login_required()
def notification_read_all(): execute("UPDATE notifications SET is_read=1 WHERE user_id=%s",(session["user_id"],)); return redirect(url_for("notifications"))

@app.route("/teacher/help/<int:hid>",methods=["GET","POST"])
@login_required("teacher")
def teacher_help_detail(hid):
    h=one("SELECT h.*,u.full_name student_name,u.roll_no,u.email,u.phone,s.subject_name FROM help_requests h JOIN users u ON u.id=h.student_id LEFT JOIN subjects s ON s.id=h.subject_id WHERE h.id=%s AND h.teacher_id=%s",(hid,session["user_id"]))
    if not h: abort(404)
    if request.method=="POST":
        reply=request.form.get("reply","").strip()
        status=request.form.get("status","answered")
        if status not in {"open","answered","closed"}: status="answered"
        execute("UPDATE help_requests SET reply=%s,status=%s WHERE id=%s",(reply,status,hid))
        student=one("SELECT * FROM users WHERE id=%s",(h["student_id"],))
        if student: send_user_alert(student,"Teacher replied to your help request",f"Your help request #{hid} has a teacher response.","help",url_for("student_dashboard")+"#help",True)
        flash("Help request updated and student notified.","success")
        return redirect(url_for("teacher_help_detail",hid=hid))
    return render_template("help_detail.html",help_request=h)

@app.route("/teacher/attendance/<int:aid>/delete",methods=["POST"])
@login_required()
def delete_attendance_record(aid):
    row=one("SELECT a.*,s.subject_name FROM attendance a JOIN subjects s ON s.id=a.subject_id WHERE a.id=%s",(aid,))
    if not row: abort(404)
    if session.get("role")=="teacher":
        allowed=one("SELECT id FROM teacher_subjects WHERE teacher_id=%s AND subject_id=%s",(session["user_id"],row["subject_id"]))
        if not allowed and row.get("marked_by")!=session["user_id"]: abort(403)
    elif session.get("role")!="admin": abort(403)
    execute("DELETE FROM attendance WHERE id=%s",(aid,))
    flash("Attendance record permanently deleted.","success")
    return redirect(request.referrer or url_for("teacher_dashboard")+"#attendance-records")

@app.route("/api/analytics/student")
@login_required("student")
def student_analytics(): return jsonify(many("SELECT DATE_FORMAT(attendance_date,'%Y-%m') month,ROUND(100*SUM(status='present')/COUNT(*),1) pct FROM attendance WHERE student_id=%s GROUP BY month ORDER BY month",(session["user_id"],)))
@app.route("/api/analytics/teacher")
@login_required("teacher")
def teacher_analytics(): return jsonify(many("SELECT s.subject_name,ROUND(100*SUM(a.status='present')/COUNT(*),1) pct FROM attendance a JOIN subjects s ON s.id=a.subject_id WHERE s.id IN (SELECT subject_id FROM teacher_subjects WHERE teacher_id=%s) GROUP BY s.id,s.subject_name ORDER BY s.subject_name",(session["user_id"],)))
@app.route("/api/subjects")
@login_required()
def api_subjects():
    branch=request.args.get("branch"); year=request.args.get("year"); sem=request.args.get("semester"); return jsonify(many("SELECT * FROM subjects WHERE branch=%s AND year_no=%s AND semester=%s ORDER BY subject_name",(branch,year,sem))) if branch and year and sem else jsonify([])
@app.route("/uploads/<path:filename>")
@login_required()
def uploaded(filename):
    safe=Path(filename)
    if ".." in safe.parts: return "Forbidden",403
    return send_from_directory(BASE/"uploads",filename,as_attachment=False)

# ------------------------- Smart Campus Hub V2 features -------------------------
def can_manage_user(target_id):
    role=session.get("role")
    if role=="admin": return True
    if role=="teacher":
        u=one("SELECT role FROM users WHERE id=%s",(target_id,))
        return bool(u and u["role"]=="student")
    return False

def can_manage_content(owner_id=None):
    role=session.get("role")
    return role=="admin" or (role=="teacher" and owner_id is not None and int(owner_id)==int(session.get("user_id")))

@app.route("/management/user/<int:uid>/edit",methods=["POST"])
@login_required()
def edit_user(uid):
    if not can_manage_user(uid): abort(403)
    u=one("SELECT * FROM users WHERE id=%s",(uid,))
    if not u: abort(404)
    role=u["role"]
    name=request.form.get("full_name","").strip()
    if not name: flash("Full name is required.","danger"); return redirect(request.referrer or url_for("admin_manage"))
    email=request.form.get("email","").strip().lower() or None; phone=request.form.get("phone","").strip() or None
    branch=request.form.get("branch") or None; year=request.form.get("year_no") or None; sem=request.form.get("semester") or None
    roll=request.form.get("roll_no","").strip().upper() or None; enr=request.form.get("enrollment_no","").strip().upper() or None
    if email and one("SELECT id FROM users WHERE email=%s AND id<>%s",(email,uid)): flash("Email already belongs to another user.","danger"); return redirect(request.referrer or url_for("admin_manage"))
    if roll and one("SELECT id FROM users WHERE roll_no=%s AND id<>%s",(roll,uid)): flash("Roll number already exists.","danger"); return redirect(request.referrer or url_for("admin_manage"))
    if enr and one("SELECT id FROM users WHERE enrollment_no=%s AND id<>%s",(enr,uid)): flash("Enrollment number already exists.","danger"); return redirect(request.referrer or url_for("admin_manage"))
    path=None
    f=request.files.get("profile_image")
    if f and f.filename:
        try: path,_=save_upload(f,"profile")
        except ValueError as e: flash(str(e),"danger"); return redirect(request.referrer or url_for("admin_manage"))
    sql="UPDATE users SET full_name=%s,email=%s,phone=%s,branch=%s,year_no=%s,semester=%s,roll_no=%s,enrollment_no=%s"; args=[name,email,phone,branch,int(year) if year else None,sem,roll,enr]
    if path: sql+=",profile_image=%s"; args.append(path)
    sql+=" WHERE id=%s"; args.append(uid); execute(sql,tuple(args))
    if role=="teacher" and session.get("role")=="admin":
        execute("UPDATE users SET designation=%s,qualification=%s,bio=%s WHERE id=%s",(request.form.get("designation") or None,request.form.get("qualification") or None,request.form.get("bio") or None,uid))
    flash("User record updated successfully.","success"); return redirect(request.referrer or url_for("admin_manage"))

@app.route("/management/post/<int:pid>/edit",methods=["POST"])
@login_required()
def edit_post(pid):
    p=one("SELECT * FROM posts WHERE id=%s",(pid,))
    if not p or not can_manage_content(p["created_by"]): abort(403 if p else 404)
    title=request.form.get("title","").strip()
    body=request.form.get("body","").strip()
    if not title: flash("Title is required.","danger"); return redirect(request.referrer or url_for("admin_manage"))
    path=None; f=request.files.get("file")
    if f and f.filename:
        try: path,ftype=save_upload(f,p["post_type"])
        except ValueError as e: flash(str(e),"danger"); return redirect(request.referrer or url_for("admin_manage"))
    sql="UPDATE posts SET title=%s,body=%s,branch=%s,year_no=%s,semester=%s"; args=[title,body,request.form.get("branch") or None,request.form.get("year_no") or None,request.form.get("semester") or None]
    if path: sql+=",file_path=%s,file_type=%s"; args.extend([path,ftype])
    sql+=" WHERE id=%s"; args.append(pid); execute(sql,tuple(args))
    flash("Note/notice/activity updated.","success")
    return redirect(request.referrer or url_for("admin_manage"))

@app.route("/management/post/<int:pid>/delete",methods=["POST"])
@login_required()
def delete_post(pid):
    p=one("SELECT * FROM posts WHERE id=%s",(pid,))
    if not p or not can_manage_content(p["created_by"]): abort(403 if p else 404)
    execute("DELETE FROM posts WHERE id=%s",(pid,)); flash("Note/notice/activity deleted.","success"); return redirect(request.referrer or url_for("admin_manage"))

@app.route("/management/event/<int:eid>/edit",methods=["POST"])
@login_required()
def edit_event(eid):
    e=one("SELECT * FROM events WHERE id=%s",(eid,))
    if not e or not can_manage_content(e["created_by"]): abort(403 if e else 404)
    execute("UPDATE events SET title=%s,description=%s,event_date=%s,start_time=%s,end_time=%s,venue=%s,event_type=%s WHERE id=%s",(request.form["title"].strip(),request.form.get("description"),request.form["event_date"],request.form.get("start_time") or None,request.form.get("end_time") or None,request.form.get("venue"),request.form.get("event_type") or "General",eid))
    flash("Event updated.","success"); return redirect(request.referrer or url_for("admin_manage"))

@app.route("/management/event/<int:eid>/delete",methods=["POST"])
@login_required()
def delete_event(eid):
    e=one("SELECT * FROM events WHERE id=%s",(eid,))
    if not e or not can_manage_content(e["created_by"]): abort(403 if e else 404)
    execute("DELETE FROM events WHERE id=%s",(eid,)); flash("Event deleted.","success"); return redirect(request.referrer or url_for("admin_manage"))

@app.route("/teacher/event",methods=["POST"])
@login_required("teacher")
def teacher_event():
    eid=execute("INSERT INTO events(title,description,event_date,start_time,end_time,venue,event_type,created_by) VALUES(%s,%s,%s,%s,%s,%s,%s,%s)",(request.form["title"],request.form.get("description"),request.form["event_date"],request.form.get("start_time") or None,request.form.get("end_time") or None,request.form.get("venue"),request.form.get("event_type") or "General",session["user_id"]))
    flash("Event created. You can edit/delete your event from the Teacher dashboard.","success"); return redirect(url_for("teacher_dashboard")+"#events")

@app.route("/admin/about",methods=["POST"])
@login_required("admin")
def admin_about():
    title=request.form.get("title","Government Polytechnic College, Jaunpur").strip(); body=request.form.get("body","").strip()
    execute("INSERT INTO site_content(content_key,title,body,updated_by) VALUES('about_college',%s,%s,%s) ON DUPLICATE KEY UPDATE title=VALUES(title),body=VALUES(body),updated_by=VALUES(updated_by)",(title,body,session["user_id"]))
    flash("About College information updated. Only Admin can change this section.","success"); return redirect(url_for("campus_page",section="college"))

@app.route("/admin/media",methods=["POST"])
@login_required("admin")
def admin_media():
    kind=request.form.get("kind","banner")
    key="portal_login_image" if kind=="login" else "portal_banner_image"
    f=request.files.get("image")
    if request.form.get("reset")=="1":
        old=one("SELECT body FROM site_content WHERE content_key=%s",(key,))
        if old and old.get("body"," ").startswith("/uploads/"):
            fp=BASE/old["body"].lstrip("/")
            if fp.is_file(): fp.unlink(missing_ok=True)
        execute("DELETE FROM site_content WHERE content_key=%s",(key,))
        flash("Portal image reset to the bundled default.","success")
        return redirect(url_for("admin_manage")+"#media")
    if not f or not f.filename: flash("Choose an image first.","danger"); return redirect(url_for("admin_manage")+"#media")
    try:
        path,_=save_upload(f,"infrastructure")
    except ValueError as e:
        flash(str(e),"danger"); return redirect(url_for("admin_manage")+"#media")
    execute("INSERT INTO site_content(content_key,title,body,updated_by) VALUES(%s,%s,%s,%s) ON DUPLICATE KEY UPDATE title=VALUES(title),body=VALUES(body),updated_by=VALUES(updated_by)",(key,kind,path,session["user_id"]))
    flash("Portal image updated. Only Admin can change shared login/banner images.","success")
    return redirect(url_for("admin_manage")+"#media")

@app.route("/infrastructure/upload",methods=["POST"])
@login_required()
def infrastructure_upload():
    if session.get("role") not in {"admin","teacher"}: abort(403)
    f=request.files.get("image")
    if not f or not f.filename: flash("Choose an image first.","danger"); return redirect(url_for("campus_page",section="infrastructure"))
    try: path,_=save_upload(f,"infrastructure")
    except ValueError as e: flash(str(e),"danger"); return redirect(url_for("campus_page",section="infrastructure"))
    execute("INSERT INTO infrastructure_images(title,file_path,uploaded_by) VALUES(%s,%s,%s)",(request.form.get("title") or secure_filename(f.filename),path,session["user_id"]))
    flash("Infrastructure image uploaded.","success"); return redirect(url_for("campus_page",section="infrastructure"))

@app.route("/infrastructure/<int:iid>/delete",methods=["POST"])
@login_required()
def infrastructure_delete(iid):
    i=one("SELECT * FROM infrastructure_images WHERE id=%s",(iid,))
    if not i: abort(404)
    if not can_manage_content(i["uploaded_by"]): abort(403)
    execute("DELETE FROM infrastructure_images WHERE id=%s",(iid,)); flash("Infrastructure image removed.","success"); return redirect(url_for("campus_page",section="infrastructure"))

@app.route("/student/id-card/download/pdf")
@login_required("student")
def download_id_pdf():
    student=one("SELECT * FROM users WHERE id=%s",(session["user_id"],))
    if not student: abort(404)
    out=BASE/"uploads"/"generated"; out.mkdir(parents=True,exist_ok=True); path=out/f"student_id_{student['id']}.pdf"
    c=pdf_canvas.Canvas(str(path),pagesize=A4); w,h=A4
    c.setStrokeColorRGB(.05,.25,.55); c.setLineWidth(3); c.roundRect(45,h-350,w-90,260,18,stroke=1,fill=0)
    c.setFont("Helvetica-Bold",16); c.drawString(70,h-125,"GOVERNMENT POLYTECHNIC COLLEGE, JAUNPUR")
    c.setFont("Helvetica-Bold",12); c.drawString(70,h-150,"COLLEGE CAMPUS PORTAL · STUDENT ID")
    photo=student.get("profile_image")
    if photo:
        fp=BASE/str(photo).lstrip("/")
        if fp.is_file():
            try: c.drawImage(ImageReader(str(fp)),w-170,h-275,width=90,height=110,preserveAspectRatio=True,mask='auto')
            except Exception: pass
    y=h-190; c.setFont("Helvetica",11)
    for label,key in [("Name","full_name"),("Roll No","roll_no"),("Enrollment No","enrollment_no"),("Branch","branch"),("Year / Semester","year_no"),("Email","email"),("Phone","phone")]:
        val=student.get(key) or "—"; val=str(val) if key!="year_no" else f"{val} / {student.get('semester') or '—'}"
        c.drawString(70,y,f"{label}: {val[:70]}"); y-=23
    c.setFont("Helvetica",8); c.drawString(70,h-325,"Digital ID · Scan the portal QR from the web ID-card page for verification.")
    c.save()
    return send_from_directory(out,path.name,as_attachment=True,download_name="GPJ_Student_ID_Card.pdf")

@app.route("/student/id-card/download/png")
@login_required("student")
def download_id_png():
    student=one("SELECT * FROM users WHERE id=%s",(session["user_id"],))
    if not student: abort(404)
    out=BASE/"uploads"/"generated"; out.mkdir(parents=True,exist_ok=True); path=out/f"student_id_{student['id']}.png"
    img=Image.new("RGB",(1200,760),"white"); d=ImageDraw.Draw(img)
    font_path="C:/Windows/Fonts/arial.ttf" if os.name=="nt" and Path("C:/Windows/Fonts/arial.ttf").exists() else None
    big=ImageFont.truetype(font_path,36) if font_path else ImageFont.load_default(); med=ImageFont.truetype(font_path,24) if font_path else ImageFont.load_default()
    d.rectangle((12,12,1188,748),outline=(20,70,145),width=8); d.rectangle((12,12,1188,145),fill=(8,61,140))
    d.text((45,40),"GOVERNMENT POLYTECHNIC COLLEGE, JAUNPUR",font=big,fill="white"); d.text((45,98),"COLLEGE CAMPUS PORTAL · STUDENT ID",font=med,fill="white")
    photo=student.get("profile_image")
    if photo:
        fp=BASE/str(photo).lstrip("/")
        if fp.is_file():
            try:
                ph=Image.open(fp).convert("RGB"); ph.thumbnail((170,190)); img.paste(ph,(960-ph.width//2,205))
            except Exception: pass
    y=200
    vals=[("Name",student.get("full_name")),("Roll No",student.get("roll_no")),("Enrollment No",student.get("enrollment_no")),("Branch",student.get("branch")),("Year / Semester",f"{student.get('year_no') or '—'} / {student.get('semester') or '—'}"),("Email",student.get("email")),("Phone",student.get("phone"))]
    for k,v in vals: d.text((70,y),f"{k}: {v or '—'}",font=med,fill=(20,40,70)); y+=62
    img.save(path)
    return send_from_directory(out,path.name,as_attachment=True,download_name="GPJ_Student_ID_Card.png")

@app.route("/management")
@login_required()
def management_home():
    return redirect(url_for("admin_manage") if session["role"]=="admin" else url_for("teacher_dashboard"))

@app.errorhandler(400)
def bad_request(e): return render_template("message.html",title="Request blocked",message=str(e.description)),400

@app.errorhandler(500)
def internal_server_error(e):
    # Keep production users away from raw tracebacks. The OTP/device-binding
    # migration issue is handled explicitly in verify_login_otp above.
    return render_template("message.html",title="Server error",
                           message="The server could not complete this request. Please refresh the page. If the problem continues, check the Flask terminal for the exact error."),500
if __name__=="__main__": app.run(host="0.0.0.0",port=int(os.getenv("PORT","5001")),debug=os.getenv("FLASK_DEBUG","0")=="1")
