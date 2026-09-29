# College Campus Portal — Local LAN Fix

## Why the old LAN page failed
The local URL is plain HTTP (`http://192.168.x.x:PORT`). A Secure session cookie is not sent over HTTP, which can cause `Invalid CSRF token`, roster loading failures and login/OTP session errors. This build automatically disables the Secure flag for HTTP LAN requests and uses a new session cookie name.

## Run
1. Stop the old Flask process with Ctrl+C.
2. Make sure `.env` contains your local MySQL settings and `SESSION_COOKIE_SECURE=0`.
3. Run `python portal.py`.
4. Open `http://127.0.0.1:5001` on the laptop.
5. For phone access, use the **laptop's IPv4 address**, not the phone hotspot gateway: `http://LAPTOP_IPV4:5001`.
6. If Windows Firewall blocks the phone, right-click `ALLOW_LAN_PORT.bat` and run it as Administrator, then enter `5001` (or the port shown by Flask).

## Important
If the phone still cannot reach the laptop after the firewall rule, the hotspot may have client/device isolation. That is a network restriction, not a Flask application error.

## Cloud
For HTTPS hosting, set `SESSION_COOKIE_SECURE=1`.
