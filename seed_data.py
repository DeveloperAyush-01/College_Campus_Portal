import mysql.connector
from werkzeug.security import generate_password_hash
from settings import PortalSettings

TEACHERS = [
    ("Mr. Deepak Saroj","Lecturer","M.Tech, B.Tech","deepaksaroj012@gmail.com","CSE"),
    ("Mr. Amarjeet Yadav","Lecturer","B.Tech","amarsky2008@gmail.com","CSE"),
    ("Mr. Sandeep Kumar Yadav","Lecturer","M.Tech, B.Tech.","gpjn@gmail.com","CSE"),
    ("Dr. Shailendra Pushkin","Lecturer","PhD(CSE), M.Tech.","s.pushkinyadav@gmail.com","CSE"),
    ("Mr. Satya Prakash","Lecturer","M.Tech, B.Tech.","cse.satyaprakash@gmail.com","CSE"),
    ("Mr. Jaishankar Singh","Lecturer","M.Tech (Electronics & Communication), PhD (Pursuing), MCA (UGC Net)","jaishankar035@gmail.com","Electronics"),
    ("Mr. Bhaskar Prasad","Lecturer","M.Tech., B.Tech.","bhaskarprasad03@yahoo.com","Electronics"),
    ("Mr. Nagendra Kumar Vishwakarma","Lecturer","PhD(Pursuing), M.Tech, B.Tech","nagendrakiet2011@gmail.com","Electronics"),
    ("Mrs. Rakhi Sahu","Principal","M.Tech., B.Tech.","sahurakhi@gmail.com","Admin"),
    ("Mr. J. P. Sonkar","Lecturer","M.Tech., B.Tech.","jpsonkar@gpjaunpur.local","Electronics"),
    ("Mr. Dhyan Singh","Lecturer","M.Tech., B.Tech.","dhyansinghknit@gmail.com","Electronics"),
    ("Dr. Pankaj Kumar Verma","Lecturer","PhD, M.Pharma","pankaj4verma@gmail.com","Pharmacy"),
    ("Mr. Vinay Kumar Shukla","Lecturer Physics","Phd(Pursuing), M.Sc (Physics)","vinayshuklap21@gmail.com","Applied Science"),
    ("Dr. Rafat Saba","Lecturer","Phd, M.Sc. (Chemistry), JRF","sabachem.au@gmail.com","Applied Science"),
    ("Dr. Anuradha","Lecturer","Phd, MA (English), NET","anuradhika5678@gmail.com","Applied Science"),
    ("Mr. Prashant Dwivedi","Lecturer","M.Sc(Maths), CSIR UGC NET-JRF","prashantdd1995@gmail.com","Applied Science"),
    ("Mr. Kailash Nath","Workshop Instructor","I.T.I.(Mechanics Machine Tools Maintenance)","kpolyjnp@gmail.com","Workshop"),
    ("Mr. Pratap Kumar","Computer Instructor","M.Sc(Computer Science)","pratapvrns@gmail.com","Workshop"),
    ("Mr. Ram Bhual","Workshop Instructor","Diploma in Mechanical (Pro.)","rbhual21@gmail.com","Workshop"),
    ("Mr. Vijay Prakash Singh","Workshop Instructor","ITI (Fitter)","vijay.pks@gmail.com","Workshop"),
    ("Mr. Gulab Singh","Workshop Superintendent","Diploma","pgjn@gmail.com","Workshop"),
    ("Mr. Jitendra Bahadur","Librarian","M.Lib","jbyjnp@gmail.com","Library"),
    ("Mr. Qamar Abbas","Personal Assistant","12th Pass","qamarpolyjnp@gmail.com","Ministerial"),
    ("Mr. Mohammad Kumail Akhter Khan","Head Assistant","M. A.","Kumailpoly@gmail.com","Ministerial"),
    ("Mr. Prabhat Ranjan","Junior Assistant","Bsc (Bio), O-Level","prabhatranjan5891@gmail.com","Ministerial"),
    ("Mr. Rajendra Prasad","CHAUKIDAR","Below Matric",None, "Other"),
    ("Mr. Lal Bahadur","LAB ATTENDENT","Below Matric",None, "Other"),
    ("Mr. Kamlesh Kumar","LAB ATTENDENT","Below Matric",None, "Other"),
    ("Mr. Manoj Kumar","MALI","", None, "Other"),
    ("Mrs. Bandana Maurya","MALI","B.A.(Arts)",None, "Other"),
    ("Mr. Raj Kumar Saroj","CHAUKIDAR","", None, "Other"),
]

