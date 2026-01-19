# TESSRYX Canonical Test Suite
**Version:** 1.0.0  
**Status:** Framework established, scenarios in progress  
**Goal:** 50 scenarios covering real-world dependency validation use cases

---

## Overview

The canonical test suite validates TESSRYX's core capabilities across five domains. Each scenario includes:
- Problem statement (what we're validating)
- TessIR graph representation (entities, relations, constraints)
- Expected valid sequences/plans
- Expected invalid sequences + why
- Expected explanation quality

**Framework adapted from:** Gregore EPIC 34 benchmark system (S11)

---

## Structure

```
canonical_suite/
├── README.md (this file)
├── SCENARIO-TEMPLATE.yaml (template for new scenarios)
├── runner.py (test runner - Phase 1)
├── comparator.py (output validator - Phase 1)
├── software_dev/ (10 scenarios)
│   ├── 01-circular-dependency.yaml
│   ├── 02-version-conflict.yaml
│   └── ...
├── it_operations/ (10 scenarios)
├── automotive/ (10 scenarios)
├── construction/ (10 scenarios)
└── adversarial/ (10 scenarios)
```

---

## Domain Coverage

### Software Development (10 scenarios)
Focus: Package managers, version conflicts, security, API changes

**Planned Scenarios:**
1. Circular dependency (A → B → A)
2. Version conflict (service X needs lib@1.0, service Y needs lib@2.0)
3. Missing transitive dependency
4. Security vulnerability cascade
5. Breaking API change impact
6. Diamond dependency (multiple paths to same package)
7. Peer dependency mismatch
8. Lockfile drift detection
9. Monorepo cross-package dependencies
10. Build order constraints with parallel builds

### IT Operations (10 scenarios)
Focus: Infrastructure, deployments, configuration, service dependencies

**Planned Scenarios:**
1. Service startup order (database before app)
2. Blue-green deployment constraints
3. Configuration drift detection
4. Resource capacity conflicts (CPU/memory)
5. Network topology dependencies
6. Rolling update constraints
7. Disaster recovery ordering
8. Certificate renewal cascades
9. Load balancer health check dependencies
10. Multi-region failover sequencing

### Automotive (10 scenarios)
Focus: ECU dependencies, CAN bus timing, safety constraints

**Planned Scenarios:**
1. ECU boot sequence (ignition → engine control → transmission)
2. CAN bus message timing constraints
3. Safety-critical redundancy requirements
4. Sensor fusion dependencies
5. OTA update sequencing
6. Power management constraints
7. Diagnostic mode transitions
8. Feature activation dependencies (requires unlock)
9. AUTOSAR component dependencies
10. Functional safety constraints (ASIL-D)

### Construction/AEC (10 scenarios)
Focus: Task sequencing, resource allocation, spatial constraints

**Planned Scenarios:**
1. Foundation before framing
2. Concurrent trade conflicts (electrical and plumbing)
3. Material delivery timing
4. Equipment resource conflicts (one crane, two lifts)
5. Weather-dependent sequencing
6. Inspection dependencies
7. Permit acquisition ordering
8. Spatial access constraints (scaffolding blocks crane)
9. Critical path identification
10. Subcontractor availability

### Adversarial (10 scenarios)
Focus: Edge cases, contradictions, malicious inputs, unsolvable problems

**Planned Scenarios:**
1. Deliberately contradictory constraints
2. Circular must-not-precede (A must not precede B, B must not precede A, both required)
3. Over-constrained (impossible to satisfy all constraints)
4. Under-constrained (ambiguous, multiple valid solutions)
5. Malicious input (invisible characters, homoglyphs)
6. Extremely large graphs (10K+ nodes)
7. Deeply nested hierarchies (100+ levels)
8. Conflicting provenance (high-confidence sources disagree)
9. Temporal paradoxes (must happen before AND after)
10. Resource oversubscription (requires 150% capacity)

---

## Scenario Format (YAML)

See `SCENARIO-TEMPLATE.yaml` for complete structure.

### Key Sections:
```yaml
metadata:
  id: "[domain]-[number]"
  name: "Short descriptive name"
  domain: "[software_dev|it_operations|automotive|construction|adversarial]"
  difficulty: "[simple|medium|complex|expert]"
  
problem:
  description: "What we're validating"
  context: "Real-world motivation"
  
tessir_graph:
  entities: [...]      # List of Entity objects
  relations: [...]     # List of Relation objects
  constraints: [...]   # List of Constraint objects
  assumptions: [...]   # List of Assumption objects
  
expected_outputs:
  feasible: true|false
  valid_sequences: [...]     # If feasible, list valid orderings
  invalid_sequences: [...]   # Sequences that violate constraints
  minimal_unsat_core: [...]  # If infeasible, minimal conflicting constraints
  explanation_must_include:  # Key phrases in human-readable output
    - "phrase 1"
    - "phrase 2"
  blast_radius:              # If testing change impact
    changed: ["entity_1"]
    affected: ["entity_2", "entity_3"]
```

---

## Test Runner (Phase 1)

**Purpose:** Automate scenario execution and validation

```python
# tests/canonical_suite/runner.py (to be implemented Phase 1)

class ScenarioRunner:
    def load_scenario(yaml_path: str) -> Scenario
    def execute_scenario(scenario: Scenario) -> Result
    def validate_result(result: Result, expected: Expected) -> ValidationReport
    def generate_summary(results: List[Result]) -> Summary

# Usage:
runner = ScenarioRunner()
results = runner.run_all_scenarios("software_dev/")
summary = runner.generate_summary(results)
# Expected: 10/10 passing, 0 failures, 0 warnings
```

---

## Comparator (Phase 1)

**Purpose:** Deep comparison of solver output vs expected output

```python
# tests/canonical_suite/comparator.py (to be implemented Phase 1)

class OutputComparator:
    def compare_feasibility(actual: bool, expected: bool) -> Match
    def compare_sequences(actual: List[Sequence], expected: List[Sequence]) -> Match
    def compare_unsat_core(actual: Set[Constraint], expected: Set[Constraint]) -> Match
    def compare_explanation(actual: str, expected: List[str]) -> Match
    def fuzzy_match(actual: str, phrase: str, threshold: float = 0.9) -> bool
```

---

## Metrics Tracked

**Per Scenario:**
- Pass/fail status
- Execution time (solver + explanation)
- Memory usage
- Constraint count
- Entity/relation count
- Explanation quality score

**Suite-Level:**
- Pass rate (target: 100%)
- Average execution time
- Slowest scenarios (optimization targets)
- Regression detection (flag if slower than baseline)

---

## Quality Standards

**Every scenario MUST:**
1. Have clear problem statement (1-2 sentences)
2. Include complete TessIR representation
3. Define expected outputs precisely
4. Be deterministic (same input → same output)
5. Be independent (scenarios don't depend on each other)
6. Be maintained (updated when TessIR spec changes)

**Explanations MUST:**
1. Be human-readable (12th grade level or lower)
2. Include "what" (outcome)
3. Include "why" (root cause)
4. Include "how to fix" (if failure)
5. Reference specific entities/constraints by name

---

## Usage During Development

### Phase 0 (Specification):
- Create scenarios in parallel with TessIR spec
- Validate spec completeness (can we represent these scenarios?)
- Refine constraint taxonomy based on scenario needs

### Phase 1 (Core Implementation):
- Run software_dev scenarios as implementation progresses
- Target: 10/10 passing by end of Phase 1

### Phase 2 (Solver Integration):
- Run all 50 scenarios
- Target: 45/50 passing by end of Phase 2 (complex cases may fail)

### Phase 3 (Versioning):
- Add version change scenarios
- Test blast radius accuracy

### Phase 4+ (Production):
- Regression suite (run on every commit)
- Performance benchmarks (track solver time trends)
- Add new scenarios as edge cases discovered

---

## Contributing New Scenarios

1. Copy `SCENARIO-TEMPLATE.yaml`
2. Fill in all sections completely
3. Run validation: `python runner.py --validate scenario.yaml`
4. Test manually first (Phase 1+)
5. Add expected outputs precisely
6. Document any ambiguities or edge cases
7. Submit PR with scenario + rationale

---

## Success Criteria

**Phase 0 Complete:** All 50 scenarios defined with expected outputs  
**Phase 1 Complete:** 10/10 software_dev scenarios passing  
**Phase 2 Complete:** 45/50 all scenarios passing  
**Phase 3 Complete:** 50/50 all scenarios passing  
**Production:** 50/50 passing on every release, <30 sec total execution time

---

## References

- [TessIR Specification](../../docs/TessIR_v1.0_SPEC.md) - Schema definitions
- [STEAL_REGISTRY.md](../../STEAL_REGISTRY.md) - S11: Framework adapted from Gregore
- [ROADMAP.md](../../ROADMAP.md) - Test suite timeline

---

**Last Updated:** 2026-01-19  
**Next Update:** When first scenarios are created (Phase 0, Week 4)
