# Impact-Aware Documentation Sync Protocol
**Version:** 1.0.0  
**Status:** Active  
**Source:** Adapted from Gregore (S12 - Four-Pillar System)

---

## Principle

**Sync What Changed, Not Everything**

Every checkpoint should update only the documents affected by recent decisions. This is token-efficient, accurate, and scales to any documentation structure.

---

## Four-Pillar Documentation System

TESSRYX uses four core documents that must stay synchronized:

1. **DNA.md** - Project identity, rarely changes
2. **STATUS.md** - Current state, updated frequently
3. **ARCHITECTURE.md** - Technical design, updated on architectural decisions
4. **ROADMAP.md** - Timeline, updated when milestones shift

Plus supporting documents:
- CHANGELOG.md - Version history
- SESSION_LOG.md - Session tracking
- STEAL_REGISTRY.md - Leverage tracking
- ADRs - Major decisions

---

## The Protocol

### Step 1: Decision Identification (Mental Task)

After every 3-5 tool calls, Claude asks:
> "What decisions did I make since the last checkpoint?"

Track decisions like:
- "Changed constraint type design (added TimeWindow)"
- "Completed 5 test scenarios"
- "Decided to use Python dataclasses instead of Pydantic for core"
- "Moved solver integration from Phase 1 to Phase 2"

### Step 2: Impact Detection (Mental Task - Lightweight)

For each decision, identify affected documents:

```yaml
decision: "Changed Engine B to use SQLite instead of JSON"
affects:
  - "docs/ARCHITECTURE.md"      # Storage layer section
  - "STATUS.md"                  # Update current progress
  
not_affected:
  - "ROADMAP.md"                 # No timeline change
  - "DNA.md"                     # Principles unchanged
```

**Decision Categories → Likely Affected Docs:**

| Decision Type | Always Update | Maybe Update | Rarely Update |
|---------------|---------------|--------------|---------------|
| Architecture change | ARCHITECTURE.md | STATUS.md, ADR | ROADMAP.md, DNA.md |
| New EPIC/task | STATUS.md | ROADMAP.md | ARCHITECTURE.md |
| EPIC completed | STATUS.md | ROADMAP.md | CHANGELOG.md |
| Phase change | DNA.md, STATUS.md, ROADMAP.md | ARCHITECTURE.md | - |
| UI/UX decision | ARCHITECTURE.md | STATUS.md | - |
| Process change | CLAUDE_INSTRUCTIONS.md | DNA.md | - |
| Principle change | DNA.md | ARCHITECTURE.md | CLAUDE_INSTRUCTIONS.md |

### Step 3: Targeted Updates (Desktop Commander)

Update ONLY affected documents using `Desktop Commander:edit_block`:

```typescript
// Example: Completed constraint taxonomy
// Affects: STATUS.md, ROADMAP.md

Desktop Commander:edit_block({
  file_path: "D:\\Projects\\TESSRYX\\STATUS.md",
  old_string: "- [ ] **Constraint taxonomy (20-30 types)**",
  new_string: "- [x] **Constraint taxonomy (20-30 types)** ✅ COMPLETE"
})

Desktop Commander:edit_block({
  file_path: "D:\\Projects\\TESSRYX\\ROADMAP.md",
  old_string: "### Week 1: Constraint Taxonomy\n- [ ] Complete 20-30 core constraint type definitions",
  new_string: "### Week 1: Constraint Taxonomy ✅ COMPLETE\n- [x] Complete 20-30 core constraint type definitions"
})
```

**Key:** Use surgical edits, not full rewrites. This keeps git diffs clean and preserves other changes.

### Step 4: Git Commit + Push (Mandatory)

Every checkpoint includes git operations:

```typescript
Desktop Commander:start_process({
  command: "cd D:\\Projects\\TESSRYX; git add -A; git commit -m 'checkpoint: completed constraint taxonomy'; git push origin main",
  timeout_ms: 30000
})
```

**Why mandatory:** Session crashes lose only 3-5 tool calls of work, not entire session.

---

## Common Patterns

### Pattern 1: Specification Work (Phase 0)

**Decision:** Completed 3 constraint type definitions

**Impact:**
- `docs/TessIR_v1.0_SPEC.md` - Add constraint types
- `STATUS.md` - Update progress counter

**Update:**
```typescript
// Update spec (add content)
edit_block(TessIR_SPEC, old_section, new_section_with_constraints)

// Update status (check off item)
edit_block(STATUS, "Constraint taxonomy (15/30)", "Constraint taxonomy (18/30)")
```

### Pattern 2: Architectural Decision (Any Phase)

**Decision:** Use SQLite for Phase 1 (defer Postgres to Phase 4)

**Impact:**
- `docs/ARCHITECTURE.md` - Update storage section
- `docs/ADR/ADR-002-sqlite-phase1.md` - Create new ADR
- `ROADMAP.md` - Adjust Phase 1 milestones

**Update:**
```typescript
// Update architecture
edit_block(ARCHITECTURE, old_storage_section, new_storage_with_sqlite)

// Create ADR (new file)
write_file("docs/ADR/ADR-002-sqlite-phase1.md", adr_content)

// Update roadmap
edit_block(ROADMAP, "PostgreSQL schema", "SQLite schema (Phase 1), Postgres migration (Phase 4)")
```

