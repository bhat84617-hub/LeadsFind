"""LeadsFind (LF) - Professional SaaS.
Run: streamlit run app.py
Client: Register -> 5 FREE leads (one-time) -> Buy pack (300/800/1800) ->
        search jitni leads, quota me se kat ti jayengi -> History + download.
Admin (tum): API keys, users, payments — sirf admin panel me.
"""
import os
import re
import secrets as _pylib_secrets
import pandas as pd
import streamlit as st
from streamlit_option_menu import option_menu
from dotenv import load_dotenv

from lf_core.database import (init_db, register_user, login_user, get_user,
                              set_plan, quota_remaining, add_quota,
                              user_stats, save_search, get_history,
                              get_leads_of_search, get_all_leads,
                              create_subscription, mark_paid,
                              latest_subscription, subscription_history,
                              all_users, total_revenue, all_subscriptions)
from lf_core.plans import PLANS, PAID_PLANS, get_plan
from lf_core.scrapers import (fetch_leads, fetch_bulk, web_bulk, apply_filters,
                              SOURCES, NOTICE)
from lf_core.billing import (is_configured, create_payment_link,
                             fetch_link_status)

load_dotenv(override=True)
init_db()

ADMIN_USER = os.getenv("ADMIN_USER", "admin").strip().lower()
ADMIN_PASS = os.getenv("ADMIN_PASS", "admin123")
SERPAPI_KEY = os.getenv("SERPAPI_API_KEY", "")

MENU_STYLE = {
    "container": {"padding": "0!important", "background-color": "transparent"},
    "icon": {"color": "#ffcf3f", "font-size": "18px"},
    "nav-link": {"color": "#eafff8", "font-size": "15px", "font-weight": "600",
                 "text-align": "left", "margin": "3px 0",
                 "--hover-color": "rgba(255,255,255,.12)"},
    "nav-link-selected": {"background-color": "#ffcf3f", "color": "#0d2b26",
                          "font-weight": "800"},
}


def google_auth_ready() -> bool:
    """Streamlit Secrets me [auth.google] keys hain? (Cloud dashboard ya local secrets.toml)"""
    try:
        g = st.secrets.get("auth", {}).get("google", {})
        return bool(g.get("client_id") and g.get("client_secret"))
    except Exception:
        return False

st.set_page_config(page_title="LeadsFind — Local Leads, Instant",
                   page_icon="🔍", layout="wide")

