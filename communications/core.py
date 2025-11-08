#!/usr/bin/env python3
"""
Core Communication System Implementation

This module implements the fixed, bulletproof communication protocol with:
- SQLite-compatible atomic operations (no SELECT FOR UPDATE)
- Proper broadcast message delivery to multiple agents
- Transactional job board integration
- Subscription-based routing
- Clear error messages for agents

Author: Protocol Audit v1.0
"""

import json
import sqlite3
import threading
import time
import uuid
from contextlib import contextmanager
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any


class CommunicationError(Exception):
    """Base exception for communication errors."""
    pass


class MessageNotFoundError(CommunicationError):
    """Message does not exist."""
    pass


class AlreadyClaimedError(CommunicationError):
    """Message already claimed by another agent."""
    pass


class NotSubscribedError(CommunicationError):
    """Agent not subscribed to channel."""
    pass


class CommunicationSystem:
    """
    Thread-safe communication system for multi-agent coordination.

    This is the low-level API. Most agents should use AgentMessenger instead.
    """

    # Thread-local storage for connections
    _local = threading.local()

    def __init__(self, project_root: str = "."):
        """
        Initialize communication system.

        Args:
            project_root: Path to project root (contains .claude/)
        """
        self.project_root = Path(project_root).resolve()
        self.claude_dir = self.project_root / ".claude"
        self.comm_dir = self.claude_dir / "communications"
        self.db_path = self.comm_dir / "messages.db"
        self.artifacts_dir = self.claude_dir / "artifacts"

        # Ensure directories exist
        self.comm_dir.mkdir(parents=True, exist_ok=True)
        self.artifacts_dir.mkdir(parents=True, exist_ok=True)

    def _get_connection(self) -> sqlite3.Connection:
        """Get thread-local database connection."""
        # Each thread gets its own connection to avoid concurrency issues
        thread_id = threading.get_ident()

        if not hasattr(self._local, 'connections'):
            self._local.connections = {}

        if thread_id not in self._local.connections:
            conn = sqlite3.connect(
                str(self.db_path),
                timeout=10.0,  # 10 second timeout for locks
                check_same_thread=False
            )

            # Configure for concurrency
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA synchronous=NORMAL")
            conn.execute("PRAGMA busy_timeout=10000")
            conn.execute("PRAGMA cache_size=-64000")  # 64MB cache
            conn.row_factory = sqlite3.Row

            self._local.connections[thread_id] = conn

        return self._local.connections[thread_id]

    @contextmanager
    def _transaction(self, immediate: bool = False):
        """
        Context manager for transactions.

        Args:
            immediate: Use BEGIN IMMEDIATE for write transactions
        """
        conn = self._get_connection()

        if immediate:
            conn.execute("BEGIN IMMEDIATE")
        else:
            conn.execute("BEGIN")

        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise

    def initialize(self) -> Dict[str, Any]:
        """
        Initialize the communication system database and structures.

        Returns:
            Dict with initialization status and paths
        """
        # Use a direct connection for initialization to ensure schema is committed
        conn = sqlite3.connect(str(self.db_path), timeout=10.0)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA synchronous=NORMAL")
        cursor = conn.cursor()

        # Main messages table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id TEXT PRIMARY KEY,
                type TEXT NOT NULL,
                version TEXT NOT NULL DEFAULT '1.0',
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

        # Indexes for performance
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_ready_messages
            ON messages(channel, status, priority DESC, timestamp)
            WHERE status = 'pending'
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_correlation
            ON messages(correlation_id)
            WHERE correlation_id IS NOT NULL
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_expiration
            ON messages(expires_at)
            WHERE expires_at IS NOT NULL
        """)

        # FIX: Add unique constraint for response correlation IDs
        cursor.execute("""
            CREATE UNIQUE INDEX IF NOT EXISTS idx_correlation_unique
            ON messages(correlation_id)
            WHERE correlation_id IS NOT NULL AND type LIKE '%.response'
        """)

        # Channel subscriptions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS channel_subscriptions (
                channel_name TEXT NOT NULL,
                agent_id TEXT NOT NULL,
                subscribed_at TEXT NOT NULL,
                PRIMARY KEY (channel_name, agent_id)
            )
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_agent_channels
            ON channel_subscriptions(agent_id)
        """)

        # Agent status table
        cursor.execute("""
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

        # FIX: Broadcast delivery tracking table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS message_deliveries (
                message_id TEXT NOT NULL,
                agent_id TEXT NOT NULL,
                delivered_at TEXT NOT NULL,
                acknowledged_at TEXT,
                PRIMARY KEY (message_id, agent_id),
                FOREIGN KEY (message_id) REFERENCES messages(id) ON DELETE CASCADE
            )
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_undelivered
            ON message_deliveries(agent_id, delivered_at)
        """)

        # Dead letter queue
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS dead_letter_queue (
                id TEXT PRIMARY KEY,
                original_message TEXT NOT NULL,
                error TEXT NOT NULL,
                moved_at TEXT NOT NULL,
                retry_count INTEGER NOT NULL
            )
        """)

        # FIX: Job board in SQLite for transactional atomicity
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS job_board (
                task_id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                description TEXT,
                status TEXT NOT NULL DEFAULT 'open',
                assigned_to TEXT,
                priority INTEGER DEFAULT 5,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                dependencies TEXT,
                result TEXT,
                FOREIGN KEY (assigned_to) REFERENCES agent_status(agent_id)
            )
        """)

        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_open_tasks
            ON job_board(status, priority DESC)
            WHERE status = 'open'
        """)

        conn.commit()

        # Create version file
        version_file = self.comm_dir / "protocol_version.txt"
        version_file.write_text("1.0")

        # Initialize default channels
        default_channels = ["general", "urgent", "technical", "review"]
        for channel in default_channels:
            cursor.execute("""
                INSERT OR IGNORE INTO channel_subscriptions (channel_name, agent_id, subscribed_at)
                VALUES (?, 'system', ?)
            """, (channel, datetime.utcnow().isoformat()))

        conn.commit()
        conn.close()

        return {
            "status": "initialized",
            "version": "1.0",
            "db_path": str(self.db_path),
            "artifacts_dir": str(self.artifacts_dir),
            "default_channels": default_channels
        }

    def send_message(
        self,
        from_agent: str,
        message_type: str,
        payload: Dict[str, Any],
        to_agent: Optional[str] = None,
        channel: str = "general",
        priority: int = 5,
        correlation_id: Optional[str] = None,
        ttl_seconds: Optional[int] = None
    ) -> str:
        """
        Send a message.

        Args:
            from_agent: Sender agent ID
            message_type: Message type (e.g., "context.query", "task.claim")
            payload: Message data (must be JSON-serializable)
            to_agent: Recipient agent ID (None for broadcast)
            channel: Routing channel
            priority: Priority 1-10 (10 = highest)
            correlation_id: Optional ID to link request/response
            ttl_seconds: Time to live in seconds

        Returns:
            message_id: UUID of created message

        Raises:
            CommunicationError: If message cannot be sent
        """
        if not 1 <= priority <= 10:
            raise CommunicationError(f"Priority must be 1-10, got {priority}")

        message_id = str(uuid.uuid4())
        timestamp = datetime.utcnow().isoformat()

        # Calculate expiration
        expires_at = None
        if ttl_seconds:
            expires_at = (datetime.utcnow() + timedelta(seconds=ttl_seconds)).isoformat()

        # Serialize payload
        try:
            payload_json = json.dumps(payload)
        except (TypeError, ValueError) as e:
            raise CommunicationError(f"Payload not JSON-serializable: {e}")

        with self._transaction(immediate=True) as conn:
            cursor = conn.cursor()

            # Insert message
            cursor.execute("""
                INSERT INTO messages (
                    id, type, version, timestamp, correlation_id,
                    from_agent, to_agent, channel, priority, payload,
                    status, created_at, expires_at
                )
                VALUES (?, ?, '1.0', ?, ?, ?, ?, ?, ?, ?, 'pending', ?, ?)
            """, (
                message_id, message_type, timestamp, correlation_id,
                from_agent, to_agent, channel, priority, payload_json,
                datetime.utcnow().isoformat(), expires_at
            ))

            # If direct message, update recipient's pending count
            if to_agent:
                cursor.execute("""
                    UPDATE agent_status
                    SET messages_pending = messages_pending + 1
                    WHERE agent_id = ?
                """, (to_agent,))

        return message_id

    def receive_messages(
        self,
        agent_id: str,
        channels: List[str],
        limit: int = 10,
        message_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Receive messages for an agent.

        FIXED: Now properly handles broadcasts using subscription table.

        Args:
            agent_id: Agent ID receiving messages
            channels: List of channels to check
            limit: Maximum messages to return
            message_type: Optional filter by message type

        Returns:
            List of message dictionaries with parsed payloads
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        # Build query with proper broadcast handling
        placeholders = ','.join('?' * len(channels))
        type_filter = "AND m.type = ?" if message_type else ""
        type_params = [message_type] if message_type else []

        query = f"""
            SELECT m.* FROM messages m
            WHERE m.status = 'pending'
              AND (
                  -- Direct messages to this agent
                  (m.to_agent = ? AND m.channel IS NULL)
                  OR
                  -- Broadcast messages in subscribed channels not yet delivered
                  (m.to_agent IS NULL
                   AND m.channel IN ({placeholders})
                   AND EXISTS (
                       SELECT 1 FROM channel_subscriptions cs
                       WHERE cs.channel_name = m.channel
                         AND cs.agent_id = ?
                   )
                   AND NOT EXISTS (
                       SELECT 1 FROM message_deliveries md
                       WHERE md.message_id = m.id
                         AND md.agent_id = ?
                   ))
              )
              {type_filter}
              AND (m.expires_at IS NULL OR datetime(m.expires_at) > datetime('now'))
            ORDER BY m.priority DESC, m.timestamp ASC
            LIMIT ?
        """

        params = [agent_id] + channels + [agent_id, agent_id] + type_params + [limit]
        cursor.execute(query, params)

        messages = []
        for row in cursor.fetchall():
            msg = dict(row)
            # Parse payload JSON
            try:
                msg['payload'] = json.loads(msg['payload'])
            except json.JSONDecodeError:
                msg['payload'] = {"error": "Invalid JSON payload"}
            messages.append(msg)

        return messages

    def claim_message(self, agent_id: str, message_id: str) -> bool:
        """
        Atomically claim a message for processing.

        FIXED: Uses SQLite-compatible atomic UPDATE instead of SELECT FOR UPDATE.
        FIXED: Properly handles broadcast messages with delivery tracking.

        Args:
            agent_id: Agent claiming the message
            message_id: Message ID to claim

        Returns:
            True if claimed successfully, False if already claimed

        Raises:
            MessageNotFoundError: If message doesn't exist
        """
        with self._transaction(immediate=True) as conn:
            cursor = conn.cursor()

            # Check if message exists and get its type
            cursor.execute("""
                SELECT to_agent, status FROM messages WHERE id = ?
            """, (message_id,))

            row = cursor.fetchone()
            if not row:
                raise MessageNotFoundError(f"Message {message_id} not found")

            to_agent = row[0]
            status = row[1]

            if to_agent is None:
                # Broadcast message - record delivery to this agent
                try:
                    cursor.execute("""
                        INSERT INTO message_deliveries (message_id, agent_id, delivered_at)
                        VALUES (?, ?, datetime('now'))
                    """, (message_id, agent_id))
                    return True
                except sqlite3.IntegrityError:
                    # Already delivered to this agent
                    return False

            else:
                # Direct message - atomic UPDATE
                cursor.execute("""
                    UPDATE messages
                    SET status = 'processing',
                        last_delivered_at = datetime('now'),
                        delivery_count = delivery_count + 1
                    WHERE id = ?
                      AND status = 'pending'
                """, (message_id,))

                if cursor.rowcount == 1:
                    # Update agent's pending count
                    cursor.execute("""
                        UPDATE agent_status
                        SET messages_pending = messages_pending - 1
                        WHERE agent_id = ?
                    """, (agent_id,))
                    return True
                else:
                    # Already claimed
                    return False

    def complete_message(
        self,
        message_id: str,
        error: Optional[str] = None
    ) -> None:
        """
        Mark a message as complete or failed.

        Args:
            message_id: Message ID to complete
            error: Optional error message if processing failed
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        new_status = 'failed' if error else 'done'

        with self._transaction(immediate=True) as conn:
            cursor = conn.cursor()

            # Get current message info
            cursor.execute("""
                SELECT delivery_count, from_agent, to_agent, type, payload
                FROM messages WHERE id = ?
            """, (message_id,))

            row = cursor.fetchone()
            if not row:
                raise MessageNotFoundError(f"Message {message_id} not found")

            delivery_count = row[0]

            # Update status
            cursor.execute("""
                UPDATE messages
                SET status = ?,
                    error = ?
                WHERE id = ?
            """, (new_status, error, message_id))

            # If failed 3 times, move to DLQ
            if error and delivery_count >= 3:
                original_message = {
                    'id': message_id,
                    'from_agent': row[1],
                    'to_agent': row[2],
                    'type': row[3],
                    'payload': row[4]
                }

                cursor.execute("""
                    INSERT INTO dead_letter_queue (id, original_message, error, moved_at, retry_count)
                    VALUES (?, ?, ?, datetime('now'), ?)
                """, (str(uuid.uuid4()), json.dumps(original_message), error, delivery_count))

                # Delete from messages table
                cursor.execute("DELETE FROM messages WHERE id = ?", (message_id,))

            # Update agent stats
            cursor.execute("""
                UPDATE agent_status
                SET messages_processed = messages_processed + 1,
                    error_count = error_count + ?
                WHERE agent_id IN (
                    SELECT from_agent FROM messages WHERE id = ?
                    UNION
                    SELECT to_agent FROM messages WHERE id = ? AND to_agent IS NOT NULL
                )
            """, (1 if error else 0, message_id, message_id))

    def send_response(
        self,
        original_message: Dict[str, Any],
        response_payload: Dict[str, Any],
        artifact_path: Optional[str] = None
    ) -> str:
        """
        Send a response to a request message.

        Args:
            original_message: The original request message dict
            response_payload: Response data
            artifact_path: Optional path to large artifact

        Returns:
            message_id of the response
        """
        if not original_message.get('correlation_id'):
            raise CommunicationError("Original message has no correlation_id")

        # Add artifact reference if provided
        if artifact_path:
            response_payload['artifact_path'] = artifact_path

        # Determine response type
        request_type = original_message['type']
        if '.' in request_type:
            base_type = request_type.rsplit('.', 1)[0]
            response_type = f"{base_type}.response"
        else:
            response_type = "response"

        return self.send_message(
            from_agent=original_message['to_agent'],
            to_agent=original_message['from_agent'],
            message_type=response_type,
            payload=response_payload,
            channel=original_message['channel'],
            priority=original_message['priority'],
            correlation_id=original_message['correlation_id']
        )

    def subscribe_to_channel(self, agent_id: str, channel_name: str) -> None:
        """Subscribe an agent to a channel."""
        conn = self._get_connection()

        with self._transaction(immediate=True) as conn:
            conn.execute("""
                INSERT OR IGNORE INTO channel_subscriptions (channel_name, agent_id, subscribed_at)
                VALUES (?, ?, datetime('now'))
            """, (channel_name, agent_id))

    def unsubscribe_from_channel(self, agent_id: str, channel_name: str) -> None:
        """Unsubscribe an agent from a channel."""
        conn = self._get_connection()

        with self._transaction(immediate=True) as conn:
            conn.execute("""
                DELETE FROM channel_subscriptions
                WHERE channel_name = ? AND agent_id = ?
            """, (channel_name, agent_id))

    def get_subscribed_channels(self, agent_id: str) -> List[str]:
        """Get list of channels an agent is subscribed to."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT channel_name FROM channel_subscriptions
            WHERE agent_id = ?
            ORDER BY channel_name
        """, (agent_id,))

        return [row[0] for row in cursor.fetchall()]

    def send_heartbeat(
        self,
        agent_id: str,
        status: str = "active",
        current_task: Optional[str] = None
    ) -> None:
        """
        Update agent's heartbeat status.

        Args:
            agent_id: Agent ID
            status: Status string (active, idle, degraded, failed)
            current_task: Optional description of current work
        """
        conn = self._get_connection()

        with self._transaction(immediate=True) as conn:
            conn.execute("""
                INSERT INTO agent_status (agent_id, status, current_task, last_heartbeat)
                VALUES (?, ?, ?, datetime('now'))
                ON CONFLICT(agent_id) DO UPDATE SET
                    status = excluded.status,
                    current_task = excluded.current_task,
                    last_heartbeat = excluded.last_heartbeat
            """, (agent_id, status, current_task))

    def get_agent_health(self, agent_id: str) -> Optional[Dict[str, Any]]:
        """Get agent's health status."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM agent_status WHERE agent_id = ?
        """, (agent_id,))

        row = cursor.fetchone()
        return dict(row) if row else None

    def cleanup_expired_messages(self) -> int:
        """
        Remove expired messages.

        Returns:
            Number of messages deleted
        """
        with self._transaction(immediate=True) as conn:
            cursor = conn.cursor()

            cursor.execute("""
                DELETE FROM messages
                WHERE expires_at IS NOT NULL
                  AND datetime(expires_at) <= datetime('now')
            """)

            count = cursor.rowcount
            return count

    # Job board methods (FIXED: Now transactional with messages)

    def create_task(
        self,
        task_id: str,
        title: str,
        description: str = "",
        priority: int = 5,
        dependencies: Optional[List[str]] = None
    ) -> str:
        """Create a new task on the job board."""
        conn = self._get_connection()

        deps_json = json.dumps(dependencies) if dependencies else None

        with self._transaction(immediate=True) as conn:
            conn.execute("""
                INSERT INTO job_board (task_id, title, description, priority, dependencies, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, datetime('now'), datetime('now'))
            """, (task_id, title, description, priority, deps_json))

        return task_id

    def claim_task(self, agent_id: str, task_id: str) -> bool:
        """
        Atomically claim a task.

        Returns:
            True if claimed, False if already taken
        """
        with self._transaction(immediate=True) as conn:
            cursor = conn.cursor()

            cursor.execute("""
                UPDATE job_board
                SET status = 'assigned',
                    assigned_to = ?,
                    updated_at = datetime('now')
                WHERE task_id = ?
                  AND status = 'open'
            """, (agent_id, task_id))

            count = cursor.rowcount
            # Transaction commits when exiting the with block

        return count == 1

    def update_task_status(
        self,
        task_id: str,
        status: str,
        result: Optional[str] = None
    ) -> None:
        """Update task status."""
        conn = self._get_connection()

        with self._transaction(immediate=True) as conn:
            conn.execute("""
                UPDATE job_board
                SET status = ?,
                    result = ?,
                    updated_at = datetime('now')
                WHERE task_id = ?
            """, (status, result, task_id))

    def get_open_tasks(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get list of open tasks."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT * FROM job_board
            WHERE status = 'open'
            ORDER BY priority DESC, created_at ASC
            LIMIT ?
        """, (limit,))

        tasks = []
        for row in cursor.fetchall():
            task = dict(row)
            if task['dependencies']:
                task['dependencies'] = json.loads(task['dependencies'])
            tasks.append(task)

        return tasks
