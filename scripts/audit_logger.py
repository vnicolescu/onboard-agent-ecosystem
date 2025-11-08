#!/usr/bin/env python3
"""
Audit Trail - 100% traceability system for all agent actions.

Logs:
- Tool calls
- Decisions
- File modifications
- Agent communications
- Task transitions
"""

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
import uuid


class AuditLogger:
    """Provides comprehensive audit trail for agent actions."""
    
    EVENT_TYPES = [
        "agent_action", "tool_call", "decision", "file_modified",
        "message_sent", "task_created", "task_updated", "error",
        "human_escalation", "system_event"
    ]
    
    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root).resolve()
        self.claude_dir = self.project_root / ".claude"
        self.audit_path = self.claude_dir / "audit-trail.jsonl"
        
    def log(self, event_type: str, agent_id: str, action: str, 
            details: Optional[Dict[str, Any]] = None,
            severity: str = "info") -> str:
        """
        Log an audit event.
        
        Args:
            event_type: Type of event (see EVENT_TYPES)
            agent_id: Agent performing the action
            action: Brief description of action
            details: Additional structured data
            severity: info|warning|error|critical
            
        Returns:
            event_id
        """
        event_id = str(uuid.uuid4())
        timestamp = datetime.now().isoformat()
        
        event = {
            "id": event_id,
            "timestamp": timestamp,
            "event_type": event_type,
            "agent_id": agent_id,
            "action": action,
            "severity": severity,
            "details": details or {},
            "trace_id": details.get("trace_id") if details else None
        }
        
        # Ensure audit file exists
        self.claude_dir.mkdir(parents=True, exist_ok=True)
        
        # Append to JSONL file
        with open(self.audit_path, 'a') as f:
            f.write(json.dumps(event) + '\n')
        
        # If critical, create alert file
        if severity == "critical":
            self._create_alert(event)
        
        return event_id
    
    def log_decision(self, agent_id: str, decision: str, reasoning: str,
                    alternatives: Optional[list] = None, context: Optional[Dict] = None):
        """Log a decision with full reasoning."""
        details = {
            "decision": decision,
            "reasoning": reasoning,
            "alternatives_considered": alternatives or [],
            "context": context or {}
        }
        
        return self.log("decision", agent_id, decision, details, severity="info")
    
    def log_tool_call(self, agent_id: str, tool_name: str, parameters: Dict,
                     result: Any, duration_ms: Optional[float] = None):
        """Log a tool invocation."""
        details = {
            "tool": tool_name,
            "parameters": parameters,
            "result_summary": str(result)[:500],  # Truncate long results
            "duration_ms": duration_ms,
            "success": True
        }
        
        return self.log("tool_call", agent_id, f"Called {tool_name}", details)
    
    def log_file_modification(self, agent_id: str, file_path: str, 
                             operation: str, details: Optional[Dict] = None):
        """Log file creation/modification/deletion."""
        log_details = {
            "file_path": file_path,
            "operation": operation,  # created|modified|deleted
            **(details or {})
        }
        
        return self.log("file_modified", agent_id, 
                       f"{operation.capitalize()} {file_path}", log_details)
    
    def log_error(self, agent_id: str, error: str, context: Optional[Dict] = None):
        """Log an error event."""
        details = {
            "error": error,
            "context": context or {}
        }
        
        return self.log("error", agent_id, error, details, severity="error")
    
    def log_escalation(self, agent_id: str, reason: str, context: Dict):
        """Log human escalation request."""
        details = {
            "reason": reason,
            "context": context,
            "requires_response": True
        }
        
        return self.log("human_escalation", agent_id, 
                       f"Escalation: {reason}", details, severity="warning")
    
    def query(self, agent_id: Optional[str] = None, event_type: Optional[str] = None,
             since: Optional[str] = None, limit: int = 100) -> list:
        """
        Query audit trail.
        
        Args:
            agent_id: Filter by agent
            event_type: Filter by event type
            since: ISO timestamp - only return events after this time
            limit: Max results
            
        Returns:
            List of matching events
        """
        if not self.audit_path.exists():
            return []
        
        events = []
        with open(self.audit_path) as f:
            for line in f:
                try:
                    event = json.loads(line.strip())
                    
                    # Apply filters
                    if agent_id and event["agent_id"] != agent_id:
                        continue
                    if event_type and event["event_type"] != event_type:
                        continue
                    if since and event["timestamp"] < since:
                        continue
                    
                    events.append(event)
                    
                    if len(events) >= limit:
                        break
                except json.JSONDecodeError:
                    continue
        
        # Return newest first
        return list(reversed(events))
    
    def get_agent_timeline(self, agent_id: str, limit: int = 50) -> list:
        """Get chronological timeline of agent actions."""
        return self.query(agent_id=agent_id, limit=limit)
    
    def get_recent_errors(self, limit: int = 20) -> list:
        """Get recent errors across all agents."""
        return self.query(event_type="error", limit=limit)
    
    def get_escalations(self) -> list:
        """Get all human escalation requests."""
        return self.query(event_type="human_escalation", limit=1000)
    
    def _create_alert(self, event: Dict):
        """Create alert file for critical events."""
        alerts_dir = self.claude_dir / "alerts"
        alerts_dir.mkdir(exist_ok=True)
        
        alert_file = alerts_dir / f"{event['timestamp'].replace(':', '-')}_{event['id'][:8]}.json"
        with open(alert_file, 'w') as f:
            json.dump(event, f, indent=2)
    
    def generate_report(self, since: Optional[str] = None) -> Dict:
        """Generate audit report."""
        events = self.query(since=since, limit=10000)
        
        report = {
            "generated_at": datetime.now().isoformat(),
            "period_start": since or "all_time",
            "total_events": len(events),
            "by_type": {},
            "by_agent": {},
            "by_severity": {},
            "errors": 0,
            "escalations": 0
        }
        
        for event in events:
            # Count by type
            etype = event["event_type"]
            report["by_type"][etype] = report["by_type"].get(etype, 0) + 1
            
            # Count by agent
            agent = event["agent_id"]
            report["by_agent"][agent] = report["by_agent"].get(agent, 0) + 1
            
            # Count by severity
            severity = event["severity"]
            report["by_severity"][severity] = report["by_severity"].get(severity, 0) + 1
            
            # Special counts
            if etype == "error":
                report["errors"] += 1
            if etype == "human_escalation":
                report["escalations"] += 1
        
        return report


