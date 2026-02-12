#!/bin/bash
#
# Clone and Scan Script for Solana Bug Bounty Hunter
#
# Clones a repository and runs security analyzers on it.
#
# Usage:
#   ./clone-and-scan.sh <repo_url> [output_dir]
#
# Example:
#   ./clone-and-scan.sh https://github.com/user/repo.git ./scans/repo_123

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Arguments
REPO_URL="$1"
OUTPUT_DIR="${2:-./scan_results}"

# Validate arguments
if [ -z "$REPO_URL" ]; then
    echo -e "${RED}Error: Repository URL required${NC}"
    echo "Usage: $0 <repo_url> [output_dir]"
    exit 1
fi

# Extract repo name from URL
REPO_NAME=$(basename "$REPO_URL" .git)
SCAN_ID="${REPO_NAME}_$(date +%Y%m%d_%H%M%S)"
SCAN_DIR="$OUTPUT_DIR/$SCAN_ID"
REPO_DIR="$SCAN_DIR/repo"

echo -e "${BLUE}🔍 Solana Bug Bounty Hunter - Scanner${NC}"
echo "=================================="
echo ""

# Create scan directory
mkdir -p "$SCAN_DIR"
echo -e "${BLUE}📁 Scan directory: $SCAN_DIR${NC}"

# Clone repository
echo ""
echo -e "${YELLOW}📥 Cloning repository...${NC}"
echo "   URL: $REPO_URL"
echo "   Name: $REPO_NAME"

if git clone --depth 1 "$REPO_URL" "$REPO_DIR" 2>&1 | tee "$SCAN_DIR/clone.log"; then
    echo -e "${GREEN}✅ Repository cloned successfully${NC}"
else
    echo -e "${RED}❌ Failed to clone repository${NC}"
    exit 1
fi

# Get repo info
echo ""
echo -e "${YELLOW}📊 Repository Information:${NC}"
cd "$REPO_DIR"
git log --oneline -1 > "$SCAN_DIR/repo_info.txt" 2>/dev/null || echo "No commits" > "$SCAN_DIR/repo_info.txt"
echo "   Latest commit: $(head -1 "$SCAN_DIR/repo_info.txt")"
echo "   Files: $(find . -type f -name "*.rs" | wc -l) Rust files"
echo "   Size: $(du -sh . | cut -f1)"
cd - > /dev/null

# Run analyzers
echo ""
echo -e "${BLUE}🔎 Running Security Analyzers${NC}"
echo "=================================="

# 1. Semgrep Analysis
echo ""
echo -e "${YELLOW}⚡ Running Semgrep...${NC}"

SEMGREP_CONFIG="$(dirname "$0")/../analyzers/solana-patterns.yaml"

if [ -f "$SEMGREP_CONFIG" ]; then
    if semgrep \
        --config="$SEMGREP_CONFIG" \
        --json \
        --output="$SCAN_DIR/semgrep_results.json" \
        "$REPO_DIR" 2>&1 | tee "$SCAN_DIR/semgrep.log"; then
        echo -e "${GREEN}✅ Semgrep analysis complete${NC}"
        
        # Count findings
        if [ -f "$SCAN_DIR/semgrep_results.json" ]; then
            FINDINGS=$(cat "$SCAN_DIR/semgrep_results.json" | python3 -c "import sys,json; print(len(json.load(sys.stdin).get('results', [])))" 2>/dev/null || echo "0")
            echo "   Found: $FINDINGS potential issues"
        fi
    else
        echo -e "${YELLOW}⚠️  Semgrep completed with warnings${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  Semgrep config not found at $SEMGREP_CONFIG${NC}"
    echo "   Skipping semgrep analysis"
fi

# 2. Cargo Audit (if Cargo.toml exists)
echo ""
echo -e "${YELLOW}📦 Running Cargo Audit...${NC}"

if [ -f "$REPO_DIR/Cargo.toml" ]; then
    cd "$REPO_DIR"
    
    if cargo audit --json 2>/dev/null > "$SCAN_DIR/cargo_audit_results.json"; then
        echo -e "${GREEN}✅ Cargo audit complete${NC}"
        
        # Count vulnerabilities
        if [ -f "$SCAN_DIR/cargo_audit_results.json" ]; then
            VULNS=$(cat "$SCAN_DIR/cargo_audit_results.json" | python3 -c "import sys,json; print(len(json.load(sys.stdin).get('vulnerabilities', {}).get('list', [])))" 2>/dev/null || echo "0")
            echo "   Found: $VULNS dependency vulnerabilities"
        fi
    else
        echo -e "${YELLOW}⚠️  No Cargo.lock found or audit failed${NC}"
        echo "   {}" > "$SCAN_DIR/cargo_audit_results.json"
    fi
    
    cd - > /dev/null
