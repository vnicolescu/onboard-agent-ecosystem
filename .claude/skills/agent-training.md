---
name: agent-training
description: Deep specialization training for agents based on project patterns. Use when agents need Round 2 training after gaining project experience. Analyzes codebase, detects patterns, and generates contextual knowledge injection.
---

# Agent Training - Round 2 Deep Specialization

## When to Use This Skill

Use this skill to provide deep, project-specific training to agents after they've gained experience:

**Triggers:**
- 24+ hours of project work
- 50+ tasks completed
- Patterns have emerged in the codebase
- Agent-manager determines training is needed
- Manual human request

**What This Skill Does:**
- Analyzes project codebase for patterns and conventions
- Detects coding standards, API patterns, testing approaches
- Generates agent-specific training content
- Injects contextual knowledge into agent templates

## Training Workflow

### Step 1: Analyze Project Patterns

**Read the codebase** to understand:

1. **Coding Standards**
   - Linter configs (.eslintrc, .prettierrc, pyproject.toml)
   - Code style consistency
   - Naming conventions
   - File organization patterns

2. **API Patterns**
   - REST vs GraphQL
   - Authentication approach
   - Error handling patterns
   - Request/response formats

3. **Testing Patterns**
   - Test framework (Jest, Pytest, etc.)
   - Coverage expectations
   - Test file organization
   - Mocking patterns

4. **Data Sources**
   - Database types (PostgreSQL, MongoDB, etc.)
   - ORM/query patterns
   - Connection management
   - Migration strategies

5. **Integration Points**
   - Third-party services (Stripe, AWS, etc.)
   - External APIs
   - Authentication providers
   - Message queues

6. **Common Libraries**
   - Major frameworks and versions
   - Utility libraries
   - Custom internal libraries

**Example Analysis:**

```python
# Use Read tool to examine files
# Example: Read package.json
content = read_file("package.json")

# Understand the stack
# "react": "^18.2.0" → React 18
# "zustand": "^4.0.0" → State management
# "@stripe/stripe-js": "^1.0.0" → Payment integration

# Read .eslintrc to understand code standards
# Read test files to understand testing patterns
# Read API files to understand endpoints
```

### Step 2: Infer Agent Needs Based on Role

For each agent, determine what project-specific knowledge they need:

**Frontend Developer:**
- Framework version and patterns
- Component architecture
- State management approach
- Styling system (Tailwind, CSS-in-JS, etc.)
- Build configuration

**Backend Developer:**
- API conventions
- Database patterns
- Authentication flow
- Error handling standards
- Deployment process

**QA/Testing:**
- Test framework
- Coverage requirements
- Test data patterns
- CI/CD integration

**Database Specialist:**
- Database type and version
- Schema conventions
- Migration patterns
- Query optimization practices

### Step 3: Generate Training Content

Create markdown training sections with:

1. **Project-Specific Context**
   - Not generic knowledge
   - Actual patterns from THIS codebase
   - Real file paths and examples

2. **Actionable Information**
   - Where to find things
   - How things are done here
   - What conventions to follow

3. **References**
   - Point to actual config files
   - Link to internal docs
   - Reference example code

**Example Training Section:**

