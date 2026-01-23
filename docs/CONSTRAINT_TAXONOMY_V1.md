# TessIR Constraint Taxonomy v1.0
**Complete Classification of Constraint Types**

**Status:** DRAFT (Phase 0 - Week 1)  
**Version:** 1.0.0-draft  
**Last Updated:** 2026-01-22  
**Authors:** David Kirsch, Claude

---

## Overview

This document provides the complete taxonomy of constraint types supported in TessIR v1.0. Each constraint type is classified by category, defined formally, and illustrated with real-world examples across multiple domains.

**Design Principles:**
1. **Composability:** Constraints can be combined to express complex rules
2. **Domain-Agnostic:** Types work across software, operations, manufacturing, construction
3. **Formally Verifiable:** Each type has clear semantics for constraint solvers
4. **Extensible:** Domain Packs can add specialized subtypes

**Total Count:** 28 core constraint types across 4 categories

---

## Category 1: Temporal Constraints (8 types)

Temporal constraints govern the timing and sequencing of entities.

### T1: Precedence
**Definition:** Entity A must complete before entity B starts.

**Parameters:**
```typescript
{
  before: UUID;              // Entity that must finish first
  after: UUID;               // Entity that must start after
  min_gap?: Duration;        // Minimum time between (optional)
  max_gap?: Duration;        // Maximum time between (optional)
}
```

**Example - Software Development:**
```json
{
  "type": "precedence",
  "before": "unit_tests",
  "after": "integration_tests",
  "min_gap": "0s",
  "priority": "hard"
}
```

**Example - Construction:**
```json
{
  "type": "precedence",
  "before": "foundation_pour",
  "after": "framing",
  "min_gap": "3 days",
  "priority": "hard",
  "note": "Concrete must cure"
}
```

---

### T2: Time Window
**Definition:** Entity must occur within specified temporal bounds.

**Parameters:**
```typescript
{
  entity: UUID;
  earliest: DateTime;        // Cannot start before this
  latest: DateTime;          // Cannot finish after this
}
```

**Example - IT Operations:**
```json
{
  "type": "time_window",
  "entity": "database_migration",
  "earliest": "2026-01-25T02:00:00Z",
  "latest": "2026-01-25T04:00:00Z",
  "priority": "hard",
  "note": "Maintenance window"
}
```

**Example - Supply Chain:**
```json
{
  "type": "time_window",
  "entity": "perishable_delivery",
  "earliest": "2026-01-22T06:00:00Z",
  "latest": "2026-01-22T12:00:00Z",
  "priority": "hard",
  "note": "Before spoilage"
}
```

---

### T3: Duration
**Definition:** Entity must take exactly, at least, or at most a specified duration.

**Parameters:**
```typescript
{
  entity: UUID;
  min_duration?: Duration;   // Minimum time required
  max_duration?: Duration;   // Maximum time allowed
  exact_duration?: Duration; // Precise time (mutually exclusive with min/max)
}
```

**Example - Manufacturing:**
```json
{
  "type": "duration",
  "entity": "paint_curing",
  "min_duration": "24 hours",
  "priority": "hard",
  "note": "Full cure time"
}
```

**Example - Automotive:**
```json
{
  "type": "duration",
  "entity": "dyno_tuning",
  "min_duration": "2 hours",
  "max_duration": "4 hours",
  "priority": "soft",
  "note": "Typical tuning session"
}
```

---

### T4: Deadline
**Definition:** Entity must complete by absolute time (hard cutoff).

**Parameters:**
```typescript
{
  entity: UUID;
  deadline: DateTime;        // Absolute completion time
  penalty?: Penalty;         // Cost/impact of missing
}
```

**Example - Project Management:**
```json
{
  "type": "deadline",
  "entity": "regulatory_filing",
  "deadline": "2026-03-31T23:59:59Z",
  "priority": "hard",
  "penalty": {
    "type": "financial",
    "amount": "$50000/day"
  }
}
```

---

