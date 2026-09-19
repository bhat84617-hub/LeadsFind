@echo off
title LeadsFind App
cd /d D:\LeadsFind
echo ================================================
echo  LeadsFind app shuru ho rahi hai...
echo  Ye window KHULI rakho! Band ki = app band.
echo  Browser me kholo: http://localhost:8501
echo ================================================
python -m streamlit run app.py --server.port 8501
pause
