# Communication Protocol Implementation Guide

**Target:** Working MVP in 2-3 days  
**Approach:** Build core, test, iterate

---

## Phase 1: Foundation (Day 1)

### Step 1.1: Create Core Module Structure

```
.claude/communications/
├── __init__.py
├── core.py              # Main CommunicationSystem class
├── models.py            # Message dataclasses
├── rate_limiter.py      # Token bucket
├── circuit_breaker.py   # Circuit breaker
└── utils.py             # Helpers
```

### Step 1.2: Implement `models.py`

```python
"""Message models and validation."""
from dataclasses import dataclass, asdict
from typing import Optional, Dict, Any
from datetime import datetime
import uuid

@dataclass
class Message:
    """Message envelope."""
    id: str
    type: str
    version: str
    timestamp: str
    from_agent: str
    channel: str
    priority: int
    payload: Dict[str, Any]
    correlation_id: Optional[str] = None
    to_agent: Optional[str] = None
    
    @classmethod
    def create(cls, from_agent: str, message_type: str, payload: dict, **kwargs):
        """Factory method for creating messages."""
        return cls(
            id=str(uuid.uuid4()),
            type=message_type,
            version="1.0",
            timestamp=datetime.utcnow().isoformat() + "Z",
            from_agent=from_agent,
            payload=payload,
            **kwargs
        )
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return asdict(self)
    
    def validate(self) -> tuple[bool, list[str]]:
        """Validate message fields."""
        errors = []
        
        if not (1 <= self.priority <= 10):
            errors.append("Priority must be 1-10")
        
        if not isinstance(self.payload, dict):
            errors.append("Payload must be dict")
        
        if self.version != "1.0":
            errors.append(f"Unsupported version: {self.version}")
        
        return (len(errors) == 0, errors)
```

### Step 1.3: Implement `core.py` - Database Setup

```python
"""Core communication system implementation."""
import sqlite3
import json
import threading
from pathlib import Path
from typing import Optional, List, Dict
from contextlib import contextmanager

from .models import Message

class CommunicationSystem:
    """SQLite-based message broker."""
    
    def __init__(self, project_root: str):
        self.project_root = Path(project_root).resolve()
        self.comm_dir = self.project_root / ".claude" / "communications"
        self.db_path = self.comm_dir / "messages.db"
        self._local = threading.local()
        
    @property
    def connection(self) -> sqlite3.Connection:
        """Get thread-local connection."""
        if not hasattr(self._local, 'conn'):
            self._local.conn = self._create_connection()
        return self._local.conn
    
    def _create_connection(self) -> sqlite3.Connection:
        """Create and configure SQLite connection."""
        conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
        conn.row_factory = sqlite3.Row
        
        # Critical pragmas
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA synchronous=NORMAL")
        conn.execute("PRAGMA busy_timeout=5000")
        conn.execute("PRAGMA cache_size=-64000")
        
        return conn
    
    def initialize(self) -> None:
        """Initialize database schema and directory structure."""
        self.comm_dir.mkdir(parents=True, exist_ok=True)
        (self.project_root / ".claude" / "artifacts").mkdir(parents=True, exist_ok=True)
        
        with self.connection as conn:
            # Messages table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    id TEXT PRIMARY KEY,
                    type TEXT NOT NULL,
                    version TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    correlation_id TEXT,
                    from_agent TEXT NOT NULL,
                    to_agent TEXT,
                    channel TEXT NOT NULL,
                    priority INTEGER NOT NULL DEFAULT 5,
                    payload TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'pending',
                    created_at TEXT NOT NULL,
                    expires_at TEXT,
                    delivery_count INTEGER DEFAULT 0,
                    last_delivered_at TEXT,
                    error TEXT
                )
            """)
            
            # Indexes
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_ready_messages 
                ON messages(channel, status, priority DESC, timestamp)
                WHERE status = 'pending'
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_correlation 
                ON messages(correlation_id)
                WHERE correlation_id IS NOT NULL
            """)
            
            # Channel subscriptions
            conn.execute("""
                CREATE TABLE IF NOT EXISTS channel_subscriptions (
                    channel_name TEXT NOT NULL,
                    agent_id TEXT NOT NULL,
                    subscribed_at TEXT NOT NULL,
                    PRIMARY KEY (channel_name, agent_id)
                )
            """)
            
            # Agent status
            conn.execute("""
                CREATE TABLE IF NOT EXISTS agent_status (
                    agent_id TEXT PRIMARY KEY,
                    status TEXT NOT NULL,
                    current_task TEXT,
                    last_heartbeat TEXT NOT NULL,
                    messages_pending INTEGER DEFAULT 0,
                    messages_processed INTEGER DEFAULT 0,
                    error_count INTEGER DEFAULT 0
                )
            """)
            
            # Dead letter queue
            conn.execute("""
                CREATE TABLE IF NOT EXISTS dead_letter_queue (
                    id TEXT PRIMARY KEY,
                    original_message TEXT NOT NULL,
                    error TEXT NOT NULL,
                    moved_at TEXT NOT NULL,
                    retry_count INTEGER NOT NULL
                )
            """)
            
            conn.commit()
```