### T5: Delay
**Definition:** Minimum gap between entity completion and another entity's start.

**Parameters:**
```typescript
{
  from_entity: UUID;
  to_entity: UUID;
  min_delay: Duration;       // Enforced gap
  reason?: string;
}
```

**Example - Construction:**
```json
{
  "type": "delay",
  "from_entity": "concrete_pour",
  "to_entity": "form_removal",
  "min_delay": "48 hours",
  "priority": "hard",
  "reason": "Structural integrity"
}
```

**Example - Software Deployment:**
```json
{
  "type": "delay",
  "from_entity": "canary_deployment",
  "to_entity": "full_rollout",
  "min_delay": "4 hours",
  "priority": "soft",
  "reason": "Monitor for errors"
}
```

---

### T6: Synchronization
**Definition:** Multiple entities must happen simultaneously (within tolerance).

**Parameters:**
```typescript
{
  entities: UUID[];          // All must sync
  tolerance?: Duration;      // Acceptable drift
  anchor?: UUID;             // Primary entity to sync to (optional)
}
```

**Example - Manufacturing:**
```json
{
  "type": "synchronization",
  "entities": ["weld_station_1", "weld_station_2", "weld_station_3"],
  "tolerance": "5 seconds",
  "priority": "soft",
  "note": "Parallel welding operations"
}
```

**Example - IT Operations:**
```json
{
  "type": "synchronization",
  "entities": ["db_primary_cutover", "db_replica_cutover"],
  "tolerance": "1 second",
  "priority": "hard",
  "note": "Zero-downtime migration"
}
```

---

### T7: Recurrence
**Definition:** Entity repeats on schedule (cron-like).

**Parameters:**
```typescript
{
  entity: UUID;
  schedule: CronExpression | Interval;
  start_date?: DateTime;
  end_date?: DateTime;
  max_occurrences?: number;
}
```

**Example - IT Operations:**
```json
{
  "type": "recurrence",
  "entity": "backup_job",
  "schedule": "0 2 * * *",
  "priority": "hard",
  "note": "Daily 2am backup"
}
```

**Example - Maintenance:**
```json
{
  "type": "recurrence",
  "entity": "oil_change",
  "schedule": "every 5000 miles",
  "priority": "soft",
  "note": "Preventive maintenance"
}
```

---

### T8: Expiration
**Definition:** Entity validity ends at specified time (temporal scope).

**Parameters:**
```typescript
{
  entity: UUID;
  expires_at: DateTime;
  grace_period?: Duration;
  consequences?: string[];
}
```

**Example - Software Development:**
```json
{
  "type": "expiration",
  "entity": "api_key_v1",
  "expires_at": "2026-12-31T23:59:59Z",
  "grace_period": "30 days",
  "consequences": ["API calls rejected", "Migration to v2 required"],
  "priority": "hard"
}
```

---

## Category 2: Resource Constraints (8 types)

Resource constraints govern allocation, capacity, and consumption.

### R1: Resource Capacity
**Definition:** Maximum concurrent usage of a resource.

**Parameters:**
```typescript
{
  resource: UUID;
  tasks: UUID[];             // Tasks competing for resource
  max_concurrent: number;    // Hard limit
  unit?: string;             // "workers", "cores", "GB", etc.
}
```

**Example - IT Operations:**
```json
{
  "type": "resource_capacity",
  "resource": "build_servers",
  "tasks": ["build_frontend", "build_backend", "build_mobile"],
  "max_concurrent": 4,
  "unit": "concurrent builds",
  "priority": "hard"
}
```

**Example - Manufacturing:**
```json
{
  "type": "resource_capacity",
  "resource": "spray_booth",
  "tasks": ["paint_car_1", "paint_car_2", "paint_car_3"],
  "max_concurrent": 1,
  "priority": "hard"
}
```

---

### R2: Resource Allocation
**Definition:** Assign specific resource quantity to task.