st.markdown("""<style>
.lf-head{background:linear-gradient(100deg,#0f2027,#203a43 55%,#0d6e5f);
 color:#fff;padding:20px 24px;border-radius:16px;margin-bottom:16px}
.lf-head h1{margin:0;font-size:30px}
.lf-head p{margin:6px 0 0;opacity:.9}
.badge{display:inline-block;padding:3px 14px;border-radius:20px;font-size:13px;
 font-weight:800;background:#ffcf3f;color:#222;margin-left:10px;vertical-align:middle}
.plan-card{background:#fff;border:2px solid #e5e9f0;border-radius:14px;
 padding:18px;text-align:center}
.plan-card.hot{border-color:#0d6e5f;box-shadow:0 4px 18px rgba(13,110,95,.18)}
.plan-price{font-size:30px;font-weight:800;color:#0d2b26}
.plan-leads{font-size:15px;color:#0d6e5f;font-weight:700}
.small{font-size:12px;color:#666}
.quota-bar{font-size:14px;font-weight:700}
.lead-card{background:#fff;border:1px solid #e5e9f0;border-radius:14px;
 padding:14px 16px;margin-bottom:10px;box-shadow:0 2px 8px rgba(0,0,0,.05)}
.lead-card b.nm{font-size:16px;color:#0d2b26}
.src{font-size:11px;background:#eef4f3;color:#0d6e5f;border-radius:10px;
 padding:2px 10px;font-weight:700}
.btn{display:inline-block;margin:6px 6px 0 0;padding:6px 14px;border-radius:20px;
 font-size:13px;font-weight:700;text-decoration:none}
.btn-call{background:#0d6e5f;color:#fff!important}
.btn-wa{background:#25D366;color:#fff!important}
.btn-web{background:#eef4f3;color:#0d6e5f!important}
.glass-wrap{display:flex;flex-direction:column;
 align-items:center;justify-content:flex-start;padding:0 10px}
.hero-title{font-size:clamp(36px,7vw,62px);font-weight:900;color:#fff;text-align:center;
 margin:0;text-shadow:0 4px 24px rgba(0,0,0,.35);letter-spacing:-1px;line-height:1.05}
.hero-sub{color:#eafff8;text-align:center;font-size:clamp(15px,2.5vw,19px);margin:8px 0 2px}
.feat{display:inline-block;background:rgba(255,255,255,.2);
 border:1px solid rgba(255,255,255,.35);color:#fff;border-radius:20px;
 padding:5px 16px;margin:4px;font-size:13px;font-weight:600}
h1,h2,h3{color:#0d2b26!important;letter-spacing:-.5px}
.lf-head.big{padding:26px 28px}
.lf-head.big h1{font-size:32px}
.stat{background:linear-gradient(135deg,#ffffff,#eefaf5);border:1px solid #dcebe5;
 border-radius:16px;padding:14px 8px;text-align:center;
 box-shadow:0 3px 12px rgba(13,110,95,.10)}
.sv{display:block;font-size:32px;font-weight:900;color:#0d2b26;line-height:1.1}
.sl{font-size:13px;color:#0d6e5f;font-weight:700}
.panel{background:#fff;border:1px solid #e5e9f0;border-top:5px solid #0d6e5f;
 border-radius:16px;padding:16px 20px;margin:14px 0;
 box-shadow:0 4px 16px rgba(0,0,0,.05)}
.panel-t{font-size:21px;font-weight:800;color:#0d2b26}
.panel-s{font-size:14px;color:#555;margin-top:4px}
.sec-title{text-align:center;color:#fff;font-size:24px;font-weight:800;
 margin:28px 0 14px;text-shadow:0 2px 12px rgba(0,0,0,.3)}
.step{background:rgba(255,255,255,.14);backdrop-filter:blur(14px);
 -webkit-backdrop-filter:blur(14px);border:1px solid rgba(255,255,255,.35);
 border-radius:18px;padding:18px 12px;text-align:center;color:#fff;min-height:140px}
.step-n{width:38px;height:38px;border-radius:50%;background:#ffcf3f;color:#222;
 font-weight:900;font-size:19px;display:flex;align-items:center;
 justify-content:center;margin:0 auto 8px}
.step span{font-size:13px;opacity:.92}
.mini-price{background:rgba(255,255,255,.14);border:1px solid rgba(255,255,255,.35);
 border-radius:14px;padding:12px 6px;text-align:center;color:#fff;font-size:12px}
.mini-price .mp{font-size:19px;font-weight:900}
.trust{text-align:center;color:#dff5ec;font-size:13px;margin-top:20px}
[data-testid="stSidebar"]{background:linear-gradient(180deg,#0f2027 0%,
 #203a43 55%,#0d6e5f 100%)}
.profile{text-align:center;padding:18px 10px 14px;
 background:rgba(255,255,255,.10);border:1px solid rgba(255,255,255,.25);
 border-radius:18px;margin-bottom:12px}
.avatar{width:62px;height:62px;border-radius:50%;
 background:linear-gradient(135deg,#ffcf3f,#ff9a3f);color:#0d2b26;font-size:28px;
 font-weight:900;display:flex;align-items:center;justify-content:center;margin:0 auto 8px}
.pname{color:#fff;font-weight:800;font-size:17px;word-break:break-all}
.pplan{display:inline-block;background:#ffcf3f;color:#0d2b26;font-size:12px;
 font-weight:800;border-radius:12px;padding:2px 14px;margin-top:5px}
.qbar{background:rgba(255,255,255,.20);border-radius:8px;height:8px;
 margin:10px 4px 5px;overflow:hidden}
.qfill{background:linear-gradient(90deg,#ffcf3f,#ff9a3f);height:100%;border-radius:8px}
.pq{color:#dff5ec;font-size:12px;font-weight:600}
.sup{color:#bfe6d8;font-size:12px;text-align:center;margin-top:10px}
</style>""", unsafe_allow_html=True)

if "username" not in st.session_state:
    st.session_state.username = None
if "is_admin" not in st.session_state:
    st.session_state.is_admin = False
if "last_df" not in st.session_state:
    st.session_state.last_df = None
if "last_sid" not in st.session_state:
    st.session_state.last_sid = None
if "go_billing" not in st.session_state:
    st.session_state.go_billing = False
if "google_login" not in st.session_state:
    st.session_state.google_login = False

