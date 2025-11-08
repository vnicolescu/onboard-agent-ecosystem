#!/usr/bin/env python3
"""
Job Board - Task management system for multi-agent coordination.

Provides:
- Task creation and assignment
- Status tracking
- Dependency management
- Conflict detection
"""

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
import uuid


class JobBoard:
    """Manages task distribution and tracking."""
    
    VALID_STATUSES = ["open", "assigned", "in-progress", "review", "done", "blocked"]
    VALID_PRIORITIES = ["critical", "high", "normal", "low"]
    
    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root).resolve()
        self.claude_dir = self.project_root / ".claude"
        self.board_path = self.claude_dir / "job-board.json"
        
    def initialize(self):
        """Initialize empty job board."""
        board = {
            "version": "1.0",
            "created_at": datetime.now().isoformat(),
            "tasks": {},
            "stats": {
                "total": 0,
                "open": 0,
                "in_progress": 0,
                "done": 0
            }
        }
        
        self.claude_dir.mkdir(parents=True, exist_ok=True)
        
        with open(self.board_path, 'w') as f:
            json.dump(board, f, indent=2)
        
        return {"status": "initialized", "path": str(self.board_path)}
    
    def create_task(self, title: str, description: str, priority: str = "normal",
                   dependencies: Optional[List[str]] = None, 
                   assigned_to: Optional[str] = None,
                   tags: Optional[List[str]] = None) -> str:
        """
        Create a new task.
        
        Returns:
            task_id
        """
        task_id = f"task-{str(uuid.uuid4())[:8]}"
        
        board = self._load_board()
        
        board["tasks"][task_id] = {
            "id": task_id,
            "title": title,
            "description": description,
            "status": "assigned" if assigned_to else "open",
            "priority": priority,
            "assigned_to": assigned_to,
            "dependencies": dependencies or [],
            "tags": tags or [],
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "started_at": None,
            "completed_at": None,
            "blocked_reason": None,
            "history": [
                {
                    "timestamp": datetime.now().isoformat(),
                    "action": "created",
                    "by": assigned_to or "system"
                }
            ]
        }
        
        board["stats"]["total"] += 1
        board["stats"]["open"] += 0 if assigned_to else 1
        
        self._save_board(board)
        
        return task_id
    
    def assign_task(self, task_id: str, agent_id: str) -> Dict:
        """Assign a task to an agent."""
        board = self._load_board()
        
        if task_id not in board["tasks"]:
            return {"error": "Task not found"}
        
        task = board["tasks"][task_id]
        
        # Check if task is already assigned
        if task["assigned_to"] and task["assigned_to"] != agent_id:
            return {
                "error": "Task already assigned",
                "assigned_to": task["assigned_to"]
            }
        
        # Check dependencies
        unmet_deps = self._check_dependencies(board, task_id)
        if unmet_deps:
            return {
                "error": "Unmet dependencies",
                "dependencies": unmet_deps
            }
        
        # Update task
        old_status = task["status"]
        task["assigned_to"] = agent_id
        task["status"] = "assigned"
        task["updated_at"] = datetime.now().isoformat()
        
        task["history"].append({
            "timestamp": datetime.now().isoformat(),
            "action": "assigned",
            "by": agent_id
        })
        
        # Update stats
        if old_status == "open":
            board["stats"]["open"] -= 1
        
        self._save_board(board)
        
        return {"success": True, "task": task}
    
    def update_status(self, task_id: str, new_status: str, agent_id: str,
                     blocked_reason: Optional[str] = None) -> Dict:
        """Update task status."""
        if new_status not in self.VALID_STATUSES:
            return {"error": f"Invalid status: {new_status}"}
        
        board = self._load_board()
        
        if task_id not in board["tasks"]:
            return {"error": "Task not found"}
        
        task = board["tasks"][task_id]
        old_status = task["status"]
        
        task["status"] = new_status
        task["updated_at"] = datetime.now().isoformat()
        
        if new_status == "in-progress" and not task["started_at"]:
            task["started_at"] = datetime.now().isoformat()
        
        if new_status == "done":
            task["completed_at"] = datetime.now().isoformat()
            board["stats"]["done"] += 1
            if old_status == "in-progress":
                board["stats"]["in_progress"] -= 1
        
        if new_status == "in-progress" and old_status != "in-progress":
            board["stats"]["in_progress"] += 1
        
        if new_status == "blocked":
            task["blocked_reason"] = blocked_reason
        
        task["history"].append({
            "timestamp": datetime.now().isoformat(),
            "action": f"status_change: {old_status} -> {new_status}",
            "by": agent_id,
            "reason": blocked_reason if blocked_reason else None
        })
        
        self._save_board(board)
        
        return {"success": True, "task": task}
    
    def get_available_tasks(self, agent_id: Optional[str] = None) -> List[Dict]:
        """Get tasks available for work."""
        board = self._load_board()
        
        available = []
        for task in board["tasks"].values():
            # Must be open or assigned to this agent
            if task["status"] in ["open", "assigned"]:
                # Check if assigned to someone else
                if task["assigned_to"] and task["assigned_to"] != agent_id:
                    continue
                
                # Check dependencies
                unmet_deps = self._check_dependencies(board, task["id"])
                if not unmet_deps:
                    available.append(task)
        
        # Sort by priority
        priority_order = {"critical": 0, "high": 1, "normal": 2, "low": 3}
        available.sort(key=lambda t: priority_order.get(t["priority"], 2))
        
        return available
    
    def get_task(self, task_id: str) -> Optional[Dict]:
        """Get a specific task."""
        board = self._load_board()
        return board["tasks"].get(task_id)
    
    def get_agent_tasks(self, agent_id: str, status_filter: Optional[str] = None) -> List[Dict]:
        """Get all tasks for an agent."""
        board = self._load_board()
        
        tasks = []
        for task in board["tasks"].values():
            if task["assigned_to"] == agent_id:
                if status_filter is None or task["status"] == status_filter:
                    tasks.append(task)
        
        return tasks
    
    def get_stats(self) -> Dict:
        """Get board statistics."""
        board = self._load_board()
        return board["stats"]
    
    def _check_dependencies(self, board: Dict, task_id: str) -> List[str]:
        """Check if task dependencies are met."""
        task = board["tasks"][task_id]
        unmet = []
        
        for dep_id in task["dependencies"]:
            if dep_id in board["tasks"]:
                dep_task = board["tasks"][dep_id]
                if dep_task["status"] != "done":
                    unmet.append(dep_id)
            else:
                unmet.append(dep_id)  # Dependency doesn't exist
        
        return unmet
    
    def _load_board(self) -> Dict:
        """Load job board from file."""
        if not self.board_path.exists():
            self.initialize()
        
        with open(self.board_path) as f:
            return json.load(f)
    
    def _save_board(self, board: Dict):
        """Save job board to file."""
        with open(self.board_path, 'w') as f:
            json.dump(board, f, indent=2)