**Parameters:**
```typescript
{
  resource: UUID;
  task: UUID;
  amount: number;            // Quantity allocated
  unit: string;
  required: boolean;         // Task cannot proceed without
}
```

**Example - Construction:**
```json
{
  "type": "resource_allocation",
  "resource": "concrete_mixer_trucks",
  "task": "foundation_pour",
  "amount": 3,
  "unit": "trucks",
  "required": true,
  "priority": "hard"
}
```

**Example - Software Development:**
```json
{
  "type": "resource_allocation",
  "resource": "memory",
  "task": "ml_training",
  "amount": 64,
  "unit": "GB",
  "required": true,
  "priority": "hard"
}
```

---

### R3: Resource Sharing
**Definition:** Resource shared across tasks with allocation rules.

**Parameters:**
```typescript
{
  resource: UUID;
  tasks: UUID[];
  allocation_policy: "fair" | "priority" | "proportional";
  min_per_task?: number;
  max_per_task?: number;
}
```

**Example - IT Operations:**
```json
{
  "type": "resource_sharing",
  "resource": "database_connections",
  "tasks": ["api_service", "batch_jobs", "analytics"],
  "allocation_policy": "priority",
  "max_per_task": 50,
  "priority": "soft"
}
```

---

### R4: Budget
**Definition:** Total cost constraint (financial or other).

**Parameters:**
```typescript
{
  entities: UUID[];          // Entities consuming budget
  max_cost: number;
  currency: string;
  cost_model: CostModel;     // How costs accumulate
}
```

**Example - Project Management:**
```json
{
  "type": "budget",
  "entities": ["dev_hours", "cloud_costs", "third_party_services"],
  "max_cost": 250000,
  "currency": "USD",
  "priority": "hard",
  "note": "Q1 project budget"
}
```

**Example - Automotive Build:**
```json
{
  "type": "budget",
  "entities": ["turbo_kit", "fuel_system", "tuning"],
  "max_cost": 15000,
  "currency": "USD",
  "priority": "soft",
  "note": "Performance upgrade budget"
}
```

---

### R5: Throughput
**Definition:** Rate limit on entity processing.

**Parameters:**
```typescript
{
  entity: UUID;
  max_rate: number;
  unit: string;              // "per second", "per hour", etc.
  window?: Duration;         // Sliding or fixed window
}
```

**Example - IT Operations:**
```json
{
  "type": "throughput",
  "entity": "api_endpoint",
  "max_rate": 1000,
  "unit": "requests per second",
  "window": "1 second",
  "priority": "hard"
}
```

**Example - Manufacturing:**
```json
{
  "type": "throughput",
  "entity": "assembly_line",
  "max_rate": 60,
  "unit": "units per hour",
  "priority": "soft"
}
```

---

### R6: Reservation
**Definition:** Exclusive resource access for duration.

**Parameters:**
```typescript
{
  resource: UUID;
  task: UUID;
  start_time: DateTime;
  duration: Duration;
  preemptible: boolean;      // Can be interrupted
}
```

**Example - Construction:**
```json
{
  "type": "reservation",
  "resource": "crane_operator",
  "task": "steel_beam_placement",
  "start_time": "2026-01-23T08:00:00Z",
  "duration": "4 hours",
  "preemptible": false,
  "priority": "hard"
}
```

---

### R7: Utilization
**Definition:** Resource usage must stay within bounds.

**Parameters:**
```typescript
{
  resource: UUID;
  min_utilization?: number;  // Minimum usage % (efficiency)
  max_utilization?: number;  // Maximum usage % (overload)
  unit: "percent";
}
```

**Example - IT Operations:**
```json
{
  "type": "utilization",
  "resource": "database_cpu",
  "max_utilization": 80,
  "unit": "percent",
  "priority": "soft",
  "note": "Avoid query slowdown"
}
```

**Example - Manufacturing:**
```json
{
  "type": "utilization",
  "resource": "cnc_machine",
  "min_utilization": 70,
  "unit": "percent",
  "priority": "soft",
  "note": "Maximize ROI"
}
```

