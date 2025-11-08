# Quick Start Guide

## Initialize the System

```python
from communications import CommunicationSystem

comm = CommunicationSystem(".")  # Project root
comm.initialize()
```

This creates:
- `.claude/communications/messages.db` - SQLite database
- All necessary tables with proper indexes
- Default channels (general, urgent, technical, review)

## For Agents: Use the Simple API

```python
from communications import AgentMessenger

# Initialize
messenger = AgentMessenger("my-agent-id")

# Send a message
messenger.send("other-agent", "context.query", {"query": "What framework?"})

# Ask and wait for response (request/response pattern)
response = messenger.ask("context-manager", "context.query", {"query": "..."}, timeout=30)
if response:
    print(response['payload'])

# Receive and process messages
messages = messenger.receive(limit=10)
for msg in messages:
    if messenger.claim(msg['id']):  # Try to claim it
        # Process it
        result = do_work(msg)

        # Reply if needed
        messenger.reply(msg, {"result": result})

        # Mark as done
        messenger.complete(msg['id'])

# Broadcast to all
messenger.broadcast("vote.initiate", {
    "topic": "Use TypeScript?",
    "options": ["yes", "no"]
})

# Job board
tasks = messenger.get_tasks()
for task in tasks:
    if messenger.claim_task(task['task_id']):
        # Do the work
        messenger.update_task(task['task_id'], "in-progress")
        result = do_task(task)
        messenger.complete_task(task['task_id'], result)
```

## Run Examples

```bash
# Example 1: Simple request/response
python communications/examples/01_simple_request_response.py

# Example 2: Broadcast voting
python communications/examples/02_broadcast_vote.py

# Example 3: Job board with workers
python communications/examples/03_job_board_worker.py
```

## Run Tests

```bash
python communications/tests/test_core_fixes.py
```

All tests should pass:
- ✓ Atomic message claiming
- ✓ Broadcast delivery to multiple agents
- ✓ Subscription-based routing
- ✓ Atomic job board operations
- ✓ Correlation ID uniqueness
- ✓ Exponential backoff
- ✓ Message expiration

## Key Features

✅ **Thread-safe**: Multiple agents can work concurrently
✅ **Atomic operations**: No race conditions, guaranteed
✅ **Broadcast support**: Same message delivered to all subscribed agents
✅ **Request/response**: Built-in correlation ID handling
✅ **Job board**: Transactional task claiming
✅ **Transparent errors**: Clear error messages
✅ **Low overhead**: <200 tokens per agent

## Next Steps

1. Read `communications/README.md` for detailed guide
2. Look at examples in `communications/examples/`
3. Integrate into your agents
4. Monitor with SQL queries to `messages.db`

## Troubleshooting

**"Database locked"**: Rare with WAL mode, should auto-retry
**"Message already claimed"**: Normal - another agent was faster
**"No messages"**: Check subscriptions with `messenger.channels()`

For more help, see the full README.md