# ================= AUTH (glassmorphism home) =================
if not st.session_state.username:
    # Google se wapas aaye ho? -> auto login
    if google_auth_ready():
        try:
            if st.user.is_logged_in and (st.user.email or "").strip():
                em = st.user.email.strip().lower()
                try:
                    register_user(em, _pylib_secrets.token_urlsafe(16), em, "")
                except Exception:
                    pass
                st.session_state.username = em
                st.session_state.is_admin = False
                st.session_state.google_login = True
                st.rerun()
        except Exception:
            pass
    st.markdown("""<style>
[data-testid="stAppViewContainer"]{background:linear-gradient(135deg,#0f2027 0%,
 #203a43 40%,#0d6e5f 75%,#0aa37e 100%)}
[data-testid="stHeader"]{background:transparent}
[data-testid="stSidebar"]{display:none}
[data-testid="block-container"]{padding-top:1rem!important;max-width:1100px}
div[data-testid="stVerticalBlockBorderWrapper"]{background:rgba(255,255,255,.93);
 backdrop-filter:blur(18px);-webkit-backdrop-filter:blur(18px);
 border:1px solid rgba(255,255,255,.65);border-radius:22px;
 box-shadow:0 12px 44px rgba(0,0,0,.28)}
.sec-title{text-align:center;color:#fff;font-size:clamp(19px,3.5vw,24px);font-weight:800;
 margin:20px 0 12px;text-shadow:0 2px 12px rgba(0,0,0,.3)}
@media (max-width:640px){
 .glass{padding:22px 18px;border-radius:18px}
 .step{min-height:0;margin-bottom:8px}
 .mini-price{margin-bottom:8px}
 .lf-head.big{padding:18px}
 .lf-head.big h1{font-size:24px}
 .sv{font-size:26px}
}
</style>
<div class="glass-wrap">
<div class="hero-title">🔍 LeadsFind</div>
<div class="hero-sub">Local business leads — city + business dalo, leads turant pao.</div>
<div style="text-align:center;margin:10px 0 18px">
<span class="feat">🎁 Signup pe 5 leads FREE</span>
<span class="feat">📞 Number + 🌐 Website filters</span>
<span class="feat">💳 Rs299 se packs</span>
</div>
</div>""", unsafe_allow_html=True)
    _, mid, _ = st.columns([1, 2, 1])
    with mid:
        with st.container(border=True):
            if google_auth_ready():
                if st.button("🔵 Continue with Google", use_container_width=True,
                             type="primary"):
                    st.login("google")
                st.markdown("<p style='text-align:center;margin:6px 0'>— ya —</p>",
                            unsafe_allow_html=True)
            t1, t2 = st.tabs(["🔑 Login", "📝 Naya Account"])
            with t1:
                u = st.text_input("Username", key="li_u")
                p = st.text_input("Password", type="password", key="li_p")
                if st.button("Login ➜", type="primary", use_container_width=True):
                    try:
                        if u.strip().lower() == ADMIN_USER and p == ADMIN_PASS:
                            st.session_state.username = ADMIN_USER
                            st.session_state.is_admin = True
                            st.rerun()
                        user = login_user(u, p)
                        st.session_state.username = user["username"]
                        st.session_state.is_admin = False
                        st.rerun()
                    except Exception as e:
                        st.error(str(e))
            with t2:
                u = st.text_input("Username chuno", key="rg_u")
                p = st.text_input("Password (min 4 char)", type="password", key="rg_p")
                e = st.text_input("Email", key="rg_e")
                ph = st.text_input("Mobile (10 digit)", key="rg_ph")
                if st.button("Account banao — 5 FREE leads 🎁", type="primary",
                             use_container_width=True):
                    try:
                        register_user(u, p, e, ph)
                        st.session_state.username = u.strip().lower()
                        st.session_state.is_admin = False
                        st.success("Account ban gaya! 5 FREE leads active 🎉")
                        st.rerun()
                    except Exception as ex:
                        st.error(str(ex))
    st.markdown('<div class="sec-title">⚡ Sirf 3 step me leads</div>',
                unsafe_allow_html=True)
    s1, s2, s3 = st.columns(3)
    s1.markdown('<div class="step"><div class="step-n">1</div><b>Account banao</b><br>'
                '<span>2 minute me signup,<br><b>5 leads FREE</b> 🎁</span></div>',
                unsafe_allow_html=True)
    s2.markdown('<div class="step"><div class="step-n">2</div><b>City + Business dalo</b><br>'
                '<span>Delhi + dentist +<br>apne ticks lagao ✅</span></div>',
                unsafe_allow_html=True)
    s3.markdown('<div class="step"><div class="step-n">3</div><b>Leads pao</b><br>'
                '<span>Call / WhatsApp karo,<br>CSV download ⬇️</span></div>',
                unsafe_allow_html=True)
    st.markdown('<div class="sec-title">💎 Packs — sirf Rs49 se shuru</div>',
                unsafe_allow_html=True)
    pc = st.columns(len(PLANS))
    for i, (k, p) in enumerate(PLANS.items()):
        with pc[i]:
            tag = "🔥 " if k == "OFFER" else ""
            price = "FREE" if p["price_inr"] == 0 else f"Rs{p['price_inr']}"
            st.markdown(f'<div class="mini-price">{tag}<b>{k}</b><br>'
                        f'<span class="mp">{price}</span><br>'
                        f'<span>{p["total_leads"]} leads</span></div>',
                        unsafe_allow_html=True)
    st.markdown('<p class="trust">🔒 Secure Razorpay payments &nbsp;•&nbsp; '
                '⚡ Turant delivery &nbsp;•&nbsp; 🇮🇳 Hindi support<br>'
                'LeadsFind © 2026 • Apna data, apna business 🚀</p>',
                unsafe_allow_html=True)
    st.stop()

