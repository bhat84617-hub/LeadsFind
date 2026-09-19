# 🔍 LeadsFind (LF) — Local Leads SaaS

`D:\Scrapegraph-ai` ke lead-scripts ka SaaS version:
- `serpapi_ghaziabad_200.py` → `lf_core/scrapers.py::serpapi_fetch()` (ab koi bhi city+business)
- `free_ghaziabad_overpass.py` → `overpass_fetch()`
- `filter_no_website.py` + CSV → SQLite (`lf_core/database.py`) taaki **dashboard + history** chale
- `local_leads_app.py` → `app.py` (login + plan + search + history + pricing)

Pura 664MB project copy **nahi** kiya (venv 640MB bekar me bhari hota).
Sirf kaam ka logic copy karke naya halka SaaS banaya hai.

## Features (tumhari demand)
1. Customer: **Location + Place name + Business profession + Platform** select kare
2. **Subscription ke hisab se** leads auto nikle (FREE 20, STARTER 100, PRO 500, AGENCY 2000)
3. Leads **dashboard me** aaye + **history me** save ho (SQLite `data/leadsfind.db`)
4. CSV download

## Run
```bat
cd /d D:\LeadsFind
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
streamlit run app.py
```
Phir browser me `http://localhost:8501`

## Paisa kaise kamana hai
- Pricing page me 4 plans hain. Razorpay/Stripe button jod ke customer se Rs499-4999/mo lo.
- Tumhara cost: SerpAPI free 100 searches, uske baad ~$50/250 searches. Isliye PRO/AGENCY me margin rakho, ya Overpass-Free default rakho.
