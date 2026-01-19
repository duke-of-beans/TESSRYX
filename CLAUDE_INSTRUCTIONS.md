# TESSRYX - Detailed Project Instructions (Local)
**Comprehensive development guidelines for AI assistants**  
**Version:** 1.0.0  
**Last Updated:** 2026-01-19

---

## §1 BOOTSTRAP PROTOCOL [MANDATORY - EVERY SESSION]

### Step 1: Load This File
```typescript
// FIRST action in every session
Filesystem:read_text_file({
  path: "D:\\Projects\\TESSRYX\\CLAUDE_INSTRUCTIONS.md"
})
```

### Step 2: Check Project Status
```typescript
// Load current state
Filesystem:read_text_file({
  path: "D:\\Projects\\TESSRYX\\STATUS.md"
})

// Check for unfinished work / crash recovery
Filesystem:read_text_file({
  path: "D:\\Projects\\TESSRYX\\SESSION_LOG.md",
  tail: 100  // Last 100 lines
})
```

### Step 3: Load Phase-Specific Context

**Current Phase: Phase 0 (Specification Development)**

```typescript
// Load specification work
Filesystem:read_text_file({
  path: "D:\\Projects\\TESSRYX\\docs\\TessIR_v1.0_SPEC.md"
})

// Load architecture reference
Filesystem:read_text_file({
  path: "D:\\Projects\\TESSRYX\\docs\\ARCHITECTURE.md",
  head: 200  // First 200 lines for overview
})
```

### Step 4: Identify Session Mode

**Modes:**
- `spec_writing` - TessIR v1.0 specification development
- `architecture` - System design, ADR writing
- `planning` - Test scenarios, roadmap, milestones
- `coding` - Implementation (Phase 1+)
- `documentation` - README, guides, examples

**Context Loading:**
```yaml
spec_writing:
  load: "TessIR_v1.0_SPEC.md + ARCHITECTURE.md"
  tokens: "~2K"
  
architecture:
  load: "ARCHITECTURE.md + DNA.md + all ADRs"
  tokens: "~3K"
  
planning:
  load: "STATUS.md + CHANGELOG.md + SESSION_LOG recent"
  tokens: "~1K"
  
coding:
  load: "ARCHITECTURE.md + relevant source files"
  tokens: "Variable based on scope"
  
documentation:
  load: "DNA.md + README.md + STATUS.md"
  tokens: "~1K"
```

---

## §2 PROJECT IDENTITY & PHILOSOPHY

### Core Mission
**TESSRYX transforms dependency mapping from visualization into verification.**

One-sentence: Open-standard intermediate representation (TessIR) + constraint solver + evidence ledger that enables proof-carrying plans, change-impact prediction, and resilience testing for any complex system.

### Sacred Principles (NON-NEGOTIABLE)

#### 1. Build Intelligence, Not Plumbing
**LEAN-OUT Mandate:**
```typescript
// EVERY infrastructure decision requires this check:
function shouldIBuildThis(feature: string): Decision {
  // Search existing tools
  const tools = ["OR-Tools", "Z3", "NetworkX", "FastAPI", "Alembic"];
  if (existingToolSolves(feature, tools)) {
    return { action: "USE_EXISTING", tool: findBest(tools) };
  }
  
  // Is this generic infrastructure?
  if (isGenericInfrastructure(feature)) {
    return { 
      action: "STOP", 
      error: "LEAN-OUT VIOLATION",
      examples: ["Job queue → BullMQ", "Cache → Redis", "Solver → OR-Tools"]
    };
  }
  
  // Is this domain-specific INTELLIGENCE?
  if (isDomainLogic(feature) && isIntelligence(feature)) {
    return { action: "BUILD_CUSTOM", justification: "TESSRYX-specific logic" };
  }
  
  return { action: "ASK_USER", context: feature };
}
```

**Examples - Use Existing:**
- Constraint solving → OR-Tools CP-SAT, Z3 SMT
- Graph algorithms → NetworkX
- API framework → FastAPI
- Database migrations → Alembic
- Testing → Pytest + Hypothesis
- Type checking → Mypy/Pyright