username = st.session_state.username
is_admin = st.session_state.is_admin

# ================= ADMIN PANEL (sirf tum) =================
if is_admin:
    st.markdown('<div class="lf-head"><h1>🛠️ LeadsFind Admin'
                '<span class="badge">OWNER</span></h1>'
                f'<p>Logged in: <b>{username}</b> — ye panel sirf tum dekh sakte ho.</p></div>',
                unsafe_allow_html=True)
    with st.sidebar:
        st.markdown('<div class="profile"><div class="avatar">A</div>'
                    '<div class="pname">Admin</div>'
                    '<div class="pplan">OWNER</div></div>', unsafe_allow_html=True)
        _asel = option_menu("LeadsFind", ["Overview", "Clients", "Payments",
                                          "API Keys", "Logout"],
                            icons=["speedometer2", "people-fill", "cash-coin",
                                   "key-fill", "box-arrow-right"],
                            menu_icon="shield-lock-fill", default_index=0,
                            styles=MENU_STYLE, key="admin_menu")
    _amap = {"Overview": "📊 Overview", "Clients": "👥 Clients",
             "Payments": "💰 Payments", "API Keys": "🔑 API Keys & Setup",
             "Logout": "🚪 Logout"}
    amenu = _amap[_asel]
    if amenu == "🚪 Logout":
        st.session_state.username = None
        st.session_state.is_admin = False
        st.rerun()

    if amenu == "📊 Overview":
        users = all_users()
        total_leads = sum(user_stats(u["username"])["leads"] for u in users)
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Clients", len(users))
        c2.metric("Revenue (paid)", f"Rs{total_revenue()}")
        c3.metric("Leads nikali", total_leads)
        c4.metric("Razorpay", "LIVE ✅" if is_configured() else "OFF — keys dalo")
        st.dataframe(pd.DataFrame(users), use_container_width=True)

    elif amenu == "👥 Clients":
        st.subheader("Clients — quota / plan manage karo")
        users = all_users()
        for u in users:
            if u["username"] == ADMIN_USER:
                continue
            with st.expander(f"{u['username']} | plan {u.get('plan')} | "
                             f"quota {u.get('leads_quota')} | used {u.get('leads_used')}"):
                c1, c2 = st.columns(2)
                with c1:
                    np = st.selectbox("Plan", list(PLANS.keys()), key=f"pl{u['username']}")
                    if st.button("Plan set karo", key=f"ps{u['username']}"):
                        set_plan(u["username"], np)
                        st.success("Done")
                        st.rerun()
                with c2:
                    extra = st.number_input("Credits add karo", 0, 10000, 100,
                                            key=f"ex{u['username']}")
                    if st.button("Credits add karo", key=f"ad{u['username']}"):
                        add_quota(u["username"], int(extra))
                        st.success(f"{extra} credits add!")
                        st.rerun()

    elif amenu == "💰 Payments":
        st.subheader("Saare payments")
        subs = all_subscriptions()
        st.metric("Revenue (paid)", f"Rs{total_revenue()}")
        if subs:
            st.dataframe(pd.DataFrame(subs), use_container_width=True)

    else:  # API keys — sirf yahin dikhega, user ko kabhi nahi
        st.subheader("🔑 API Keys & Setup (secret — sirf tum)")
        st.write(f"SerpAPI: {'✅ set hai' if SERPAPI_KEY else '❌ missing — .env me SERPAPI_API_KEY dalo'}")
        st.write(f"Razorpay: {'✅ LIVE' if is_configured() else '❌ missing — .env me RAZORPAY_KEY_ID/SECRET dalo'}")
        with st.expander("Razorpay keys kaise laaye?"):
            st.write("1. razorpay.com → Settings → API Keys → Test Mode keys banao\n"
                     "2. `D:\\LeadsFind\\.env` me dalo:\n"
                     "`RAZORPAY_KEY_ID=rzp_test_...` , `RAZORPAY_KEY_SECRET=...`\n"
                     "3. App restart karo. Pehle Rs1 ka test payment khud karke verify karo.")
    st.stop()

