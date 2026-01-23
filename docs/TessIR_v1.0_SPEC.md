# TessIR v1.0 Specification
**TESSRYX Intermediate Representation - Formal Specification**

**Status:** DRAFT (Phase 0 - Outline)  
**Version:** 1.0.0-draft  
**Last Updated:** 2026-01-19  
**Authors:** David Kirsch, Genius Council (GPT, Gemini, Claude)

---

## Abstract

TessIR (TESSRYX Intermediate Representation) is an open standard for representing dependencies, constraints, and their associated metadata in a domain-agnostic, formally verifiable manner. This specification defines the core primitives, data structures, constraint types, and operations that enable universal dependency intelligence.

**Key Design Goals:**
1. **Domain-Agnostic:** Works for software, hardware, operations, construction, supply chain
2. **Formally Verifiable:** All plans can be proven valid or explained as impossible
3. **Evidence-Based:** Every relationship has provenance and confidence
4. **Versionable:** Git-like operations for dependency state
5. **Composable:** Hierarchical entities, constraint templates, domain packs

---

## Table of Contents

1. [Core Primitives](#core-primitives)
2. [Entity Schema](#entity-schema)
3. [Relation Types](#relation-types)
4. [Constraint System](#constraint-system)
5. [Contract Model](#contract-model)
6. [Assumption Schema](#assumption-schema)
7. [Provenance Model](#provenance-model)
8. [Version Control](#version-control)
9. [Domain Packs](#domain-packs)
10. [Operations](#operations)
11. [Serialization Format](#serialization-format)
12. [Conformance](#conformance)

---

## 1. Core Primitives

TessIR defines seven core primitives that form the foundation of all dependency representations:

### 1.1 Entity
A discrete unit that can participate in dependencies (packages, tasks, components, resources).

### 1.2 Relation
A typed connection between entities that represents a dependency relationship.

### 1.3 Constraint
A first-class rule that governs valid entity states or sequences.

### 1.4 Contract
A rich specification of preconditions, postconditions, and invariants for a relation.

### 1.5 Assumption
An explicit statement about the world that may be uncertain or time-limited.

### 1.6 Provenance
Metadata tracking the source, evidence, and confidence of any assertion.

### 1.7 Version
A snapshot of dependency state with commit/branch/merge semantics.

---

## 2. Entity Schema

### 2.1 Entity Definition

```typescript
interface Entity {
  id: UUID;                    // Unique identifier
  type: EntityType;            // Domain-specific type
  name: string;                // Human-readable name
  version?: string;            // Optional version string
  parent?: UUID;               // Hierarchical composition
  children?: UUID[];           // Child entities (for bundles)
  metadata: Record<string, any>;  // Extensible properties
  created_at: DateTime;
  updated_at: DateTime;
}
```

### 2.2 EntityType System

**Base Types (Universal):**
- `component` - Generic building block
- `resource` - Consumable or capacity-limited
- `task` - Work item or process step
- `gate` - Checkpoint or decision point

**Domain Pack Extension:**
Domain packs extend with specific types:
```yaml
# Software Dev Pack
entity_types:
  - package       # extends: component
  - service       # extends: component
  - database      # extends: resource
  - deployment    # extends: task
  
# Automotive Pack
entity_types:
  - part          # extends: component
  - subsystem     # extends: component
  - tool          # extends: resource
  - installation  # extends: task
```

### 2.3 Hierarchical Composition

Entities can form parent-child relationships:
```
Vehicle (parent)
  ├── Powertrain (child, parent)
  │   ├── Engine (child)
  │   ├── Transmission (child)
  │   └── Driveshaft (child)
  └── Electrical (child, parent)
      ├── Battery (child)
      └── Alternator (child)
```

**Semantics:**
- Changes to parent MAY propagate to children
- Constraints on parent MAY apply to children
- Deleting parent REQUIRES handling children

---

## 3. Relation Types

### 3.1 Relation Definition

```typescript
interface Relation {
  id: UUID;
  type: RelationType;       // Semantic relationship type
  from_entity: UUID;        // Source entity
  to_entity: UUID;          // Target entity
  strength: number;         // 0.0-1.0 (for probabilistic)
  contract?: Contract;      // Rich dependency contract
  provenance: Provenance;   // Evidence and confidence
  created_at: DateTime;
  updated_at: DateTime;
}
```

### 3.2 Core Relation Types (Universal)

**Dependency Relations:**
- `requires` - A needs B to function
- `enables` - A makes B possible
- `blocks` - A prevents B
- `conflicts` - A and B are mutually exclusive

**Temporal Relations:**
- `precedes` - A must happen before B
- `follows` - A must happen after B
- `concurrent` - A and B can/must happen simultaneously

**Compositional Relations:**
- `contains` - A is composed of B
- `part_of` - Inverse of contains
- `replaces` - A is a substitute for B

### 3.3 Relation Strength

**Strength Values:**
- `1.0` - Hard dependency (deterministic)
- `0.5-0.99` - Probabilistic dependency
- `0.01-0.49` - Weak/optional dependency
- `0.0` - No dependency (used for removals)

**Example:**
```json
{
  "type": "requires",
  "from_entity": "turbo_kit",
  "to_entity": "fuel_upgrade",
  "strength": 0.85,
  "provenance": {
    "confidence": 0.85,
    "note": "Most builds need fuel upgrade, some stock OK if boost <8 PSI"
  }
}
```

---

## 4. Constraint System

### 4.1 Overview

Constraints are first-class objects that govern valid entity states, sequences, and relationships. TessIR v1.0 defines **28 core constraint types** across 4 categories, providing universal coverage for dependency intelligence across all domains.

**Design Principles:**
- **First-Class Objects:** Constraints are entities themselves, not edge properties
- **Composable:** Complex rules expressed by combining simple constraints
- **Domain-Agnostic:** Types work across software, operations, manufacturing, construction
- **Solver-Ready:** Each type maps to constraint programming (CP-SAT) or SMT (Z3) primitives
- **Extensible:** Domain Packs can add specialized subtypes

**Complete Taxonomy:** See [CONSTRAINT_TAXONOMY_V1.md](CONSTRAINT_TAXONOMY_V1.md) for full definitions, parameters, and cross-domain examples.

### 4.2 Constraint Definition

```typescript
interface Constraint {
  id: UUID;
  type: ConstraintType;
  entities: UUID[];              // Entities involved
  parameters: Record<string, any>;  // Type-specific params
  priority: Priority;            // Hard, Soft, Preference
  provenance: Provenance;
  scope?: Scope;                 // Context where this applies
  created_at: DateTime;
}
```

### 4.3 Constraint Categories (28 Types)

#### 4.3.1 Temporal Constraints (8 types)
Govern timing, sequencing, and scheduling:
- **Precedence:** A must complete before B starts
- **Time Window:** Entity must occur within temporal bounds
- **Duration:** Entity must take specified time
- **Deadline:** Hard completion cutoff
- **Delay:** Minimum gap between events
- **Synchronization:** Multiple entities happen simultaneously
- **Recurrence:** Repeating schedule (cron-like)
- **Expiration:** Entity validity ends at time

#### 4.3.2 Resource Constraints (8 types)
Govern allocation, capacity, and consumption:
- **Resource Capacity:** Maximum concurrent usage
- **Resource Allocation:** Assign quantity to task
- **Resource Sharing:** Shared allocation across tasks
- **Budget:** Total cost constraint
- **Throughput:** Rate limiting
- **Reservation:** Exclusive access period
- **Utilization:** Min/max usage percentage
- **Dependency Quota:** Limit complexity (max dependencies)

#### 4.3.3 Logical Constraints (7 types)
Define boolean relationships and choices:
- **Mutual Exclusion (Mutex):** Entities cannot co-occur
- **Choice:** Select exactly N of M entities
- **Conditional:** If-then rule (context-dependent)
- **Implication:** If A then B must occur
- **Equivalence:** A if and only if B
- **Disjunction:** At least one must occur (OR)
- **Negation:** Entity must not occur (prohibition)

#### 4.3.4 Structural Constraints (5 types)
Govern hierarchies, composition, and interfaces:
- **Hierarchy:** Parent-child ordering
- **Composition:** Whole requires all parts
- **Encapsulation:** Internal entities hidden
- **Interface Compatibility:** Type checking
- **Cardinality:** Relationship count constraints (1-to-many, etc)

### 4.4 Constraint Priority

```typescript
enum Priority {
  HARD = "hard",       // MUST be satisfied (infeasible if violated)
  SOFT = "soft",       // SHOULD be satisfied (optimize for)
  PREFERENCE = "pref"  // NICE TO satisfy (lowest priority)
}
```

**Solver Behavior:**
- **Hard:** Infeasible if violated (search terminates, minimal unsat core returned)
- **Soft:** Objective function penalty (search continues, minimizes violations)
- **Preference:** Tiebreaker when multiple solutions exist (lowest priority optimization)

### 4.5 Constraint Scope

Constraints can be context-dependent:

```typescript
interface Scope {
  applies_when: Condition[];  // Boolean expressions
  domains: string[];          // Which domain packs
  versions: string[];         // Which entity versions
  geographic?: string;        // Regional applicability
  temporal?: TimeRange;       // Time period
}
```

**Example:**
```json
{
  "type": "precedence",
  "before": "painting",
  "after": "sanding",
  "scope": {
    "applies_when": ["ambient_temp > 50F", "humidity < 70%"],
    "geographic": "outdoor_only"
  }
}
```

### 4.6 Constraint Composition

Complex rules expressed by combining simple constraints:

**Example: Automotive Build Constraints**
```json
{
  "constraints": [
    {
      "type": "implication",
      "antecedent": "turbo_kit",
      "consequent": "fuel_system_upgrade",
      "priority": "hard"
    },
    {
      "type": "conditional",
      "condition": "boost_pressure > 15psi",
      "then_constraint": {
        "type": "implication",
        "antecedent": "turbo_kit",
        "consequent": "forged_internals"
      },
      "priority": "hard"
    },
    {
      "type": "budget",
      "entities": ["turbo_kit", "fuel_system_upgrade", "forged_internals"],
      "max_cost": 25000,
      "currency": "USD",
      "priority": "hard"
    }
  ]
}
```

### 4.7 Solver Backend Mapping

Each constraint type maps to solver primitives:

| Constraint Type | OR-Tools (CP-SAT) | Z3 (SMT) | Domain |
|----------------|-------------------|----------|--------|
| Precedence | IntervalVar | Arithmetic | Scheduling |
| Mutex | NoOverlap | Distinct | Resource |
| Choice | Exactly/AtMost | PbEq/PbLe | Selection |
| Budget | ScalProd | Sum | Optimization |
| Implication | OnlyEnforceIf | Implies | Logic |
| Time Window | IntervalVar.StartRange | And(>=, <=) | Scheduling |

**Strategy:**
- Temporal + Resource → OR-Tools CP-SAT (scheduling domain)
- Logical + Structural → Z3 SMT (boolean/arithmetic)
- Hybrid problems → Multi-solver orchestration (cascade or tribunal pattern)

*Full mapping table in implementation phase (Phase 2)*

---

## 5. Contract Model

### 5.1 Contract Definition

Dependencies are contracts with formal specifications:

```typescript
interface Contract {
  preconditions: Condition[];    // Must be true before
  postconditions: Condition[];   // Will be true after
  invariants: Condition[];       // Must stay true throughout
  failure_modes: FailureMode[];  // What can go wrong
  scope: Scope;                  // Context where valid
}
```

### 5.2 Condition System

```typescript
interface Condition {
  expression: string;       // Boolean expression
  language: "python" | "z3" | "custom";
  variables: Record<string, Type>;
}
```

**Example:**
```json
{
  "expression": "engine.torque <= transmission.max_torque",
  "language": "python",
  "variables": {
    "engine.torque": "number",
    "transmission.max_torque": "number"
  }
}
```

### 5.3 Failure Modes

```typescript
interface FailureMode {
  condition: Condition;       // When this fails
  impact: ImpactLevel;        // Severity
  detectability: number;      // 0.0-1.0 (how easily caught)
  mitigation?: string[];      // How to prevent/fix
  blast_radius?: UUID[];      // What else fails
}
```

---

## 6. Assumption Schema

### 6.1 Assumption Definition

Explicit tracking of uncertain beliefs:

```typescript
interface Assumption {
  id: UUID;
  statement: string;              // Human-readable
  confidence: number;             // 0.0-1.0
  evidence: Evidence[];
  expiry_date?: DateTime;         // When to re-validate
  owner: UUID;                    // Who made this assumption
  impact_if_false: ImpactAssessment;
  alternatives?: string[];        // Other possible values
  created_at: DateTime;
}
```

### 6.2 Impact Assessment

```typescript
interface ImpactAssessment {
  affected_entities: UUID[];
  cost_impact?: Money;
  time_impact?: Duration;
  risk_level: "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";
  invalidated_plans?: UUID[];
  required_actions?: string[];
}
```

**Example:**
```json
{
  "statement": "Supplier X delivers within 14 days",
  "confidence": 0.85,
  "evidence": ["last_6_months_avg", "supplier_contract_2025"],
  "expiry_date": "2026-06-30",
  "impact_if_false": {
    "time_impact": "+3 weeks",
    "cost_impact": "$12,000",
    "risk_level": "HIGH",
    "required_actions": ["find_alternative_supplier", "expedite_shipping"]
  }
}
```

---

## 7. Provenance Model

### 7.1 Provenance Definition

Trust infrastructure for every assertion:

```typescript
interface Provenance {
  source: Source;
  evidence: Evidence[];
  confidence: number;          // 0.0-1.0
  asserted_by: UUID;           // User/system
  asserted_at: DateTime;
  last_validated?: DateTime;
  validation_method?: ValidationMethod;
  scope?: Scope;
  conflicts?: UUID[];          // Other provenances this contradicts
}
```

### 7.2 Source Types

```typescript
enum Source {
  USER_INPUT = "user_input",           // Manual entry
  DOC_IMPORT = "doc_import",           // Extracted from docs
  MEASUREMENT = "measurement",         // Empirical observation
  TEMPLATE = "template",               // Domain pack default
  COMMUNITY = "community",             // Crowd-sourced
  INFERRED = "inferred",               // Derived by system
  EXTERNAL_API = "external_api"        // Third-party data
}
```

### 7.3 Evidence Structure

```typescript
interface Evidence {
  type: "document" | "measurement" | "historical" | "expert";
  reference: string;           // URL, citation, identifier
  excerpt?: string;            // Relevant quote
  timestamp?: DateTime;
  confidence_contribution: number;  // How much this adds to confidence
}
```

### 7.4 Confidence Propagation

**Rules for confidence through chains:**
- Single path: Use minimum confidence in chain
- Multiple paths: Use maximum confidence across paths
- Conflicts: Reduce confidence based on disagreement

*Note: Detailed propagation algorithm TBD in implementation phase*

---

## 8. Version Control

### 8.1 Commit Model

```typescript
interface Commit {
  id: UUID;
  parent?: UUID;               // Parent commit (null for initial)
  author: UUID;
  message: string;
  timestamp: DateTime;
  changeset: ChangeSet;
  signature?: string;          // Cryptographic (future)
}
```

### 8.2 ChangeSet Structure

```typescript
interface ChangeSet {
  added: {
    entities?: Entity[];
    relations?: Relation[];
    constraints?: Constraint[];
  };
  removed: {
    entity_ids?: UUID[];
    relation_ids?: UUID[];
    constraint_ids?: UUID[];
  };
  modified: {
    entities?: EntityChange[];
    relations?: RelationChange[];
    constraints?: ConstraintChange[];
  };
}
```

### 8.3 Branch and Tag

```typescript
interface Branch {
  id: UUID;
  name: string;
  head: UUID;                  // Current commit
  scenario?: Scenario;         // "What-if" parameters
  created_at: DateTime;
}

interface Tag {
  id: UUID;
  name: string;
  commit: UUID;
  verified: boolean;           // Community verification
  created_at: DateTime;
}
```

### 8.4 Diff Calculation

```typescript
interface Diff {
  from_commit: UUID;
  to_commit: UUID;
  structural_diff: ChangeSet;
  impact_assessment: ImpactAssessment;
  blast_radius: UUID[];        // Affected entities
  invalidated_plans?: UUID[];
}
```

---

## 9. Domain Packs

### 9.1 Domain Pack Structure

```typescript
interface DomainPack {
  name: string;
  version: string;
  description: string;
  ontology: Ontology;
  constraint_templates: ConstraintTemplate[];
  scoring_weights: ScoringWeights;
  validated_library: ValidatedLibrary;
  importers: Importer[];
  exporters: Exporter[];
  canonical_examples: Example[];
}
```

### 9.2 Ontology Definition

```typescript
interface Ontology {
  entity_types: EntityTypeDefinition[];
  relation_types: RelationTypeDefinition[];
  constraint_types?: ConstraintTypeDefinition[];  // Domain-specific
}
```

### 9.3 Validated Library

Pre-verified dependencies with provenance:

```typescript
interface ValidatedLibrary {
  relations: Map<string, Relation>;     // Key: "from_id:to_id"
  confidence_threshold: number;         // Minimum to include
  verification_method: string;
  last_updated: DateTime;
  contributors: UUID[];
}
```

---

## 10. Operations

### 10.1 Core Operations (Must Support)

All implementations MUST support these primitive operations.

#### 10.1.1 Create Operations
```typescript
/**
 * Create a new entity in the graph
 * @throws EntityAlreadyExists if entity.id already present
 * @throws ValidationError if entity schema invalid
 */
create_entity(entity: Entity): Result<UUID, Error>

/**
 * Create a new relation between entities
 * @throws EntityNotFound if from/to entities don't exist
 * @throws ValidationError if relation schema invalid
 * @throws CycleDetected if creates circular dependency (optional check)
 */
create_relation(relation: Relation): Result<UUID, Error>

/**
 * Create a new constraint
 * @throws EntityNotFound if referenced entities don't exist
 * @throws ValidationError if constraint parameters invalid
 * @throws ConflictDetected if contradicts existing constraint (optional)
 */
create_constraint(constraint: Constraint): Result<UUID, Error>
```

#### 10.1.2 Read Operations
```typescript
/**
 * Retrieve entity by ID
 * @throws EntityNotFound if ID doesn't exist
 */
get_entity(id: UUID): Result<Entity, EntityNotFound>

/**
 * Get all relations for an entity
 * @param direction - "in" (incoming), "out" (outgoing), "both"
 * @param types - Optional filter by relation types
 */
get_relations(
  entity_id: UUID, 
  direction: "in" | "out" | "both",
  types?: RelationType[]
): Result<Relation[], Error>

/**
 * Get constraints involving entities
 * @param entity_ids - Entities to find constraints for
 * @param recursive - Include transitive dependencies
 */
get_constraints(
  entity_ids: UUID[],
  recursive?: boolean
): Result<Constraint[], Error>

/**
 * Get entity provenance and validation history
 */
get_provenance(id: UUID): Result<Provenance, Error>
```

#### 10.1.3 Update Operations
```typescript
/**
 * Update entity properties
 * @throws EntityNotFound if ID doesn't exist
 * @throws ValidationError if changes invalid
 * @emits EntityUpdated event with changeset
 */
update_entity(
  id: UUID, 
  changes: Partial<Entity>
): Result<Entity, Error>

/**
 * Update relation properties (strength, contract, etc)
 * @throws RelationNotFound if ID doesn't exist
 * @emits RelationUpdated event
 */
update_relation(
  id: UUID, 
  changes: Partial<Relation>
): Result<Relation, Error>

/**
 * Update constraint parameters
 * @throws ConstraintNotFound if ID doesn't exist
 * @emits ConstraintUpdated event
 */
update_constraint(
  id: UUID,
  changes: Partial<Constraint>
): Result<Constraint, Error>
```

#### 10.1.4 Delete Operations
```typescript
/**
 * Delete entity and optionally cascade
 * @param cascade - If true, delete dependent relations/constraints
 * @throws EntityHasDependencies if cascade=false and dependencies exist
 * @emits EntityDeleted event
 */
delete_entity(
  id: UUID, 
  cascade?: boolean
): Result<void, Error>

/**
 * Delete relation
 * @emits RelationDeleted event
 */
delete_relation(id: UUID): Result<void, Error>

/**
 * Delete constraint
 * @emits ConstraintDeleted event
 */
delete_constraint(id: UUID): Result<void, Error>
```

---

### 10.2 Graph Operations (GraphOps)

Algorithms for dependency analysis and graph traversal.

```typescript
/**
 * Detect strongly connected components (cycles)
 * @returns Array of SCCs, each containing cycle entities
 * @algorithm Tarjan's SCC (O(V+E))
 */
detect_cycles(): Result<SCC[], Error>

interface SCC {
  entities: UUID[];
  relations: UUID[];
  is_simple_cycle: boolean;  // true if exactly one cycle path
}

/**
 * Topological sort of dependency graph
 * @returns Ordered list of entities (dependencies first)
 * @throws CycleDetected if graph contains cycles
 * @algorithm Kahn's algorithm (O(V+E))
 */
topological_sort(): Result<UUID[], CycleDetected>

/**
 * Calculate blast radius (downstream impact)
 * @param changed - Entities that changed
 * @param max_depth - Limit traversal depth (optional)
 * @returns All transitively affected entities
 */
blast_radius(
  changed: UUID[],
  max_depth?: number
): Result<BlastRadiusResult, Error>

interface BlastRadiusResult {
  affected: UUID[];              // All impacted entities
  by_depth: Map<number, UUID[]>; // Entities by distance
  critical: UUID[];              // High-impact entities
  estimated_cost?: number;       // If cost metadata available
}

/**
 * Find critical path between entities
 * @returns Longest path (scheduling) or highest-priority path
 * @throws NoPathExists if no dependency chain
 */
critical_path(
  start: UUID, 
  end: UUID
): Result<Path, NoPathExists>

interface Path {
  entities: UUID[];
  relations: UUID[];
  total_duration?: Duration;
  bottlenecks: UUID[];  // Slowest entities on path
}

/**
 * Reachability query
 * @returns true if path exists from source to target
 */
is_reachable(
  source: UUID, 
  target: UUID,
  max_hops?: number
): boolean

/**
 * Shortest path (fewest hops)
 * @algorithm BFS (O(V+E))
 */
shortest_path(
  source: UUID,
  target: UUID
): Result<Path, NoPathExists>
```

---

### 10.3 Solver Operations (PlanOps)

Constraint solving and plan validation.

```typescript
/**
 * Solve constraint satisfaction problem
 * @param entities - Entities to schedule/allocate
 * @param constraints - Constraints to satisfy
 * @param objectives - Optimization goals (soft constraints)
 * @returns Valid solution or explanation of infeasibility
 */
solve(
  entities: Entity[],
  constraints: Constraint[],
  objectives: Objective[]
): Result<Solution, Infeasible>

interface Solution {
  assignments: Map<UUID, Assignment>;  // Entity → state/time/resource
  objective_value: number;             // Optimization score
  solver_stats: SolverStats;
  proof_certificate?: Certificate;     // Formal proof (future)
}

interface Assignment {
  entity: UUID;
  start_time?: DateTime;
  end_time?: DateTime;
  resources?: Map<UUID, number>;
  state?: any;
}

interface Infeasible {
  reason: "overconstrained" | "conflicting" | "unbounded";
  minimal_unsat_core: Constraint[];   // Smallest conflicting set
  explanation: string;                // Human-readable
  relaxation_suggestions?: Relaxation[];
}

interface Relaxation {
  constraint: UUID;
  old_value: any;
  new_value: any;
  impact: "small" | "medium" | "large";
}

/**
 * Validate if plan satisfies all constraints
 * @param plan - Proposed entity assignments
 * @returns Validation result with violations
 */
validate_plan(plan: Plan): ValidationResult

interface Plan {
  assignments: Map<UUID, Assignment>;
}

interface ValidationResult {
  is_valid: boolean;
  violations: Violation[];
  warnings: Warning[];
}

interface Violation {
  constraint: Constraint;
  entities: UUID[];
  severity: "hard" | "soft" | "preference";
  message: string;
}

/**
 * Explain why constraints cannot be satisfied
 * @returns Minimal unsat core + explanations
 * @algorithm Deletion-based MUS extraction or Z3 unsat core
 */
explain_infeasibility(
  constraints: Constraint[]
): MinimalUnsatCore

interface MinimalUnsatCore {
  core_constraints: Constraint[];  // Smallest conflicting subset
  conflict_graph: ConflictGraph;   // Visual representation
  narrative_explanation: string;   // "X requires Y, but Y is blocked by Z"
  resolution_strategies: string[];
}

/**
 * Generate alternative valid plans
 * @param count - Number of alternatives to return
 * @param diversity_factor - 0.0-1.0 (how different solutions should be)
 */
generate_alternatives(
  entities: Entity[],
  constraints: Constraint[],
  count: number,
  diversity_factor?: number
): Result<Solution[], Error>
```

---

### 10.4 Version Operations (VersionOps)

Git-like operations for dependency state management.

```typescript
/**
 * Commit current state to version history
 * @param message - Commit message (conventional commit format)
 * @param changeset - What changed since last commit
 * @emits CommitCreated event
 */
commit(
  message: string, 
  changeset: ChangeSet
): Result<Commit, Error>

/**
 * Create new branch for "what-if" scenarios
 * @param scenario - Parameters for alternate reality
 */
branch(
  name: string, 
  scenario?: Scenario
): Result<Branch, Error>

interface Scenario {
  changed_entities?: Map<UUID, Partial<Entity>>;
  changed_constraints?: Map<UUID, Partial<Constraint>>;
  description: string;
}

/**
 * Merge two branches
 * @returns Commit if successful, Conflict if incompatible
 */
merge(
  from_branch: UUID, 
  to_branch: UUID,
  strategy?: "ours" | "theirs" | "manual"
): Result<Commit, Conflict>

interface Conflict {
  entity_conflicts: EntityConflict[];
  constraint_conflicts: ConstraintConflict[];
  resolution_required: boolean;
}

/**
 * Calculate structural and semantic diff
 * @returns Comprehensive change analysis
 */
diff(
  from_commit: UUID, 
  to_commit: UUID
): Result<Diff, Error>

interface Diff {
  structural_diff: ChangeSet;
  impact_assessment: ImpactAssessment;
  blast_radius: UUID[];
  invalidated_plans?: UUID[];
  estimated_effort?: Duration;
}

/**
 * Create lockfile (pinned dependency state)
 * @returns Snapshot with hashes for verification
 */
lockfile_snapshot(): Lockfile

interface Lockfile {
  commit: UUID;
  entities: Map<UUID, EntitySnapshot>;
  relations: Map<UUID, RelationSnapshot>;
  hash: string;  // Cryptographic hash of entire state
  created_at: DateTime;
}

/**
 * Restore state from lockfile
 * @throws HashMismatch if lockfile tampered
 */
restore_from_lockfile(lockfile: Lockfile): Result<void, Error>
```

---

### 10.5 Explanation Operations (ExplainOps)

Human-readable explanations of decisions and failures.

```typescript
/**
 * Explain why entity has specific dependencies
 * @returns Narrative explanation with evidence
 */
explain_why(
  entity: UUID,
  question: "depends_on" | "blocks" | "enables" | "conflicts_with",
  target: UUID
): Explanation

interface Explanation {
  narrative: string;
  evidence: Evidence[];
  confidence: number;
  alternative_interpretations?: string[];
}

/**
 * Explain why entity cannot be in state/time/resource
 * @returns Violated constraints and suggestions
 */
explain_why_not(
  entity: UUID,
  proposed_state: Assignment
): Explanation

/**
 * Suggest alternatives when constraints conflict
 * @returns Ranked list of resolutions
 */
suggest_alternatives(
  infeasible: Infeasible
): Alternative[]

interface Alternative {
  description: string;
  constraints_relaxed: UUID[];
  impact: ImpactAssessment;
  feasibility_score: number;  // 0.0-1.0
}
```

---

### 10.6 Provenance Operations

Trust and evidence tracking.

```typescript
/**
 * Record evidence for assertion
 * @param target - Entity, Relation, or Constraint ID
 * @param evidence - Supporting documentation/measurement
 */
add_evidence(
  target: UUID,
  evidence: Evidence
): Result<void, Error>

/**
 * Validate assertion against evidence
 * @returns Updated confidence score
 */
validate_assertion(
  target: UUID,
  method: ValidationMethod
): Result<number, Error>  // Returns confidence 0.0-1.0

/**
 * Detect conflicting assertions
 * @returns Conflicts requiring resolution
 */
detect_conflicts(
  scope?: Scope
): Result<Conflict[], Error>

/**
 * Propagate confidence through dependency chains
 * @algorithm Minimum confidence in chain
 */
propagate_confidence(
  entity: UUID
): Result<number, Error>
```

---

### 10.7 Query Operations

High-level queries for common patterns.

```typescript
/**
 * Find all entities of type matching criteria
 */
find_entities(
  type: EntityType,
  filters?: Record<string, any>
): Result<Entity[], Error>

/**
 * Find broken dependencies (references to missing entities)
 */
find_broken_dependencies(): Result<BrokenDependency[], Error>

interface BrokenDependency {
  relation: Relation;
  missing_entity: UUID;
  impact: "blocking" | "degraded" | "none";
}

/**
 * Find circular dependencies
 * @returns All cycles in graph
 */
find_circular_dependencies(): Result<SCC[], Error>

/**
 * Find over-constrained entities (too many hard constraints)
 */
find_overconstrained_entities(
  threshold?: number
): Result<UUID[], Error>

/**
 * Audit trail for entity
 * @returns Complete history of changes
 */
get_audit_trail(
  entity: UUID,
  from?: DateTime,
  to?: DateTime
): Result<AuditEvent[], Error>

interface AuditEvent {
  timestamp: DateTime;
  actor: UUID;
  action: "created" | "updated" | "deleted";
  changeset: ChangeSet;
}
```

---

### 10.8 Domain Pack Operations

Loading and managing domain-specific vocabularies.

```typescript
/**
 * Register domain pack
 * @param pack - Domain-specific ontology and templates
 */
register_domain_pack(pack: DomainPack): Result<void, Error>

/**
 * Import entities from domain-specific format
 * @param format - "npm", "maven", "docker", etc.
 * @param data - Raw data to import
 */
import_from_domain(
  pack_name: string,
  format: string,
  data: any
): Result<ImportResult, Error>

interface ImportResult {
  entities_created: number;
  relations_created: number;
  constraints_applied: number;
  warnings: Warning[];
}

/**
 * Export to domain-specific format
 * @param format - Target format
 */
export_to_domain(
  pack_name: string,
  format: string,
  entity_ids: UUID[]
): Result<any, Error>
```

---

## 11. Serialization Format

### 11.1 Primary Format: JSON

All TessIR objects MUST be serializable to JSON.

**Example Entity:**
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "type": "package",
  "name": "express",
  "version": "4.18.2",
  "metadata": {
    "language": "javascript",
    "license": "MIT"
  },
  "created_at": "2026-01-19T10:30:00Z"
}
```

### 11.2 Compact Binary Format (Future)

For high-performance scenarios, define Protocol Buffers schema.

### 11.3 Human-Readable Format (YAML)

For documentation and hand-editing:
```yaml
entity:
  type: package
  name: express
  version: 4.18.2
  metadata:
    language: javascript
    license: MIT
```

---

## 12. Conformance

### 12.1 Conformance Levels

**Level 1 (Minimal):**
- Entities, Relations, Basic Constraints
- Core operations (CRUD)
- JSON serialization

**Level 2 (Standard):**
- Full constraint system (20+ types)
- Provenance tracking
- Graph operations
- Version control (commits, branches)

**Level 3 (Full):**
- Solver integration
- Proof certificates
- Domain packs
- All operations

### 12.2 Conformance Testing

Implementations MUST pass canonical test suite (50 scenarios).

---

## 13. Complete Examples

This section demonstrates TessIR in action across five diverse domains. Each example shows entities, relations, constraints, and how solving/validation works.

---

### 13.1 Example 1: Software Development (npm Dependency Hell)

**Scenario:** A Node.js application with conflicting package version requirements.

#### Entities
```json
{
  "entities": [
    {
      "id": "app",
      "type": "package",
      "name": "my-web-app",
      "version": "1.0.0"
    },
    {
      "id": "react",
      "type": "package",
      "name": "react",
      "version": "18.2.0"
    },
    {
      "id": "react-router",
      "type": "package",
      "name": "react-router-dom",
      "version": "6.8.0"
    },
    {
      "id": "old-plugin",
      "type": "package",
      "name": "legacy-react-plugin",
      "version": "2.1.0"
    }
  ]
}
```

#### Relations
```json
{
  "relations": [
    {
      "type": "requires",
      "from_entity": "app",
      "to_entity": "react",
      "strength": 1.0,
      "provenance": {
        "source": "doc_import",
        "confidence": 1.0,
        "reference": "package.json"
      }
    },
    {
      "type": "requires",
      "from_entity": "app",
      "to_entity": "react-router",
      "strength": 1.0
    },
    {
      "type": "requires",
      "from_entity": "app",
      "to_entity": "old-plugin",
      "strength": 1.0
    },
    {
      "type": "requires",
      "from_entity": "react-router",
      "to_entity": "react",
      "strength": 1.0,
      "contract": {
        "preconditions": ["react.version >= 16.8.0"],
        "postconditions": [],
        "invariants": [],
        "failure_modes": []
      }
    },
    {
      "type": "requires",
      "from_entity": "old-plugin",
      "to_entity": "react",
      "strength": 1.0,
      "contract": {
        "preconditions": ["react.version >= 16.0.0", "react.version < 17.0.0"],
        "postconditions": [],
        "invariants": [],
        "failure_modes": [
          {
            "condition": "react.version >= 17.0.0",
            "impact": "high",
            "detectability": 1.0,
            "mitigation": ["upgrade legacy-react-plugin", "use compatibility shim"]
          }
        ]
      }
    }
  ]
}
```

#### Constraints
```json
{
  "constraints": [
    {
      "type": "choice",
      "entities": ["react"],
      "min_select": 1,
      "max_select": 1,
      "priority": "hard",
      "note": "Only one React version allowed"
    },
    {
      "type": "interface_compatibility",
      "entity": "react-router",
      "interface": {
        "signature": "React",
        "min_version": "16.8.0"
      },
      "strict": false,
      "priority": "hard"
    },
    {
      "type": "interface_compatibility",
      "entity": "old-plugin",
      "interface": {
        "signature": "React",
        "min_version": "16.0.0",
        "max_version": "16.99.99"
      },
      "strict": true,
      "priority": "hard"
    }
  ]
}
```

#### Solve Result
```json
{
  "result": "infeasible",
  "minimal_unsat_core": [
    {
      "type": "interface_compatibility",
      "entity": "react-router",
      "note": "requires React 16.8+"
    },
    {
      "type": "interface_compatibility",
      "entity": "old-plugin",
      "note": "requires React <17.0"
    },
    {
      "type": "choice",
      "note": "only one React version allowed"
    }
  ],
  "explanation": "react-router requires React 16.8+, old-plugin requires React <17.0, but React 18.2.0 is specified. No React version satisfies both constraints.",
  "relaxation_suggestions": [
    {
      "description": "Upgrade old-plugin to version 3.0 (supports React 18)",
      "impact": "medium",
      "constraints_relaxed": ["old-plugin version constraint"]
    },
    {
      "description": "Downgrade React to 16.14.0",
      "impact": "large",
      "constraints_relaxed": ["react version"]
    },
    {
      "description": "Remove old-plugin dependency",
      "impact": "large",
      "constraints_relaxed": ["app requires old-plugin"]
    }
  ]
}
```

---

### 13.2 Example 2: IT Operations (Database Migration)

**Scenario:** Zero-downtime migration from PostgreSQL 13 to 15 with replica synchronization.

#### Entities
```json
{
  "entities": [
    {
      "id": "pg13-primary",
      "type": "database",
      "name": "PostgreSQL 13 Primary",
      "metadata": {
        "host": "prod-db-01",
        "port": 5432,
        "version": "13.8"
      }
    },
    {
      "id": "pg13-replica",
      "type": "database",
      "name": "PostgreSQL 13 Replica",
      "metadata": {
        "host": "prod-db-02",
        "replication_lag": "< 100ms"
      }
    },
    {
      "id": "pg15-primary",
      "type": "database",
      "name": "PostgreSQL 15 Primary",
      "metadata": {
        "host": "prod-db-03"
      }
    },
    {
      "id": "pg15-replica",
      "type": "database",
      "name": "PostgreSQL 15 Replica",
      "metadata": {
        "host": "prod-db-04"
      }
    },
    {
      "id": "data-sync",
      "type": "task",
      "name": "Logical Replication Setup"
    },
    {
      "id": "cutover",
      "type": "task",
      "name": "Application Cutover"
    },
    {
      "id": "validation",
      "type": "task",
      "name": "Data Validation"
    }
  ]
}
```

#### Constraints
```json
{
  "constraints": [
    {
      "type": "precedence",
      "before": "data-sync",
      "after": "validation",
      "priority": "hard"
    },
    {
      "type": "precedence",
      "before": "validation",
      "after": "cutover",
      "priority": "hard"
    },
    {
      "type": "time_window",
      "entity": "cutover",
      "earliest": "2026-01-26T02:00:00Z",
      "latest": "2026-01-26T04:00:00Z",
      "priority": "hard",
      "note": "Maintenance window"
    },
    {
      "type": "duration",
      "entity": "data-sync",
      "min_duration": "24 hours",
      "priority": "hard",
      "note": "Full initial sync"
    },
    {
      "type": "duration",
      "entity": "cutover",
      "max_duration": "5 minutes",
      "priority": "hard",
      "note": "Minimal downtime"
    },
    {
      "type": "synchronization",
      "entities": ["pg13-primary", "pg15-primary"],
      "tolerance": "1 second",
      "priority": "hard",
      "note": "Zero data loss cutover"
    },
    {
      "type": "mutex",
      "entities": ["pg13-primary", "pg15-primary"],
      "scope": "time",
      "priority": "hard",
      "note": "Only one primary at a time"
    }
  ]
}
```

#### Solve Result
```json
{
  "result": "feasible",
  "solution": {
    "assignments": {
      "data-sync": {
        "start_time": "2026-01-25T02:00:00Z",
        "end_time": "2026-01-26T02:00:00Z"
      },
      "validation": {
        "start_time": "2026-01-26T02:00:00Z",
        "end_time": "2026-01-26T02:30:00Z"
      },
      "cutover": {
        "start_time": "2026-01-26T02:30:00Z",
        "end_time": "2026-01-26T02:35:00Z"
      }
    },
    "objective_value": 0.0,
    "solver_stats": {
      "solver": "OR-Tools",
      "solve_time": "127ms",
      "nodes_explored": 43
    }
  }
}
```

---

### 13.3 Example 3: Automotive (Turbo Build Dependencies)

**Scenario:** Performance upgrade with cascading requirements and budget constraints.

#### Entities & Constraints
```json
{
  "entities": [
    {"id": "stock-engine", "type": "component", "name": "Stock Engine Block"},
    {"id": "forged-internals", "type": "component", "name": "Forged Pistons + Rods"},
    {"id": "turbo-kit", "type": "component", "name": "Garrett GTX3584RS"},
    {"id": "fuel-system", "type": "component", "name": "1000cc Injectors + Pump"},
    {"id": "tuning", "type": "task", "name": "Dyno Tuning"},
    {"id": "install", "type": "task", "name": "Installation"}
  ],
  "constraints": [
    {
      "type": "implication",
      "antecedent": "turbo-kit",
      "consequent": "fuel-system",
      "priority": "hard",
      "note": "Stock injectors insufficient for boost"
    },
    {
      "type": "conditional",
      "condition": "turbo_boost > 15psi",
      "then_constraint": {
        "type": "implication",
        "antecedent": "turbo-kit",
        "consequent": "forged-internals"
      },
      "priority": "hard",
      "note": "High boost requires internal strength"
    },
    {
      "type": "precedence",
      "before": "forged-internals",
      "after": "install",
      "priority": "hard"
    },
    {
      "type": "precedence",
      "before": "install",
      "after": "tuning",
      "priority": "hard"
    },
    {
      "type": "budget",
      "entities": ["turbo-kit", "fuel-system", "forged-internals", "tuning"],
      "max_cost": 25000,
      "currency": "USD",
      "priority": "hard"
    },
    {
      "type": "duration",
      "entity": "tuning",
      "min_duration": "2 hours",
      "max_duration": "4 hours",
      "priority": "soft"
    }
  ],
  "solve_result": "feasible",
  "total_cost": "$24,500",
  "estimated_timeline": "3 weeks",
  "warnings": [
    "Approaching budget limit",
    "Consider upgraded clutch for power handling"
  ]
}
```

---

### 13.4 Example 4: Construction (Foundation + Framing)

**Scenario:** Residential construction with weather dependencies and resource constraints.

#### Entities & Constraints
```json
{
  "entities": [
    {"id": "excavation", "type": "task", "name": "Site Excavation"},
    {"id": "forms", "type": "task", "name": "Form Installation"},
    {"id": "rebar", "type": "task", "name": "Rebar Placement"},
    {"id": "pour", "type": "task", "name": "Concrete Pour"},
    {"id": "cure", "type": "task", "name": "Concrete Curing"},
    {"id": "form-removal", "type": "task", "name": "Form Removal"},
    {"id": "framing", "type": "task", "name": "Wall Framing"},
    {"id": "concrete-truck", "type": "resource", "name": "Concrete Mixer Trucks"},
    {"id": "crew", "type": "resource", "name": "Construction Crew"}
  ],
  "constraints": [
    {
      "type": "precedence",
      "before": "excavation",
      "after": "forms",
      "priority": "hard"
    },
    {
      "type": "precedence",
      "before": "forms",
      "after": "rebar",
      "priority": "hard"
    },
    {
      "type": "precedence",
      "before": "rebar",
      "after": "pour",
      "priority": "hard"
    },
    {
      "type": "duration",
      "entity": "cure",
      "exact_duration": "3 days",
      "priority": "hard",
      "note": "Minimum cure time for structural integrity"
    },
    {
      "type": "delay",
      "from_entity": "pour",
      "to_entity": "form-removal",
      "min_delay": "3 days",
      "priority": "hard",
      "reason": "Concrete must cure"
    },
    {
      "type": "precedence",
      "before": "form-removal",
      "after": "framing",
      "priority": "hard"
    },
    {
      "type": "resource_allocation",
      "resource": "concrete-truck",
      "task": "pour",
      "amount": 3,
      "unit": "trucks",
      "required": true,
      "priority": "hard"
    },
    {
      "type": "resource_capacity",
      "resource": "crew",
      "tasks": ["forms", "rebar", "pour", "framing"],
      "max_concurrent": 1,
      "priority": "hard",
      "note": "Single crew team"
    },
    {
      "type": "conditional",
      "condition": "temperature < 40F",
      "then_constraint": {
        "type": "negation",
        "entity": "pour",
        "reason": "Concrete freeze risk"
      },
      "priority": "hard"
    }
  ],
  "timeline": {
    "excavation": "Day 1",
    "forms": "Day 2",
    "rebar": "Day 3",
    "pour": "Day 4 (if temp > 40F)",
    "cure": "Days 5-7",
    "form-removal": "Day 8",
    "framing": "Days 9-12"
  }
}
```

---

### 13.5 Example 5: Supply Chain (Just-In-Time Manufacturing)

**Scenario:** Automotive parts assembly with supplier dependencies and lead times.

#### Entities & Constraints
```json
{
  "entities": [
    {"id": "chassis-assembly", "type": "task", "name": "Chassis Assembly"},
    {"id": "engine-install", "type": "task", "name": "Engine Installation"},
    {"id": "paint", "type": "task", "name": "Paint Process"},
    {"id": "final-assembly", "type": "task", "name": "Final Assembly"},
    {"id": "supplier-a", "type": "resource", "name": "Engine Supplier"},
    {"id": "supplier-b", "type": "resource", "name": "Chassis Supplier"},
    {"id": "paint-booth", "type": "resource", "name": "Paint Booth"}
  ],
  "constraints": [
    {
      "type": "precedence",
      "before": "chassis-assembly",
      "after": "engine-install",
      "priority": "hard"
    },
    {
      "type": "precedence",
      "before": "engine-install",
      "after": "paint",
      "priority": "hard"
    },
    {
      "type": "precedence",
      "before": "paint",
      "after": "final-assembly",
      "priority": "hard"
    },
    {
      "type": "duration",
      "entity": "paint",
      "min_duration": "24 hours",
      "priority": "hard",
      "note": "Paint cure time"
    },
    {
      "type": "resource_capacity",
      "resource": "paint-booth",
      "tasks": ["paint"],
      "max_concurrent": 2,
      "priority": "hard"
    },
    {
      "type": "throughput",
      "entity": "final-assembly",
      "max_rate": 50,
      "unit": "vehicles per day",
      "priority": "soft"
    },
    {
      "type": "time_window",
      "entity": "chassis-assembly",
      "earliest": "2026-01-27T06:00:00Z",
      "latest": "2026-01-27T14:00:00Z",
      "priority": "soft",
      "note": "Supplier A delivery window"
    }
  ],
  "assumptions": [
    {
      "statement": "Supplier A delivers within 2-week lead time",
      "confidence": 0.85,
      "evidence": [
        {"type": "historical", "reference": "last_6_months_avg"}
      ],
      "impact_if_false": {
        "time_impact": "+3 weeks",
        "cost_impact": "$50,000",
        "risk_level": "HIGH",
        "required_actions": ["find_alternative_supplier", "air_freight"]
      }
    }
  ]
}
```

---

## Status & Next Steps

**Current Status:** DRAFT (Significant progress - Phase 0 Week 1)

**Phase 0 Deliverables:**
- [x] Complete constraint type taxonomy (28 types across 4 categories)
- [x] Define all core operations precisely (40+ operations across 8 categories)
- [x] Write 5 complete cross-domain examples
- [ ] Finalize confidence propagation algorithm
- [ ] Peer review + public feedback

**Completed This Session (2026-01-22):**
- ✅ CONSTRAINT_TAXONOMY_V1.md created (28 types, formal definitions, cross-domain examples)
- ✅ Section 4 (Constraint System) expanded with taxonomy reference and solver mapping
- ✅ Section 10 (Operations) fully specified with TypeScript signatures and error handling
- ✅ Section 13 (Complete Examples) added with 5 diverse domain examples

**Remaining Work for Phase 0:**
- Confidence propagation algorithm (section 7.4) - precise mathematical specification
- Peer review coordination (GPT, Gemini, community feedback)
- Canonical test suite creation (50 scenarios) - separate effort
- ADR-001 through ADR-005 - formal architecture decision records

**Quality Metrics:**
- Constraint types: 28 (target: 20-30) ✅
- Operations defined: 40+ (target: comprehensive) ✅
- Examples: 5 domains (target: 5) ✅
- Specification completeness: ~75% (target: 90% for Phase 0 end)

**Future Versions:**
- **v1.1:** Add probabilistic constraints, stochastic solving
- **v1.2:** Add temporal logic, time-series dependencies
- **v2.0:** Add machine learning integration, pattern inference

---

## References

- [DNA.md](../DNA.md) - Project principles
- [ARCHITECTURE.md](ARCHITECTURE.md) - System architecture
- [Genius Council Synthesis](../GCsynth2%20-%20Genius%20Council%20Synthesis.md) - Strategic reviews

---

**Contributors:**
- David Kirsch (Author)
- GPT-4 (Genius Council - Architecture review)
- Gemini 2.0 (Genius Council - Technical recommendations)
- Claude (Anthropic - Synthesis and refinement)

**Last Updated:** 2026-01-19  
**Next Review:** After canonical test suite creation