CSE = {
1: {
"1":["Communication Skills-I","Applied Mathematics-I","Applied Physics-I","Applied Chemistry","Fundamentals of Computer & IT","Engineering/Technical Drawing","Workshop Practice"],
"2":["Communication Skills-II","Applied Mathematics-II","Applied Physics-II","Basics of Electrical & Electronics Engineering","Concept of Programming Using C","Computer Center Management"]},
2:{
"3":["Data Structures Using C/C++","Object-Oriented Programming in C++","Operating Systems","Digital Logic Design / Digital Electronics","Computer Organization & Architecture","Electronic Devices & Circuits"],
"4":["Database Management System (DBMS)","Computer Networks / Networking","Microprocessor & Programming","Linux/Unix Operating System","Software Engineering","Multimedia Technology"]},
3:{
"5":["Java Programming","Web Designing / Web Development","Operating System Internals / System Software","Theory of Computation","Elective-I (Python / Network Administration)","Major Project (Phase-I)"],
"6":["Advanced Java / Mobile App Development (Android)","Computer Graphics","Management / Entrepreneurship","Network Security / Wireless Communication","Major Project (Phase-II) & Viva-Voce"]}}

ELECTRONICS = {
1:{"1":["English Communication / Skills","Applied Mathematics-I","Applied Physics-I","Applied Chemistry","Basic Electrical Engineering & Electronic Components","Engineering Drawing"],
"2":["Applied Mathematics-II","Applied Physics-II","Electronic Components & Devices","Programming with C","Basics of Information Technology","General Workshop Practice"]},
2:{"3":["Applied Mathematics-III","Analog Electronics-I","Digital Electronics","Network Analysis","Electrical Machines","Electronic Measurements"],
"4":["Analog Electronics-II","Linear Integrated Circuits (Op-Amps)","Microprocessors and Microcontrollers","Electronic Communication Systems","Principles of Digital Communication"]},
3:{"5":["Industrial Electronics & Instrumentation","Microwave Engineering","Optical Communication","Embedded Systems","Troubleshooting & Maintenance of Electronic Equipment","Industrial Training"],
"6":["Computer Networking & Data Communication","Mobile & Wireless Communication","Industrial Automation / PLC","Internet of Things (IoT)","Major Project Work & Seminar"]}}

PHARMACY = {
1:{"Annual":["Pharmaceutics (Theory & Practical)","Pharmaceutical Chemistry (Theory & Practical)","Pharmacognosy (Theory & Practical)","Human Anatomy and Physiology (Theory & Practical)","Social Pharmacy (Theory & Practical)"]},
2:{"Annual":["Pharmacology (Theory & Practical)","Community Pharmacy and Management (Theory & Practical)","Biochemistry and Clinical Pathology (Theory & Practical)","Pharmacotherapeutics (Theory & Practical)","Hospital and Clinical Pharmacy (Theory & Practical)","Pharmacy Law and Ethics (Theory only)"]}}

FIRST_NAMES = ["Aarav","Vivaan","Advik","Arjun","Atharv","Kabir","Reyansh","Ayaan","Krishna","Rudra","Ishaan","Vihaan","Yuvaan","Aditya","Rohan","Kartik","Manav","Dev","Harsh","Lakshya","Anaya","Aadhya","Aarohi","Diya","Myra","Ira","Anvi","Kiara","Navya","Meera","Saanvi","Riya","Shreya","Kavya","Tanya","Nandini","Ishita","Pihu","Muskan","Simran"]
LAST_NAMES = ["Sharma","Verma","Yadav","Singh","Gupta","Mishra","Patel","Tiwari","Pandey","Srivastava","Maurya","Tripathi","Saxena","Chauhan","Kushwaha","Jaiswal","Dubey","Soni","Awasthi","Shukla"]

def connect():
    return mysql.connector.connect(host=PortalSettings.MYSQL_HOST, port=PortalSettings.MYSQL_PORT,
        user=PortalSettings.MYSQL_USER, password=PortalSettings.MYSQL_PASSWORD, database=PortalSettings.MYSQL_DATABASE)

