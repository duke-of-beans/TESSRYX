EXHAUSTIVE STEAL LIST: GREGORE → TESSRYX

🏗️ INFRASTRUCTURE / BACKEND
1. BullMQ + Redis Parallel Execution System ⭐⭐⭐
Status: Production (EPIC 70 - Complete)
LOC: ~1,500 lines
ROI: 125 hours saved (89% reduction vs custom build)
What to steal:

Complete BullMQ configuration and setup
Worker pool management (3-5 concurrent workers)
Job queue definitions and handlers
Redis connection management
Resource throttling and rate limiting
Job result aggregation patterns
Error handling and retry logic
Progress tracking and status updates
Queue monitoring and metrics

TESSRYX use cases:

Run multiple solver strategies in parallel (OR-Tools + Z3 + heuristics)
Parallel graph algorithm execution (SCC, reachability, critical path)
Concurrent Domain Pack validation
Async constraint satisfaction checks
Background indexing and caching

Files to steal:
src/server/queues/
  - bullmq-config.ts
  - worker-manager.ts
  - job-handlers/
  - result-aggregator.ts

2. Session Checkpoint System ⭐⭐⭐
Status: Production (Every 2-3 tool calls)
LOC: ~400 lines
ROI: Prevents catastrophic work loss
What to steal:

Checkpoint state serialization
Recovery protocol on crash/restart
State diff calculation (only save changes)
Checkpoint triggers (time-based + operation-based)
State validation on restore
Checkpoint history management
Rollback capability

TESSRYX use cases:

Long-running constraint solving (10+ minutes)
Multi-phase solver operations
Iterative refinement processes
Graph mutation tracking
"Undo" for graph state changes

Files to steal:
src/server/session/
  - checkpoint-manager.ts
  - state-serializer.ts
  - recovery-handler.ts

3. Desktop Application Infrastructure ⭐⭐
Status: Production (EPIC 41)
LOC: ~2,000 lines + configs
ROI: Months of Tauri setup + debugging
What to steal:

Complete Tauri setup and configuration
Next.js 16 + React 19 + TypeScript configs
Build system and bundling
Windows installer creation
IPC (Inter-Process Communication) patterns between Rust backend and React frontend
File system access patterns
Native OS integration
Auto-update infrastructure
Error reporting and crash handling

TESSRYX use cases:

Desktop-first for local graph processing
Native file system integration (no CORS issues)
Better performance for large graphs
Local database access (SQLite)
Native OS notifications

Files to steal:
src-tauri/
  - tauri.conf.json
  - Cargo.toml
  - src/main.rs
  - capabilities/
next.config.js
package.json (desktop scripts)

4. SQLite + Encryption Infrastructure ⭐
Status: Production
LOC: ~300 lines
ROI: Secure local storage patterns
What to steal:

SQLite setup with AES-256 encryption
Migration system
Schema versioning
Connection pooling
Transaction patterns
Backup and restore utilities

TESSRYX use cases:

Local graph storage (encrypted)
Sensitive dependency data
User credentials and tokens
Cache layer for remote data

Files to steal:
src/server/database/
  - sqlite-config.ts
  - encryption.ts
  - migrations/
  - backup-manager.ts

📊 DATA MODELS / SCHEMAS
5. Evidence Ledger Schema ⭐⭐⭐
Status: 60-70% complete (Engine H)
LOC: ~500 lines schema + logic
ROI: Months of provenance design
What to steal:
sql-- Nearly identical to TESSRYX needs
CREATE TABLE provenance (
    id UUID PRIMARY KEY,
    relation_id UUID,  -- What this evidence supports
    source TEXT NOT NULL,  -- 'manual', 'doc', 'measurement', 'community'
    evidence_links JSONB,  -- Array of URLs/references
    confidence FLOAT CHECK (confidence >= 0 AND confidence <= 1),
    asserted_by UUID,
    asserted_at TIMESTAMP,
    last_validated TIMESTAMP,
    validation_method TEXT,  -- 'manual', 'automated', 'cross_reference'
    conflicts JSONB  -- Other provenances this contradicts
);

CREATE TABLE evidence_validation_history (
    id UUID PRIMARY KEY,
    provenance_id UUID REFERENCES provenance(id),
    validation_date TIMESTAMP,
    validation_method TEXT,
    result TEXT,  -- 'confirmed', 'refuted', 'inconclusive'
    validator UUID,
    notes TEXT
);
Plus algorithms:

