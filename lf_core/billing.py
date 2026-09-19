"""LeadsFind (LF) - Razorpay billing via Payment Links API.
Flow (Streamlit-friendly, bina webhook ke):
  1. Customer plan chune -> create_payment_link() -> short_url milega
  2. Customer naye tab me pay kare (UPI/card/netbanking)
  3. "Payment Verify Karo" dabaye -> fetch_link_status() == paid
     -> turant plan upgrade (mark_paid + set_plan)
Razorpay docs: POST/GET https://api.razorpay.com/v1/payment_links (Basic Auth key:secret)
"""
import os
import requests
from requests.auth import HTTPBasicAuth

API_BASE = "https://api.razorpay.com/v1"


def rz_keys():
    return (os.getenv("RAZORPAY_KEY_ID", "").strip(),
            os.getenv("RAZORPAY_KEY_SECRET", "").strip())


def is_configured() -> bool:
    k, s = rz_keys()
    return bool(k and s)


def create_payment_link(username: str, plan: str, amount_inr: int,
                        email: str = "", phone: str = "") -> dict:
    """Razorpay payment link banao. Return: {link_id, link_url, status}."""
    key_id, key_secret = rz_keys()
    if not key_id or not key_secret:
        raise RuntimeError("Razorpay keys nahi hain. .env me RAZORPAY_KEY_ID/SECRET dalo.")
    if amount_inr <= 0:
        raise ValueError("FREE plan ke liye payment nahi chahiye.")
    payload = {
        "amount": int(amount_inr * 100),  # paise
        "currency": "INR",
        "description": f"LeadsFind {plan} - {username}",
        "reference_id": f"LF-{username}-{plan}",
        "reminder_enable": True,
        "callback_url": os.getenv("LF_CALLBACK_URL", "http://localhost:8501"),
        "callback_method": "get",
    }
    customer = {"name": username}
    if email:
        customer["email"] = email
    if phone:
        customer["contact"] = phone
    if len(customer) > 1:
        payload["customer"] = customer
        payload["notify"] = {"sms": bool(phone), "email": bool(email)}
    r = requests.post(f"{API_BASE}/payment_links", json=payload,
                      auth=HTTPBasicAuth(key_id, key_secret), timeout=30)
    if r.status_code not in (200, 201):
        raise RuntimeError(f"Razorpay link fail ({r.status_code}): {r.text[:300]}")
    j = r.json()
    return {"link_id": j.get("id"), "link_url": j.get("short_url"),
            "status": j.get("status", "created")}


def fetch_link_status(link_id: str) -> dict:
    """Link ka live status lao. paid/created/cancelled + amount_paid."""
    key_id, key_secret = rz_keys()
    r = requests.get(f"{API_BASE}/payment_links/{link_id}",
                     auth=HTTPBasicAuth(key_id, key_secret), timeout=30)
    if r.status_code != 200:
        raise RuntimeError(f"Status check fail ({r.status_code}): {r.text[:300]}")
    j = r.json()
    return {"status": j.get("status"), "amount_paid": j.get("amount_paid", 0),
            "payments": j.get("payments", []), "raw": j}
