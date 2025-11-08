# Multi-Agent Communication Protocol Specification

**Version:** 1.0  
**Status:** Implementation Ready  
**Target:** Claude Code Multi-Agent System

---

## Executive Summary

This protocol enables 20+ concurrent agents to coordinate via SQLite-based messaging with filesystem artifacts. Design goals: zero external dependencies, <200 token overhead per agent, 100+ messages/minute throughput, ACID guarantees.

**Core Pattern:** SQLite message broker + filesystem artifacts + correlation IDs + token bucket rate limiting

---

## Architecture

### Storage Strategy

**Primary:** SQLite database in WAL mode (all coordination)  
**Secondary:** Filesystem (large artifacts, agent outputs)

```
.claude/
├── communications/
│   ├── messages.db          # SQLite message broker (WAL mode)
│   └── protocol_version.txt # "1.0"
├── artifacts/
│   └── {agent_id}/          # Agent-specific outputs
└── audit-trail.jsonl        # Already exists
```

### Message Flow

1. Agent A writes message to SQLite (`messages` table)
2. Agent B polls for messages (filtered by channel/type)
3. Agent B claims message atomically (BEGIN IMMEDIATE transaction)
4. Agent B processes and updates status
5. Large results → filesystem artifact + reference in response message

---

## Message Format

### Envelope Structure

```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "type": "context.query",
  "version": "1.0",
  "timestamp": "2025-11-08T15:30:00Z",
  "correlation_id": "req-001",
  "from_agent": "frontend-dev-01",
  "to_agent": "context-manager",
  "channel": "general",
  "priority": 5,
  "payload": {
    "query": "Frontend development context needed",
    "aspects": ["ui_architecture", "component_ecosystem"]
  }
}
```

### Field Definitions

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | UUID | Yes | Unique message identifier |
| `type` | string | Yes | Message type for routing (e.g., "context.query") |
| `version` | string | Yes | Protocol version ("1.0") |
| `timestamp` | ISO 8601 | Yes | Creation time |
| `correlation_id` | UUID | No | Links request → response |
| `from_agent` | string | Yes | Sender agent ID |
| `to_agent` | string | No | Recipient agent ID (null for broadcasts) |
| `channel` | string | Yes | Routing channel (e.g., "general", "urgent") |
| `priority` | int | Yes | Priority 1-10 (10 = highest) |
| `payload` | object | Yes | Message-specific data |

### Standard Message Types

| Type | Purpose | Payload Schema |
|------|---------|----------------|
| `context.query` | Request context from context-manager | `{query: string, aspects?: string[]}` |
| `context.response` | Return context data | `{context: object, artifact_path?: string}` |
| `task.claim` | Claim a task from job board | `{task_id: string}` |
| `task.update` | Update task status | `{task_id: string, status: string, progress?: number}` |
| `vote.initiate` | Start voting process | `{topic: string, options: string[], deadline: ISO8601}` |
| `vote.cast` | Cast a vote | `{vote_id: string, option: string, reasoning?: string}` |
| `broadcast` | System-wide announcement | `{message: string, severity: string}` |
| `heartbeat` | Agent health check | `{status: string, current_task?: string}` |

---

## Database Schema

### Messages Table

```sql
CREATE TABLE messages (
    id TEXT PRIMARY KEY,
    type TEXT NOT NULL,
    version TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    correlation_id TEXT,
    from_agent TEXT NOT NULL,
    to_agent TEXT,
    channel TEXT NOT NULL,
    priority INTEGER NOT NULL DEFAULT 5,
    payload TEXT NOT NULL,  -- JSON
    status TEXT NOT NULL DEFAULT 'pending',
    created_at TEXT NOT NULL,
    expires_at TEXT,
    delivery_count INTEGER DEFAULT 0,
    last_delivered_at TEXT,
    error TEXT
);

-- Critical indexes
CREATE INDEX idx_ready_messages ON messages(channel, status, priority DESC, timestamp)
    WHERE status = 'pending';

CREATE INDEX idx_correlation ON messages(correlation_id)
    WHERE correlation_id IS NOT NULL;

CREATE INDEX idx_expiration ON messages(expires_at)
    WHERE expires_at IS NOT NULL;
```

### Channel Subscriptions Table

```sql
CREATE TABLE channel_subscriptions (
    channel_name TEXT NOT NULL,
    agent_id TEXT NOT NULL,
    subscribed_at TEXT NOT NULL,
    PRIMARY KEY (channel_name, agent_id)
);

CREATE INDEX idx_agent_channels ON channel_subscriptions(agent_id);
```