Confidence score propagation through chains
Conflict detection and resolution
Cross-verification logic
Evidence aging and decay
Community validation aggregation

TESSRYX use cases:

Dependency claim provenance (identical requirement)
Constraint source tracking
Validation history for Domain Packs
Trust scoring for community-contributed data


6. Trust Tier System ⭐⭐
Status: Complete (EPIC 38, T0-T5)
LOC: ~600 lines
ROI: Progressive complexity reveal
What to steal:
typescriptinterface TrustTier {
  level: 0 | 1 | 2 | 3 | 4 | 5;
  name: string;
  capabilities: string[];
  dataAccess: string[];
  automationLevel: number;
}

// Scoring algorithm
function calculateTrustScore(user: User): TrustScore {
  // Factors: usage time, validation accuracy, contribution quality
  // Returns tier level + progress to next tier
}

// Feature gating
function canAccessFeature(user: User, feature: string): boolean {
  const tier = user.trustTier;
  return features[feature].minTier <= tier;
}
```

**Plus:**
- Trust progression triggers
- Feature unlock logic
- Capability gating system
- UI progressive disclosure patterns
- Tier transition animations

**TESSRYX use cases:**
- Gate constraint types by sophistication (T0 = basic, T5 = full taxonomy)
- Progressive solver feature unlock
- Domain Pack access control
- Advanced visualization features
- API rate limits by tier

**Files to steal:**
```
src/server/trust/
  - tier-system.ts
  - scoring-algorithm.ts
  - feature-gates.ts
  - progression-triggers.ts

7. Version Control Schema (Concept - 90% designed)
Status: Designed, not yet implemented
ROI: Git for cognitive state
What to steal (design):
sqlCREATE TABLE commits (
    id UUID PRIMARY KEY,
    parent_id UUID REFERENCES commits(id),
    author UUID,
    message TEXT,
    timestamp TIMESTAMP,
    changeset JSONB  -- What changed
);

CREATE TABLE branches (
    id UUID PRIMARY KEY,
    name TEXT,
    head UUID REFERENCES commits(id),
    scenario JSONB  -- "What-if" parameters
);

CREATE TABLE tags (
    id UUID PRIMARY KEY,
    name TEXT,
    commit UUID REFERENCES commits(id),
    verified BOOLEAN  -- Community verification
);
```

**TESSRYX use cases:**
- Version control for graph state (EXACTLY what TESSRYX Phase 3 needs)
- Commit/branch/merge operations
- Lockfile generation
- Diff calculation

---

## 🧠 ALGORITHMS / LOGIC

### 8. Benchmarking Framework ⭐⭐
**Status:** Complete (EPIC 34)  
**LOC:** ~800 lines  
**ROI:** Immediate performance validation

**What to steal:**
- Benchmark suite runner
- Statistical analysis (mean, median, p95, p99)
- Comparison logic (A/B testing)
- Performance regression detection
- Visual reporting (charts, graphs)
- Canonical scenario definitions
- Result caching and historical tracking

**TESSRYX use cases:**
- Solver performance comparison (OR-Tools vs Z3)
- Heuristic effectiveness measurement
- Graph algorithm optimization validation
- Domain Pack performance benchmarking
- Regression detection on updates

**Files to steal:**
```
src/server/benchmarks/
  - benchmark-runner.ts
  - statistical-analysis.ts
  - regression-detector.ts
  - reporting/
tests/benchmarks/
  - canonical-scenarios/

9. Greg Gate (4-Mode Assertiveness) ⭐
Status: Complete (Engine F)
LOC: ~300 lines
ROI: Quality control on outputs
What to steal:
typescript// G-Score calculation
function calculateGScore(
  claim: string,
  evidence: Evidence[],
  confidence: number
): GScore {
  // Returns 0.0-1.0 based on evidence quality
}

