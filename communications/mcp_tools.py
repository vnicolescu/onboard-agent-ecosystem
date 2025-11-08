#!/usr/bin/env python3
"""
MCP Tools for Onboard Agent Communication System

This module exposes the communication system as MCP tools that can be used
by agents in the Claude Agent SDK.

Author: SDK Migration v2.0
"""

from typing import Any, Dict, Optional, List
from claude_agent_sdk import tool
from .core import CommunicationSystem, CommunicationError
from .voting import VotingSystem


# Initialize communication and voting systems
_comm = None
_voting = None


def get_comm_system(project_root: str = ".") -> CommunicationSystem:
    """Get or create communication system singleton."""
    global _comm
    if _comm is None:
        _comm = CommunicationSystem(project_root)
    return _comm


def get_voting_system(project_root: str = ".") -> VotingSystem:
    """Get or create voting system singleton."""
    global _voting
    if _voting is None:
        _voting = VotingSystem(project_root)
    return _voting


# =============================================================================
# Communication Tools
# =============================================================================

@tool(
    name="comm-send-message",
    description="Send a message to another agent or broadcast to a channel. Use for agent-to-agent communication, status updates, or broadcasting information.",
    input_schema={
        "from_agent": str,
        "message_type": str,
        "payload": dict,
        "to_agent": Optional[str],
        "channel": str,
        "priority": int,
        "correlation_id": Optional[str],
        "ttl_seconds": Optional[int]
    }
)
async def send_message(args: Dict[str, Any]) -> Dict[str, Any]:
    """
    Send a message through the communication system.

    Args:
        from_agent: Sender agent ID
        message_type: Message type (e.g., "context.query", "task.update")
        payload: Message data (JSON-serializable dict)
        to_agent: Recipient agent ID (None for broadcast)
        channel: Routing channel (default "general")
        priority: Priority 1-10 (10 = highest, default 5)
        correlation_id: Optional ID to link request/response
        ttl_seconds: Time to live in seconds (optional)

    Returns:
        {"message_id": str, "status": "sent"}

    Example:
        send_message({
            "from_agent": "frontend-dev",
            "to_agent": "context-manager",
            "message_type": "context.query",
            "payload": {"query": "What are the frontend patterns?"},
            "channel": "general",
            "priority": 7
        })
    """
    try:
        comm = get_comm_system()

        message_id = comm.send_message(
            from_agent=args["from_agent"],
            message_type=args["message_type"],
            payload=args["payload"],
            to_agent=args.get("to_agent"),
            channel=args.get("channel", "general"),
            priority=args.get("priority", 5),
            correlation_id=args.get("correlation_id"),
            ttl_seconds=args.get("ttl_seconds")
        )

        return {
            "content": [{
                "type": "text",
                "text": f"✅ Message sent successfully\nMessage ID: {message_id}"
            }],
            "message_id": message_id,
            "status": "sent"
        }
    except CommunicationError as e:
        return {
            "content": [{
                "type": "text",
                "text": f"❌ Failed to send message: {str(e)}"
            }],
            "is_error": True
        }


@tool(
    name="comm-receive-messages",
    description="Receive pending messages for the current agent. Use to check for incoming messages, requests, or broadcasts.",
    input_schema={
        "agent_id": str,
        "channels": list,
        "limit": int,
        "message_type": Optional[str]
    }
)
async def receive_messages(args: Dict[str, Any]) -> Dict[str, Any]:
    """
    Receive pending messages for an agent.

    Args:
        agent_id: Agent ID receiving messages
        channels: List of channels to check
        limit: Maximum messages to return (default 10)
        message_type: Optional filter by message type

    Returns:
        {"messages": [...], "count": int}

    Example:
        receive_messages({
            "agent_id": "frontend-dev",
            "channels": ["general", "technical"],
            "limit": 10
        })
    """
    try:
        comm = get_comm_system()

        messages = comm.receive_messages(
            agent_id=args["agent_id"],
            channels=args.get("channels", ["general"]),
            limit=args.get("limit", 10),
            message_type=args.get("message_type")
        )

        # Format messages for readability
        formatted = []
        for msg in messages:
            formatted.append({
                "id": msg["id"],
                "from": msg["from_agent"],
                "to": msg.get("to_agent", "broadcast"),
                "type": msg["type"],
                "payload": msg["payload"],
                "priority": msg["priority"],
                "timestamp": msg["timestamp"]
            })

        return {
            "content": [{
                "type": "text",
                "text": f"📬 Received {len(formatted)} message(s)\n\n" +
                       "\n\n".join([
                           f"Message {i+1}:\n"
                           f"  ID: {m['id']}\n"
                           f"  From: {m['from']}\n"
                           f"  Type: {m['type']}\n"
                           f"  Payload: {m['payload']}"
                           for i, m in enumerate(formatted)
                       ])
            }],
            "messages": formatted,
            "count": len(formatted)
        }
    except Exception as e:
        return {
            "content": [{
                "type": "text",
                "text": f"❌ Failed to receive messages: {str(e)}"
            }],
            "is_error": True
        }


