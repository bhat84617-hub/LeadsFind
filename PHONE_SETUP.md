# 📱 LeadsFind Phone Server (Termux) — Hindi Guide

> ⚠️ Sach: 24/7 charging se battery phoolne ka khatra hai. **Purana spare phone** use karo,
> charger pe ventilated jagah rakho, roz check karo. Ye jugaad hai, permanent hal VPS hai.

## Step 1 — Termux install karo
- Play Store wala PURANA hai — GitHub/F-Droid se latest Termux + Termux:Boot lo.

## Step 2 — Ye commands ek-ek karke chalao
```bash
pkg update -y && pkg upgrade -y
pkg install -y python git cloudflared
git clone https://github.com/bhat84617-hub/LeadsFind.git
cd LeadsFind
pip install -r requirements.txt
```

## Step 3 — App chalao (Web Search source = bina key ke chalega)
```bash
streamlit run app.py --server.port 8501
```
Phone ke browser me kholo: `http://localhost:8501`

## Step 4 — Public link (sabko dene ke liye)
Nayi Termux window (swipe + New session):
```bash
cloudflared tunnel --url http://localhost:8501
```
Jo `https://...trycloudflare.com` link aaye — wahi public link hai.

## Step 5 — Band na ho (jitna ho sake)
```bash
termux-wake-lock
```
- Phone Settings → Battery → Termux ko **Unrestricted** karo
- Charger lagake rakho, screen timeout lamba karo

## ATM — Agar koi step fail ho to uska error bhejo, fix kar dunga.