// Response mode selection
function selectResponseMode(gScore: number): ResponseMode {
  if (gScore > 0.8) return 'ASSERT';
  if (gScore > 0.5) return 'PROBABILISTIC';
  if (gScore > 0.2) return 'INVESTIGATIVE';
  return 'REFUSE';
}
```

**TESSRYX use cases:**
- Constraint satisfaction confidence scoring
- Solver result validation (don't hallucinate feasibility)
- Explanation quality control
- User-facing confidence communication
- "I don't know" when constraints are ambiguous

---

### 10. Cognitive Token Economy ⭐
**Status:** Production (Plane B: Attention Model)  
**LOC:** ~400 lines  
**ROI:** Cost optimization

**What to steal:**
- Token budget tracking per operation
- Cost-per-information-gain calculation
- Adaptive routing based on ROI
- Budget exhaustion handling
- Priority-based allocation

**TESSRYX use cases:**
- Solver computation budget allocation
- Graph operation cost tracking
- Multi-strategy resource allocation
- User quota management (free vs paid tiers)
- Optimization: stop early if diminishing returns

**Files to steal:**
```
src/server/cognitive/
  - token-economy.ts
  - budget-manager.ts
  - roi-calculator.ts

11. Homeostasis (Digital Endocrine System) ⭐
Status: Production
LOC: ~500 lines
ROI: Adaptive system behavior
What to steal:
typescriptinterface Hormones {
  cortisol: number;    // Stress/urgency (0-1)
  dopamine: number;    // Reward/creativity (0-1)
  melatonin: number;   // Consolidation mode (0-1)
  adenosine: number;   // Fatigue (0-1)
  oxytocin: number;    // Trust/bonding (0-1)
}

// Behavioral profiles derived from hormone levels
enum Profile {
  CRISIS,
  DEEP_WORK,
  EXPLORATION,
  CONSOLIDATION,
  RECOVERY,
  FLOW,
  FATIGUE
}
```

**TESSRYX use cases:**
- Adaptive solver strategy selection (crisis = fast heuristic, deep work = exhaustive)
- System load balancing
- User interaction pacing
- Background vs foreground task prioritization
- Progressive relaxation when constraints are tight

---

### 12. Multi-Model Orchestration Patterns ⭐⭐
**Status:** Production (6 patterns implemented)  
**LOC:** ~1,200 lines  
**ROI:** Proven patterns for AI orchestration

**What to steal:**
- **Direct**: Single model call
- **Cascade**: Cheap → expensive on failure
- **Builder-Auditor**: Generate → review → fix
- **Tribunal**: Parallel voting, majority wins
- **Workspace**: Serial turn-taking, shared state
- **Ensemble**: All models, weighted synthesis

**TESSRYX use cases:**
- Parallel solver strategies (Tribunal pattern)
- Plan generation → validation (Builder-Auditor)
- Multiple LLMs for explanation generation (Ensemble)
- Cheap validation → expensive proof (Cascade)

**Files to steal:**
```
src/server/orchestration/
  - patterns/
    - direct.ts
    - cascade.ts
    - builder-auditor.ts
    - tribunal.ts
    - workspace.ts
    - ensemble.ts
  - orchestrator.ts
  - result-synthesizer.ts
