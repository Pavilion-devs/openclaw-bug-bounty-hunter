Plan: Solana Bug Bounty Hunter — OpenClaw Skill
Architecture Overview
Project Structure (GitHub Repo)
solana-bounty-hunter/
├── SKILL.md                    # OpenClaw skill definition
├── README.md                   # Setup guide for hackathon judges
├── scripts/
│   ├── github-monitor.py       # Discover new Solana repos via GitHub API
│   ├── clone-and-scan.sh       # Clone repo + run static analyzers
│   ├── findings-db.py          # Store/query findings (SQLite)
│   └── report-formatter.py     # Format findings for submission
├── prompts/
│   ├── audit-system.md         # System prompt for code audit agent
│   └── triage-system.md        # System prompt for severity classification
├── analyzers/
│   ├── solana-patterns.yaml    # Semgrep rules for Solana vulns
│   └── common-vulns.md         # Known Solana vulnerability patterns
├── setup.sh                    # One-command install (deps + OpenClaw skill)
└── openclaw.example.json       # Example config snippet
How OpenClaw Fits In
Component	OpenClaw Feature	What It Does
Scheduling	cron tool	Triggers GitHub scan every N hours
GitHub Discovery	web_search + exec	Find new Solana repos, clone them
Code Analysis	exec + LLM reasoning	Run static analyzers, then LLM reviews flagged code
Parallel Audits	Sub-agents (sessions_spawn)	Audit multiple repos concurrently
Human Review	message tool (Telegram/WhatsApp)	Send findings to user, wait for approve/reject
Slash Commands	/bounty_scan <repo>	Manual trigger for a specific repo
Reporting	exec + web_fetch	Generate reports, optionally submit to platforms
SKILL.md Skeleton
---
name: solana-bounty-hunter
description: Autonomous Solana smart contract vulnerability scanner. Monitors GitHub for new repos, runs static analysis + LLM-powered audits, and reports findings for human review.
metadata: {"openclaw": {"requires": {"bins": ["git", "python3"]}, "primaryEnv": "GITHUB_TOKEN"}}
---
Then the body of SKILL.md contains the agent instructions — how to use the scripts, audit workflow, severity classification, and when to notify the user.

Workflow (What the Agent Actually Does)
Cron fires → agent runs github-monitor.py → gets list of new/updated Solana repos
For each repo → sessions_spawn a sub-agent that:
Clones the repo via exec
Runs semgrep with custom Solana rules
Runs cargo-audit if applicable
LLM reads flagged files and reasons about exploitability
Classifies severity (Critical/High/Medium/Low/FP)
Findings above threshold → sent to you via Telegram/WhatsApp with code snippets + explanation
You reply approve/reject → agent logs the decision, optionally formats for submission
Publishing to ClawHub
Once it's ready:

npx clawhub@latest sync
# or
npx clawhub@latest upload ./solana-bounty-hunter
Anyone can then install it with:

clawhub install solana-bounty-hunter
What to Build First (Hackathon Priority)
SKILL.md + github-monitor.py — get the discovery loop working
Semgrep rules for top 10 Solana vulns (reentrancy, missing signer checks, PDA seed collisions, etc.)
The audit prompt — this is where the LLM value is, make it sharp
Telegram notification flow — demo the human-in-the-loop review
One end-to-end demo — scan a known-vulnerable repo, find the bug, send the alert
This gives you a working demo where anyone clones your repo, installs the skill into their OpenClaw instance, and has an autonomous bounty hunter running.