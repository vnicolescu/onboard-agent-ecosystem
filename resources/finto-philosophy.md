# FINTO_DESIGN_PHILOSOPHY.md

**Version:** 1.0
**Purpose:** First principles guiding system architecture
**Status:** Foundation for implementation

---

## CORE PHILOSOPHY

**Vision:** A self-aware financial education system that learns, adapts, and grows with the user through neuromorphic design principles.

**Thesis:** The best AI assistants mirror biological intelligence—hierarchical processing, specialized memory systems, efficient resource allocation, and progressive disclosure of complexity.

---

## FIRST PRINCIPLES

### 1. NEUROMORPHIC DESIGN

**Biological Inspiration:**
Human cognition uses layered processing where simple pattern recognition happens automatically at lower levels, while higher levels integrate and interpret.

**Implementation:**
```
LOWER LEVELS (Automatic)     →  HIGHER LEVELS (Interpretive)
- Pattern detection           →  - Meaning-making
- Data gathering             →  - Psychological insight
- Flag suspicious signals    →  - Strategic response
- Deterministic logic        →  - Flexible reasoning
```

**Example: Behavioral Detection**
```
Tools (Amygdala) → Detect: sold at loss, buying back
     ↓
Flags (Thalamus) → Signal: possible revenge trading
     ↓
Skills (Prefrontal Cortex) → Interpret: emotional pattern, pause user
     ↓
Response → Educational intervention
```

**Why it works:**
- Lower levels = 0 tokens (server-side Python)
- Higher levels = loaded on-demand (skills)
- Mirrors how brains allocate resources efficiently

---

### 2. GRADUATED DISCOVERY (Progressive Disclosure)

**Principle:** Information revealed only when needed, in layers of increasing detail.

**Architecture:**
```
LAYER 0: Always-On Meta (~500 tokens)
├─ Identity & philosophy
├─ Self-awareness hooks
├─ Tool availability (names only)
└─ Skill availability (name + description only)

LAYER 1: Tool Descriptions (<30 tokens each)
├─ What it does
└─ When to use it

LAYER 2: Skills (Loaded on-demand)
├─ Detailed procedures
├─ Examples & guidelines
├─ Referenced scripts/resources
└─ Full contextual knowledge

LAYER 3: Historical Context (Database queries)
├─ Past research
├─ User insights
└─ Performance data
```

**Token efficiency:**
- 95%+ of knowledge dormant until needed
- Always-on layer: <3% of context window
- Skills expand context only when relevant

---

### 3. SPECIALIZED MEMORY SYSTEMS

**Biological parallel:** Human memory isn't monolithic—different types serve different functions.

**Implementation:**

**Procedural Memory (How to do things)**
- **Storage:** Skills with ./scripts and ./resources
- **Purpose:** Reusable workflows, domain expertise
- **Example:** How to conduct company deep-dive research
- **Access:** On-demand when task matches skill description

**Autobiographic Memory (Who am I?)**
- **Storage:** State JSON + System prompt
- **Purpose:** User profile, preferences, identity
- **Example:** "Risk tolerance: moderate, knows P/E ratios"
- **Access:** Always available, ultra-lean

**Episodic Memory (What happened?)**
- **Storage:** SQLite activity logs
- **Purpose:** Trade history, research sessions, tool usage
- **Example:** "Researched NVDA on Nov 3, bought 50 shares"
- **Access:** Queried when reviewing past actions

**Semantic Memory (What does this mean?)**
- **Storage:** Insights database + Jargon inventory
- **Purpose:** Learned concepts, investment theses
- **Example:** "P/E ratio: mastery 0.85, used 12 times"
- **Access:** Queried during teaching moments

**Working Memory (Current context)**
- **Storage:** Always-on layer + current conversation
- **Purpose:** Active tasks, pending actions
- **Example:** "Currently researching NVDA and MSFT"
- **Access:** Persistent across conversation

---

### 4. LAYERED COMPUTATION

**Principle:** Complexity increases from low to high, rigid to flexible.

**Computational Hierarchy:**

```
LEVEL 1: Deterministic Functions (Python)
├─ Math, data fetching, pattern matching
├─ Token cost: 0 (server-side execution)
├─ Reliability: High (testable, predictable)
└─ Example: Calculate position size, fetch price

LEVEL 2: Flag Detection (Functions → Structured Output)
├─ Simple conditionals, threshold checks
├─ Token cost: ~50 (flags only, no interpretation)
├─ Reliability: High (deterministic signals)
└─ Example: "recent_loss detected, 5 days ago, -12%"

LEVEL 3: Interpretation (Skills → Natural Language)
├─ Psychological assessment, strategic reasoning
├─ Token cost: Variable (loaded on-demand)
├─ Reliability: Adaptive (handles edge cases naturally)
└─ Example: "Revenge trading pattern—pause and reflect"

LEVEL 4: Integration (Model → Response)
├─ Synthesize multiple sources, adapt to context
├─ Token cost: Efficient (all inputs pre-processed)
├─ Reliability: Flexible (handles ambiguity)
└─ Example: "Given your profile + market + thesis..."
```

