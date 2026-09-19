"""LeadsFind (LF) - SQLite: users(auth+quota) + searches + leads + subscriptions.
Quota system: har lead = 1 credit. Search pe `got` credits kat te hain.
"""
import sqlite3
import json
import os
import hashlib
from datetime import datetime

from .plans import get_plan

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "leadsfind.db")


def _conn():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    c = sqlite3.connect(DB_PATH)
    c.row_factory = sqlite3.Row
    return c


def hash_pw(pw: str) -> str:
    return hashlib.sha256(("LF$" + pw).encode()).hexdigest()


def init_db():
    c = _conn()
    c.execute("""CREATE TABLE IF NOT EXISTS users(
        username TEXT PRIMARY KEY,
        plan TEXT DEFAULT 'FREE',
        created_at TEXT
    )""")
    for col in ["password_hash TEXT DEFAULT ''", "email TEXT DEFAULT ''",
                "phone TEXT DEFAULT ''",
                "leads_quota INTEGER DEFAULT 0",
                "leads_used INTEGER DEFAULT 0"]:
        try:
            c.execute(f"ALTER TABLE users ADD COLUMN {col}")
        except Exception:
            pass
    c.execute("""CREATE TABLE IF NOT EXISTS searches(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        location TEXT,
        place_name TEXT,
        business TEXT,
        platform TEXT,
        asked INTEGER,
        got INTEGER,
        created_at TEXT
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS leads(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        search_id INTEGER,
        username TEXT,
        business_name TEXT,
        phone TEXT,
        address TEXT,
        rating TEXT,
        reviews TEXT,
        hours TEXT,
        website TEXT,
        extra TEXT,
        FOREIGN KEY(search_id) REFERENCES searches(id)
    )""")
    c.execute("""CREATE TABLE IF NOT EXISTS subscriptions(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        plan TEXT,
        amount_inr INTEGER,
        link_id TEXT,
        link_url TEXT,
        status TEXT DEFAULT 'created',
        created_at TEXT,
        paid_at TEXT
    )""")
    c.commit()
    c.close()


# ---------------- auth ----------------
def register_user(username: str, password: str, email: str = "", phone: str = ""):
    username = username.strip().lower()
    if not username or not password or len(password) < 4:
        raise ValueError("Username + min 4-char password chahiye.")
    c = _conn()
    if c.execute("SELECT 1 FROM users WHERE username=?", (username,)).fetchone():
        c.close()
        raise ValueError("Ye username already hai. Login karo.")
    free_n = get_plan("FREE")["total_leads"]
    c.execute(
        "INSERT INTO users(username, plan, created_at, password_hash, email, phone,"
        " leads_quota, leads_used) VALUES(?,?,?,?,?,?,?,0)",
        (username, "FREE", datetime.now().isoformat(timespec="seconds"),
         hash_pw(password), email, phone, free_n))
    c.commit()
    c.close()
    return username


def login_user(username: str, password: str):
    username = username.strip().lower()
    c = _conn()
    row = c.execute("SELECT * FROM users WHERE username=?", (username,)).fetchone()
    c.close()
    if row is None:
        raise ValueError("User nahi mila. Pehle Register karo.")
    d = dict(row)
    if not d.get("password_hash"):
        set_password(username, password)
        return get_user(username)
    if d["password_hash"] != hash_pw(password):
        raise ValueError("Galat password.")
    return d


def set_password(username: str, password: str):
    c = _conn()
    c.execute("UPDATE users SET password_hash=? WHERE username=?",
              (hash_pw(password), username))
    c.commit()
    c.close()


def get_user(username: str):
    c = _conn()
    row = c.execute("SELECT * FROM users WHERE username=?",
                    (username.strip().lower(),)).fetchone()
    c.close()
    if not row:
        return None
    d = dict(row)
    # quota hamesha plan ke hisab se (unlimited-era migration wapas)
    q_plan = get_plan(d.get("plan", "FREE"))["total_leads"]
    if not d.get("leads_quota") or (d.get("leads_quota") or 0) >= 99999999:
        set_quota(d["username"], q_plan)
        d["leads_quota"] = q_plan
    d["leads_used"] = d.get("leads_used") or 0
    return d


def get_or_create_user(username: str, plan: str = "FREE"):
    u = get_user(username)
    if u:
        return u
    register_user(username, "temp1234")
    return get_user(username)


# ---------------- quota ----------------
def quota_remaining(username: str) -> int:
    u = get_user(username)
    return max(0, (u.get("leads_quota") or 0) - (u.get("leads_used") or 0))


def set_quota(username: str, quota: int):
    c = _conn()
    c.execute("UPDATE users SET leads_quota=? WHERE username=?", (quota, username))
    c.commit()
    c.close()


def add_quota(username: str, extra: int):
    """Payment pe quota badhao + plan set karo (credits add hote hain, reset nahi)."""
    c = _conn()
    c.execute("UPDATE users SET leads_quota=COALESCE(leads_quota,0)+? WHERE username=?",
              (extra, username))
    c.commit()
    c.close()


def set_plan(username: str, plan: str):
    c = _conn()
    c.execute("UPDATE users SET plan=? WHERE username=?", (plan, username))
    c.commit()
    c.close()


