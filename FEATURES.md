# College Campus Portal — complete feature map

## Identity and isolation
- Display name: **College Campus Portal**.
- Independent project files, module names, database name, session cookie and device cookie.
- Default local port: `5001`; cloud Render port is supplied by `PORT` (Render uses `10000`).
- Does not use the previous project's database by default.

## Login and real OTP
- Student, Teacher and Admin login.
- Student/Teacher password login followed by a 6-digit OTP.
- OTP is stored hashed, expires in 10 minutes and has attempt limits.
- Device binding is retained with an admin reset option.
- Real email OTP via Brevo HTTPS API (recommended for Render) or Gmail/SMTP locally.
- Real SMS OTP via Twilio.
- Real WhatsApp OTP via Twilio WhatsApp sender.
- If no provider is configured, local demo OTP is explicitly labelled; production deployment should configure a provider.

## Admin and Teacher management
- Student search by Name, Roll No, Enrollment No, Username and Phone.
- Admin can edit users; Teachers can edit student records.
- Activate/deactivate users and reset device binding.
- Notes / Notices / Timetable / Circular / Activities / Forms can be edited and deleted by the owner; Admin can manage all.
- Events can be edited/deleted by the owner; Admin can manage all.
- About College editing is Admin-only.
- Admin-only shared Login/Banner image replacement and reset.

## Attendance
- Teacher subject-wise attendance.
- Search roster by Name / Roll No / Username.
- Manual Present/Absent and 60-minute QR attendance.
- Attendance percentage and below-75% alerts.

## Infrastructure and media
- Admin/Teacher infrastructure image upload.
- Admin can remove any image; Teacher can remove their own uploads.
- Full-screen image viewer with zoom in/out/reset.
- Admin-only shared portal login/banner media editor.

## Student services
- Assignments, submissions and grading.
- Results.
- Complaints and teacher help requests.
- Notifications.
- Digital Student ID with QR verification.
- Student ID downloadable as PNG or PDF and printable.

- Local college knowledge base in MySQL.
- Wikipedia public API snippets.
- DuckDuckGo public instant-answer snippets when available.
- Transparent search buttons for Google, Bing, Wikipedia, YouTube, Quora, Reddit, Instagram, Facebook, X and LinkedIn.
- Study-focused search buttons for NPTEL, SWAYAM, MIT OpenCourseWare, Khan Academy, MDN and GeeksforGeeks.
- Optional OpenAI-compatible model endpoint can synthesize answers from retrieved evidence; this can point to a self-hosted/open-source model service.
- No scraping/login automation of social-media accounts is used.

## Jaunpur Tourism
- Shahi Qila
- Atala Masjid
- Shahi Bridge
- Jama Masjid
- Lal Darwaza Masjid
- Heritage Walk / old-city exploration

## Branding and images
- First user-supplied image is bundled as the Login Page image.
- Second user-supplied image is bundled as the after-login top banner.
- Admin can replace/reset both from Management → Shared Portal Images.
- Contact: **9935840560**; WhatsApp can use the same number when configured with the chosen WhatsApp provider.
- Instagram: `https://www.instagram.com/silent.killer_x_07?stkn=c3B3N2kybDIwb3p2`

## Deployment files
- `Procfile` and `render.yaml` for Render.
- `runtime.txt` pins Python 3.12.8.
- `.env.example` lists cloud MySQL, Brevo, Twilio and optional AI variables.
- `README.md` contains the complete local + Render + Vercel/Railway notes.