@tool(
    name="comm-claim-message",
    description="Atomically claim a message for processing. Use to ensure only one agent processes a message. Returns true if claimed successfully.",
    input_schema={
        "agent_id": str,
        "message_id": str
    }
)
async def claim_message(args: Dict[str, Any]) -> Dict[str, Any]:
    """
    Atomically claim a message for processing.

    Args:
        agent_id: Agent claiming the message
        message_id: Message ID to claim

    Returns:
        {"claimed": bool, "message": str}

    Example:
        claim_message({
            "agent_id": "frontend-dev",
            "message_id": "msg-abc123"
        })
    """
    try:
        comm = get_comm_system()
        claimed = comm.claim_message(args["agent_id"], args["message_id"])

        if claimed:
            return {
                "content": [{
                    "type": "text",
                    "text": f"✅ Successfully claimed message {args['message_id']}"
                }],
                "claimed": True
            }
        else:
            return {
                "content": [{
                    "type": "text",
                    "text": f"⚠️ Message {args['message_id']} already claimed by another agent"
                }],
                "claimed": False
            }
    except Exception as e:
        return {
            "content": [{
                "type": "text",
                "text": f"❌ Failed to claim message: {str(e)}"
            }],
            "is_error": True
        }


@tool(
    name="comm-complete-message",
    description="Mark a message as processed (completed or failed). Use after finishing message processing.",
    input_schema={
        "message_id": str,
        "error": Optional[str]
    }
)
async def complete_message(args: Dict[str, Any]) -> Dict[str, Any]:
    """
    Mark a message as complete or failed.

    Args:
        message_id: Message ID to complete
        error: Optional error message if processing failed

    Returns:
        {"status": str, "message": str}

    Example:
        complete_message({
            "message_id": "msg-abc123",
            "error": None  # or error message if failed
        })
    """
    try:
        comm = get_comm_system()
        comm.complete_message(args["message_id"], args.get("error"))

        status = "failed" if args.get("error") else "completed"
        return {
            "content": [{
                "type": "text",
                "text": f"✅ Message {args['message_id']} marked as {status}"
            }],
            "status": status
        }
    except Exception as e:
        return {
            "content": [{
                "type": "text",
                "text": f"❌ Failed to complete message: {str(e)}"
            }],
            "is_error": True
        }


@tool(
    name="comm-send-heartbeat",
    description="Update agent health status. Use to let the system know you're alive and what you're working on.",
    input_schema={
        "agent_id": str,
        "status": str,
        "current_task": Optional[str]
    }
)
async def send_heartbeat(args: Dict[str, Any]) -> Dict[str, Any]:
    """
    Send agent heartbeat.

    Args:
        agent_id: Agent ID
        status: Status (active, idle, degraded, failed)
        current_task: Optional description of current work

    Returns:
        {"status": "ok"}

    Example:
        send_heartbeat({
            "agent_id": "frontend-dev",
            "status": "active",
            "current_task": "Implementing login form"
        })
    """
    try:
        comm = get_comm_system()
        comm.send_heartbeat(
            args["agent_id"],
            args.get("status", "active"),
            args.get("current_task")
        )

        return {
            "content": [{
                "type": "text",
                "text": f"💓 Heartbeat sent for {args['agent_id']}"
            }],
            "status": "ok"
        }
    except Exception as e:
        return {
            "content": [{
                "type": "text",
                "text": f"❌ Failed to send heartbeat: {str(e)}"
            }],
            "is_error": True
        }


