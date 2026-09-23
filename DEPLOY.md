# 🚀 LeadsFind 24/7 Deployment Guide (Hindi)

## Option A — Render FREE (sabse aasan, ₹0) ✅

> 750 free hours/month = ek service 24/7 chalne ke liye poora mahina.
> Neeche wala keep-alive setup free me so jane nahi deta.

### 1. Code GitHub pe dalo
```bat
cd /d D:\LeadsFind
git add .
git commit -m "render deploy: render.yaml + keep-alive health ping"
git push origin main
```

### 2. Render pe deploy
1. [render.com](https://render.com) pe free account banao → **New + → Blueprint**
2. GitHub repo `bhat84617-hub/LeadsFind` connect karo
3. `render.yaml` auto detect hoga → **Apply**
4. Deploy start ho jayega (Docker build ~2-4 min)

### 3. Environment variables (Render Dashboard → Service → Environment)
| Key | Value |
|---|---|
| `ADMIN_PASS` | apna strong password |
| `SERPAPI_API_KEY` | (optional) SerpAPI key |
| `RAZORPAY_KEY_ID` / `RAZORPAY_KEY_SECRET` | (optional) Razorpay test keys |
| `LF_CALLBACK_URL` | `https://<tumhara-app>.onrender.com` |

Save → service auto-redeploy.

### 4. Healthy endpoint (24/7 ka proof)
- `https://<tumhara-app>.onrender.com/_stcore/health` → **200 OK + `ok`**
- Render ise health-check me use karta hai — app crash hui toh turant restart.

### 5. Free me SOOJNE mat do (keep-alive) ⭐
Render free instance **15 min idle pe sleep** ho jata hai (cold start ~50s).
Is repo me GitHub Action `/.github/workflows/keep-alive.yml` hai jo **har 2 min**
health ping karta hai:

1. GitHub repo → **Settings → Secrets and variables → Actions → Variables**
2. New variable: `LEADSFIND_URL` = `https://<tumhara-app>.onrender.com`
3. Done — Actions har 2 min ping karega, app 24/7 awake rahegi.

*(Alternative: [cron-job.org](https://cron-job.org) pe free cron banao, URL = `https://<app>.onrender.com/_stcore/health`, har 2-5 min.)*

> ⚠️ GitHub scheduled workflows 60 din tak koi commit na ho toh band ho jate hain —
> mahine me ek baar koi bhi commit kar dete raho.

### 6. ⚠️ Free plan ki limits (imaan se)
- **Disk ephemeral hai**: `data/leadsfind.db` restart/redeploy pe uad jata hai.
  Paise wale leads/clients ka data chahiye toh Render ka paid plan + Disk lo,
  ya SQLite ko free Postgres (Neon/Supabase) pe le jao.
- Sleep-free rakhne ke liye keep-alive chalna chahiye (step 5).
- `onrender.com` subdomain free, custom domain paid plan me.

---

## Option B — VPS (guaranteed 24/7, data safe)

## 1. Kya-kya chahiye (sirf 3 cheez)

| Cheez | Kahan se | Kharcha (andaza) |
|---|---|---|
| **VPS Server** (24/7 computer) | Hostinger / DigitalOcean / Contabo — 2GB RAM wala plan | ~Rs450–800/month |
| **API Keys** | Koi nahi chahiye! OpenStreetMap + Web Search 100% free hain | Rs0 |
| Domain (optional, professional look) | Hostinger/GoDaddy se `leadsfind.in` jaisa | ~Rs800–1000/saal |

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