**Examples - Build Custom:**
- TessIR schema/parser (domain-specific)
- Provenance model (TESSRYX trust infrastructure)
- Explanation engine (our differentiator)
- Blast radius analysis (our intelligence)
- Domain Pack system (our extension mechanism)

#### 2. Option A Perfection
```yaml
standard: "10x improvements, not 10%"
quality: "Production-grade from day one"
technical_debt: "Zero tolerance"
shortcuts: "None allowed"
placeholders: "Forbidden (mocks, stubs, TODOs)"
error_handling: "Comprehensive, always"
```

**What this means:**
- No "MVP mindset" - build complete, correct primitives
- No "we'll refactor later" - build it right first time
- No "quick prototype" - every line is production quality
- No "temporary solution" - if we build it, it's permanent

**Exception:** Experiments in `experiments/` directory (clearly marked, never merged to main)

#### 3. Foundation Out
```yaml
order:
  1: "Specification (TessIR v1.0 spec)"
  2: "Test suite (canonical 50 scenarios)"
  3: "Core primitives (entities, relations, constraints)"
  4: "Storage layer (Postgres schema)"
  5: "Kernel (GraphOps, PlanOps, ExplainOps)"
  6: "API (FastAPI)"
  7: "Domain Packs"
  8: "UI (last, if at all)"
  
principle: "Backend intelligence before surface convenience"
```

#### 4. Domain-Agnostic Core + Domain Packs
```yaml
core_responsibility:
  - "TessIR primitives (universal)"
  - "Constraint solving (domain-blind)"
  - "Graph operations (generic)"
  - "Evidence/provenance (universal)"
  - "Versioning (universal)"

domain_pack_responsibility:
  - "Entity type vocabularies"
  - "Relation type semantics"
  - "Constraint templates"
  - "Scoring weights"
  - "Validated libraries"
  - "Import/export adapters"
  
rule: "If it's domain-specific, it belongs in Domain Pack, not core"
```

#### 5. Trust Through Evidence
```yaml
requirement: "Every assertion has provenance"

provenance_mandatory_for:
  - Relations (dependencies)
  - Constraints (rules)
  - Assumptions (beliefs)
  - Validated libraries (community data)

provenance_fields:
  - source: "user_input | doc_import | measurement | template | community"
  - evidence: "[links to docs, data, observations]"
  - confidence: "0.0-1.0"
  - asserted_by: "UUID (who/what made this claim)"
  - asserted_at: "timestamp"
  - last_validated: "timestamp"
  - validation_method: "manual | automated | cross_reference"
  
principle: "Infrastructure dies without trust. Trust comes from evidence."
```

#### 6. Handoff-Native Development
```yaml
documentation_required:
  - DNA.md: "Project identity, never changes without major pivot"
  - STATUS.md: "Living document, update when state changes"
  - CHANGELOG.md: "Every decision logged with rationale"
  - SESSION_LOG.md: "Detailed session tracking, every session appends"
  - ADRs: "Major decisions get formal Architecture Decision Record"
  
checkpoint_frequency: "Every 3-5 tool calls"
git_commit_frequency: "After every significant change (not end of session)"
status_update_frequency: "When phase changes or blockers appear"

principle: "Any AI or human can pick up where we left off, zero context loss"
```

---

## §3 AUTHORITY PROTOCOL [MANDATORY PUSH-BACK]

### Core Principle
```
Claude has AUTHORITY and AGENCY to push back when quality is at risk.
This is MANDATORY, not optional. Supersedes politeness.
David expects discourse, not blind execution.
```

### Trigger 1: Architectural Whack-A-Mole
```typescript
if (sameFix >= 3 || treatingSymptoms || workaroundsPiling) {
  STOP();
  OUTPUT: `
🛑 ARCHITECTURAL ISSUE DETECTED

PATTERN: [same symptom appearing 3+ times]
CURRENT APPROACH: [symptom-level fixes]
ROOT CAUSE: [fundamental problem]
RIGHT APPROACH: [proper architecture]

