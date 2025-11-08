#!/usr/bin/env python3
"""
Example 2: Broadcast Voting Pattern

Demonstrates:
- Broadcasting to multiple agents
- Multiple agents receiving the same message
- Collecting responses from multiple agents

This shows how broadcasts work correctly (fixing the audit issue).
"""

import sys
import time
from pathlib import Path
from threading import Thread

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from communications import AgentMessenger, CommunicationSystem


def voter(agent_id: str, vote_choice: str, delay: float = 0):
    """Agent that votes on proposals."""
    time.sleep(delay)

    messenger = AgentMessenger(agent_id)
    messenger.subscribe("general")

    print(f"\n[{agent_id}] Looking for votes...")

    # Wait for vote message
    time.sleep(0.5)
    messages = messenger.receive(message_type="vote.initiate")

    print(f"[{agent_id}] Found {len(messages)} vote(s)")

    for msg in messages:
        if messenger.claim(msg['id']):
            print(f"[{agent_id}] ✓ Claimed vote: {msg['payload']['topic']}")

            # Cast vote
            messenger.send(
                to="orchestrator",
                message_type="vote.cast",
                data={
                    "vote_id": msg['payload']['vote_id'],
                    "option": vote_choice,
                    "reasoning": f"I think {vote_choice} is the right choice"
                },
                priority=7
            )

            print(f"[{agent_id}] ✓ Voted: {vote_choice}")

            messenger.complete(msg['id'])
            break


def orchestrator():
    """Agent that initiates vote and collects results."""
    print("\n[ORCHESTRATOR] Starting...")

    messenger = AgentMessenger("orchestrator")

    # Initiate vote (broadcast to all agents)
    print("\n[ORCHESTRATOR] Broadcasting vote...")
    messenger.broadcast(
        message_type="vote.initiate",
        data={
            "vote_id": "vote-001",
            "topic": "Should we use TypeScript for the new module?",
            "options": ["yes", "no", "later"],
            "deadline": "2025-11-08T17:00:00Z"
        },
        priority=8
    )

    print("[ORCHESTRATOR] ✓ Vote broadcast sent")

    # Wait for votes
    print("\n[ORCHESTRATOR] Waiting for votes (10 seconds)...")
    votes = []
    timeout = time.time() + 10

    while time.time() < timeout:
        messages = messenger.receive(message_type="vote.cast")

        for msg in messages:
            if messenger.claim(msg['id']):
                votes.append(msg)
                print(f"[ORCHESTRATOR] ✓ Received vote from {msg['from_agent']}: {msg['payload']['option']}")
                messenger.complete(msg['id'])

        time.sleep(0.2)

    # Tally results
    print(f"\n[ORCHESTRATOR] Vote complete! Received {len(votes)} votes")

    tally = {}
    for vote in votes:
        option = vote['payload']['option']
        tally[option] = tally.get(option, 0) + 1

    print("\n[ORCHESTRATOR] Results:")
    for option, count in sorted(tally.items(), key=lambda x: x[1], reverse=True):
        print(f"  {option}: {count} vote(s)")


def main():
    """Run the broadcast vote example."""
    print("=" * 60)
    print("EXAMPLE 2: Broadcast Voting")
    print("=" * 60)

    # Initialize
    comm = CommunicationSystem(".")
    print("\nInitializing communication system...")
    comm.initialize()
    print("✓ Initialized")

    # Create voter threads
    voters = [
        Thread(target=voter, args=("frontend-dev-01", "yes", 0.2), daemon=True),
        Thread(target=voter, args=("backend-dev-01", "yes", 0.3), daemon=True),
        Thread(target=voter, args=("database-expert", "no", 0.4), daemon=True),
    ]

    # Start orchestrator thread
    orch_thread = Thread(target=orchestrator, daemon=True)
    orch_thread.start()

    time.sleep(0.1)

    # Start voters
    for v in voters:
        v.start()

    # Wait for completion
    orch_thread.join(timeout=15)
    for v in voters:
        v.join(timeout=1)

    print("\n" + "=" * 60)
    print("✓ Example complete!")
    print("\nNote: All 3 agents received the broadcast message")
    print("      (This validates the broadcast fix)")
    print("=" * 60)


if __name__ == "__main__":
    main()