```

---

## 🎨 UI / UX PATTERNS

### 13. Progressive Disclosure State Machine
**Status:** Designed (EPIC 35 specs complete)  
**ROI:** "Grandma Test" compliance

**What to steal:**
- Feature reveal triggers
- Complexity gating logic
- Onboarding flow state machine
- User readiness detection
- Tooltip and hint system
- Settings-driven complexity control

**TESSRYX use cases:**
- Start with simple constraints (Precedence only)
- Progressively reveal advanced constraint types
- Gate solver features by user sophistication
- Adaptive UI complexity

---

### 14. Command Palette (Cmd+K) ⭐
**Status:** Complete  
**LOC:** ~400 lines  
**ROI:** Power user efficiency

**What to steal:**
- Fuzzy search implementation
- Command registry system
- Keyboard shortcut handling
- Action execution pipeline
- Recently used tracking
- Context-aware command filtering

**TESSRYX use cases:**
- Quick constraint creation
- Graph navigation shortcuts
- Solver invocation commands
- Settings access
- Domain Pack management

---

### 15. Inspector Drawer System
**Status:** Designed (Phase 6)  
**ROI:** Non-intrusive debugging

**What to steal:**
- Drawer slide-out animation
- Tab-based content organization
- Collapsible sections
- Real-time data streaming
- Export/copy functionality

**TESSRYX use cases:**
- Constraint inspector
- Graph state viewer
- Solver progress monitor
- Provenance explorer
- Version history browser

---

### 16. Shimmering Memory Reveals ⭐
**Status:** Designed (EPIC 35)  
**ROI:** Delightful context awareness

**What to steal:**
- Text shimmer animation
- Semantic search on hover
- Click-to-expand modal pattern
- Inline contextual information
- Privacy controls per reveal

**TESSRYX use cases:**
- Highlight similar past constraints
- Show related dependencies on hover
- Reveal cached solutions
- Surface relevant Domain Pack examples

---

## 🧪 TESTING / QUALITY

### 17. Canonical Test Suite ⭐⭐
**Status:** Partial (EPIC 34 benchmarks)  
**LOC:** ~50 scenarios  
**ROI:** Regression prevention

**What to steal:**
- Test scenario structure
- Expected output definitions
- Automated comparison logic
- Regression detection
- Coverage tracking

**TESSRYX use cases:**
- 50 canonical dependency scenarios (direct port concept)
- Solver validation suite
- Domain Pack test cases
- API contract tests

---

### 18. Property-Based Testing Patterns
**Status:** Designed (not yet implemented)  
**ROI:** Edge case discovery

**What to steal (concept):**
- Hypothesis-style generators
- Property definitions
- Invariant checking
- Shrinking for minimal failing cases

**TESSRYX use cases:**
- Generate random constraint sets
- Verify solver correctness properties
- Graph operation invariants
- Provenance consistency checks

---

## ⚙️ DEVOPS / TOOLING

### 19. Git Integration Patterns ⭐
**Status:** Production (via Desktop Commander)  
**LOC:** ~200 lines  
**ROI:** Clean git discipline

**What to steal:**
- Conventional commit enforcement
- Automatic commit on checkpoint
- Pre-commit hooks (TypeScript validation)
- Branch naming conventions
- Tag management for releases
- Commit message templates

**TESSRYX use cases:**
- Version control integration
- Automatic documentation commits
- Release tagging (Domain Packs)
- Contribution workflow

---

### 20. Architecture Decision Records (ADR) System
**Status:** Designed (not yet implemented)  
**ROI:** Decision transparency

**What to steal:**
- ADR template structure
- Numbering system
- Decision consequence tracking
- Superseding mechanism
- Index generation

**TESSRYX use cases:**
- Technology choice documentation (Python vs Rust)
- Constraint design decisions
- Solver selection rationale
- Schema evolution tracking

---

### 21. Session Logging System ⭐
**Status:** Production  
**LOC:** ~300 lines  
**ROI:** Handoff quality

**What to steal:**
- Structured session logs
- Decision tracking per session
- Next steps documentation
- Handoff protocol templates
- Session summaries

**TESSRYX use cases:**
- Development session tracking
- Solver run documentation
- Bug investigation logs
- User support history

**Files to steal:**
```
docs/
  - SESSION_LOG.md (template)
  - session-logger.ts
```

---

## 📚 DOCUMENTATION / PROCESS

### 22. Four-Pillar Documentation System ⭐⭐
**Status:** Production  
**ROI:** Always-current docs

**What to steal:**
- Document structure: DNA, ROADMAP, STATUS, ARCHITECTURE
- Atomic update protocol (all 4 sync together)
- Impact-aware sync (only update affected docs)
- Checkpoint integration
- Git commit discipline

**TESSRYX use cases:**
- Project documentation system (already using similar structure!)
- Session-to-session continuity
- Multi-contributor coordination
- Stakeholder communication

---

### 23. Instruction System (Hierarchical) ⭐⭐
**Status:** Production  
**LOC:** ~1,200 lines  
**ROI:** Token-efficient AI development

**What to steal:**
- Two-tier structure: In-app (<500 tokens) + Detailed (~8K tokens)
- Bootstrap protocol
- Authority triggers (6 mandatory push-back scenarios)
- LEAN-OUT decision tree
- Checkpoint protocols
- Phase-specific workflows

**TESSRYX use cases:**
- AI-assisted development guidelines
- Quality enforcement automation
- Handoff instructions
- Contributor onboarding

**Files to steal:**
```
CLAUDE_INSTRUCTIONS_INAPP.md
CLAUDE_INSTRUCTIONS.md
docs/INSTRUCTION_SYSTEM_COMPLETE.md

