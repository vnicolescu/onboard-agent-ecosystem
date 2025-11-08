# Voting & Consensus Protocols

## Overview

When agents disagree on critical decisions, structured voting ensures progress while maintaining quality and involving humans when necessary.

## When to Use Voting

### **Mandatory Voting Scenarios:**
1. **Architecture Decisions**
   - Framework selection
   - Database choices
   - Major refactoring
   - Breaking API changes

2. **Contradictory Expert Opinions**
   - ≥2 agents disagree on approach
   - No clear "correct" answer
   - Trade-offs must be evaluated

3. **Resource Allocation**
   - Budget decisions
   - Timeline extensions
   - Team expansion requests

4. **Quality Gates**
   - Production deployment approval
   - Release criteria met/not met
   - Security vulnerability severity

### **Optional Voting (Efficiency Gains):**
- Feature prioritization
- Code style preferences  
- Tool selection (non-critical)
- Documentation format

## Voting Mechanisms

### 1. Simple Majority (Fast)

**Use When:**
- Low stakes
- Clear options
- Fast decision needed
- Reversible decision

**Process:**
1. Poll all relevant agents
2. Count votes
3. Winner = >50% votes
4. Execute immediately

**Example:** "Should we use Jest or Vitest for testing?"

---

### 2. Weighted Voting (Expert Priority)

**Use When:**
- Domain expertise matters
- Some agents more qualified
- Technical complexity high

**Weights:**
- Domain expert: 3 votes
- Related specialist: 2 votes
- Generalist: 1 vote

**Process:**
1. Identify domain experts
2. Assign weights
3. Calculate weighted sum
4. Winner = highest score

**Example:** "Database schema design" → database-optimizer gets weight=3

---

### 3. Consensus Building (High Stakes)

**Use When:**
- Critical path decision
- Irreversible change
- High-cost failure
- Security implications

**Process:**
1. **Round 1: Proposals**
   - Each agent submits proposal
   - Include rationale & trade-offs
   
2. **Round 2: Discussion**
   - Agents debate merits
   - Identify concerns
   - Refine proposals

3. **Round 3: Consensus Check**
   - Each agent votes: Support / Acceptable / Block
   - "Block" requires explanation
   - Iterate if blocked

4. **Resolution:**
   - Unanimous support → Execute
   - No blocks + majority support → Execute
   - Any blocks → Human escalation

**Example:** "Migrate production database to new schema"

---

### 4. Human-in-Loop (Ultimate Authority)

**Automatic Triggers:**
- Consensus deadlock (3+ rounds, no agreement)
- Security vulnerability debate
- Compliance question
- Budget > threshold
- Timeline extension > 20%

**Process:**
1. Package decision context
2. Summarize positions
3. Highlight trade-offs
4. Request human decision
5. Execute human's choice
6. Document in audit trail

## Vote Recording

All votes logged to audit trail:

```json
{
  "vote_id": "vote-abc123",
  "timestamp": "2025-11-07T10:30:00Z",
  "topic": "Select payment gateway",
  "mechanism": "weighted_voting",
  "participants": [
    {"agent": "backend-dev-01", "vote": "Stripe", "weight": 2},
    {"agent": "security-audit-01", "vote": "Stripe", "weight": 3},
    {"agent": "frontend-dev-01", "vote": "PayPal", "weight": 1}
  ],
  "result": "Stripe (8 weighted votes)",
  "executed": true
}
```

## Decision Quality Safeguards

### Red Flags (Trigger Human Review):
- ⚠️ Vote result contradicts established requirements
- ⚠️ Security expert blocks but overruled
- ⚠️ <70% confidence in any agent's vote
- ⚠️ Insufficient information to decide
- ⚠️ Rushed timeline (decision in <1 hour for major change)

### Cooling Off Period:
For critical decisions:
- Announce vote 24 hours before
- Allow async participation
- Provide full context upfront
- No snap decisions

