#!/usr/bin/env python3
"""
Communication System - Initializes agent messaging infrastructure.

Creates:
- Message channels (files + SQLite index)
- Agent registry with IDs
- Priority routing
- Broadcast mechanisms
"""

import json
import sqlite3
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
import uuid


class CommunicationSystem:
    """Manages multi-agent communication infrastructure."""
    
    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root).resolve()
        self.claude_dir = self.project_root / ".claude"
        self.comm_dir = self.claude_dir / "communications"
        self.db_path = self.comm_dir / "messages.db"
        self.registry_path = self.claude_dir / "agent-registry.json"
        
    def initialize(self):
        """Initialize complete communication system."""
        # Create directories
        self.comm_dir.mkdir(parents=True, exist_ok=True)
        (self.comm_dir / "urgent").mkdir(exist_ok=True)
        (self.comm_dir / "channels").mkdir(exist_ok=True)
        (self.comm_dir / "direct").mkdir(exist_ok=True)
        (self.comm_dir / "archive").mkdir(exist_ok=True)
        
        # Initialize database
        self._init_database()
        
        # Initialize agent registry
        self._init_registry()
        
        # Create communication protocol doc
        self._create_protocol_doc()
        
        return {
            "status": "initialized",
            "comm_dir": str(self.comm_dir),
            "db_path": str(self.db_path),
            "registry_path": str(self.registry_path)
        }
    
    def _init_database(self):
        """Create SQLite database for message indexing."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Messages table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id TEXT PRIMARY KEY,
                timestamp TEXT NOT NULL,
                from_agent TEXT NOT NULL,
                to_agent TEXT,
                channel TEXT,
                priority TEXT NOT NULL,
                message_type TEXT,
                subject TEXT,
                file_path TEXT NOT NULL,
                read INTEGER DEFAULT 0,
                archived INTEGER DEFAULT 0,
                created_at TEXT NOT NULL
            )
        """)
        
        # Message index for fast queries
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_timestamp ON messages(timestamp DESC)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_to_agent ON messages(to_agent)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_priority ON messages(priority)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_read ON messages(read)
        """)
        
        # Agent status table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS agent_status (
                agent_id TEXT PRIMARY KEY,
                status TEXT NOT NULL,
                current_task TEXT,
                last_heartbeat TEXT,
                messages_pending INTEGER DEFAULT 0
            )
        """)
        
        conn.commit()
        conn.close()
    
    def _init_registry(self):
        """Initialize agent registry."""
        if self.registry_path.exists():
            return  # Already exists
        
        registry = {
            "version": "1.0",
            "created_at": datetime.now().isoformat(),
            "agents": {},
            "channels": {
                "general": {
                    "description": "General coordination",
                    "subscribers": []
                },
                "urgent": {
                    "description": "Critical system alerts",
                    "subscribers": []
                },
                "technical": {
                    "description": "Technical discussions",
                    "subscribers": []
                },
                "review": {
                    "description": "Code and design reviews",
                    "subscribers": []
                }
            }
        }
        
        with open(self.registry_path, 'w') as f:
            json.dump(registry, f, indent=2)
    
    def register_agent(self, agent_name: str, role: str, capabilities: List[str]) -> str:
        """
        Register an agent and assign ID.
        
        Returns:
            agent_id
        """
        with open(self.registry_path) as f:
            registry = json.load(f)
        
        # Generate semantic ID
        agent_id = f"{role.lower()}-{str(uuid.uuid4())[:8]}"
        
        registry["agents"][agent_id] = {
            "name": agent_name,
            "role": role,
            "capabilities": capabilities,
            "registered_at": datetime.now().isoformat(),
            "status": "active"
        }
        
        # Auto-subscribe to general channel
        if agent_id not in registry["channels"]["general"]["subscribers"]:
            registry["channels"]["general"]["subscribers"].append(agent_id)
        
        with open(self.registry_path, 'w') as f:
            json.dump(registry, f, indent=2)
        
        # Update agent status
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT OR REPLACE INTO agent_status (agent_id, status, last_heartbeat, messages_pending)
            VALUES (?, ?, ?, 0)
        """, (agent_id, "active", datetime.now().isoformat()))
        conn.commit()
        conn.close()
        
        return agent_id
    
    def send_message(self, from_agent: str, to: str, message: str, 
                    priority: str = "normal", message_type: str = "info", 
                    subject: Optional[str] = None) -> str:
        """
        Send a message.
        
        Args:
            from_agent: Sender agent ID
            to: Recipient agent ID or channel name
            message: Message content
            priority: urgent|normal|low
            message_type: info|request|response|alert
            subject: Optional subject line
            
        Returns:
            message_id
        """
        message_id = str(uuid.uuid4())
        timestamp = datetime.now().isoformat()
        
        # Determine routing
        if to.startswith("#"):
            # Channel message
            channel = to[1:]
            to_agent = None
            file_dir = self.comm_dir / "channels" / channel
        elif priority == "urgent":
            # Urgent broadcast
            channel = "urgent"
            to_agent = to
            file_dir = self.comm_dir / "urgent"
        else:
            # Direct message
            channel = None
            to_agent = to
            file_dir = self.comm_dir / "direct" / to_agent
        
        file_dir.mkdir(parents=True, exist_ok=True)
        
        # Create message file
        msg_data = {
            "id": message_id,
            "timestamp": timestamp,
            "from": from_agent,
            "to": to_agent,
            "channel": channel,
            "priority": priority,
            "type": message_type,
            "subject": subject,
            "message": message,
            "read": False
        }
        
        file_path = file_dir / f"{timestamp.replace(':', '-')}_{message_id[:8]}.json"
        with open(file_path, 'w') as f:
            json.dump(msg_data, f, indent=2)
        
        # Index in database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO messages 
            (id, timestamp, from_agent, to_agent, channel, priority, message_type, subject, file_path, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (message_id, timestamp, from_agent, to_agent, channel, priority, 
              message_type, subject, str(file_path), datetime.now().isoformat()))
        
        # Update recipient pending count
        if to_agent:
            cursor.execute("""
                UPDATE agent_status 
                SET messages_pending = messages_pending + 1
                WHERE agent_id = ?
            """, (to_agent,))
        
        conn.commit()
        conn.close()
        
        return message_id
    
    def get_messages(self, agent_id: str, unread_only: bool = False, 
                    priority: Optional[str] = None) -> List[Dict]:
        """Retrieve messages for an agent."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        query = """
            SELECT * FROM messages 
            WHERE (to_agent = ? OR channel IN (
                SELECT channel FROM channels WHERE ? IN subscribers
            ))
        """
        params = [agent_id, agent_id]
        
        if unread_only:
            query += " AND read = 0"
        if priority:
            query += " AND priority = ?"
            params.append(priority)
        
        query += " ORDER BY timestamp DESC LIMIT 50"
        
        cursor.execute(query, params)
        messages = [dict(row) for row in cursor.fetchall()]
        
        conn.close()
        
        # Load message content
        for msg in messages:
            try:
                with open(msg['file_path']) as f:
                    content = json.load(f)
                    msg['content'] = content['message']
            except:
                msg['content'] = "[Message file not found]"
        
        return messages
    
    def _create_protocol_doc(self):
        """Create communication protocol documentation."""
        protocol_doc = """# Multi-Agent Communication Protocol

