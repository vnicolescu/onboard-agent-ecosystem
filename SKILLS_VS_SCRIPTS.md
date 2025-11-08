# Skills vs Scripts - Design Philosophy

**Date:** 2025-11-08
**Purpose:** Clarify when to use skills (LLM) vs scripts (code)

---

## Core Principle

There are two fundamentally different types of computation:

### 1. Latent, Abstract Computation (LLM Territory)
- Pattern recognition across diverse inputs
- Contextual understanding and interpretation
- Content generation based on examples
- Decision-making with incomplete information
- Flexible reasoning about edge cases
- Semantic understanding
- Natural language processing

### 2. Deterministic, Sequential Computation (Script Territory)
- Database CRUD operations
- File I/O transformations
- Mathematical calculations
- Data structure manipulations
- API calls with fixed parameters
- Atomic state changes
- Predictable input/output mappings

---

## When to Use Skills

**Use LLM-powered skills when:**

✅ **Pattern Recognition**
- "Analyze this codebase and identify the state management pattern"
- "Detect coding conventions from example files"
- "Understand the API design philosophy"

✅ **Contextual Generation**
- "Generate agent training based on project patterns"
- "Create documentation from code examples"
- "Synthesize best practices from codebase"

✅ **Flexible Decision-Making**
- "Choose which agents to recruit based on project needs"
- "Determine appropriate specialization depth"
- "Decide when Round 2 training is needed"

✅ **Edge Case Handling**
- "Adapt to unusual project structures"
- "Handle incomplete or messy codebases"
- "Work with novel frameworks or patterns"

✅ **Semantic Understanding**
- "Interpret project requirements"
- "Understand agent role from description"
- "Map capabilities to needs"

---

## When to Use Scripts

**Use Python scripts when:**

✅ **Database Operations**
- INSERT, UPDATE, DELETE, SELECT with fixed schemas
- Transaction management
- Index creation
- Schema migrations

✅ **File Transformations**
- JSON parsing and serialization
- File copying, moving, renaming
- Format conversions (CSV → JSON, etc.)
- Archive creation

✅ **Atomic State Management**
- Message queue operations (claim, complete)
- Job board task state transitions
- Audit log appends
- Configuration updates

✅ **Mathematical Operations**
- Vote tallying (simple majority: count and compare)
- Metrics calculation
- Resource allocation arithmetic
- Token counting

✅ **API Interactions**
- HTTP requests with fixed parameters
- Webhook delivery
- External service calls
- Rate limiting enforcement

---

## Examples from This Project

### ❌ Wrong: Script Trying to Do LLM Work

**`train_agents_round2.py` (DEPRECATED)**

```python
def _detect_coding_standards(self):
    """Detect coding standards from config files."""
    standards = {}

    # ❌ This is pattern recognition, should be LLM
    if (self.project_root / ".eslintrc").exists():
        standards["linter"] = "ESLint"

    # ❌ Understanding conventions requires semantic analysis
    return standards

def _generate_training_section(self, agent_name: str, patterns: Dict):
    """Generate agent-specific training content."""

    # ❌ Content generation is LLM work
    if "frontend" in role:
        training += self._generate_frontend_training(patterns)
```

**Why it's wrong:**
- Uses brittle pattern matching (file existence checks)
- Hardcoded logic for understanding project structure
- Can't adapt to novel patterns
- Content generation with templates (inflexible)

### ✅ Right: Skill Using LLM

**`agent-training.md` (SKILL)**

```markdown
### Step 1: Analyze Project Patterns

**Read the codebase** to understand:

1. **Coding Standards**
   - Linter configs (.eslintrc, .prettierrc, pyproject.toml)
   - Code style consistency
   - Naming conventions
   - File organization patterns

# LLM examines files and understands patterns
# Not hardcoded checks, but flexible reasoning
```

**Why it's right:**
- LLM reads and interprets code
- Understands context and patterns
- Adapts to edge cases naturally
- Generates contextual content

### ✅ Right: Script for Deterministic Operations

**`communications/core.py`**

```python
def claim_message(self, agent_id: str, message_id: str) -> bool:
    """Atomically claim a message for processing."""
    with self._transaction(immediate=True) as conn:
        cursor = conn.cursor()

        # Deterministic: Check status, update if pending
        cursor.execute("""
            UPDATE messages
            SET status = 'processing',
                last_delivered_at = datetime('now'),
                delivery_count = delivery_count + 1
            WHERE id = ? AND status = 'pending'
        """, (message_id,))

        return cursor.rowcount == 1
```

**Why it's right:**
- Fixed schema and operations
- Atomic transaction (ACID required)
- No interpretation needed
- Predictable input/output

---

## Migration Examples

### Example 1: Agent Training

**Before (Script):**
```python
# train_agents_round2.py
def analyze_project_patterns(self):
    patterns = {
        "coding_standards": self._detect_coding_standards(),  # ❌
        "api_patterns": self._detect_api_patterns(),          # ❌
        "testing_patterns": self._detect_testing_patterns()   # ❌
    }
    return patterns
```

