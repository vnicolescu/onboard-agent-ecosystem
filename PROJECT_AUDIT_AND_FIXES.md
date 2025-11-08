# Project Onboard Skill - Critical Audit & Fix Tracking

**Date**: 2025-11-08  
**Status**: Pre-Implementation Audit  
**Priority**: Address Critical Issues Before Any Testing

---

## 📋 TABLE OF CONTENTS

1. [Critical Issues (Must Fix)](#critical-issues)
2. [Major Issues (High Priority)](#major-issues)
3. [Minor Issues (Can Defer)](#minor-issues)
4. [Architectural Decisions Required](#architectural-decisions)
5. [Implementation Checklist](#implementation-checklist)
6. [Testing Strategy](#testing-strategy)

---

## 🔴 CRITICAL ISSUES (Must Fix)

### 1. Concurrency Control - File System Race Conditions

**Files Affected**: `create_job_board.py`, `setup_communication.py`, `audit_logger.py`

**Problem**: Multiple agents reading/writing same files simultaneously will cause:
- Task assignment conflicts (two agents claim same task)
- Message corruption
- Audit log corruption
- Job board data loss

**Current Code (BROKEN)**:
```python
# create_job_board.py - Line ~120
def assign_task(self, task_id: str, agent_id: str):
    board = self._load_board()  # ❌ Race condition here
    task = board["tasks"][task_id]
    task["assigned_to"] = agent_id
    self._save_board(board)  # ❌ Another agent might write between load and save
```

**Solutions** (Choose One):

- [ ] **Option A: File Locking** (Simplest, filesystem-based)
```python
import fcntl  # Unix
import time

def _load_board_locked(self):
    with open(self.board_path, 'r+') as f:
        fcntl.flock(f.fileno(), fcntl.LOCK_EX)  # Exclusive lock
        board = json.load(f)
        # Keep lock until save completes
        return board, f

def assign_task(self, task_id: str, agent_id: str):
    board, f = self._load_board_locked()
    # Check if already assigned
    if board["tasks"][task_id]["assigned_to"]:
        fcntl.flock(f.fileno(), fcntl.LOCK_UN)
        f.close()
        return {"error": "Task already assigned"}
    
    board["tasks"][task_id]["assigned_to"] = agent_id
    f.seek(0)
    json.dump(board, f, indent=2)
    f.truncate()
    fcntl.flock(f.fileno(), fcntl.LOCK_UN)
    f.close()
```

- [ ] **Option B: SQLite Migration** (Most robust)
```python
# Replace job-board.json with job-board.db
# Use ACID transactions for all operations
import sqlite3

def assign_task(self, task_id: str, agent_id: str):
    conn = sqlite3.connect(self.db_path)
    cursor = conn.cursor()
    
    # Atomic check-and-set
    cursor.execute("""
        UPDATE tasks 
        SET assigned_to = ?, status = 'assigned'
        WHERE id = ? AND assigned_to IS NULL
    """, (agent_id, task_id))
    
    if cursor.rowcount == 0:
        conn.close()
        return {"error": "Task already assigned"}
    
    conn.commit()
    conn.close()
```

- [ ] **Option C: Optimistic Locking** (Lightweight)
```python
# Add version field to job board
{
  "version": 47,  # Increments on every write
  "tasks": {...}
}

def assign_task(self, task_id: str, agent_id: str):
    board = self._load_board()
    original_version = board["version"]
    
    # Make changes
    board["tasks"][task_id]["assigned_to"] = agent_id
    board["version"] += 1
    
    # Try to save with version check
    try:
        self._save_board_if_version_matches(board, original_version)
    except VersionConflictError:
        # Retry or fail
        return {"error": "Conflict, please retry"}
```

**Action Items**:
- [ ] Decide on concurrency strategy (A/B/C)
- [ ] Implement file locking in `create_job_board.py`
- [ ] Implement file locking in `setup_communication.py` for message writes
- [ ] Implement atomic writes in `audit_logger.py`
- [ ] Add retry logic for concurrent access failures
- [ ] Test with 3+ agents attempting simultaneous task claims

---

### 2. Communication System Protocol Mismatch

**Files Affected**: `setup_communication.py`, all agent `.md` files

**Problem**: Agent templates expect structured JSON protocol:
```json
{
  "requesting_agent": "frontend-dev-01",
  "request_type": "get_context",
  "payload": {"query": "..."}
}
```

But `setup_communication.py` only handles plain text messages:
```python
def send_message(self, from_agent: str, to: str, message: str, ...):
    # Takes string, not structured data
```

**Impact**: Agents can't actually communicate as designed.

**Solutions**:

- [ ] **Option A: Implement JSON Protocol Handler**
```python
def send_structured_message(self, from_agent: str, to: str, message_data: dict, priority='normal'):
    """Send structured data that can be parsed by recipient."""
    message_id = str(uuid.uuid4())
    
    msg = {
        "id": message_id,
        "timestamp": datetime.now().isoformat(),
        "from": from_agent,
        "to": to,
        "type": message_data.get("request_type", "info"),
        "payload": message_data.get("payload"),
        "priority": priority
    }
    
    # Save as JSON
    file_path = self._get_message_path(to, priority)
    with open(file_path, 'w') as f:
        json.dump(msg, f, indent=2)
    
    # Index in DB
    self._index_message(msg)
    
    return message_id

def get_structured_messages(self, agent_id: str, unread_only=False):
    """Return messages as parsed JSON objects."""
    messages = self.get_messages(agent_id, unread_only)
    
    for msg in messages:
        try:
            with open(msg['file_path']) as f:
                msg['parsed'] = json.load(f)
        except:
            msg['parsed'] = None
    
    return messages
```

- [ ] **Option B: Simplify Agent Expectations**
```markdown
# In agent templates, replace JSON protocol with:

**Querying Context Manager:**
Send message to context-manager with text:
"Context request: Frontend development context needed - current UI architecture, component ecosystem, design language."

Context manager will respond with relevant information.
```

**Action Items**:
- [ ] Choose protocol approach (A or B)
- [ ] Update `setup_communication.py` with structured message support
- [ ] Update all agent templates with correct protocol
- [ ] Create message schema validation
- [ ] Document protocol in `resources/communication_protocols.md`

---

### 3. Voting System - No Implementation

**Files Affected**: `voting-protocols.md`, `setup_communication.py`

**Problem**: Detailed voting rules exist, but no way to:
- Initiate a vote
- Notify eligible voters
- Collect votes
- Tally results
- Broadcast outcome

**Required Implementation**:

```python
# Add to setup_communication.py

class VotingSystem:
    def __init__(self, comm_system, audit_logger):
        self.comm = comm_system
        self.audit = audit_logger
        self.votes_dir = Path('.claude/votes')
        self.votes_dir.mkdir(parents=True, exist_ok=True)
    
    def initiate_vote(self, proposer_agent: str, topic: str, 
                     options: list, mechanism: str = 'simple_majority',
                     eligible_voters: list = None, timeout_hours: int = 24):
        """Start a new vote."""
        vote_id = f"vote-{uuid.uuid4().hex[:8]}"
        
        vote_data = {
            "vote_id": vote_id,
            "topic": topic,
            "options": options,
            "mechanism": mechanism,
            "proposed_by": proposer_agent,
            "proposed_at": datetime.now().isoformat(),
            "deadline": (datetime.now() + timedelta(hours=timeout_hours)).isoformat(),
            "eligible_voters": eligible_voters or self._get_all_agents(),
            "votes_cast": {},
            "status": "open"
        }
        
        # Save vote record
        vote_file = self.votes_dir / f"{vote_id}.json"
        with open(vote_file, 'w') as f:
            json.dump(vote_data, f, indent=2)
        
        # Broadcast to eligible voters
        for voter in vote_data["eligible_voters"]:
            self.comm.send_message(
                from_agent="voting-system",
                to=voter,
                message=f"Vote initiated: {topic}. Options: {', '.join(options)}. Vote ID: {vote_id}",
                priority="urgent"
            )
        
        # Log to audit trail
        self.audit.log("vote_initiated", proposer_agent, f"Vote {vote_id}: {topic}")
        
        return vote_id
    
    def cast_vote(self, agent_id: str, vote_id: str, choice: str, reasoning: str = ""):
        """Record an agent's vote."""
        vote_file = self.votes_dir / f"{vote_id}.json"
        
        with open(vote_file, 'r+') as f:
            fcntl.flock(f.fileno(), fcntl.LOCK_EX)
            vote_data = json.load(f)
            
            # Validate
            if agent_id not in vote_data["eligible_voters"]:
                fcntl.flock(f.fileno(), fcntl.LOCK_UN)
                return {"error": "Not eligible to vote"}
            
            if vote_data["status"] != "open":
                fcntl.flock(f.fileno(), fcntl.LOCK_UN)
                return {"error": "Vote is closed"}
            
            # Record vote
            vote_data["votes_cast"][agent_id] = {
                "choice": choice,
                "reasoning": reasoning,
                "timestamp": datetime.now().isoformat()
            }
            
            # Save
            f.seek(0)
            json.dump(vote_data, f, indent=2)
            f.truncate()
            fcntl.flock(f.fileno(), fcntl.LOCK_UN)
        
        self.audit.log("vote_cast", agent_id, f"Voted on {vote_id}: {choice}")
        
        return {"success": True}
    
    def tally_vote(self, vote_id: str):
        """Count votes and determine outcome."""
        vote_file = self.votes_dir / f"{vote_id}.json"
        
        with open(vote_file) as f:
            vote_data = json.load(f)
        
        mechanism = vote_data["mechanism"]
        votes = vote_data["votes_cast"]
        
        if mechanism == "simple_majority":
            tally = {}
            for vote in votes.values():
                choice = vote["choice"]
                tally[choice] = tally.get(choice, 0) + 1
            
            winner = max(tally, key=tally.get)
            result = {
                "outcome": winner,
                "tally": tally,
                "total_votes": len(votes)
            }
        
        elif mechanism == "weighted_voting":
            # Implement weighted logic
            pass
        
        # Update vote record
        vote_data["status"] = "closed"
        vote_data["result"] = result
        vote_data["closed_at"] = datetime.now().isoformat()
        
        with open(vote_file, 'w') as f:
            json.dump(vote_data, f, indent=2)
        
        # Broadcast result
        for voter in vote_data["eligible_voters"]:
            self.comm.send_message(
                from_agent="voting-system",
                to=voter,
                message=f"Vote {vote_id} closed. Outcome: {result['outcome']}",
                priority="normal"
            )
        
        self.audit.log("vote_closed", "system", f"Vote {vote_id}: {result['outcome']}")
        
        return result
```

**Action Items**:
- [ ] Implement `VotingSystem` class in new file `voting_system.py`
- [ ] Integrate with `setup_communication.py`
- [ ] Add vote initiation instructions to agent templates
- [ ] Create vote UI/CLI for human oversight
- [ ] Add automatic vote tallying (deadline-based)
- [ ] Test with mock vote scenario

---

### 4. Bootstrap Chicken-and-Egg Problem

**Files Affected**: `SKILL.md`, `analyze_project.py`, all setup scripts

**Problem**: Circular dependencies in initialization:

```
Need context-manager → But it's an agent → Agents need communication system
      ↓                                              ↓
Communication system needs setup → Who sets it up? → Need an agent
      ↓                                              ↓
Job board needs tasks → Who creates them? → Need agents working
```

**Current Approach**: Manual Python scripts (breaks "organic seed" philosophy)

**Solutions**:

- [ ] **Option A: Seed Agent Bootstrap**
```python
# Create minimal "bootstrap-agent" that:
# 1. Analyzes project
# 2. Sets up communication
# 3. Creates job board
# 4. Spawns other agents
# 5. Self-terminates

# In SKILL.md, single entry point:
"Initialize team for this project"

# Claude (as bootstrap agent) then:
1. Run analyze_project.py
2. Run setup_communication.py
3. Run create_job_board.py
4. Run recruit_agents.py
5. Run specialize_agents.py
6. Hand off to agent-manager
```

- [ ] **Option B: Phased Manual → Automated**
```markdown
# SKILL.md Phase 0 (Manual/Hybrid):
User runs: python scripts/setup_infrastructure.py

This script:
- Creates .claude/ directory structure
- Initializes communication (no agents yet)
- Creates empty job board
- Prepares agent recruitment

# Phase 1 (Automated):
User tells Claude: "Onboard the team"

Claude then:
- Recruits agents using existing infrastructure
- Specializes them
- Registers them in communication system
- Starts coordination
```

- [ ] **Option C: System Agent (Always Present)**
```python
# Create special "system" agent that is never terminated
# This agent owns:
# - Communication system
# - Job board
# - Agent registry
# - Voting system

# Lives in .claude/system/ (separate from .claude/agents/)
# All other agents interact with system agent
# Solves bootstrap by having persistent coordinator
```

**Action Items**:
- [ ] Choose bootstrap strategy (A/B/C)
- [ ] Implement chosen approach
- [ ] Update SKILL.md with clear entry point
- [ ] Test initialization from blank project directory
- [ ] Document exact commands/invocations needed

---

### 5. Round 2 Training Not Implemented

**Files Affected**: `specialize_agents.py`, `specialization-guidelines.md`, `agent-manager.md`

**Problem**: 
- Round 2 training referenced everywhere
- `agent-manager.md` says it "handles recruitment and training"
- `specialize_agents.py` has placeholder:
```python
def _round2_specialization(self, body: str, context: Dict, frontmatter: str) -> str:
    domain_section = """
    **Project-Specific Conventions:**
    (To be populated by agent-manager during Round 2 training)
    """
```

**But**: No actual implementation of how agent-manager trains agents.

**Required Implementation**:

```python
# New file: scripts/train_agents.py

class AgentTrainer:
    """Round 2 deep training for agents."""
    
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.agents_dir = self.project_root / ".claude" / "agents"
        self.specs_dir = self.project_root / "specs"
    
    def analyze_project_patterns(self):
        """Extract conventions from existing codebase."""
        patterns = {
            "coding_standards": self._detect_coding_standards(),
            "api_patterns": self._detect_api_patterns(),
            "testing_patterns": self._detect_testing_patterns(),
            "data_sources": self._map_data_sources(),
            "integration_points": self._find_integrations()
        }
        return patterns
    
    def _detect_coding_standards(self):
        """Look for .eslintrc, .prettierrc, style guides, etc."""
        standards = {}
        
        # Check for linter configs
        if (self.project_root / ".eslintrc").exists():
            standards["linter"] = "ESLint"
            # Parse config...
        
        if (self.project_root / "pyproject.toml").exists():
            # Check for black, ruff, etc.
            pass
        
        return standards
    
    def train_agent(self, agent_name: str, patterns: dict):
        """Apply Round 2 training to specific agent."""
        agent_file = self.agents_dir / f"{agent_name}.md"
        
        with open(agent_file) as f:
            content = f.read()
        
        # Extract frontmatter and body
        frontmatter, body = self._split_frontmatter(content)
        
        # Generate domain-specific training
        training_section = self._generate_training_section(agent_name, patterns)
        
        # Inject into agent
        updated_body = self._inject_training(body, training_section)
        
        # Save
        updated_content = f"---\n{frontmatter}\n---\n\n{updated_body}"
        with open(agent_file, 'w') as f:
            f.write(updated_content)
        
        return {"agent": agent_name, "trained": True}
    
    def _generate_training_section(self, agent_name: str, patterns: dict):
        """Create agent-specific training based on role."""
        
        if "frontend" in agent_name:
            return f"""
## Deep Domain Training

**Project-Specific Conventions:**
- Linter: {patterns['coding_standards'].get('linter', 'Not configured')}
- Component structure: {patterns.get('component_pattern', 'Standard')}
- State management: {patterns.get('state_management', 'To be determined')}

**Data Sources:**
- API Base URL: {patterns['data_sources'].get('api_url', 'See .env')}
- Auth endpoint: {patterns['data_sources'].get('auth_endpoint', '/api/auth')}

**Integration Points:**
- Backend API: {patterns['integration_points'].get('backend', 'Not yet configured')}

---
**Training Status:** Round 2 Complete - {datetime.now().isoformat()}
"""
        
        # Similar logic for other agent types...
        return ""
```

**Action Items**:
- [ ] Implement `AgentTrainer` class
- [ ] Add pattern detection methods (coding standards, APIs, etc.)
- [ ] Create training section generator for each agent type
- [ ] Integrate with agent-manager workflow
- [ ] Add Round 2 trigger (after N tasks completed? After 24 hours? Manual?)
- [ ] Test training on sample project

---

### 6. Message System: SQLite Query References Non-Existent Table

**File**: `setup_communication.py`, line ~280

**Problem**:
```python
query = """
    SELECT * FROM messages 
    WHERE (to_agent = ? OR channel IN (
        SELECT channel FROM channels WHERE ? IN subscribers  # ❌ No 'channels' table!
    ))
"""
```

Only `messages` and `agent_status` tables are created. Channel subscription is stored in `agent-registry.json`.

**Fix**:
```python
def get_messages(self, agent_id: str, unread_only: bool = False):
    """Retrieve messages for an agent."""
    
    # Load channel subscriptions from registry
    with open(self.registry_path) as f:
        registry = json.load(f)
    
    # Find which channels agent is subscribed to
    subscribed_channels = []
    for channel_name, channel_data in registry["channels"].items():
        if agent_id in channel_data["subscribers"]:
            subscribed_channels.append(channel_name)
    
    # Build query
    conn = sqlite3.connect(self.db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Get direct messages and subscribed channel messages
    placeholders = ','.join(['?'] * len(subscribed_channels))
    query = f"""
        SELECT * FROM messages 
        WHERE (to_agent = ? OR channel IN ({placeholders}))
    """
    
    params = [agent_id] + subscribed_channels
    
    if unread_only:
        query += " AND read = 0"
    
    query += " ORDER BY timestamp DESC LIMIT 50"
    
    cursor.execute(query, params)
    messages = [dict(row) for row in cursor.fetchall()]
    
    conn.close()
    
    # Load message content from files
    for msg in messages:
        try:
            with open(msg['file_path']) as f:
                content = json.load(f)
                msg['content'] = content['message']
        except:
            msg['content'] = "[Message file not found]"
    
    return messages
```

**Action Items**:
- [ ] Fix `get_messages()` query to use registry instead of non-existent table
- [ ] Add channel subscription to DB if needed for performance
- [ ] Test message retrieval for agents in multiple channels
- [ ] Add error handling for missing registry file

---

### 7. SKILL.md Workflow Ambiguity

**File**: `SKILL.md`

**Problem**: Mixes manual script execution with Claude orchestration

```bash
# User manually runs:
python scripts/analyze_project.py > project-context.json

# Then tells Claude:
"Initialize the project team"

# But then shows Python code in markdown:
import sys
from pathlib import Path
sys.path.insert(0, 'scripts/')
```

Who executes what? When?

**Fix - Clear Execution Model**:

```markdown
# Project Team Onboarding

## Usage (Choose One Approach)

### Approach A: Fully Automated (Recommended)

Tell Claude from your project root:
```
"Initialize the onboard project team for this project"
```

Claude will automatically:
1. Analyze your project structure
2. Create `.claude/` directory structure  
3. Set up communication infrastructure
4. Recruit and specialize relevant agents
5. Create initial tasks in job board
6. Start team coordination

### Approach B: Manual Step-by-Step (For Debugging)

If you prefer manual control or need to debug:

```bash
# 1. Analyze project
python /mnt/skills/user/project-onboard/scripts/analyze_project.py . > context.json

# 2. Review recommendations
cat context.json

# 3. Initialize infrastructure
python /mnt/skills/user/project-onboard/scripts/setup_communication.py .
python /mnt/skills/user/project-onboard/scripts/create_job_board.py init

# 4. Tell Claude to continue:
"Based on context.json, recruit and specialize the recommended agents"
```

## What Claude Does Internally

When you say "Initialize the onboard project team", Claude:

1. **Runs** `analyze_project.py` using bash tool
2. **Reads** output to understand your project
3. **Runs** infrastructure setup scripts
4. **Recruits** agents from templates
5. **Specializes** agents (Round 1)
6. **Registers** agents in communication system
7. **Creates** initial tasks
8. **Broadcasts** coordination protocol

You don't need to run Python manually unless debugging.
```

**Action Items**:
- [ ] Rewrite SKILL.md with clear usage instructions
- [ ] Remove ambiguous code snippets
- [ ] Document Approach A (fully automated) as default
- [ ] Document Approach B (manual) for debugging
- [ ] Test both approaches end-to-end

---

### 8. Agent Manager Responsibility Contradiction

**Files**: `agent-manager.md`, `specialization-guidelines.md`

**Problem**:
- `agent-manager.md` description: "multi-agent orchestration, team assembly, workflow optimization"
- `specialization-guidelines.md` says: "Round 2 performed by agent-manager using training protocol"
- But `agent-manager.md` has NO mention of training capabilities

**Fix**:

Update `agent-manager.md` to include:

```markdown
---
name: agent-manager
description: Expert agent manager specializing in multi-agent orchestration, team assembly, agent training, and workflow optimization. Masters task decomposition, agent selection, specialization, and coordination strategies with focus on achieving optimal team performance and resource utilization.
tools: Read, Write, Edit, Glob, Grep, Bash
---

[... existing content ...]

## Agent Training & Specialization

### Round 2 Deep Training

After initial project work begins, agent-manager coordinates deep specialization:

**Training Workflow:**
1. Analyze project patterns and conventions
2. Identify agent-specific training needs
3. Generate specialized knowledge sections
4. Inject training into agent definitions
5. Validate training effectiveness

**Training Areas:**
- Coding standards and conventions
- Project-specific APIs and data sources
- Integration patterns
- Company policies
- Security requirements
- Testing strategies

**Triggering Round 2:**
- After 24 hours of project work, OR
- After 50 tasks completed, OR
- When patterns become clear
- Manual trigger by human

**Implementation:**
Use scripts/train_agents.py to analyze and specialize:
```bash
python scripts/train_agents.py --round 2 --agents frontend-developer,backend-developer
```

Training updates are logged to audit trail and agents are notified of new capabilities.

[... rest of content ...]
```

**Action Items**:
- [ ] Update `agent-manager.md` with training section
- [ ] Clarify when Round 2 is triggered
- [ ] Add training capabilities to agent-manager tools
- [ ] Test training workflow

---

## 🟡 MAJOR ISSUES (High Priority)

### 9. Token Budget Violation

**Problem**: FINTO philosophy says "95%+ dormant", but:
- Each agent: 2000-4000 tokens (base template)
- Round 1 adds: 300-500 tokens
- Communication protocol: 200 tokens
- **Total per agent**: 2500-4700 tokens
- **With 12 agents**: 30,000-56,400 tokens always active

This violates progressive disclosure.

**Solution**:
- [ ] Move communication protocol to separate file (loaded once)
- [ ] Use agent summaries in registry (50 tokens each)
- [ ] Load full agent only when assigned task
- [ ] Compress common patterns into shared resources

---

### 10. No Health Checks or Agent Status Updates

**Files**: `setup_communication.py`, `agent_status` table

**Problem**: Table has `last_heartbeat` but nothing updates it.

**Solution**:
```python
# Add to each agent's workflow
def report_status(self, agent_id: str, status: str, current_task: str = None):
    """Update agent status and heartbeat."""
    conn = sqlite3.connect(self.db_path)
    cursor = conn.cursor()
    
    cursor.execute("""
        INSERT OR REPLACE INTO agent_status 
        (agent_id, status, current_task, last_heartbeat, messages_pending)
        VALUES (?, ?, ?, ?, ?)
    """, (agent_id, status, current_task, datetime.now().isoformat(), 0))
    
    conn.commit()
    conn.close()

# Add health checker
def check_agent_health(self):
    """Detect stale/crashed agents."""
    conn = sqlite3.connect(self.db_path)
    cursor = conn.cursor()
    
    # Find agents that haven't heartbeat in 10 minutes
    stale_threshold = (datetime.now() - timedelta(minutes=10)).isoformat()
    
    cursor.execute("""
        SELECT agent_id, last_heartbeat 
        FROM agent_status
        WHERE last_heartbeat < ?
    """, (stale_threshold,))
    
    stale_agents = cursor.fetchall()
    conn.close()
    
    return stale_agents
```

**Action Items**:
- [ ] Implement `report_status()` method
- [ ] Add heartbeat calls to agent templates
- [ ] Implement `check_agent_health()` periodic task
- [ ] Add automatic task reassignment for crashed agents

---

### 11. Audit Log Performance Degradation

**File**: `audit_logger.py`

**Problem**: O(n) scan on every query. After 10,000 events, becomes very slow.

**Solution**:
```python
# Option A: Migrate to SQLite
# Replace .jsonl with .db

# Option B: Periodic compaction
def compact_audit_log(self, older_than_days: int = 30):
    """Move old events to archive."""
    cutoff = (datetime.now() - timedelta(days=older_than_days)).isoformat()
    
    current = []
    archive = []
    
    with open(self.audit_path) as f:
        for line in f:
            event = json.loads(line)
            if event["timestamp"] < cutoff:
                archive.append(event)
            else:
                current.append(event)
    
    # Write current events back
    with open(self.audit_path, 'w') as f:
        for event in current:
            f.write(json.dumps(event) + '\n')
    
    # Write archive
    archive_file = self.claude_dir / f"audit-trail-{datetime.now().strftime('%Y%m')}.jsonl"
    with open(archive_file, 'w') as f:
        for event in archive:
            f.write(json.dumps(event) + '\n')
```

**Action Items**:
- [ ] Choose audit storage strategy (SQLite or compaction)
- [ ] Implement chosen approach
- [ ] Add scheduled compaction (if using files)
- [ ] Test query performance with 100k+ events

---

### 12. GitHub Agent Fetch: No Caching or Fallback

**File**: `recruit_agents.py`

**Problem**: Every recruitment hits network. If GitHub down, onboarding fails.

**Solution**:
```python
def recruit(self, agent_name: str, required_capabilities: Optional[List[str]] = None) -> Dict:
    """Recruit an agent - try local cache → GitHub → create new."""
    
    # 1. Check local cache first
    cache_dir = Path(__file__).parent.parent / "cache" / "agents"
    cache_file = cache_dir / f"{agent_name}.md"
    
    if cache_file.exists():
        # Check if cache is fresh (< 7 days old)
        age = time.time() - cache_file.stat().st_mtime
        if age < 7 * 24 * 3600:
            with open(cache_file) as f:
                return {
                    "status": "found_cache",
                    "agent": agent_name,
                    "source": "local_cache",
                    "content": f.read()
                }
    
    # 2. Try templates directory
    local_path = self.local_templates / f"{agent_name}.md"
    if local_path.exists():
        with open(local_path) as f:
            return {
                "status": "found_local",
                "agent": agent_name,
                "source": "local_template",
                "content": f.read()
            }
    
    # 3. Try GitHub
    github_result = self._fetch_from_github(agent_name)
    if github_result["status"] == "success":
        # Cache for future use
        cache_dir.mkdir(parents=True, exist_ok=True)
        with open(cache_file, 'w') as f:
            f.write(github_result["content"])
        return github_result
    
    # 4. Fall back to creation (with warning)
    return self._create_agent(agent_name, required_capabilities)
```

**Action Items**:
- [ ] Implement caching layer
- [ ] Add cache invalidation (age-based or manual)
- [ ] Bundle essential agents with skill
- [ ] Test with network disabled

---

### 13. Job Board: No Task Timeout or Staleness Detection

**File**: `create_job_board.py`

**Problem**: Task can be "in-progress" forever if agent crashes.

**Solution**:
```python
def detect_stale_tasks(self, max_hours: int = 24):
    """Find tasks in-progress for too long."""
    board = self._load_board()
    now = datetime.now()
    stale = []
    
    for task_id, task in board["tasks"].items():
        if task["status"] == "in-progress" and task["started_at"]:
            started = datetime.fromisoformat(task["started_at"])
            hours_elapsed = (now - started).total_seconds() / 3600
            
            if hours_elapsed > max_hours:
                stale.append({
                    "task_id": task_id,
                    "assigned_to": task["assigned_to"],
                    "hours_stuck": hours_elapsed
                })
    
    return stale

def reassign_stale_task(self, task_id: str):
    """Unassign stale task and mark for reassignment."""
    board = self._load_board()
    task = board["tasks"][task_id]
    
    # Log previous owner
    prev_owner = task["assigned_to"]
    
    # Reset task
    task["assigned_to"] = None
    task["status"] = "open"
    task["started_at"] = None
    task["history"].append({
        "timestamp": datetime.now().isoformat(),
        "action": f"reassigned_from_stale (was: {prev_owner})",
        "by": "system"
    })
    
    self._save_board(board)
    
    return {"success": True, "previous_owner": prev_owner}
```

**Action Items**:
- [ ] Implement staleness detection
- [ ] Add periodic background check (every 30 min?)
- [ ] Implement automatic reassignment
- [ ] Notify agents of reassigned tasks

---

### 14. Communication: No Message Expiration or Archive

**File**: `setup_communication.py`

**Problem**: Messages accumulate forever, bloating storage and slowing queries.

**Solution**:
```python
def archive_old_messages(self, older_than_days: int = 30):
    """Move old messages to archive."""
    cutoff = (datetime.now() - timedelta(days=older_than_days)).isoformat()
    
    conn = sqlite3.connect(self.db_path)
    cursor = conn.cursor()
    
    # Find old messages
    cursor.execute("""
        SELECT id, file_path FROM messages
        WHERE timestamp < ? AND archived = 0
    """, (cutoff,))
    
    old_messages = cursor.fetchall()
    
    # Move files to archive
    archive_dir = self.comm_dir / "archive" / datetime.now().strftime("%Y-%m")
    archive_dir.mkdir(parents=True, exist_ok=True)
    
    for msg_id, file_path in old_messages:
        src = Path(file_path)
        if src.exists():
            dest = archive_dir / src.name
            src.rename(dest)
            
            # Update DB
            cursor.execute("""
                UPDATE messages SET archived = 1, file_path = ?
                WHERE id = ?
            """, (str(dest), msg_id))
    
    conn.commit()
    conn.close()
    
    return len(old_messages)
```

**Action Items**:
- [ ] Implement message archiving
- [ ] Add scheduled cleanup task
- [ ] Test retrieval from archive
- [ ] Add archive browsing capability

---

### 15. Dependencies: Circular Checks But Not Enforcement

**File**: `create_job_board.py`

**Problem**: `_check_dependencies()` warns but doesn't prevent work on blocked tasks.

**Solution**:
```python
def get_available_tasks(self, agent_id: Optional[str] = None) -> List[Dict]:
    """Get tasks available for work (dependencies met)."""
    board = self._load_board()
    
    available = []
    for task in board["tasks"].values():
        # Must be open or assigned to this agent
        if task["status"] not in ["open", "assigned"]:
            continue
        
        # Check assignment
        if task["assigned_to"] and task["assigned_to"] != agent_id:
            continue
        
        # Check dependencies - BLOCK if unmet
        unmet_deps = self._check_dependencies(board, task["id"])
        if unmet_deps:
            continue  # ✅ Don't include in available tasks
        
        available.append(task)
    
    # Sort by priority
    priority_order = {"critical": 0, "high": 1, "normal": 2, "low": 3}
    available.sort(key=lambda t: priority_order.get(t["priority"], 2))
    
    return available

# Also add explicit blocking in assign_task
def assign_task(self, task_id: str, agent_id: str) -> Dict:
    board = self._load_board()
    
    if task_id not in board["tasks"]:
        return {"error": "Task not found"}
    
    task = board["tasks"][task_id]
    
    # Check dependencies first - ENFORCE
    unmet_deps = self._check_dependencies(board, task_id)
    if unmet_deps:
        return {
            "error": "Unmet dependencies",
            "blocked_by": unmet_deps,
            "message": f"Cannot assign. Complete these tasks first: {', '.join(unmet_deps)}"
        }
    
    # ... rest of assignment logic
```

**Action Items**:
- [ ] Enforce dependency blocking in `get_available_tasks()`
- [ ] Add explicit dependency check in `assign_task()`
- [ ] Add dependency graph visualization (optional)
- [ ] Test with complex dependency chains

---

### 16. Specialization: Fragile Injection Pattern

**File**: `specialize_agents.py`

**Problem**: Looks for "You are a" text pattern. Breaks if template varies.

**Solution**:
```python
def _round1_specialization(self, body: str, context: Dict, frontmatter: str) -> str:
    """Round 1: Light touch specialization using marker-based injection."""
    
    project_section = f"""
## Project Context
... (same as before)
"""
    
    comm_section = """
## Communication Protocol
... (same as before)
"""
    
    # Look for explicit marker first
    if "<!-- INJECT_SPECIALIZATION_HERE -->" in body:
        return body.replace("<!-- INJECT_SPECIALIZATION_HERE -->", 
                          project_section + comm_section)
    
    # Otherwise, find first heading and inject after
    lines = body.split('\n')
    for i, line in enumerate(lines):
        if line.startswith('## '):
            # Inject before first heading
            lines.insert(i, project_section + comm_section)
            return '\n'.join(lines)
    
    # Fallback: prepend
    return project_section + comm_section + "\n\n" + body
```

**Better Yet**: Use structured YAML blocks:
```markdown
---
name: frontend-developer
specialization_points:
  - after: "## Core Responsibilities"
  - before: "## Tools"
---
```

**Action Items**:
- [ ] Add injection markers to all agent templates
- [ ] Use marker-based injection
- [ ] Add validation of injected content
- [ ] Test with various template formats

---

## 🟢 MINOR ISSUES (Can Defer)

### 17. README Example Shows 12 Agents - No Formula

Suggest: `num_agents = min(tech_stack_count + 3, 15)`

### 18. No Skill Usage Tracking

Implement in audit log: skill invocation counts, success rates.

### 19. Agent Templates Oversell Capabilities

Context-manager promises "vector embeddings" but has no implementation.

### 20. No Rate Limiting Enforcement

Protocol.md mentions limits but no code checks them.

### 21. Audit Log: No Tamper Detection

Could add checksums or signatures for integrity.

### 22. Token Calculation Missing

No way to estimate total token usage before deployment.

---

## 🎯 ARCHITECTURAL DECISIONS REQUIRED

### Decision 1: Concurrency Control Strategy

**Options**:
- [ ] **A. File Locking** (Simple, portable)
  - Pros: Works with existing file structure
  - Cons: Deadlock risk, platform-specific (fcntl)
  
- [ ] **B. SQLite Migration** (Robust)
  - Pros: ACID, transactions, better queries
  - Cons: More refactoring, learning curve
  
- [ ] **C. Sequential Epochs** (Safest)
  - Pros: No race conditions possible
  - Cons: Slower, artificial constraint

**Recommendation**: Start with **C** for MVP (sequential), migrate to **B** (SQLite) for production.

**Action**: 
- [ ] Decide on concurrency model
- [ ] Document decision in `resources/architecture-decisions.md`

---

### Decision 2: Communication Protocol Formality

**Options**:
- [ ] **A. Structured JSON** (Powerful)
  - Pros: Machine-parseable, typed, extensible
  - Cons: Overhead, complexity
  
- [ ] **B. Text + Conventions** (Simple)
  - Pros: Natural, flexible, easy to debug
  - Cons: Ambiguous, hard to validate
  
- [ ] **C. Hybrid** (Balanced)
  - Urgent messages: text
  - Complex requests: JSON

**Recommendation**: **C** - Hybrid approach

**Action**:
- [ ] Choose protocol approach
- [ ] Update agent templates consistently
- [ ] Document in `resources/communication_protocols.md`

---

### Decision 3: Bootstrap Strategy

**Options**:
- [ ] **A. Manual Scripts → Agent Takeover**
  - User runs infrastructure setup
  - Then agents coordinate
  
- [ ] **B. Seed Agent Bootstrap**
  - Special bootstrap agent does everything
  - Self-terminates when done
  
- [ ] **C. System Agent (Persistent Coordinator)**
  - Always-on system agent owns infrastructure
  - Other agents come and go

**Recommendation**: **B** - Seed agent (most aligned with "organic seed" philosophy)

**Action**:
- [ ] Choose bootstrap approach
- [ ] Implement chosen strategy
- [ ] Update SKILL.md with clear entry point

---

### Decision 4: Agent Specialization Depth

**Options**:
- [ ] **A. Light Touch Only** (300-500 tokens)
  - Just organizational principles
  - Fast, token-efficient
  
- [ ] **B. Two Rounds** (300-500 + 1000-2000 tokens)
  - Round 1: Org principles
  - Round 2: Deep domain knowledge
  
- [ ] **C. Progressive Levels** (3+ rounds)
  - Continuous refinement as project evolves

**Recommendation**: **B** - Two rounds (as originally designed)

**Action**:
- [ ] Implement Round 2 training system
- [ ] Define triggers for Round 2 (time/task-based)

---

## ✅ IMPLEMENTATION CHECKLIST

### Phase 0: Critical Fixes (Do First)

- [ ] **Concurrency Control**
  - [ ] Implement file locking in job board
  - [ ] Implement file locking in communication system
  - [ ] Add atomic writes to audit logger
  - [ ] Test with 3+ concurrent agents

- [ ] **Communication Protocol**
  - [ ] Choose structured/text/hybrid approach
  - [ ] Implement message handler
  - [ ] Update all agent templates consistently
  - [ ] Document protocol clearly

- [ ] **Voting System**
  - [ ] Implement vote initiation
  - [ ] Implement vote casting
  - [ ] Implement vote tallying
  - [ ] Integrate with communication system
  - [ ] Test mock vote

- [ ] **Bootstrap Sequence**
  - [ ] Clarify manual vs automated
  - [ ] Implement chosen approach
  - [ ] Update SKILL.md with clear entry
  - [ ] Test from blank project

- [ ] **Round 2 Training**
  - [ ] Implement AgentTrainer class
  - [ ] Add pattern detection
  - [ ] Create training generators
  - [ ] Test on sample project

- [ ] **SQLite Query Fix**
  - [ ] Fix get_messages() to use registry
  - [ ] Test channel-based message retrieval

- [ ] **SKILL.md Clarity**
  - [ ] Rewrite with clear usage instructions
  - [ ] Remove ambiguous code
  - [ ] Test both automated and manual modes

- [ ] **Agent Manager Update**
  - [ ] Add training capabilities to description
  - [ ] Document Round 2 workflow
  - [ ] Clarify responsibilities

---

### Phase 1: Major Fixes (Do Next)

- [ ] **Token Budget**
  - [ ] Extract communication protocol to shared file
  - [ ] Implement agent summaries
  - [ ] Test token usage with 12 agents

- [ ] **Health Checks**
  - [ ] Implement report_status()
  - [ ] Add heartbeat to agent templates
  - [ ] Implement health checker
  - [ ] Add auto-reassignment

- [ ] **Audit Performance**
  - [ ] Choose SQLite or compaction
  - [ ] Implement chosen approach
  - [ ] Test with 100k+ events

- [ ] **GitHub Caching**
  - [ ] Implement cache layer
  - [ ] Bundle essential agents
  - [ ] Test offline mode

- [ ] **Task Staleness**
  - [ ] Implement detection
  - [ ] Add periodic checker
  - [ ] Implement reassignment
  - [ ] Test timeout scenarios

- [ ] **Message Archiving**
  - [ ] Implement archive system
  - [ ] Add scheduled cleanup
  - [ ] Test retrieval

- [ ] **Dependency Enforcement**
  - [ ] Block tasks with unmet deps
  - [ ] Enforce in assignment
  - [ ] Test dependency chains

- [ ] **Specialization Robustness**
  - [ ] Add injection markers
  - [ ] Implement marker-based injection
  - [ ] Validate injected content

---

### Phase 2: Minor Fixes (Optional)

- [ ] Agent selection formula
- [ ] Skill usage tracking
- [ ] Rate limiting enforcement
- [ ] Audit log integrity
- [ ] Token calculation tool

---

## 🧪 TESTING STRATEGY

### Test Project: "Simple Todo App"

**Stack**: React (frontend), Node.js (backend), SQLite (database)

**Test Phases**:

#### Phase 1: Infrastructure Test
- [ ] Initialize in blank directory
- [ ] Verify .claude/ structure created
- [ ] Check communication system
- [ ] Verify job board
- [ ] Verify audit trail

#### Phase 2: Agent Recruitment Test
- [ ] Recruit 4 agents: context-manager, agent-manager, frontend-developer, backend-developer
- [ ] Verify all templates fetched
- [ ] Check Round 1 specialization applied
- [ ] Verify agents registered in communication system

#### Phase 3: Communication Test
- [ ] Send test message from one agent to another
- [ ] Verify message indexed in DB
- [ ] Verify message file created
- [ ] Test broadcast to all agents
- [ ] Test channel-based messaging

#### Phase 4: Job Board Test
- [ ] Create initial tasks (setup project, create UI, create API)
- [ ] Have agent claim task
- [ ] Verify no double-assignment possible
- [ ] Test task completion
- [ ] Test dependency blocking

#### Phase 5: Coordination Test
- [ ] Agents query context-manager
- [ ] Agents update job board
- [ ] Messages flow between agents
- [ ] Audit trail captures all actions
- [ ] No file corruption or race conditions

#### Phase 6: Voting Test
- [ ] Initiate mock vote (CSS framework choice)
- [ ] Agents cast votes
- [ ] System tallies
- [ ] Result broadcast
- [ ] Audit log records

#### Phase 7: Round 2 Test
- [ ] Trigger Round 2 training
- [ ] Verify agents receive domain knowledge
- [ ] Check token additions reasonable
- [ ] Test improved performance

---

### Mental Simulation Checklist

Walk through end-to-end:
- [ ] User invokes skill
- [ ] Bootstrap sequence starts
- [ ] Each script execution traced
- [ ] Each file read/write logged
- [ ] Each message sent tracked
- [ ] Potential race conditions identified
- [ ] Token usage calculated
- [ ] Failure points identified
- [ ] Recovery mechanisms tested

---

## 📊 TRACKING METRICS

### Before Testing:
- Critical issues: **8**
- Major issues: **15**
- Minor issues: **10**

### Target After Fixes:
- Critical issues: **0**
- Major issues: **0**
- Minor issues: **<5**

### Current Status:
- [ ] Phase 0 complete (critical fixes)
- [ ] Phase 1 complete (major fixes)
- [ ] Phase 2 complete (minor fixes)
- [ ] Testing phase complete
- [ ] Production ready

---

## 🚀 NEXT STEPS

1. **Review this document** with human
2. **Make architectural decisions** (concurrency, protocol, bootstrap)
3. **Fix critical issues** (Phase 0)
4. **Test infrastructure** with minimal agents
5. **Fix major issues** (Phase 1)
6. **Run full test** with todo app
7. **Iterate** based on test results
8. **Document** lessons learned
9. **Ship** MVP

---

**Document Version**: 1.0  
**Last Updated**: 2025-11-08  
**Status**: Ready for Review

---

## 💭 FINAL THOUGHTS

This audit reveals that the **conceptual design is excellent** but the **implementation has critical gaps**. The good news: most issues are solvable with systematic work.

**Biggest risks**:
1. Concurrency (will cause data corruption)
2. Bootstrap confusion (users won't know how to start)
3. Communication mismatch (agents can't actually talk)

**Fix these three first**, then everything else follows.

The vision is sound. The execution needs love. Let's make it real. 🎯
