#!/usr/bin/env python3
"""
Telegram Notifier for Solana Bug Bounty Hunter

Sends vulnerability findings to Telegram for human review.

Usage:
    python telegram-notify.py --finding finding.json
    python telegram-notify.py --finding-id FND-20240210-123
    python telegram-notify.py --message "Custom message"
"""

import os
import sys
import json
import argparse
import requests
from typing import Dict, Optional

# Telegram configuration
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")
TELEGRAM_API_URL = "https://api.telegram.org/bot{token}/sendMessage"


class TelegramNotifier:
    """Sends notifications via Telegram."""
    
    def __init__(self, bot_token: str = None, chat_id: str = None):
        self.bot_token = bot_token or TELEGRAM_BOT_TOKEN
        self.chat_id = chat_id or TELEGRAM_CHAT_ID
        
        if not self.bot_token or not self.chat_id:
            raise ValueError(
                "TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID must be set. "
                "Get your bot token from @BotFather and chat ID from @userinfobot"
            )
    
    def send_message(self, message: str, parse_mode: str = "HTML") -> bool:
        """
        Send a message to Telegram.
        
        Args:
            message: Message text (HTML formatted)
            parse_mode: Parse mode (HTML, Markdown, MarkdownV2)
            
        Returns:
            True if sent successfully, False otherwise
        """
        url = TELEGRAM_API_URL.format(token=self.bot_token)
        
        payload = {
            "chat_id": self.chat_id,
            "text": message,
            "parse_mode": parse_mode,
            "disable_web_page_preview": False,
        }
        
        try:
            response = requests.post(url, json=payload, timeout=30)
            response.raise_for_status()
            result = response.json()
            
            if result.get("ok"):
                print(f"✅ Message sent successfully (ID: {result['result']['message_id']})")
                return True
            else:
                print(f"❌ Telegram API error: {result.get('description')}")
                return False
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Failed to send message: {e}")
            return False
    
    def send_finding(self, finding: Dict) -> bool:
        """
        Send a vulnerability finding to Telegram.
        
        Args:
            finding: Finding dictionary with vulnerability details
            
        Returns:
            True if sent successfully, False otherwise
        """
        # Severity emoji mapping
        severity_emoji = {
            "Critical": "🔴",
            "High": "🟠",
            "Medium": "🟡",
            "Low": "🟢",
            "Informational": "⚪"
        }
        
        severity = finding.get("severity", "Unknown")
        emoji = severity_emoji.get(severity, "⚪")
        
        # Build message
        message = f"""{emoji} <b>New {severity} Severity Finding</b>

<b>Repository:</b> <code>{finding.get('repo_name', 'Unknown')}</code>
<b>Finding ID:</b> <code>{finding.get('finding_id', 'N/A')}</code>

<b>Vulnerability:</b> {finding.get('vulnerability_type', 'Unknown')}
<b>Title:</b> {finding.get('title', 'No title')}

<b>Location:</b>
📁 File: <code>{finding.get('file_path', 'N/A')}</code>
📍 Line: {finding.get('line_number', 'N/A')}

<b>Description:</b>
{finding.get('description', 'No description')[:500]}

<b>Impact:</b>
{finding.get('impact', 'No impact analysis')[:300]}

<b>Confidence:</b> {finding.get('confidence', 0)}%
<b>Analyzer:</b> {finding.get('analyzer', 'Unknown')}

<b>Actions:</b>
👉 Review: <code>/bounty_review {finding.get('finding_id')}</code>
✅ Approve: <code>/bounty_approve {finding.get('finding_id')}</code>
❌ Reject: <code>/bounty_reject {finding.get('finding_id')}</code>

<b>Full Details:</b>
<code>{finding.get('repo_url', '')}</code>
"""
        
        # Truncate if too long
        if len(message) > 4000:
            message = message[:3900] + "\n\n<i>(Message truncated - see full report in database)</i>"
        
        return self.send_message(message)
    
    def send_summary(self, stats: Dict) -> bool:
        """
        Send a summary report.
        
        Args:
            stats: Statistics dictionary
            
        Returns:
            True if sent successfully
        """
        message = f"""📊 <b>Solana Bug Bounty Hunter - Summary</b>

<b>Scan Statistics:</b>
• Total Findings: {stats.get('total_findings', 0)}
• Recent (7 days): {stats.get('recent_findings', 0)}

<b>By Severity:</b>
🔴 Critical: {stats.get('by_severity', {}).get('Critical', 0)}
🟠 High: {stats.get('by_severity', {}).get('High', 0)}
🟡 Medium: {stats.get('by_severity', {}).get('Medium', 0)}
🟢 Low: {stats.get('by_severity', {}).get('Low', 0)}

<b>By Status:</b>
⏳ Pending Review: {stats.get('by_status', {}).get('pending', 0)}
✅ Approved: {stats.get('by_status', {}).get('approved', 0)}
📤 Submitted: {stats.get('by_status', {}).get('submitted', 0)}
💰 Paid: {stats.get('by_status', {}).get('paid', 0)}

<b>Earnings:</b> ${stats.get('total_earnings', 0):,.2f}

<b>Commands:</b>
• /bounty_stats - Show full statistics
• /bounty_review - Review pending findings
• /bounty_scan &lt;url&gt; - Scan new repository
"""
        
        return self.send_message(message)
    
    def send_scan_complete(self, repo_name: str, findings_count: int, scan_dir: str) -> bool:
        """
        Send notification when scan completes.
        
        Args:
            repo_name: Repository name
            findings_count: Number of findings
            scan_dir: Scan directory path
            
        Returns:
            True if sent successfully
        """
        message = f"""✅ <b>Scan Complete</b>

Repository: <code>{repo_name}</code>
Findings: {findings_count}

Scan directory: <code>{scan_dir}</code>

<b>Next Steps:</b>
1. Review findings in database
2. Use /bounty_review to see pending items
3. Approve/reject each finding
"""
        
        return self.send_message(message)
    
    def send_approval_request(self, finding: Dict) -> bool:
        """
        Send detailed approval request.
        
        Args:
            finding: Finding dictionary
            
        Returns:
            True if sent successfully
        """
        severity = finding.get("severity", "Unknown")
        
        message = f"""🚨 <b>APPROVAL REQUIRED</b>

<b>Finding ID:</b> <code>{finding.get('finding_id')}</code>
<b>Severity:</b> {severity}
<b>Repository:</b> {finding.get('repo_name')}

<b>Code Snippet:</b>
<pre><code class="rust">{finding.get('code_snippet', 'No code snippet')[:800]}</code></pre>

<b>Recommendation:</b>
{finding.get('recommendation', 'No recommendation')[:500]}

<b>Reply with:</b>
• "approve" - Submit this finding to bounty platforms
• "reject" - Mark as false positive
• "more info" - Request additional details
"""
        
        # Truncate if too long
        if len(message) > 4000:
            code = finding.get('code_snippet', '')[:400]
            message = message.replace(
                finding.get('code_snippet', '')[:800],
                code + "\n<i>(truncated)</i>"
            )
        
        return self.send_message(message)