def consume_leads(username: str, n: int):
    c = _conn()
    c.execute("UPDATE users SET leads_used=COALESCE(leads_used,0)+? WHERE username=?",
              (n, username))
    c.commit()
    c.close()


# ---------------- searches / leads ----------------
def save_search(username, location, place_name, business, platform, asked, lead_dicts):
    c = _conn()
    cur = c.execute(
        "INSERT INTO searches(username,location,place_name,business,platform,asked,got,created_at)"
        " VALUES(?,?,?,?,?,?,?,?)",
        (username, location, place_name, business, platform, asked, len(lead_dicts),
         datetime.now().isoformat(timespec="seconds")))
    sid = cur.lastrowid
    for L in lead_dicts:
        c.execute(
            "INSERT INTO leads(search_id,username,business_name,phone,address,rating,reviews,hours,website,extra)"
            " VALUES(?,?,?,?,?,?,?,?,?,?)",
            (sid, username, L.get("business_name", ""), L.get("phone", ""),
             L.get("address", ""), str(L.get("rating", "")), str(L.get("reviews", "")),
             L.get("hours", ""), L.get("website", ""),
             json.dumps(L, ensure_ascii=False)[:2000]))
    c.execute("UPDATE users SET leads_used=COALESCE(leads_used,0)+? WHERE username=?",
              (len(lead_dicts), username))
    c.commit()
    c.close()
    return sid


def user_stats(username: str) -> dict:
    c = _conn()
    searches = c.execute(
        "SELECT COUNT(*) n, COALESCE(SUM(got),0) g FROM searches WHERE username=?",
        (username,)).fetchone()
    leads = c.execute(
        "SELECT COUNT(*) n FROM leads WHERE username=?", (username,)).fetchone()
    with_phone = c.execute(
        "SELECT COUNT(*) n FROM leads WHERE username=? AND phone<>''",
        (username,)).fetchone()
    no_site = c.execute(
        "SELECT COUNT(*) n FROM leads WHERE username=? AND website='NO WEBSITE'",
        (username,)).fetchone()
    c.close()
    u = get_user(username) or {}
    return {"searches": searches["n"], "leads_got": searches["g"],
            "leads": leads["n"], "with_phone": with_phone["n"],
            "no_website": no_site["n"],
            "quota": u.get("leads_quota", 0), "used": u.get("leads_used", 0),
            "remaining": max(0, (u.get("leads_quota") or 0) - (u.get("leads_used") or 0))}


def get_history(username: str, limit: int = 50):
    c = _conn()
    rows = c.execute(
        "SELECT * FROM searches WHERE username=? ORDER BY id DESC LIMIT ?",
        (username, limit)).fetchall()
    c.close()
    return [dict(r) for r in rows]


def get_leads_of_search(search_id: int):
    c = _conn()
    rows = c.execute("SELECT * FROM leads WHERE search_id=?", (search_id,)).fetchall()
    c.close()
    return [dict(r) for r in rows]


def get_all_leads(username: str, limit: int = 5000):
    c = _conn()
    rows = c.execute(
        "SELECT * FROM leads WHERE username=? ORDER BY id DESC LIMIT ?",
        (username, limit)).fetchall()
    c.close()
    return [dict(r) for r in rows]


# ---------------- admin helpers ----------------
def all_users():
    c = _conn()
    rows = c.execute("SELECT * FROM users ORDER BY created_at DESC").fetchall()
    c.close()
    return [dict(r) for r in rows]


def total_revenue() -> int:
    c = _conn()
    row = c.execute(
        "SELECT COALESCE(SUM(amount_inr),0) s FROM subscriptions WHERE status='paid'"
    ).fetchone()
    c.close()
    return row["s"]


def all_subscriptions(limit: int = 100):
    c = _conn()
    rows = c.execute(
        "SELECT * FROM subscriptions ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
    c.close()
    return [dict(r) for r in rows]


# ---------------- subscriptions ----------------
def create_subscription(username, plan, amount_inr, link_id, link_url):
    c = _conn()
    cur = c.execute(
        "INSERT INTO subscriptions(username,plan,amount_inr,link_id,link_url,status,created_at)"
        " VALUES(?,?,?,?,?,?,?)",
        (username, plan, amount_inr, link_id, link_url, "created",
         datetime.now().isoformat(timespec="seconds")))
    sid = cur.lastrowid
    c.commit()
    c.close()
    return sid


def mark_paid(link_id: str, plan: str, username: str):
    """Payment milte hi: subscription paid + credits add + plan upgrade."""
    c = _conn()
    c.execute("UPDATE subscriptions SET status='paid', paid_at=? WHERE link_id=?",
              (datetime.now().isoformat(timespec="seconds"), link_id))
    c.commit()
    c.close()
    add_quota(username, get_plan(plan)["total_leads"])
    set_plan(username, plan)


def latest_subscription(username: str):
    c = _conn()
    row = c.execute(
        "SELECT * FROM subscriptions WHERE username=? ORDER BY id DESC LIMIT 1",
        (username,)).fetchone()
    c.close()
    return dict(row) if row else None


def subscription_history(username: str, limit: int = 20):
    c = _conn()
    rows = c.execute(
        "SELECT * FROM subscriptions WHERE username=? ORDER BY id DESC LIMIT ?",
        (username, limit)).fetchall()
    c.close()
    return [dict(r) for r in rows]
