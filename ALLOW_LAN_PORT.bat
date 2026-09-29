@echo off
set /p PORT=Enter the portal port (default 5001): 
if "%PORT%"=="" set PORT=5001
echo Adding Windows Firewall rule for TCP port %PORT%...
netsh advfirewall firewall add rule name="College Campus Portal %PORT%" dir=in action=allow protocol=TCP localport=%PORT%
if errorlevel 1 (echo Please right-click this file and choose Run as administrator.) else echo Firewall rule added successfully.
pause
