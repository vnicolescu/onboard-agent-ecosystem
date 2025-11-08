# Project Onboard - Multi-Agent Ecosystem

**Version:** 2.0 (SDK Migration)
**Author:** Vlad-Alexandru Nicolescu (with Claude's assistance)
**Status:** Migrated to Official Anthropic Python Agent SDK

> **🚀 New in v2.0**: Fully refactored to use the official Anthropic Python Agent SDK with MCP tools!

## Migration Notice

**Version 2.0** represents a major architectural upgrade:
- ✅ **Official SDK**: Now built on `claude-agent-sdk` (Python)
- ✅ **MCP Tools**: Communication system exposed as Model Context Protocol tools
- ✅ **Better Architecture**: Subagents defined using `AgentDefinition`
- ✅ **Cleaner Integration**: Standard MCP protocol for tool access
- ✅ **All Audit Issues Fixed**: Issues #1-#10 from audit resolved

See `REFACTORING_PLAN.md` and `AUDIT_FIXES_SDK.md` for technical details.

## What This Does

Transforms any project into a self-organizing multi-agent system with:
- ✅ Specialized agents recruited and trained for your project
- ✅ Complete communication infrastructure (like Microsoft Teams for agents)
- ✅ Job board for task coordination
- ✅ 100% audit trail for traceability
- ✅ Voting mechanisms for conflict resolution
- ✅ Human-in-loop for critical decisions
- ✅ Progressive specialization (agents get smarter over time)

## Installation

### Prerequisites

1. **Install Claude Code CLI**:
   ```bash
   npm install -g @anthropic-ai/claude-code
   ```

2. **Install Python SDK**:
   ```bash
   pip install -r requirements.txt
   ```

   This installs:
   - `claude-agent-sdk` (Official Anthropic SDK)
   - Development dependencies (pytest, black, mypy, etc.)

### Setup

1. **Initialize Communication System**:
   ```bash
   python -c "from communications.core import CommunicationSystem; CommunicationSystem('.').initialize()"
   ```

2. **Test MCP Tools**:
   ```bash
   python examples/sdk_mcp_tools_example.py
   ```

## Quick Start

### Option 1: Using the SDK (Recommended)

```python
import asyncio
from claude_agent_sdk import ClaudeSDKClient, ClaudeAgentOptions, create_sdk_mcp_server
from communications.mcp_tools import ALL_TOOLS, get_all_tool_names

async def main():
    # Create MCP server with communication tools
    comms_server = create_sdk_mcp_server(
        name="comms",
        version="1.0.0",
        tools=ALL_TOOLS
    )

    # Configure Claude
    options = ClaudeAgentOptions(
        mcp_servers={"comms": comms_server},
        allowed_tools=get_all_tool_names() + ["Read", "Write", "Bash"],
        system_prompt={
            "type": "preset",
            "preset": "claude_code",
            "append": "You have access to the Onboard communication system..."
        }
    )

    # Start session
    async with ClaudeSDKClient(options=options) as client:
        await client.query("Initialize the agent ecosystem")
        async for message in client.receive_response():
            # Process messages
            pass

asyncio.run(main())
```

### Option 2: Using Skills (Legacy)

Skills can guide Claude's behavior:
```bash
# Skills are in .claude/skills/
# Claude Code auto-discovers them
```

See `examples/sdk_mcp_tools_example.py` for a complete working example.

## What Gets Created

```
your-project/
├── .claude/
│   ├── agents/                      # Your specialized team
│   │   ├── context-manager.md
│   │   ├── agent-manager.md
│   │   ├── multi-agent-orchestrator.md
│   │   ├── frontend-developer.md
│   │   ├── backend-developer.md
│   │   └── ... (8-12 agents total)
│   │
│   ├── skills/                      # Agent-created skills
│   │   ├── pending/                 # Await human approval
│   │   └── [approved skills]
│   │
│   ├── communications/              # Messaging system
│   │   ├── urgent/                  # Priority broadcasts
│   │   ├── channels/                # #general, #technical, etc
│   │   ├── direct/                  # Agent-to-agent DMs
│   │   ├── messages.db              # SQLite index
│   │   └── PROTOCOL.md              # How to communicate
│   │
│   ├── job-board.json               # Task management
│   ├── audit-trail.jsonl            # Complete history
│   └── agent-registry.json          # Who's who
│
└── [your existing project files]
```

## Core Features

### 1. Smart Agent Recruitment

Analyzes your tech stack and recruits appropriate specialists:
- Tries GitHub repo first: https://github.com/VoltAgent/awesome-claude-code-subagents
- Creates new agents if not found
- Specializes each agent for your project

### 2. Two-Round Specialization

**Round 1 (Light Touch):**
- Adds organizational knowledge
- Communication protocols
- Resource locations
- ~300-500 tokens per agent

**Round 2 (Deep Training - Optional):**
- Domain-specific conventions
- Data source mapping
- Integration patterns
- ~1000-2000 tokens per agent
- Done by agent-manager when patterns emerge

### 3. Communication Infrastructure

Hybrid messaging system:
- **Urgent broadcasts**: System-wide alerts
- **Channels**: Topic-based (like Slack)
- **Direct messages**: Agent-to-agent
- **SQLite index**: Fast queries
- **File-based**: Lightweight, inspectable

### 4. Job Board

Task management with:
- Dependencies tracking
- Status transitions (open → assigned → in-progress → done)
- Priority levels
- Conflict detection (prevents overlapping work)

### 5. Audit Trail

Every action logged:
- Tool calls
- Decisions with reasoning
- File modifications
- Messages sent
- Escalations
- 100% traceability

### 6. Voting & Consensus

When agents disagree:
- Simple majority for low stakes
- Weighted voting for expertise-dependent
- Consensus building for critical decisions
- Human-in-loop as ultimate authority

## Philosophy

Based on FINTO design philosophy:
- **Neuromorphic design**: Hierarchical processing (simple → complex)
- **Progressive disclosure**: Load info only when needed
- **Specialized memory systems**: Different types for different purposes
- **Layered computation**: Deterministic → flexible
- **Token efficiency**: 95%+ of knowledge dormant until needed
- **Self-awareness**: System knows what it knows
- **Fail-safe**: Explicit errors > silent failures

See `resources/finto-philosophy.md` for deep dive.

## Example Usage

### Scenario: New E-Commerce Project

```bash
$ python scripts/analyze_project.py .
{
  "project_name": "shop-app",
  "tech_stack": ["React", "Next.js", "TypeScript", "PostgreSQL"],
  "recommended_agents": [
    "context-manager",
    "agent-manager",
    "multi-agent-orchestrator",
    "frontend-developer",
    "react-specialist",
    "backend-developer",
    "database-optimizer",
    "code-reviewer",
    "test-automator",
    "ui-designer",
    "security-auditor",
    "documentation-engineer"
  ]
}
```

Claude then:
1. Creates communication system
2. Recruits 12 agents
3. Specializes each for e-commerce
4. Sets up job board with initial tasks
5. Starts coordination

Agents self-organize to build the project while you oversee through audit trail.

## Advanced Features

### Checkpointing & Recovery

Resume interrupted workflows:
```python
# System auto-saves checkpoints
# Resume from last known good state
```

### Circuit Breakers

Automatic failure handling:
- Detects failing agents
- Reroutes tasks
- Escalates if critical

### Skill Creation by Agents

When agents find reusable patterns:
1. Propose skill
2. Create in `.claude/skills/pending/`
3. Human reviews
4. Activate if approved

Reduces token usage and improves reliability.

## Resource Documents

In `resources/`:

- **specialization-guidelines.md**: How agents are trained
- **voting-protocols.md**: Decision-making procedures
- **skill-writing-guide.md**: How agents create skills
- **finto-philosophy.md**: Core design principles

## Troubleshooting

### "Agent not found" error
- Check `.claude/agent-registry.json`
- Verify agent file exists in `.claude/agents/`
- Re-run registration if needed

### "Task already assigned" error
- Another agent claimed it first
- Check job board for other available tasks
- System working as intended (prevents overlap)

### Messages not flowing
- Verify `.claude/communications/` exists
- Check SQLite database created
- Test with: `python scripts/setup_communication.py .`

### Audit trail empty
- Ensure `.claude/audit-trail.jsonl` writable
- Test logging: `python scripts/audit_logger.py log test system "hi"`

## Best Practices

### ✅ Do:
- Review pending agents before approval
- Check audit trail regularly
- Let agents self-organize
- Use voting for conflicts
- Document decisions

### ❌ Don't:
- Micromanage communication
- Skip approval steps
- Ignore escalations
- Modify agents mid-task
- Bypass audit logging

## Roadmap

### Version 1.0 (Current)
- [x] Project analysis
- [x] Agent recruitment from GitHub
- [x] Two-round specialization
- [x] Communication infrastructure
- [x] Job board with dependencies
- [x] Audit trail
- [x] Voting mechanisms

### Version 1.1 (Planned)
- [ ] Web UI for audit trail visualization
- [ ] Agent performance metrics
- [ ] Auto-scaling (add agents as needed)
- [ ] Learning loops (system improves)
- [ ] Advanced pattern detection

### Version 2.0 (Future)
- [ ] Multi-project coordination
- [ ] Agent marketplace
- [ ] Skill sharing across projects
- [ ] ML-based task assignment
- [ ] Predictive bottleneck detection

## Contributing

Found a bug or have an idea?
- File issue in project repo
- Propose improvements
- Share successful patterns

## License

MIT License - use freely, modify as needed.

## Acknowledgments

- Inspired by FINTO design philosophy
- Agent templates from VoltAgent/awesome-claude-code-subagents
- Built with love and many hours of trial & error
- Special thanks to Claude for being an amazing coding partner

---

**Remember:** This is a seed that unfolds organically. Plant it, water it with good specifications, and watch your multi-agent team flourish. 🌱 → 🌳

**Questions?** Read the resource docs in `resources/` - they're comprehensive and answer most questions.

**Ready?** Run the analyzer and let's build something amazing!
