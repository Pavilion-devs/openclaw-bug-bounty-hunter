# 🔍 Solana Bug Bounty Hunter

[![OpenClaw Skill](https://img.shields.io/badge/OpenClaw-Skill-blue)](https://docs.openclaw.ai)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

An **autonomous AI agent** built as an [OpenClaw](https://docs.openclaw.ai) skill that discovers and audits Solana smart contracts for security vulnerabilities, 24/7.

## 🎯 How It Works

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│   GitHub    │────▶│   Semgrep    │────▶│  LLM Audit  │
│   Monitor   │     │   Scanner    │     │  (OpenClaw) │
└─────────────┘     └──────────────┘     └──────┬──────┘
      ▲                                         │
      │ cron                   ┌────────────────┘
      │                        ▼
┌─────────────┐       ┌────────────────┐
│  OpenClaw   │──────▶│  Human Review  │◀── Telegram / WhatsApp / Discord
│  Gateway    │       │  (Approve?)    │    (any OpenClaw channel)
└─────────────┘       └───────┬────────┘
                              │
                              ▼
                      ┌────────────────┐
                      │  Bug Bounty    │
                      │  Submission    │
                      └────────────────┘
```

## ✨ Features

- **🔎 Automated Discovery** — Monitors GitHub for new Solana repos via cron
- **⚡ Parallel Audits** — Uses OpenClaw sub-agents to scan multiple repos simultaneously
- **🧠 AI-Powered Analysis** — Semgrep static analysis + LLM reasoning about exploitability
- **📱 Human-in-the-Loop** — Findings sent to you via whatever channel you use (Telegram, WhatsApp, Discord, etc.)
- **📊 Smart Classification** — Auto-categorizes severity (Critical/High/Medium/Low)
- **💾 Findings Database** — SQLite DB tracks all findings, scan history, and bounty submissions
- **💰 Earnings Tracker** — Monitors bounty submissions and payouts

## 🚀 Quick Start

### Prerequisites

- [OpenClaw](https://docs.openclaw.ai/start/getting-started) installed and running (with at least one channel configured)
- Python 3.8+
- Git
- A [GitHub token](https://github.com/settings/tokens) with `public_repo` scope

### Installation

```bash
# 1. Clone this repository
git clone https://github.com/Pavilion-devs/openclaw-bug-bounty-hunter.git
cd openclaw-bug-bounty-hunter

# 2. Run setup (installs Python deps, semgrep, initializes database)
chmod +x setup.sh
./setup.sh

# 3. Set your GitHub token
export GITHUB_TOKEN="ghp_your_github_token_here"

# 4. Install as OpenClaw skill (copy to your workspace skills folder)
cp -r . ~/.openclaw/workspace/skills/solana-bounty-hunter
```

> **No Telegram bot token needed!** Notifications are handled by OpenClaw's built-in `message` tool — it sends findings through whatever channel you already have configured (Telegram, WhatsApp, Discord, etc.).

### Configure the GitHub Token in OpenClaw

Add your token to `~/.openclaw/openclaw.json` so the skill can access it:

```json
{
  "skills": {
    "entries": {
      "solana-bounty-hunter": {
        "enabled": true,
        "apiKey": "ghp_your_github_token_here"
      }
    }
  }
}
```

Then restart the gateway: `openclaw gateway restart`

## 📖 Usage

All commands are sent through your OpenClaw chat (Telegram, WhatsApp, Control UI, etc.):

### Manual Scan

```
/bounty_scan https://github.com/coral-xyz/anchor
```

Clones the repo, runs semgrep with 15 Solana-specific rules, saves findings to the database, then uses the LLM to triage and report real vulnerabilities.

### Discover New Repos

```
/bounty_discover
```

Searches GitHub for recently updated Solana repositories, ranked by priority score (stars, activity, DeFi keywords).

### Check Statistics

```
/bounty_stats
```

Shows total findings, severity breakdown, submission status, and earnings.

### Review Pending Findings

```
/bounty_review
```

Lists all findings awaiting your approval. Reply with:
- `approve <finding_id>` — mark as confirmed, ready for submission
- `reject <finding_id>` — mark as false positive
- `more info <finding_id>` — get deeper LLM analysis

### Generate Report

```
/bounty_report <finding_id>
```

Generates a professional bug bounty submission report in Markdown.

### Enable Automated Scanning

Tell the agent to set up a cron job:

> "Set up automated scanning every 6 hours"

The agent will use OpenClaw's `cron` tool to schedule periodic GitHub discovery + auditing.

## 🏗️ Architecture

### How OpenClaw Integrates

| What | OpenClaw Tool | Purpose |
|------|--------------|---------|
| Run scripts | `exec` | GitHub monitor, clone-and-scan, findings DB |
| Notifications | `message` | Send findings to Telegram/WhatsApp/Discord |
| Scheduling | `cron` | Automated scans every N hours |
| Parallel audits | `sessions_spawn` | Multiple repos scanned simultaneously |
| Research | `web_search` / `web_fetch` | Check bounty programs, research repos |
| Code review | `read` | Read flagged source files for LLM analysis |

### Workflow

1. **Cron fires** → `exec` runs `github-monitor.py` → discovers repos
2. **Per repo** → `exec` runs `clone-and-scan.sh` → semgrep analysis
3. **Findings saved** → auto-inserted into SQLite database
4. **LLM triage** → agent reads flagged files, classifies severity, filters false positives
5. **Notification** → `message` tool sends findings to your channel
6. **Human review** → you reply approve/reject
7. **Report** → `exec` runs `report-formatter.py` for submission

### File Structure

```
solana-bounty-hunter/
├── SKILL.md                        # OpenClaw skill definition
├── README.md                       # This file
├── setup.sh                        # One-command setup
├── requirements.txt                # Python dependencies
├── scripts/
│   ├── github-monitor.py           # GitHub repo discovery
│   ├── clone-and-scan.sh           # Clone + semgrep + DB insert
│   ├── findings-db.py              # SQLite database operations
│   ├── report-formatter.py         # Bug bounty report generator
│   └── telegram-notify.py          # Standalone notifier (non-OpenClaw use)
├── prompts/
│   ├── audit-system.md             # LLM system prompt for code auditing
│   └── triage-system.md            # Severity classification guide
└── analyzers/
    ├── solana-patterns.yaml        # 15 semgrep rules for Solana vulns
    └── common-vulns.md             # Known vulnerability patterns reference
```

### Semgrep Rules (15 patterns)

| Rule | Severity | What It Catches |
|------|----------|-----------------|
| `missing-signer-transfer` | 🔴 High | Fund transfers without signer check |
| `unchecked-arithmetic` | 🔴 High | `+`, `-`, `*` without overflow protection |
| `unwrap-on-arithmetic` | 🔴 High | `.unwrap()` on checked operations |
| `missing-owner-check` | 🟡 Medium | Account used without owner validation |
| `potential-reentrancy` | 🟡 Medium | State changes after external CPI calls |
| `pda-seed-validation` | 🟡 Medium | PDA derivation without seed validation |
| `missing-init-check` | 🟡 Medium | Account used without initialization check |
| `dangerous-expect` | 🟡 Medium | `.expect()` that can panic |
| `unchecked-cpi-result` | 🔴 High | CPI invoke without `?` error handling |
| `token-account-ownership` | 🟡 Medium | Token transfer without ownership check |
| `oracle-confidence-check` | 🟡 Medium | Oracle price without confidence validation |
| `mutable-borrow-check` | 🟡 Medium | Multiple mutable borrows on accounts |
| `clock-manipulation` | 🟢 Low | Clock timestamp usage (TOCTOU risk) |
| `close-account-safety` | 🟡 Medium | Account close without proper cleanup |
| `authority-transfer` | 🔴 High | Authority reassignment without validation |

## 🛡️ Security & Ethics

This tool is designed for **responsible disclosure**:

- ✅ All findings require human approval before submission
- ✅ Focus on improving Solana ecosystem security
- ✅ Never exploits vulnerabilities for personal gain
- ✅ Respects bug bounty program rules and scope
- ✅ LLM filters false positives — only real issues get reported

## 📊 Demo

```
[09:14:23] 🎯 Discovered 3 new Solana repositories
[09:14:45] 🔍 Auditing repo: anza-xyz/pinocchio (⭐849, priority 48/100)
[09:15:12] ⚠️  193 semgrep findings → LLM triaging...
[09:15:45] 🔴 3 real vulnerabilities identified
[09:15:46] 📤 Sending to Telegram for review...

[Telegram/WhatsApp Message]
🔴 HIGH Finding — pinocchio

📁 File: src/processor.rs
📍 Line: 142

🔍 Type: Missing Signer Check
📝 Fund transfer without authorization verification

Description:
The transfer function does not verify the sender is a signer,
allowing anyone to transfer lamports from any account.

Code:
  **from.try_borrow_mut_lamports()? -= amount;
  **to.try_borrow_mut_lamports()? += amount;

Recommendation:
Add signer check before transfer operation.

Reply "approve FND-abc123" or "reject FND-abc123"
```

## 🤝 Contributing

Contributions welcome! Areas to improve:

- Add more semgrep rules for Solana-specific patterns
- Improve LLM audit prompts for fewer false positives
- Add bounty platform API integrations (Immunefi, HackerOne)
- Support Anchor IDL parsing for smarter analysis
- Create a web dashboard for findings

## 📜 License

MIT License - See [LICENSE](LICENSE) for details.

## 🙏 Credits

Built with:
- [OpenClaw](https://docs.openclaw.ai) — AI agent framework and orchestration
- [Semgrep](https://semgrep.dev) — Static analysis engine
- [GitHub API](https://docs.github.com/en/rest) — Repository discovery

## 📞 Support

- GitHub Issues: [Report bugs](https://github.com/Pavilion-devs/openclaw-bug-bounty-hunter/issues)
- Telegram: @Olathepavilion

---

**Built for the Solana ecosystem 🦀 — Powered by OpenClaw 🦞**