---

### R8: Dependency Quota
**Definition:** Limit number of dependencies per entity (complexity control).

**Parameters:**
```typescript
{
  entity: UUID;
  max_dependencies: number;
  direction: "in" | "out" | "both";
  scope?: "direct" | "transitive";
}
```

**Example - Software Development:**
```json
{
  "type": "dependency_quota",
  "entity": "microservice",
  "max_dependencies": 5,
  "direction": "out",
  "scope": "direct",
  "priority": "soft",
  "note": "Limit coupling"
}
```

---

## Category 3: Logical Constraints (7 types)

Logical constraints define boolean relationships and choices.

### L1: Mutual Exclusion (Mutex)
**Definition:** Entities cannot co-occur (mutually exclusive).

**Parameters:**
```typescript
{
  entities: UUID[];          // All mutually exclusive
  scope: "state" | "time" | "space" | "global";
}
```

**Example - Software Development:**
```json
{
  "type": "mutex",
  "entities": ["postgres_13", "postgres_14", "postgres_15"],
  "scope": "state",
  "priority": "hard",
  "note": "Single database version"
}
```

**Example - Automotive:**
```json
{
  "type": "mutex",
  "entities": ["turbo_kit", "supercharger_kit"],
  "scope": "state",
  "priority": "hard",
  "note": "Choose one forced induction method"
}
```

---

### L2: Choice
**Definition:** Exactly N of M entities must be selected.

**Parameters:**
```typescript
{
  entities: UUID[];
  min_select: number;        // At least this many
  max_select: number;        // At most this many
}
```

**Example - Construction:**
```json
{
  "type": "choice",
  "entities": ["tile_option_a", "tile_option_b", "tile_option_c"],
  "min_select": 1,
  "max_select": 1,
  "priority": "hard",
  "note": "Choose exactly one tile style"
}
```

**Example - Software Development:**
```json
{
  "type": "choice",
  "entities": ["winston", "pino", "bunyan"],
  "min_select": 1,
  "max_select": 2,
  "priority": "soft",
  "note": "Primary logger + optional fallback"
}
```

---

### L3: Conditional
**Definition:** If condition holds, then constraint applies.

**Parameters:**
```typescript
{
  condition: Condition;      // Boolean expression
  then_constraint: Constraint;
  else_constraint?: Constraint;
}
```

**Example - IT Operations:**
```json
{
  "type": "conditional",
  "condition": "environment == 'production'",
  "then_constraint": {
    "type": "precedence",
    "before": "approval",
    "after": "deployment"
  },
  "priority": "hard"
}
```

**Example - Manufacturing:**
```json
{
  "type": "conditional",
  "condition": "ambient_temp < 50F",
  "then_constraint": {
    "type": "mutex",
    "entities": ["outdoor_painting"],
    "scope": "time"
  },
  "priority": "hard"
}
```

---

### L4: Implication
**Definition:** If A occurs, then B must occur (logical implication).

**Parameters:**
```typescript
{
  antecedent: UUID;          // If this
  consequent: UUID;          // Then this
  temporal?: "before" | "after" | "concurrent" | "unspecified";
}
```

**Example - Software Development:**
```json
{
  "type": "implication",
  "antecedent": "database_migration",
  "consequent": "application_restart",
  "temporal": "after",
  "priority": "hard"
}
```

**Example - Automotive:**
```json
{
  "type": "implication",
  "antecedent": "turbo_upgrade",
  "consequent": "fuel_system_upgrade",
  "temporal": "concurrent",
  "priority": "hard",
  "note": "Stock injectors insufficient"
}
```

---

### L5: Equivalence
**Definition:** A if and only if B (bidirectional implication).

**Parameters:**
```typescript
{
  entity_a: UUID;
  entity_b: UUID;
  synchronization?: boolean; // Must happen simultaneously
}
```

**Example - IT Operations:**
```json
{
  "type": "equivalence",
  "entity_a": "feature_flag_enabled",
  "entity_b": "new_ui_active",
  "synchronization": true,
  "priority": "hard"
}
```