## Overview

This system uses a hybrid communication model:
- **Urgent messages**: Broadcast immediately via `/urgent/` directory
- **Direct messages**: Agent-to-agent via `/direct/` directory
- **Channels**: Topic-based via `/channels/` directory
- **Database index**: SQLite for querying and tracking

## Message Priority

- `urgent`: Critical system alerts, requires immediate attention
- `normal`: Standard inter-agent communication
- `low`: Background notifications, informational

## Message Types

- `info`: General information sharing
- `request`: Requesting action or information
- `response`: Replying to a request
- `alert`: System or error alerts
- `heartbeat`: Agent status updates

## Channels

- `#general`: General coordination
- `#urgent`: System-wide critical alerts
- `#technical`: Technical discussions and decisions
- `#review`: Code and design review discussions

## Usage Patterns

### Before Starting Work
```python
# Check for urgent messages
messages = comm.get_messages(agent_id, priority="urgent")

# Check unread messages
messages = comm.get_messages(agent_id, unread_only=True)
```

### Broadcasting Critical Info
```python
comm.send_message(
    from_agent=my_id,
    to="#urgent",
    message="Critical decision needed on X",
    priority="urgent",
    message_type="alert"
)
```

### Direct Communication
```python
comm.send_message(
    from_agent=my_id,
    to="other-agent-id",
    message="Can you review my implementation?",
    priority="normal",
    message_type="request"
)
```

## Best Practices

1. **Check messages before starting work** - prevents duplicate effort
2. **Use appropriate priority** - don't abuse urgent
3. **Provide context** - include task_id, related docs
4. **Respond to requests** - acknowledge receipt
5. **Clean up read messages** - mark as read after processing

## Circuit Breakers

If an agent fails repeatedly:
1. System marks agent as `degraded`
2. Tasks are rerouted
3. Alert sent to `#urgent`
4. Human notified via audit log

## Rate Limits

- Max 100 messages/minute per agent
- Max 10 urgent broadcasts/hour system-wide
- Violations trigger throttling

---
Created: {datetime.now().isoformat()}
"""
        
        protocol_path = self.comm_dir / "PROTOCOL.md"
        with open(protocol_path, 'w') as f:
            f.write(protocol_doc.format(datetime=datetime))


def main():
    """CLI entry point."""
    project_root = sys.argv[1] if len(sys.argv) > 1 else "."
    
    comm_system = CommunicationSystem(project_root)
    result = comm_system.initialize()
    
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
