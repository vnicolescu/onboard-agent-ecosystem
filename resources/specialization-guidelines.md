# Agent Specialization Guidelines

## Overview

Agent specialization occurs in two rounds to balance token efficiency with deep domain expertise.

## Round 1: Light Touch (Organizational Principles)

**Purpose:** Enable immediate coordination without heavy context load

**What Gets Added:**
1. **Project Context References**
   - Where to find project spec
   - Key technologies used
   - Important file locations

2. **Communication Protocol**
   - How to query context-manager
   - Message types and priorities
   - Job board interaction
   - Audit logging requirements

3. **Meta-Orchestrator Links**
   - Who coordinates what
   - When to escalate
   - How to request resources

4. **Team Structure**
   - Other active agents
   - Channels to monitor
   - Collaboration patterns

**What NOT to Add:**
- Detailed domain knowledge (wait for Round 2)
- Company-specific conventions (in project spec, not agent)
- Data source details (context-manager handles this)
- Implementation specifics (too heavy for Round 1)

**Token Budget:** ~300-500 tokens added per agent

## Round 2: Deep Training (Domain Expertise)

**Purpose:** Specialize agents with project-specific knowledge

**Timing:** AFTER communication system initialized and project spec comprehensive

**Performed By:** agent-manager using training protocol

**What Gets Added:**
1. **Domain-Specific Knowledge**
   - Coding standards and conventions
   - API patterns used in project
   - Testing requirements
   - Documentation formats
   - Performance targets

2. **Data Source Mapping**
   - Where configuration lives
   - How to access secrets
   - Database schemas
   - External API endpoints

3. **Integration Patterns**
   - How services communicate
   - Authentication flows
   - Error handling conventions
   - Logging patterns

4. **Company Policies**
   - Security requirements
   - Compliance needs
   - Review processes
   - Deployment procedures

**Token Budget:** ~1000-2000 tokens added per agent

## Specialization Anti-Patterns

**❌ Don't duplicate project spec content**
- Agents should REFERENCE spec, not repeat it
- "See specs/requirements.md section 3.2" not inline details

**❌ Don't hardcode changing information**
- API endpoints change → reference config file
- Team members change → reference team roster
- Deadlines change → reference project timeline

**❌ Don't over-specialize**
- Keep general problem-solving ability
- Maintain flexibility for edge cases
- Don't lock into rigid procedures

**❌ Don't break agent identity**
- Maintain core role and expertise
- Add context, don't replace personality
- Keep "you are a senior X" framing

## Approval Workflow

### Round 1 Agents (Pending Folder)
1. Agents created in `.claude/agents/pending/`
2. Human reviews organizational additions
3. Human moves approved agents to `.claude/agents/`
4. Agents become active

### Round 2 Training (In-Place Updates)
1. agent-manager proposes deep specialization
2. Creates training plan in `.claude/training-plans/`
3. Human approves plan
4. agent-manager applies training
5. Updated agents stay in `.claude/agents/`

## Quality Checks

**Before Round 1 Deployment:**
- [ ] Communication protocol correct
- [ ] References valid (not hallucinated)
- [ ] Token budget reasonable
- [ ] No business logic embedded
- [ ] Audit logging instructions clear

**Before Round 2 Training:**
- [ ] Project spec comprehensive
- [ ] Data sources mapped
- [ ] Integration patterns documented
- [ ] Training plan approved
- [ ] Rollback plan exists

## Example: Round 1 vs Round 2

**Round 1 (Light Touch):**
```markdown
## Project Context
**Project:** E-commerce Checkout
**Technologies:** React, Next.js, Stripe
**Specification:** See `specs/blueprint.md`

**Communication:** 
- Query context-manager before work
- Update job-board.json when taking tasks
- Log decisions to audit trail
```

**Round 2 (Deep Training):**
```markdown
## Deep Domain Training

**Coding Standards:**
- Use TypeScript strict mode
- Follow Airbnb style guide (see `.eslintrc`)
- Component tests required (>80% coverage)
- Storybook stories for all UI components

**API Integration:**
- Stripe API v2024-10-28
- Authentication via JWT (see `lib/auth.ts`)
- Rate limiting: 100 req/min (circuit breaker in place)
- Error handling: See `lib/error-handler.ts`

**Data Sources:**
- Product catalog: PostgreSQL `products` schema
- User sessions: Redis cluster
- Payment methods: Stripe API
- Analytics: PostHog (token in `.env.local`)

**Security Requirements:**
- PCI-DSS compliance mandatory
- No payment data in logs
- HTTPS only
- CSP headers enforced
```

## Verification

**How to verify good specialization:**

1. **References are Valid**
   - All file paths exist
   - All URLs work
   - All tools available

2. **Not Redundant**
   - Check against project spec
   - Ensure not duplicating
   - Add only unique value

3. **Actionable**
   - Agent can use info immediately
   - No vague guidance
   - Concrete steps provided

4. **Maintainable**
   - Updates won't break agents
   - Conventions documented centrally
   - References > hardcoded values

---
**Version:** 1.0  
**Last Updated:** {timestamp}
