#!/usr/bin/env python3
"""
GitHub Monitor for Solana Bug Bounty Hunter

Discovers recently updated Solana repositories on GitHub
and prioritizes them for security auditing.

Usage:
    python github-monitor.py --min-stars 50 --max-repos 10
    python github-monitor.py --since 2026-02-01
"""

import requests
import os
import sys
import json
import argparse
from datetime import datetime, timedelta
from typing import List, Dict, Optional

# GitHub API configuration
GITHUB_API_URL = "https://api.github.com"
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")

# Search queries for finding Solana repositories
SOLANA_QUERIES = [
    "language:rust solana program stars:>50",
    "language:rust solana smart contract stars:>50",
    "language:rust solana anchor stars:>50",
    "topic:solana language:rust stars:>50",
    "spl-token language:rust stars:>50",
]

# Repositories to exclude (already audited or not relevant)
EXCLUDED_REPOS = [
    "solana-labs/solana",  # Core repo, too large
    "solana-labs/solana-program-library",  # Already audited
]


class GitHubMonitor:
    """Monitors GitHub for Solana repositories to audit."""
    
    def __init__(self, token: str = None):
        self.token = token or GITHUB_TOKEN
        self.headers = {
            "Accept": "application/vnd.github.v3+json",
        }
        if self.token:
            self.headers["Authorization"] = f"token {self.token}"
    
    def search_repositories(
        self, 
        query: str, 
        sort: str = "updated",
        order: str = "desc",
        per_page: int = 30
    ) -> List[Dict]:
        """
        Search GitHub repositories.
        
        Args:
            query: Search query string
            sort: Sort field (stars, forks, updated)
            order: Sort order (asc, desc)
            per_page: Results per page (max 100)
            
        Returns:
            List of repository dictionaries
        """
        url = f"{GITHUB_API_URL}/search/repositories"
        params = {
            "q": query,
            "sort": sort,
            "order": order,
            "per_page": per_page,
        }
        
        try:
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            data = response.json()
            return data.get("items", [])
        except requests.exceptions.RequestException as e:
            print(f"Error searching repositories: {e}", file=sys.stderr)
            return []
    
    def get_repo_details(self, owner: str, repo: str) -> Optional[Dict]:
        """
        Get detailed information about a specific repository.
        
        Args:
            owner: Repository owner
            repo: Repository name
            
        Returns:
            Repository details dictionary or None
        """
        url = f"{GITHUB_API_URL}/repos/{owner}/{repo}"
        
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error fetching repo details: {e}", file=sys.stderr)
            return None
    
    def get_recent_commits(self, owner: str, repo: str, since: str = None) -> List[Dict]:
        """
        Get recent commits to assess repository activity.
        
        Args:
            owner: Repository owner
            repo: Repository name
            since: ISO 8601 timestamp
            
        Returns:
            List of commit dictionaries
        """
        url = f"{GITHUB_API_URL}/repos/{owner}/{repo}/commits"
        params = {"per_page": 10}
        if since:
            params["since"] = since
        
        try:
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"Error fetching commits: {e}", file=sys.stderr)
            return []
    
    def is_solana_project(self, repo: Dict) -> bool:
        """
        Check if repository is likely a Solana project.
        
        Args:
            repo: Repository dictionary
            
        Returns:
            True if Solana project, False otherwise
        """
        # Check description
        description = (repo.get("description") or "").lower()
        solana_keywords = ["solana", "spl", "anchor", "sealevel"]
        if any(kw in description for kw in solana_keywords):
            return True
        
        # Check topics
        topics = [t.lower() for t in repo.get("topics", [])]
        if any(kw in topics for kw in solana_keywords):
            return True
        
        # Check language
        if repo.get("language") == "Rust":
            return True
        
        return False
    
    def should_audit(self, repo: Dict, min_stars: int = 50) -> bool:
        """
        Determine if repository should be audited.
        
        Args:
            repo: Repository dictionary
            min_stars: Minimum star count
            
        Returns:
            True if should audit, False otherwise
        """
        # Check minimum stars
        if repo.get("stargazers_count", 0) < min_stars:
            return False
        
        # Check if excluded
        full_name = repo.get("full_name", "")
        if full_name in EXCLUDED_REPOS:
            return False
        
        # Check if Solana project
        if not self.is_solana_project(repo):
            return False
        
        # Check if archived
        if repo.get("archived", False):
            return False
        
        return True
    
    def discover_repositories(
        self, 
        max_repos: int = 10,
        min_stars: int = 50,
        days_since_update: int = 7
    ) -> List[Dict]:
        """
        Discover Solana repositories to audit.
        
        Args:
            max_repos: Maximum repositories to return
            min_stars: Minimum star count
            days_since_update: Only repos updated in last N days
            
        Returns:
            List of repository dictionaries to audit
        """
        discovered = []
        seen = set()
        
        # Calculate date threshold
        since_date = (datetime.now() - timedelta(days=days_since_update)).strftime("%Y-%m-%d")
        
        print(f"🔍 Searching for Solana repositories (updated since {since_date})...")
        
        for query in SOLANA_QUERIES:
            print(f"  Query: {query}")
            
            # Add date filter to query
            filtered_query = f"{query} pushed:>{since_date}"
            
            repos = self.search_repositories(filtered_query, per_page=30)
            
            for repo in repos:
                repo_id = repo.get("id")
                if repo_id in seen:
                    continue
                
                seen.add(repo_id)
                
                if self.should_audit(repo, min_stars):
                    discovered.append({
                        "id": repo_id,
                        "name": repo.get("name"),
                        "full_name": repo.get("full_name"),
                        "owner": repo.get("owner", {}).get("login"),
                        "url": repo.get("html_url"),
                        "clone_url": repo.get("clone_url"),
                        "stars": repo.get("stargazers_count"),
                        "forks": repo.get("forks_count"),
                        "language": repo.get("language"),
                        "description": repo.get("description"),
                        "topics": repo.get("topics", []),
                        "updated_at": repo.get("updated_at"),
                        "created_at": repo.get("created_at"),
                        "audit_priority": self._calculate_priority(repo),
                    })
                    
                    if len(discovered) >= max_repos:
                        break
            
            if len(discovered) >= max_repos:
                break
        
        # Sort by priority (highest first)
        discovered.sort(key=lambda x: x["audit_priority"], reverse=True)
        
        return discovered[:max_repos]
    
    def _calculate_priority(self, repo: Dict) -> int:
        """
        Calculate audit priority score (0-100).
        
        Higher score = more important to audit
        
        Args:
            repo: Repository dictionary
            
        Returns:
            Priority score (0-100)
        """
        score = 0
        
        # Stars (up to 40 points)
        stars = repo.get("stargazers_count", 0)
        score += min(stars / 100, 40)
        
        # Recent activity (up to 30 points)
        updated_at = repo.get("updated_at", "")
        if updated_at:
            try:
                updated = datetime.fromisoformat(updated_at.replace("Z", "+00:00"))
                days_since = (datetime.now(updated.tzinfo) - updated).days
                if days_since < 7:
                    score += 30
                elif days_since < 30:
                    score += 20
                elif days_since < 90:
                    score += 10
            except:
                pass
        
        # Forks indicate usage (up to 20 points)
        forks = repo.get("forks_count", 0)
        score += min(forks / 20, 20)
        
        # Solana-specific keywords (up to 10 points)
        description = (repo.get("description") or "").lower()
        keywords = ["token", "defi", "lending", "dex", "amm", "staking", "governance"]
        for kw in keywords:
            if kw in description:
                score += 2
        
        return int(score)
    
    def save_discovered_repos(self, repos: List[Dict], output_file: str = "discovered_repos.json"):
        """
        Save discovered repositories to JSON file.
        
        Args:
            repos: List of repository dictionaries
            output_file: Output JSON file path
        """
        with open(output_file, "w") as f:
            json.dump(repos, f, indent=2)
        
        print(f"💾 Saved {len(repos)} repositories to {output_file}")