**After (Skill):**
```markdown
# agent-training.md
### Step 1: Analyze Project Patterns

Use your LLM capabilities to understand:

1. Read configuration files (.eslintrc, prettier, etc.)
2. Examine actual code to see patterns
3. Understand conventions from examples
4. Detect testing approaches from test files
5. Identify integration patterns from imports

Generate contextual, specific training based on what you discover.
```

### Example 2: Agent Recruitment

**Before (Script):**
```python
# recruit_agents.py
def determine_agents(self, project_context):
    agents = []

    # ❌ Hardcoded logic
    if project_context.get("frontend_files"):
        agents.append("frontend-developer")

    if "react" in str(project_context):
        agents.append("react-specialist")

    return agents
```

**After (Skill):**
```markdown
# agent-recruitment.md
### Step 2: Determine Agent Recommendations

Analyze the project and decide which agents are needed:

- Read file structure (use Glob)
- Understand technology stack
- Consider project complexity
- Think about phase (early vs mature)

Create ranked list:
- Essential: Always needed
- High priority: Based on stack
- Medium priority: Based on gaps
- Optional: Nice to have
```

### Example 3: Vote Tallying

**Correct (Script):**
```python
# communications/voting.py
def _tally_simple_majority(self, votes_cast: Dict, options: List[str]):
    """Tally using simple majority."""
    tally = {option: 0 for option in options}

    # ✅ Deterministic counting
    for vote in votes_cast.values():
        choice = vote["choice"]
        tally[choice] = tally.get(choice, 0) + 1

    # ✅ Mathematical comparison
    winner = max(tally, key=tally.get)

    return {"outcome": winner, "tally": tally}
```

**Why it stays a script:**
- Pure mathematics (counting, comparing)
- No interpretation needed
- Fixed algorithm
- Predictable behavior

---

## Decision Flowchart

```
Task needs computation
        ↓

Can it be done with fixed logic?
├─ YES → Use script
│   ├─ Database operation? → script
│   ├─ Math calculation? → script
│   ├─ File transformation? → script
│   └─ API call? → script
│
└─ NO → Requires understanding?
    ├─ Pattern recognition? → skill
    ├─ Content generation? → skill
    ├─ Contextual decision? → skill
    ├─ Semantic understanding? → skill
    └─ Flexible reasoning? → skill
```

---

## Current State

### Skills (LLM Territory)

✅ **Created:**
- `agent-training.md` - Deep agent specialization
- `agent-recruitment.md` - Team assembly
- `skill-writing-guide.md` - Skill creation (existing)

🔄 **To Create:**
- `agent-specialization.md` - Round 1 light touch
- `project-analysis.md` - Initial project understanding

### Scripts (Deterministic Territory)

✅ **Correct:**
- `communications/core.py` - Database operations
- `communications/voting.py` - Vote tallying (math)
- `create_job_board.py` - Job board CRUD
- `audit_logger.py` - Log file appends

🗑️ **Deprecated (were doing LLM work):**
- `train_agents_round2.py` → Replaced by skill
- `setup_communication.py` → Replaced by core.py

---

## Benefits of This Approach

### Token Efficiency
- Skills load on-demand (0 tokens until needed)
- Scripts execute server-side (0 tokens)
- LLM only invoked when reasoning required

### Flexibility
- Skills adapt to edge cases naturally
- No need to predict all scenarios
- Handles novel patterns automatically

### Maintainability
- Skills are declarative (what, not how)
- Scripts are testable (fixed behavior)
- Clear separation of concerns

### Reliability
- Scripts have predictable behavior
- Skills handle ambiguity gracefully
- Each does what it's good at

---

## Guidelines for Future Development

### Adding New Functionality

**Ask yourself:**

1. **Does this require understanding context?**
   - YES → Skill
   - NO → Script

2. **Can edge cases be enumerated?**
   - YES → Script
   - NO → Skill

3. **Is the output deterministic?**
   - YES → Script
   - NO → Skill

4. **Does it need to adapt to new patterns?**
   - YES → Skill
   - NO → Script

### Red Flags for Scripts

🚩 Multiple if-else chains trying to cover cases
🚩 Hardcoded pattern matching
🚩 Content generation with templates
🚩 Semantic analysis with regex
🚩 Comments saying "this might not work for..."

### Green Lights for Skills

✅ "Analyze and understand..."
✅ "Generate based on examples..."
✅ "Decide based on context..."
✅ "Interpret the meaning..."
✅ "Adapt to the pattern..."

---

## Conclusion

**Scripts** = Deterministic servants (database, files, math)
**Skills** = Intelligent assistants (understanding, reasoning, generation)

Use each for what it's naturally good at, and the system becomes more:
- **Flexible** - Adapts to edge cases
- **Efficient** - Minimal token usage
- **Maintainable** - Clear responsibilities
- **Reliable** - Each part does what it's designed for

---

**Version:** 1.0
**Last Updated:** 2025-11-08
