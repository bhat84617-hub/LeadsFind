@echo off
title LeadsFind - Public Link
cd /d "%~dp0bin"
echo ================================================
echo  LeadsFind PUBLIC ho raha hai...
echo  Ye window BAND mat karna, PC on rakhna!
echo  Neeche wali https link copy karke sabko de do:
echo ================================================
cloudflared.exe tunnel --url http://localhost:8501
pause