### Pattern 3: Milestone Completion (Any Phase)

**Decision:** Phase 0 complete

**Impact:**
- `STATUS.md` - Update phase
- `ROADMAP.md` - Check off Phase 0
- `CHANGELOG.md` - Add entry
- `DNA.md` - Update version history

**Update:**
```typescript
edit_block(STATUS, "Phase 0 (Specification)", "Phase 1 (Core Implementation)")
edit_block(ROADMAP, "Phase 0: [■■■■]", "Phase 0: [■■■■] ✅ COMPLETE")
edit_block(CHANGELOG, "## Unreleased", "## v0.2.0 (YYYY-MM-DD)\n- Phase 0 complete\n\n## Unreleased")
edit_block(DNA, version_section, version_section_with_new_entry)
```

### Pattern 4: Bug Fix or Code Change (Phase 1+)

**Decision:** Fixed graph traversal bug

**Impact:**
- Source code files (affected modules)
- `CHANGELOG.md` - Note fix
- Possibly `STATUS.md` - Remove blocker

**Update:**
```typescript
// Fix code
edit_block(source_file, buggy_code, fixed_code)

// Document fix
edit_block(CHANGELOG, "## Unreleased", "## Unreleased\n- Fixed: Graph traversal infinite loop on cyclic graphs")

// Remove blocker (if applicable)
edit_block(STATUS, "Blocker: Graph traversal bug", "") // Remove line
```

---

## Anti-Patterns (Don't Do This)

❌ **Updating all four pillars on every checkpoint**
- Token waste
- Adds unnecessary git noise
- Makes diffs hard to review

❌ **Skipping doc updates "for later"**
- Crash = context lost forever
- Future you won't remember the decision rationale

❌ **Conversation-only decisions**
- User says "let's use X", Claude says "ok" and proceeds
- Nothing documented = decision lost on crash

❌ **Vague updates**
- "Updated STATUS" without specifics
- Can't reconstruct what actually changed

---

## Checkpoint Checklist

Every 3-5 tool calls:

- [ ] **Identify:** What decisions were made?
- [ ] **Impact:** Which docs are affected?
- [ ] **Update:** Edit ONLY affected docs (surgical, not full rewrite)
- [ ] **Commit:** Git add, commit with message, push to remote
- [ ] **Log:** Append checkpoint to SESSION_LOG.md

**Estimated time:** 2-3 minutes per checkpoint (vs 10+ minutes updating all docs)

---

## Session End Protocol

At session end, additional steps:

1. **Final doc sync** (any remaining affected docs)
2. **Verify completeness** (all decisions documented?)
3. **Update CONTINUATION_PROMPT_NEXT_SESSION.md** (optional, if exists)
4. **Git commit + push** (final state)
5. **Mark session complete** (if using KERNL/SHIM)

---

## Recovery Protocol

If session crashes before final sync:

1. **Check last git commit** - What was last saved state?
2. **Read SESSION_LOG.md tail** - What was in progress?
3. **Identify missing updates** - What decisions aren't documented?
4. **Reconstruct from context** - Update docs based on best memory
5. **Note uncertainty** - Flag any uncertain decisions with "TODO: verify"

---

## Metrics

**Success indicators:**
- Every checkpoint commits in <3 minutes
- Git history shows frequent small commits (not giant batches)
- Diffs are readable (surgical changes, not wholesale rewrites)
- No "what was I thinking?" moments (decisions are documented with rationale)

**Failure indicators:**
- Checkpoints take 10+ minutes
- Git history shows infrequent massive commits
- Diffs are unreadable (entire files rewritten)
- Decisions reconstructed from memory instead of docs

---

## Examples

### Good Checkpoint:
```
Time: 2 minutes
Decisions: "Completed TimeWindow constraint definition"
Affected: TessIR_SPEC.md, STATUS.md
Updates: 2 surgical edits
Commit: "spec: add TimeWindow constraint with temporal bounds"
Result: Clean diff, clear history
```

### Bad Checkpoint:
```
Time: 12 minutes
Decisions: Multiple vague decisions
Affected: "Updated all docs"
Updates: 4 full file rewrites
Commit: "updated stuff"
Result: Massive diff, unclear what changed
```

---

## Integration with TESSRYX Workflow

**Phase 0 (Specification):**
- Primary affected: `TessIR_v1.0_SPEC.md`, `STATUS.md`
- Checkpoints every 3 constraint definitions

**Phase 1 (Implementation):**
- Primary affected: Source code, `STATUS.md`, `CHANGELOG.md`
- Checkpoints every 2-3 functions implemented

**Phase 2+ (Features):**
- Primary affected: Source code, `ARCHITECTURE.md` (if patterns), `STATUS.md`
- Checkpoints every feature increment

---

## Tool Preference

**Use Desktop Commander for file edits:**
- Keeps processing local (token efficient)
- Supports surgical `edit_block` operations
- Handles git operations reliably

**Avoid:**
- Reading entire file, modifying in context, rewriting entire file
- Multiple round-trip reads just to change one line

---

## Version History

- **v1.0.0** (2026-01-19): Initial protocol documented from Gregore S12

---

**Last Updated:** 2026-01-19  
**Next Review:** After Phase 1 (assess effectiveness)
