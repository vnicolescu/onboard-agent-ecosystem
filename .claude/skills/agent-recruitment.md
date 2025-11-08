---
name: agent-recruitment
description: Recruit and configure agents based on project needs. Analyzes project to determine required roles, fetches agent templates, and prepares them for specialization. Use when initializing project team or adding new capabilities.
---

# Agent Recruitment

## When to Use This Skill

Use this skill when you need to build or expand your agent team:

**Triggers:**
- New project initialization
- Adding capabilities to existing team
- Scaling team for larger scope
- Replacing or upgrading agents

**What This Skill Does:**
- Analyzes project to determine required agent roles
- Fetches agent templates from repository or creates new ones
- Prepares agents for Round 1 specialization
- Validates agent configurations

## Recruitment Workflow

### Step 1: Analyze Project Requirements

**Understand the project** to determine what agents are needed:

1. **Read Project Structure**
   ```python
   # Use Glob to find key files
   frontend_files = glob("src/**/*.tsx") + glob("src/**/*.jsx")
   backend_files = glob("api/**/*.py") + glob("server/**/*.js")
   test_files = glob("**/*.test.*") + glob("**/*.spec.*")
   db_files = glob("**/migrations/**") + glob("**/models/**")
   ```

2. **Detect Technology Stack**
   - Frontend: React, Vue, Angular, Svelte?
   - Backend: Node.js, Python, Ruby, Go?
   - Database: PostgreSQL, MongoDB, MySQL?
   - Testing: Jest, Pytest, Mocha?
   - DevOps: Docker, K8s, CI/CD?

3. **Identify Required Roles**

   **Always Required:**
   - context-manager (manages shared knowledge)
   - agent-manager (coordinates team)
   - multi-agent-orchestrator (workflow coordination)

   **Based on Stack:**
   - Frontend → frontend-developer
   - React/Vue/Angular → framework-specialist
   - Backend API → backend-developer
   - Database → database-specialist
   - Tests → test-engineer
   - DevOps → deployment-engineer
   - Security → security-auditor
   - Documentation → documentation-writer

4. **Consider Project Phase**
   - Early stage → smaller team (6-8 agents)
   - Growth stage → medium team (8-12 agents)
   - Mature → larger team (12-15 agents)

### Step 2: Determine Agent Recommendations

Create a ranked list of agents based on project needs:

```python
# Example analysis result
recommendations = {
    "essential": [
        "context-manager",
        "agent-manager",
        "multi-agent-orchestrator"
    ],
    "high_priority": [
        "frontend-developer",  # Found React files
        "backend-developer",   # Found API routes
        "database-specialist"  # Found migrations
    ],
    "medium_priority": [
        "test-engineer",      # Test coverage needed
        "code-reviewer",      # Quality assurance
        "documentation-writer" # Docs lacking
    ],
    "optional": [
        "ui-designer",        # If design work needed
        "performance-engineer" # If optimization needed
    ]
}
```

### Step 3: Fetch Agent Templates

For each required agent, get the template:

**Option 1: Check Local Templates First**
```python
# Look in templates/agents/
local_path = f"templates/agents/{agent_name}.md"
if file_exists(local_path):
    template = read_file(local_path)
    return {"source": "local", "content": template}
```

**Option 2: Fetch from GitHub Repository**
```python
# Repository: VoltAgent/awesome-claude-code-subagents
url = f"https://raw.githubusercontent.com/VoltAgent/awesome-claude-code-subagents/main/agents/{agent_name}.md"

# Use WebFetch to get template
result = fetch_url(url)
if result.success:
    return {"source": "github", "content": result.content}
```

**Option 3: Create Custom Agent**

If agent not found, create basic template:

```markdown
---
name: {agent_name}
description: {inferred_description}
tools: Read, Write, Edit, Bash, Glob, Grep
---

You are a {role} specializing in {domain}. Your focus is {primary_responsibility}.

## Communication Protocol

**See:** `resources/agent-communication-guide.md` for complete protocol documentation.

### Quick Setup

```python
from communications.agent_sdk import AgentMessenger

messenger = AgentMessenger("{agent_name}")
messenger.heartbeat("active", "Ready for {role} tasks")
```

## Responsibilities

{list_of_responsibilities}

## Key Skills

{list_of_key_skills}

## Development Workflow

{workflow_steps}
```

### Step 4: Prepare Agents for Specialization

Place fetched/created agents in pending directory:

```python
# Create pending directory
ensure_directory(".claude/agents/pending/")

# Save agent template
agent_path = f".claude/agents/pending/{agent_name}.md"
write_file(agent_path, agent_content)

print(f"✓ Prepared {agent_name} for specialization")
```

### Step 5: Generate Recruitment Summary

Create report for human review:

```markdown
# Agent Recruitment Report

## Project Analysis
- **Frontend:** React 18 with TypeScript
- **Backend:** Node.js Express API
- **Database:** PostgreSQL with Prisma ORM
- **Testing:** Jest + React Testing Library
- **DevOps:** Docker + GitHub Actions

## Recommended Team (10 agents)

### Essential (3)
- ✅ context-manager - Shared knowledge management
- ✅ agent-manager - Team coordination
- ✅ multi-agent-orchestrator - Workflow orchestration

### High Priority (4)
- ✅ frontend-developer - React/TypeScript components
- ✅ backend-developer - Express API endpoints
- ✅ database-specialist - PostgreSQL/Prisma management
- ✅ test-engineer - Jest test coverage

### Medium Priority (3)
- ✅ code-reviewer - Quality assurance
- ✅ deployment-engineer - CI/CD and Docker
- ✅ documentation-writer - API and code docs

## Agents Pending Review

All agents prepared in `.claude/agents/pending/`

**Next Steps:**
1. Review each agent template
2. Approve by moving to `.claude/agents/`
3. Run Round 1 specialization
4. Register in communication system
```

