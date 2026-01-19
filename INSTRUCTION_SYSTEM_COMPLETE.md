# TESSRYX Instruction System Complete ✅

## What We Built

### Two-Tier Hierarchical System

**1. In-App Instructions (Token-Efficient Routing)**
- **File:** `CLAUDE_INSTRUCTIONS_INAPP.md`
- **Size:** ~500 tokens
- **Purpose:** Paste into Claude Desktop project settings
- **Contains:**
  - Bootstrap protocol (load detailed instructions)
  - Quick project identity
  - Core principles summary
  - Authority protocol triggers
  - File organization overview
  - Routing to detailed local instructions

**2. Local Detailed Instructions (Comprehensive Rules)**
- **File:** `CLAUDE_INSTRUCTIONS.md`
- **Size:** 1,064 lines (~8K tokens when loaded)
- **Purpose:** Full project context, loaded when needed
- **Contains:**
  - Complete bootstrap protocol
  - All sacred principles with enforcement details
  - LEAN-OUT mandate with decision tree
  - Authority protocol (6 mandatory push-back triggers)
  - Session management (checkpoint every 3-5 tools)
  - Phase-specific workflows
  - Code quality standards (Phase 1+)
  - Git workflow conventions
  - File organization
  - Phase 0 checklist
  - Quick reference commands

---

## Key Features

### Token Efficiency Strategy
```
In-App (always loaded): <500 tokens
→ Routes to local when details needed

Local (loaded on demand): ~8K tokens
→ Only when specific guidance required

Mounted files (unlimited): Full project access
→ When comprehensive context needed
```

### Authority Protocol (Mandatory Push-Back)

Claude MUST stop and require confirmation when:
1. **Architectural whack-a-mole** (same symptom 3x)
2. **Long operations** (>8 min without checkpoints)
3. **Documentation drift** (critical decisions mid-session)
4. **Quality violations** (mocks, stubs, TODOs, missing error handling)
5. **Large file anti-pattern** (>1000 lines + frequent queries)
6. **LEAN-OUT challenge** (building infrastructure that exists)

### LEAN-OUT Enforcement

Decision tree for every infrastructure choice:
```typescript
Does existing tool solve this?
  YES → Use existing tool ✅
  NO ↓
Is this generic infrastructure?
  YES → STOP (LEAN-OUT violation) ❌
  NO ↓
Is this domain-specific intelligence?
  YES → Build custom ✅
  NO → Ask user
```

Examples:
- ✅ USE: OR-Tools, Z3, NetworkX, FastAPI, Alembic
- ❌ BUILD: Job queue, cache, scheduler, monitor
- ✅ BUILD: TessIR parser, provenance model, blast radius analysis

### Sacred Principles Enforced

1. **Build Intelligence, Not Plumbing**
   - LEAN-OUT mandatory checks
   - Use proven tools for generic infrastructure

2. **Option A Perfection**
   - Production-grade from day one
   - Zero technical debt tolerance
   - No mocks, stubs, placeholders, TODOs

3. **Foundation Out**
   - Spec → Test → Core → API → UI
   - Backend before surface

4. **Domain-Agnostic Core + Domain Packs**
   - Universal primitives in core
   - Domain-specific in packs

5. **Trust Through Evidence**
   - Every assertion has provenance
   - Confidence, validation, source tracking

6. **Handoff-Native Development**
   - Checkpoint every 3-5 tool calls
   - Comprehensive documentation
   - Git commits after every significant change

---

## How to Use

### In Claude Desktop App

1. **Project Settings → Custom Instructions:**
   - Paste contents of `CLAUDE_INSTRUCTIONS_INAPP.md`
   - This gives token-efficient routing + triggers

2. **Session Start:**
   - Claude automatically loads detailed instructions
   - Checks STATUS.md
   - Checks SESSION_LOG.md for recovery

3. **During Work:**
   - Claude checkpoints every 3-5 tool calls
   - Git commits after every significant change
   - Updates STATUS.md when state changes
   - Triggers authority protocol when needed

