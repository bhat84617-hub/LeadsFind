@echo off
title LeadsFind - Home Google Maps Scraper (Home IP)
cd /d "%~dp0"
if not exist "tools" mkdir tools

if not exist "tools\google-maps-scraper.exe" (
  echo [1/3] Google Maps scraper download ho raha hai (pehli baar ~50MB)...
  powershell -NoProfile -Command "Invoke-WebRequest -Uri 'https://github.com/gosom/google-maps-scraper/releases/download/v1.15.0/google_maps_scraper-1.15.0-windows-amd64.exe' -OutFile 'tools\google-maps-scraper.exe'"
  if not exist "tools\google-maps-scraper.exe" (
    echo DOWNLOAD FAIL - internet check karke dobara chalao.
    pause & exit /b 1
  )
)

echo [2/3] Scraper start ho raha hai (localhost:8080)...
echo       * Pehli baar browser (Chromium) auto-download ho sakta hai - thoda time lagega
echo       * Ye kaam TUMHARE HOME IP se hoga = Google trust karega
start "GMaps-Scraper" tools\google-maps-scraper.exe -web -data-folder "%~dp0gmapsdata" -c 1
timeout /t 8 /nobreak >nul

echo [3/3] Cloudflare tunnel start ho raha hai...
echo.
echo ============================================================
echo  NEECHE doosri window (Cloudflare) me ek link aayega:
echo      https://......trycloudflare.com
echo  Wo copy karke Render me daalo:
echo      Render Dashboard -^> Service -^> Environment -^>
echo      Naya key: GMAPS_BASE_URL   Value: ^<wo https link^>
echo      Save Changes
echo.
echo  IMPORTANT:
echo   - Ye 3 window (Scraper + Cloudflare + ye) BAND mat karna
echo   - PC ON rakhna tabhi Google Maps chalega (nahi toh app
echo     apne aap OpenStreetMap/Web Search pe fallback lega)
echo   - Link restart pe BADAL jata hai - tab wapas set karna
echo   - Link ke paas koi auth nahi hai - kisi ko mat dena
echo ============================================================
start "Cloudflare-Tunnel" bin\cloudflared.exe tunnel --url http://localhost:8080
pause
