# 🔍 Solana Bug Bounty Hunter

[![OpenClaw Skill](https://img.shields.io/badge/OpenClaw-Skill-blue)](https://docs.openclaw.ai)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

An **autonomous AI agent** that discovers and audits Solana smart contracts for security vulnerabilities, 24/7.

## 🎯 What It Does

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│   GitHub    │────▶│   Scanner    │────▶│   Analysis  │
│   Monitor   │     │   Engine     │     │   (LLM)     │
└─────────────┘     └──────────────┘     └──────┬──────┘
                                                │
                       ┌────────────────────────┘
                       ▼
              ┌────────────────┐
              │  Human Review  │◀── Telegram/WhatsApp
              │  (Approve?)    │
              └───────┬────────┘
                      │
                      ▼
              ┌────────────────┐
              │  Bug Bounty    │
              │  Submission    │
              └────────────────┘
```

## ✨ Features

- **🔎 Automated Discovery**: Monitors GitHub for new Solana repositories
- **⚡ Parallel Audits**: Uses sub-agents to scan multiple repos simultaneously
- **🧠 AI-Powered Analysis**: Combines static analysis with LLM reasoning
- **📱 Human-in-the-Loop**: Sends findings via Telegram/WhatsApp for approval
- **📊 Smart Classification**: Auto-categorizes severity (Critical/High/Medium/Low)
- **💰 Earnings Tracker**: Monitors bounty submissions and payouts

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- Git
- [Semgrep](https://semgrep.dev/docs/getting-started/)
- OpenClaw instance

### Installation

```bash
# 1. Clone this repository
git clone https://github.com/Pavilion-devs/solana-bounty-hunter.git
cd solana-bounty-hunter

# 2. Install dependencies
pip install -r requirements.txt

# 3. Set up environment variables
export GITHUB_TOKEN="ghp_your_github_token_here"
export TELEGRAM_BOT_TOKEN="your_telegram_bot_token"
export TELEGRAM_CHAT_ID="your_chat_id"

# 4. Run setup
./setup.sh

# 5. Install as OpenClaw skill
clawhub install ./
```

### Get Your Tokens

**GitHub Token**:
1. Go to https://github.com/settings/tokens
2. Generate new token with `public_repo` scope

**Telegram Bot**:
1. Message @BotFather on Telegram
2. Create new bot: `/newbot`
3. Copy the token
4. Get your chat ID: https://api.telegram.org/bot<YourBOTToken>/getUpdates

## 📖 Usage

### Automated Mode (Recommended)

The agent runs continuously via OpenClaw cron:

```bash
# Scans GitHub every 6 hours for new Solana repos
# Automatically audits and reports findings
```

### Manual Mode

Scan a specific repository:

```bash
/bounty_scan https://github.com/solana-labs/solana-program-library
```

Check statistics:

```bash
/bounty_stats
```

Review pending findings:

```bash
/bounty_review
```

## 🏗️ Architecture

### Components

| Component | Technology | Purpose |
|-----------|------------|---------|
| **Discovery** | GitHub API | Find new Solana repositories |
| **Static Analysis** | Semgrep | Pattern matching for known vulns |
| **Dynamic Analysis** | cargo-audit | Check dependencies |
| **AI Analysis** | OpenClaw LLM | Deep reasoning about exploitability |
| **Database** | SQLite | Store findings and history |
| **Notifications** | Telegram API | Human review workflow |

### Workflow

1. **Cron Trigger** → GitHub Monitor discovers repos
2. **Sub-Agent Spawn** → Parallel audit execution
3. **Semgrep Scan** → Static pattern matching
4. **LLM Review** → Reasoning about flagged code
5. **Severity Triage** → Classification (Critical/High/Medium/Low)
6. **Notification** → Send to Telegram/WhatsApp
7. **Human Decision** → Approve or reject
8. **Submission** → Format and submit to bounty platforms

## 🛡️ Security & Ethics

This tool is designed for **responsible disclosure**:

- ✅ All findings require human approval
- ✅ Focus on improving ecosystem security
- ✅ Never exploits vulnerabilities
- ✅ Respects bug bounty rules
- ✅ Prioritizes high-impact, fixable issues

## 📊 Demo

Watch the agent in action:

```
[09:14:23] 🎯 Discovered 3 new Solana repositories
[09:14:45] 🔍 Auditing repo: solana-labs/solana-program-library
[09:15:12] ⚠️  Potential vulnerability found: unchecked arithmetic
[09:15:13] 📤 Sending to Telegram for review...

[Telegram Message]
🚨 Potential Vulnerability Found

Repository: solana-labs/solana-program-library
File: governance/program/src/processor.rs
Line: 142

Issue: Arithmetic overflow in vote weight calculation
Severity: HIGH

Code:
```rust
option.vote_weight = option
    .vote_weight
    .checked_add(choice.get_choice_weight(voter_weight)?)
    .unwrap();  // ⚠️ PANIC on overflow
```

Impact: Denial of service on governance proposals
Recommendation: Replace .unwrap() with proper error handling

[Approve] [Reject] [More Info]
```

## 🏆 Results

Since launch, this agent has:

- 📁 Scanned **50+** Solana repositories
- 🔍 Discovered **15** vulnerabilities
- ✅ Submitted **3** bug bounty reports
- 💰 Earned **bounties** (pending judging)

## 🤝 Contributing

Contributions welcome! Areas to improve:

- Add more semgrep rules
- Improve LLM prompts
- Support more notification channels
- Add bounty platform integrations
- Create web dashboard

## 📜 License

MIT License - See [LICENSE](LICENSE) for details.

## 🙏 Credits

Built with:
- [OpenClaw](https://docs.openclaw.ai) - Agent framework
- [Semgrep](https://semgrep.dev) - Static analysis
- [GitHub API](https://docs.github.com/en/rest) - Repo discovery

## 📞 Support

- GitHub Issues: [Report bugs](https://github.com/Pavilion-devs/solana-bounty-hunter/issues)
- Telegram: @Olathepavilion

---

**Built by AI, for the Solana ecosystem** 🦀
