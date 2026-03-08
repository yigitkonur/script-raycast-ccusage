# Claude Usage — Raycast Script

```
🟢 ━━━━━━━━┈┈ 42%  ↻ 2h18m  7d Op 8% · So 12%  $0 extra
```

## video

https://github.com/user-attachments/assets/6c0163cf-e251-434d-be78-5705106785ea


Shows your Claude.ai usage directly in the Raycast bar. Refreshes every 5 minutes. No API key needed — reads your existing browser session.

**What you see:**

| Part | Meaning |
|------|---------|
| 🟢 ━━━━━━┈┈┈┈ 60% ↻ 1h22m | 5-hour window: 60% used, resets in 1h22m |
| 7d Op 8% · So 5% · Cw 0% | 7-day per-model: Opus / Sonnet / Cowork |
| $4.20 / $25.00 | Extra usage credits consumed this month |

Status dots: 🟢 < 50% · 🟡 50–69% · 🟠 70–89% · 🔴 ≥ 90%

## Requirements

- **macOS** (browser cookie access is macOS-only)
- **[Raycast](https://raycast.com)** installed
- **[uv](https://docs.astral.sh/uv/)** — `brew install uv`
- **Logged into [claude.ai](https://claude.ai)** in Chrome, Safari, Firefox, or Brave
- A **paid Claude plan** (Pro / Team / Enterprise) — free plans have no usage data

## Setup

```bash
git clone https://github.com/yigitkonur/script-raycast-ccusage.git
cd script-raycast-ccusage
chmod +x claude-usage.py
```

Then in Raycast: **Extensions → + → Add Script Directory** → select this folder.

"Claude Usage" appears in Raycast and starts showing your usage inline. First run takes ~2s while `uv` fetches dependencies; subsequent runs use the cache and are instant.

## How it works

1. Reads `sessionKey` (or `__Secure-next-auth.session-token`) from your browser's cookie store via [rookiepy](https://github.com/thewh1teagle/rookiepy), which handles macOS Keychain decryption
2. Calls `claude.ai/api/organizations` and `.../usage` using [curl-cffi](https://github.com/yifeikong/curl-cffi) with Chrome TLS fingerprint impersonation (required to pass Cloudflare)
3. Formats the response into a single-line summary for Raycast's inline mode

No credentials are stored. The cookie is read fresh on each refresh. No data is sent anywhere except to `claude.ai`.

## Troubleshooting

| Problem | Fix |
|---------|-----|
| 🚫 Log in to claude.ai first | Not logged into claude.ai in any supported browser |
| HTTP 403 / no data | `curl-cffi` version mismatch — pin to `>=0.14.0` (already in inline deps) |
| Script not in Raycast | Check `chmod +x claude-usage.py` — Raycast requires the executable bit |
| `uv` not found | `brew install uv` or `curl -LsSf https://astral.sh/uv/install.sh \| sh` |
| Keychain popup | macOS asks once for cookie access — click "Always Allow" to skip future prompts |
| "No usage data" | You're on a free plan — usage endpoint only works for paid plans |

## Alternative: manual venv (no uv)

```bash
python3.12 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

Then change the first line of `claude-usage.py` to:

```python
#!/path/to/your/.venv/bin/python
```

## Credits

Cookie extraction and API pattern adapted from [claude-bar](https://github.com/BOUSHABAMohammed/claude-bar) by [@BOUSHABAMohammed](https://github.com/BOUSHABAMohammed) — a full macOS menu bar app for Claude usage. Use that if you prefer a persistent menu bar icon over a Raycast inline script.

## License

MIT