```markdown
## Round 2 Deep Training

**Training Status:** Completed on 2025-11-08
**Training Level:** Deep Domain Specialization

### Frontend Development Context

**Framework & Architecture:**
- React 18.2 with TypeScript 5.0
- Component pattern: Functional components with hooks
- State management: Zustand (global) + React Context (local)
- Styling: Tailwind CSS with custom design tokens in `tailwind.config.js`

**Project Conventions:**
- Component files: `ComponentName/index.tsx` + `ComponentName.test.tsx`
- Naming: PascalCase for components, camelCase for utilities
- Imports: Use path aliases (@components, @utils, @hooks)
- Props: Always define explicit TypeScript interfaces

**Key Files:**
- Design tokens: `src/styles/tokens.ts`
- Component library: `src/components/`
- Hooks: `src/hooks/`
- Utils: `src/utils/`

**Testing:**
- Framework: Jest + React Testing Library
- Coverage: Minimum 80%
- Test location: Co-located with components
- Mock API: Use MSW (Mock Service Worker)

**Integration Points:**
- Backend API: `/api/*` proxied to `http://localhost:3001`
- Auth: Auth0 with custom hook `useAuth()`
- Payments: Stripe Elements integrated in `CheckoutForm`

---
**Last Updated:** 2025-11-08
```

### Step 4: Inject Training into Agent

**Locate injection point** in agent file:

1. Look for `## Development Workflow` section
2. Insert training BEFORE that section
3. Or append to end if no suitable marker

**Update the agent file:**

```python
# Read agent file
agent_content = read_file(".claude/agents/frontend-developer.md")

# Generate training section (from Step 3)
training_section = """
## Round 2 Deep Training
[content from above]
"""

# Find injection point
if "## Development Workflow" in agent_content:
    parts = agent_content.split("## Development Workflow", 1)
    updated_content = parts[0] + training_section + "\n## Development Workflow" + parts[1]
else:
    # Append to end
    updated_content = agent_content + "\n\n" + training_section

# Write updated agent
write_file(".claude/agents/frontend-developer.md", updated_content)
```

### Step 5: Log Training Event

Log to audit trail:

```python
from audit_logger import AuditLogger

logger = AuditLogger('.')
logger.log(
    'agent_training_round2',
    'agent-manager',
    f'Trained frontend-developer with project patterns'
)
```

### Step 6: Notify Agent

Broadcast training completion:

```python
from communications.agent_sdk import AgentMessenger

messenger = AgentMessenger("agent-manager")
messenger.send(
    to="frontend-developer",
    message_type="training.complete",
    data={
        "round": 2,
        "training_areas": ["framework", "conventions", "testing", "integrations"],
        "message": "Deep specialization training completed. You now have project-specific knowledge."
    }
)
```

## Best Practices

### 1. Pattern Recognition

**Good:** "I see 15 components using Zustand store pattern in `src/store/`"
**Bad:** Assuming based on package.json alone

**Good:** "All API files use async/await with try-catch error handling"
**Bad:** Documenting general JavaScript knowledge

### 2. Specificity

**Good:** "Authentication: Auth0 with custom `useAuth()` hook in `src/hooks/useAuth.ts`"
**Bad:** "Use authentication"

**Good:** "Test coverage target: 80% (enforced in jest.config.js)"
**Bad:** "Write tests"

### 3. File References

**Always** include actual file paths:
- Config files: `tailwind.config.js`
- Example code: `src/components/Dashboard/index.tsx`
- Documentation: `.claude/docs/architecture.md`

### 4. Avoid Redundancy

**Don't** duplicate information the agent already knows:
- ❌ "React uses components" (generic knowledge)
- ✅ "Components in this project use compound pattern (see `src/components/Form/`)" (specific)

### 5. Context Over Instructions

**Focus on** what exists, not what to do:
- ✅ "State managed with Zustand, store defined in `src/store/appStore.ts`"
- ❌ "You should use Zustand for state management"

## Token Considerations

**Training Section Size:**
- Aim for 500-1000 tokens per agent
- More for specialized roles (database, architecture)
- Less for generic roles (code-reviewer)

**Break-Even Analysis:**
- Training cost: ~800 tokens once
- Savings per task: ~200 tokens (avoiding questions, using right patterns)
- Break-even: ~4 tasks
- Benefit: Increases over agent lifetime

## Common Patterns to Detect

### Frontend
- Framework and version
- State management approach
- Styling system
- Build tool configuration
- Component patterns
- Route structure

### Backend
- API framework
- Authentication method
- Database ORM
- Error handling pattern
- Logging approach
- Deployment process

### Testing
- Test framework
- Coverage thresholds
- Mock patterns
- Test data management
- CI/CD integration

### Database
- Database type and version
- Schema conventions
- Migration tool
- Query patterns
- Connection pooling

## Failure Cases

**If pattern detection fails:**
1. Fall back to asking user
2. Document what's unclear
3. Recommend creating project spec
4. Train with available information

**If agent already trained:**
1. Check if retraining needed (major changes?)
2. Update existing training section
3. Increment version number
4. Log update to audit trail

## Example Usage

```python
# As agent-manager, when Round 2 is triggered:

# 1. Analyze project
# Use Read, Glob, Grep tools to examine codebase

# 2. Detect patterns
# Understand frameworks, conventions, integrations

# 3. Generate training for each agent
# Create contextual, specific training sections

# 4. Inject into agent files
# Update .claude/agents/*.md files

# 5. Log and notify
# Audit trail + broadcast to agents
```

---

**Version:** 1.0
**Requires:** Read, Write, Edit, Glob, Grep tools
**Complements:** agent-specialization (Round 1), agent-recruitment