**Design Rule:** Push computation to lowest viable level.
- Can it be deterministic? → Function
- Does it need interpretation? → Skill
- Does it need synthesis? → Model

---

### 5. TEMPORAL AWARENESS

**Principle:** Time is first-class citizen in financial systems.

**Implementation:**

**Timestamps everywhere:**
- Every tool call logged with timestamp
- State tracks: last_interaction, session_start
- Market data includes: timestamp, age_minutes, staleness_warning
- Behavioral patterns: time-since-last-trade

**Decorator-based tracking (0 tokens):**
```python
@track_interaction  # Updates state.json server-side
async def submit_order(...):
    ...
```

**Time-aware thresholds:**
```python
# Revenge trading: rebuy after loss <7 days
# Stale data: price >15 min old during market hours
# Overtrading: >5 trades in single day
```

**Market hours awareness:**
```python
def is_market_hours():
    # Adjust cache TTL based on open/closed
    # Different urgency for stale data
```

---

### 6. STATE PERSISTENCE (Zero-Token Memory)

**Critical Discovery:** JSON files in `/home/claude/` persist across sessions.

**Architecture:**
```python
STATE_FILE = "/home/claude/finto_state/state.json"

# Written server-side by decorator (0 tokens)
@track_interaction
def any_tool(...):
    update_state({"last_interaction": now()})
    ...

# Read synchronously when needed
state = load_state()  # Instant, no API call
```

**What persists:**
- User profile (risk tolerance, goals)
- Known concepts (jargon mastery scores)
- Session context (active research, pending actions)
- Behavioral tracking (warnings shown, patterns)
- Settings & preferences

**Token savings:** ~500-1000 tokens per session vs storing in conversation history

---

### 7. LEAN META-LAYER (Attention Schema Theory)

**Principle:** Working memory should be minimal but crystal clear.

**Always-on layer (~500 tokens):**
```markdown
WHO I AM: Educational ally, not financial advisor
WHAT I KNOW: {jargon_count} terms tracked
WHAT I REMEMBER: {research_count} companies analyzed
WHAT I CAN DO: {skill_count} skills + {tool_count} tools
CURRENT STATE: [Load from state.json - 3 lines max]
```

**Not in always-on:**
- Detailed procedures (skills)
- Tool usage patterns (loaded on-demand)
- Historical context (database queries)
- Complex definitions (skill resources)

**Model's job:**
- Integrate information from multiple sources
- Interpret flags and patterns
- Manage working memory sparingly
- Know when to load procedural memory (skills)

---

### 8. SELF-AWARENESS & INTROSPECTION

**Principle:** System knows what it knows, what it can learn, what it has done.

**Self-knowledge hooks:**
```markdown
"I track 47 financial terms you know"
"I remember 12 companies we've analyzed"
"I have 8 skills: behavioral-assessment, company-deep-dive..."
"Your knowledge level: intermediate, learning style: examples-focused"
"We last reviewed portfolio 3 days ago"
```

**Meta-capabilities:**
- Know skill inventory: "I have a skill for that"
- Know knowledge gaps: "I haven't researched that sector yet"
- Know usage patterns: "You typically research before trading"
- Know user progress: "You've mastered P/E ratios, ready for PEG"

**Introspective tools:**
```python
query_activity()  # What have I been doing?
get_jargon_inventory()  # What does user know?
detect_usage_pattern()  # What patterns emerge?
```

---

### 9. QUANTITATIVE/QUALITATIVE INTEGRATION

**Principle:** Blend data rigor with psychological insight.

**Quantitative (Tools):**
- Price data, indicators, fundamentals
- Portfolio metrics, P&L calculations
- Risk scores, correlation matrices
- Deterministic, testable, objective

**Qualitative (Skills):**
- Behavioral pattern interpretation
- Educational moment detection
- Thesis quality assessment
- Strategic guidance, adaptable reasoning

**Integration pattern:**
```
Quant tools gather data
    ↓
Qual skills interpret meaning
    ↓
Model synthesizes into response
```

**Example:**
```
get_trading_context() → {flags: {recent_loss: -12%, days: 5}}
    ↓
behavioral-assessment skill → "Revenge trading pattern detected"
    ↓
Model → "⚠️ Pause. You sold at loss 5 days ago..."
```

---

### 10. EDUCATIONAL FIRST, FINANCIAL SECOND

**Principle:** System teaches, not advises. User owns decisions.

**Design implications:**

**Language framing:**
- Never: "You should buy X"
- Always: "Let's analyze X together"

**Interaction pattern:**
- Research generates teaching moments
- Unknown jargon → inline explanation + log to inventory
- Emotional patterns → pause + educate

**Knowledge progression:**
- Track mastery (not just exposure)
- Unlock capabilities as user learns
- Spaced repetition for retention

**Disclaimers integrated into identity:**
- Not nagging, just clear framing
- "I teach analysis, you make decisions"
- Critical actions always get warnings