### Step 1.4: Implement Core Message Operations

```python
# Add to CommunicationSystem class in core.py

def send_message(
    self,
    from_agent: str,
    message_type: str,
    payload: dict,
    to_agent: Optional[str] = None,
    channel: str = "general",
    priority: int = 5,
    correlation_id: Optional[str] = None,
    ttl_seconds: Optional[int] = None
) -> str:
    """Send a message."""
    msg = Message.create(
        from_agent=from_agent,
        message_type=message_type,
        payload=payload,
        to_agent=to_agent,
        channel=channel,
        priority=priority,
        correlation_id=correlation_id
    )
    
    # Validate
    valid, errors = msg.validate()
    if not valid:
        raise ValueError(f"Invalid message: {errors}")
    
    # Calculate expiration
    expires_at = None
    if ttl_seconds:
        from datetime import datetime, timedelta
        expires_at = (datetime.utcnow() + timedelta(seconds=ttl_seconds)).isoformat() + "Z"
    
    # Insert
    with self.connection as conn:
        conn.execute("BEGIN IMMEDIATE")
        try:
            conn.execute("""
                INSERT INTO messages (
                    id, type, version, timestamp, correlation_id,
                    from_agent, to_agent, channel, priority, payload,
                    status, created_at, expires_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'pending', ?, ?)
            """, (
                msg.id, msg.type, msg.version, msg.timestamp, msg.correlation_id,
                msg.from_agent, msg.to_agent, msg.channel, msg.priority,
                json.dumps(msg.payload), msg.timestamp, expires_at
            ))
            
            conn.commit()
            return msg.id
        except Exception as e:
            conn.rollback()
            raise

def receive_messages(
    self,
    agent_id: str,
    channels: List[str],
    limit: int = 10
) -> List[Dict]:
    """Poll for messages (read-only, does not claim)."""
    placeholders = ','.join('?' * len(channels))
    
    with self.connection as conn:
        cursor = conn.execute(f"""
            SELECT * FROM messages
            WHERE channel IN ({placeholders})
              AND (to_agent = ? OR to_agent IS NULL)
              AND status = 'pending'
            ORDER BY priority DESC, timestamp ASC
            LIMIT ?
        """, (*channels, agent_id, limit))
        
        messages = []
        for row in cursor:
            msg = dict(row)
            msg['payload'] = json.loads(msg['payload'])
            messages.append(msg)
        
        return messages

def claim_message(self, agent_id: str, message_id: str) -> bool:
    """Atomically claim a message for processing."""
    from datetime import datetime
    
    with self.connection as conn:
        conn.execute("BEGIN IMMEDIATE")
        try:
            # Check current status
            cursor = conn.execute(
                "SELECT status FROM messages WHERE id = ?",
                (message_id,)
            )
            row = cursor.fetchone()
            
            if not row or row['status'] != 'pending':
                conn.rollback()
                return False
            
            # Claim it
            now = datetime.utcnow().isoformat() + "Z"
            conn.execute("""
                UPDATE messages
                SET status = 'processing',
                    last_delivered_at = ?,
                    delivery_count = delivery_count + 1
                WHERE id = ?
            """, (now, message_id))
            
            conn.commit()
            return True
        except Exception:
            conn.rollback()
            return False

def complete_message(
    self,
    message_id: str,
    error: Optional[str] = None
) -> None:
    """Mark message as done or failed."""
    status = 'failed' if error else 'done'
    
    with self.connection as conn:
        # Check if should move to DLQ
        cursor = conn.execute(
            "SELECT delivery_count, payload FROM messages WHERE id = ?",
            (message_id,)
        )
        row = cursor.fetchone()
        
        if row and error and row['delivery_count'] >= 3:
            # Move to DLQ
            from datetime import datetime
            now = datetime.utcnow().isoformat() + "Z"
            
            conn.execute("""
                INSERT INTO dead_letter_queue (id, original_message, error, moved_at, retry_count)
                VALUES (?, ?, ?, ?, ?)
            """, (message_id, row['payload'], error, now, row['delivery_count']))
            
            conn.execute("DELETE FROM messages WHERE id = ?", (message_id,))
        else:
            # Update status
            conn.execute("""
                UPDATE messages
                SET status = ?, error = ?
                WHERE id = ?
            """, (status, error, message_id))
        
        conn.commit()
```

