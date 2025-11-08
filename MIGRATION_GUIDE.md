# Migration Guide: Current → New Communication Protocol

**Goal:** Replace broken implementation with working protocol while preserving audit trail and job board.

---

## Current State Assessment

### What's Broken

1. **setup_communication.py** - Protocol mismatch (text-only vs JSON)
2. **Agent templates** - Expect JSON protocol that doesn't exist
3. **SQLite queries** - Reference non-existent `channels` table
4. **No request/response** - Correlation IDs unused
5. **No concurrency control** - Race conditions on writes
6. **No rate limiting** - Can spam unlimited messages
7. **No circuit breakers** - Failures cascade

### What's Working (Keep These)

✅ `.claude/audit-trail.jsonl` - Audit system  
✅ `.claude/job-board.json` - Task management  
✅ `.claude/agent-registry.json` - Agent directory  
✅ Directory structure - `.claude/` organization  

---

## Migration Strategy

### Phase 1: Parallel Deployment (No Breaking Changes)

1. Install new system alongside old
2. Test with 2-3 agents
3. Validate nothing breaks
4. Keep old system as fallback

### Phase 2: Agent Migration (Gradual)

1. Update context-manager first (most critical)
2. Update meta-orchestrators (agent-manager, multi-agent-orchestrator)
3. Update specialist agents (frontend-dev, backend-dev, etc.)
4. Verify each migration step

### Phase 3: Cleanup (After Validation)

1. Remove old `setup_communication.py`
2. Update all documentation
3. Archive old message files
4. Celebrate 🎉

---

## Step-by-Step Migration

### Step 1: Install New System (Day 1 Morning)

```bash
cd .claude/

# Create new directory structure
mkdir -p communications
mkdir -p artifacts

# Copy new implementation
cp /path/to/new/communications/* communications/

# Initialize database
python -c "
from communications.core import CommunicationSystem
comm = CommunicationSystem('.')
comm.initialize()
print('✓ Communication system initialized')
"

# Verify
ls -la communications/
# Should see: messages.db, messages.db-shm, messages.db-wal, __init__.py, core.py, etc.
```

### Step 2: Test New System in Isolation (Day 1 Afternoon)

```python
# test_new_system.py
from communications.core import CommunicationSystem

def test_basic_flow():
    """Verify new system works."""
    comm = CommunicationSystem('.')
    
    # Send message
    msg_id = comm.send_message(
        from_agent="test-agent-01",
        message_type="test.ping",
        payload={"message": "Hello new system"},
        channel="general"
    )
    print(f"✓ Sent message: {msg_id}")
    
    # Receive message
    messages = comm.receive_messages("test-agent-02", ["general"])
    assert len(messages) == 1
    print(f"✓ Received message")
    
    # Claim message
    claimed = comm.claim_message("test-agent-02", messages[0]['id'])
    assert claimed
    print(f"✓ Claimed message")
    
    # Complete message
    comm.complete_message(messages[0]['id'])
    print(f"✓ Completed message")
    
    print("\n✓ All basic operations work!")

if __name__ == "__main__":
    test_basic_flow()
```

Run test:
```bash
python test_new_system.py
```

Expected output:
```
✓ Sent message: 550e8400-e29b-41d4-a716-446655440000
✓ Received message
✓ Claimed message
✓ Completed message

✓ All basic operations work!
```

### Step 3: Update Context Manager (Day 1 Evening)

**Before (context-manager.md):**

```markdown
## Communication Protocol

### Initial Context Assessment

Context query:
```json
{
  "requesting_agent": "context-manager",
  "request_type": "get_context",
  "payload": {
    "query": "..."
  }
}
```
```

**After (context-manager.md):**

```markdown
## Communication Protocol

This agent uses the CommunicationSystem for coordination.

### Handling Context Queries

```python
from communications.core import CommunicationSystem

comm = CommunicationSystem('.')
agent_id = "context-manager"

# Send heartbeat
comm.send_heartbeat(agent_id, "active")

# Main loop
while True:
    # Check for queries
    messages = comm.receive_messages(agent_id, ["general"])
    
    for msg in messages:
        if msg['type'] == 'context.query':
            # Claim message
            if comm.claim_message(agent_id, msg['id']):
                try:
                    # Process query
                    query = msg['payload']['query']
                    context_data = retrieve_context(query)
                    
                    # Send response
                    comm.send_response(
                        original_message=msg,
                        response_payload={"context": context_data}
                    )
                    
                    # Mark complete
                    comm.complete_message(msg['id'])
                except Exception as e:
                    comm.complete_message(msg['id'], error=str(e))
    
    time.sleep(0.5)  # Poll every 500ms
```
```

### Step 4: Update Agent Templates (Day 2 Morning)

**Template for all agents:**

Add this to the "Communication Protocol" section:

```markdown
## Communication Protocol

### Using the Communication System

```python
from communications.core import CommunicationSystem
import uuid

# Initialize
comm = CommunicationSystem('.')