24. LEAN-OUT Decision Framework ⭐⭐⭐
Status: Production philosophy
ROI: Prevents infrastructure bloat
What to steal:
typescriptfunction shouldIBuildThis(feature: string): Decision {
  // 1. Search existing tools
  const tool = searchEcosystem(['npm', 'cargo', 'pip', 'MCP']);
  if (tool.exists && tool.solves(feature)) {
    return { action: 'USE_EXISTING', tool: tool.name };
  }
  
  // 2. Is this generic infrastructure?
  if (isGeneric(feature)) {
    return { action: 'STOP', error: 'LEAN-OUT VIOLATION' };
  }
  
  // 3. Domain-specific intelligence only
  if (isDomainSpecific(feature) && isIntelligence(feature)) {
    return { action: 'BUILD_CUSTOM', justification: 'Domain logic' };
  }
  
  return { action: 'ASK_USER' };
}

// Infrastructure RED FLAGS
const NEVER_BUILD = [
  'job_queue',      // → BullMQ
  'cache_layer',    // → Redis
  'retry_logic',    // → BullMQ built-in
  'rate_limiter',   // → ioredis-rate-limiter
  'scheduler',      // → BullMQ repeatable
  'ast_parser',     // → ESLint/TypeScript Compiler
  'monitoring',     // → Grafana + Prometheus
];
TESSRYX use cases:

Prevent reinventing solvers (use OR-Tools, Z3)
Use proven databases (Postgres, Neo4j)
Leverage existing graph libraries (NetworkX)
Focus on intelligence (TessIR, explanation engine)


25. Authority Protocol ⭐⭐
Status: Production
ROI: Prevents quality disasters
What to steal:

6 mandatory push-back triggers:

Architectural whack-a-mole (treating symptoms)
Long operations without checkpoints (>8 min)
Documentation drift (mid-session decisions)
Quality violations (mocks, stubs, TODOs)
Large file anti-pattern (>1000 lines frequently queried)
LEAN-OUT challenge (building generic infrastructure)


Discourse protocol (not servant/master, peer with expertise)
Decision documentation requirement
Veto mechanism

TESSRYX use cases:

AI code generation quality control
Architecture review automation
Technical debt prevention
Documentation enforcement


🔐 SECURITY / PRIVACY
26. Encryption at Rest Patterns ⭐
Status: Production (AES-256 SQLite)
LOC: ~150 lines
ROI: Privacy compliance
What to steal:

AES-256 encryption setup
Key derivation (PBKDF2)
Key storage and management
Secure deletion patterns
Encrypted backup creation

TESSRYX use cases:

Sensitive dependency data
User credentials
Proprietary graph data
Client information (enterprise use)


27. Privacy Tier System
Status: Designed (EPIC 37)
ROI: User control over data
What to steal:

Three privacy presets (Maximum, Balanced, Full Power)
Feature dependency mapping
Privacy impact warnings
Consent flow management
Data residency controls

TESSRYX use cases:

Control where graph data is stored (local vs cloud)
Toggle telemetry and analytics
Manage third-party integrations
Compliance requirements (GDPR, SOC2)


💰 MONETIZATION / BUSINESS
28. Trust-Based Feature Unlocking
Status: Production (T0-T5 system)
ROI: Freemium conversion strategy
What to steal:

Progressive value demonstration
Earned capability model (not just paywall)
Conversion funnel tracking
Free tier limitations (computational, not artificial)

TESSRYX use cases:

Free: Basic constraints + small graphs
T1-T2: Medium graphs + common Domain Packs
T3-T4: Large graphs + advanced features
T5: Enterprise features + custom packs


📈 ANALYTICS / METRICS
29. Performance Metrics Dashboard (Concept)
Status: Designed (EPIC 34 foundation)
ROI: Data-driven optimization
What to steal:

Metric collection framework
Time series storage
Visualization patterns
Alert thresholds
Export/reporting

TESSRYX use cases:

Solver performance tracking
API latency monitoring
Graph operation metrics
User behavior analytics
Cost per operation


🎯 COGNITIVE SYSTEMS (Concepts)
30. ORACLE (Adaptive Routing) ⭐
Status: Production
ROI: Intelligent routing decisions
What to steal:
typescript// Query classification
function classifyQuery(query: string): QueryType {
  // Returns: simple | complex | computational | creative
}

// Route by entropy reduction per cost
function selectStrategy(
  query: QueryType,
  availableStrategies: Strategy[]
): Strategy {
  // Pick cheapest strategy that reduces uncertainty most
}
TESSRYX use cases:

Route to appropriate solver (OR-Tools vs Z3)
Select graph algorithm by query type
Choose explanation detail level
Optimize computation budget


