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
    "icon": {"color": "#b154f9", "font-size": "18px"},
    "nav-link": {"color": "#e1e1e1", "font-size": "15px", "font-weight": "600",
                 "text-align": "left", "margin": "3px 0",
                 "border-radius": "max(.875rem,.9722vw)",
                 "--hover-color": "rgba(177,84,249,.22)"},
    "nav-link-selected": {"background-color": "#b154f9", "color": "#ffffff",
                          "font-weight": "700"},
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
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&display=swap');
:root{
 --kg100:#f1f1f1; --kg300:#b3b3b3; --kg500:#6c6b6b; --kg700:#2e2e2e; --kg900:#171717;
 --kp:#b154f9; --kpd:#8300e9; --krad:max(.875rem,.9722vw);
 --kease:cubic-bezier(.16,1,.3,1);
 --gp:linear-gradient(90deg,#8300e9,#b154f9);
 --gsunset:linear-gradient(90deg,#ff5b79 2%,#bb5ff0 45%,#6988f5 94%);
 --gpeach:linear-gradient(92.37deg,#b78aff 17%,#fe9c72 91%);
 --gmint:linear-gradient(92.37deg,#a8dafa 17%,#99f8cd 91%);
 --gsky:linear-gradient(95.66deg,#77b5ff 18%,#a782ff 89%);
}
html,body,[class*="css"],.stApp,.stApp button,input,textarea,select{
 font-family:'Space Grotesk',sans-serif!important}
.stApp{background:var(--kg100)}
[data-testid="stAppViewContainer"]{background:var(--kg100)}
[data-testid="stHeader"]{background:transparent}
h1,h2,h3,h4{color:var(--kg900)!important;letter-spacing:-.01em!important;line-height:1.2}
.lf-head{background:#fff;color:var(--kg900);padding:20px 24px;border-radius:var(--krad);
 border:1px solid #e1e1e1;margin-bottom:16px;box-shadow:0 1px 2px rgba(0,0,0,.04);
 animation:kFade .7s var(--kease) both}
.lf-head h1{margin:0;font-size:30px;font-weight:700}
.lf-head p{margin:6px 0 0;color:var(--kg500)}
.badge{display:inline-block;padding:3px 14px;border-radius:999px;font-size:13px;
 font-weight:700;background:var(--gp);color:#fff;margin-left:10px;vertical-align:middle}
.plan-card{background:#fff;border:1px solid #e1e1e1;border-radius:var(--krad);
 padding:20px 18px;text-align:center;transition:transform .35s var(--kease),box-shadow .35s var(--kease)}
.plan-card:hover{transform:translateY(-6px);box-shadow:0 18px 40px rgba(131,0,233,.16)}
.plan-card.hot{border-color:var(--kp);box-shadow:0 10px 30px rgba(177,84,249,.22);
 background:linear-gradient(180deg,#fff,#faf5ff)}
.plan-price{font-size:30px;font-weight:700;color:var(--kg900)}
.plan-leads{font-size:15px;color:var(--kpd);font-weight:700}
.small{font-size:12px;color:var(--kg500)}
.quota-bar{font-size:14px;font-weight:700}
.lead-card{background:#fff;border:1px solid #e1e1e1;border-radius:var(--krad);
 padding:14px 16px;margin-bottom:10px;box-shadow:0 1px 2px rgba(0,0,0,.04);
 transition:transform .3s var(--kease),box-shadow .3s var(--kease)}
.lead-card:hover{transform:translateY(-3px);box-shadow:0 14px 30px rgba(0,0,0,.08)}
.lead-card b.nm{font-size:16px;color:var(--kg900);font-weight:700}
.src{font-size:11px;background:#f3e8ff;color:var(--kpd);border-radius:999px;
 padding:2px 10px;font-weight:700}
.btn{display:inline-block;margin:6px 6px 0 0;padding:6px 14px;border-radius:var(--krad);
 font-size:13px;font-weight:700;text-decoration:none;transition:transform .25s var(--kease),
 opacity .25s}
.btn:hover{transform:translateY(-2px);opacity:.92}
.btn-call{background:var(--kp);color:#fff!important}
.btn-wa{background:#25D366;color:#fff!important}
.btn-web{background:var(--kg100);color:var(--kg900)!important;border:1px solid #e1e1e1}
.hero-title{font-size:clamp(36px,6.5vw,64px);font-weight:700;color:#fff;text-align:left;
 margin:0;letter-spacing:-.02em;line-height:1.12;text-shadow:none}
.hero-sub{color:var(--kg300);text-align:left;font-size:clamp(15px,2vw,18px);margin:8px 0 2px}
.feat{display:inline-block;background:rgba(255,255,255,.08);
 border:1px solid rgba(255,255,255,.18);color:#fff;border-radius:999px;
 padding:5px 16px;margin:4px;font-size:13px;font-weight:500;
 transition:background .3s,transform .3s var(--kease)}
.feat:hover{background:rgba(177,84,249,.35);transform:translateY(-2px)}
.lf-head.big{padding:26px 28px}
.lf-head.big h1{font-size:32px}
.stat{background:#fff;border:1px solid #e1e1e1;border-radius:var(--krad);
 padding:16px 8px;text-align:center;box-shadow:0 1px 2px rgba(0,0,0,.04);
 transition:transform .35s var(--kease),box-shadow .35s var(--kease);
 animation:kFade .7s var(--kease) both}
.stat:hover{transform:translateY(-5px);box-shadow:0 16px 34px rgba(0,0,0,.09)}
.sv{display:block;font-size:30px;font-weight:700;color:var(--kg900);line-height:1.15}
.sl{font-size:13px;color:var(--kpd);font-weight:600}
.panel{background:#fff;border:1px solid #e1e1e1;border-radius:var(--krad);
 padding:18px 22px;margin:14px 0;box-shadow:0 1px 2px rgba(0,0,0,.04);
 animation:kFade .7s var(--kease) both}
.panel::before{content:"";display:block;width:34px;height:5px;border-radius:99px;
 background:var(--gp);margin-bottom:10px}
.panel-t{font-size:21px;font-weight:700;color:var(--kg900)}
.panel-s{font-size:14px;color:var(--kg500);margin-top:4px}
.sec-title{text-align:center;color:var(--kg900)!important;font-size:26px;font-weight:700;
 letter-spacing:-.01em;margin:34px 0 16px}
.step{background:#fff;border:1px solid #e1e1e1;border-radius:var(--krad);padding:20px 14px;
 text-align:center;color:var(--kg900);min-height:140px;
 transition:transform .35s var(--kease),box-shadow .35s var(--kease);
 animation:kFade .8s var(--kease) both}
.step:hover{transform:translateY(-6px);box-shadow:0 18px 36px rgba(177,84,249,.16)}
.step-n{width:40px;height:40px;border-radius:50%;background:var(--gp);color:#fff;
 font-weight:700;font-size:19px;display:flex;align-items:center;
 justify-content:center;margin:0 auto 10px;box-shadow:0 6px 16px rgba(131,0,233,.35)}
.step span{font-size:13px;color:var(--kg500)}
.mini-price{background:#fff;border:1px solid #e1e1e1;border-radius:var(--krad);
 padding:16px 8px;text-align:center;color:var(--kg900);font-size:12px;
 transition:transform .35s var(--kease),box-shadow .35s var(--kease);
 animation:kFade .8s var(--kease) both}
.mini-price:hover{transform:translateY(-5px);box-shadow:0 16px 34px rgba(0,0,0,.10)}
.mini-price .mp{font-size:22px;font-weight:700;display:block;margin:4px 0}
.trust{text-align:center;color:var(--kg500);font-size:13px;margin-top:22px}
[data-testid="stSidebar"]{background:var(--kg900)}
[data-testid="stSidebar"] *{color:#e1e1e1}
.profile{text-align:center;padding:18px 10px 14px;
 background:rgba(255,255,255,.06);border:1px solid rgba(255,255,255,.12);
 border-radius:var(--krad);margin-bottom:12px}
.avatar{width:62px;height:62px;border-radius:50%;
 background:var(--gpeach);color:#171717;font-size:28px;
 font-weight:900;display:flex;align-items:center;justify-content:center;margin:0 auto 8px}
.pname{color:#fff;font-weight:700;font-size:17px;word-break:break-all}
.pplan{display:inline-block;background:var(--kp);color:#fff;font-size:12px;
 font-weight:700;border-radius:999px;padding:2px 14px;margin-top:5px}
.qbar{background:rgba(255,255,255,.14);border-radius:99px;height:8px;
 margin:10px 4px 5px;overflow:hidden}
.qfill{background:var(--gp);height:100%;border-radius:99px;
 transition:width .8s var(--kease)}
.pq{color:var(--kg300);font-size:12px;font-weight:600}
.sup{color:var(--kg500);font-size:12px;text-align:center;margin-top:10px}
[data-testid="stButton"] button{border-radius:var(--krad);font-weight:600;
 border:1px solid #d9d9d9;background:#fff;color:var(--kg900);
 transition:all .3s var(--kease)}
[data-testid="stButton"] button:hover{transform:translateY(-2px);
 border-color:var(--kp);color:var(--kpd);box-shadow:0 10px 24px rgba(177,84,249,.18);
 border-color:var(--kp)}
[data-testid="stButton"] button[kind="primary"],
[data-testid="stFormSubmitButton"] button{background:var(--gp);border:none;color:#fff}
[data-testid="stButton"] button[kind="primary"]:hover,
[data-testid="stFormSubmitButton"] button:hover{background:var(--kpd);color:#fff;
 box-shadow:0 12px 28px rgba(131,0,233,.35);border-color:transparent}
[data-testid="stTextInput"] input,[data-testid="stNumberInput"] input,
[data-testid="stSelectbox"] [data-baseweb="select"]>div{
 border-radius:var(--krad)!important;border:1px solid #d9d9d9;background:#fff}
[data-testid="stTextInput"] input:focus,[data-testid="stNumberInput"] input:focus{
 border-color:var(--kp);box-shadow:0 0 0 3px rgba(177,84,249,.18)}
[data-testid="stProgress"]>div>div>div>div{background:var(--gp)}
[data-testid="stExpander"] details{border-radius:var(--krad);border:1px solid #e1e1e1}
[data-baseweb="tab"]{border-radius:var(--krad)!important;font-weight:600}
[data-baseweb="tab"][aria-selected="true"]{background:var(--kg900);color:#fff!important}
@keyframes kFade{from{opacity:0;transform:translateY(22px)}to{opacity:1;transform:none}}
@keyframes kReveal{from{opacity:0;transform:skewY(-4deg) translate3d(0,100%,0) rotateX(-45deg)}
 to{opacity:1;transform:none}}
@keyframes kMarquee{from{transform:translateX(0)}to{transform:translateX(-50%)}}
@keyframes kBlob{0%,100%{transform:translate(0,0) scale(1)}
 50%{transform:translate(5vw,-4vw) scale(1.18)}}
@keyframes kGrad{0%,100%{background-position:0% 50%}50%{background-position:100% 50%}}
.k-grad{background:var(--gsunset);background-size:220% 220%;
 -webkit-background-clip:text;background-clip:text;color:transparent;
 animation:kGrad 7s ease infinite}
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
 [data-testid="stAppViewContainer"]{background:var(--kg100)}
 [data-testid="stSidebar"]{display:none}
 [data-testid="block-container"]{padding-top:1rem!important;max-width:1120px}
 div[data-testid="stVerticalBlockBorderWrapper"]{background:#fff;
  border:1px solid #e1e1e1;border-radius:var(--krad);
  box-shadow:0 1px 2px rgba(0,0,0,.05)}
 @media (max-width:640px){
  .lf-head.big{padding:18px}
  .lf-head.big h1{font-size:24px}
  .sv{font-size:26px}
  .step{min-height:0;margin-bottom:8px}
  .mini-price{margin-bottom:8px}
 }
 /* ---- Krepling hero ---- */
 .k-hero{position:relative;overflow:hidden;background:var(--kg900);
  border-radius:var(--krad);padding:clamp(34px,5vw,64px) clamp(22px,4vw,48px);
  margin-bottom:14px;color:#fff}
 .k-hero .blob{position:absolute;border-radius:50%;filter:blur(70px);opacity:.55;
  pointer-events:none;animation:kBlob 14s ease-in-out infinite}
 .k-b1{width:340px;height:340px;background:#8300e9;top:-90px;right:-60px}
 .k-b2{width:280px;height:280px;background:#ff5b79;bottom:-100px;left:-70px;
  animation-delay:-5s!important}
 .k-b3{width:220px;height:220px;background:#6988f5;top:40%;left:38%;
  animation-delay:-9s!important;opacity:.35}
 .k-eyebrow{font-size:clamp(15px,2vw,19px);font-weight:500;color:#f1f1f1;
  max-width:520px;margin-left:auto;transform-origin:0 0;
  animation:kReveal 1.1s var(--kease) .05s both;position:relative}
 .k-eyebrow i,.k-gh{font-style:italic;background:var(--gpeach);
  -webkit-background-clip:text;background-clip:text;color:transparent}
 @media (max-width:760px){.k-hide-sm{text-align:left!important}}
 .k-hero-grid{display:grid;grid-template-columns:1.35fr 1fr;gap:26px;
  align-items:end;margin-top:clamp(40px,7vw,90px);position:relative}
 @media (max-width:760px){.k-hero-grid{grid-template-columns:1fr}}
 .k-h1{font-size:clamp(34px,5.4vw,58px);font-weight:700;line-height:1.12;
  letter-spacing:-.02em;margin:0;transform-origin:0 0;
  animation:kReveal 1.2s var(--kease) .15s both}
 .k-desc{color:var(--kg300);font-size:clamp(15px,1.6vw,17px);margin:0 0 16px;
  animation:kFade .9s var(--kease) .4s both}
 .k-cta{animation:kFade .9s var(--kease) .55s both;text-align:right}
 @media (max-width:760px){.k-cta{text-align:left}}
 /* ---- marquee ---- */
 .k-marquee{overflow:hidden;background:#fff;border:1px solid #e1e1e1;
  border-radius:var(--krad);padding:14px 0;margin-bottom:14px}
 .k-track{display:flex;gap:42px;width:max-content;
  animation:kMarquee 26s linear infinite;align-items:center}
 .k-track span{font-weight:600;color:var(--kg500);font-size:14px;white-space:nowrap}
 /* ---- showcase section ---- */
 .k-sec{background:#fff;border:1px solid #e1e1e1;border-radius:var(--krad);
  padding:clamp(24px,3.5vw,44px);margin-bottom:14px;animation:kFade .8s var(--kease) both}
 .k-sec.dark{background:var(--kg900);border-color:var(--kg900);color:#fff}
 .k-sec.dark h2,.k-sec.dark h3{color:#fff!important}
 .k-sec.dark .k-sub{color:var(--kg300)}
 .k-icon{width:52px;height:52px;border-radius:14px;background:var(--gp);
  display:flex;align-items:center;justify-content:center;font-size:24px;
  margin-bottom:14px;box-shadow:0 8px 22px rgba(131,0,233,.35)}
 .k-sec h2{font-size:clamp(26px,3.6vw,40px);font-weight:700;letter-spacing:-.01em;
  margin:0 0 8px;line-height:1.2}
 .k-sec h2 em{background:var(--gpeach);-webkit-background-clip:text;
  background-clip:text;color:transparent;font-style:italic}
 .k-sec.dark h2 em{background:var(--gmint);-webkit-background-clip:text;
  background-clip:text;color:transparent}
 .k-sub{color:var(--kg500);font-size:15px;margin:0 0 22px;max-width:640px}
 .k-3{display:grid;grid-template-columns:repeat(3,1fr);gap:14px}
 @media (max-width:760px){.k-3{grid-template-columns:1fr}}
 .k-card{background:var(--kg100);border:1px solid #e1e1e1;border-radius:var(--krad);
  padding:18px;transition:transform .35s var(--kease),box-shadow .35s var(--kease);
  animation:kFade .8s var(--kease) both}
 .k-sec.dark .k-card{background:rgba(255,255,255,.06);border-color:rgba(255,255,255,.12)}
 .k-card:hover{transform:translateY(-6px);box-shadow:0 18px 36px rgba(0,0,0,.12)}
 .k-card h4{margin:0 0 6px;font-size:16px;font-weight:700;color:var(--kg900)}
 .k-sec.dark .k-card h4{color:#fff}
 .k-card p{margin:0;font-size:13.5px;color:var(--kg500);line-height:1.55}
 .k-sec.dark .k-card p{color:var(--kg300)}
 /* ---- benefits ---- */
 .k-ben{display:flex;align-items:baseline;gap:12px;padding:12px 0;
  border-bottom:1px solid #e1e1e1;transform-origin:0 0;
  animation:kReveal .9s var(--kease) both}
 .k-sec.dark .k-ben{border-color:rgba(255,255,255,.12)}
 .k-ben:last-child{border-bottom:none}
 .k-ben .bi{font-size:18px}
 .k-ben b{font-size:15px;color:var(--kg900);min-width:200px}
 .k-sec.dark .k-ben b{color:#fff}
 .k-ben span{font-size:13.5px;color:var(--kg500)}
 .k-sec.dark .k-ben span{color:var(--kg300)}
 /* ---- FAQ ---- */
 .k-faq{background:#fff;border:1px solid #e1e1e1;border-radius:var(--krad);
  overflow:hidden;margin-bottom:14px}
 .k-faq details{border-bottom:1px solid #e1e1e1}
 .k-faq details:last-child{border-bottom:none}
 .k-faq summary{cursor:pointer;list-style:none;padding:20px 24px;font-weight:700;
  font-size:15.5px;color:var(--kg900);display:flex;justify-content:space-between;
  align-items:center;transition:background .25s;gap:12px}
 .k-faq summary:hover{background:var(--kg100)}
 .k-faq summary::-webkit-details-marker{display:none}
 .k-faq summary::after{content:"+";font-size:22px;color:var(--kp);
  transition:transform .3s var(--kease);flex-shrink:0}
 .k-faq details[open] summary::after{transform:rotate(45deg)}
 .k-faq details[open] summary{color:var(--kpd)}
 .k-faq .fa{padding:0 24px 20px;color:var(--kg500);font-size:14px;line-height:1.65;
  animation:kFade .4s var(--kease) both}
 /* ---- CTA band ---- */
 .k-cta-band{background:var(--kg900);border-radius:var(--krad);
  padding:clamp(30px,4vw,52px);text-align:center;margin-bottom:14px;
  position:relative;overflow:hidden;animation:kFade .8s var(--kease) both}
 .k-cta-band .blob{position:absolute;border-radius:50%;filter:blur(64px);opacity:.5;
  width:300px;height:300px;background:#8300e9;top:-120px;left:20%;
  animation:kBlob 12s ease-in-out infinite}
 .k-cta-band h2{color:#fff!important;font-size:clamp(24px,3.4vw,36px);margin:0 0 18px;
  position:relative;letter-spacing:-.01em}
 /* ---- footer ---- */
 .k-footer{background:#fff;border:1px solid #e1e1e1;border-radius:var(--krad);
  padding:clamp(24px,3vw,40px);animation:kFade .8s var(--kease) both}
 .k-fcols{display:grid;grid-template-columns:1.4fr 1fr 1fr 1fr;gap:22px;margin-bottom:22px}
 @media (max-width:760px){.k-fcols{grid-template-columns:1fr 1fr}}
 .k-fcols h5{margin:0 0 10px;font-size:13px;font-weight:700;color:var(--kg900);
  text-transform:uppercase;letter-spacing:.06em}
 .k-fcols a,.k-fcols p{display:block;color:var(--kg500);font-size:14px;
  margin:0 0 8px;text-decoration:none;transition:color .25s}
 .k-fcols a:hover{color:var(--kp)}
 .k-fbot{border-top:1px solid #e1e1e1;padding-top:16px;display:flex;
  justify-content:space-between;flex-wrap:wrap;gap:8px;
  color:var(--kg500);font-size:13px}
 </style>
 <div class="k-hero">
  <div class="blob k-b1"></div><div class="blob k-b2"></div><div class="blob k-b3"></div>
  <div class="k-eyebrow">Dhundhne ke liye clicks, <i class="k-gh">ghanton ki
   manual search nahi.</i></div>
  <div class="k-hero-grid">
   <h1 class="k-h1">Shetron ke liye <span class="k-grad">asli business
    leads</span> ka platform.</h1>
   <div>
    <p class="k-desc">Har business ko ek aisa sales channel chahiye jo
     engineering challenge na ho — city + business dalo, leads turant pao.</p>
    <div style="text-align:right" class="k-hide-sm">
     <span class="feat">🎁 5 FREE</span>
     <span class="feat">📞 Phone filters</span>
     <span class="feat">💳 Rs49 se</span>
    </div>
   </div>
  </div>
 </div>
 <div class="k-marquee"><div class="k-track">
  <span>Google Maps</span><span>SerpAPI</span><span>JustDial</span>
  <span>OpenStreetMap</span><span>Web Search</span><span>📞 Call</span>
  <span>💬 WhatsApp</span><span>⬇ CSV export</span><span>⭐ Ratings</span>
  <span>Google Maps</span><span>SerpAPI</span><span>JustDial</span>
  <span>OpenStreetMap</span><span>Web Search</span><span>📞 Call</span>
  <span>💬 WhatsApp</span><span>⬇ CSV export</span><span>⭐ Ratings</span>
 </div></div>""", unsafe_allow_html=True)
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
    # ---- Krepling-style: product showcase (light section) ----
    st.markdown("""<div class="k-sec">
     <div class="k-icon">⚡</div>
     <h2>3 step me leads — <em>bina jhanjhat.</em></h2>
     <p class="k-sub">Signup se lekar call tak — poora journey sirf click karke.</p>
     <div class="k-3">
      <div class="k-card" style="animation-delay:.05s"><h4>1 · Account banao</h4>
       <p>2 minute me signup — pehli <b>5 leads bilkul FREE</b> 🎁.</p></div>
      <div class="k-card" style="animation-delay:.15s"><h4>2 · City + Business dalo</h4>
       <p>Jaise <b>Delhi + dentist</b> — phone/website ke ticks apni marzi se ✅.</p></div>
      <div class="k-card" style="animation-delay:.25s"><h4>3 · Leads pao</h4>
       <p>Call / WhatsApp ek click se 💬, ya poora CSV download ⬇️.</p></div>
     </div></div>""", unsafe_allow_html=True)
    # ---- dark showcase: sources ----
    st.markdown("""<div class="k-sec dark">
     <div class="k-icon">🔍</div>
     <h2>Leads kahan se aati hain — <em>chaar sources.</em></h2>
     <p class="k-sub">Ek fail hua toh agla source apne aap — results kabhi khaali nahi.</p>
     <div class="k-3">
      <div class="k-card" style="animation-delay:.05s"><h4>⭐ Google Maps</h4>
       <p>Official SerpAPI — phone, rating, reviews pakka.</p></div>
      <div class="k-card" style="animation-delay:.15s"><h4>📇 JustDial + OSM</h4>
       <p>Bina-website business dhoondne ke best.</p></div>
      <div class="k-card" style="animation-delay:.25s"><h4>🌐 Web Search</h4>
       <p>Fresh websites wali leads — automatic fallback.</p></div>
     </div></div>""", unsafe_allow_html=True)
    st.markdown('<div class="sec-title">💎 Packs — sirf Rs49 se shuru</div>',
                unsafe_allow_html=True)
    pc = st.columns(len(PLANS))
    for i, (k, p) in enumerate(PLANS.items()):
        with pc[i]:
            tag = "🔥 " if k == "OFFER" else ""
            price = "FREE" if p["price_inr"] == 0 else f"Rs{p['price_inr']}"
            st.markdown(f'<div class="mini-price" style="animation-delay:{i*0.08:.2f}s">'
                        f'{tag}<b>{k}</b><br>'
                        f'<span class="mp">{price}</span><br>'
                        f'<span>{p["total_leads"]} leads</span></div>',
                        unsafe_allow_html=True)
    # ---- FAQ (Krepling ListAccordion) ----
    st.markdown('<div class="sec-title">Frequently Asked Questions</div>',
                unsafe_allow_html=True)
    st.markdown("""<div class="k-faq">
     <details><summary>Kya sach me 5 leads free milte hain?</summary>
      <div class="fa">Haan — account banate hi 5 credits milte hain, bina
      kisi card ke. Uske baad Rs49 wala pack le sakte ho.</div></details>
     <details><summary>Leads me kya-kya aata hai?</summary>
      <div class="fa">Business ka naam, phone number, address, rating/reviews
      aur website (ya "NO WEBSITE" — jo sabse badi opportunity hai).</div></details>
     <details><summary>Bina website wale clients kaise milega?</summary>
      <div class="fa">Source me <b>Google Maps</b> ya <b>OpenStreetMap</b> chuno
      aur <b>🚫 Bina website wale</b> tick lagao — bechne ke best clients wahi hain.</div></details>
     <details><summary>Payment safe hai?</summary>
      <div class="fa">Razorpay se — India ka sabse trusted gateway. Payment ke
      <b>turant</b> credits balance me add ho jaate hain.</div></details>
    </div>""", unsafe_allow_html=True)
    # ---- CTA band ----
    st.markdown("""<div class="k-cta-band"><div class="blob"></div>
     <h2>Aaj hi apne business ke liye leads nikalo</h2>
     <div style="display:flex;gap:12px;justify-content:center;flex-wrap:wrap;position:relative">
      <span class="feat" style="background:#b154f9;border-color:#b154f9;font-weight:700">
       🎁 5 leads FREE shuru karo</span>
      <span class="feat">💳 Rs49 se upgrade</span>
     </div></div>""", unsafe_allow_html=True)
    # ---- footer ----
    st.markdown("""<div class="k-footer">
     <div class="k-fcols">
      <div><h5>LeadsFind</h5><p>Local business leads — city + business dalo,
       leads turant pao. 🇮🇳 Made in India.</p></div>
      <div><h5>Product</h5><a href="#">Dashboard</a><a href="#">Lead sources</a>
       <a href="#">CSV export</a></div>
      <div><h5>Resources</h5><a href="#">Pricing</a><a href="#">FAQ</a>
       <a href="#">Support</a></div>
      <div><h5>Contact</h5><p>care@leadsfind.in</p><p>Secure Razorpay payments</p></div>
     </div>
     <div class="k-fbot"><span>© 2026 LeadsFind. All rights reserved.</span>
      <span>Privacy · Terms · Legal</span></div></div>""", unsafe_allow_html=True)
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
        location = st.text_input("City *", value="",
                                 placeholder="Jaise: Delhi, Lucknow...")
        place_name = st.text_input("Area (optional)", value="",
                                   help="Jaise: Karol Bagh, Laxmi Nagar")
    with c2:
        business = st.text_input("Business *", value="",
                                 placeholder="dentist, gym, salon, restaurant...",
                                 help="dentist, gym, salon, astrologer, restaurant...")
        # Key hai toh sabse reliable source (Google Maps via SerpAPI) pehle
        if SERPAPI_KEY.strip():
            _srcs = ["serpapi", "justdial", "gmaps_free", "overpass", "web"]
        else:
            _srcs = ["gmaps_free", "overpass", "web"]
        platform = st.selectbox("Source (kahan se nikale?)", _srcs,
                                format_func=lambda p: SOURCES[p],
                                index=0,
                                help="Google Maps (SerpAPI) = best quality (official API). "
                                     "Bina-website client chahiye toh tick dekho — "
                                     "Web Search me almost har lead website rakhti hai.")
    hints = {
        "serpapi": "⭐ BEST — asli Google Maps official API: phone 100%, rating+reviews. Free 100 searches/mahina.",
        "justdial": "📞 JustDial listings (SerpAPI key se).",
        "gmaps_free": "🆓 Bina key ke Google Maps — kabhi-throttle, tab fallback.",
        "overpass": "🗺️ OpenStreetMap — free; bina-website business milne ke best.",
        "web": "🌐 Websites wali leads — 'Bina website wale' tick ke saath 0 dega.",
    }
    st.caption(hints.get(platform, ""))

    st.write("**✅ Apni marzi ke ticks lagao (koi tick nahi = sab leads):**")
    t1, t2, t3 = st.columns(3)
    with t1:
        need_phone = st.checkbox("📞 Number wale hi", value=False,
                                 help="Sirf phone-number wali leads")
    with t2:
        want_with = st.checkbox("🌐 Website wale", value=False,
                                help="Jinki website bani hai")
    with t3:
        want_without = st.checkbox("🚫 Bina website wale", value=False,
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