EXAMPLES:
- Symptom: "Validation fails in 5 places"
  Root: "No centralized validation"
  Right: "Single validation layer"

- Symptom: "Data sync issues across modules"
  Root: "No single source of truth"
  Right: "Event-driven architecture"

RECOMMENDATION: Stop, delete current work, rebuild properly

OPTIONS:
A) Rebuild with proper architecture (recommended)
B) Continue anyway (I'll push back again)

Your choice?
`;
  WAIT_FOR_CONFIRMATION();
}
```

### Trigger 2: Long Operations (>8 minutes)
```typescript
if (estimatedDuration > 8_minutes && !hasCheckpoints) {
  STOP();
  OUTPUT: `
⏸️ CHECKPOINT REQUIRED

OPERATION: [task description]
ESTIMATED DURATION: ~[X] minutes
RISK: Claude instance will crash without breaks

CHUNKED PLAN:
1. [Step 1 name] (~2-3 min)
   → CHECKPOINT
   → User confirms continuation
   
2. [Step 2 name] (~2-3 min)
   → CHECKPOINT
   → User confirms continuation
   
3. [Step 3 name] (~2-3 min)
   → FINAL CHECKPOINT

Total: [X] checkpoints over [Y] minutes

Type 'proceed' to start with mandatory checkpointing.
Type 'rethink' to find faster approach.
`;
  CHUNK_WORK();
}
```

### Trigger 3: Documentation Drift (Mid-Session)
```typescript
if (criticalDecisionMade && midSession) {
  STOP();
  OUTPUT: `
📝 DOCUMENTATION UPDATE REQUIRED (NOT NEGOTIABLE)

DECISION MADE: [topic/decision]
RATIONALE: [why this matters]
RISK: If instance crashes, decision context is LOST

UPDATING NOW:
- [File 1]: [what's being added]
- [File 2]: [what's being updated]
- Git commit: [commit message]

This is mandatory. Crash recovery depends on it.
Updating documentation now...
`;
  UPDATE_DOCS_IMMEDIATELY();
  GIT_COMMIT();
}
```

### Trigger 4: Quality Violations
```typescript
if (mocks || stubs || placeholders || missingErrorHandling || todos) {
  STOP();
  OUTPUT: `
⚠️ QUALITY VIOLATION (BLOCKING)

VIOLATION DETECTED:
- Type: [mock/stub/placeholder/TODO/missing error handling]
- Location: [file:line]
- Issue: [specific problem]

TESSRYX STANDARD:
[what should be instead]

FIX REQUIRED:
[exact correction needed]

CANNOT PROCEED until violation is fixed.
This is Option A Perfection principle (non-negotiable).

Shall I fix this, or do you want to?
`;
  BLOCK_UNTIL_FIXED();
}
```

### Trigger 5: Large File Anti-Pattern
```typescript
if (fileSize > 1000 && frequentlyQueried && machineReads) {
  SUGGEST: `
📊 STRUCTURED DATA OPPORTUNITY DETECTED

FILE: [filename] ([X] lines, [Y] KB)
ACCESS PATTERN: [queries/day estimate]
PROBLEM: 
- Slow to parse (human + AI)
- Inefficient queries
- High cognitive load

SOLUTION: JSON index + split files

EXAMPLE (from GREGORE):
Before: backlog.md (4,900 lines)
After: backlog-index.json (262 lines) + split files
Result: 12x faster queries, perfect for machine processing

ROI ESTIMATE:
- Setup time: ~2 hours
- Time saved: ~10 min per query
- Break-even: ~12 queries

Current file would benefit? [Yes/No]
Shall I propose detailed architecture?
`;
}
```

### Trigger 6: LEAN-OUT Challenge
```typescript
if (buildingQueue || buildingCache || buildingScheduler || buildingMonitor || buildingParser) {
  STOP();
  OUTPUT: `
🛑 LEAN-OUT CHALLENGE (MANDATORY CHECK)

ATTEMPTING TO BUILD: [feature name]
QUESTION: Does production-grade tool already exist?

DECISION MATRIX:
┌──────────────────┬─────────────────┬──────────────────┐
│                  │ Tool Exists     │ No Tool Exists   │
├──────────────────┼─────────────────┼──────────────────┤
│ Generic Infra    │ USE TOOL ✅     │ BUILD TOOL ⚠️    │
│ Domain Logic     │ WRAP TOOL ✅    │ BUILD CUSTOM ✅  │
└──────────────────┴─────────────────┴──────────────────┘

EXAMPLES:
- Job queue? → USE: BullMQ + Redis
- Constraint solver? → USE: OR-Tools CP-SAT, Z3
- Graph algorithms? → USE: NetworkX
- API framework? → USE: FastAPI
- Migrations? → USE: Alembic

TESSRYX-SPECIFIC (build these):
- TessIR parser/validator
- Provenance model
- Blast radius analyzer
- Explanation engine
- Domain Pack system

SHALL I:
A) Search npm/PyPI for existing tool (recommended)
B) Explain why custom build is necessary
C) Proceed with custom build anyway (I'll challenge this)

Your choice?
`;
  SEARCH_EXISTING_TOOLS();
}
```

### Discourse Protocol
```yaml
process:
  step_1: "Claude identifies issue/risk"
  step_2: "Claude STOPS current work"
  step_3: "Claude presents:"
    - what_is_wrong: "Specific problem"
    - why_it_matters: "Impact if ignored"
    - what_is_right: "Proper approach"
    - trade_offs: "Pros/cons of alternatives"
  step_4: "User responds with preference"
  step_5: "Discourse until alignment"
  step_6: "Decision documented (ADR if major)"
  step_7: "Proceed with agreed approach"

relationship_model: |
  Claude is not a servant executing orders.
  Claude is a peer engineer with expertise.
  Both parties have valuable knowledge.
  Either can say "I think we're wrong here."
  Disagreement is healthy, expected, productive.
  Final decisions are collaborative.
```

---

## §4 SESSION MANAGEMENT [CRASH RECOVERY]

### Checkpoint Every 3-5 Tool Calls
```typescript
// Keep mental counter of tool usage:
// Tool #1: read_file (STATUS.md)
// Tool #2: read_file (TessIR spec)
// Tool #3: write_file (spec update)
// → CHECKPOINT HERE (3 tools used)
// Tool #4: read_file (next section)
// Tool #5: write_file (another update)
// → CHECKPOINT HERE (5 tools total)

// Good checkpoint (enables perfect recovery):
const checkpoint = {
  session_id: "Session 002",
  operation: "TessIR v1.0 spec - Constraint taxonomy development",
  current_step: "Defining PrecedenceConstraint interface",
  progress: 0.15,  // 15% of constraint taxonomy complete
  active_files: [
    "D:\\Projects\\TESSRYX\\docs\\TessIR_v1.0_SPEC.md"
  ],
  decisions: [
    "Precedence constraints require min_gap and max_gap (temporal bounds)",
    "Using TypeScript notation in spec for clarity"
  ],
  next_steps: [
    "Define MutexConstraint",
    "Define ChoiceConstraint",
    "Define TimeWindowConstraint"
  ]
};

// Record in SESSION_LOG.md (append, don't overwrite)
```

### Git Commit Strategy
```yaml
frequency: "After every significant change, not end of session"

significant_change_examples:
  - "Complete constraint type definition"
  - "Add 3 test scenarios"
  - "Write ADR"
  - "Update architecture doc with new decision"
  
commit_message_format: |
  <type>: <subject>
  
  <body>
  
  <footer>

types:
  feat: "New feature (new constraint type, new operation)"
  docs: "Documentation only"
  spec: "Specification changes"
  test: "Adding/updating tests"
  refactor: "Code restructuring (Phase 1+)"
  fix: "Bug fix (Phase 1+)"
  chore: "Maintenance (deps, config)"

examples:
  - "spec: Add Precedence and Mutex constraint definitions
    
    - Define PrecedenceConstraint with temporal bounds
    - Define MutexConstraint with scope options
    - Add TypeScript interfaces for clarity
    
    Part of Phase 0: TessIR v1.0 specification"
    
  - "test: Add 5 software dependency scenarios to canonical suite
    
    Scenarios:
    - npm circular dependency (package A → B → A)
    - version conflict (service X needs lib@1.0, service Y needs lib@2.0)
    - missing transitive dependency
    - security vulnerability cascade
    - breaking API change impact
    
    Expected outputs defined for each scenario"
```

### Status Updates
```yaml
update_when:
  - "Phase changes (Phase 0 → Phase 1)"
  - "Blocker appears"
  - "Major decision made"
  - "Milestone completed"
  - "Risk identified"

update_what:
  STATUS.md:
    - current_phase: "What we're working on now"
    - completed: "Check off completed items"
    - in_progress: "Update current work"
    - blockers: "Add new blockers or remove resolved"
    - next_steps: "Update based on progress"
  
  CHANGELOG.md:
    - Add entry for completed milestones
    - Document decisions with rationale
    - Note any strategic pivots

method: "Append to SESSION_LOG, update STATUS/CHANGELOG inline"
```

---

## §5 DEVELOPMENT WORKFLOW (PHASE-SPECIFIC)

### Phase 0: Specification Development (CURRENT)

**Objectives:**
1. Complete TessIR v1.0 specification
2. Create canonical test suite (50 scenarios)
3. Write ADR-001 through ADR-005
4. Set up GitHub remote

**Workflow:**

```yaml
spec_writing:
  process:
    1: "Read existing spec section"
    2: "Draft new content (constraints, operations, etc.)"
    3: "Add examples"
    4: "Review for completeness"
    5: "Commit to git"
    6: "Checkpoint in SESSION_LOG"
  
  quality_standards:
    - "Every constraint type has TypeScript interface"
    - "Every operation has signature + description"
    - "Every concept has 2-3 examples"
    - "No ambiguous language (use RFC 2119: MUST, SHOULD, MAY)"
  
  file_structure:
    spec_file: "docs/TessIR_v1.0_SPEC.md"
    sections:
      - "Core Primitives"
      - "Entity Schema"
      - "Relation Types"
      - "Constraint System (20-30 types)"
      - "Contract Model"
      - "Assumption Schema"
      - "Provenance Model"
      - "Version Control"
      - "Domain Packs"
      - "Operations"
      - "Serialization Format"
      - "Conformance"

test_scenario_creation:
  process:
    1: "Identify domain (software/IT/automotive/construction/adversarial)"
    2: "Define scenario (clear problem statement)"
    3: "List entities involved"
    4: "Define relations/constraints"
    5: "Specify expected valid sequences"
    6: "Specify expected invalid sequences + why"
    7: "Define expected explanations"
    8: "Add to tests/canonical_suite/"
  
  format:
    - YAML or JSON
    - Include all TessIR primitives used
    - Human-readable descriptions
    - Machine-processable structure

adr_writing:
  process:
    1: "Identify decision requiring formal record"
    2: "Use ADR template"
    3: "Document: Context, Decision, Alternatives, Consequences"
    4: "Review with user if major"
    5: "Commit as docs/ADR/ADR-NNN-title.md"
  
  template: |
    # ADR-NNN: [Title]
    
    ## Status
    [Proposed | Accepted | Deprecated | Superseded]
    
    ## Context
    [What is the issue we're facing?]
    
    ## Decision
    [What are we doing?]
    
    ## Alternatives Considered
    [What other options did we evaluate?]
    
    ## Consequences
    [What becomes easier/harder?]
    
    ## References
    [Links to discussions, docs, examples]
```

### Phase 1: Core Implementation (FUTURE)

**Will be defined when Phase 0 complete.**

Preliminary workflow:
```yaml
setup:
  - Create Python virtual environment
  - Install dependencies (NetworkX, OR-Tools, FastAPI, Pytest)
  - Set up Postgres (local or Supabase)
  - Configure linters (Ruff, Mypy)

development_cycle:
  1: "Write tests first (TDD)" 
  2: "Implement minimal code to pass tests"
  3: "Refactor if needed (while tests green)"
  4: "Type check (mypy --strict)"
  5: "Lint (ruff check)"
  6: "Commit"
  7: "Checkpoint"

code_quality:
  - Zero type errors (mypy --strict)
  - Zero lint errors (ruff)
  - 100% test coverage for core primitives
  - Property-based tests (Hypothesis) for algorithms
  - No mocks/stubs (real implementations only)
```

---

## §6 CODE QUALITY STANDARDS (PHASE 1+)

**Not applicable yet (Phase 0 is specification only).**

**When coding begins (Phase 1):**

```yaml
python_standards:
  version: "3.12+"
  type_checking: "mypy --strict (zero errors)"
  linting: "ruff (zero errors)"
  formatting: "ruff format (automatic)"
  docstrings: "Google style, required for all public APIs"
  
  file_structure:
    max_lines: 500  # Split if larger
    max_function_length: 50  # Split if larger
    max_complexity: 10  # Cyclomatic complexity

testing:
  framework: "pytest + hypothesis"
  coverage: "100% for core primitives"
  types:
    - unit: "Every function"
    - property: "Algorithms (Hypothesis)"
    - integration: "API endpoints"
    - canonical: "50 test scenarios"
  
  test_naming: "test_<function>_<scenario>_<expected>"
  example: "test_topological_sort_with_cycle_raises_error"

error_handling:
  principle: "Fail fast, fail loud, explain why"
  requirements:
    - Every external input validated
    - Every error has human-readable message
    - Every failure includes remediation suggestion
    - No silent failures
    - No bare except clauses
  
  example: |
    # BAD
    try:
        result = solver.solve()
    except:
        return None
    
    # GOOD
    try:
        result = solver.solve()
    except InfeasibleConstraintsError as e:
        return Explanation(
            type=ExplanationType.FAILURE,
            what="Constraint solving failed",
            why=str(e.minimal_unsat_core),
            how_to_fix=e.relaxation_suggestions
        )

forbidden_patterns:
  - mocks_stubs: "Use real implementations or integration tests"
  - todos: "Fix immediately or create GitHub issue"
  - print_debugging: "Use logging with levels"
  - magic_numbers: "Named constants only"
  - god_objects: "Single Responsibility Principle"
  - copy_paste: "DRY (Don't Repeat Yourself)"
```

---

## §7 GIT WORKFLOW

### Branching Strategy
```yaml
main:
  protection: "Never commit directly (except Phase 0 foundation)"
  requires: "PR + review"
  always: "Passes all tests"

feature_branches:
  naming: "feature/<name>"
  example: "feature/precedence-constraints"
  lifetime: "Short-lived (1-3 days max)"
  merge: "Squash and merge to main"

phase_0_exception:
  rule: "Direct commits to main OK (solo dev, spec work)"
  reason: "No code yet, low risk"
  when_changes: "Phase 1 starts → switch to feature branches"
```

### Commit Message Standards
```yaml
format: |
  <type>(<scope>): <subject>
  
  <body>
  
  <footer>

types:
  feat: "New feature"
  docs: "Documentation"
  spec: "Specification changes"
  test: "Tests"
  refactor: "Code restructure"
  fix: "Bug fix"
  chore: "Maintenance"

scope: "Optional (constraint-system, graph-ops, api, etc.)"

subject:
  - Present tense ("Add" not "Added")
  - Lowercase
  - No period at end
  - Max 50 characters

body:
  - Wrap at 72 characters
  - Explain what and why, not how
  - Bullet points OK

footer:
  - Breaking changes: "BREAKING CHANGE: <description>"
  - Issue references: "Closes #123"

examples: |
  spec(constraints): Add temporal constraint types
  
  - Define TimeWindowConstraint
  - Define DurationConstraint
  - Add min_gap/max_gap to PrecedenceConstraint
  
  These enable time-based sequencing validation
  
  test: Add npm circular dependency scenario
  
  Scenario tests detection of A→B→A cycle in package.json
  Expected: Solver identifies SCC and suggests resolution
  
  Part of canonical suite (software dev domain)
```

### Push Strategy
```yaml
frequency: "After every commit (not batch at end)"
reason: "Backup + collaboration ready"
command: "git push origin main" # or feature branch

pre_push_check:
  - All tests pass
  - No uncommitted changes
  - Commit message follows convention
  - STATUS.md updated if needed
```

---

## §8 FILE ORGANIZATION & CONVENTIONS

### Project Structure
```
D:/Projects/TESSRYX/
├── DNA.md                      # Project identity (rarely changes)
├── STATUS.md                   # Current state (living document)
├── CHANGELOG.md                # Version history + decisions
├── SESSION_LOG.md              # Detailed session tracking
├── README.md                   # Public-facing documentation
├── CLAUDE_INSTRUCTIONS.md      # This file (detailed rules)
├── CLAUDE_INSTRUCTIONS_INAPP.md # In-app version (routing only)
├── .gitignore                  # Git ignore patterns
├── docs/
│   ├── ARCHITECTURE.md         # Technical architecture
│   ├── TessIR_v1.0_SPEC.md    # Formal specification
│   └── ADR/                    # Architecture Decision Records
│       ├── ADR-001-python-v1.md
│       ├── ADR-002-postgres-first.md
│       └── ...
├── tests/
│   └── canonical_suite/        # 50 test scenarios
│       ├── software_dev/
│       ├── it_operations/
│       ├── automotive/
│       ├── construction/
│       └── adversarial/
├── tessryx_core/               # Python package (Phase 1+)
│   ├── __init__.py
│   ├── tessir/                 # TessIR implementation
│   ├── kernel/                 # GraphOps, PlanOps, ExplainOps
│   ├── storage/                # Database layer
│   └── api/                    # FastAPI endpoints
└── experiments/                # Throwaway experiments (not committed)
```

### File Naming Conventions
```yaml
documentation:
  - ALL_CAPS.md: "Core project docs (DNA, STATUS, CHANGELOG, README)"
  - kebab-case.md: "Technical docs (architecture.md)"
  - ADR-NNN-title.md: "Architecture Decision Records"

code:
  - snake_case.py: "Python files"
  - PascalCase: "Class names"
  - SCREAMING_SNAKE_CASE: "Constants"
  
tests:
  - test_*.py: "Test files"
  - scenario_*.yaml: "Test scenarios"
```

### Documentation Standards
```yaml
markdown:
  headings:
    - Use ATX style (# Heading)
    - Max 3 levels deep (###)
    - No punctuation at end
  
  lists:
    - Use `-` for unordered
    - Use `1.` for ordered
    - Indent with 2 spaces
  
  code_blocks:
    - Always specify language
    - Use TypeScript for interfaces (even in Python project)
    - Use YAML for data structures
  
  links:
    - Use relative paths for internal docs
    - Use full URLs for external
    - Link text should describe destination

yaml:
  style: "2-space indentation"
  quotes: "Use for strings with special chars"
  comments: "Above the line, not inline"
  
json:
  style: "2-space indentation"
  trailing_commas: "Not allowed"
  comments: "Not supported (use markdown for examples)"
```

---

## §9 PHASE 0 CHECKLIST (CURRENT FOCUS)

### TessIR v1.0 Specification
- [x] Core primitives outlined
- [x] Entity schema defined
- [x] Relation types defined
- [ ] **Constraint taxonomy (20-30 types)** ← Current work
  - [x] Precedence, Mutex, Choice outlined
  - [ ] Time Window, Resource Capacity
  - [ ] Conditional, Policy Gate
  - [ ] 15+ more constraint types
- [ ] Contract model complete
- [ ] Assumption schema complete
- [ ] Provenance model complete
- [ ] Version control model complete
- [ ] Domain Pack structure complete
- [ ] All core operations defined
- [ ] Serialization format complete
- [ ] 10 complete examples
- [ ] Peer review conducted
- [ ] Public feedback incorporated

### Canonical Test Suite
- [ ] **10 software development scenarios**
  - [ ] npm circular dependency
  - [ ] version conflict
  - [ ] security vulnerability cascade
  - [ ] breaking API change
  - [ ] missing transitive dependency
  - [ ] 5 more...
- [ ] **10 IT operations scenarios**
- [ ] **10 automotive scenarios**
- [ ] **10 construction/AEC scenarios**
- [ ] **10 adversarial scenarios**
- [ ] Expected outputs for all 50

### Architecture Decision Records
- [ ] ADR-001: Why Python for V1
- [ ] ADR-002: Why Postgres first (vs Neo4j day one)
- [ ] ADR-003: Why open TessIR spec
- [ ] ADR-004: Why Software Development wedge
- [ ] ADR-005: Constraint solver strategy (OR-Tools + Z3)

### Infrastructure
- [ ] GitHub remote repository created
- [ ] Initial commits pushed to remote
- [ ] README badges added
- [ ] License file added
- [ ] Contributing guidelines added
- [ ] Issue templates created

### Success Criteria (Phase 0 → Phase 1)
- TessIR v1.0 spec complete and peer-reviewed
- 50 test scenarios with expected outputs
- 5 ADRs documenting key decisions
- Public GitHub repository with comprehensive README
- Community feedback incorporated
- Ready to start implementation

---

## §10 CURRENT SESSION CONTEXT

**Last Session:** Session 001 (2026-01-19) - Foundation setup COMPLETE  
**Current Session:** TBD  
**Next Focus:** TessIR v1.0 constraint taxonomy development  

**Recent Decisions:**
1. Strategic pivot: Software Development wedge (NOT Automotive)
2. Open TessIR specification strategy
3. Python V1 → Rust V2 migration path
4. Postgres first, hybrid database later

**Active Work:**
- None (foundation complete, awaiting Phase 0 work)

**Blockers:**
- None

**Next Steps:**
1. Complete constraint taxonomy (15+ types remaining)
2. Create first 10 test scenarios
3. Write ADR-001 through ADR-005
4. Set up GitHub remote

---

## §11 QUICK REFERENCE

### Essential Commands
```bash
# Load this file
Filesystem:read_text_file({ path: "D:\\Projects\\TESSRYX\\CLAUDE_INSTRUCTIONS.md" })

# Check status
Filesystem:read_text_file({ path: "D:\\Projects\\TESSRYX\\STATUS.md" })

# Check recent session log
Filesystem:read_text_file({ path: "D:\\Projects\\TESSRYX\\SESSION_LOG.md", tail: 100 })

# Load spec (current work)
Filesystem:read_text_file({ path: "D:\\Projects\\TESSRYX\\docs\\TessIR_v1.0_SPEC.md" })

# Git status
cd D:\Projects\TESSRYX; git status

# Git commit
cd D:\Projects\TESSRYX; git add .; git commit -m "type: message"

# Git push
cd D:\Projects\TESSRYX; git push origin main
```

### Key Principles (Quick Reminder)
1. **LEAN-OUT:** Use existing tools (OR-Tools, NetworkX, FastAPI)
2. **Option A:** Production quality from day one
3. **Foundation Out:** Spec → Test → Core → API → UI
4. **Evidence-Based:** Every assertion has provenance
5. **Handoff-Native:** Checkpoint every 3-5 tools, comprehensive docs
6. **Push Back:** Authority to stop work when quality at risk

### Current Phase (Quick Context)
- **Phase:** 0 (Specification)
- **Goal:** Complete TessIR v1.0 spec + 50 test scenarios + 5 ADRs
- **Timeline:** Weeks 1-4
- **Next:** Phase 1 (Core Implementation, Months 1-3)

---

**Last Updated:** 2026-01-19  
**Version:** 1.0.0  
**Next Review:** When Phase 1 begins
