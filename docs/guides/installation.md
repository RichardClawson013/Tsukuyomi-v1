# Installation Guide

**Audience:** Anyone installing Tsukuyomi for the first time.
**Prerequisites:** Python 3.11+, Git, ≥4 GB RAM, Linux/macOS/WSL2.
**Reading time:** 5–10 minutes.

---

## 1. System requirements

| Component | Minimum | Recommended |
| --- | --- | --- |
| OS | Linux 5.10+, macOS 13+, WSL2 (Ubuntu 22.04+) | Linux 6.x or WSL2 with `/dev/kvm` |
| Python | 3.11.0 | 3.12.x |
| Git | 2.30 | 2.40+ |
| Disk | 500 MB for Tsukuyomi + memory growth | 5 GB to allow a year of logs |
| RAM | 2 GB free | 4 GB free |
| Optional | Node.js 20+ (for GitNexus MCP server) | npx in PATH |

If `/dev/kvm` is present (`ls -l /dev/kvm`), you are ready for the v1.1 Microsandbox migration without further work; v1.0 itself does not require it.

## 2. Install via pip (recommended)

```bash
python -m pip install --user tsukuyomi
```

This installs the `tsukuyomi` CLI and the importable Python package. Verify:

```bash
tsukuyomi --version
# tsukuyomi 1.0.0
```

## 3. Install from source (for contributors)

```bash
git clone https://github.com/robdevet/tsukuyomi.git
cd tsukuyomi
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
pytest    # confirms the install
```

## 4. Initialize a Tsukuyomi data directory

Tsukuyomi stores its configuration, logs, and anatomic memory in `~/.local/share/tsukuyomi/` (Linux/macOS) or `%APPDATA%\tsukuyomi\` (Windows). On first run:

```bash
tsukuyomi init
```

This creates:

```
~/.local/share/tsukuyomi/
├── config/
│   ├── corelaw.json              copy of corelaw.example.json
│   ├── knee_patterns.json
│   ├── gary_evasion_phrases.json
│   ├── gary_risk_keywords.json
│   └── model_pricing.json
├── data/
│   ├── memory.db                 (SQLite, empty)
│   ├── logs/                     (empty)
│   ├── audits/                   (empty)
│   ├── proposals/                (empty)
│   └── budget_state.json         {}
└── README.md                     pointer back to docs
```

Inspect the generated config:

```bash
$EDITOR ~/.local/share/tsukuyomi/config/corelaw.json
```

## 5. Configure your provider credentials

Tsukuyomi forwards to one or more upstream LLM providers. Configure their credentials via environment variables (Tsukuyomi never reads keys from `corelaw.json`):

```bash
# In your shell profile (~/.bashrc, ~/.zshrc, etc.)
export ANTHROPIC_API_KEY=sk-ant-...
export OPENAI_API_KEY=sk-...
export OPENROUTER_API_KEY=sk-or-...
```

Tsukuyomi reads these on startup. Missing keys for unconfigured upstreams is fine; only configured upstreams need keys.

## 6. Optional: install GitNexus for the Shoulders organ

The Shoulders organ uses GitNexus for blast-radius analysis. Install:

```bash
npm install -g gitnexus
```

Verify:

```bash
gitnexus --version
```

Without GitNexus, the Shoulders return `UNKNOWN` for all queries, which downstream is treated as `HIGH` risk (conservative). Tsukuyomi works without GitNexus; it's just less precise.

## 7. Start Tsukuyomi

```bash
tsukuyomi start
# 2026-04-19 14:00:00  INFO  tsukuyomi.interceptor  listening on http://127.0.0.1:9999
```

Leave this terminal open. From another terminal, verify with a test request:

```bash
curl -s http://localhost:9999/health
# {"status":"ok","version":"1.0.0","uptime_seconds":12}
```

Now you are ready to point an agent at Tsukuyomi. Continue with the integration guide for your agent: `integrating_claude_code.md`, `integrating_hermes.md`, `integrating_cursor.md`, or `integrating_custom.md`.

## 8. Uninstall

```bash
tsukuyomi stop
pip uninstall tsukuyomi
# data is preserved in ~/.local/share/tsukuyomi/
# remove explicitly if desired:
rm -rf ~/.local/share/tsukuyomi/
```

## 9. Common issues

**"address already in use" on port 9999.** Another process holds the port. Use `--port 9998` or stop the conflicting process.

**"sqlite3.OperationalError: unable to open database file."** The data directory is not writable; check `ls -ld ~/.local/share/tsukuyomi/`.

**"GitNexus MCP server failed to start" warning.** Either install GitNexus (Section 6) or accept the conservative-fallback behavior (`UNKNOWN` → `HIGH`).

For more, see `troubleshooting.md`.
