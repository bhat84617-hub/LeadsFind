@echo off
cd /d D:\LeadsFind
if not exist venv (
  echo venv bana raha hoon...
  python -m venv venv
)
call venv\Scripts\activate.bat
pip install -r requirements.txt
if not exist .env copy .env.example .env
if not exist data mkdir data
streamlit run app.py --server.port 8501