### Token Flow Example

```
User: "Let's work on constraint taxonomy"

Claude: [Loads CLAUDE_INSTRUCTIONS_INAPP.md - 500 tokens]
        ↓
        [Sees: Need detailed rules, load local file]
        ↓
        [Loads D:\Projects\TESSRYX\CLAUDE_INSTRUCTIONS.md - 8K tokens]
        ↓
        [Loads D:\Projects\TESSRYX\STATUS.md - current state]
        ↓
        [Loads D:\Projects\TESSRYX\docs\TessIR_v1.0_SPEC.md - work file]
        ↓
        [Ready to work with full context]

Total context: ~10K tokens (well within Claude's capacity)
```

---

## Advantages Over Single-File Approach

### Old Way (Single Large Instructions)
```
❌ Always loads 10K+ tokens (wastes context window)
❌ Can't scale (adding details = bloat)
❌ Hard to navigate (everything in one file)
❌ Token budget issues for complex queries
```

### New Way (Hierarchical)
```
✅ Only loads what's needed
✅ Scales infinitely (add details without bloat)
✅ Clear separation (routing vs rules)
✅ Token budget optimized
✅ Can mount entire project when needed
```

---

## File Structure Now

```
D:/Projects/TESSRYX/
├── CLAUDE_INSTRUCTIONS_INAPP.md     # In-app (routing, 500 tokens)
├── CLAUDE_INSTRUCTIONS.md           # Local (detailed, 8K tokens)
├── DNA.md                           # Project identity
├── STATUS.md                        # Current state
├── CHANGELOG.md                     # Version history
├── SESSION_LOG.md                   # Session tracking
├── README.md                        # Public docs
├── docs/
│   ├── ARCHITECTURE.md              # Technical architecture
│   ├── TessIR_v1.0_SPEC.md         # Formal specification
│   └── ADR/                         # Decision records
└── ...
```

---

## What This Enables

### 1. Context Window Efficiency
- Small queries: Only routing instructions loaded
- Complex work: Full rules loaded on demand
- Maximum work: Mount entire project via MCP

### 2. Handoff-Native Development
- Any AI can pick up where we left off
- Zero context loss
- Comprehensive recovery from crashes

### 3. Quality Enforcement
- Mandatory push-back on quality risks
- LEAN-OUT prevents infrastructure bloat
- Option A perfection non-negotiable

### 4. Scalability
- Add more details to local file (no token penalty)
- Add more phases (just append to local)
- Add more workflows (routing still <500 tokens)

---

## Commits Made

**Commit 7bf5f3e:**
```
docs: Add hierarchical instruction system for Claude Desktop

- Add CLAUDE_INSTRUCTIONS_INAPP.md (in-app routing, <500 tokens)
- Add CLAUDE_INSTRUCTIONS.md (detailed local rules, 1064 lines)

Features:
- Token-efficient two-tier system
- Complete development workflows
- Authority protocol (mandatory push-back)
- LEAN-OUT enforcement
- Checkpoint protocols
- Phase-specific guidelines
- Code quality standards
- Git workflow conventions

Files: 2 changed, 1190 insertions(+)
```

---

## Next Steps

1. **Copy CLAUDE_INSTRUCTIONS_INAPP.md to Claude Desktop settings**
2. **Test the system** (start new session, verify bootstrap works)
3. **Begin Phase 0 work** (constraint taxonomy development)

---

## Summary

**You now have a professional-grade instruction system that:**
- ✅ Optimizes token usage (routing vs detailed)
- ✅ Enforces all sacred principles
- ✅ Provides mandatory quality checks
- ✅ Enables perfect handoff
- ✅ Scales without bloat
- ✅ Supports crash recovery
- ✅ Documents decisions
- ✅ Maintains git discipline

**Based on proven patterns from DEV environment** (KERNL, GREGORE, SHIM, Consensus)

**Ready for Phase 0 specification development work!** 🚀

---

**Created:** 2026-01-19  
**Commit:** 7bf5f3e  
**Status:** COMPLETE ✅
