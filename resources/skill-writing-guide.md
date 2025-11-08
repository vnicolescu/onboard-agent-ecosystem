# Agent Skill Writing Guide

## When Agents Should Write Skills

Agents write skills to capture reusable cognitive processes that:
1. **Repeat frequently** (≥3 times in project)
2. **Follow consistent patterns** (deterministic workflow)
3. **Reduce token usage** (skill loads on-demand vs re-explaining)
4. **Improve reliability** (scripts > generated code)

## Approval Workflow

### Phase 1: Recognition
Agent identifies reusable pattern:
```python
# Agent realizes: "I keep explaining how to validate
# form data in this project. This should be a skill."
```

### Phase 2: Proposal
Agent creates skill proposal in `.claude/skills/proposals/`:
```json
{
  "proposed_by": "frontend-dev-01",
  "skill_name": "form-validation",
  "purpose": "Validate form inputs against project schema",
  "frequency": "8 times in last week",
  "token_savings": "~500 tokens per use",
  "status": "pending_review"
}
```

### Phase 3: Human Approval
Human reviews proposal:
- Does it add value?
- Is scope appropriate?
- Should it be skill vs documentation?

If approved → Agent writes skill

### Phase 4: Skill Creation
Agent writes skill to `.claude/skills/pending/`:
- SKILL.md with instructions
- Optional scripts in `scripts/`
- Reference materials in `resources/`

### Phase 5: First Use Approval
Human reviews actual skill before first use:
- Quality check
- Security review
- Move to `.claude/skills/` to activate

### Phase 6: Usage & Iteration
- Agent uses skill
- Logs effectiveness
- Proposes improvements
- Human approves updates

## Skill Anatomy

### Minimal Skill (Procedural Knowledge)
```markdown
---
name: form-validation
description: Validate form inputs against project JSON schema. Use when handling form submissions or user input validation.
---

## Quick Start

Validate form data against schema:

```python
import jsonschema

schema = load_schema('schemas/user-form.json')
jsonschema.validate(instance=form_data, schema=schema)
```

## Error Handling

On validation failure:
1. Capture specific errors
2. Map to user-friendly messages
3. Return to frontend with field-level errors
```

### Enhanced Skill (With Scripts)
```
form-validation/
├── SKILL.md
├── scripts/
│   └── validate.py      # Reusable validation script
└── resources/
    ├── schemas/         # Project schemas
    └── error-messages.json  # Error message templates
```

## Good Skill Examples

### ✅ Example 1: API Request Pattern
```markdown
---
name: stripe-api-requests
description: Make authenticated requests to Stripe API with proper error handling and retry logic.
---

## Authentication

Use secret key from environment:
```python
import stripe
stripe.api_key = os.getenv('STRIPE_SECRET_KEY')
```

## Request Pattern

All requests use this pattern:
```python
try:
    result = stripe.Customer.create(...)
except stripe.error.CardError as e:
    # Handle declined card
except stripe.error.RateLimitError as e:
    # Retry after backoff
except stripe.error.InvalidRequestError as e:
    # Bad parameters
```

See [Stripe error handling](https://stripe.com/docs/error-handling)
```

**Why it's good:**
- Captures project-specific pattern
- Reduces repeated explanations
- Links to official docs
- Handles common errors

---

### ✅ Example 2: Database Query Optimization
```markdown
---
name: query-optimization
description: Optimize database queries following project patterns. Use when writing SQL queries or ORM calls.
---

## Query Checklist

Before running query:
- [ ] Indexes exist on WHERE columns
- [ ] LIMIT clause present
- [ ] No N+1 queries
- [ ] Eager loading configured

## Pattern: Batch Loading

Instead of:
```python
for user in users:
    user.orders  # N+1 query!
```

Do:
```python
users = User.objects.prefetch_related('orders').all()
```

## Monitoring

Check `scripts/query_analyzer.py` for slow queries.
```

---

## Bad Skill Examples

### ❌ Example 1: Too Generic
```markdown
---
name: python-programming
description: How to program in Python
---

Python is a programming language...
```

**Why it's bad:**
- Too broad, not project-specific
- Claude already knows Python
- No unique value added
- Wastes context window

---

### ❌ Example 2: Should Be Documentation
```markdown
---
name: project-setup
description: How to set up the project
---

1. Clone repo
2. Install dependencies
3. Run migrations
4. Start server
```

