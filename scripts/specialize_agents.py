#!/usr/bin/env python3
"""
Agent Specialization - Refines template agents for specific projects.

Two-round specialization:
- Round 1: Light touch - organizational principles, communication protocols
- Round 2: Deep training - company policies, data locations, domain expertise
"""

import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional


class AgentSpecializer:
    """Specializes template agents for project-specific needs."""
    
    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root).resolve()
        self.claude_dir = self.project_root / ".claude"
        self.agents_dir = self.claude_dir / "agents"
        self.templates_dir = Path(__file__).parent.parent / "templates" / "agents"
        
    def specialize_agent(self, template_path: Path, project_context: Dict, round_num: int = 1) -> str:
        """
        Specialize a template agent for the project.
        
        Args:
            template_path: Path to agent template
            project_context: Project metadata and requirements
            round_num: 1 for light touch, 2 for deep training
            
        Returns:
            Specialized agent content
        """
        with open(template_path) as f:
            content = f.read()
        
        # Extract YAML frontmatter
        frontmatter, body = self._split_frontmatter(content)
        
        if round_num == 1:
            specialized = self._round1_specialization(body, project_context, frontmatter)
        else:
            specialized = self._round2_specialization(body, project_context, frontmatter)
        
        # Reconstruct with frontmatter
        return f"---\n{frontmatter}\n---\n\n{specialized}"
    
    def _split_frontmatter(self, content: str) -> tuple[str, str]:
        """Split YAML frontmatter from body."""
        if content.startswith("---"):
            parts = content.split("---", 2)
            if len(parts) >= 3:
                return parts[1].strip(), parts[2].strip()
        return "", content
    
    def _round1_specialization(self, body: str, context: Dict, frontmatter: str) -> str:
        """
        Round 1: Light touch specialization.
        
        Adds:
        - Project-specific context references
        - Communication protocol details
        - Links to job board and message system
        - References to meta-orchestrators
        """
        # Add project context section at the beginning
        project_section = f"""
## Project Context

**Project:** {context.get('project_name', 'Unknown')}
**Technologies:** {', '.join(context.get('tech_stack', []))}
**Specification:** See `{context.get('spec_files', ['project docs'])[0] if context.get('spec_files') else 'project docs'}`

**Key Resources:**
- Job Board: `.claude/job-board.json`
- Messages: `.claude/communications/`
- Project Spec: `{context.get('spec_files', ['specs/'])[0] if context.get('spec_files') else 'specs/'}`
- Audit Log: `.claude/audit-trail.jsonl`

"""
        
        # Add communication protocol reference
        comm_section = """
## Communication Protocol

**IMPORTANT**: You operate within a coordinated multi-agent system.

**Core Communication Rules:**
1. **Query context-manager** before starting work to get current system state
2. **Update job board** immediately when taking/completing tasks
3. **Broadcast critical updates** via urgent messages
4. **Log all significant decisions** to audit trail
5. **Request human review** for conflicts or major decisions

**Message Types:**
- `urgent`: Broadcast immediately (system-wide)
- `normal`: Queued message (specific recipient or channel)
- `low`: Background notification

**Meta-Orchestrators** (your coordinators):
- `context-manager`: Information storage and retrieval
- `agent-manager`: Team coordination and training
- `multi-agent-orchestrator`: Workflow execution

**Communication Format:**
```json
{
  "from": "your-agent-id",
  "to": "recipient-agent-id or channel",
  "priority": "urgent|normal|low",
  "message": "Your message",
  "context": {"task_id": "...", "related_docs": ["..."]}
}
```

**Always check messages** before starting work - coordination prevents duplicate effort!

"""
        
        # Insert sections after the main identity paragraph
        lines = body.split('\n')
        insert_idx = 0
        for i, line in enumerate(lines):
            if line.startswith("You are a") or line.startswith("You're a"):
                # Find end of paragraph
                for j in range(i+1, len(lines)):
                    if lines[j].strip() == "":
                        insert_idx = j + 1
                        break
                break
        
        if insert_idx > 0:
            lines.insert(insert_idx, project_section)
            lines.insert(insert_idx + 1, comm_section)
            body = '\n'.join(lines)
        else:
            # Fallback: prepend
            body = project_section + comm_section + body
        
        return body
    
    def _round2_specialization(self, body: str, context: Dict, frontmatter: str) -> str:
        """
        Round 2: Deep training specialization.
        
        Adds:
        - Detailed domain knowledge
        - Company-specific conventions
        - Data source locations
        - Integration patterns
        
        This is invoked AFTER communication system is initialized.
        """
        # This will be more elaborate - for now, placeholder structure
        domain_section = f"""
## Deep Domain Training

**Project-Specific Conventions:**
(To be populated by agent-manager during Round 2 training)

- Coding standards: [Location TBD]
- API patterns: [Location TBD]
- Testing requirements: [Location TBD]
- Documentation format: [Location TBD]

**Data Sources:**
(To be mapped by agent-manager during Round 2 training)

- Configuration: [Location TBD]
- Environment vars: [Location TBD]
- Secrets management: [Location TBD]

**Integration Points:**
(To be defined during Round 2 training)

- External APIs: [List TBD]
- Internal services: [List TBD]
- Database connections: [Schema TBD]

---
**Training Status:** Round 2 Complete - {datetime.now().isoformat()}
"""
        
        body = body + "\n\n" + domain_section
        return body
    
    def deploy_agents(self, agent_names: List[str], project_context: Dict, round_num: int = 1):
        """
        Deploy specialized agents to .claude/agents/ directory.
        
        Agents go to pending/ for Round 1 (await approval).
        """
        self.agents_dir.mkdir(parents=True, exist_ok=True)
        
        if round_num == 1:
            target_dir = self.agents_dir / "pending"
        else:
            target_dir = self.agents_dir
        
        target_dir.mkdir(parents=True, exist_ok=True)
        
        deployed = []
        failed = []
        
        for agent_name in agent_names:
            template_path = self.templates_dir / f"{agent_name}.md"
            
            if not template_path.exists():
                failed.append({"agent": agent_name, "reason": "template_not_found"})
                continue
            
            try:
                specialized = self.specialize_agent(template_path, project_context, round_num)
                
                output_path = target_dir / f"{agent_name}.md"
                with open(output_path, 'w') as f:
                    f.write(specialized)
                
                deployed.append({"agent": agent_name, "path": str(output_path)})
            except Exception as e:
                failed.append({"agent": agent_name, "reason": str(e)})
        
        return {"deployed": deployed, "failed": failed}


def main():
    """CLI entry point."""
    if len(sys.argv) < 3:
        print("Usage: python specialize_agents.py <project_context.json> <agent1,agent2,...> [round_num]")
        sys.exit(1)
    
    context_file = sys.argv[1]
    agent_names = sys.argv[2].split(',')
    round_num = int(sys.argv[3]) if len(sys.argv) > 3 else 1
    
    with open(context_file) as f:
        project_context = json.load(f)
    
    specializer = AgentSpecializer()
    result = specializer.deploy_agents(agent_names, project_context, round_num)
    
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
