# Refactoring Plan: Migrate to Official Anthropic Python Agent SDK

## Current Architecture Issues

**Problem**: Custom polling-based agent system doesn't align with SDK's push-based model.

Current system:
- Agents as markdown templates
- Custom AgentMessenger that polls SQLite
- Agents run as separate processes
- Pull model: agents poll for messages

**SDK Model**:
- Agents defined using `AgentDefinition`
- Agents invoked by Claude via Task tool
- Push model: orchestrator invokes agents as needed
- No separate processes - agents are on-demand subagents

## New Architecture

### Layer 1: Communication Infrastructure (MCP Tools)

Keep SQLite communication system, expose as MCP tools:

```python
@tool("comm-send-message", "Send a message to another agent or broadcast", {...})
@tool("comm-receive-messages", "Receive pending messages for current agent", {...})
@tool("comm-claim-message", "Atomically claim a message for processing", {...})
@tool("comm-complete-message", "Mark a message as processed", {...})
@tool("comm-subscribe-channel", "Subscribe to a communication channel", {...})
@tool("comm-send-heartbeat", "Update agent health status", {...})
@tool("comm-get-health", "Get health status of an agent", {...})
```

### Layer 2: Job Board (MCP Tools)

```python
@tool("jobboard-create-task", "Create a new task", {...})
@tool("jobboard-claim-task", "Atomically claim a task", {...})
@tool("jobboard-update-task", "Update task status", {...})
@tool("jobboard-get-tasks", "Get open tasks from job board", {...})
```

### Layer 3: Voting System (MCP Tools)

```python
@tool("voting-initiate", "Initiate a vote", {...})
@tool("voting-cast-vote", "Cast a vote", {...})
@tool("voting-tally", "Tally votes and get results", {...})
@tool("voting-get-status", "Get current status of a vote", {...})
```

### Layer 4: Agent Definitions

Convert markdown templates to `AgentDefinition`:

```python
agents = {
    "context-manager": AgentDefinition(
        description="Provides project context and domain knowledge. Use when you need information about project structure, patterns, or conventions.",
        prompt="You are the context manager...",
        tools=["Read", "Grep", "Glob", "comm-send-message", "comm-receive-messages"]
    ),
    "frontend-developer": AgentDefinition(
        description="Senior frontend developer specializing in React. Use for frontend tasks.",
        prompt="You are a senior frontend developer...",
        tools=["Read", "Write", "Edit", "Bash", "comm-send-message", "jobboard-claim-task"]
    ),
    # ... more agents
}
```

### Layer 5: Main Orchestrator

Uses `ClaudeSDKClient` to coordinate agents:

```python
from claude_agent_sdk import ClaudeSDKClient, ClaudeAgentOptions, create_sdk_mcp_server

# Create MCP server with all tools
comm_server = create_sdk_mcp_server(
    name="onboard-comms",
    version="1.0.0",
    tools=[
        comm_send_message,
        comm_receive_messages,
        # ... all tools
    ]
)

# Configure options
options = ClaudeAgentOptions(
    mcp_servers={"comms": comm_server},
    agents=agents,
    allowed_tools=[
        "Task",  # For spawning subagents
        "mcp__comms__*",  # All comm tools
        "Read", "Write", "Edit", "Bash"
    ],
    system_prompt={
        "type": "preset",
        "preset": "claude_code",
        "append": "You are the main orchestrator for Project Onboard..."
    }
)

# Run orchestrator
async with ClaudeSDKClient(options=options) as client:
    await client.query("Initialize the onboard agent ecosystem")
    async for message in client.receive_response():
        # Process messages
```

## Migration Steps

### Phase 1: Create MCP Tools Layer (CURRENT)
1. ✅ Create `communications/mcp_tools.py` with MCP tool definitions
2. ✅ Wrap existing CommunicationSystem functions
3. ✅ Wrap VotingSystem functions
4. ✅ Test MCP tools independently