# ================= CLIENT APP =================
user = get_user(username) or {"username": username, "plan": "FREE",
                              "leads_quota": 5, "leads_used": 0}
stats = user_stats(username)
remaining = stats["remaining"]

st.markdown(f'<div class="lf-head big"><h1>👋 Namaste, {username}!'
            f'<span class="badge">{user.get("plan", "FREE")}</span></h1>'
            f'<p>Aapke paas <b>💎 {remaining} leads</b> bachi hain '
            f'({stats["used"]}/{stats["quota"]} used) — aaj hi nikalo!</p></div>',
            unsafe_allow_html=True)
st.progress(min(1.0, (stats["used"] / stats["quota"]) if stats["quota"] else 0))

pct = min(100, int((stats["used"] / stats["quota"] * 100))) if stats["quota"] else 0
with st.sidebar:
    st.markdown(f'''<div class="profile"><div class="avatar">{username[0].upper()}</div>
<div class="pname">{username}</div>
<div class="pplan">{user.get("plan", "FREE")}</div>
<div class="qbar"><div class="qfill" style="width:{pct}%"></div></div>
<div class="pq">💎 {remaining} / {stats["quota"]} leads bachi</div></div>''',
                unsafe_allow_html=True)
    _force = "Buy Leads" if st.session_state.go_billing else None
    st.session_state.go_billing = False
    _sel = option_menu("Menu", ["Dashboard", "My Leads", "History",
                                "Buy Leads", "Logout"],
                       icons=["grid-1x2-fill", "folder-fill", "clock-history",
                              "gem", "box-arrow-right"],
                       menu_icon="person-circle", default_index=0,
                       manual_select=_force, styles=MENU_STYLE, key="main_menu")
    st.markdown('<div class="sup">Support: care@leadsfind.in</div>',
                unsafe_allow_html=True)
_cmap = {"Dashboard": "📊 Dashboard", "My Leads": "📁 My Leads",
         "History": "📜 History", "Buy Leads": "💎 Buy Leads",
         "Logout": "🚪 Logout"}
menu = _cmap[_sel]
if menu == "🚪 Logout":
    if st.session_state.google_login:
        try:
            st.logout()
        except Exception:
            pass
    for k in ("username", "is_admin", "last_df", "last_sid", "google_login"):
        st.session_state[k] = None if k not in ("is_admin", "google_login") else False
    st.rerun()

