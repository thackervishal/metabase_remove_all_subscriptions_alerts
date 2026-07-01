#!/usr/bin/env python3
"""Removes all dashboard subscriptions and alerts from a Metabase instance."""
import json
import sys

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

BASE_URL = "https://your-metabase-instance.example.com"
USERNAME = "your-admin-email@example.com"
PASSWORD = "your-admin-password"

SESSION = requests.Session()
_retry_adapter = HTTPAdapter(max_retries=Retry(
    total=3, connect=3, read=3, backoff_factor=0.3,
    allowed_methods=frozenset(["GET", "PUT", "POST"]),
))
SESSION.mount("http://", _retry_adapter)
SESSION.mount("https://", _retry_adapter)


def authenticate():
    resp = SESSION.post(f"{BASE_URL}/api/session", json={"username": USERNAME, "password": PASSWORD})
    session_id = resp.json().get("id") if resp.ok else None
    if not session_id:
        sys.exit(f"FAILED to authenticate against {BASE_URL}: {resp.text}")
    SESSION.headers["X-Metabase-Session"] = session_id


def get_pulses():
    return SESSION.get(f"{BASE_URL}/api/pulse", params={"archived": "false"}).json()


def get_alert_ids():
    return [a["id"] for a in SESSION.get(f"{BASE_URL}/api/alert", params={"archived": "false"}).json()]


def pulse_label(p):
    return f"dashboard subscription (dashboard {p['dashboard_id']})" if p.get("dashboard_id") else "standalone pulse"


def archive_pulses(pulses, execute):
    if not pulses:
        print("None to remove.")
    for p in pulses:
        body = {"archived": True}
        label = pulse_label(p)
        print(f"PUT {BASE_URL}/api/pulse/{p['id']} {json.dumps(body)}  # {label}")
        if not execute:
            continue
        resp = SESSION.put(f"{BASE_URL}/api/pulse/{p['id']}", json=body)
        if resp.ok:
            print(f"Archived {label} {p['id']}")
        else:
            print(f"FAILED to archive {label} {p['id']} (HTTP {resp.status_code})", file=sys.stderr)


def archive_alerts(alert_ids, execute):
    if not alert_ids:
        print("None to remove.")
        return
    body = {"notification_ids": alert_ids, "action": "archive"}
    print(f"POST {BASE_URL}/api/notification/admin/bulk {json.dumps(body)}")
    if not execute:
        return
    resp = SESSION.post(f"{BASE_URL}/api/notification/admin/bulk", json=body)
    updated = resp.json().get("updated") if resp.ok else None
    if updated == len(alert_ids):
        print(f"Bulk-archived {updated} alert(s): {resp.text}")
    else:
        print(f"FAILED to bulk-archive alerts (HTTP {resp.status_code}, expected {len(alert_ids)} updated): "
              f"{resp.text}", file=sys.stderr)


def main():
    execute = "--execute" in sys.argv

    print("\n== Authenticating ==")
    authenticate()

    print("\n== Getting current counts ==")
    pulses = get_pulses()
    alert_ids = get_alert_ids()
    sub_count = sum(1 for p in pulses if p.get("dashboard_id"))
    print(f"Found {sub_count} active dashboard subscription(s), {len(pulses) - sub_count} active standalone "
          f"pulse(s), {len(alert_ids)} active alert(s).")

    if not pulses and not alert_ids:
        print("Nothing to delete.")
        return

    if not execute:
        print("\n-- DRY RUN (default): no requests will be sent --")
        print("\n== Removing dashboard subscriptions ==")
        archive_pulses(pulses, execute=False)
        print("\n== Removing alerts ==")
        archive_alerts(alert_ids, execute=False)
        print("\nRe-run with --execute to actually archive these.")
        return

    confirm = input(f"\nAbout to archive {sub_count} dashboard subscription(s), "
                     f"{len(pulses) - sub_count} standalone pulse(s), and {len(alert_ids)} alert(s). "
                     f"This cannot be easily undone (see README). Type 'yes' to confirm: ")
    if confirm != "yes":
        sys.exit("Aborted.")

    print("\n== Removing dashboard subscriptions ==")
    archive_pulses(pulses, execute=True)

    print("\n== Removing alerts ==")
    archive_alerts(alert_ids, execute=True)

    print("\n== Retesting ==")
    pulses_remaining = len(get_pulses())
    alerts_remaining = len(get_alert_ids())
    print(f"After cleanup: {pulses_remaining} active dashboard subscription(s)/pulse(s), "
          f"{alerts_remaining} active alert(s) remain.")

    print("\n== Done ==")
    if pulses_remaining == 0 and alerts_remaining == 0:
        print("OK: all subscriptions and alerts archived.")
    else:
        sys.exit("WARNING: some subscriptions/alerts were not archived.")


if __name__ == "__main__":
    main()