---

### L6: Disjunction
**Definition:** At least one of the entities must occur (logical OR).

**Parameters:**
```typescript
{
  entities: UUID[];
  min_required: number;      // Default: 1
}
```

**Example - Construction:**
```json
{
  "type": "disjunction",
  "entities": ["permit_a", "permit_b", "permit_waiver"],
  "min_required": 1,
  "priority": "hard",
  "note": "At least one authorization path"
}
```

**Example - Software Development:**
```json
{
  "type": "disjunction",
  "entities": ["unit_tests", "integration_tests", "e2e_tests"],
  "min_required": 2,
  "priority": "soft",
  "note": "Multiple test levels recommended"
}
```

---

### L7: Negation
**Definition:** Entity must not occur (prohibition).

**Parameters:**
```typescript
{
  entity: UUID;
  scope?: Scope;             // Context where prohibited
  reason?: string;
}
```

**Example - Software Development:**
```json
{
  "type": "negation",
  "entity": "eval_function",
  "scope": {
    "applies_when": ["production_environment"]
  },
  "priority": "hard",
  "reason": "Security vulnerability"
}
```

**Example - Automotive:**
```json
{
  "type": "negation",
  "entity": "race_cam",
  "scope": {
    "applies_when": ["street_legal_build"]
  },
  "priority": "hard",
  "reason": "Emissions compliance"
}
```

---

## Category 4: Structural Constraints (5 types)

Structural constraints govern hierarchies, composition, and interfaces.

### S1: Hierarchy
**Definition:** Parent-child ordering must be respected.

**Parameters:**
```typescript
{
  parent: UUID;
  children: UUID[];
  propagation: "full" | "partial" | "none";  // Constraint inheritance
}
```

**Example - Software Development:**
```json
{
  "type": "hierarchy",
  "parent": "web_application",
  "children": ["frontend", "backend", "database"],
  "propagation": "partial",
  "priority": "hard",
  "note": "Changes to parent affect children"
}
```

**Example - Manufacturing:**
```json
{
  "type": "hierarchy",
  "parent": "vehicle",
  "children": ["powertrain", "chassis", "body", "interior"],
  "propagation": "full",
  "priority": "hard"
}
```

---

### S2: Composition
**Definition:** Whole requires all specified parts (completeness).

**Parameters:**
```typescript
{
  whole: UUID;
  parts: UUID[];
  optional_parts?: UUID[];
  substitution_groups?: UUID[][];  // Alternative part sets
}
```

**Example - Construction:**
```json
{
  "type": "composition",
  "whole": "electrical_system",
  "parts": ["breaker_panel", "wiring", "outlets"],
  "optional_parts": ["solar_panels", "backup_generator"],
  "priority": "hard"
}
```

**Example - Software Development:**
```json
{
  "type": "composition",
  "whole": "authentication_service",
  "parts": ["user_db", "token_service", "password_hasher"],
  "substitution_groups": [
    ["bcrypt_hasher", "argon2_hasher"]
  ],
  "priority": "hard"
}
```

---

### S3: Encapsulation
**Definition:** Internal entities hidden from external dependencies.

**Parameters:**
```typescript
{
  container: UUID;
  internal_entities: UUID[];
  exposed_interface: UUID[];
}
```

**Example - Software Development:**
```json
{
  "type": "encapsulation",
  "container": "payment_module",
  "internal_entities": ["stripe_client", "payment_db", "retry_logic"],
  "exposed_interface": ["process_payment", "refund_payment"],
  "priority": "hard",
  "note": "Internal implementation can change"
}
```

---

### S4: Interface Compatibility
**Definition:** Entity must satisfy interface contract (type checking).

**Parameters:**
```typescript
{
  entity: UUID;
  interface: InterfaceDefinition;
  strict: boolean;           // Allow subtype or exact match only
}
```

