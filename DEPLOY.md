# 🚀 LeadsFind 24/7 Deployment Guide (Hindi)

## 1. Kya-kya chahiye (sirf 3 cheez)

| Cheez | Kahan se | Kharcha (andaza) |
|---|---|---|
| **VPS Server** (24/7 computer) | Hostinger / DigitalOcean / Contabo — 2GB RAM wala plan | ~Rs450–800/month |
| **API Keys** | Koi nahi chahiye! OpenStreetMap + Web Search 100% free hain | Rs0 |
| Domain (optional, professional look) | Hostinger/GoDaddy se `leadsfind.in` jaisa | ~Rs800–1000/saal |

> Bina VPS ke free me (Streamlit Cloud/Render) app **so jayega** — 24/7 ke liye VPS hi lo.

## 2. Server pe chalane ke steps

```bash
# 1. Code server pe lao (GitHub pe push karke clone karo)
git clone <tumhara-repo> && cd LeadsFind

# 2. .env banao (apni REAL keys ke saath)
cp .env.example .env
nano .env   # SERPAPI_API_KEY, RAZORPAY_KEY_ID/SECRET, ADMIN_USER/ADMIN_PASS dalo

# 3. Chalao (background me, restart-proof)
docker compose up -d --build

# 4. Dekho: http://TUMHARE-SERVER-IP:8501
docker compose logs -f
```

## 3. Domain + HTTPS (https://leadsfind.in jaisa)

Sabse aasan: **Caddy** (SSL free + auto):
```bash
sudo apt install caddy
# /etc/caddy/Caddyfile me:
# leadsfind.in { reverse_proxy localhost:8501 }
sudo systemctl reload caddy
```
Domain ko server IP pe point karo (A-record) — 10 min me live + 🔒.

## 4. Dhyan rakhne wali baatein

- `data/` folder ka **backup** lete raho (wahi tumhare clients + history hai).
- Sources 100% free hain — koi API bill nahi ayega. Heavy use pe OpenStreetMap
  fair-use aur Web Search rate-limit lag sakta hai; tab thoda ruk ke retry karo.