def main():
    parser = argparse.ArgumentParser(
        description="Discover Solana repositories for security auditing"
    )
    parser.add_argument(
        "--max-repos",
        type=int,
        default=10,
        help="Maximum repositories to discover (default: 10)"
    )
    parser.add_argument(
        "--min-stars",
        type=int,
        default=50,
        help="Minimum star count (default: 50)"
    )
    parser.add_argument(
        "--days-since-update",
        type=int,
        default=7,
        help="Only repos updated in last N days (default: 7)"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="discovered_repos.json",
        help="Output JSON file (default: discovered_repos.json)"
    )
    
    args = parser.parse_args()
    
    # Check for GitHub token
    if not GITHUB_TOKEN:
        print("⚠️  Warning: GITHUB_TOKEN not set. API rate limits will be restricted.")
        print("   Set your token: export GITHUB_TOKEN='your_token_here'")
    
    # Initialize monitor
    monitor = GitHubMonitor()
    
    # Discover repositories
    repos = monitor.discover_repositories(
        max_repos=args.max_repos,
        min_stars=args.min_stars,
        days_since_update=args.days_since_update
    )
    
    if not repos:
        print("❌ No repositories found matching criteria")
        sys.exit(1)
    
    # Display results
    print(f"\n✅ Discovered {len(repos)} repositories to audit:\n")
    for i, repo in enumerate(repos, 1):
        print(f"{i}. {repo['full_name']}")
        print(f"   ⭐ {repo['stars']} stars | 🍴 {repo['forks']} forks | Priority: {repo['audit_priority']}/100")
        print(f"   🔗 {repo['url']}")
        if repo['description']:
            print(f"   📝 {repo['description'][:100]}...")
        print()
    
    # Save to file
    monitor.save_discovered_repos(repos, args.output)
    
    print(f"🎯 Ready to audit! Use: /bounty_scan <repo_url>")


if __name__ == "__main__":
    main()