**Example - Software Development:**
```json
{
  "type": "interface_compatibility",
  "entity": "database_driver",
  "interface": {
    "methods": ["connect", "query", "close"],
    "signature": "Database"
  },
  "strict": false,
  "priority": "hard"
}
```

**Example - Manufacturing:**
```json
{
  "type": "interface_compatibility",
  "entity": "replacement_part",
  "interface": {
    "dimensions": "100mm x 50mm",
    "bolt_pattern": "M8 x 4",
    "voltage": "12V"
  },
  "strict": true,
  "priority": "hard"
}
```

---

### S5: Cardinality
**Definition:** Entity relationship count constraints (1-to-many, etc).

**Parameters:**
```typescript
{
  from_entity: UUID;
  to_entity: UUID;
  min_count: number;
  max_count: number | "unbounded";
  relationship: RelationType;
}
```

**Example - Software Development:**
```json
{
  "type": "cardinality",
  "from_entity": "user",
  "to_entity": "api_key",
  "min_count": 1,
  "max_count": 5,
  "relationship": "owns",
  "priority": "hard"
}
```

**Example - IT Operations:**
```json
{
  "type": "cardinality",
  "from_entity": "load_balancer",
  "to_entity": "backend_server",
  "min_count": 2,
  "max_count": "unbounded",
  "relationship": "distributes_to",
  "priority": "hard",
  "note": "High availability"
}
```

---

## Constraint Priority System

All constraints have a priority level that determines solver behavior:

```typescript
enum Priority {
  HARD = "hard",       // MUST be satisfied (plan fails if violated)
  SOFT = "soft",       // SHOULD be satisfied (optimize to minimize violations)
  PREFERENCE = "pref"  // NICE to satisfy (lowest priority optimization)
}
```

**Solver Behavior:**
- **Hard:** Infeasible if violated (search terminates)
- **Soft:** Objective function penalty (search continues)
- **Preference:** Tiebreaker when multiple solutions exist

**Example Usage:**
```json
{
  "type": "precedence",
  "before": "tests",
  "after": "deployment",
  "priority": "hard",
  "note": "Never deploy without passing tests"
}
```

```json
{
  "type": "duration",
  "entity": "build_time",
  "max_duration": "10 minutes",
  "priority": "soft",
  "note": "Prefer faster builds, but not critical"
}
```

---

## Constraint Composition

Constraints can be combined to express complex rules:

### Example: Automotive Build Constraints
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
    },
    {
      "type": "precedence",
      "before": "forged_internals",
      "after": "dyno_tuning",
      "priority": "hard"
    }
  ]
}
```

---

## Domain Pack Extensions

Domain Packs can add specialized constraint types:

### Example: Software Dev Pack
```json
{
  "constraint_types": [
    {
      "type": "version_compatibility",
      "extends": "interface_compatibility",
      "parameters": {
        "package_a": "UUID",
        "package_b": "UUID",
        "semver_rule": "string"
      }
    },
    {
      "type": "security_policy",
      "extends": "negation",
      "parameters": {
        "vulnerability_id": "string",
        "severity": "critical | high | medium | low"
      }
    }
  ]
}
```

---

## Summary

**Total Constraint Types: 28**

| Category | Count | Purpose |
|----------|-------|---------|
| Temporal | 8 | Timing, sequencing, scheduling |
| Resource | 8 | Allocation, capacity, budgets |
| Logical | 7 | Boolean relationships, choices |
| Structural | 5 | Hierarchies, composition, interfaces |

**Next Steps:**
1. Implement constraint validators in Phase 1
2. Map constraint types to solver backends (OR-Tools, Z3)
3. Create canonical test scenarios for each type
4. Define constraint template library for Domain Packs

---

**Version History:**
- **v1.0.0-draft** (2026-01-22): Complete taxonomy (28 types, 4 categories)

---

**Contributors:**
- David Kirsch (Author)
- Claude (Anthropic - Design and examples)

**Last Updated:** 2026-01-22  
**Next Review:** After Phase 1 implementation begins