31. PARALLAX (Semantic Search) ⭐
Status: Production
ROI: Fast retrieval
What to steal:

Semantic indexing system
Vector embedding storage
Similarity search
Result ranking
Cache invalidation

TESSRYX use cases:

Find similar constraints
Search Domain Pack libraries
Locate relevant examples
Pattern matching in graphs


32. CONSOLIDATION (Background Processing)
Status: Production
ROI: Offline optimization
What to steal:

Background job scheduling
Overnight processing patterns
Incremental updates
Result caching
Priority queue management

TESSRYX use cases:

Graph pre-computation (overnight SCC, critical paths)
Constraint library indexing
Validation queue processing
Cache warming
Backup generation


33. SENTRY (External Intelligence) ⭐
Status: Production
ROI: Stay current
What to steal:

Web scraping patterns
Change detection
Notification system
Source reliability scoring
Update frequency management

TESSRYX use cases:

Monitor package manager updates
Track dependency vulnerabilities
Watch for constraint library updates
Domain Pack version tracking


🏛️ ARCHITECTURE PATTERNS
34. Three-Plane Toroidal Architecture (Concept) ⭐
Status: Theoretical framework
ROI: Elegant system design
What to steal (concept):

Plane A: World Model (claims, unknowns, causal graph)
Plane B: Attention Model (working set, cognitive tokens)
Plane C: Self Model (competence, calibration, observer)
Prediction error minimization loop

TESSRYX use cases:

Plane A: Graph state + constraints (world model)
Plane B: Solver focus + resource allocation (attention)
Plane C: Solver performance history + meta-learning (self)


35. The Ghost (Self-Observer) ⭐
Status: Production
ROI: Self-correction capability
What to steal:
typescript// R(t) score (self-reference)
function calculateRScore(
  system: System,
  timeWindow: number
): RScore {
  // Components: self-mention, meta-cognition, uncertainty,
  // goal alignment, value consistency, drift detection
}

// Ghost states
enum GhostState {
  DORMANT,
  OBSERVING,
  ANALYZING,
  ALERTING,
  VETOING
}

// Alert system
function checkForViolations(
  action: Action,
  sacredLaws: Law[]
): Alert | null {
  // Returns alert if action violates principles
}
```

**TESSRYX use cases:**
- Self-monitoring of solver quality
- Detect when hallucinating feasibility
- Catch constraint contradictions
- Flag when provenance is weak
- Veto unsafe graph mutations

---

## 🔧 UTILITY SYSTEMS

### 36. Configuration Management ⭐
**Status:** Production  
**ROI:** Clean settings handling

**What to steal:**
- Settings schema validation (Zod)
- Default value management
- Migration on schema changes
- Settings export/import
- Environment-specific configs

**TESSRYX use cases:**
- Solver preferences
- Graph display options
- API configurations
- Privacy settings
- Performance tuning

---

### 37. Error Handling Patterns ⭐
**Status:** Production  
**ROI:** Graceful degradation

**What to steal:**
- Structured error types
- Error boundary components (React)
- Retry strategies
- Fallback mechanisms
- User-friendly error messages
- Error reporting/telemetry

**TESSRYX use cases:**
- Solver failure handling
- Graph corruption recovery
- API timeout management
- Constraint conflict resolution
- Import validation errors

---

### 38. State Management (Zustand) ⭐
**Status:** Production  
**ROI:** Clean state architecture

**What to steal:**
- Store structure patterns
- Async action handling
- State persistence
- DevTools integration
- Middleware patterns

**TESSRYX use cases:**
- Graph state management (if building UI)
- Solver status tracking
- User session state
- Settings management

---

---

# WHERE TO FIND THESE IN GREGORE

Most code is at: `D:\Gregore\`

**Key directories:**
```
src/server/
  - queues/           # BullMQ infrastructure
  - session/          # Checkpoint system
  - trust/            # Trust tier system
  - orchestration/    # Multi-model patterns
  - cognitive/        # Token economy, ORACLE
  - benchmarks/       # Benchmarking framework
  
src/components/
  - ui/               # UI patterns
  - CommandPalette/   # Cmd+K implementation
  
docs/
  - ARCHITECTURE.md   # System design
  - SACRED_LAWS.md    # Principles
  - engines/          # Engine specs
  - systems/          # System specs
  
CLAUDE_INSTRUCTIONS.md  # Development guidelines
PROJECT_DNA.yaml        # Project identity