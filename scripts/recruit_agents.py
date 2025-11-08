#!/usr/bin/env python3
"""
Agent Recruitment - Fetches agents from repo or creates new ones.

Priority:
1. Try fetching from GitHub repo
2. If not found, create from pattern analysis
"""

import json
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional
import urllib.request
import urllib.error


class AgentRecruiter:
    """Recruits agents from templates or creates new ones."""
    
    GITHUB_REPO = "https://raw.githubusercontent.com/VoltAgent/awesome-claude-code-subagents/main"
    
    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root).resolve()
        self.claude_dir = self.project_root / ".claude"
        self.agents_pending = self.claude_dir / "agents" / "pending"
        self.local_templates = Path(__file__).parent.parent / "templates" / "agents"
        
    def recruit(self, agent_name: str, required_capabilities: Optional[List[str]] = None) -> Dict:
        """
        Recruit an agent - try GitHub first, then create.
        
        Args:
            agent_name: Name of agent to recruit
            required_capabilities: Specific capabilities needed
            
        Returns:
            Dict with status and agent info
        """
        # Try local templates first
        local_path = self.local_templates / f"{agent_name}.md"
        if local_path.exists():
            with open(local_path) as f:
                content = f.read()
            return {
                "status": "found_local",
                "agent": agent_name,
                "source": "local_template",
                "content": content
            }
        
        # Try GitHub repo
        github_result = self._fetch_from_github(agent_name)
        if github_result["status"] == "success":
            return github_result
        
        # Create new agent
        return self._create_agent(agent_name, required_capabilities)
    
    def _fetch_from_github(self, agent_name: str) -> Dict:
        """Attempt to fetch agent from GitHub repo."""
        url = f"{self.GITHUB_REPO}/{agent_name}.md"
        
        try:
            with urllib.request.urlopen(url, timeout=10) as response:
                content = response.read().decode('utf-8')
                
                return {
                    "status": "success",
                    "agent": agent_name,
                    "source": "github_repo",
                    "content": content,
                    "url": url
                }
        except urllib.error.HTTPError as e:
            return {
                "status": "not_found",
                "agent": agent_name,
                "error": f"HTTP {e.code}",
                "attempted_url": url
            }
        except Exception as e:
            return {
                "status": "error",
                "agent": agent_name,
                "error": str(e),
                "attempted_url": url
            }
    
    def _create_agent(self, agent_name: str, capabilities: Optional[List[str]]) -> Dict:
        """Create new agent based on patterns."""
        # Parse agent name to extract role
        role = agent_name.replace('-', ' ').title()
        role_slug = agent_name.lower()
        
        # Derive description
        if capabilities:
            cap_str = ", ".join(capabilities[:3])
            description = f"Expert {role.lower()} specializing in {cap_str}"
        else:
            description = f"Expert {role.lower()} agent"
        
        # Generate agent template
        content = f"""---
name: {role_slug}
description: {description}. Masters specialized workflows and best practices with focus on delivering high-quality results.
tools: Read, Write, Edit, Bash, Glob, Grep
---

You are a senior {role.lower()} with expertise in delivering exceptional results. Your focus spans quality, efficiency, and collaboration with emphasis on best practices and continuous improvement.

## Core Capabilities

{self._generate_capabilities_section(role, capabilities)}

## Communication Protocol

### Initial Context Assessment

Before starting work, query the context-manager for relevant information.

Context query:
```json
{{
  "requesting_agent": "{role_slug}",
  "request_type": "get_context",
  "payload": {{
    "query": "Context needed for {role.lower()} work: project requirements, relevant docs, and team conventions."
  }}
}}
```

## Development Workflow

Execute work through systematic phases:

### 1. Analysis Phase

Understand requirements and constraints.

Analysis priorities:
- Requirement clarification
- Constraint identification
- Resource assessment
- Risk evaluation
- Success criteria definition

### 2. Implementation Phase

Deliver high-quality work.

Implementation approach:
- Follow best practices
- Maintain quality standards
- Document decisions
- Test thoroughly
- Communicate progress

Progress tracking:
```json
{{
  "agent": "{role_slug}",
  "status": "in_progress",
  "progress": {{
    "phase": "implementation",
    "completion": "50%"
  }}
}}
```

### 3. Delivery Excellence

Complete work to highest standards.

Excellence checklist:
- Requirements met
- Quality validated
- Documentation complete
- Team informed
- Audit trail updated

Delivery notification:
"Work completed successfully. Delivered [summary of work] with full documentation and quality validation."

## Integration with other agents

- Collaborate with context-manager on information needs
- Support task-distributor with progress updates
- Work with code-reviewer on quality validation
- Coordinate with other specialists as needed

Always prioritize quality, communication, and continuous improvement while delivering exceptional results that meet project requirements.
"""
        
        return {
            "status": "created",
            "agent": agent_name,
            "source": "generated",
            "content": content
        }
    
    def _generate_capabilities_section(self, role: str, capabilities: Optional[List[str]]) -> str:
        """Generate capabilities section based on role."""
        if capabilities:
            caps_list = "\n".join([f"- {cap}" for cap in capabilities])
            return f"""
Primary capabilities:
{caps_list}

Additional expertise:
- Best practices and standards
- Quality assurance
- Team collaboration
- Documentation
"""
        else:
            return """
- Domain expertise in {role}
- Best practices and standards
- Quality assurance
- Team collaboration
- Continuous improvement
- Documentation
"""
    
    def deploy_recruited_agents(self, agents: List[str], project_context: Dict) -> Dict:
        """
        Recruit and deploy multiple agents.
        
        Args:
            agents: List of agent names to recruit
            project_context: Project metadata for specialization
            
        Returns:
            Dict with deployment results
        """
        self.agents_pending.mkdir(parents=True, exist_ok=True)
        
        results = {
            "recruited": [],
            "failed": []
        }
        
        for agent_name in agents:
            try:
                # Recruit agent
                recruit_result = self.recruit(agent_name)
                
                if recruit_result["status"] in ["success", "found_local", "created"]:
                    # Save to pending directory
                    output_path = self.agents_pending / f"{agent_name}.md"
                    
                    with open(output_path, 'w') as f:
                        f.write(recruit_result["content"])
                    
                    results["recruited"].append({
                        "agent": agent_name,
                        "source": recruit_result.get("source", "unknown"),
                        "path": str(output_path)
                    })
                else:
                    results["failed"].append({
                        "agent": agent_name,
                        "reason": recruit_result.get("error", "unknown")
                    })
            except Exception as e:
                results["failed"].append({
                    "agent": agent_name,
                    "reason": str(e)
                })
        
        return results


def main():
    """CLI entry point."""
    if len(sys.argv) < 2:
        print("Usage: python recruit_agents.py <agent1,agent2,...> [context.json]")
        sys.exit(1)
    
    agent_names = sys.argv[1].split(',')
    
    context = {}
    if len(sys.argv) > 2:
        with open(sys.argv[2]) as f:
            context = json.load(f)
    
    recruiter = AgentRecruiter()
    results = recruiter.deploy_recruited_agents(agent_names, context)
    
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