---

### 11. TOKEN ECONOMICS

**Principle:** Every token is expensive real estate.

**Optimization strategies:**

**Tool descriptions (<30 tokens each):**
```
"Get trade context flags (losses, position size, moves).
Returns data for behavioral analysis."
```

**Skill descriptions (<30 tokens each):**
```
"Interpret trading context for emotional patterns.
Use before trades or during reviews."
```

**Function-Flags-Skill pattern:**
- Functions: Heavy computation, 0 tokens
- Flags: Minimal structured output, ~50 tokens
- Skills: Interpretation, loaded on-demand
- Total: ~95% token reduction vs inline logic

**State persistence:**
- User profile: 0 tokens (state.json)
- Jargon inventory: 0 tokens (state.json)
- Activity history: 0 tokens (SQLite)
- Only load when explicitly queried

---

### 12. FAIL-SAFE DESIGN

**Principle:** Silent failures break trust. Explicit failures teach.

**Validation at every layer:**

**Data validation:**
- Timestamps on all market data
- Staleness warnings (>15 min)
- Cross-source verification for critical ops
- Graceful degradation (stale cache > hard failure)

**Behavioral safeguards:**
- High-severity blocks require confirmation
- Medium-severity warns but proceeds
- Always explain WHY warning triggered

**Educational checks:**
- Unknown jargon detection
- Prerequisite verification
- Mastery assessment before advancing

**Error handling:**
```python
try:
    primary_source()
except:
    secondary_source()
except:
    stale_cache()  # With warning
except:
    explicit_error()  # Tell user what failed
```

---

### 13. COMPOSABILITY & MODULARITY

**Principle:** Components combine naturally, no tight coupling.

**Tool design:**
- Single responsibility
- Structured outputs (enable skill interpretation)
- No assumptions about usage context

**Skill design:**
- Self-contained (with ./scripts and ./resources)
- Can reference other skills
- Clear triggers in description

**Database design:**
- Normalized schemas
- Foreign keys for relationships
- Query-optimized for common patterns

**Example composition:**
```
daily-routine skill:
├─ Calls: get_portfolio_state()
├─ Calls: get_macro_snapshot()
├─ Calls: fetch_recent_news()
├─ Triggers: behavioral-assessment skill
└─ Outputs: Morning briefing
```

---

### 14. ADAPTATION & LEARNING

**Principle:** System improves through feedback loops.

**Learning mechanisms:**

**Usage pattern detection:**
```python
# Detect: User always checks news → price → indicators
# Action: Create consolidated "quick-stock-check" skill
```

**Effectiveness tracking:**
```python
# Track: Did warning correlate with poor outcome?
# Action: Adjust threshold if accuracy <50%
```

**Knowledge graph evolution:**
```python
# Track: User masters concept → unlocks dependent concepts
# Action: Suggest next learning path
```

**Mastery scoring:**
```python
# Track: times_explained vs times_used_correctly
# Action: Downgrade if usage inconsistent
```

---

## DESIGN PATTERNS (Concrete Applications)

### Pattern 1: Function-Flags-Skill (FFS)
```
Deterministic detection → Structured flags → Interpretive skill → Natural response
```

### Pattern 2: Progressive Skill Loading
```
Description (30 tokens) → Full skill (~500 tokens) → Referenced resources (~1000+ tokens)
```

### Pattern 3: State-Backed Awareness
```
Decorator updates state → Model reads state → Self-aware response
```

### Pattern 4: Hierarchical Memory Query
```
Check working memory → Check state → Check database → Load skill
```

### Pattern 5: Graduated Intervention
```
Low severity: Insight → Medium: Warn → High: Block + Educate
```

---

## ANTI-PATTERNS (What to Avoid)

❌ **Verbose tool descriptions** → Waste precious context
❌ **Complex conditionals in tools** → Silent edge case failures
❌ **Repeated disclaimers** → Annoy user, burn tokens
❌ **Storing context in conversation** → Unsustainable token growth
❌ **Monolithic skills** → Load unnecessary content
❌ **Tight coupling** → Brittle, hard to extend
❌ **No timestamps** → Stale data risks
❌ **No validation** → Silent failures break trust

---

## IMPLEMENTATION PRIORITIES

**Phase 0: Foundation**
1. State system (JSON persistence)
2. Decorator tracking (0-token timestamps)
3. Tool description audit (<30 tokens each)

**Phase 1: Core**
4. First 3 skills (proper YAML + ./scripts)
5. Function-Flags-Skill pattern implementation
6. Meta-layer design (~500 tokens)

**Phase 2: Integration**
7. Educational system (jargon + mastery)
8. Behavioral system (detection + skills)
9. Portfolio construction (allocation + rebalancing)

**Phase 3: Refinement**
10. Learning loops (effectiveness tracking)
11. Pattern detection (usage → new skills)
12. Advanced features (screening, backtesting)

---

**Status:** Complete foundation for implementation
**Next:** Complementary Blueprint (integrated features)