def main():
    """CLI entry point."""
    if len(sys.argv) < 2:
        print("Usage: python audit_logger.py <command> [args...]")
        print("Commands: log, query, report")
        sys.exit(1)
    
    command = sys.argv[1]
    logger = AuditLogger()
    
    if command == "log":
        if len(sys.argv) < 5:
            print("Usage: log <event_type> <agent_id> <action> [details_json]")
            sys.exit(1)
        
        event_type = sys.argv[2]
        agent_id = sys.argv[3]
        action = sys.argv[4]
        details = json.loads(sys.argv[5]) if len(sys.argv) > 5 else None
        
        event_id = logger.log(event_type, agent_id, action, details)
        print(json.dumps({"event_id": event_id}, indent=2))
    
    elif command == "query":
        agent_id = sys.argv[2] if len(sys.argv) > 2 else None
        events = logger.query(agent_id=agent_id, limit=50)
        print(json.dumps(events, indent=2))
    
    elif command == "report":
        since = sys.argv[2] if len(sys.argv) > 2 else None
        report = logger.generate_report(since=since)
        print(json.dumps(report, indent=2))
    
    elif command == "errors":
        errors = logger.get_recent_errors()
        print(json.dumps(errors, indent=2))
    
    elif command == "escalations":
        escalations = logger.get_escalations()
        print(json.dumps(escalations, indent=2))
    
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)


if __name__ == "__main__":
    main()
