# Agent Communication Guide

**Version:** 2.0 (New Protocol)
**For Agents:** Context Manager, Frontend Developer, Backend Developer, etc.
**Purpose:** Lightweight, token-efficient reference for agent-to-agent communication

---

## Quick Start

All agents use the **AgentMessenger** API for communication. This replaces the old JSON protocol.

### Basic Setup

```python
from communications.agent_sdk import AgentMessenger

# Initialize once
messenger = AgentMessenger("your-agent-id")

# Send heartbeat (let system know you're active)
messenger.heartbeat("active", "Working on task XYZ")
```

---

## Core Operations

### 1. Send a Message (Fire and Forget)

```python
# Direct message to specific agent
msg_id = messenger.send(
    to="context-manager",
    message_type="context.query",
    data={"query": "Need frontend architecture details"}
)

# Broadcast to all agents in channel
msg_id = messenger.broadcast(
    message_type="announcement",
    data={"message": "Starting deployment process"},
    channel="general",
    priority=8
)
```

### 2. Request/Response Pattern (Ask and Wait)

```python
# Ask a question and wait for answer
response = messenger.ask(
    to="context-manager",
    message_type="context.query",
    data={"query": "What's the current UI framework?"},
    timeout=30  # Wait up to 30 seconds
)

if response:
    context = response['payload']['context']
    # Use the context...
else:
    # Handle timeout
    print("No response received")
```

### 3. Receive and Process Messages

```python
# Get pending messages
messages = messenger.receive(limit=10)

for msg in messages:
    # Try to claim it (prevents duplicate processing)
    if messenger.claim(msg['id']):
        try:
            # Process the message
            if msg['type'] == 'context.query':
                result = handle_query(msg['payload'])

                # Send response
                messenger.reply(msg, {"context": result})

            # Mark as complete
            messenger.complete(msg['id'])
        except Exception as e:
            # Mark as failed
            messenger.complete(msg['id'], error=str(e))
```

---

## Common Message Types

### Context Manager Queries

```python
# Query context
response = messenger.ask(
    "context-manager",
    "context.query",
    {"query": "Frontend development context: architecture, patterns, tools"}
)
```

### Task Coordination

```python
# Claim a task from job board
tasks = messenger.get_tasks(limit=10)
for task in tasks:
    if messenger.claim_task(task['task_id']):
        # Work on it
        messenger.update_task(task['task_id'], "in-progress")

        # Do work...
        result = do_work(task)

        # Complete it
        messenger.complete_task(task['task_id'], result)
        break
```

### Status Updates

```python
# Update your status
messenger.heartbeat("active", "Implementing authentication module")

# Broadcast progress
messenger.broadcast(
    "progress.update",
    {
        "task_id": "task-123",
        "progress": 75,
        "eta": "15 minutes"
    }
)
```

### Voting

```python
# Initiate a vote
messenger.broadcast(
    "vote.initiate",
    {
        "vote_id": "vote-123",
        "topic": "Use TypeScript for new components?",
        "options": ["yes", "no", "defer"],
        "deadline": "2025-11-08T16:00:00Z"
    },
    priority=9
)

# Cast a vote
messenger.send(
    "voting-system",
    "vote.cast",
    {
        "vote_id": "vote-123",
        "choice": "yes",
        "reasoning": "Type safety reduces bugs"
    }
)
```

---

## Channels and Subscriptions

Agents are automatically subscribed to `general` channel. Subscribe to more as needed:

```python
# Subscribe to channels
messenger.subscribe("technical")
messenger.subscribe("urgent")

# Check subscriptions
channels = messenger.channels()
# Returns: ["general", "technical", "urgent"]

# Unsubscribe
messenger.unsubscribe("technical")
```

**Available Channels:**
- `general` - All agents (default)
- `technical` - Technical discussions
- `urgent` - Priority broadcasts
- `review` - Code review requests

---

## Best Practices

### 1. Always Query Context First

Before asking the user questions, query context-manager:

```python
context = messenger.ask(
    "context-manager",
    "context.query",
    {"query": "Project structure and conventions for [your domain]"}
)

# Use context to inform your work
if context:
    framework = context['payload']['context'].get('framework')
    # Proceed with knowledge...
```

### 2. Send Heartbeats Regularly

```python
# Every few minutes or when status changes
messenger.heartbeat("active", "Current task description")
```

### 3. Handle Timeouts Gracefully

```python
response = messenger.ask("context-manager", "context.query", data, timeout=30)

if not response:
    # Fallback: ask user or use defaults
    framework = ask_user("What framework are we using?")
```

### 4. Claim Before Processing

Always claim messages to prevent duplicate work:

```python
messages = messenger.receive()
for msg in messages:
    if messenger.claim(msg['id']):  # Only one agent will succeed
        # Safe to process
        process_message(msg)
        messenger.complete(msg['id'])
```

### 5. Broadcast Important Updates

```python
# Notify all agents when you complete major work
messenger.broadcast(
    "task.completed",
    {
        "task_id": "auth-module",
        "summary": "Authentication system implemented",
        "files_modified": ["src/auth.ts", "tests/auth.test.ts"]
    },
    priority=7
)
```

---

## Error Handling

```python
try:
    response = messenger.ask("context-manager", "context.query", data)
    if not response:
        raise TimeoutError("Context manager didn't respond")

    # Process...
except TimeoutError:
    # Handle timeout
    pass
except Exception as e:
    # Log error and continue
    messenger.heartbeat("degraded", f"Error: {str(e)}")
```

---

## Message Priority Levels

- **10** - Critical (system emergencies)
- **9** - Urgent (votes, critical decisions)
- **8** - High (task claims, important updates)
- **5** - Normal (default, regular communication)
- **3** - Low (informational)
- **1** - Lowest (background tasks)

---

## Resources and Documentation

For detailed implementation:
- **Protocol Spec:** `COMMUNICATION_PROTOCOL_SPEC.md`
- **Examples:** `communications/examples/`
- **Core API:** `communications/core.py`
- **Agent SDK:** `communications/agent_sdk.py`

For project philosophy and patterns:
- **Philosophy:** `resources/finto-philosophy.md`
- **Skill Writing:** `resources/skill-writing-guide.md`
- **Specialization:** `resources/specialization-guidelines.md`

---

## Quick Reference Table

| Operation | Code | Returns |
|-----------|------|---------|
| Send message | `messenger.send(to, type, data)` | `message_id` |
| Broadcast | `messenger.broadcast(type, data)` | `message_id` |
| Ask and wait | `messenger.ask(to, type, data)` | `response` or `None` |
| Receive messages | `messenger.receive(limit=10)` | `List[message]` |
| Claim message | `messenger.claim(msg_id)` | `True/False` |
| Complete message | `messenger.complete(msg_id)` | `None` |
| Reply to message | `messenger.reply(msg, data)` | `message_id` |
| Get tasks | `messenger.get_tasks()` | `List[task]` |
| Claim task | `messenger.claim_task(task_id)` | `True/False` |
| Update task | `messenger.update_task(id, status)` | `None` |
| Heartbeat | `messenger.heartbeat(status)` | `None` |

---

**Token Cost:** This guide is ~500 tokens. Load it once, reference as needed. The actual agent templates should link to this instead of repeating the protocol.

**Note:** This guide replaces all old JSON-based protocol examples. If you see JSON protocol blocks in agent templates, they are outdated.