### Step 1.5: Test Core Functionality

```python
# test_core.py
def test_send_receive():
    comm = CommunicationSystem(".")
    comm.initialize()
    
    # Send message
    msg_id = comm.send_message(
        from_agent="test-agent-01",
        message_type="test.ping",
        payload={"message": "hello"},
        channel="general"
    )
    
    # Receive message
    messages = comm.receive_messages(
        agent_id="test-agent-02",
        channels=["general"]
    )
    
    assert len(messages) == 1
    assert messages[0]['payload']['message'] == "hello"
    
    # Claim message
    claimed = comm.claim_message("test-agent-02", messages[0]['id'])
    assert claimed == True
    
    # Complete message
    comm.complete_message(messages[0]['id'])
    
    print("✓ Core messaging works")

if __name__ == "__main__":
    test_send_receive()
```

---

## Phase 2: Request/Response (Day 2)

### Step 2.1: Implement Response Helper

```python
# Add to core.py

def send_response(
    self,
    original_message: Dict,
    response_payload: dict,
    artifact_path: Optional[str] = None
) -> str:
    """Send response to a request."""
    if artifact_path:
        response_payload['artifact_path'] = artifact_path
    
    response_type = original_message['type'] + ".response"
    
    return self.send_message(
        from_agent=original_message['to_agent'],  # Swap roles
        message_type=response_type,
        payload=response_payload,
        to_agent=original_message['from_agent'],
        channel=original_message['channel'],
        priority=original_message['priority'],
        correlation_id=original_message.get('correlation_id')
    )

def wait_for_response(
    self,
    agent_id: str,
    correlation_id: str,
    channels: List[str],
    timeout_seconds: float = 30.0
) -> Optional[Dict]:
    """Wait for response with specific correlation_id."""
    import time
    
    deadline = time.time() + timeout_seconds
    
    while time.time() < deadline:
        messages = self.receive_messages(agent_id, channels)
        
        for msg in messages:
            if msg.get('correlation_id') == correlation_id:
                # Claim and return
                if self.claim_message(agent_id, msg['id']):
                    self.complete_message(msg['id'])
                    return msg
        
        time.sleep(0.1)  # Poll every 100ms
    
    return None  # Timeout
```

### Step 2.2: Test Request/Response

