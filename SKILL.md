---
name: project-onboard
description: Initialize multi-agent team for any project with complete infrastructure. Creates agents, communication system, job board, and audit trail. Use when starting a new project or initializing agent coordination for existing projects.
---

# Project Team Onboarding

Transforms any project into a coordinated multi-agent system with self-organizing specialists, communication infrastructure, and 100% traceability.

## Philosophy

This skill embodies organic, seed-like initialization:
- **Progressive specialization** - agents refine themselves for the project
- **Self-organizing** - experts coordinate without micromanagement  
- **Traceable** - complete audit trail of all decisions and actions
- **Adaptive** - system learns and improves
- **Human-in-loop** - critical decisions involve human oversight

## Quick Start

From your project root directory:

```bash
# Initialize team onboarding
python scripts/analyze_project.py > project-context.json
```

Then follow the systematic workflow below.

## Onboarding Workflow

### Phase 1: Project Analysis

Run project analyzer:
```bash
python scripts/analyze_project.py . > /tmp/project-context.json
cat /tmp/project-context.json
```

Review output for:
- Project name and technologies
- Existing specifications
- Recommended agents
- Initial task breakdown

**Decision:** Create spec if needed, otherwise proceed to Phase 2.

---

### Phase 2: Communication Infrastructure

Initialize systems:
```bash
# Communication system (NEW)
python -c "
from communications.core import CommunicationSystem
comm = CommunicationSystem('.')
result = comm.initialize()
print('✓ Communication system initialized')
print(f'Database: {result[\"db_path\"]}')
print(f'Artifacts: {result[\"artifacts_dir\"]}')
"

# Job board
python scripts/create_job_board.py init

# Audit trail
mkdir -p .claude
touch .claude/audit-trail.jsonl
```

Verify:
```bash
ls .claude/communications/
# Should see: messages.db, protocol_version.txt

ls .claude/
# Should see: communications/, job-board.json, audit-trail.jsonl
```

---

### Phase 3: Agent Recruitment

Recruit and deploy agents:
```bash
# Get recommended agents from context
AGENTS=$(cat /tmp/project-context.json | jq -r '.recommended_agents[:12] | join(",")')

# Recruit from GitHub or create
python scripts/recruit_agents.py "$AGENTS" /tmp/project-context.json

# Specialize (Round 1)
python scripts/specialize_agents.py /tmp/project-context.json "$AGENTS" 1
```

Review pending agents:
```bash
ls .claude/agents/pending/
# Review each file, verify communication protocols added
```

Approve agents:
```bash
# After review, activate
mv .claude/agents/pending/* .claude/agents/
```

---

### Phase 4: Team Registration

Register agents in communication system:
```python
from pathlib import Path
from communications.core import CommunicationSystem

comm = CommunicationSystem('.')

# Auto-subscribe agents to default channels
for agent_file in Path('.claude/agents').glob('*.md'):
    agent_name = agent_file.stem

    # Subscribe to channels
    comm.subscribe_to_channel(agent_name, "general")
    comm.subscribe_to_channel(agent_name, "technical")

    # Register with heartbeat
    comm.send_heartbeat(agent_name, "registered", "Ready for tasks")

    print(f"Registered: {agent_name}")
```

---

### Phase 5: Initial Tasks

Create tasks from project requirements:
```python
from create_job_board import JobBoard

board = JobBoard('.')

# Example tasks
tasks = [
    {
        "title": "Set up project infrastructure",
        "description": "Initialize build system and testing",
        "priority": "critical"
    },
    # Add more tasks based on project spec
]

for task in tasks:
    task_id = board.create_task(**task)
    print(f"Created: {task_id}")
```

---

### Phase 6: Team Briefing

Broadcast coordination protocol:
```python
from communications.core import CommunicationSystem

comm = CommunicationSystem('.')

protocol_msg = {
    "welcome": "Team initialized successfully!",
    "protocol": {
        "before_work": [
            "Use AgentMessenger to receive messages",
            "Query context-manager for project state",
            "Check job board for available tasks"
        ],
        "during_work": [
            "Claim task from job board",
            "Send heartbeats regularly",
            "Log decisions to audit trail",
            "Broadcast blockers immediately"
        ],
        "escalation": {
            "conflicts": "Human decision required",
            "security": "Human review required",
            "architecture": "Use voting protocol"
        }
    },
    "resources": {
        "communication": "resources/agent-communication-guide.md",
        "voting": "resources/voting-protocols.md",
        "specialization": "resources/specialization-guidelines.md",
        "skills": "resources/skill-writing-guide.md"
    }
}

# Broadcast to all agents
comm.send_message(
    from_agent="system",
    message_type="system.welcome",
    payload=protocol_msg,
    channel="general",
    priority=9
)

print("✓ Team briefing broadcast to all agents")
```

---

### Phase 7: First Coordination

Test the system:
```python
# Agent claims task
available = board.get_available_tasks()
board.assign_task(available[0]['id'], 'backend-dev-01')

# Agent logs work
from audit_logger import AuditLogger
logger = AuditLogger('.')
logger.log('task_updated', 'backend-dev-01', 'Started infrastructure setup')

# Agent completes work
board.update_status(available[0]['id'], 'done', 'backend-dev-01')
```

Verify in audit trail, job board, and messages.

---

## System Architecture

```
.claude/
├── agents/                    # Specialized agents
│   └── pending/              # Awaiting approval
├── skills/                   # Agent-created skills  
│   └── pending/             # Awaiting approval
├── communications/          # Messaging system
│   ├── urgent/
│   ├── channels/
│   ├── direct/
│   └── messages.db
├── job-board.json          # Task management
├── audit-trail.jsonl       # Complete history
└── agent-registry.json     # Agent directory
```

---

## Advanced Operations

### Round 2 Specialization

After project progresses, agent-manager can provide deep training:
```bash
python scripts/specialize_agents.py /tmp/project-context.json "$AGENTS" 2
```

See `resources/specialization-guidelines.md` for details.

### Agent Skill Creation

When agents identify reusable patterns:
1. Propose skill in `.claude/skills/proposals/`
2. Create skill in `.claude/skills/pending/`  
3. Human reviews and approves
4. Move to `.claude/skills/` to activate

See `resources/skill-writing-guide.md` for guidelines.

### Voting & Consensus

For conflicting decisions:
1. Initiate vote via communication system
2. Follow voting-protocols.md procedures
3. Document outcome in audit trail
4. Execute winning decision

---

## Troubleshooting

**Agent not receiving messages:**
```bash
# Check registration
cat .claude/agent-registry.json | jq '.agents'
```

**Tasks not appearing:**
```bash
python scripts/create_job_board.py stats
```

**Audit trail not logging:**
```bash
python scripts/audit_logger.py log test_event system "Test"
tail .claude/audit-trail.jsonl
```

---

## Success Checklist

Onboarding complete when:
- [ ] .claude/ structure created
- [ ] 8-12 agents deployed
- [ ] Communication system active
- [ ] Job board has tasks
- [ ] Audit trail logging
- [ ] First task claimed and started
- [ ] Team coordination verified

---

## Reference Documents

In `resources/`:
- `specialization-guidelines.md` - Agent training  
- `voting-protocols.md` - Decision-making
- `skill-writing-guide.md` - Skill creation

---

**Remember:** This is a seed that unfolds organically. Start simple, let specialization emerge, trust coordination protocols, and maintain the audit trail.

**Human role:** Gardener, not micromanager. Approve key decisions, review audit trail, but let agents self-organize.

Now initialize your team! 🚀