### Agent Status Table

```sql
CREATE TABLE agent_status (
    agent_id TEXT PRIMARY KEY,
    status TEXT NOT NULL,  -- 'active', 'idle', 'degraded', 'failed'
    current_task TEXT,
    last_heartbeat TEXT NOT NULL,
    messages_pending INTEGER DEFAULT 0,
    messages_processed INTEGER DEFAULT 0,
    error_count INTEGER DEFAULT 0
);
```

### Dead Letter Queue Table

```sql
CREATE TABLE dead_letter_queue (
    id TEXT PRIMARY KEY,
    original_message TEXT NOT NULL,  -- JSON of full message
    error TEXT NOT NULL,
    moved_at TEXT NOT NULL,
    retry_count INTEGER NOT NULL
);
```

---

## Core API

### Initialization

```python
def initialize_communication_system(project_root: str) -> None:
    """
    Initialize communication system in .claude/communications/
    
    Creates:
    - SQLite database with schema
    - Configures WAL mode
    - Sets pragmas for concurrency
    - Creates directory structure
    """
```

### Message Operations

```python
def send_message(
    from_agent: str,
    to_agent: Optional[str],
    message_type: str,
    payload: dict,
    channel: str = "general",
    priority: int = 5,
    correlation_id: Optional[str] = None,
    ttl_seconds: Optional[int] = None
) -> str:
    """
    Send a message. Returns message_id.
    
    Implementation:
    - Generate UUID for message_id
    - Create envelope with all fields
    - BEGIN IMMEDIATE transaction
    - INSERT into messages table
    - Update recipient's messages_pending count
    - COMMIT
    - Return message_id
    """

def receive_messages(
    agent_id: str,
    channels: List[str],
    limit: int = 10,
    timeout_seconds: Optional[float] = None
) -> List[dict]:
    """
    Poll for messages. Returns list of message envelopes.
    
    Implementation:
    - Query messages WHERE channel IN channels AND 
      (to_agent = agent_id OR to_agent IS NULL)
      AND status = 'pending'
    - ORDER BY priority DESC, timestamp ASC
    - LIMIT to requested count
    - Return without claiming (read-only)
    """

def claim_message(agent_id: str, message_id: str) -> bool:
    """
    Atomically claim a message for processing.
    
    Implementation:
    - BEGIN IMMEDIATE transaction
    - SELECT status WHERE id = message_id FOR UPDATE
    - If status != 'pending': ROLLBACK, return False
    - UPDATE status = 'processing', last_delivered_at = now()
    - COMMIT
    - Return True
    """

def complete_message(message_id: str, error: Optional[str] = None) -> None:
    """
    Mark message as done or failed.
    
    Implementation:
    - UPDATE status = 'done' (or 'failed' if error)
    - Set error field if provided
    - If failed and delivery_count >= 3: move to DLQ
    """

def send_response(
    original_message: dict,
    response_payload: dict,
    artifact_path: Optional[str] = None
) -> str:
    """
    Send response to a request message.
    
    Implementation:
    - Extract correlation_id from original_message
    - Create response message with same correlation_id
    - Set from_agent = original to_agent
    - Set to_agent = original from_agent
    - If artifact_path provided, include in payload
    - Call send_message()
    """
```

### Channel Operations

```python
def subscribe_to_channel(agent_id: str, channel_name: str) -> None:
    """Add agent to channel subscription."""

def unsubscribe_from_channel(agent_id: str, channel_name: str) -> None:
    """Remove agent from channel subscription."""

def get_subscribed_channels(agent_id: str) -> List[str]:
    """Get list of channels agent is subscribed to."""
```

### Health & Monitoring

```python
def send_heartbeat(agent_id: str, status: str, current_task: Optional[str]) -> None:
    """
    Update agent health status.
    
    Implementation:
    - UPDATE agent_status SET last_heartbeat = now(), status = status
    """

def get_agent_health(agent_id: str) -> dict:
    """Get agent's current health status."""

def cleanup_expired_messages() -> int:
    """
    Remove messages past their TTL. Returns count deleted.
    Should be called periodically (e.g., every 60 seconds).
    """
```

---

## Concurrency Model

### SQLite Configuration

Required pragmas on every connection:

```python
conn.execute("PRAGMA journal_mode=WAL")
conn.execute("PRAGMA synchronous=NORMAL")
conn.execute("PRAGMA busy_timeout=5000")
conn.execute("PRAGMA cache_size=-64000")
```

### Transaction Pattern

**For Claims (Write Operations):**

```python
conn.execute("BEGIN IMMEDIATE")
try:
    # SELECT FOR UPDATE
    # UPDATE status
    conn.commit()
except sqlite3.OperationalError:
    conn.rollback()
    # Handle conflict (retry or fail)
```

**For Reads (Query Operations):**

```python
# No transaction needed - WAL mode allows concurrent reads
cursor = conn.execute("SELECT ...")
```

### Threading Model

- Each agent runs in its own thread
- Use `threading.local()` for per-thread SQLite connections
- Never share connection objects across threads
- Use `queue.Queue` for inter-thread communication when needed

---

## Rate Limiting

### Token Bucket Implementation

Each agent gets a token bucket:
- **Capacity:** 100 tokens
- **Refill rate:** 10 tokens/second
- **Cost per message:** 1 token

```python
class TokenBucket:
    def __init__(self, capacity: int, refill_rate: float):
        self.capacity = capacity
        self.tokens = capacity
        self.refill_rate = refill_rate
        self.last_refill = time.time()
        self.lock = threading.Lock()
    
    def consume(self, tokens: int = 1) -> bool:
        """Try to consume tokens. Returns True if successful."""
        with self.lock:
            now = time.time()
            elapsed = now - self.last_refill
            self.tokens = min(
                self.capacity,
                self.tokens + elapsed * self.refill_rate
            )
            self.last_refill = now
            
            if self.tokens >= tokens:
                self.tokens -= tokens
                return True
            return False
```

### Circuit Breaker

Protect against failing agents:

```python
class CircuitBreaker:
    def __init__(self, failure_threshold: int = 5, timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.failures = 0
        self.last_failure_time = None
        self.state = 'closed'  # closed, open, half_open
    
    def call(self, func, *args, **kwargs):
        """Execute function through circuit breaker."""
        if self.state == 'open':
            if time.time() - self.last_failure_time > self.timeout:
                self.state = 'half_open'
            else:
                raise Exception("Circuit breaker is OPEN")
        
        try:
            result = func(*args, **kwargs)
            if self.state == 'half_open':
                self.state = 'closed'
                self.failures = 0
            return result
        except Exception as e:
            self.failures += 1
            self.last_failure_time = time.time()
            if self.failures >= self.failure_threshold:
                self.state = 'open'
            raise
```

---

## Request/Response Pattern

### Making a Request

```python
# 1. Generate correlation ID
correlation_id = str(uuid.uuid4())

# 2. Send request
request_id = send_message(
    from_agent="frontend-dev-01",
    to_agent="context-manager",
    message_type="context.query",
    payload={"query": "Frontend context needed"},
    correlation_id=correlation_id
)

# 3. Poll for response
response = None
timeout = time.time() + 30  # 30 second timeout

while time.time() < timeout:
    messages = receive_messages(
        agent_id="frontend-dev-01",
        channels=["general"]
    )
    
    for msg in messages:
        if msg.get("correlation_id") == correlation_id:
            if claim_message("frontend-dev-01", msg["id"]):
                response = msg
                complete_message(msg["id"])
                break
    
    if response:
        break
    
    time.sleep(0.1)  # Poll every 100ms

if not response:
    raise TimeoutError("No response received")
```

### Sending a Response

```python
# Agent receives request message
request = receive_messages(agent_id, channels)[0]
claim_message(agent_id, request["id"])

# Process request
result = process_query(request["payload"])

# Send response with same correlation_id
send_response(
    original_message=request,
    response_payload={"context": result}
)

# Mark request as complete
complete_message(request["id"])
```

---

## Artifact Pattern

For large payloads (>10KB or complex objects):

```python
# 1. Write artifact to filesystem
artifact_path = f".claude/artifacts/{agent_id}/{task_id}/result.json"
os.makedirs(os.path.dirname(artifact_path), exist_ok=True)

# Atomic write
temp_path = artifact_path + ".tmp"
with open(temp_path, 'w') as f:
    json.dump(large_data, f)
    f.flush()
    os.fsync(f.fileno())

os.replace(temp_path, artifact_path)

# 2. Send message with reference
send_message(
    from_agent=agent_id,
    to_agent=requester,
    message_type="task.complete",
    payload={
        "task_id": task_id,
        "artifact_path": artifact_path,
        "summary": "Processed 10,000 records"
    }
)
```