```python
# test_request_response.py
import uuid
from threading import Thread
import time

def responder(comm):
    """Simulates context-manager responding to queries."""
    time.sleep(0.2)  # Simulate work
    
    messages = comm.receive_messages("context-manager", ["general"])
    for msg in messages:
        if msg['type'] == 'context.query':
            comm.claim_message("context-manager", msg['id'])
            
            # Send response
            comm.send_response(
                original_message=msg,
                response_payload={"context": {"ui_arch": "React"}}
            )
            
            comm.complete_message(msg['id'])

def test_request_response():
    comm = CommunicationSystem(".")
    comm.initialize()
    
    # Start responder thread
    Thread(target=responder, args=(comm,), daemon=True).start()
    
    # Send request
    correlation_id = str(uuid.uuid4())
    comm.send_message(
        from_agent="frontend-dev-01",
        message_type="context.query",
        payload={"query": "Need UI architecture"},
        to_agent="context-manager",
        channel="general",
        correlation_id=correlation_id
    )
    
    # Wait for response
    response = comm.wait_for_response(
        agent_id="frontend-dev-01",
        correlation_id=correlation_id,
        channels=["general"],
        timeout_seconds=5.0
    )
    
    assert response is not None
    assert response['payload']['context']['ui_arch'] == "React"
    
    print("✓ Request/Response works")

if __name__ == "__main__":
    test_request_response()
```

---

## Phase 3: Safety & Monitoring (Day 3)

### Step 3.1: Implement Rate Limiter

```python
# rate_limiter.py
import time
import threading

class TokenBucket:
    """Thread-safe token bucket rate limiter."""
    
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
            
            # Refill tokens
            self.tokens = min(
                self.capacity,
                self.tokens + elapsed * self.refill_rate
            )
            self.last_refill = now
            
            # Try to consume
            if self.tokens >= tokens:
                self.tokens -= tokens
                return True
            return False
    
    def wait_for_token(self, tokens: int = 1, timeout: float = 10.0) -> bool:
        """Wait until tokens available or timeout."""
        deadline = time.time() + timeout
        
        while time.time() < deadline:
            if self.consume(tokens):
                return True
            time.sleep(0.01)
        
        return False
```

### Step 3.2: Implement Circuit Breaker

```python
# circuit_breaker.py
import time
from enum import Enum

class CircuitState(Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"

class CircuitBreaker:
    """Circuit breaker for protecting against failures."""
    
    def __init__(self, failure_threshold: int = 5, timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.failures = 0
        self.last_failure_time = None
        self.state = CircuitState.CLOSED
    
    def call(self, func, *args, **kwargs):
        """Execute function through circuit breaker."""
        # Check if circuit should transition
        if self.state == CircuitState.OPEN:
            if time.time() - self.last_failure_time > self.timeout:
                self.state = CircuitState.HALF_OPEN
            else:
                raise Exception(f"Circuit breaker OPEN for {func.__name__}")
        
        # Try execution
        try:
            result = func(*args, **kwargs)
            
            # Success - reset if half open
            if self.state == CircuitState.HALF_OPEN:
                self.state = CircuitState.CLOSED
                self.failures = 0
            
            return result
        
        except Exception as e:
            self.failures += 1
            self.last_failure_time = time.time()
            
            if self.failures >= self.failure_threshold:
                self.state = CircuitState.OPEN
            
            raise
```

### Step 3.3: Add Health Monitoring