### Step 6: Log Recruitment

```python
from audit_logger import AuditLogger

logger = AuditLogger('.')
logger.log(
    'agents_recruited',
    'agent-manager',
    f'Recruited {len(agents)} agents: {", ".join(agent_names)}'
)
```

## Agent Selection Heuristics

### Based on File Patterns

```python
# Frontend indicators
if has_files("src/**/*.tsx") or has_files("src/**/*.jsx"):
    recommend("frontend-developer")

    if has_files("src/components/**"):
        recommend("react-specialist")

# Backend indicators
if has_files("server/**/*.ts") or has_files("api/**/*.py"):
    recommend("backend-developer")

    if has_files("api/routes/**"):
        recommend("api-specialist")

# Database indicators
if has_files("prisma/schema.prisma"):
    recommend("database-specialist")
    recommend_note("Prisma ORM experience preferred")

if has_files("migrations/**"):
    recommend("database-specialist")

# Testing indicators
if has_files("**/*.test.*") or has_files("**/*.spec.*"):
    recommend("test-engineer")

    test_count = count_files("**/*.test.*")
    if test_count < 20:
        priority("high")  # Need more test coverage

# DevOps indicators
if has_files("Dockerfile") or has_files("docker-compose.yml"):
    recommend("deployment-engineer")

if has_files(".github/workflows/**"):
    recommend("devops-specialist")
```

### Based on Project Complexity

```python
# Simple project (< 100 files)
team_size = 6

# Medium project (100-500 files)
team_size = 10

# Large project (> 500 files)
team_size = 14

# Adjust based on file count
total_files = count_files("**/*")
```

### Based on Existing Specs

```python
# Read project specification if exists
if file_exists("specs/requirements.md"):
    spec = read_file("specs/requirements.md")

    # Look for role mentions
    if "payment processing" in spec:
        recommend("payment-integration-specialist")

    if "authentication" in spec:
        recommend("auth-specialist")

    if "real-time" in spec:
        recommend("websocket-engineer")
```

## Best Practices

### 1. Start Small, Scale Up

**Initial Team (6-8):**
- Core coordination (3)
- Primary development (2-3)
- Quality assurance (1-2)

**Expand Later:**
- Add specialists as needs emerge
- Don't over-staff early
- Agents can handle multiple responsibilities initially

### 2. Match to Phase

**Greenfield Project:**
- Focus on developers and architects
- Defer optimization specialists

**Mature Project:**
- Add performance engineers
- Include security auditors
- Expand testing team

### 3. Consider Constraints

**Token Budget:**
- Each agent: ~3000 tokens active
- Team of 12: ~36,000 tokens
- Stay within context limits

**Human Oversight:**
- More agents = more to review
- Keep team manageable
- Quality over quantity

### 4. Validate Templates

Before using, check:
- ✅ Valid YAML frontmatter
- ✅ Has communication protocol
- ✅ Specifies required tools
- ✅ Clear responsibilities
- ✅ No hardcoded secrets

## Common Patterns

### E-Commerce Project

```python
team = [
    "context-manager",
    "agent-manager",
    "multi-agent-orchestrator",
    "frontend-developer",     # Product pages, cart
    "backend-developer",      # API, orders
    "database-specialist",    # Product catalog, orders
    "payment-specialist",     # Stripe integration
    "test-engineer",         # E2E tests
    "security-auditor",      # PCI compliance
    "deployment-engineer"    # Production deployment
]
```

### Internal Tool

```python
team = [
    "context-manager",
    "agent-manager",
    "multi-agent-orchestrator",
    "fullstack-developer",   # Smaller scope
    "database-specialist",   # Data management
    "test-engineer"         # Quality assurance
]
```

### API Service

```python
team = [
    "context-manager",
    "agent-manager",
    "multi-agent-orchestrator",
    "backend-developer",     # Endpoints
    "database-specialist",   # Data layer
    "api-designer",         # OpenAPI spec
    "test-engineer",        # Integration tests
    "performance-engineer", # Load testing
    "documentation-writer"  # API docs
]
```

## Example Usage

```python
# As agent-manager during project initialization:

# 1. Analyze project structure
# Use Glob, Read to understand codebase

# 2. Determine required agents
# Based on files, stack, complexity

# 3. Fetch agent templates
# Local first, then GitHub, then create

# 4. Prepare in pending directory
# .claude/agents/pending/*.md

# 5. Generate recruitment report
# Summary for human review

# 6. Wait for human approval
# Human moves approved agents to .claude/agents/

# 7. Proceed to Round 1 specialization
# Use agent-specialization skill
```

---

**Version:** 1.0
**Requires:** Read, Write, Glob, Grep, WebFetch tools
**Complements:** agent-specialization, agent-training
**Next Step:** After recruitment → agent-specialization (Round 1)