@tool(
    name="comm-get-agent-health",
    description="Get health status of an agent. Use to check if another agent is available before sending requests.",
    input_schema={
        "agent_id": str
    }
)
async def get_agent_health(args: Dict[str, Any]) -> Dict[str, Any]:
    """
    Get agent health status.

    Args:
        agent_id: Agent ID to check

    Returns:
        Health status dict or None if agent not found

    Example:
        get_agent_health({"agent_id": "context-manager"})
    """
    try:
        comm = get_comm_system()
        health = comm.get_agent_health(args["agent_id"])

        if health:
            return {
                "content": [{
                    "type": "text",
                    "text": f"🏥 Health status for {args['agent_id']}:\n"
                           f"  Status: {health['status']}\n"
                           f"  Last heartbeat: {health['last_heartbeat']}\n"
                           f"  Current task: {health.get('current_task', 'None')}\n"
                           f"  Messages pending: {health.get('messages_pending', 0)}"
                }],
                "health": health,
                "available": health["status"] in ["active", "idle"]
            }
        else:
            return {
                "content": [{
                    "type": "text",
                    "text": f"⚠️ Agent {args['agent_id']} not found or never sent heartbeat"
                }],
                "health": None,
                "available": False
            }
    except Exception as e:
        return {
            "content": [{
                "type": "text",
                "text": f"❌ Failed to get health: {str(e)}"
            }],
            "is_error": True
        }


@tool(
    name="comm-get-broadcast-status",
    description="Check how many agents received a broadcast message. Use to verify broadcast delivery.",
    input_schema={
        "message_id": str
    }
)
async def get_broadcast_status(args: Dict[str, Any]) -> Dict[str, Any]:
    """
    Get broadcast delivery status.

    Args:
        message_id: Broadcast message ID

    Returns:
        {"delivered": int, "total_subscribers": int, "percentage": float}

    Example:
        get_broadcast_status({"message_id": "msg-abc123"})
    """
    try:
        comm = get_comm_system()
        conn = comm._get_connection()
        cursor = conn.cursor()

        # Get delivery statistics
        cursor.execute("""
            SELECT
                COUNT(DISTINCT md.agent_id) as delivered,
                (SELECT COUNT(*) FROM channel_subscriptions cs
                 WHERE cs.channel_name = m.channel) as total_subscribers,
                m.channel
            FROM messages m
            LEFT JOIN message_deliveries md ON md.message_id = m.id
            WHERE m.id = ?
            GROUP BY m.channel
        """, (args["message_id"],))

        row = cursor.fetchone()

        if not row:
            return {
                "content": [{
                    "type": "text",
                    "text": f"❌ Message {args['message_id']} not found"
                }],
                "is_error": True
            }

        delivered = row[0]
        total = row[1]
        channel = row[2]
        percentage = (delivered / total * 100) if total > 0 else 0

        return {
            "content": [{
                "type": "text",
                "text": f"📊 Broadcast delivery status:\n"
                       f"Channel: {channel}\n"
                       f"Delivered: {delivered}/{total} agents ({percentage:.1f}%)\n"
                       f"Status: {'✅ Complete' if delivered == total else '⚠️ Pending'}"
            }],
            "delivered": delivered,
            "total_subscribers": total,
            "percentage": percentage,
            "complete": delivered == total
        }
    except Exception as e:
        return {
            "content": [{
                "type": "text",
                "text": f"❌ Failed to get broadcast status: {str(e)}"
            }],
            "is_error": True
        }


@tool(
    name="comm-subscribe-channel",
    description="Subscribe to a communication channel. Use to receive broadcasts on specific channels.",
    input_schema={
        "agent_id": str,
        "channel_name": str
    }
)
async def subscribe_channel(args: Dict[str, Any]) -> Dict[str, Any]:
    """
    Subscribe to a channel.

    Args:
        agent_id: Agent ID
        channel_name: Channel to subscribe to

    Returns:
        {"status": "subscribed"}

    Example:
        subscribe_channel({
            "agent_id": "frontend-dev",
            "channel_name": "technical"
        })
    """
    try:
        comm = get_comm_system()
        comm.subscribe_to_channel(args["agent_id"], args["channel_name"])

        return {
            "content": [{
                "type": "text",
                "text": f"✅ Subscribed to channel: {args['channel_name']}"
            }],
            "status": "subscribed"
        }
    except Exception as e:
        return {
            "content": [{
                "type": "text",
                "text": f"❌ Failed to subscribe: {str(e)}"
            }],
            "is_error": True
        }


# =============================================================================
# Job Board Tools
# =============================================================================

