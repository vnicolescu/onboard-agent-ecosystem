# Communication System - Agent Guide

**A simple, transparent messaging system for multi-agent coordination.**

## Quick Start

```python
from communications import AgentMessenger

# Initialize (only need agent ID)
messenger = AgentMessenger("my-agent-id")

# Send a message
messenger.send("other-agent", "task.update", {"status": "done"})

# Receive messages
messages = messenger.receive()
for msg in messages:
    if messenger.claim(msg['id']):
        print(f"Got: {msg['payload']}")
        messenger.complete(msg['id'])
```

That's it! Everything else is handled for you.

---

## Core Concepts

### 1. Messages

Every message has:
- **type**: What kind of message (e.g., "context.query", "task.update")
- **payload**: Your data (Python dict)
- **from_agent**: Who sent it
- **to_agent**: Who receives it (or None for broadcast)
- **channel**: Where it goes (usually "general")
- **priority**: 1-10, higher = more urgent

### 2. Channels

Think of channels like Slack channels:
- `general`: Default, everyone sees it
- `urgent`: Critical alerts only
- `technical`: Technical discussions
- `review`: Code/design reviews

You're auto-subscribed to `general`. Subscribe to others as needed:
```python
messenger.subscribe("urgent")
```

### 3. Broadcasts

Send to everyone on a channel:
```python
messenger.broadcast("vote.initiate", {
    "topic": "Use TypeScript?",
    "options": ["yes", "no"]
})
```

**Every subscribed agent will receive it** (unlike direct messages).

---

## Common Patterns

### Pattern 1: Fire and Forget

Just send a message, don't wait for response:

```python
messenger.send(
    "task-distributor",
    "task.update",
    {"task_id": "123", "status": "done"}
)
```

### Pattern 2: Request/Response

Ask a question and wait for answer:

```python
response = messenger.ask(
    "context-manager",
    "context.query",
    {"query": "What frontend framework?"},
    timeout=30
)

if response:
    context = response['payload']['context']
    print(f"Framework: {context['framework']}")
else:
    print("No response (timeout)")
```

The `.ask()` method handles:
- Correlation IDs
- Waiting with exponential backoff
- Timeout handling
- Claiming and completing the response

### Pattern 3: Processing Messages

Receive and process multiple messages:

```python
# Get messages
messages = messenger.receive(limit=10)

for msg in messages:
    # Try to claim it (might already be claimed by another agent)
    if messenger.claim(msg['id']):
        try:
            # Process it
            if msg['type'] == 'context.query':
                result = get_context(msg['payload']['query'])
                messenger.reply(msg, {"context": result})

            # Mark as done
            messenger.complete(msg['id'])

        except Exception as e:
            # Mark as failed
            messenger.complete(msg['id'], error=str(e))
```

### Pattern 4: Responding to Requests

When you receive a request, reply to it:

```python
messages = messenger.receive()
for msg in messages:
    if messenger.claim(msg['id']):
        if msg['type'] == 'context.query':
            # Get the answer
            context = retrieve_context(msg['payload']['query'])

            # Send response (correlation ID handled automatically)
            messenger.reply(msg, {"context": context})

            # Mark original message as complete
            messenger.complete(msg['id'])
```

### Pattern 5: Broadcasting to Multiple Agents

Announce something to all agents:

```python
# Vote
messenger.broadcast("vote.initiate", {
    "vote_id": "vote-001",
    "topic": "Should we refactor the API?",
    "options": ["yes", "no", "later"],
    "deadline": "2025-11-08T17:00:00Z"
})

# Wait for votes
votes = messenger.wait_for_messages(
    message_type="vote.cast",
    timeout=300  # 5 minutes
)

print(f"Received {len(votes)} votes")
```

---

## Job Board Integration

Claim and work on tasks:

```python
# See available tasks
tasks = messenger.get_tasks()

for task in tasks:
    # Try to claim it
    if messenger.claim_task(task['task_id']):
        print(f"Claimed: {task['title']}")

        # Update status
        messenger.update_task(task['task_id'], "in-progress")

        # Do the work
        result = do_work(task)

        # Mark as complete
        messenger.complete_task(task['task_id'], result)
        break
```

**Atomicity guarantee:** Only ONE agent can claim a task. The database ensures this.

---

## Heartbeats

Let the system know you're alive:

```python
# Every 30 seconds or so
messenger.heartbeat("active", task="Processing frontend components")

# If idle
messenger.heartbeat("idle")

# If something's wrong
messenger.heartbeat("degraded", task="Retrying failed operation")
```

---

## Error Handling

The system gives clear error messages:

```python
from communications import CommunicationError, MessageNotFoundError, AlreadyClaimedError

try:
    messenger.claim(message_id)
except MessageNotFoundError:
    print("Message doesn't exist (maybe expired?)")
except AlreadyClaimedError:
    print("Another agent claimed it first")
except CommunicationError as e:
    print(f"Communication error: {e}")
```

---

## Message Types

Standard types (feel free to add your own):

| Type | Purpose | Payload Example |
|------|---------|----------------|
| `context.query` | Request context | `{"query": "Frontend stack"}` |
| `context.response` | Return context | `{"context": {...}}` |
| `task.claim` | Claim a task | `{"task_id": "123"}` |
| `task.update` | Update task status | `{"task_id": "123", "status": "done"}` |
| `vote.initiate` | Start a vote | `{"topic": "...", "options": [...]}` |
| `vote.cast` | Cast a vote | `{"vote_id": "...", "option": "yes"}` |
| `broadcast` | General announcement | `{"message": "System restarting in 5 min"}` |
| `heartbeat` | Health check | `{"status": "active"}` |

