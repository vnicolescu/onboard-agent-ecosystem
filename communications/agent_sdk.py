#!/usr/bin/env python3
"""
Agent SDK - Simple, transparent messaging for agents

This is the agent-facing API. It hides complexity and provides clear,
simple methods with helpful error messages.

Example usage:
    messenger = AgentMessenger("my-agent-id")
    messenger.send("other-agent", "context.query", {"query": "What framework?"})
    response = messenger.ask("context-manager", "context.query", {"query": "..."})
"""

import time
import uuid
from typing import Dict, List, Optional, Any

from .core import CommunicationSystem, AlreadyClaimedError, MessageNotFoundError


class AgentMessenger:
    """
    Simple, transparent messaging interface for agents.

    This class provides a friendly API that handles:
    - Automatic channel subscriptions
    - Request/response patterns with waiting
    - Clear error messages
    - Heartbeat management
    """

    def __init__(self, agent_id: str, project_root: str = "."):
        """
        Initialize messenger for an agent.

        Args:
            agent_id: Unique identifier for this agent
            project_root: Path to project root (usually ".")
        """
        self.agent_id = agent_id
        self.comm = CommunicationSystem(project_root)

        # Ensure agent is registered
        self.comm.send_heartbeat(agent_id, "active")

        # Auto-subscribe to general channel
        self.comm.subscribe_to_channel(agent_id, "general")

    def send(
        self,
        to: str,
        message_type: str,
        data: Dict[str, Any],
        priority: int = 5,
        channel: str = "general"
    ) -> str:
        """
        Send a message (fire and forget).

        Args:
            to: Recipient agent ID (or None for broadcast)
            message_type: Type of message (e.g., "task.update", "context.query")
            data: Message payload (dict)
            priority: Priority 1-10 (default 5, urgent = 10)
            channel: Channel name (default "general")

        Returns:
            message_id: UUID of sent message

        Example:
            msg_id = messenger.send(
                "context-manager",
                "context.query",
                {"query": "Frontend context needed"}
            )
        """
        to_agent = to if to else None

        return self.comm.send_message(
            from_agent=self.agent_id,
            message_type=message_type,
            payload=data,
            to_agent=to_agent,
            channel=channel,
            priority=priority
        )

    def broadcast(
        self,
        message_type: str,
        data: Dict[str, Any],
        channel: str = "general",
        priority: int = 5
    ) -> str:
        """
        Broadcast a message to all agents on a channel.

        Args:
            message_type: Type of message
            data: Message payload
            channel: Channel to broadcast on
            priority: Priority 1-10

        Returns:
            message_id

        Example:
            messenger.broadcast(
                "vote.initiate",
                {
                    "topic": "Use TypeScript?",
                    "options": ["yes", "no"],
                    "deadline": "2025-11-08T16:00:00Z"
                }
            )
        """
        return self.comm.send_message(
            from_agent=self.agent_id,
            message_type=message_type,
            payload=data,
            to_agent=None,  # Broadcast
            channel=channel,
            priority=priority
        )

    def receive(
        self,
        limit: int = 10,
        message_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Receive pending messages.

        Args:
            limit: Maximum number of messages to retrieve
            message_type: Optional filter by message type

        Returns:
            List of messages (newest first by priority)

        Example:
            messages = messenger.receive(limit=5)
            for msg in messages:
                print(f"From {msg['from_agent']}: {msg['payload']}")
        """
        channels = self.comm.get_subscribed_channels(self.agent_id)

        return self.comm.receive_messages(
            agent_id=self.agent_id,
            channels=channels,
            limit=limit,
            message_type=message_type
        )

    def claim(self, message_id: str) -> bool:
        """
        Claim a message for processing.

        Args:
            message_id: Message ID to claim

        Returns:
            True if claimed, False if already taken

        Example:
            messages = messenger.receive()
            for msg in messages:
                if messenger.claim(msg['id']):
                    # Process it
                    result = process(msg)
                    messenger.complete(msg['id'])
        """
        try:
            return self.comm.claim_message(self.agent_id, message_id)
        except MessageNotFoundError:
            return False

    def complete(self, message_id: str, error: Optional[str] = None) -> None:
        """
        Mark a message as processed.

        Args:
            message_id: Message ID to complete
            error: Optional error message if processing failed

        Example:
            if messenger.claim(msg['id']):
                try:
                    process(msg)
                    messenger.complete(msg['id'])
                except Exception as e:
                    messenger.complete(msg['id'], error=str(e))
        """
        self.comm.complete_message(message_id, error)

    def ask(
        self,
        to: str,
        message_type: str,
        data: Dict[str, Any],
        timeout: float = 30.0,
        priority: int = 5
    ) -> Optional[Dict[str, Any]]:
        """
        Send a request and wait for response (request/response pattern).

        This method:
        1. Sends a message with a correlation ID
        2. Waits for a response with the same correlation ID
        3. Returns the response payload

        Args:
            to: Recipient agent ID
            message_type: Request type (response will be "{type}.response")
            data: Request payload
            timeout: How long to wait for response (seconds)
            priority: Priority 1-10

        Returns:
            Response payload dict, or None if timeout

        Example:
            response = messenger.ask(
                "context-manager",
                "context.query",
                {"query": "Frontend framework?"},
                timeout=30
            )
            if response:
                print(f"Context: {response['payload']['context']}")
            else:
                print("No response received!")
        """
        # Generate correlation ID
        correlation_id = str(uuid.uuid4())

        # Send request
        self.comm.send_message(
            from_agent=self.agent_id,
            message_type=message_type,
            payload=data,
            to_agent=to,
            channel="general",
            priority=priority,
            correlation_id=correlation_id
        )

        # Wait for response with exponential backoff
        start = time.time()
        backoff = 0.01  # Start at 10ms
        max_backoff = 1.0  # Max 1 second

        channels = self.comm.get_subscribed_channels(self.agent_id)

        while time.time() - start < timeout:
            messages = self.comm.receive_messages(
                agent_id=self.agent_id,
                channels=channels,
                limit=50
            )

            for msg in messages:
                if msg.get('correlation_id') == correlation_id:
                    # Found response!
                    if self.comm.claim_message(self.agent_id, msg['id']):
                        self.comm.complete_message(msg['id'])
                        return msg

            # Exponential backoff
            time.sleep(backoff)
            backoff = min(backoff * 2, max_backoff)

        # Timeout
        return None

    def reply(
        self,
        original_message: Dict[str, Any],
        response_data: Dict[str, Any],
        artifact_path: Optional[str] = None
    ) -> str:
        """
        Reply to a message (automatically handles correlation ID).

        Args:
            original_message: The message you're replying to
            response_data: Response payload
            artifact_path: Optional path to large artifact file

        Returns:
            message_id of response

        Example:
            messages = messenger.receive()
            for msg in messages:
                if messenger.claim(msg['id']):
                    if msg['type'] == 'context.query':
                        context = get_context(msg['payload']['query'])
                        messenger.reply(msg, {"context": context})
                        messenger.complete(msg['id'])
        """
        return self.comm.send_response(
            original_message=original_message,
            response_payload=response_data,
            artifact_path=artifact_path
        )

    def subscribe(self, channel: str) -> None:
        """
        Subscribe to a channel.

        Args:
            channel: Channel name (e.g., "technical", "urgent")

        Example:
            messenger.subscribe("urgent")  # Get critical alerts
            messenger.subscribe("technical")  # Technical discussions
        """
        self.comm.subscribe_to_channel(self.agent_id, channel)

    def unsubscribe(self, channel: str) -> None:
        """Unsubscribe from a channel."""
        self.comm.unsubscribe_from_channel(self.agent_id, channel)

    def channels(self) -> List[str]:
        """Get list of subscribed channels."""
        return self.comm.get_subscribed_channels(self.agent_id)

    def heartbeat(self, status: str = "active", task: Optional[str] = None) -> None:
        """
        Send heartbeat (let system know you're alive).

        Args:
            status: Status (active, idle, degraded, failed)
            task: Optional description of current work

        Example:
            messenger.heartbeat("active", "Processing frontend task")
        """
        self.comm.send_heartbeat(self.agent_id, status, task)

    def health(self) -> Optional[Dict[str, Any]]:
        """Get this agent's health status."""
        return self.comm.get_agent_health(self.agent_id)

    # Job board helpers

    def claim_task(self, task_id: str) -> bool:
        """
        Claim a task from the job board.

        Returns:
            True if claimed, False if already taken

        Example:
            tasks = messenger.get_tasks()
            for task in tasks:
                if messenger.claim_task(task['task_id']):
                    # Work on it
                    do_work(task)
                    messenger.complete_task(task['task_id'], "done")
        """
        claimed = self.comm.claim_task(self.agent_id, task_id)

        # Also broadcast claim to prevent races
        if claimed:
            self.broadcast(
                "task.claimed",
                {"task_id": task_id, "agent_id": self.agent_id},
                priority=8
            )

        return claimed

    def get_tasks(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get list of available tasks from job board."""
        return self.comm.get_open_tasks(limit)

    def update_task(
        self,
        task_id: str,
        status: str,
        result: Optional[str] = None
    ) -> None:
        """
        Update task status.

        Args:
            task_id: Task ID
            status: New status (assigned, in-progress, done, failed)
            result: Optional result description

        Example:
            messenger.update_task("task-123", "in-progress")
            # ... do work ...
            messenger.update_task("task-123", "done", "Implemented feature X")
        """
        self.comm.update_task_status(task_id, status, result)

        # Broadcast update
        self.broadcast(
            "task.update",
            {
                "task_id": task_id,
                "status": status,
                "agent_id": self.agent_id
            }
        )

    def complete_task(self, task_id: str, result: str = "completed") -> None:
        """Mark task as complete."""
        self.update_task(task_id, "done", result)

    # Utility methods

    def wait_for_messages(
        self,
        message_type: Optional[str] = None,
        timeout: float = 60.0,
        callback=None
    ) -> List[Dict[str, Any]]:
        """
        Wait for messages to arrive (blocking with timeout).

        Args:
            message_type: Optional filter by type
            timeout: How long to wait (seconds)
            callback: Optional function to call for each message

        Returns:
            List of messages received

        Example:
            # Wait for votes
            votes = messenger.wait_for_messages(
                message_type="vote.cast",
                timeout=60,
                callback=lambda msg: print(f"Vote from {msg['from_agent']}")
            )
        """
        collected = []
        start = time.time()
        backoff = 0.1

        while time.time() - start < timeout:
            messages = self.receive(message_type=message_type)

            for msg in messages:
                if self.claim(msg['id']):
                    collected.append(msg)
                    if callback:
                        callback(msg)
                    self.complete(msg['id'])

            if collected:
                return collected

            time.sleep(backoff)
            backoff = min(backoff * 1.5, 2.0)

        return collected

    def __repr__(self) -> str:
        """String representation."""
        return f"AgentMessenger(agent_id='{self.agent_id}')"
