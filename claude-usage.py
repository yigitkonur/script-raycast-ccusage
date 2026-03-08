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


def fmt_reset(iso_str):
    if not iso_str:
        return None
    try:
        resets = datetime.datetime.fromisoformat(iso_str)
        now = datetime.datetime.now(timezone.utc)
        total_secs = max(int((resets - now).total_seconds()), 0)
        hours, remainder = divmod(total_secs, 3600)
        minutes, _ = divmod(remainder, 60)
        return f"{hours}h{minutes:02d}m" if hours else f"{minutes}m"
    except Exception:
        return None


def status_dot(pct):
    if pct >= 90:
        return "\U0001F534"   # red
    if pct >= 70:
        return "\U0001F7E0"   # orange
    if pct >= 50:
        return "\U0001F7E1"   # yellow
    return "\U0001F7E2"       # green


def bar(pct, width=10):
    filled = round(pct / 100 * width)
    return "\u2501" * filled + "\u2508" * (width - filled)


def main():
    name, val = get_cookie()
    if not val:
        print("\U0001F6AB Log in to claude.ai first")
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

    # 5-hour window
    fh = data.get("five_hour")
    if fh and fh.get("utilization") is not None:
        pct = fh["utilization"]
        reset = fmt_reset(fh.get("resets_at"))
        reset_str = f"  \u21BB {reset}" if reset else ""
        parts.append(f"{status_dot(pct)} {bar(pct)} {pct:.0f}%{reset_str}")

    # Per-model 7-day windows
    model_keys = [
        ("seven_day_opus", "Op"),
        ("seven_day_sonnet", "So"),
        ("seven_day_cowork", "Cw"),
    ]
    active_models = []
    for key, label in model_keys:
        window = data.get(key)
        if window and window.get("utilization") is not None:
            pct = window["utilization"]
            active_models.append(f"{label}\u2009{pct:.0f}%")
    if active_models:
        parts.append("7d " + " \u2022 ".join(active_models))

    # Legacy seven_day fallback
    sd = data.get("seven_day")
    if sd and sd.get("utilization") is not None and not active_models:
        pct = sd["utilization"]
        reset = fmt_reset(sd.get("resets_at"))
        reset_str = f" \u21BB {reset}" if reset else ""
        parts.append(f"7d {pct:.0f}%{reset_str}")

    # Credits
    extra = data.get("extra_usage") or {}
    if extra.get("is_enabled"):
        used = extra.get("used_credits", 0)
        limit = extra.get("monthly_limit")
        if limit:
            parts.append(f"${used:.2f}\u2009/\u2009${limit:.2f}")
        elif used > 0:
            parts.append(f"${used:.2f} spent")
        else:
            parts.append("$0 extra")

    print("  ".join(parts) if parts else "No usage data")


if __name__ == "__main__":
    main()
