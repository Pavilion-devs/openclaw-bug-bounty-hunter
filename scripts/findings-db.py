#!/usr/bin/env python3
"""
Findings Database for Solana Bug Bounty Hunter

Manages SQLite database for storing and querying security findings.

Usage:
    python findings-db.py --init                    # Initialize database
    python findings-db.py --add finding.json        # Add a finding
    python findings-db.py --list --severity HIGH    # List findings
    python findings-db.py --stats                   # Show statistics
"""

import sqlite3
import json
import os
import sys
import argparse
from datetime import datetime
from typing import Dict, List, Optional
from pathlib import Path

# Database path
DEFAULT_DB_PATH = os.path.expanduser("~/.solana-bounty-hunter/findings.db")


class FindingsDatabase:
    """SQLite database for security findings."""
    
    def __init__(self, db_path: str = None):
        self.db_path = db_path or DEFAULT_DB_PATH
        self._ensure_directory()
        self.conn = None
    
    def _ensure_directory(self):
        """Ensure database directory exists."""
        dir_path = os.path.dirname(self.db_path)
        if dir_path and not os.path.exists(dir_path):
            os.makedirs(dir_path)
    
    def connect(self):
        """Connect to database."""
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        return self
    
    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()
            self.conn = None
    
    def __enter__(self):
        return self.connect()
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
    
    def init_database(self):
        """Initialize database schema."""
        cursor = self.conn.cursor()
        
        # Findings table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS findings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                finding_id TEXT UNIQUE NOT NULL,
                repo_name TEXT NOT NULL,
                repo_url TEXT NOT NULL,
                repo_owner TEXT,
                file_path TEXT,
                line_number INTEGER,
                vulnerability_type TEXT NOT NULL,
                title TEXT NOT NULL,
                description TEXT,
                severity TEXT NOT NULL CHECK(severity IN ('Critical', 'High', 'Medium', 'Low', 'Informational')),
                impact TEXT,
                recommendation TEXT,
                code_snippet TEXT,
                status TEXT DEFAULT 'pending' CHECK(status IN ('pending', 'approved', 'rejected', 'submitted', 'confirmed', 'paid')),
                confidence REAL DEFAULT 0.0,
                analyzer TEXT,
                scan_id TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                submitted_at TIMESTAMP,
                bounty_platform TEXT,
                bounty_url TEXT,
                bounty_amount REAL,
                notes TEXT
            )
        """)
        
        # Repositories table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS repositories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                repo_name TEXT UNIQUE NOT NULL,
                repo_url TEXT NOT NULL,
                owner TEXT,
                stars INTEGER,
                forks INTEGER,
                audit_priority INTEGER,
                last_scan_id TEXT,
                last_scan_date TIMESTAMP,
                total_findings INTEGER DEFAULT 0,
                status TEXT DEFAULT 'active' CHECK(status IN ('active', 'archived', 'excluded')),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Scan history table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS scan_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                scan_id TEXT UNIQUE NOT NULL,
                repo_name TEXT NOT NULL,
                scan_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                semgrep_findings INTEGER DEFAULT 0,
                cargo_vulnerabilities INTEGER DEFAULT 0,
                llm_findings INTEGER DEFAULT 0,
                files_scanned INTEGER DEFAULT 0,
                lines_scanned INTEGER DEFAULT 0,
                duration_seconds INTEGER,
                status TEXT DEFAULT 'completed' CHECK(status IN ('running', 'completed', 'failed')),
                error_message TEXT
            )
        """)
        
        # Create indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_findings_severity ON findings(severity)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_findings_status ON findings(status)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_findings_repo ON findings(repo_name)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_findings_type ON findings(vulnerability_type)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_scans_repo ON scan_history(repo_name)")
        
        self.conn.commit()
        print(f"✅ Database initialized at {self.db_path}")
    
    def add_finding(self, finding: Dict) -> int:
        """
        Add a new finding to the database.
        
        Args:
            finding: Dictionary with finding details
            
        Returns:
            ID of the inserted finding
        """
        cursor = self.conn.cursor()
        
        # Generate finding ID if not provided
        if 'finding_id' not in finding:
            finding['finding_id'] = f"FND-{datetime.now().strftime('%Y%m%d')}-{finding.get('repo_name', 'unknown')[:10]}"
        
        cursor.execute("""
            INSERT INTO findings (
                finding_id, repo_name, repo_url, repo_owner, file_path, line_number,
                vulnerability_type, title, description, severity, impact, recommendation,
                code_snippet, analyzer, scan_id, confidence, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            finding.get('finding_id'),
            finding.get('repo_name'),
            finding.get('repo_url'),
            finding.get('repo_owner'),
            finding.get('file_path'),
            finding.get('line_number'),
            finding.get('vulnerability_type'),
            finding.get('title'),
            finding.get('description'),
            finding.get('severity'),
            finding.get('impact'),
            finding.get('recommendation'),
            finding.get('code_snippet'),
            finding.get('analyzer'),
            finding.get('scan_id'),
            finding.get('confidence', 0.0),
            finding.get('created_at', datetime.now().isoformat())
        ))
        
        self.conn.commit()
        return cursor.lastrowid
    
    def update_finding_status(self, finding_id: str, status: str, notes: str = None):
        """
        Update the status of a finding.
        
        Args:
            finding_id: Unique finding ID
            status: New status (pending, approved, rejected, submitted, confirmed, paid)
            notes: Optional notes
        """
        cursor = self.conn.cursor()
        
        if status == 'submitted':
            cursor.execute("""
                UPDATE findings 
                SET status = ?, updated_at = ?, submitted_at = ?, notes = COALESCE(?, notes)
                WHERE finding_id = ?
            """, (status, datetime.now().isoformat(), datetime.now().isoformat(), notes, finding_id))
        else:
            cursor.execute("""
                UPDATE findings 
                SET status = ?, updated_at = ?, notes = COALESCE(?, notes)
                WHERE finding_id = ?
            """, (status, datetime.now().isoformat(), notes, finding_id))
        
        self.conn.commit()
    
    def get_findings(
        self, 
        severity: str = None, 
        status: str = None, 
        repo: str = None,
        limit: int = 50
    ) -> List[Dict]:
        """
        Query findings with optional filters.
        
        Args:
            severity: Filter by severity
            status: Filter by status
            repo: Filter by repository
            limit: Maximum results
            
        Returns:
            List of finding dictionaries
        """
        cursor = self.conn.cursor()
        
        query = "SELECT * FROM findings WHERE 1=1"
        params = []
        
        if severity:
            query += " AND severity = ?"
            params.append(severity)
        
        if status:
            query += " AND status = ?"
            params.append(status)
        
        if repo:
            query += " AND repo_name = ?"
            params.append(repo)
        
        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        return [dict(row) for row in rows]
    
    def get_finding_by_id(self, finding_id: str) -> Optional[Dict]:
        """Get a specific finding by ID."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM findings WHERE finding_id = ?", (finding_id,))
        row = cursor.fetchone()
        return dict(row) if row else None
    
    def get_pending_findings(self, min_severity: str = "High") -> List[Dict]:
        """
        Get findings awaiting human review.
        
        Args:
            min_severity: Minimum severity level
            
        Returns:
            List of pending findings
        """
        severity_order = ["Critical", "High", "Medium", "Low", "Informational"]
        min_index = severity_order.index(min_severity) if min_severity in severity_order else 0
        allowed_severities = severity_order[:min_index + 1]
        
        placeholders = ','.join('?' * len(allowed_severities))
        
        cursor = self.conn.cursor()
        cursor.execute(f"""
            SELECT * FROM findings 
            WHERE status = 'pending' AND severity IN ({placeholders})
            ORDER BY 
                CASE severity
                    WHEN 'Critical' THEN 1
                    WHEN 'High' THEN 2
                    WHEN 'Medium' THEN 3
                    WHEN 'Low' THEN 4
                    ELSE 5
                END,
                confidence DESC
        """, allowed_severities)
        
        return [dict(row) for row in cursor.fetchall()]
    
    def get_statistics(self) -> Dict:
        """Get database statistics."""
        cursor = self.conn.cursor()
        
        stats = {}
        
        # Total findings
        cursor.execute("SELECT COUNT(*) FROM findings")
        stats['total_findings'] = cursor.fetchone()[0]
        
        # By severity
        cursor.execute("""
            SELECT severity, COUNT(*) as count 
            FROM findings 
            GROUP BY severity
        """)
        stats['by_severity'] = {row[0]: row[1] for row in cursor.fetchall()}
        
        # By status
        cursor.execute("""
            SELECT status, COUNT(*) as count 
            FROM findings 
            GROUP BY status
        """)
        stats['by_status'] = {row[0]: row[1] for row in cursor.fetchall()}
        
        # By repository
        cursor.execute("""
            SELECT repo_name, COUNT(*) as count 
            FROM findings 
            GROUP BY repo_name
            ORDER BY count DESC
            LIMIT 10
        """)
        stats['by_repo'] = {row[0]: row[1] for row in cursor.fetchall()}
        
        # Recent activity
        cursor.execute("""
            SELECT COUNT(*) FROM findings 
            WHERE created_at > datetime('now', '-7 days')
        """)
        stats['recent_findings'] = cursor.fetchone()[0]
        
        # Bounty tracking
        cursor.execute("""
            SELECT COUNT(*) FROM findings 
            WHERE status IN ('submitted', 'confirmed', 'paid')
        """)
        stats['submissions'] = cursor.fetchone()[0]
        
        cursor.execute("""
            SELECT COALESCE(SUM(bounty_amount), 0) FROM findings 
            WHERE status = 'paid'
        """)
        stats['total_earnings'] = cursor.fetchone()[0]
        
        return stats
    
    def add_repository(self, repo_info: Dict):
        """Add or update repository information."""
        cursor = self.conn.cursor()
        
        cursor.execute("""
            INSERT OR REPLACE INTO repositories 
            (repo_name, repo_url, owner, stars, forks, audit_priority, last_scan_id, last_scan_date)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            repo_info.get('repo_name'),
            repo_info.get('repo_url'),
            repo_info.get('owner'),
            repo_info.get('stars'),
            repo_info.get('forks'),
            repo_info.get('audit_priority'),
            repo_info.get('last_scan_id'),
            repo_info.get('last_scan_date')
        ))
        
        self.conn.commit()
    
    def add_scan_history(self, scan_info: Dict):
        """Add scan history entry."""
        cursor = self.conn.cursor()
        
        cursor.execute("""
            INSERT INTO scan_history 
            (scan_id, repo_name, scan_date, semgrep_findings, cargo_vulnerabilities,
             llm_findings, files_scanned, lines_scanned, duration_seconds, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            scan_info.get('scan_id'),
            scan_info.get('repo_name'),
            scan_info.get('scan_date'),
            scan_info.get('semgrep_findings', 0),
            scan_info.get('cargo_vulnerabilities', 0),
            scan_info.get('llm_findings', 0),
            scan_info.get('files_scanned', 0),
            scan_info.get('lines_scanned', 0),
            scan_info.get('duration_seconds'),
            scan_info.get('status', 'completed')
        ))
        
        self.conn.commit()