```python
# Add to core.py

def send_heartbeat(
    self,
    agent_id: str,
    status: str = "active",
    current_task: Optional[str] = None
) -> None:
    """Update agent health status."""
    from datetime import datetime
    now = datetime.utcnow().isoformat() + "Z"
    
    with self.connection as conn:
        conn.execute("""
            INSERT INTO agent_status (agent_id, status, current_task, last_heartbeat)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(agent_id) DO UPDATE SET
                status = excluded.status,
                current_task = excluded.current_task,
                last_heartbeat = excluded.last_heartbeat
        """, (agent_id, status, current_task, now))
        conn.commit()

def get_agent_health(self, agent_id: str) -> Optional[Dict]:
    """Get agent's current health status."""
    cursor = self.connection.execute(
        "SELECT * FROM agent_status WHERE agent_id = ?",
        (agent_id,)
    )
    row = cursor.fetchone()
    return dict(row) if row else None

def cleanup_expired_messages(self) -> int:
    """Remove expired messages. Returns count deleted."""
    from datetime import datetime
    now = datetime.utcnow().isoformat() + "Z"
    
    with self.connection as conn:
        cursor = conn.execute("""
            DELETE FROM messages
            WHERE expires_at IS NOT NULL AND expires_at < ?
        """, (now,))
        count = cursor.rowcount
        conn.commit()
        return count
```

---

## Phase 4: Integration with Existing System

### Step 4.1: Update Agent Templates

Replace the communication protocol section in agent templates:

```markdown
## Communication Protocol

Use the CommunicationSystem to coordinate:

```python
from communications.core import CommunicationSystem

comm = CommunicationSystem('.')

# Query context manager
import uuid
correlation_id = str(uuid.uuid4())

comm.send_message(
    from_agent="your-agent-id",
    message_type="context.query",
    payload={"query": "Frontend context needed"},
    to_agent="context-manager",
    correlation_id=correlation_id
)

# Wait for response
response = comm.wait_for_response(
    agent_id="your-agent-id",
    correlation_id=correlation_id,
    channels=["general"],
    timeout_seconds=30
)
```
```

### Step 4.2: Wire Up Context Manager

Update `context-manager.md` agent to handle queries:

```python
# In context-manager agent
from communications.core import CommunicationSystem

comm = CommunicationSystem('.')
comm.send_heartbeat("context-manager", "active")

# Poll for queries
while True:
    messages = comm.receive_messages("context-manager", ["general"])
    
    for msg in messages:
        if msg['type'] == 'context.query':
            if comm.claim_message("context-manager", msg['id']):
                # Process query
                context_data = retrieve_context(msg['payload']['query'])
                
                # Send response
                comm.send_response(
                    original_message=msg,
                    response_payload={"context": context_data}
                )
                
                comm.complete_message(msg['id'])
```

### Step 4.3: Integration Test

```python
# test_integration.py
def test_three_agents():
    """Test 3 agents coordinating."""
    comm = CommunicationSystem(".")
    comm.initialize()
    
    # Agent 1: Requester
    # Agent 2: Context Manager (responder)
    # Agent 3: Observer
    
    # Implementation left as exercise
    pass
```

---

## Performance Tuning

### If seeing "database is locked" errors:

1. Increase busy_timeout: `PRAGMA busy_timeout=10000`
2. Reduce transaction scope
3. Add retry logic with exponential backoff

### If messages are slow:

1. Verify WAL mode: `PRAGMA journal_mode=WAL`
2. Check indexes exist
3. Add ANALYZE: `ANALYZE`

---

## Deployment Checklist

- [ ] SQLite in WAL mode
- [ ] All indexes created
- [ ] Connection per thread
- [ ] Rate limiters configured
- [ ] Circuit breakers in place
- [ ] Heartbeat monitoring active
- [ ] Expired message cleanup scheduled
- [ ] Integration tests passing
- [ ] Load test with 20 agents

---

## Debugging Tips

**View messages:**
```bash
sqlite3 .claude/communications/messages.db "SELECT * FROM messages"
```

**Check queue depth:**
```python
cursor = conn.execute("SELECT COUNT(*) FROM messages WHERE status = 'pending'")
print(f"Pending messages: {cursor.fetchone()[0]}")
```

**Monitor agent health:**
```python
cursor = conn.execute("SELECT * FROM agent_status")
for row in cursor:
    print(dict(row))
```

---

**Next Steps After MVP:**

1. Add channel auto-creation
2. Implement message priorities in practice
3. Add metrics dashboard
4. Optimize for higher throughput
5. Add message replay capability
