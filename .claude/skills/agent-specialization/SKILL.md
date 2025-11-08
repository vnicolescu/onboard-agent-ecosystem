---
name: agent-specialization
description: Specialize agents with project-specific organizational principles and communication protocols. Use this for Round 1 specialization to add lightweight context, communication setup, and team structure to newly recruited agents.
---

# Agent Specialization - Round 1 (Light Touch)

## Purpose

Round 1 specialization provides agents with organizational principles and communication protocols without heavy token overhead. This enables immediate coordination while maintaining efficiency.

## When to Use This Skill

Use this skill when:
- New agents have been recruited and need basic onboarding
- Agents need communication protocol training
- Setting up project context references
- Establishing team structure and coordination patterns

**Do NOT use for:**
- Deep domain training (use agent-training skill for Round 2)
- Company-specific implementation details
- Data source specifics (context-manager handles this)

## Round 1 Specialization Process

### 1. Verify Prerequisites

Before starting Round 1 specialization:

```bash
# Check communication system is initialized
ls .claude/communications/messages.db

# Verify project structure
ls .claude/agents/
ls templates/agents/
```

### 2. Analyze Project Context

Gather essential information:
- Project technology stack
- Key file locations
- Active agents and roles
- Communication channels

### 3. Apply Light Touch Training

For each agent, add **300-500 tokens** covering:

#### A. Project Context References

Add a section to the agent template:

```markdown
## Project Context

**Project:** [Project Name]
**Technologies:** [Key tech stack]
**Specification:** See `[path/to/spec.md]`

**Key Resources:**
- Architecture: `[path/to/architecture.md]`
- API Docs: `[path/to/api-docs/]`
- Configuration: `[path/to/config/]`
```

#### B. Communication Protocol

Essential communication instructions:

```markdown
## Communication Protocol

### Context Manager Queries

Before starting work, query the context-manager:

```python
from communications.agent_sdk import AgentMessenger
messenger = AgentMessenger("your-agent-id")

# Check if context-manager is available
health = messenger.comm.get_agent_health("context-manager")
if health and health['status'] == 'active':
    response = messenger.ask(
        "context-manager",
        "context.query",
        {"query": "What context do I need for [task]?"},
        timeout=30
    )
else:
    # Escalate to user if context-manager unavailable
    print("⚠️ Context manager unavailable - requesting user input")
```

### Job Board Interaction

Check and claim tasks atomically:

```python
# Get available tasks
tasks = messenger.get_tasks(limit=10)

# Claim a task (atomic operation)
for task in tasks:
    if task['priority'] >= 5:  # Filter by priority
        if messenger.claim_task(task['task_id']):
            # Successfully claimed - now work on it
            work_on_task(task)
            messenger.complete_task(task['task_id'], "Done: [result]")
            break
```

### Message Types and Priorities

| Type | Priority | Use Case |
|------|----------|----------|
| `*.urgent` | 9-10 | Critical blockers, security issues |
| `*.query` | 7-8 | Context requests, information needs |
| `*.update` | 5-6 | Status updates, progress reports |
| `*.info` | 3-4 | General information, logs |

### Error Handling

When processing fails, send error responses:

```python
try:
    result = process_request(msg)
    messenger.reply(msg, {"result": result})
    messenger.complete(msg['id'])
except Exception as e:
    # Send error response instead of just failing
    messenger.reply(msg, {
        "error": str(e),
        "type": "processing_failed"
    })
    messenger.complete(msg['id'], error=str(e))
```
```

#### C. Team Structure

Add team awareness:

```markdown
## Team Structure

**Active Agents:**
- `context-manager`: Provides project context and domain knowledge
- `task-distributor`: Assigns and coordinates tasks
- `code-reviewer`: Reviews code quality and standards
- `[other-agents]`: [Their roles]

**Coordination:**
- Subscribe to relevant channels based on your role
- Send heartbeats every 5 minutes during active work
- Escalate blockers to task-distributor
- Report completion to general channel

**Channels:**
- `general`: Broadcasts, announcements, coordination
- `technical`: Technical discussions, architecture decisions
- `urgent`: Critical issues, blockers
- `review`: Code reviews, quality checks
```

#### D. Audit Logging

Add audit requirements:

```markdown
## Audit Trail

Log all significant actions:

```python
# When making decisions
messenger.send(
    "audit-logger",
    "decision.log",
    {
        "agent": messenger.agent_id,
        "decision": "Chose approach X because Y",
        "timestamp": datetime.utcnow().isoformat(),
        "task_id": task_id
    }
)

# When completing work
messenger.broadcast(
    "work.completed",
    {
        "agent": messenger.agent_id,
        "task": task_id,
        "result": result_summary
    },
    channel="general"
)
```
```

### 4. Validate Specialization

Before deploying:

**Quality Checks:**
- [ ] Communication protocol correct and complete
- [ ] All file path references exist (no hallucinations)
- [ ] Token budget within 300-500 tokens
- [ ] No business logic embedded in agent
- [ ] Audit logging instructions clear
- [ ] Health check pattern included
- [ ] Error handling pattern included

### 5. Deploy to Pending Folder

Save specialized agents to `.claude/agents/pending/` for human review:

```python
# Save specialized agent
agent_path = Path(".claude/agents/pending") / f"{agent_name}.md"
agent_path.parent.mkdir(parents=True, exist_ok=True)
agent_path.write_text(specialized_agent_content)

print(f"✅ Created: {agent_path}")
print("📋 Please review and move to .claude/agents/ to activate")
```

## What NOT to Include in Round 1

**❌ Don't add these (wait for Round 2):**
- Detailed coding standards
- API integration patterns
- Database schemas
- Company-specific conventions
- Implementation specifics
- Deep domain knowledge

**Why?** These add significant token overhead and should only be added during Round 2 deep training, after the communication system is proven and agents are functioning.

## Example: Before and After

### Before Round 1 (Template Only)

```markdown
---
name: frontend-developer
description: Senior frontend developer
---

You are a senior frontend developer specializing in React...
```

### After Round 1 (Specialized)

```markdown
---
name: frontend-developer
description: Senior frontend developer
---

You are a senior frontend developer specializing in React...

## Project Context

**Project:** E-commerce Checkout
**Technologies:** React, Next.js, TypeScript, Tailwind
**Specification:** See `specs/checkout-blueprint.md`

## Communication Protocol

Before starting work, query context-manager:
[communication instructions as above]

## Team Structure

**Active Agents:**
- context-manager: Project context
- backend-developer: API integration
- code-reviewer: Code quality
[team structure as above]
```

## Verification Commands

After specialization, verify:

```bash
# Check token count (should be ~300-500 added)
wc -w .claude/agents/pending/*.md

# Validate references
for file in $(grep -o '`[^`]*\.md`' .claude/agents/pending/*.md | tr -d '`'); do
  test -f "$file" && echo "✅ $file" || echo "❌ $file MISSING"
done

# Check no hardcoded secrets
grep -i "password\|secret\|api_key" .claude/agents/pending/*.md
```

## Next Steps

After Round 1 specialization:
1. Human reviews agents in `.claude/agents/pending/`
2. Human moves approved agents to `.claude/agents/`
3. Agents become active and start coordinating
4. After system is stable, proceed to Round 2 deep training using `agent-training` skill

## Resources

- See `resources/specialization-guidelines.md` for detailed guidelines
- See `resources/agent-communication-guide.md` for protocol details
- See `communications/agent_sdk.py` for API reference

---
**Version:** 1.0
**Token Budget:** 300-500 tokens per agent
**Prerequisite:** Communication system initialized