def print_findings(findings: List[Dict]):
    """Pretty print findings."""
    if not findings:
        print("No findings found.")
        return
    
    print(f"\nFound {len(findings)} findings:\n")
    print("-" * 80)
    
    for f in findings:
        severity_emoji = {
            'Critical': '🔴',
            'High': '🟠',
            'Medium': '🟡',
            'Low': '🟢',
            'Informational': '⚪'
        }.get(f.get('severity'), '⚪')
        
        print(f"{severity_emoji} {f.get('severity')} | {f.get('finding_id')}")
        print(f"   Repository: {f.get('repo_name')}")
        print(f"   Type: {f.get('vulnerability_type')}")
        print(f"   Title: {f.get('title')}")
        print(f"   File: {f.get('file_path')}:{f.get('line_number')}")
        print(f"   Status: {f.get('status')}")
        print(f"   Created: {f.get('created_at')}")
        print("-" * 80)


def print_stats(stats: Dict):
    """Pretty print statistics."""
    print("\n📊 Database Statistics")
    print("=" * 50)
    print(f"Total Findings: {stats.get('total_findings', 0)}")
    print(f"Recent (7 days): {stats.get('recent_findings', 0)}")
    print(f"Submissions: {stats.get('submissions', 0)}")
    print(f"Total Earnings: ${stats.get('total_earnings', 0):,.2f}")
    
    print("\nBy Severity:")
    for severity, count in stats.get('by_severity', {}).items():
        print(f"  {severity}: {count}")
    
    print("\nBy Status:")
    for status, count in stats.get('by_status', {}).items():
        print(f"  {status}: {count}")
    
    print("\nTop Repositories:")
    for repo, count in stats.get('by_repo', {}).items():
        print(f"  {repo}: {count} findings")


