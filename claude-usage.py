#!/usr/bin/env -S uv run --python 3.12 --script
# -*- coding: utf-8 -*-
# /// script
# requires-python = ">=3.12"
# dependencies = [
#   "rookiepy==0.5.5",
#   "curl-cffi>=0.14.0",
# ]
# ///

# Required parameters:
# @raycast.schemaVersion 1
# @raycast.title Claude Usage
# @raycast.mode inline
# @raycast.refreshTime 5m

# Optional parameters:
# @raycast.icon ✦
# @raycast.packageName Claude

# Documentation:
# @raycast.author Yigit Konur
# @raycast.authorURL https://github.com/yigitkonur
# @raycast.description Shows Claude Pro usage (5h window + per-model 7-day + credits)

import datetime
import sys
from datetime import timezone

import rookiepy
from curl_cffi import requests

COOKIE_NAMES = ("sessionKey", "__Secure-next-auth.session-token")
BROWSERS = ("chrome", "safari", "firefox", "brave")


def get_cookie():
    for browser in BROWSERS:
        try:
            loader = getattr(rookiepy, browser)
            for c in loader(["claude.ai"]):
                if c["name"] in COOKIE_NAMES:
                    return c["name"], c["value"]
        except Exception:
            continue
    return None, None


def parse_reset(iso_str):
    if not iso_str:
        return None
    try:
        return datetime.datetime.fromisoformat(iso_str)
    except Exception:
        return None


def fmt_reset(iso_str):
    reset_at = parse_reset(iso_str)
    if not reset_at:
        return None
    now = datetime.datetime.now(timezone.utc)
    total_secs = max(int((reset_at - now).total_seconds()), 0)
    hours, remainder = divmod(total_secs, 3600)
    minutes, _ = divmod(remainder, 60)
    return f"{hours}h{minutes:02d}m" if hours else f"{minutes}m"


def fmt_restore_at(iso_str):
    reset_at = parse_reset(iso_str)
    if not reset_at:
        return None
    local_reset = reset_at.astimezone()
    local_now = datetime.datetime.now().astimezone()
    if local_reset.date() == local_now.date():
        return local_reset.strftime("%H:%M")
    tomorrow = local_now.date() + datetime.timedelta(days=1)
    if local_reset.date() == tomorrow:
        return f"tom {local_reset:%H:%M}"
    return local_reset.strftime("%a %H:%M")


def status_dot(pct):
    if pct >= 90:
        return "🔴"
    if pct >= 70:
        return "🟠"
    if pct >= 50:
        return "🟡"
    return "🟢"


def bar(pct, width=10):
    filled = round(pct / 100 * width)
    return "━" * filled + "┈" * (width - filled)


def main():
    name, val = get_cookie()
    if not val:
        print("🚫 Log in to claude.ai first")
        sys.exit(1)

    s = requests.Session(impersonate="chrome120")
    s.cookies.set(name, val, domain="claude.ai")

    resp = s.get("https://claude.ai/api/organizations", timeout=10)
    resp.raise_for_status()
    org_id = resp.json()[0].get("uuid") or resp.json()[0].get("id")

    resp = s.get(f"https://claude.ai/api/organizations/{org_id}/usage", timeout=10)
    resp.raise_for_status()
    data = resp.json()

    parts = []

    fh = data.get("five_hour")
    if fh and fh.get("utilization") is not None:
        pct = fh["utilization"]
        reset = fmt_reset(fh.get("resets_at"))
        restore_at = fmt_restore_at(fh.get("resets_at"))
        parts.append(f"{status_dot(pct)} {bar(pct)} {pct:.0f}%")
        if reset:
            parts.append(f"↻ {reset}")
        if restore_at:
            parts.append(f"at {restore_at}")

    extra = data.get("extra_usage") or {}
    if extra.get("is_enabled"):
        used = extra.get("used_credits", 0)
        limit = extra.get("monthly_limit")
        if limit and used > 0:
            parts.append(f"${used:.2f}/${limit:.2f}")
        elif used > 0:
            parts.append(f"${used:.2f} extra")

    print("  ".join(parts) if parts else "No usage data")


if __name__ == "__main__":
    main()
