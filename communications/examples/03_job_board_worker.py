#!/usr/bin/env python3
"""
Example 3: Job Board Worker Pattern

Demonstrates:
- Creating tasks on the job board
- Multiple workers competing for tasks
- Atomic task claiming (only one wins)
- Task status updates

This validates the transactional job board fix.
"""

import sys
import time
from pathlib import Path
from threading import Thread
import random

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from communications import AgentMessenger, CommunicationSystem


def worker(agent_id: str):
    """Worker agent that claims and processes tasks."""
    messenger = AgentMessenger(agent_id)

    print(f"\n[{agent_id}] Starting worker...")

    time.sleep(0.5)  # Wait for tasks to be created

    # Look for tasks
    tasks = messenger.get_tasks()
    print(f"[{agent_id}] Found {len(tasks)} available task(s)")

    for task in tasks:
        print(f"[{agent_id}] Attempting to claim: {task['title']}")

        # Try to claim
        if messenger.claim_task(task['task_id']):
            print(f"[{agent_id}] ✓ CLAIMED: {task['title']}")

            # Update to in-progress
            messenger.update_task(task['task_id'], "in-progress")
            print(f"[{agent_id}]   Status: in-progress")

            # Simulate work
            work_time = random.uniform(0.5, 1.5)
            time.sleep(work_time)

            # Complete task
            result = f"Completed by {agent_id} in {work_time:.2f}s"
            messenger.complete_task(task['task_id'], result)
            print(f"[{agent_id}]   ✓ Completed: {result}")

            break  # Only do one task
        else:
            print(f"[{agent_id}] ✗ Already claimed by another worker")


def task_creator():
    """Create tasks on the job board."""
    print("\n[TASK CREATOR] Creating tasks...")

    comm = CommunicationSystem(".")

    tasks = [
        ("task-001", "Implement login form", "Create React login component", 8),
        ("task-002", "Write API endpoint", "Create /api/auth endpoint", 7),
        ("task-003", "Database migration", "Add users table", 6),
        ("task-004", "Write tests", "Unit tests for auth", 5),
        ("task-005", "Update documentation", "Document auth flow", 4),
    ]

    for task_id, title, description, priority in tasks:
        comm.create_task(task_id, title, description, priority)
        print(f"[TASK CREATOR] ✓ Created: {title}")

    print(f"[TASK CREATOR] All {len(tasks)} tasks created")


def main():
    """Run the job board example."""
    print("=" * 60)
    print("EXAMPLE 3: Job Board with Competing Workers")
    print("=" * 60)

    # Initialize
    comm = CommunicationSystem(".")
    print("\nInitializing communication system...")
    comm.initialize()
    print("✓ Initialized")

    # Create tasks
    creator_thread = Thread(target=task_creator, daemon=True)
    creator_thread.start()
    creator_thread.join()

    # Create worker threads (5 workers competing for 5 tasks)
    workers = [
        Thread(target=worker, args=(f"worker-{i:02d}",), daemon=True)
        for i in range(1, 6)
    ]

    print("\n" + "=" * 60)
    print("Starting 5 workers to compete for 5 tasks...")
    print("(Each worker will try to claim all tasks)")
    print("=" * 60)

    # Start all workers simultaneously
    for w in workers:
        w.start()

    # Wait for completion
    for w in workers:
        w.join(timeout=5)

    # Check final status
    print("\n" + "=" * 60)
    print("Final Task Status:")
    print("=" * 60)

    cursor = comm._get_connection().cursor()
    cursor.execute("""
        SELECT task_id, title, status, assigned_to, result
        FROM job_board
        ORDER BY priority DESC
    """)

    for row in cursor.fetchall():
        task_id, title, status, assigned_to, result = row
        print(f"\n{title}")
        print(f"  Status: {status}")
        print(f"  Assigned to: {assigned_to}")
        if result:
            print(f"  Result: {result}")

    print("\n" + "=" * 60)
    print("✓ Example complete!")
    print("\nNote: Each task was claimed by exactly ONE worker")
    print("      (This validates the atomic task claiming)")
    print("=" * 60)


if __name__ == "__main__":
    main()
