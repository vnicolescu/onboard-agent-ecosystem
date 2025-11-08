#!/usr/bin/env python3
"""
Voting System for Multi-Agent Coordination

Implements voting protocols for agent decision-making:
- Simple majority voting
- Weighted voting (expertise-based)
- Consensus building
- Vote tracking and audit trail

Based on: resources/voting-protocols.md
"""

import json
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any

from .core import CommunicationSystem


class VotingSystem:
    """
    Voting system for multi-agent consensus and decision-making.

    Uses CommunicationSystem for vote broadcasting and collection.
    """

    def __init__(self, project_root: str = "."):
        """
        Initialize voting system.

        Args:
            project_root: Path to project root (contains .claude/)
        """
        self.project_root = Path(project_root).resolve()
        self.votes_dir = self.project_root / ".claude" / "votes"
        self.votes_dir.mkdir(parents=True, exist_ok=True)

        self.comm = CommunicationSystem(project_root)

    def initiate_vote(
        self,
        proposer_agent: str,
        topic: str,
        options: List[str],
        mechanism: str = "simple_majority",
        eligible_voters: Optional[List[str]] = None,
        timeout_hours: int = 24,
        description: Optional[str] = None
    ) -> str:
        """
        Initiate a new vote.

        Args:
            proposer_agent: Agent proposing the vote
            topic: Vote topic/question
            options: List of voting options
            mechanism: Voting mechanism (simple_majority, weighted, consensus)
            eligible_voters: List of eligible voter IDs (None = all registered agents)
            timeout_hours: Hours until vote closes
            description: Optional detailed description

        Returns:
            vote_id: Unique vote identifier

        Example:
            vote_id = voting.initiate_vote(
                proposer_agent="frontend-dev-01",
                topic="Use TypeScript for new components?",
                options=["yes", "no", "defer"],
                mechanism="simple_majority",
                timeout_hours=24
            )
        """
        vote_id = f"vote-{uuid.uuid4().hex[:8]}"

        # Get all registered agents if no specific voters provided
        if not eligible_voters:
            eligible_voters = self._get_all_agents()

        vote_data = {
            "vote_id": vote_id,
            "topic": topic,
            "description": description or topic,
            "options": options,
            "mechanism": mechanism,
            "proposed_by": proposer_agent,
            "proposed_at": datetime.utcnow().isoformat() + "Z",
            "deadline": (datetime.utcnow() + timedelta(hours=timeout_hours)).isoformat() + "Z",
            "eligible_voters": eligible_voters,
            "votes_cast": {},
            "status": "open"
        }

        # Save vote record
        vote_file = self.votes_dir / f"{vote_id}.json"
        with open(vote_file, 'w') as f:
            json.dump(vote_data, f, indent=2)

        # Broadcast to eligible voters
        vote_message = {
            "vote_id": vote_id,
            "topic": topic,
            "description": description or topic,
            "options": options,
            "mechanism": mechanism,
            "deadline": vote_data["deadline"],
            "instructions": "Cast your vote using messenger.send('voting-system', 'vote.cast', {...})"
        }

        self.comm.send_message(
            from_agent="voting-system",
            message_type="vote.initiate",
            payload=vote_message,
            channel="general",
            priority=9  # Urgent
        )

        return vote_id

    def cast_vote(
        self,
        agent_id: str,
        vote_id: str,
        choice: str,
        reasoning: str = ""
    ) -> Dict[str, Any]:
        """
        Cast a vote.

        Args:
            agent_id: Agent casting the vote
            vote_id: Vote ID
            choice: Selected option
            reasoning: Optional reasoning for choice

        Returns:
            Dict with success/error status

        Example:
            result = voting.cast_vote(
                agent_id="frontend-dev-01",
                vote_id="vote-abc123",
                choice="yes",
                reasoning="Type safety reduces bugs significantly"
            )
        """
        vote_file = self.votes_dir / f"{vote_id}.json"

        if not vote_file.exists():
            return {"error": "Vote not found"}

        # Load vote data
        with open(vote_file, 'r') as f:
            vote_data = json.load(f)

        # Validate
        if agent_id not in vote_data["eligible_voters"]:
            return {"error": "Not eligible to vote"}

        if vote_data["status"] != "open":
            return {"error": f"Vote is {vote_data['status']}"}

        if choice not in vote_data["options"]:
            return {"error": f"Invalid choice. Must be one of: {vote_data['options']}"}

        # Check if already voted
        if agent_id in vote_data["votes_cast"]:
            return {"error": "Already voted. Cannot change vote."}

        # Record vote
        vote_data["votes_cast"][agent_id] = {
            "choice": choice,
            "reasoning": reasoning,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }

        # Save updated vote
        with open(vote_file, 'w') as f:
            json.dump(vote_data, f, indent=2)

        # Notify via communication system
        self.comm.send_message(
            from_agent="voting-system",
            message_type="vote.recorded",
            payload={
                "vote_id": vote_id,
                "voter": agent_id,
                "votes_received": len(vote_data["votes_cast"]),
                "votes_needed": len(vote_data["eligible_voters"])
            },
            channel="general",
            priority=5
        )

        return {"success": True, "votes_cast": len(vote_data["votes_cast"])}

    def tally_vote(self, vote_id: str, force: bool = False) -> Dict[str, Any]:
        """
        Tally votes and determine outcome.

        Args:
            vote_id: Vote ID to tally
            force: Force tally even if deadline not reached

        Returns:
            Dict with tally results and outcome

        Example:
            result = voting.tally_vote("vote-abc123")
            print(f"Winner: {result['outcome']}")
            print(f"Tally: {result['tally']}")
        """
        vote_file = self.votes_dir / f"{vote_id}.json"

        if not vote_file.exists():
            return {"error": "Vote not found"}

        # Load vote data
        with open(vote_file, 'r') as f:
            vote_data = json.load(f)

        # Check if can tally
        deadline = datetime.fromisoformat(vote_data["deadline"].replace('Z', '+00:00'))
        if not force and datetime.utcnow() < deadline.replace(tzinfo=None):
            return {"error": "Vote still open. Use force=True to tally early."}

        # Tally based on mechanism
        mechanism = vote_data["mechanism"]
        votes_cast = vote_data["votes_cast"]

        if mechanism == "simple_majority":
            result = self._tally_simple_majority(votes_cast, vote_data["options"])
        elif mechanism == "weighted":
            result = self._tally_weighted(votes_cast, vote_data)
        elif mechanism == "consensus":
            result = self._tally_consensus(votes_cast, vote_data)
        else:
            return {"error": f"Unknown mechanism: {mechanism}"}

        # Update vote record
        vote_data["status"] = "closed"
        vote_data["result"] = result
        vote_data["closed_at"] = datetime.utcnow().isoformat() + "Z"

        with open(vote_file, 'w') as f:
            json.dump(vote_data, f, indent=2)

        # Broadcast result
        self.comm.send_message(
            from_agent="voting-system",
            message_type="vote.result",
            payload={
                "vote_id": vote_id,
                "topic": vote_data["topic"],
                "outcome": result["outcome"],
                "tally": result["tally"],
                "total_votes": result["total_votes"]
            },
            channel="general",
            priority=8
        )

        return result

    def get_vote_status(self, vote_id: str) -> Optional[Dict[str, Any]]:
        """Get current status of a vote."""
        vote_file = self.votes_dir / f"{vote_id}.json"

        if not vote_file.exists():
            return None

        with open(vote_file) as f:
            return json.load(f)

    def get_open_votes(self) -> List[Dict[str, Any]]:
        """Get list of open votes."""
        open_votes = []

        for vote_file in self.votes_dir.glob("vote-*.json"):
            with open(vote_file) as f:
                vote_data = json.load(f)
                if vote_data["status"] == "open":
                    open_votes.append(vote_data)

        return sorted(open_votes, key=lambda v: v["proposed_at"], reverse=True)

    # Helper methods

    def _get_all_agents(self) -> List[str]:
        """Get list of all registered agents."""
        # Query agent_status table for registered agents
        conn = self.comm._get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT agent_id FROM agent_status")
        agents = [row[0] for row in cursor.fetchall()]

        return agents if agents else ["system"]

    def _tally_simple_majority(
        self,
        votes_cast: Dict[str, Dict],
        options: List[str]
    ) -> Dict[str, Any]:
        """Tally using simple majority."""
        tally = {option: 0 for option in options}

        for vote in votes_cast.values():
            choice = vote["choice"]
            tally[choice] = tally.get(choice, 0) + 1

        # Find winner
        if not tally:
            outcome = "no_votes"
        else:
            winner = max(tally, key=tally.get)
            outcome = winner

        return {
            "outcome": outcome,
            "tally": tally,
            "total_votes": len(votes_cast),
            "mechanism": "simple_majority"
        }

    def _tally_weighted(
        self,
        votes_cast: Dict[str, Dict],
        vote_data: Dict
    ) -> Dict[str, Any]:
        """Tally using weighted voting (based on expertise)."""
        # For now, implement simple weighted based on agent type
        # Can be enhanced with actual expertise scores
        tally = {}

        for agent_id, vote in votes_cast.items():
            choice = vote["choice"]
            # Weight: specialist agents get 2x weight
            weight = 2 if any(x in agent_id for x in ['specialist', 'expert', 'senior']) else 1

            tally[choice] = tally.get(choice, 0) + weight

        if not tally:
            outcome = "no_votes"
        else:
            winner = max(tally, key=tally.get)
            outcome = winner

        return {
            "outcome": outcome,
            "tally": tally,
            "total_votes": len(votes_cast),
            "mechanism": "weighted"
        }

    def _tally_consensus(
        self,
        votes_cast: Dict[str, Dict],
        vote_data: Dict
    ) -> Dict[str, Any]:
        """Tally using consensus (requires unanimous or near-unanimous agreement)."""
        tally = {}

        for vote in votes_cast.values():
            choice = vote["choice"]
            tally[choice] = tally.get(choice, 0) + 1

        total_votes = len(votes_cast)
        total_eligible = len(vote_data["eligible_voters"])

        # Consensus requires 80% agreement
        consensus_threshold = 0.8

        if not tally:
            outcome = "no_consensus"
        else:
            winner = max(tally, key=tally.get)
            winner_pct = tally[winner] / total_votes if total_votes > 0 else 0

            if winner_pct >= consensus_threshold:
                outcome = winner
            else:
                outcome = "no_consensus"

        return {
            "outcome": outcome,
            "tally": tally,
            "total_votes": total_votes,
            "mechanism": "consensus",
            "consensus_threshold": consensus_threshold
        }