---

## Error Handling

### Retry Strategy

```python
def send_with_retry(
    max_attempts: int = 3,
    base_delay: float = 1.0,
    **message_args
) -> str:
    """Send message with exponential backoff retry."""
    for attempt in range(max_attempts):
        try:
            return send_message(**message_args)
        except Exception as e:
            if attempt == max_attempts - 1:
                raise
            
            # Exponential backoff with jitter
            delay = base_delay * (2 ** attempt)
            jitter = random.uniform(0.5, 1.5)
            time.sleep(delay * jitter)
```

### Dead Letter Queue

Messages that fail 3+ times automatically move to DLQ:

```python
if delivery_count >= 3:
    conn.execute("""
        INSERT INTO dead_letter_queue (id, original_message, error, moved_at, retry_count)
        VALUES (?, ?, ?, ?, ?)
    """, (message_id, json.dumps(original_message), error, now(), delivery_count))
    
    conn.execute("DELETE FROM messages WHERE id = ?", (message_id,))
```

---

## Validation

### Message Schema Validation

```python
from typing import Any, get_type_hints
from dataclasses import dataclass
import json

@dataclass
class MessageEnvelope:
    id: str
    type: str
    version: str
    timestamp: str
    from_agent: str
    channel: str
    priority: int
    payload: dict
    correlation_id: str = None
    to_agent: str = None

def validate_message(msg: dict) -> tuple[bool, list[str]]:
    """Validate message against schema. Returns (is_valid, errors)."""
    errors = []
    
    # Required fields
    required = ["id", "type", "version", "timestamp", "from_agent", "channel", "priority", "payload"]
    for field in required:
        if field not in msg:
            errors.append(f"Missing required field: {field}")
    
    # Type validation
    if "priority" in msg and not isinstance(msg["priority"], int):
        errors.append("priority must be integer")
    
    if "priority" in msg and not (1 <= msg["priority"] <= 10):
        errors.append("priority must be 1-10")
    
    if "payload" in msg and not isinstance(msg["payload"], dict):
        errors.append("payload must be object")
    
    # Version check
    if msg.get("version") != "1.0":
        errors.append(f"Unsupported version: {msg.get('version')}")
    
    return (len(errors) == 0, errors)
```

---

## Performance Targets

| Metric | Target | Measured Method |
|--------|--------|-----------------|
| Message latency | <10ms p95 | Time from send to receive |
| Throughput | 100+ msg/min | Messages processed per minute |
| Claim atomicity | 100% | No double processing |
| Token overhead | <200 tokens/agent | Protocol + message size |
| Concurrent agents | 20+ | Simultaneous active agents |

---

## Testing Strategy

### Unit Tests

- Message validation
- Token bucket algorithm
- Circuit breaker state machine
- Atomic file operations
- Correlation ID matching

### Integration Tests

- 3 agents sending messages
- Request/response cycle
- Channel subscriptions
- DLQ handling
- Artifact passing

### Load Tests

- 20 agents, 1000 messages
- Measure: latency, throughput, errors
- Verify: no deadlocks, no data loss

---

## Migration from Current Implementation

1. **Keep existing `audit-trail.jsonl`** - no changes needed
2. **Replace `setup_communication.py`** with new implementation
3. **Update agent templates** to use new message format
4. **Add `messages.db`** alongside existing files
5. **Test with 2-3 agents** before full deployment

---

## Open Questions for Implementation

1. **Connection pooling:** One connection per thread, or connection pool?
   - **Recommendation:** One per thread (simpler, sufficient)

2. **Message expiration:** Default TTL?
   - **Recommendation:** 1 hour for normal, 5 minutes for urgent

3. **Heartbeat frequency:** How often?
   - **Recommendation:** Every 30 seconds

4. **Channel auto-creation:** Create channels on first use?
   - **Recommendation:** Yes, pre-define core channels only

---

## Success Criteria

✅ Agents can send/receive structured messages  
✅ Request/response pattern works with correlation IDs  
✅ No race conditions under concurrent load  
✅ No data loss or corruption  
✅ Token overhead <200 per agent  
✅ Throughput >100 msg/min  
✅ Complete audit trail  

---

**Implementation Priority:** Core messaging → Request/response → Rate limiting → Circuit breakers → Monitoring

**Estimated Implementation Time:** 2-3 days for MVP, 1 week for full spec