else
    echo -e "${YELLOW}⚠️  No Cargo.toml found${NC}"
    echo "   Skipping cargo audit"
fi

# 3. File Statistics
echo ""
echo -e "${YELLOW}📈 Analyzing Code Structure...${NC}"

# Count different file types
find "$REPO_DIR" -type f -name "*.rs" | wc -l > "$SCAN_DIR/rust_file_count.txt"
find "$REPO_DIR" -type f -name "Cargo.toml" | wc -l > "$SCAN_DIR/crate_count.txt"

# Find entry points (lib.rs, main.rs)
find "$REPO_DIR" -type f \( -name "lib.rs" -o -name "main.rs" \) > "$SCAN_DIR/entry_points.txt"

# Count total lines of code
find "$REPO_DIR" -type f -name "*.rs" -exec wc -l {} + | tail -1 | awk '{print $1}' > "$SCAN_DIR/total_lines.txt" 2>/dev/null || echo "0" > "$SCAN_DIR/total_lines.txt"

echo "   Rust files: $(cat "$SCAN_DIR/rust_file_count.txt")"
echo "   Crates: $(cat "$SCAN_DIR/crate_count.txt")"
echo "   Total lines: $(cat "$SCAN_DIR/total_lines.txt")"

# 4. Extract flagged files for LLM review
echo ""
echo -e "${YELLOW}📝 Preparing files for LLM review...${NC}"

# Get files with semgrep findings
if [ -f "$SCAN_DIR/semgrep_results.json" ]; then
    python3 -c "
import json, sys

scan_dir = sys.argv[1]
try:
    with open(scan_dir + '/semgrep_results.json', 'r') as f:
        data = json.load(f)
    results = data.get('results', [])
    
    # Extract unique file paths
    files = set()
    for result in results:
        files.add(result.get('path', ''))
    
    # Save to file
    with open(scan_dir + '/flagged_files.txt', 'w') as f:
        for file_path in sorted(files):
            if file_path:
                f.write(file_path + '\n')
    
    print(f'   Flagged {len(files)} files for review')
except Exception as e:
    print(f'   Error: {e}')
    open(scan_dir + '/flagged_files.txt', 'w').close()
" "$SCAN_DIR"
fi

# Create summary
echo ""
echo -e "${BLUE}📋 Scan Summary${NC}"
echo "=================================="
echo "Repository: $REPO_NAME"
echo "Scan ID: $SCAN_ID"
echo "Location: $SCAN_DIR"
echo ""

# Count results
SEMGREP_COUNT=0
if [ -f "$SCAN_DIR/semgrep_results.json" ]; then
    SEMGREP_COUNT=$(cat "$SCAN_DIR/semgrep_results.json" | python3 -c "import sys,json; print(len(json.load(sys.stdin).get('results', [])))" 2>/dev/null || echo "0")
fi

CARGO_COUNT=0
if [ -f "$SCAN_DIR/cargo_audit_results.json" ]; then
    CARGO_COUNT=$(cat "$SCAN_DIR/cargo_audit_results.json" | python3 -c "import sys,json; print(len(json.load(sys.stdin).get('vulnerabilities', {}).get('list', [])))" 2>/dev/null || echo "0")
fi

echo "Results:"
echo "  - Semgrep findings: $SEMGREP_COUNT"
echo "  - Dependency vulns: $CARGO_COUNT"
echo "  - Files flagged: $(wc -l < "$SCAN_DIR/flagged_files.txt" 2>/dev/null || echo 0)"

# Create scan metadata
cat > "$SCAN_DIR/scan_metadata.json" << EOF
{
  "scan_id": "$SCAN_ID",
  "repo_name": "$REPO_NAME",
  "repo_url": "$REPO_URL",
  "scan_date": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "scan_dir": "$SCAN_DIR",
  "repo_dir": "$REPO_DIR",
  "results": {
    "semgrep_findings": $SEMGREP_COUNT,
    "cargo_vulnerabilities": $CARGO_COUNT,
    "rust_files": $(cat "$SCAN_DIR/rust_file_count.txt" 2>/dev/null || echo 0),
    "total_lines": $(cat "$SCAN_DIR/total_lines.txt" 2>/dev/null || echo 0)
  }
}
EOF

