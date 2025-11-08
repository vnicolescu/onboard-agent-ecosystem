#!/usr/bin/env python3
"""
Complete Workflow Example - New Communication Protocol

Demonstrates the full agent coordination workflow:
1. Initialize communication system
2. Register agents
3. Context manager handles queries
4. Agents claim and complete tasks
5. Voting on decisions
6. Round 2 training

This example showcases the migrated system in action.
"""

import time
from pathlib import Path
from threading import Thread

from communications.core import CommunicationSystem
from communications.agent_sdk import AgentMessenger
from communications.voting import VotingSystem


def setup_system(project_root="."):
    """Initialize the communication system."""
    print("=" * 60)
    print("STEP 1: Initialize Communication System")
    print("=" * 60)

    comm = CommunicationSystem(project_root)
    result = comm.initialize()

    print(f"✓ Database: {result['db_path']}")
    print(f"✓ Version: {result['version']}")
    print(f"✓ Channels: {', '.join(result['default_channels'])}")
    print()

    return comm


def register_agents(comm):
    """Register agents in the system."""
    print("=" * 60)
    print("STEP 2: Register Agents")
    print("=" * 60)

    agents = ["context-manager", "frontend-dev-01", "backend-dev-01"]

    for agent_id in agents:
        # Subscribe to channels
        comm.subscribe_to_channel(agent_id, "general")
        comm.subscribe_to_channel(agent_id, "technical")

        # Send heartbeat
        comm.send_heartbeat(agent_id, "active", "Ready for tasks")

        print(f"✓ Registered: {agent_id}")

    print()
    return agents


def simulate_context_manager():
    """Simulate context manager responding to queries."""
    messenger = AgentMessenger("context-manager")

    print("[Context Manager] Starting to listen for queries...")

    # Listen for context queries
    for _ in range(5):  # Poll 5 times
        messages = messenger.receive(message_type="context.query")

        for msg in messages:
            if messenger.claim(msg['id']):
                print(f"[Context Manager] Received query: {msg['payload']['query']}")

                # Simulate processing
                time.sleep(0.5)

                # Send response
                context_data = {
                    "framework": "React 18",
                    "state_management": "Zustand",
                    "styling": "Tailwind CSS",
                    "testing": "Jest + React Testing Library"
                }

                messenger.reply(msg, {"context": context_data})
                messenger.complete(msg['id'])

                print(f"[Context Manager] Responded with project context")

        time.sleep(0.5)


def demo_request_response():
    """Demonstrate request/response pattern."""
    print("=" * 60)
    print("STEP 3: Request/Response Pattern")
    print("=" * 60)

    # Start context manager in background
    Thread(target=simulate_context_manager, daemon=True).start()

    time.sleep(0.5)  # Let it start

    # Frontend developer queries context
    messenger = AgentMessenger("frontend-dev-01")

    print("[Frontend Dev] Querying context manager...")

    response = messenger.ask(
        to="context-manager",
        message_type="context.query",
        data={"query": "Need frontend architecture details"},
        timeout=10
    )

    if response:
        context = response['payload']['context']
        print(f"[Frontend Dev] Received context:")
        print(f"  - Framework: {context['framework']}")
        print(f"  - State: {context['state_management']}")
        print(f"  - Styling: {context['styling']}")
        print("✓ Request/response successful!")
    else:
        print("✗ No response received")

    print()


def demo_task_board():
    """Demonstrate job board integration."""
    print("=" * 60)
    print("STEP 4: Job Board Coordination")
    print("=" * 60)

    messenger = AgentMessenger("backend-dev-01")

    # Create a task
    task_id = messenger.comm.create_task(
        task_id="task-001",
        title="Implement user authentication API",
        description="Create POST /api/auth/login and /api/auth/register endpoints",
        priority=8
    )

    print(f"✓ Created task: {task_id}")

    # Get open tasks
    tasks = messenger.get_tasks()
    print(f"✓ Found {len(tasks)} open tasks")

    # Claim task
    if tasks:
        task = tasks[0]
        if messenger.claim_task(task['task_id']):
            print(f"✓ [Backend Dev] Claimed task: {task['title']}")

            # Update status
            messenger.update_task(task['task_id'], "in-progress")
            print(f"✓ [Backend Dev] Updated status to in-progress")

            # Simulate work
            time.sleep(0.5)

            # Complete task
            messenger.complete_task(task['task_id'], "Authentication API implemented")
            print(f"✓ [Backend Dev] Completed task")

    print()


def demo_voting():
    """Demonstrate voting system."""
    print("=" * 60)
    print("STEP 5: Voting System")
    print("=" * 60)

    voting = VotingSystem()

    # Initiate vote
    vote_id = voting.initiate_vote(
        proposer_agent="frontend-dev-01",
        topic="Use TypeScript for new components?",
        options=["yes", "no", "defer"],
        mechanism="simple_majority",
        timeout_hours=1  # 1 hour for demo
    )

    print(f"✓ Vote initiated: {vote_id}")
    print(f"  Topic: Use TypeScript for new components?")

    # Agents cast votes
    agents = ["frontend-dev-01", "backend-dev-01", "context-manager"]

    for agent_id in agents:
        choice = "yes" if "dev" in agent_id else "defer"
        result = voting.cast_vote(
            agent_id=agent_id,
            vote_id=vote_id,
            choice=choice,
            reasoning=f"Vote from {agent_id}"
        )

        if result.get("success"):
            print(f"✓ [{agent_id}] Voted: {choice}")

    # Tally vote (force early tally for demo)
    result = voting.tally_vote(vote_id, force=True)

    print(f"\n✓ Vote results:")
    print(f"  Winner: {result['outcome']}")
    print(f"  Tally: {result['tally']}")
    print(f"  Total votes: {result['total_votes']}")

    print()


def demo_round2_training():
    """Demonstrate Round 2 training."""
    print("=" * 60)
    print("STEP 6: Round 2 Deep Training")
    print("=" * 60)

    # Note: This would normally be triggered after project work
    print("Round 2 training analyzes project patterns and specializes agents.")
    print("Example:")
    print("  $ python scripts/train_agents_round2.py analyze")
    print("  $ python scripts/train_agents_round2.py train frontend-developer")
    print()
    print("See: scripts/train_agents_round2.py for implementation")
    print()


def main():
    """Run complete workflow demonstration."""
    print("\n")
    print("╔" + "=" * 58 + "╗")
    print("║" + " " * 10 + "ONBOARD AGENT ECOSYSTEM v2.0" + " " * 20 + "║")
    print("║" + " " * 12 + "Complete Workflow Example" + " " * 21 + "║")
    print("╚" + "=" * 58 + "╝")
    print()

    project_root = "."

    try:
        # Step 1: Setup
        comm = setup_system(project_root)

        # Step 2: Register agents
        agents = register_agents(comm)

        # Step 3: Request/Response
        demo_request_response()

        # Step 4: Job Board
        demo_task_board()

        # Step 5: Voting
        demo_voting()

        # Step 6: Round 2 Training
        demo_round2_training()

        print("=" * 60)
        print("✓ ALL WORKFLOWS COMPLETED SUCCESSFULLY!")
        print("=" * 60)
        print()
        print("System is ready for production use.")
        print("Agents can now coordinate using the new protocol.")
        print()

    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