### Veto Power (Always Human):
Humans can veto ANY agent decision:
- Security concerns
- Legal/compliance issues
- Business strategy conflicts
- Gut feeling something's wrong

## Common Voting Scenarios

### Scenario 1: Framework Selection
```
Context: Choose frontend framework
Options: React, Vue, Svelte
Stakes: High (long-term commitment)
Mechanism: Consensus Building

Process:
1. frontend-dev proposes React (familiar, large ecosystem)
2. performance-eng supports Svelte (smaller bundle)
3. team-lead supports React (team expertise)
4. Discussion: Trade ecosystem vs performance
5. Consensus: React (2 support, 1 acceptable, 0 blocks)
```

### Scenario 2: Production Deployment
```
Context: Deploy v2.0 to production
Options: Deploy / Delay
Stakes: Critical (customer impact)
Mechanism: Quality Gate Voting

Required Approvals:
- qa-expert: PASS
- security-auditor: PASS
- tech-lead: APPROVE

Process:
1. qa-expert: "All tests green" → PASS
2. security-auditor: "Vulnerability in dependency" → BLOCK
3. Escalate: Fix vulnerability first
4. Re-vote after fix
5. All pass → Deploy
```

### Scenario 3: Code Review Disagreement
```
Context: Merge PR with controversial approach
Options: Approve / Request Changes / Reject
Stakes: Medium (reversible)
Mechanism: Simple Majority

Process:
1. code-reviewer-01: "Approve" (clever solution)
2. code-reviewer-02: "Request changes" (too clever, hard to maintain)
3. senior-dev: "Approve" (trust author)
4. Result: 2-1 Approve → Merge
5. Document concerns in commit message
```

## Vote Manipulation Prevention

**Sybil Attack Prevention:**
- One vote per unique agent
- Agent identity verified
- Vote weight capped at 3x

**Influence Prevention:**
- Votes logged before revealing
- No vote changing after seeing others
- Simultaneous submission enforced

**Gaming Detection:**
- Pattern analysis on votes
- Unusual alliances flagged
- Audit review of surprising outcomes

## Best Practices

### For Agents Initiating Votes:
1. **Clear Framing**
   - State question precisely
   - List all options
   - Provide context
   - Set deadline

2. **Information Equality**
   - All voters get same info
   - No hidden context
   - Time to research

3. **Bias Acknowledgment**
   - Declare conflicts of interest
   - "I prefer X because Y"

### For Voting Agents:
1. **Vote Your Expertise**
   - Stay in your domain
   - Defer to experts outside your area
   - Abstain if uninformed

2. **Provide Reasoning**
   - "I vote X because..."
   - Reference data/docs
   - Explain trade-offs considered

3. **Accept Outcome**
   - Support winning decision
   - Voice concerns, then commit
   - No sabotage

## Escalation to Human

**Package Contains:**
1. Decision question
2. All proposals with rationale
3. Vote tallies
4. Key disagreements
5. Recommended action (but human decides)
6. Urgency level

**Example Escalation:**
```markdown
# Human Decision Needed: Database Migration

**Question:** Migrate to PostgreSQL or stay with MySQL?

**Proposals:**
1. PostgreSQL (database-optimizer, backend-lead)
   - Better JSON support
   - Superior query planner
   - Migration cost: 40 hours

2. MySQL (devops-eng, legacy-maintainer)
   - Team familiarity
   - Existing tooling
   - No migration cost

**Votes:** 2-2 tie after 3 rounds

**Key Concerns:**
- database-optimizer: "MySQL limiting new features"
- devops-eng: "Migration risk during peak season"

**Recommendation:** Delay decision until after Q4 peak

**Urgency:** Medium (blocking 2 features, not critical path)

**Your decision:**
[ ] PostgreSQL - Migrate now
[ ] MySQL - Stay for now
[ ] PostgreSQL - Migrate after Q4
[ ] Other: ___________
```

---
**Version:** 1.0  
**Last Updated:** {timestamp}
