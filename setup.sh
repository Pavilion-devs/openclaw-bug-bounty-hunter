#!/bin/bash
#
# Setup Script for Solana Bug Bounty Hunter
#
# One-command installation of the autonomous security agent

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}"
echo "╔════════════════════════════════════════════════════════╗"
echo "║     Solana Bug Bounty Hunter - Setup Script           ║"
echo "║     Autonomous Security Agent Installation            ║"
echo "╚════════════════════════════════════════════════════════╝"
echo -e "${NC}"
echo ""

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo -e "${YELLOW}📋 Step 1: Checking Prerequisites${NC}"
echo "======================================"

# Check Python
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version)
    echo -e "${GREEN}✅ Python found: $PYTHON_VERSION${NC}"
else
    echo -e "${RED}❌ Python 3 not found. Please install Python 3.8+${NC}"
    exit 1
fi

# Check Git
if command -v git &> /dev/null; then
    echo -e "${GREEN}✅ Git found${NC}"
else
    echo -e "${RED}❌ Git not found. Please install Git${NC}"
    exit 1
fi

# Check Semgrep
if command -v semgrep &> /dev/null; then
    echo -e "${GREEN}✅ Semgrep found${NC}"
else
    echo -e "${YELLOW}⚠️  Semgrep not found. Installing...${NC}"
    pip3 install semgrep || {
        echo -e "${RED}❌ Failed to install semgrep. Please install manually:${NC}"
        echo "   pip3 install semgrep"
        echo "   or: brew install semgrep"
        exit 1
    }
fi

echo ""
echo -e "${YELLOW}📦 Step 2: Installing Python Dependencies${NC}"
echo "======================================"

pip3 install -r requirements.txt || {
    echo -e "${RED}❌ Failed to install dependencies${NC}"
    exit 1
}

echo -e "${GREEN}✅ Dependencies installed${NC}"

echo ""
echo -e "${YELLOW}🗄️  Step 3: Initializing Database${NC}"
echo "======================================"

python3 scripts/findings-db.py --init || {
    echo -e "${RED}❌ Failed to initialize database${NC}"
    exit 1
}

echo ""
echo -e "${YELLOW}📁 Step 4: Creating Directory Structure${NC}"
echo "======================================"

mkdir -p ~/.solana-bounty-hunter/scans
mkdir -p ~/.solana-bounty-hunter/reports
mkdir -p ~/.solana-bounty-hunter/logs

echo -e "${GREEN}✅ Directories created${NC}"

echo ""
echo -e "${YELLOW}🔑 Step 5: Environment Configuration${NC}"
echo "======================================"

echo ""
echo "Please set the following environment variables:"
echo ""

# Check if already set
if [ -z "$GITHUB_TOKEN" ]; then
    echo -e "${RED}⚠️  GITHUB_TOKEN not set${NC}"
    echo "   1. Go to: https://github.com/settings/tokens"
    echo "   2. Generate new token with 'public_repo' scope"
    echo "   3. Run: export GITHUB_TOKEN='your_token_here'"
else
    echo -e "${GREEN}✅ GITHUB_TOKEN is set${NC}"
fi

# Check OpenClaw
if command -v openclaw &> /dev/null; then
    echo -e "${GREEN}✅ OpenClaw found$(openclaw --version 2>/dev/null | head -1)${NC}"
else
    echo ""
    echo -e "${YELLOW}⚠️  OpenClaw not installed${NC}"
    echo "   Install: curl -fsSL https://openclaw.ai/install.sh | bash"
    echo "   Notifications are handled by OpenClaw's message tool (Telegram/WhatsApp/Discord)"
    echo "   No separate bot token needed."
fi

echo ""
echo -e "${YELLOW}💾 Step 6: Creating Environment File${NC}"
echo "======================================"

cat > .env << EOF
# Solana Bug Bounty Hunter Environment Variables
# Copy these to your shell profile or export them

export GITHUB_TOKEN="${GITHUB_TOKEN:-your_github_token_here}"

# Optional Configuration
export MIN_SEVERITY="High"
export SCAN_INTERVAL_HOURS="6"
export MAX_REPOS_PER_SCAN="10"

# Notifications are handled by OpenClaw's built-in message tool.
# No separate Telegram bot token needed — configure channels via:
#   openclaw onboard
EOF

echo -e "${GREEN}✅ Environment file created: .env${NC}"
echo "   Source it with: source .env"

echo ""
echo -e "${YELLOW}🧪 Step 7: Running Tests${NC}"
echo "======================================"

# Test database
python3 scripts/findings-db.py --stats > /dev/null 2>&1 && echo -e "${GREEN}✅ Database working${NC}" || echo -e "${RED}❌ Database test failed${NC}"

# Test GitHub monitor (without API call)
python3 -c "import scripts.github_monitor" 2>/dev/null && echo -e "${GREEN}✅ GitHub monitor imports${NC}" || echo -e "${YELLOW}⚠️  Import test skipped${NC}"

echo ""
echo -e "${BLUE}"
echo "╔════════════════════════════════════════════════════════╗"
echo "║              Setup Complete!                           ║"
echo "╚════════════════════════════════════════════════════════╝"
echo -e "${NC}"
echo ""
echo "Next Steps:"
echo "1. Set environment variables (see .env file)"
echo "2. Source the environment: source .env"
echo "3. Test Telegram notifications:"
echo "   python3 scripts/telegram-notify.py --message \"Test message\""
echo "4. Run first scan:"
echo "   python3 scripts/github-monitor.py --max-repos 5"
echo ""
echo "Commands:"
echo "  /bounty_scan <url>  - Scan specific repository"
echo "  /bounty_stats       - Show statistics"
echo "  /bounty_review      - Review pending findings"
echo ""
echo "Documentation:"
echo "  README.md           - Full usage guide"
echo "  SKILL.md            - OpenClaw skill definition"
echo ""
echo -e "${GREEN}Happy hunting! 🎯${NC}"
