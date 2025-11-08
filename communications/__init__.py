"""
Multi-Agent Communication System

A transparent, reliable messaging system for coordinating 20+ concurrent agents.

Simple usage:
    from communications import AgentMessenger

    messenger = AgentMessenger("my-agent-id")
    messenger.send("other-agent", "Hello!")
    messages = messenger.receive()
"""

from .core import CommunicationSystem
from .agent_sdk import AgentMessenger

__version__ = "1.0.0"
__all__ = ["CommunicationSystem", "AgentMessenger"]