# ---------- Dashboard ----------
if menu == "📊 Dashboard":
    q1, q2, q3, q4 = st.columns(4)
    q1.markdown(f'<div class="stat"><span class="sv">💎 {remaining}</span>'
                '<span class="sl">Bachi leads</span></div>', unsafe_allow_html=True)
    q2.markdown(f'<div class="stat"><span class="sv">{stats["leads"]}</span>'
                '<span class="sl">Total nikali</span></div>', unsafe_allow_html=True)
    q3.markdown(f'<div class="stat"><span class="sv">📞 {stats["with_phone"]}</span>'
                '<span class="sl">Number wali</span></div>', unsafe_allow_html=True)
    q4.markdown(f'<div class="stat"><span class="sv">🚫 {stats["no_website"]}</span>'
                '<span class="sl">Bina website</span></div>', unsafe_allow_html=True)

    if remaining <= 0:
        st.error("😔 Aapki leads khatm ho gayi!")
        if st.button("💎 Abhi Leads Kharido", type="primary"):
            st.session_state.go_billing = True
            st.rerun()
        st.stop()

    st.markdown(f'<div class="panel"><div class="panel-t">🔎 Nayi leads nikalo</div>'
                f'<div class="panel-s">Har lead = 1 credit. Example: Delhi 50 + Dehradun 70 '
                f'= 120 credits. Aapke paas <b>{remaining}</b> bachi hain.</div></div>',
                unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        location = st.text_input("City *", value="Delhi")
        place_name = st.text_input("Area (optional)", value="",
                                   help="Jaise: Karol Bagh, Laxmi Nagar")
    with c2:
        business = st.text_input("Business *", value="dentist",
                                 help="dentist, gym, salon, astrologer, restaurant...")
        _srcs = [k for k in SOURCES
                 if k not in ("serpapi", "justdial") or SERPAPI_KEY.strip()]
        platform = st.selectbox("Source (kahan se nikale?)", _srcs,
                                format_func=lambda p: SOURCES[p],
                                index=0,
                                help="Bina-website client chahiye toh Google Maps ya "
                                     "OpenStreetMap best hai. Web Search me almost "
                                     "har lead website rakhti hai.")
    hints = {
        "gmaps_free": "🆓 Asli Google Maps — free; bina-website + number dono milte hain.",
        "overpass": "🗺️ OpenStreetMap — free; bina-website business milne ke best.",
        "serpapi": "📍 Naam + phone + website + rating — best quality (SerpAPI key chahiye).",
        "justdial": "📞 JD-listed shops — naam + address pakka.",
        "web": "🌐 Websites wali leads — 'Bina website wale' tick ke saath 0 dega.",
    }
    st.caption(hints.get(platform, ""))

    st.write("**✅ Apni marzi ke ticks lagao:**")
    t1, t2, t3 = st.columns(3)
    with t1:
        need_phone = st.checkbox("📞 Number wale hi", value=False,
                                 help="Sirf phone-number wali leads")
    with t2:
        want_with = st.checkbox("🌐 Website wale", value=True,
                                help="Jinki website bani hai")
    with t3:
        want_without = st.checkbox("🚫 Bina website wale", value=True,
                                   help="Jinki website nahi — bechne ke best client!")
    if remaining <= 0:
        st.warning("💎 Credits khatam ho gaye — pehle **💎 Buy Leads** se pack lo, "
                   "phir search karein.")
        st.stop()
    asked = st.number_input("Kitni leads? (credits katega)", 1, max(1, remaining),
                            value=min(20, remaining))

    if st.button("🚀 Leads Nikalo", type="primary"):
        if not location.strip() or not business.strip():
            st.error("City aur Business dono bharo.")
            st.stop()
        buffer_n = min(int(asked) * 2 + 10, 200)
        bulk = int(asked) > 60 and platform in ("serpapi", "web")
        with st.spinner(f"{asked} leads nikal rahe hain "
                        f"({'bulk mode: kayi rounds (FREE)' if bulk else SOURCES[platform].split('—')[0].strip()})..."):
            try:
                if bulk and platform == "web":
                    raw = web_bulk(location.strip(), business.strip(),
                                   place_name.strip(), int(asked) + 50)
                elif bulk:
                    raw = fetch_bulk(location.strip(), business.strip(),
                                     place_name.strip(), int(asked) + 30, SERPAPI_KEY)
                else:
                    raw = fetch_leads(platform, location.strip(), business.strip(),
                                      place_name.strip(), buffer_n, SERPAPI_KEY)
                leads = apply_filters(raw, need_phone, want_with, want_without)[:int(asked)]
            except Exception as e:
                st.error(f"Fail: {e}")
                st.stop()
        if NOTICE["msg"]:
            st.info(NOTICE["msg"])
            NOTICE["msg"] = ""
        if not leads:
            hp = sum(1 for L in raw if (L.get("phone") or "").strip())
            hs = sum(1 for L in raw if (L.get("website") or "")
                     not in ("", "NO WEBSITE"))
            st.warning(
                f"Filter me kuch nahi mila ({len(raw)} raw me se 0). "
                f"Raw me: **{hp}** ke paas number, **{hs}** ke paas website thi.")
            if want_without and not want_with:
                st.info("💡 Tum sirf **'Bina website wale'** chahte ho — par is source "
                        "ki almost har lead website rakhti hai. **2 me se 1 chuno:**\n"
                        "- Source **Google Maps** ya **OpenStreetMap** rakho "
                        "(unme sach me bina-website business milte hain), ya\n"
                        "- Dono website ticks **ON** kar do (website wali leads bhi chalegi).")
            else:
                st.info("Ticks badal ke dekho — dono website tick = sab (filter off).")
            st.stop()
        if len(leads) < asked:
            st.info(f"Filter ke baad {len(leads)} mili ({len(raw)} me se) — "
                    f"utne hi credits katega.")
        sid = save_search(username, location, place_name, business,
                          platform, int(asked), leads)
        st.session_state.last_df = pd.DataFrame(leads)
        st.session_state.last_sid = sid
        left = quota_remaining(username)
        st.success(f"✅ Search #{sid}: {len(leads)} leads save! 💎 {left} bachi.")

    df = st.session_state.last_df
    if df is not None:
        r1, r2, r3, r4 = st.columns(4)
        r1.markdown(f'<div class="stat"><span class="sv">{len(df)}</span>'
                    '<span class="sl">Mili</span></div>', unsafe_allow_html=True)
        r2.markdown(f'<div class="stat"><span class="sv">📞 '
                    f'{int((df["phone"].astype(str).str.strip() != "").sum())}</span>'
                    '<span class="sl">Number</span></div>', unsafe_allow_html=True)
        r3.markdown(f'<div class="stat"><span class="sv">🌐 '
                    f'{int((df["website"] != "NO WEBSITE").sum())}</span>'
                    '<span class="sl">Website</span></div>', unsafe_allow_html=True)
        r4.markdown(f'<div class="stat"><span class="sv">🚫 '
                    f'{int((df["website"] == "NO WEBSITE").sum())}</span>'
                    '<span class="sl">Bina website</span></div>', unsafe_allow_html=True)
        view = st.radio("View", ["📋 Table", "🃏 Cards (Call/WhatsApp)"],
                        horizontal=True)
        q = st.text_input("Filter")
        show = df[df.apply(lambda r: q.lower() in str(r.values).lower(), axis=1)] if q else df
        if view.startswith("📋"):
            st.dataframe(show, use_container_width=True, height=450)
        else:
            for _, L in show.head(30).iterrows():
                ph = str(L.get("phone", "")).strip()
                digits = re.sub(r"\D", "", ph)
                if len(digits) == 10:
                    digits = "91" + digits
                btns = ""
                if ph and digits:
                    btns += (f'<a class="btn btn-call" href="tel:+{digits}">📞 Call</a>'
                             f'<a class="btn btn-wa" href="https://wa.me/{digits}" '
                             f'target="_blank">💬 WhatsApp</a>')
                if str(L.get("website", "")) not in ("", "NO WEBSITE"):
                    btns += (f'<a class="btn btn-web" href="{L.get("website")}" '
                             f'target="_blank">🌐 Website</a>')
                st.markdown(
                    f'<div class="lead-card"><b class="nm">{L.get("business_name", "")}</b> '
                    f'<span class="src">{L.get("source", "")}</span><br>'
                    f'<span class="small">📍 {L.get("address", "")}'
                    f'{" | ⭐ " + str(L.get("rating", "")) if L.get("rating", "") else ""}'
                    f'{" | 📞 " + ph if ph else ""}</span><br>{btns}</div>',
                    unsafe_allow_html=True)
            if len(show) > 30:
                st.caption("Pehli 30 cards dikh rahi hain — baaki Table/CSV me dekho.")
        st.download_button("⬇ CSV Download", show.to_csv(index=False).encode("utf-8"),
                           f"LF_{username}_{st.session_state.last_sid}.csv", "text/csv")

# ---------- My Leads ----------
elif menu == "📁 My Leads":
    st.markdown('<div class="panel"><div class="panel-t">📁 Meri saari leads</div>'
                '<div class="panel-s">Ab tak ki sabhi leads — filter karo, download karo.</div></div>',
                unsafe_allow_html=True)
    all_leads = get_all_leads(username)
    if not all_leads:
        st.info("Abhi koi lead nahi. Dashboard se pehli search chalao (5 FREE).")
    else:
        df = pd.DataFrame(all_leads).drop(
            columns=["id", "search_id", "extra"], errors="ignore")
        f1, f2, f3 = st.columns(3)
        with f1:
            only_phone = st.checkbox("📞 Number wale hi", key="ml_phone")
        with f2:
            only_with = st.checkbox("🌐 Website wale", key="ml_with")
        with f3:
            only_nosite = st.checkbox("🚫 Bina website", key="ml_without")
        if only_phone:
            df = df[df["phone"].astype(str).str.strip() != ""]
        if only_with and not only_nosite:
            df = df[df["website"] != "NO WEBSITE"]
        if only_nosite and not only_with:
            df = df[df["website"] == "NO WEBSITE"]
        q = st.text_input("Search")
        if q:
            df = df[df.apply(lambda r: q.lower() in str(r.values).lower(), axis=1)]
        st.caption(f"{len(df)} leads | 💎 {remaining} bachi")
        st.dataframe(df, use_container_width=True, height=500)
        st.download_button("⬇ Saari Leads CSV", df.to_csv(index=False).encode("utf-8"),
                           f"LF_{username}_all.csv", "text/csv")

# ---------- History ----------
elif menu == "📜 History":
    st.markdown('<div class="panel"><div class="panel-t">📜 History</div>'
                '<div class="panel-s">Har search ka poora hisaab — dobara download karo.</div></div>',
                unsafe_allow_html=True)
    hist = get_history(username)
    if not hist:
        st.info("Koi history nahi.")
    else:
        for h in hist:
            with st.expander(f"#{h['id']} | {h['created_at']} | "
                             f"{h['business']} in {h['location']} ({h['place_name']}) | "
                             f"{h['got']} leads"):
                leads = get_leads_of_search(h["id"])
                if leads:
                    df = pd.DataFrame(leads).drop(
                        columns=["id", "search_id", "extra"], errors="ignore")
                    st.dataframe(df, use_container_width=True, height=300)
                    st.download_button(f"⬇ CSV #{h['id']}",
                                       df.to_csv(index=False).encode("utf-8"),
                                       f"LF_history_{h['id']}.csv", "text/csv",
                                       key=f"dl{h['id']}")

# ---------- Buy Leads ----------
else:
    st.markdown('<div class="panel"><div class="panel-t">💎 Leads Kharido</div>'
                '<div class="panel-s">Payment ke <b>turant</b> credits add — Rs49 se shuru.</div></div>',
                unsafe_allow_html=True)
    st.caption(f"Plan: **{user.get('plan')}** | 💎 {remaining} bachi "
               f"({stats['used']}/{stats['quota']} used)")
    cols = st.columns(len(PAID_PLANS))
    for i, k in enumerate(PAID_PLANS):
        p = PLANS[k]
        per = p["price_inr"] / p["total_leads"]
        with cols[i]:
            hot = " hot" if k == "PRO" else ""
            tag = "🔥 SPECIAL<br>" if k == "OFFER" else ""
            st.markdown(f'<div class="plan-card{hot}">{tag}<b>{k}</b><br>'
                        f'<span class="plan-price">Rs{p["price_inr"]}</span><br>'
                        f'<span class="plan-leads">{p["total_leads"]} leads</span><br>'
                        f'<span class="small">~Rs{per:.2f}/lead</span></div>',
                        unsafe_allow_html=True)
            if st.button(f"Buy {k}", key=f"buy{k}", type="primary" if k == "PRO" else "secondary"):
                if not is_configured():
                    st.error("Online payment jald live hoga. Support se sampark karo.")
                else:
                    try:
                        link = create_payment_link(username, k, p["price_inr"],
                                                   user.get("email", ""),
                                                   user.get("phone", ""))
                        create_subscription(username, k, p["price_inr"],
                                            link["link_id"], link["link_url"])
                        st.success("Link ban gaya! Neeche Pay karo.")
                        st.rerun()
                    except Exception as e:
                        st.error(str(e))

    sub = latest_subscription(username)
    if sub and sub["status"] == "created" and is_configured():
        st.divider()
        st.link_button(f"💰 Pay Rs{sub['amount_inr']} — {sub['plan']} "
                       f"({PLANS[sub['plan']]['total_leads']} leads)", sub["link_url"])
        if st.button("✅ Payment ho gaya — Credits pao", type="primary"):
            try:
                stt = fetch_link_status(sub["link_id"])
                if stt["status"] == "paid":
                    mark_paid(sub["link_id"], sub["plan"], username)
                    st.success(f"🎉 {PLANS[sub['plan']]['total_leads']} credits add! "
                               f"Ab {quota_remaining(username)} leads bachi.")
                    st.rerun()
                else:
                    st.warning(f"Status: {stt['status']}. Pehle pay karo, fir dabao.")
            except Exception as e:
                st.error(str(e))
    with st.expander("Mere orders"):
        for s in subscription_history(username):
            st.write(f"#{s['id']} {s['created_at']} {s['plan']} Rs{s['amount_inr']} — {s['status']}")

st.divider()
st.caption("LeadsFind © 2026 • Secure payments • Apni leads, apna business 🚀")