---

## Artifacts (Large Data)

For big files (>10KB), use artifacts instead of payload:

```python
import json
from pathlib import Path

# Write artifact
artifact_dir = Path(".claude/artifacts") / messenger.agent_id
artifact_dir.mkdir(parents=True, exist_ok=True)

artifact_path = artifact_dir / "result.json"
with open(artifact_path, 'w') as f:
    json.dump(large_data, f)

# Send message with reference
messenger.reply(original_msg, {
    "summary": "Processed 10,000 records",
    "artifact_path": str(artifact_path)
})

# Receiver reads artifact
if 'artifact_path' in response['payload']:
    with open(response['payload']['artifact_path']) as f:
        data = json.load(f)
```

---

## Best Practices

### ✅ Do:

1. **Check messages before starting work**
   ```python
   messages = messenger.receive()
   # Process messages before doing anything else
   ```

2. **Always claim before processing**
   ```python
   if messenger.claim(msg['id']):
       process(msg)
   ```

3. **Always complete after processing**
   ```python
   messenger.complete(msg['id'])  # or complete(msg['id'], error="...")
   ```

4. **Use appropriate priority**
   - 1-3: Low priority, background tasks
   - 4-6: Normal operations
   - 7-9: Important, needs attention
   - 10: Critical, urgent

5. **Send heartbeats regularly**
   ```python
   # Every 30 seconds
   messenger.heartbeat("active")
   ```

6. **Use .ask() for request/response**
   ```python
   response = messenger.ask("other-agent", "query", {...})
   ```

### ❌ Don't:

1. **Don't process without claiming**
   ```python
   # BAD
   for msg in messages:
       process(msg)  # Might be claimed by another agent!

   # GOOD
   for msg in messages:
       if messenger.claim(msg['id']):
           process(msg)
   ```

2. **Don't forget to complete**
   ```python
   # BAD
   if messenger.claim(msg['id']):
       process(msg)
       # Forgot to complete! Message stays in 'processing' forever

   # GOOD
   if messenger.claim(msg['id']):
       try:
           process(msg)
           messenger.complete(msg['id'])
       except Exception as e:
           messenger.complete(msg['id'], error=str(e))
   ```

3. **Don't abuse urgent priority**
   ```python
   # BAD
   messenger.send("other", "task.update", {...}, priority=10)  # Not urgent!

   # GOOD
   messenger.send("other", "task.update", {...}, priority=5)  # Normal
   ```

4. **Don't block the main loop**
   ```python
   # BAD
   while True:
       messages = messenger.receive()
       time.sleep(10)  # Too long!

   # GOOD
   while True:
       messages = messenger.receive()
       time.sleep(0.5)  # Quick polling
   ```

---

## Debugging

### Check message status:

```python
import sqlite3

conn = sqlite3.connect(".claude/communications/messages.db")
cursor = conn.cursor()

# See all pending messages
cursor.execute("SELECT * FROM messages WHERE status = 'pending'")
for row in cursor.fetchall():
    print(row)

# See agent health
cursor.execute("SELECT * FROM agent_status")
for row in cursor.fetchall():
    print(row)
```

### Check subscriptions:

```python
channels = messenger.channels()
print(f"Subscribed to: {channels}")
```

### Check health:

```python
health = messenger.health()
print(f"Status: {health['status']}")
print(f"Pending: {health['messages_pending']}")
print(f"Processed: {health['messages_processed']}")
```

---

## Performance

The system is designed for:
- **20+ concurrent agents**
- **100+ messages/minute throughput**
- **<10ms message latency** (p95)
- **<200 tokens overhead** per agent

**Benchmarks:**
- Send message: ~2ms
- Receive messages: ~5ms
- Claim message: ~3ms (atomic, thread-safe)
- Request/response cycle: ~15ms

---

## Architecture Notes

For the curious (you don't need to know this to use the system):

- **Storage:** SQLite in WAL mode for concurrency
- **Atomicity:** Database transactions ensure no race conditions
- **Broadcasts:** Tracked with delivery table, each agent gets a copy
- **Rate limiting:** Token bucket (100 tokens, 10/sec refill)
- **Retries:** Failed messages auto-retry 3 times, then move to dead letter queue
- **Expiration:** Messages can have TTL, auto-cleaned up

---

## Need Help?

Common issues:

**"Message already claimed"**
- Another agent was faster. This is normal. Try the next message.

**"Timeout waiting for response"**
- Recipient might be offline. Check agent health.
- Increase timeout: `messenger.ask(..., timeout=60)`

**"No messages received"**
- Check if you're subscribed: `messenger.channels()`
- Check if messages exist: `messenger.receive(limit=50)`

**"Database locked"**
- Should be rare with WAL mode. If persistent, check for long-running transactions.

---

## Examples

See `communications/examples/` for complete examples:
- `simple_request_response.py` - Basic request/response
- `broadcast_vote.py` - Voting pattern
- `job_board_worker.py` - Task processing
- `context_manager_simulation.py` - Full context manager example

---

**Remember:** Keep it simple. Send, receive, claim, complete. That's the pattern.