def main():
    parser = argparse.ArgumentParser(description="Findings Database Manager")
    parser.add_argument("--db", help="Database path", default=DEFAULT_DB_PATH)
    parser.add_argument("--init", action="store_true", help="Initialize database")
    parser.add_argument("--add", help="Add finding from JSON file")
    parser.add_argument("--list", action="store_true", help="List findings")
    parser.add_argument("--pending", action="store_true", help="Show pending findings")
    parser.add_argument("--severity", help="Filter by severity")
    parser.add_argument("--status", help="Filter by status")
    parser.add_argument("--repo", help="Filter by repository")
    parser.add_argument("--stats", action="store_true", help="Show statistics")
    parser.add_argument("--update-status", help="Update finding status")
    parser.add_argument("--finding-id", help="Finding ID to update")
    parser.add_argument("--notes", help="Notes for status update")
    parser.add_argument("--limit", type=int, default=50, help="Limit results")
    
    args = parser.parse_args()
    
    db = FindingsDatabase(args.db)
    
    if args.init:
        with db:
            db.init_database()
    
    elif args.add:
        with open(args.add, 'r') as f:
            finding = json.load(f)
        with db:
            finding_id = db.add_finding(finding)
            print(f"✅ Added finding with ID: {finding_id}")
    
    elif args.stats:
        with db:
            stats = db.get_statistics()
            print_stats(stats)
    
    elif args.pending:
        with db:
            findings = db.get_pending_findings()
            print_findings(findings)
    
    elif args.list:
        with db:
            findings = db.get_findings(
                severity=args.severity,
                status=args.status,
                repo=args.repo,
                limit=args.limit
            )
            print_findings(findings)
    
    elif args.update_status and args.finding_id:
        with db:
            db.update_finding_status(args.finding_id, args.update_status, args.notes)
            print(f"✅ Updated {args.finding_id} to status: {args.update_status}")
    
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