# Query context manager
correlation_id = str(uuid.uuid4())
comm.send_message(
    from_agent="{agent-id}",
    message_type="context.query",
    payload={"query": "Context needed for {role}"},
    to_agent="context-manager",
    correlation_id=correlation_id
)

# Wait for response
response = comm.wait_for_response(
    agent_id="{agent-id}",
    correlation_id=correlation_id,
    channels=["general"],
    timeout_seconds=30
)

if response:
    context = response['payload']['context']
    # Use context...
```

### Update job board interaction
```python
# Claim task
comm.send_message(
    from_agent="{agent-id}",
    message_type="task.claim",
    payload={"task_id": task_id},
    channel="general"
)

# Update task status
comm.send_message(
    from_agent="{agent-id}",
    message_type="task.update",
    payload={
        "task_id": task_id,
        "status": "in-progress",
        "progress": 50
    },
    channel="general"
)
```
```

**Agents to update:**
- agent-manager.md
- multi-agent-orchestrator.md
- frontend-developer.md
- backend-developer.md (if exists)
- code-reviewer.md
- task-distributor.md
- All other agent templates

### Step 5: Integration Test (Day 2 Afternoon)

```python
# test_integration.py
from communications.core import CommunicationSystem
from threading import Thread
import time
import uuid

def test_context_manager_integration():
    """Test real context-manager interaction."""
    comm = CommunicationSystem('.')
    
    # Simulate context-manager in thread
    def context_manager_loop():
        time.sleep(0.1)  # Let requester send first
        messages = comm.receive_messages("context-manager", ["general"])
        
        for msg in messages:
            if msg['type'] == 'context.query':
                if comm.claim_message("context-manager", msg['id']):
                    comm.send_response(
                        original_message=msg,
                        response_payload={
                            "context": {"framework": "React", "version": "18"}
                        }
                    )
                    comm.complete_message(msg['id'])
    
    # Start context manager
    Thread(target=context_manager_loop, daemon=True).start()
    
    # Requester
    correlation_id = str(uuid.uuid4())
    comm.send_message(
        from_agent="frontend-dev-01",
        message_type="context.query",
        payload={"query": "Frontend framework"},
        to_agent="context-manager",
        correlation_id=correlation_id
    )
    
    # Wait for response
    response = comm.wait_for_response(
        agent_id="frontend-dev-01",
        correlation_id=correlation_id,
        channels=["general"],
        timeout_seconds=5
    )
    
    assert response is not None, "No response received"
    assert response['payload']['context']['framework'] == "React"
    
    print("✓ Context manager integration works!")

if __name__ == "__main__":
    test_context_manager_integration()
```

### Step 6: Load Test (Day 2 Evening)

```python
# test_load.py
from communications.core import CommunicationSystem
from threading import Thread
import time
import uuid

def simulate_agent(agent_id, duration_seconds=10):
    """Simulate agent sending messages."""
    comm = CommunicationSystem('.')
    start = time.time()
    count = 0
    
    while time.time() - start < duration_seconds:
        # Send message
        comm.send_message(
            from_agent=agent_id,
            message_type="test.load",
            payload={"timestamp": time.time()},
            channel="general"
        )
        count += 1
        time.sleep(0.1)  # 10 msg/sec per agent
    
    return count

def test_load():
    """Test with 20 agents for 10 seconds."""
    comm = CommunicationSystem('.')
    
    # Start 20 agents
    threads = []
    for i in range(20):
        t = Thread(target=simulate_agent, args=(f"agent-{i:02d}",))
        t.start()
        threads.append(t)
    
    # Wait for completion
    for t in threads:
        t.join()
    
    # Check results
    cursor = comm.connection.execute("""
        SELECT COUNT(*) FROM messages 
        WHERE type = 'test.load'
    """)
    count = cursor.fetchone()[0]
    
    print(f"✓ Processed {count} messages")
    print(f"✓ Throughput: {count/10:.1f} messages/second")
    
    # Verify no errors
    cursor = comm.connection.execute("""
        SELECT COUNT(*) FROM messages 
        WHERE status = 'failed'
    """)
    errors = cursor.fetchone()[0]
    
    assert errors == 0, f"Found {errors} failed messages"
    print(f"✓ Zero failures!")

if __name__ == "__main__":
    test_load()
```

Expected output:
```
✓ Processed 2000 messages
✓ Throughput: 200.0 messages/second
✓ Zero failures!
```

### Step 7: Monitoring Setup (Day 3 Morning)

Create monitoring script:

```python
# monitor_system.py
from communications.core import CommunicationSystem
import time

def monitor():
    """Display real-time system health."""
    comm = CommunicationSystem('.')
    
    while True:
        # Queue depth
        cursor = comm.connection.execute("""
            SELECT status, COUNT(*) 
            FROM messages 
            GROUP BY status
        """)
        status_counts = dict(cursor.fetchall())
        
        # Agent health
        cursor = comm.connection.execute("""
            SELECT COUNT(*), 
                   COUNT(CASE WHEN datetime(last_heartbeat) > datetime('now', '-1 minute') THEN 1 END)
            FROM agent_status
        """)
        total_agents, active_agents = cursor.fetchone()
        
        # DLQ
        cursor = comm.connection.execute("SELECT COUNT(*) FROM dead_letter_queue")
        dlq_count = cursor.fetchone()[0]
        
        # Display
        print("\n=== System Health ===")
        print(f"Queue: {status_counts}")
        print(f"Agents: {active_agents}/{total_agents} active")
        print(f"DLQ: {dlq_count} messages")
        print("=====================\n")
        
        time.sleep(5)

if __name__ == "__main__":
    monitor()
```

Run in separate terminal:
```bash
python monitor_system.py
```

### Step 8: Cleanup Old System (Day 3 Afternoon)

**Only after everything works!**

```bash
cd .claude/

# Archive old implementation
mkdir -p archive/old-communication
mv setup_communication.py archive/old-communication/
mv communications/PROTOCOL.md archive/old-communication/ 2>/dev/null || true

# Remove old message files (if any)
rm -rf communications/urgent/
rm -rf communications/channels/
rm -rf communications/direct/

# Keep: audit-trail.jsonl, job-board.json, agent-registry.json
```

### Step 9: Update Documentation (Day 3 Evening)

Update these files:

**README.md:**
```markdown
## Communication System

Uses SQLite-based message broker for agent coordination.

**Key features:**
- Request/response with correlation IDs
- Rate limiting (100 msg/min per agent)
- Circuit breakers for failure protection
- 100% audit trail
- <200 token overhead

**Usage:**
See `.claude/communications/` for implementation.
```

**SKILL.md:**
```markdown
## Phase 2: Communication Infrastructure

Initialize systems:
```bash
# Communication system (NEW)
python -c "
from communications.core import CommunicationSystem
comm = CommunicationSystem('.')
comm.initialize()
"

# Job board (existing)
python scripts/create_job_board.py init

# Audit trail (existing)
mkdir -p .claude
touch .claude/audit-trail.jsonl
```
```

---

## Rollback Plan

If something breaks:

```bash
cd .claude/

# Restore old setup
mv archive/old-communication/setup_communication.py .

# Remove new system
rm -rf communications/

# Reinitialize old system
python setup_communication.py .
```

---

## Validation Checklist

Before declaring migration complete:

- [ ] New database exists and has schema
- [ ] Context manager responds to queries
- [ ] 3+ agents can coordinate
- [ ] Request/response works with correlation IDs
- [ ] Load test passes (20 agents, 1000 messages)
- [ ] No race conditions detected
- [ ] Rate limiting enforces limits
- [ ] Circuit breakers trigger correctly
- [ ] Audit trail still logging
- [ ] Job board still working
- [ ] Agent registry preserved
- [ ] No data loss during migration
- [ ] Old system archived
- [ ] Documentation updated
- [ ] Team knows how to use new system

---

## Common Migration Issues

### Issue 1: "Database is locked"

**Symptom:** `sqlite3.OperationalError: database is locked`

**Fix:**
```python
# Increase timeout
conn.execute("PRAGMA busy_timeout=10000")

# Verify WAL mode
cursor = conn.execute("PRAGMA journal_mode")
print(cursor.fetchone())  # Should be 'wal'
```

### Issue 2: Agents not receiving messages

**Symptom:** Messages sent but never received

**Debug:**
```sql
SELECT * FROM messages WHERE status = 'pending';
```

**Fix:** Verify agents subscribing to correct channels

### Issue 3: Old code still referencing old system

**Symptom:** Import errors or attribute errors

**Find all references:**
```bash
grep -r "setup_communication" .
grep -r "CommunicationSystem" . | grep -v ".claude/communications"
```

**Fix:** Update imports to new location

---

## Performance Comparison

### Before (Broken System)
- Protocol mismatch ❌
- No concurrency control ❌
- Race conditions ❌
- No rate limiting ❌
- Throughput: 0 msg/min (broken) ❌

### After (New System)
- Working protocol ✅
- SQLite transactions ✅
- ACID guarantees ✅
- Token bucket rate limiting ✅
- Throughput: 1000+ msg/min ✅

---

## Support & Troubleshooting

### View system state:

```bash
# SQLite CLI
sqlite3 .claude/communications/messages.db

# Useful queries
.schema
SELECT COUNT(*), status FROM messages GROUP BY status;
SELECT * FROM agent_status;
SELECT * FROM dead_letter_queue;
```

### Reset system (nuclear option):

```bash
rm .claude/communications/messages.db*
python -c "from communications.core import CommunicationSystem; CommunicationSystem('.').initialize()"
```

---

**Migration Complete! 🎉**

Your multi-agent communication system now has:
- ✅ Working protocol
- ✅ Request/response
- ✅ Concurrency safety
- ✅ Rate limiting
- ✅ Circuit breakers
- ✅ Complete audit trail
- ✅ Production-ready reliability
