# TESSRYX - Claude Desktop Instructions (In-App)
**Token-efficient routing to local detailed instructions**  
**Version:** 1.0.0  
**Location:** Paste this into Claude Desktop project settings

---

## Bootstrap (Every Session Start)

```typescript
// STEP 1: Load local detailed instructions
Filesystem:read_text_file({
  path: "D:\\Projects\\TESSRYX\\CLAUDE_INSTRUCTIONS.md"
})

// STEP 2: Check project status
Filesystem:read_text_file({
  path: "D:\\Projects\\TESSRYX\\STATUS.md"
})

// STEP 3: Check for session recovery
// If this is continuation from crash/interruption:
Filesystem:read_text_file({
  path: "D:\\Projects\\TESSRYX\\SESSION_LOG.md",
  tail: 50  // Last 50 lines
})
```

---

## Quick Project Identity

**Name:** TESSRYX  
**Mission:** Universal Dependency Intelligence Infrastructure  
**Current Phase:** Phase 0 (Specification development)  
**Location:** D:/Projects/TESSRYX/  
**Version:** 0.1.0-genesis  
**Wedge:** Software Development (NOT Automotive)

---

## Core Principles (Enforced)

1. **Build Intelligence, Not Plumbing** - LEAN-OUT: Use OR-Tools/Z3, not custom solvers
2. **Option A Perfection** - Production-grade from day one, zero technical debt
3. **Foundation Out** - TessIR spec before implementation, backend before UI
4. **Evidence-Based Trust** - Every relationship has provenance + confidence
5. **Handoff-Native** - Checkpoint every 3-5 tool calls, comprehensive docs

---

## Authority Protocol (Mandatory Push-Back)

🛑 **STOP and require confirmation when:**
- Architectural whack-a-mole (same symptom 3x = wrong layer)
- Long operations (>8min without checkpoints)
- Documentation drift (critical decisions mid-session)
- Quality violations (mocks, stubs, placeholders, TODOs)
- Large file anti-pattern (>1000 lines + frequent queries)
- LEAN-OUT challenge (building infrastructure that exists)

---

## File Organization

**Core Docs:** DNA.md, STATUS.md, CHANGELOG.md, SESSION_LOG.md, README.md  
**Detailed Instructions:** CLAUDE_INSTRUCTIONS.md (5K+ tokens, load when needed)  
**Technical:** docs/ARCHITECTURE.md, docs/TessIR_v1.0_SPEC.md  
**Decisions:** docs/ADR/ (Architecture Decision Records)

---

## Session Workflow

```yaml
start_session:
  1. Load CLAUDE_INSTRUCTIONS.md (detailed rules)
  2. Read STATUS.md (current state)
  3. Check SESSION_LOG.md tail (recovery if needed)
  4. Identify mode: spec_writing | architecture | planning | coding

checkpoint_every: "3-5 tool calls"
commit_git: "After every significant change"
update_status: "When phase changes or blockers appear"
```

---

## Current Focus (Phase 0)

- TessIR v1.0 specification (constraint taxonomy, operations, serialization)
- Canonical test suite (50 scenarios with expected outputs)
- Architecture Decision Records (ADR-001 through ADR-005)
- GitHub remote setup + push

---

## Technology Stack

**V1 (Current):** Python 3.12+, NetworkX, OR-Tools, Postgres, FastAPI  
**V2 (Future):** Rust kernel, Neo4j, gRPC, React

**Key Decisions:**
- Software Dev wedge (data already exists in package managers)
- Open TessIR spec (ecosystem strategy)
- Postgres first, migrate to hybrid if needed
- Constraints as first-class objects (NON-NEGOTIABLE)

---

## For Detailed Rules

**Load:** `Filesystem:read_text_file({ path: "D:\\Projects\\TESSRYX\\CLAUDE_INSTRUCTIONS.md" })`

This gives full:
- Development workflows
- Code quality standards
- Testing requirements
- Git commit conventions
- Checkpoint protocols
- LEAN-OUT enforcement details
- Phase-specific guidelines

---

**Last Updated:** 2026-01-19  
**Token Budget:** <500 tokens (routing only, details in local file)