# 5. Insert semgrep findings into database
echo ""
echo -e "${YELLOW}💾 Inserting findings into database...${NC}"

SCRIPT_BASE="$(dirname "$0")"
if [ -f "$SCAN_DIR/semgrep_results.json" ] && [ "$SEMGREP_COUNT" -gt 0 ]; then
    python3 -c "
import json, sys, os, hashlib
from datetime import datetime

scan_dir = sys.argv[1]
repo_name = sys.argv[2]
repo_url = sys.argv[3]
scan_id = sys.argv[4]
db_script = sys.argv[5]

with open(os.path.join(scan_dir, 'semgrep_results.json'), 'r') as f:
    data = json.load(f)

results = data.get('results', [])
inserted = 0

for r in results:
    rule_id = r.get('check_id', 'unknown').split('.')[-1]
    file_path = r.get('path', 'unknown')
    line = r.get('start', {}).get('line', 0)
    message = r.get('extra', {}).get('message', r.get('message', ''))
    severity_map = {'ERROR': 'High', 'WARNING': 'Medium', 'INFO': 'Low'}
    severity = severity_map.get(r.get('extra', {}).get('severity', 'WARNING'), 'Medium')
    code = r.get('extra', {}).get('lines', '')
    confidence = r.get('extra', {}).get('metadata', {}).get('confidence', 'MEDIUM')
    conf_score = {'HIGH': 80, 'MEDIUM': 50, 'LOW': 30}.get(confidence, 50)

    uid = hashlib.md5(f'{repo_name}:{file_path}:{line}:{rule_id}'.encode()).hexdigest()[:12]
    finding_id = f'FND-{scan_id[:8]}-{uid}'

    finding = {
        'finding_id': finding_id,
        'repo_name': repo_name,
        'repo_url': repo_url,
        'file_path': file_path,
        'line_number': line,
        'vulnerability_type': rule_id,
        'title': message[:200],
        'description': message,
        'severity': severity,
        'impact': 'Requires LLM triage — see semgrep rule for details.',
        'recommendation': 'Pending LLM analysis.',
        'code_snippet': code[:500] if code else '',
        'analyzer': 'semgrep',
        'scan_id': scan_id,
        'confidence': conf_score,
    }

    finding_path = os.path.join(scan_dir, f'finding_{inserted}.json')
    with open(finding_path, 'w') as f:
        json.dump(finding, f, indent=2)

    ret = os.system(f'python3 {db_script} --add {finding_path} 2>/dev/null')
    if ret == 0:
        inserted += 1

print(f'   Inserted {inserted}/{len(results)} findings into database')
" "$SCAN_DIR" "$REPO_NAME" "$REPO_URL" "$SCAN_ID" "$SCRIPT_BASE/findings-db.py"
else
    echo "   No semgrep findings to insert."
fi

# Record scan in history
python3 -c "
import sys, os
sys.path.insert(0, os.path.dirname(sys.argv[1]))
from importlib.util import spec_from_file_location, module_from_spec
spec = spec_from_file_location('findings_db', sys.argv[1])
mod = module_from_spec(spec)
spec.loader.exec_module(mod)

db = mod.FindingsDatabase()
with db:
    db.add_scan_history({
        'scan_id': sys.argv[2],
        'repo_name': sys.argv[3],
        'semgrep_findings': int(sys.argv[4]),
        'cargo_vulnerabilities': int(sys.argv[5]),
        'files_scanned': int(sys.argv[6]),
        'lines_scanned': int(sys.argv[7]),
        'status': 'completed'
    })
    print('   Scan history recorded.')
" "$SCRIPT_BASE/findings-db.py" "$SCAN_ID" "$REPO_NAME" "$SEMGREP_COUNT" "$CARGO_COUNT" \
  "$(cat "$SCAN_DIR/rust_file_count.txt" 2>/dev/null || echo 0)" \
  "$(cat "$SCAN_DIR/total_lines.txt" 2>/dev/null || echo 0)"

echo ""
echo -e "${GREEN}✅ Scan complete!${NC}"
echo ""
echo "Next steps:"
echo "  1. Review flagged files: $SCAN_DIR/flagged_files.txt"
echo "  2. Run LLM analysis on findings"
echo "  3. Check results: $SCAN_DIR/semgrep_results.json"
echo "  4. Check database: python3 $SCRIPT_BASE/findings-db.py --stats"

# Output scan ID for automation
echo ""
echo "SCAN_ID:$SCAN_ID"
