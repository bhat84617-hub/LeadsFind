"""Self keep-alive: Render free instance 15 min idle pe so jata hai.

Ye thread har 5 min app ke PUBLIC URL ko hit karta hai — Render ko
inbound request milta rehta hai, isliye instance kabhi sleep nahi hota.
Eksik: thread tab tak start nahi hota jab tak koi bahar se ek baar app na
khole (deploy ke baad pehli visit = loop shuru).
"""
import os
import threading
import time

import requests

THREAD_NAME = "lf-keepalive"
PING_EVERY = 300  # 5 min (Render sleep threshold 15 min hai)


def _loop():
    base = os.environ.get("RENDER_EXTERNAL_URL", "").rstrip("/")
    if not base:
        return  # local dev — Render pe RENDER_EXTERNAL_URL auto-set hota hai
    health = base + "/_stcore/health"
    time.sleep(30)  # boot settle
    while True:
        try:
            requests.get(health, timeout=45)
        except Exception:
            pass
        time.sleep(PING_EVERY)


def start_keepalive():
    if any(t.name == THREAD_NAME for t in threading.enumerate()):
        return  # already running (process-level guard, module reload pe bhi safe)
    threading.Thread(target=_loop, daemon=True, name=THREAD_NAME).start()
