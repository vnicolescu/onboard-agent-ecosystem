#!/usr/bin/env python3
"""
Simple example demonstrating the MCP tools for onboard agent communication.

This example shows how to:
1. Create an MCP server with communication tools
2. Use the tools with Claude Agent SDK
3. Initialize the communication system
4. Send and receive messages

Run with: python examples/sdk_mcp_tools_example.py
"""

import asyncio
from pathlib import Path
from claude_agent_sdk import ClaudeSDKClient, ClaudeAgentOptions, create_sdk_mcp_server

# Import our MCP tools
import sys
sys.path.append(str(Path(__file__).parent.parent))

from communications.mcp_tools import ALL_TOOLS, get_all_tool_names
from communications.core import CommunicationSystem


async def main():
    """
    Example: Using MCP tools with Claude Agent SDK
    """

    print("="*60)
    print("Onboard Agent Ecosystem - MCP Tools Example")
    print("="*60)

    # Step 1: Initialize communication system
    print("\n📦 Initializing communication system...")
    comm = CommunicationSystem(".")
    result = comm.initialize()
    print(f"✅ Communication system initialized:")
    print(f"   Database: {result['db_path']}")
    print(f"   Channels: {', '.join(result['default_channels'])}")

    # Step 2: Create MCP server with our tools
    print("\n🔧 Creating MCP server with communication tools...")
    comms_server = create_sdk_mcp_server(
        name="comms",
        version="1.0.0",
        tools=ALL_TOOLS
    )
    print(f"✅ MCP server created with {len(ALL_TOOLS)} tools")

    # Step 3: Configure Claude Agent SDK options
    print("\n⚙️  Configuring Claude Agent SDK...")
    options = ClaudeAgentOptions(
        mcp_servers={"comms": comms_server},
        allowed_tools=get_all_tool_names() + ["Read", "Write", "Bash"],
        permission_mode="acceptEdits",
        system_prompt={
            "type": "preset",
            "preset": "claude_code",
            "append": """
You have access to the Onboard Agent Communication System through MCP tools.

Available tool categories:
- Communication: comm-send-message, comm-receive-messages, comm-claim-message, comm-complete-message
- Health: comm-send-heartbeat, comm-get-agent-health
- Channels: comm-subscribe-channel
- Job Board: jobboard-create-task, jobboard-claim-task, jobboard-update-task, jobboard-get-tasks
- Voting: voting-initiate, voting-cast-vote, voting-tally, voting-get-status

Test the communication system by:
1. Sending a heartbeat as "test-agent"
2. Creating a task on the job board
3. Checking agent health
4. Listing open tasks
"""
        }
    )

    # Step 4: Test with Claude
    print("\n🤖 Starting Claude Agent SDK session...")
    print("=" * 60)

    async with ClaudeSDKClient(options=options) as client:
        # Test 1: Basic communication system operations
        await client.query("""
Test the onboard communication system:

1. Send a heartbeat as "test-agent" with status "active"
2. Create a task titled "Implement login feature" with priority 8
3. Get the list of open tasks
4. Check the health of "test-agent"

Provide a clear summary of each operation's result.
""")

        print("\n📨 Processing messages from Claude...\n")

        async for message in client.receive_response():
            # Just iterate through - the SDK handles display
            pass

    print("\n" + "=" * 60)
    print("✅ Example completed successfully!")
    print("\nThe communication system is now ready for multi-agent orchestration.")
    print("\nNext steps:")
    print("  1. Define agents using AgentDefinition")
    print("  2. Create main orchestrator")
    print("  3. Test multi-agent workflows")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
