#!/usr/bin/env python3
"""
auto_restart.py

Ei script ta tomar VPS panel (127.0.0.1:5000) er nijer start/stop
API/route ke use kore, protha e login kore, tarpor proti ghonta
(default) por por - jei bot gula ei muhurte "RUNNING" ache, sudhu
segulake dhore stop + start (restart) kore dey.

Notun bot start dile / kono bot stop kore rakhle, poroborti cycle e
script nijei abar current running list detect kore nibe - fixed
list likhe rakhte hobe na.

REQUIREMENTS:
    pip install requests

USAGE:
    1. Niche CONFIG section e PASSWORD ta bosao (tomar panel login password)
    2. python auto_restart.py
    3. Background e chalate chaile: nohup python auto_restart.py &
       (ba tmux/screen use koro Termux e)
"""

import re
import time
import requests

# ================= CONFIG =================
BASE_URL = "http://127.0.0.1:5000"
PASSWORD = "TOMAR_PANEL_PASSWORD_EKHANE_DIO"
RESTART_INTERVAL_SECONDS = 60 * 60   # 1 hour
CHECK_ONLY_LOG = True                # True hole prottek cycle e ki korlo seta print korbe
# ============================================

session = requests.Session()


def login() -> bool:
    try:
        r = session.post(BASE_URL + "/", data={"password": PASSWORD}, timeout=15)
        # login successful hole shadharonoto /dashboard e redirect hoy
        return "/dashboard" in r.url or r.status_code == 200
    except Exception as e:
        print(f"[login error] {e}")
        return False


def get_running_bots() -> list[str]:
    """
    Dashboard page fetch kore, jei bot gular 'stop' form ache
    (mane bot ta RUNNING) segular naam ber kore ane.
    """
    try:
        r = session.get(BASE_URL + "/dashboard", timeout=15)
        if r.status_code != 200:
            print(f"[warn] dashboard fetch status: {r.status_code}")
            return []
        names = re.findall(r'action="/server/([^/"]+)/stop"', r.text)
        return list(dict.fromkeys(names))  # duplicate remove, order rakhe
    except Exception as e:
        print(f"[get_running_bots error] {e}")
        return []


def restart_bot(name: str) -> bool:
    try:
        r1 = session.post(f"{BASE_URL}/server/{name}/stop", timeout=15)
        time.sleep(2)  # process ke properly bondho hote time dicchi
        r2 = session.post(f"{BASE_URL}/server/{name}/start", timeout=15)
        ok = r1.status_code == 200 and r2.status_code == 200
        return ok
    except Exception as e:
        print(f"[restart error] {name}: {e}")
        return False


def cycle():
    running = get_running_bots()
    if not running:
        print("[i] Ekhon kono bot RUNNING obostay nei, restart korar kichu nei.")
        return

    print(f"[i] RUNNING bot paoa gelo: {running}")
    for name in running:
        ok = restart_bot(name)
        status = "✓ restarted" if ok else "✗ restart failed"
        print(f"    - {name}: {status}")


def main():
    print(f"Auto-restart watcher shuru holo. Interval: {RESTART_INTERVAL_SECONDS}s")

    if PASSWORD == "TOMAR_PANEL_PASSWORD_EKHANE_DIO":
        print("[!] Age CONFIG section e tomar actual panel password bosao, tarpor abar run koro.")
        return

    if not login():
        print("[!] Login fail holo. Password thik ache kina check koro.")
        return
    print("[✓] Login successful.")

    try:
        while True:
            cycle()
            print(f"--- ({RESTART_INTERVAL_SECONDS}s ghum, porer cycle e abar check hobe) ---\n")
            time.sleep(RESTART_INTERVAL_SECONDS)
    except KeyboardInterrupt:
        print("\nStopped.")


if __name__ == "__main__":
    main()