def main():
    """CLI entry point."""
    if len(sys.argv) < 2:
        print("Usage: python create_job_board.py <command> [args...]")
        print("Commands: init, create, assign, update, list, get")
        sys.exit(1)
    
    command = sys.argv[1]
    board = JobBoard()
    
    if command == "init":
        result = board.initialize()
        print(json.dumps(result, indent=2))
    
    elif command == "create":
        if len(sys.argv) < 4:
            print("Usage: create <title> <description> [priority] [assigned_to]")
            sys.exit(1)
        
        title = sys.argv[2]
        description = sys.argv[3]
        priority = sys.argv[4] if len(sys.argv) > 4 else "normal"
        assigned_to = sys.argv[5] if len(sys.argv) > 5 else None
        
        task_id = board.create_task(title, description, priority, assigned_to=assigned_to)
        print(json.dumps({"task_id": task_id}, indent=2))
    
    elif command == "list":
        agent_id = sys.argv[2] if len(sys.argv) > 2 else None
        tasks = board.get_available_tasks(agent_id)
        print(json.dumps(tasks, indent=2))
    
    elif command == "get":
        task_id = sys.argv[2]
        task = board.get_task(task_id)
        print(json.dumps(task, indent=2))
    
    elif command == "stats":
        stats = board.get_stats()
        print(json.dumps(stats, indent=2))
    
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)


if __name__ == "__main__":
    main()