@tool(
    name="jobboard-create-task",
    description="Create a new task on the job board. Use when you want to delegate work to other agents.",
    input_schema={
        "task_id": str,
        "title": str,
        "description": str,
        "priority": int,
        "dependencies": Optional[list]
    }
)
async def create_task(args: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create a new task on the job board.

    Args:
        task_id: Unique task identifier
        title: Task title
        description: Detailed description
        priority: Priority 1-10 (10 = highest)
        dependencies: Optional list of task IDs this depends on

    Returns:
        {"task_id": str, "status": "created"}
    """
    try:
        comm = get_comm_system()
        task_id = comm.create_task(
            task_id=args["task_id"],
            title=args["title"],
            description=args.get("description", ""),
            priority=args.get("priority", 5),
            dependencies=args.get("dependencies")
        )

        return {
            "content": [{
                "type": "text",
                "text": f"✅ Task created: {args['title']}\nTask ID: {task_id}"
            }],
            "task_id": task_id,
            "status": "created"
        }
    except Exception as e:
        return {
            "content": [{
                "type": "text",
                "text": f"❌ Failed to create task: {str(e)}"
            }],
            "is_error": True
        }


@tool(
    name="jobboard-claim-task",
    description="Atomically claim a task from the job board. Use when you want to work on a task. Returns true if claimed successfully.",
    input_schema={
        "agent_id": str,
        "task_id": str
    }
)
async def claim_task(args: Dict[str, Any]) -> Dict[str, Any]:
    """
    Atomically claim a task.

    Args:
        agent_id: Agent claiming the task
        task_id: Task ID to claim

    Returns:
        {"claimed": bool, "task_id": str}
    """
    try:
        comm = get_comm_system()
        claimed = comm.claim_task(args["agent_id"], args["task_id"])

        if claimed:
            return {
                "content": [{
                    "type": "text",
                    "text": f"✅ Successfully claimed task {args['task_id']}"
                }],
                "claimed": True,
                "task_id": args["task_id"]
            }
        else:
            return {
                "content": [{
                    "type": "text",
                    "text": f"⚠️ Task {args['task_id']} already claimed by another agent"
                }],
                "claimed": False
            }
    except Exception as e:
        return {
            "content": [{
                "type": "text",
                "text": f"❌ Failed to claim task: {str(e)}"
            }],
            "is_error": True
        }


@tool(
    name="jobboard-update-task",
    description="Update task status. Use to report progress or completion.",
    input_schema={
        "task_id": str,
        "status": str,
        "result": Optional[str]
    }
)
async def update_task(args: Dict[str, Any]) -> Dict[str, Any]:
    """
    Update task status.

    Args:
        task_id: Task ID
        status: New status (assigned, in-progress, done, failed)
        result: Optional result description

    Returns:
        {"status": "updated"}
    """
    try:
        comm = get_comm_system()
        comm.update_task_status(
            task_id=args["task_id"],
            status=args["status"],
            result=args.get("result")
        )

        return {
            "content": [{
                "type": "text",
                "text": f"✅ Task {args['task_id']} updated to: {args['status']}"
            }],
            "status": "updated"
        }
    except Exception as e:
        return {
            "content": [{
                "type": "text",
                "text": f"❌ Failed to update task: {str(e)}"
            }],
            "is_error": True
        }


@tool(
    name="jobboard-get-tasks",
    description="Get open tasks from the job board. Use to see what work is available.",
    input_schema={
        "limit": int
    }
)
async def get_tasks(args: Dict[str, Any]) -> Dict[str, Any]:
    """
    Get list of open tasks.

    Args:
        limit: Maximum tasks to return (default 20)

    Returns:
        {"tasks": [...], "count": int}
    """
    try:
        comm = get_comm_system()
        tasks = comm.get_open_tasks(args.get("limit", 20))

        # Format tasks for readability
        formatted = []
        for task in tasks:
            formatted.append({
                "task_id": task["task_id"],
                "title": task["title"],
                "description": task.get("description", ""),
                "priority": task["priority"],
                "status": task["status"],
                "created_at": task["created_at"]
            })

        return {
            "content": [{
                "type": "text",
                "text": f"📋 Found {len(formatted)} open task(s)\n\n" +
                       "\n\n".join([
                           f"Task {i+1}: {t['title']}\n"
                           f"  ID: {t['task_id']}\n"
                           f"  Priority: {t['priority']}\n"
                           f"  Description: {t['description']}"
                           for i, t in enumerate(formatted)
                       ])
            }],
            "tasks": formatted,
            "count": len(formatted)
        }
    except Exception as e:
        return {
            "content": [{
                "type": "text",
                "text": f"❌ Failed to get tasks: {str(e)}"
            }],
            "is_error": True
        }


# =============================================================================
# Voting Tools
# =============================================================================

@tool(
    name="voting-initiate",
    description="Initiate a new vote for agent consensus. Use when you need collective decision-making.",
    input_schema={
        "proposer_agent": str,
        "topic": str,
        "options": list,
        "mechanism": str,
        "eligible_voters": Optional[list],
        "timeout_hours": int,
        "description": Optional[str]
    }
)
async def initiate_vote(args: Dict[str, Any]) -> Dict[str, Any]:
    """
    Initiate a new vote.

    Args:
        proposer_agent: Agent proposing the vote
        topic: Vote topic/question
        options: List of voting options
        mechanism: Voting mechanism (simple_majority, weighted, consensus)
        eligible_voters: Optional list of eligible voter IDs
        timeout_hours: Hours until vote closes (default 24)
        description: Optional detailed description

    Returns:
        {"vote_id": str, "status": "initiated"}
    """
    try:
        voting = get_voting_system()

        # FIX Issue #3: Validate minimum voter threshold
        eligible_voters = args.get("eligible_voters")
        if eligible_voters and len(eligible_voters) < 3:
            return {
                "content": [{
                    "type": "text",
                    "text": f"❌ Insufficient voters: need at least 3, found {len(eligible_voters)}\n"
                           f"Cannot initiate meaningful vote with so few participants."
                }],
                "is_error": True
            }

        vote_id = voting.initiate_vote(
            proposer_agent=args["proposer_agent"],
            topic=args["topic"],
            options=args["options"],
            mechanism=args.get("mechanism", "simple_majority"),
            eligible_voters=eligible_voters,
            timeout_hours=args.get("timeout_hours", 24),
            description=args.get("description")
        )

        # Also check if auto-detected voters are sufficient
        vote_status = voting.get_vote_status(vote_id)
        actual_voters = len(vote_status.get("eligible_voters", []))
        if actual_voters < 3:
            return {
                "content": [{
                    "type": "text",
                    "text": f"⚠️ Warning: Only {actual_voters} eligible voters detected\n"
                           f"Votes with fewer than 3 participants may not be meaningful.\n"
                           f"Vote ID: {vote_id}"
                }],
                "vote_id": vote_id,
                "status": "initiated_with_warning"
            }

        return {
            "content": [{
                "type": "text",
                "text": f"🗳️ Vote initiated: {args['topic']}\n"
                       f"Vote ID: {vote_id}\n"
                       f"Options: {', '.join(args['options'])}\n"
                       f"Mechanism: {args.get('mechanism', 'simple_majority')}\n"
                       f"Eligible voters: {actual_voters}"
            }],
            "vote_id": vote_id,
            "status": "initiated"
        }
    except Exception as e:
        return {
            "content": [{
                "type": "text",
                "text": f"❌ Failed to initiate vote: {str(e)}"
            }],
            "is_error": True
        }


@tool(
    name="voting-cast-vote",
    description="Cast a vote. Use to participate in a vote and record your choice.",
    input_schema={
        "agent_id": str,
        "vote_id": str,
        "choice": str,
        "reasoning": str
    }
)
async def cast_vote(args: Dict[str, Any]) -> Dict[str, Any]:
    """
    Cast a vote.

    Args:
        agent_id: Agent casting the vote
        vote_id: Vote ID
        choice: Selected option
        reasoning: Optional reasoning for choice

    Returns:
        {"success": bool, "votes_cast": int}
    """
    try:
        voting = get_voting_system()
        result = voting.cast_vote(
            agent_id=args["agent_id"],
            vote_id=args["vote_id"],
            choice=args["choice"],
            reasoning=args.get("reasoning", "")
        )

        if result.get("error"):
            return {
                "content": [{
                    "type": "text",
                    "text": f"❌ {result['error']}"
                }],
                "is_error": True
            }

        return {
            "content": [{
                "type": "text",
                "text": f"✅ Vote cast successfully\n"
                       f"Choice: {args['choice']}\n"
                       f"Votes cast so far: {result.get('votes_cast', 0)}"
            }],
            "success": True,
            "votes_cast": result.get("votes_cast", 0)
        }
    except Exception as e:
        return {
            "content": [{
                "type": "text",
                "text": f"❌ Failed to cast vote: {str(e)}"
            }],
            "is_error": True
        }


@tool(
    name="voting-tally",
    description="Tally votes and determine outcome. Use to close a vote and get results.",
    input_schema={
        "vote_id": str,
        "force": bool
    }
)
async def tally_vote(args: Dict[str, Any]) -> Dict[str, Any]:
    """
    Tally votes and get results.

    Args:
        vote_id: Vote ID to tally
        force: Force tally even if deadline not reached

    Returns:
        {"outcome": str, "tally": dict, "total_votes": int}
    """
    try:
        voting = get_voting_system()
        result = voting.tally_vote(
            vote_id=args["vote_id"],
            force=args.get("force", False)
        )

        if result.get("error"):
            return {
                "content": [{
                    "type": "text",
                    "text": f"❌ {result['error']}"
                }],
                "is_error": True
            }

        return {
            "content": [{
                "type": "text",
                "text": f"🏆 Vote results:\n"
                       f"Outcome: {result['outcome']}\n"
                       f"Total votes: {result['total_votes']}\n"
                       f"Tally: {result['tally']}"
            }],
            "outcome": result["outcome"],
            "tally": result["tally"],
            "total_votes": result["total_votes"]
        }
    except Exception as e:
        return {
            "content": [{
                "type": "text",
                "text": f"❌ Failed to tally vote: {str(e)}"
            }],
            "is_error": True
        }


@tool(
    name="voting-get-status",
    description="Get current status of a vote. Use to check vote progress.",
    input_schema={
        "vote_id": str
    }
)
async def get_vote_status(args: Dict[str, Any]) -> Dict[str, Any]:
    """
    Get current vote status.

    Args:
        vote_id: Vote ID

    Returns:
        Vote status dict
    """
    try:
        voting = get_voting_system()
        status = voting.get_vote_status(args["vote_id"])

        if not status:
            return {
                "content": [{
                    "type": "text",
                    "text": f"❌ Vote {args['vote_id']} not found"
                }],
                "is_error": True
            }

        votes_cast = len(status.get("votes_cast", {}))
        eligible = len(status.get("eligible_voters", []))

        return {
            "content": [{
                "type": "text",
                "text": f"📊 Vote status:\n"
                       f"Topic: {status['topic']}\n"
                       f"Status: {status['status']}\n"
                       f"Votes cast: {votes_cast}/{eligible}\n"
                       f"Deadline: {status['deadline']}"
            }],
            "status": status
        }
    except Exception as e:
        return {
            "content": [{
                "type": "text",
                "text": f"❌ Failed to get vote status: {str(e)}"
            }],
            "is_error": True
        }


# =============================================================================
# Tool Registry
# =============================================================================

# Export all tools for easy registration
ALL_TOOLS = [
    # Communication tools
    send_message,
    receive_messages,
    claim_message,
    complete_message,
    send_heartbeat,
    get_agent_health,
    get_broadcast_status,  # FIX Issue #4
    subscribe_channel,

    # Job board tools
    create_task,
    claim_task,
    update_task,
    get_tasks,

    # Voting tools
    initiate_vote,  # FIX Issue #3 - includes voter validation
    cast_vote,
    tally_vote,
    get_vote_status
]


def get_all_tool_names() -> List[str]:
    """Get list of all MCP tool names."""
    return [
        # Communication
        "mcp__comms__comm-send-message",
        "mcp__comms__comm-receive-messages",
        "mcp__comms__comm-claim-message",
        "mcp__comms__comm-complete-message",
        "mcp__comms__comm-send-heartbeat",
        "mcp__comms__comm-get-agent-health",
        "mcp__comms__comm-get-broadcast-status",  # FIX Issue #4
        "mcp__comms__comm-subscribe-channel",

        # Job board
        "mcp__comms__jobboard-create-task",
        "mcp__comms__jobboard-claim-task",
        "mcp__comms__jobboard-update-task",
        "mcp__comms__jobboard-get-tasks",

        # Voting
        "mcp__comms__voting-initiate",  # FIX Issue #3 - includes voter validation
        "mcp__comms__voting-cast-vote",
        "mcp__comms__voting-tally",
        "mcp__comms__voting-get-status"
    ]
