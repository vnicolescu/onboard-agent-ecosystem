#!/usr/bin/env python3
"""
Example 1: Simple Request/Response Pattern

Demonstrates:
- Sending a request
- Waiting for a response
- Using the .ask() helper method

Run this to see a basic request/response cycle.
"""

import sys
import time
from pathlib import Path
from threading import Thread

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from communications import AgentMessenger, CommunicationSystem


def requester():
    """Agent that requests context."""
    print("=== REQUESTER AGENT ===")

    messenger = AgentMessenger("frontend-dev-01")
    print(f"✓ Initialized as {messenger.agent_id}")

    # Simple request/response using .ask()
    print("\nSending context query...")
    response = messenger.ask(
        to="context-manager",
        message_type="context.query",
        data={"query": "What frontend framework should I use?"},
        timeout=10
    )

    if response:
        print(f"✓ Got response: {response['payload']}")
    else:
        print("✗ No response (timeout)")


def responder():
    """Agent that responds to context queries."""
    print("\n=== RESPONDER AGENT ===")

    messenger = AgentMessenger("context-manager")
    print(f"✓ Initialized as {messenger.agent_id}")

    # Wait a moment for request to arrive
    time.sleep(0.5)

    print("\nChecking for messages...")
    messages = messenger.receive(limit=10)
    print(f"✓ Found {len(messages)} message(s)")

    for msg in messages:
        print(f"\nProcessing message {msg['id'][:8]}...")
        print(f"  Type: {msg['type']}")
        print(f"  From: {msg['from_agent']}")
        print(f"  Payload: {msg['payload']}")

        if messenger.claim(msg['id']):
            print(f"  ✓ Claimed")

            # Process the request
            if msg['type'] == 'context.query':
                response_data = {
                    "context": {
                        "framework": "React",
                        "version": "18.2",
                        "state_management": "Redux Toolkit",
                        "routing": "React Router v6"
                    }
                }

                # Send response
                messenger.reply(msg, response_data)
                print(f"  ✓ Sent response")

            # Mark as complete
            messenger.complete(msg['id'])
            print(f"  ✓ Completed")
        else:
            print(f"  ✗ Already claimed by another agent")


def main():
    """Run the example."""
    print("=" * 60)
    print("EXAMPLE 1: Simple Request/Response")
    print("=" * 60)

    # Initialize communication system
    comm = CommunicationSystem(".")
    print("\nInitializing communication system...")
    result = comm.initialize()
    print(f"✓ Initialized at {result['db_path']}")

    # Run responder in background thread
    responder_thread = Thread(target=responder, daemon=True)
    responder_thread.start()

    # Give responder time to start
    time.sleep(0.1)

    # Run requester in main thread
    requester()

    # Wait for responder to finish
    responder_thread.join(timeout=2)

    print("\n" + "=" * 60)
    print("✓ Example complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
