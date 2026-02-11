---
name: solana-bounty-hunter
description: Autonomous Solana smart contract vulnerability scanner. Monitors GitHub for new repos, runs static analysis + LLM-powered audits, and reports findings for human review.
metadata:
  {
    "openclaw":
      {
        "emoji": "🎯",
        "requires": { "bins": ["git", "python3", "semgrep"], "env": ["GITHUB_TOKEN", "TELEGRAM_BOT_TOKEN", "TELEGRAM_CHAT_ID"] },
        "primaryEnv": "GITHUB_TOKEN",
      },
  }
---

# Solana Bug Bounty Hunter

An autonomous agent that discovers and audits Solana smart contracts for security vulnerabilities.

## Overview

This skill transforms your OpenClaw instance into a 24/7 bug bounty hunter that:

1. **Discovers** new Solana repositories on GitHub
2. **Audits** them using static analysis + LLM reasoning
3. **Classifies** findings by severity (Critical/High/Medium/Low)
4. **Notifies** you via Telegram/WhatsApp with detailed reports
5. **Learns** from your feedback to improve accuracy

## Workflow

### 1. Discovery (Cron-triggered)
- Scans GitHub API for recently updated Solana repositories
- Filters by activity (stars, commits, language)
- Prioritizes new or actively maintained projects

### 2. Analysis (Parallel Sub-agents)
For each repository:
- Clone the repository
- Run semgrep with Solana-specific rules
- Run cargo audit for dependency vulnerabilities
- LLM reviews flagged code for exploitability
- Classify severity based on impact and likelihood

### 3. Reporting (Human-in-the-loop)
For findings above severity threshold:
- Send Telegram/WhatsApp message with:
  - Repository name and link
  - Vulnerability type and location
  - Code snippet
  - Severity classification
  - Recommended fix
- Wait for human approval/rejection
- Log decision for future learning

### 4. Submission (Optional)
If approved:
- Format report for bug bounty platforms
- Generate PoC code
- Track submission status

## Commands

### `/bounty_scan <repo_url>`
Manually trigger an audit of a specific repository.

Example:
```
/bounty_scan https://github.com/solana-labs/solana-program-library
```

### `/bounty_stats`
Show statistics:
- Repositories scanned
- Findings discovered
- Bounties submitted
- Earnings tracked

### `/bounty_review`
Review pending findings awaiting approval.

## Configuration

Required environment variables:
- `GITHUB_TOKEN` - GitHub API token for repo discovery
- `TELEGRAM_BOT_TOKEN` - Telegram bot token for notifications
- `TELEGRAM_CHAT_ID` - Your Telegram chat ID

Optional:
- `MIN_SEVERITY` - Minimum severity to report (default: "High")
- `SCAN_INTERVAL_HOURS` - Cron interval (default: 6)
- `MAX_REPOS_PER_SCAN` - Limit concurrent audits (default: 5)

## Severity Classification

### Critical
- Direct fund loss or theft
- Unauthorized minting/burning
- Privilege escalation

### High
- Denial of service with economic impact
- Oracle manipulation
- Flash loan attacks

### Medium
- Logic errors affecting protocol
- Missing validation checks
- Race conditions

### Low
- Best practice violations
- Code quality issues
- Gas optimizations

## File Structure

```
solana-bounty-hunter/
├── SKILL.md                    # This file
├── README.md                   # Setup and usage guide
├── scripts/
│   ├── github-monitor.py       # GitHub repo discovery
│   ├── clone-and-scan.sh       # Clone + run analyzers
│   ├── findings-db.py          # SQLite database operations
│   └── report-formatter.py     # Format findings for submission
├── prompts/
│   ├── audit-system.md         # LLM system prompt for audits
│   └── triage-system.md        # Severity classification prompt
└── analyzers/
    ├── solana-patterns.yaml    # Semgrep rules for Solana
    └── common-vulns.md         # Known vulnerability patterns
```

## Safety & Ethics

This tool is designed for **responsible disclosure**:
- All findings require human approval before submission
- Focuses on improving ecosystem security
- Never exploits vulnerabilities for personal gain
- Respects bug bounty program rules

## Installation

1. Install dependencies:
```bash
pip install requests sqlite3 python-telegram-bot
# Install semgrep: https://semgrep.dev/docs/getting-started/
```

2. Set environment variables:
```bash
export GITHUB_TOKEN="your_github_token"
export TELEGRAM_BOT_TOKEN="your_telegram_bot_token"
export TELEGRAM_CHAT_ID="your_chat_id"
```

3. Run setup:
```bash
./setup.sh
```

4. Start hunting:
```bash
# Via cron (automated)
# Or manual scan
/bounty_scan https://github.com/user/repo
```

## Credits

Built with OpenClaw for the Solana ecosystem.