**Why it's bad:**
- One-time setup, not reusable
- Should be in README.md
- Not a cognitive process
- Skills ≠ documentation

---

### ❌ Example 3: Duplicates Project Spec
```markdown
---
name: requirements
description: Project requirements
---

The project must support:
- User authentication
- Payment processing
...
```

**Why it's bad:**
- Already in specs/requirements.md
- Agents should reference spec
- Redundancy causes sync issues
- No new value

---

## Skill Writing Best Practices

### 1. Progressive Disclosure
```markdown
# Quick Start (Level 2 - loaded when skill triggered)
Basic usage here

# Advanced Usage (Level 3 - in separate file)
See [ADVANCED.md](ADVANCED.md) for complex scenarios
```

### 2. Executable Scripts
```markdown
Run validation script:
```bash
python scripts/validate_form.py data.json schema.json
```

**Why scripts?**
- 0 tokens to execute (only output consumed)
- More reliable than generated code
- Testable and versioned
```

### 3. Context References
```markdown
**Schema Location:** `schemas/user-form.json`
**Error Messages:** `config/errors.yaml`
**Test Data:** `tests/fixtures/forms/`

(Agent reads files as needed)
```

### 4. Clear Triggers
```markdown
description: "Validate form inputs against project JSON schema. Use when handling form submissions, processing user input, or before database saves."
```

Multiple triggers = easier discovery

---

## Token Economics

### When Skill Saves Tokens:

**Repeated Task (Used 5x):**
- Without skill: 500 tokens × 5 = 2,500 tokens
- With skill: 100 (metadata) + 200 (SKILL.md) × 5 = 1,100 tokens
- **Savings: 1,400 tokens** ✅

**Infrequent Task (Used 1x):**
- Without skill: 500 tokens
- With skill: 100 + 200 = 300 tokens
- Overhead: -200 tokens ❌

**Break-even: ~2-3 uses**

### When to NOT Create Skill:

- Used only once
- Knowledge Claude already has
- Constantly changing procedure
- Better as documentation

---

## Skill Maintenance

### Update Triggers:
1. Pattern changes in project
2. Tool version upgrade
3. New edge case discovered
4. Error handling improvement

### Update Process:
1. Agent proposes change
2. Creates diff/patch
3. Explains rationale
4. Human approves
5. Skill updated

### Deprecation:
When skill no longer needed:
1. Move to `.claude/skills/deprecated/`
2. Add deprecation notice
3. Suggest alternative
4. Keep for 1 month
5. Delete if unused

---

## Testing Skills

### Before Approval:
```python
# 1. Syntax valid?
with open('SKILL.md') as f:
    validate_yaml_frontmatter(f.read())

# 2. References valid?
check_file_paths(['schemas/user-form.json'])

# 3. Scripts executable?
subprocess.run(['python', 'scripts/validate.py', '--help'])

# 4. No secrets?
assert 'sk_live_' not in skill_content
```

### During Usage:
- Log each skill invocation
- Track success/failure
- Measure token savings
- Collect improvement suggestions

---

## Common Mistakes

### Mistake 1: Skill Too Large
**Problem:** SKILL.md is 2,000 lines  
**Fix:** Split into multiple files with progressive disclosure

### Mistake 2: Hardcoded Values
**Problem:** API keys, URLs in skill  
**Fix:** Reference config files or environment variables

### Mistake 3: No Error Handling
**Problem:** Script fails silently  
**Fix:** Explicit error messages and recovery steps

### Mistake 4: Outdated Documentation
**Problem:** Skill references deprecated library  
**Fix:** Regular maintenance reviews

### Mistake 5: Missing Triggers
**Problem:** Skill never gets discovered  
**Fix:** Add specific trigger phrases in description

---

## Skill Metrics

Track effectiveness:
```json
{
  "skill": "form-validation",
  "created": "2025-11-01",
  "uses": 23,
  "success_rate": 0.96,
  "token_savings_estimate": 11500,
  "last_updated": "2025-11-07",
  "proposed_by": "frontend-dev-01",
  "maintenance_cost": "low"
}
```

Review monthly:
- Drop unused skills
- Improve low-success skills
- Promote high-value skills

---
**Version:** 1.0  
**Last Updated:** {timestamp}