### Phase 2: Convert Agent Templates
1. Create `agents/definitions.py` with AgentDefinition instances
2. Convert each markdown template to AgentDefinition
3. Update agent prompts to reference MCP tools instead of AgentMessenger

### Phase 3: Create Main Orchestrator
1. Create `orchestrator/main.py`
2. Implement ClaudeSDKClient setup
3. Implement job board monitoring
4. Implement agent invocation logic

### Phase 4: Testing & Documentation
1. Test end-to-end workflows
2. Update all documentation
3. Update skills to reflect new architecture
4. Update examples

## Key Changes from Audit

Now that we're using the SDK:

### Issue #1: Skill Invocation
- **Old**: Unclear how agents invoke skills
- **New**: Skills are invoked by Claude Code's skill system, not by agents directly
- **Fix**: Document that skills guide the orchestrator, not individual agents

### Issue #2: Health Check
- **Old**: Agents need to check context-manager health before querying
- **New**: Orchestrator manages agent availability, spawns context-manager on-demand
- **Fix**: Orchestrator checks health, agents don't worry about it

### Issue #7: Error Response Handling
- **Old**: Agents need to send error responses
- **New**: SDK handles tool errors automatically via `is_error` in tool results
- **Fix**: Implement proper error returns in MCP tools

### Issue #9: Circular Dependencies
- **Old**: Need to track request chains
- **New**: SDK's Task tool handles subagent invocation, prevents cycles
- **Fix**: Rely on SDK's built-in protection

## Benefits of SDK Architecture

1. **Automatic Context Management**: Each agent invocation has isolated context
2. **Parallel Execution**: SDK can run multiple subagents concurrently
3. **Built-in Tool Safety**: Permission system prevents dangerous operations
4. **Standard Protocol**: Uses MCP (Model Context Protocol) - industry standard
5. **Better Error Handling**: SDK provides structured error reporting
6. **Hooks Support**: Can intercept tool use for auditing/security
7. **Cost Tracking**: SDK provides usage and cost metrics
8. **Session Management**: Can resume sessions, fork conversations

## File Structure

```
onboard-agent-ecosystem/
├── communications/
│   ├── core.py                 # Keep SQLite system as-is
│   ├── voting.py               # Keep voting system as-is
│   ├── mcp_tools.py            # NEW: MCP tool wrappers
│   └── agent_sdk.py            # DEPRECATED: Remove after migration
├── agents/
│   ├── definitions.py          # NEW: AgentDefinition instances
│   └── registry.py             # NEW: Agent registry and metadata
├── orchestrator/
│   ├── main.py                 # NEW: Main orchestrator using ClaudeSDKClient
│   ├── job_monitor.py          # NEW: Job board monitoring
│   └── health_checker.py       # NEW: Health monitoring
├── templates/agents/           # Keep for reference, but deprecated
├── .claude/
│   ├── skills/                 # Keep and update for SDK
│   └── agents/                 # Optional: filesystem-based agents
└── examples/
    ├── simple_orchestration.py # NEW: Simple example
    └── multi_agent_workflow.py # NEW: Complex example
```

## Testing Strategy

1. **Unit Tests**: Test each MCP tool individually
2. **Integration Tests**: Test orchestrator with mock agents
3. **End-to-End Tests**: Full workflow with real agents
4. **Performance Tests**: Measure parallelization benefits

## Rollback Plan

Keep old system in `legacy/` folder until new system is proven:

```bash
git checkout -b sdk-migration
# Do all work on branch
# Keep main branch with old system
# Only merge when fully tested
```

## Timeline

- Phase 1 (MCP Tools): 1-2 hours
- Phase 2 (Agent Definitions): 1 hour
- Phase 3 (Orchestrator): 2-3 hours
- Phase 4 (Testing/Docs): 2 hours

**Total**: ~6-8 hours of focused work

## Next Steps

1. Start with Phase 1: Create `communications/mcp_tools.py`
2. Implement and test each MCP tool
3. Create simple example to verify tools work
4. Then proceed to Phase 2

---

**Status**: Planning complete, ready to implement Phase 1
**Last Updated**: 2025-11-08