def main():
    db = connect(); cur = db.cursor(dictionary=True)
    # Admin
    cur.execute("SELECT id FROM users WHERE username=%s", ("admin",))
    if not cur.fetchone():
        cur.execute("""INSERT INTO users(username,password_hash,role,full_name,email,phone)
                       VALUES(%s,%s,'admin',%s,%s,%s)""",
                    ("admin", generate_password_hash("Admin@123"), "AYUSH KUMAR PATEL","ayush.kumar.patel@collegecampus.local","9935840560"))
    else:
        cur.execute("UPDATE users SET full_name=%s,email=%s,phone=%s WHERE username=%s", ("AYUSH KUMAR PATEL","ayush.kumar.patel@collegecampus.local","9935840560","admin"))
    # Teachers
    teacher_phones={1:"9936919401",2:"9151661612",3:"7310342996",4:"8081936300"}
    for i,(name,designation,qualification,email,dept) in enumerate(TEACHERS,1):
        username = f"teacher{i:02d}"
        phone = teacher_phones.get(i)
        cur.execute("SELECT id FROM users WHERE username=%s", (username,))
        if not cur.fetchone():
            cur.execute("""INSERT INTO users(username,password_hash,role,full_name,email,phone,branch,designation,qualification)
                           VALUES(%s,%s,'teacher',%s,%s,%s,%s,%s,%s)""",
                        (username,generate_password_hash("Teacher@123"),name,email,phone,dept,designation,qualification))
        else:
            cur.execute("UPDATE users SET full_name=%s,email=%s,phone=COALESCE(%s,phone),branch=%s,designation=%s,qualification=%s WHERE username=%s",(name,email,phone,dept,designation,qualification,username))
    # Subjects
    subject_map={}
    for branch, data in [("CSE",CSE),("Electronics",ELECTRONICS),("Pharmacy",PHARMACY)]:
        for year, semesters in data.items():
            for sem, subjects in semesters.items():
                for idx, subject in enumerate(subjects,1):
                    code=f"{branch[:3].upper()}{year}{sem if sem!='Annual' else 'A'}{idx:02d}"
                    cur.execute("""INSERT IGNORE INTO subjects(branch,year_no,semester,subject_code,subject_name)
                                   VALUES(%s,%s,%s,%s,%s)""",(branch,year,sem,code,subject))
                    cur.execute("""SELECT id FROM subjects WHERE branch=%s AND year_no=%s AND semester=%s AND subject_name=%s""",
                                (branch,year,sem,subject))
                    subject_map[(branch,year,sem,subject)] = cur.fetchone()["id"]
    # 20 new students per branch/year/semester. Names are synthetic and intentionally different
    # from the older 60-student sample.
    counter=1
    for branch,data in [("CSE",CSE),("Electronics",ELECTRONICS),("Pharmacy",PHARMACY)]:
        for year, semesters in data.items():
            for sem in semesters:
                for n in range(20):
                    idx=(counter-1)%len(FIRST_NAMES)
                    name=f"{FIRST_NAMES[idx]} {LAST_NAMES[(counter*3)%len(LAST_NAMES)]}"
                    username=f"{branch.lower()}y{year}{sem.lower().replace(' ','')}_{n+1:02d}"
                    roll=f"GPJ{branch[:2].upper()}{year}{n+1:02d}{counter:03d}"
                    email=f"{username}@student.gpjaunpur.ac.in"
                    phone=f"9{(700000000+counter*137)%1000000000:09d}"
                    cur.execute("SELECT id FROM users WHERE username=%s",(username,))
                    if not cur.fetchone():
                        cur.execute("""INSERT INTO users(username,password_hash,role,full_name,email,phone,branch,year_no,semester,roll_no)
                                       VALUES(%s,%s,'student',%s,%s,%s,%s,%s,%s,%s)""",
                                    (username,generate_password_hash("Student@123"),name,email,phone,branch,year,sem,roll))
                    counter += 1
    # Ten fixed demo students for hackathon testing. Login ID = Enrollment No.
    DEMO=[
        ("GPJ-DEMO-001","ENR-GPJ-2026-001","Ayush Demo 01","CSE",1,"1"),
        ("GPJ-DEMO-002","ENR-GPJ-2026-002","Ayush Demo 02","CSE",1,"1"),
        ("GPJ-DEMO-003","ENR-GPJ-2026-003","Ayush Demo 03","CSE",1,"1"),
        ("GPJ-DEMO-004","ENR-GPJ-2026-004","Ayush Demo 04","CSE",1,"1"),
        ("GPJ-DEMO-005","ENR-GPJ-2026-005","Ayush Demo 05","CSE",1,"1"),
        ("GPJ-DEMO-006","ENR-GPJ-2026-006","Ayush Demo 06","Electronics",1,"1"),
        ("GPJ-DEMO-007","ENR-GPJ-2026-007","Ayush Demo 07","Electronics",1,"1"),
        ("GPJ-DEMO-008","ENR-GPJ-2026-008","Ayush Demo 08","Pharmacy",1,"Annual"),
        ("GPJ-DEMO-009","ENR-GPJ-2026-009","Ayush Demo 09","CSE",2,"3"),
        ("GPJ-DEMO-010","ENR-GPJ-2026-010","Ayush Demo 10","Electronics",2,"3")
    ]
    for roll,enr,name,branch,year,sem in DEMO:
        email=f"{enr.lower()}@demo.gpjaunpur.local"
        cur.execute("SELECT id FROM users WHERE username=%s",(enr,))
        if not cur.fetchone():
            cur.execute("""INSERT INTO users(username,password_hash,role,full_name,email,branch,year_no,semester,roll_no,enrollment_no,active,registration_status) VALUES(%s,%s,'student',%s,%s,%s,%s,%s,%s,%s,1,'active')""",(enr,generate_password_hash("Student@123"),name,email,branch,year,sem,roll,enr))
        else:
            cur.execute("UPDATE users SET roll_no=%s,enrollment_no=%s,full_name=%s,branch=%s,year_no=%s,semester=%s,active=1,registration_status='active' WHERE username=%s",(roll,enr,name,branch,year,sem,enr))

    # New Smart Campus Hub knowledge base / tourism data.
    cur.execute("INSERT INTO site_content(content_key,title,body) VALUES('about_college',%s,%s) ON DUPLICATE KEY UPDATE title=VALUES(title)", ("Government Polytechnic College, Jaunpur", "Government Polytechnic College, Jaunpur is a government technical education institute at Jagdishpur, Jaunpur, Uttar Pradesh. The College Campus Portal combines academics, attendance, assignments, results, events, digital identity and student support."))
    for key,title,body in [("admin_instagram","Admin Instagram","https://www.instagram.com/silent.killer_x_07?stkn=c3B3N2kybDIwb3p2"),("admin_whatsapp","Admin WhatsApp","9935840560"),("team_name","Team Name","DIGITAL DYNAMOS")]:
        cur.execute("INSERT INTO site_content(content_key,title,body) VALUES(%s,%s,%s) ON DUPLICATE KEY UPDATE body=VALUES(body),title=VALUES(title)",(key,title,body))
    tourism=[("Shahi Qila","Historic Jaunpur fort associated with the Sharqi period.","https://commons.wikimedia.org/wiki/Special:Redirect/file/FortJaunpur.jpg","Shahi Qila Road, Jaunpur, Uttar Pradesh 222001, India","https://commons.wikimedia.org/wiki/File:FortJaunpur.jpg",1),("Atala Masjid","Landmark Sharqi-era mosque and one of Jaunpur's best-known heritage monuments.","https://commons.wikimedia.org/wiki/Special:Redirect/file/Atala_Masjid_Jaunpur.JPG","Atala Masjid Road, Jaunpur, Uttar Pradesh 222001, India","https://commons.wikimedia.org/wiki/File:Atala_Masjid_Jaunpur.JPG",2),("Shahi Bridge","Historic stone bridge over the Gomti and an iconic Jaunpur heritage/photo stop.","https://commons.wikimedia.org/wiki/Special:Redirect/file/Shahi_bridge.jpg","Shahi Bridge, Gomti River, Jaunpur, Uttar Pradesh 222001, India","https://commons.wikimedia.org/wiki/File:Shahi_bridge.jpg",3),("Jama Masjid, Jaunpur","Grand historic mosque near the Shahi Qila area, noted for medieval architecture.","https://commons.wikimedia.org/wiki/Special:Redirect/file/Jaunpur_Jama_Masjid.jpg","Jama Masjid, Shahi Qila area, Jaunpur, Uttar Pradesh 222001, India","https://commons.wikimedia.org/wiki/File:Jaunpur_Jama_Masjid.jpg",4),("Lal Darwaza Masjid","Historic mosque connected with Jaunpur's Sharqi architectural landscape.","https://commons.wikimedia.org/wiki/Special:Redirect/file/Lal_Darwaza_Masjid_01.jpg","Lal Darwaza, Jaunpur, Uttar Pradesh 222001, India","https://commons.wikimedia.org/wiki/File:Lal_Darwaza_Masjid_01.jpg",5),("Heritage Walk","Suggested old-city heritage walk connecting historic architecture, markets and Gomti-side landmarks.","https://commons.wikimedia.org/wiki/Special:Redirect/file/Shahi_bridge.jpg","Old Jaunpur heritage area, Jaunpur, Uttar Pradesh, India","https://commons.wikimedia.org/wiki/File:Shahi_bridge.jpg",6)]
    for row in tourism: cur.execute("INSERT IGNORE INTO tourism_places(name,description,image_path,address,source_url,sort_order) VALUES(%s,%s,%s,%s,%s,%s)",row)

    # Assign academic teachers to subjects so analytics and attendance work immediately.
    cur.execute("SELECT id, branch FROM users WHERE role='teacher' ORDER BY id")
    for t in cur.fetchall():
        cur.execute("SELECT id FROM subjects WHERE branch=%s ORDER BY id", (t['branch'],))
        for s in cur.fetchall()[:8]:
            cur.execute("INSERT IGNORE INTO teacher_subjects(teacher_id,subject_id) VALUES(%s,%s)", (t['id'],s['id']))
    db.commit()
    cur.close(); db.close()
    print("Seed complete.")
    print("Admin: admin / Admin@123")
    print("Teacher: teacher01..teacher31 / Teacher@123")
    print("Students: generated usernames / Student@123")

if __name__=="__main__":
    main()