def load_finding_from_db(finding_id: str, db_path: str = None) -> Optional[Dict]:
    """Load finding from database by ID."""
    try:
        import sqlite3
        
        if not db_path:
            db_path = os.path.expanduser("~/.solana-bounty-hunter/findings.db")
        
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM findings WHERE finding_id = ?", (finding_id,))
        row = cursor.fetchone()
        conn.close()
        
        return dict(row) if row else None
        
    except Exception as e:
        print(f"Error loading from database: {e}")
        return None


def main():
    parser = argparse.ArgumentParser(description="Telegram Notifier for Bug Bounty Hunter")
    parser.add_argument("--finding", help="Path to finding JSON file")
    parser.add_argument("--finding-id", help="Finding ID from database")
    parser.add_argument("--message", help="Custom message to send")
    parser.add_argument("--summary", action="store_true", help="Send statistics summary")
    parser.add_argument("--approve-request", help="Send approval request for finding ID")
    parser.add_argument("--db", help="Database path")
    
    args = parser.parse_args()
    
    # Check environment
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("❌ Error: TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID must be set")
        print("\nSetup instructions:")
        print("1. Message @BotFather on Telegram to create a bot")
        print("2. Copy the bot token")
        print("3. Message @userinfobot to get your chat ID")
        print("4. Set environment variables:")
        print("   export TELEGRAM_BOT_TOKEN='your_token'")
        print("   export TELEGRAM_CHAT_ID='your_chat_id'")
        sys.exit(1)
    
    # Initialize notifier
    try:
        notifier = TelegramNotifier()
    except ValueError as e:
        print(f"❌ Error: {e}")
        sys.exit(1)
    
    # Send notification based on arguments
    if args.finding:
        with open(args.finding, 'r') as f:
            finding = json.load(f)
        success = notifier.send_finding(finding)
        
    elif args.finding_id:
        finding = load_finding_from_db(args.finding_id, args.db)
        if finding:
            success = notifier.send_finding(finding)
        else:
            print(f"❌ Finding {args.finding_id} not found in database")
            sys.exit(1)
            
    elif args.message:
        success = notifier.send_message(args.message)
        
    elif args.summary:
        # Load stats from database
        try:
            from findings_db import FindingsDatabase
            with FindingsDatabase(args.db) as db:
                stats = db.get_statistics()
                success = notifier.send_summary(stats)
        except Exception as e:
            print(f"❌ Error loading statistics: {e}")
            sys.exit(1)
            
    elif args.approve_request:
        finding = load_finding_from_db(args.approve_request, args.db)
        if finding:
            success = notifier.send_approval_request(finding)
        else:
            print(f"❌ Finding {args.approve_request} not found in database")
            sys.exit(1)
    else:
        # Send test message
        success = notifier.send_message(
            "🎯 <b>Solana Bug Bounty Hunter</b> is now active!\n\n"
            "You'll receive notifications when new vulnerabilities are discovered.\n\n"
            "<b>Commands:</b>\n"
            "• /bounty_scan &lt;url&gt; - Scan repository\n"
            "• /bounty_review - Review findings\n"
            "• /bounty_stats - Show statistics"
        )
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
