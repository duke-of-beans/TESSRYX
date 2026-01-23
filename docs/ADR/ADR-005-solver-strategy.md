# ADR-005: Use OR-Tools + Z3 Multi-Solver Strategy

**Status:** Accepted  
**Date:** 2026-01-22  
**Deciders:** David Kirsch, Genius Council (technical consensus)  
**Tags:** #technology #solver #algorithms #phase2

---

## Context

TESSRYX's core value proposition is **proving** that dependency plans are valid or explaining why they're impossible. This requires industrial-strength constraint solving capabilities.

**Requirement Categories:**
1. **Scheduling:** Temporal constraints (precedence, time windows, duration)
2. **Resource Allocation:** Capacity, sharing, budgets
3. **Boolean Logic:** Mutex, choice, implication, conditional
4. **Arithmetic:** Numeric comparisons, summations, optimization

**Candidate Solvers:**
- **OR-Tools (Google):** CP-SAT (Constraint Programming)
- **Z3 (Microsoft):** SMT (Satisfiability Modulo Theories)
- **Gurobi:** Commercial MIP (Mixed Integer Programming)
- **CPLEX:** Commercial MIP (IBM)
- **MiniZinc:** Declarative modeling layer
- **Choco:** Java CP solver
- **Custom:** Build our own (LEAN-OUT violation)

**Key Questions:**
1. Single solver or multi-solver orchestration?
2. Open-source or commercial?
3. Specialized (CP/SMT) or general (MIP)?
4. Python bindings quality?

---

## Decision

**We will use OR-Tools (CP-SAT) as primary solver with Z3 (SMT) for logical constraints, orchestrated via cascade pattern.**

**Architecture:**
```
TessIR Constraints
       ↓
┌──────────────────────────┐
│  Solver Orchestration    │
│  (Cascade Pattern)       │
└──────────────────────────┘
       ↓          ↓
   OR-Tools      Z3
   (CP-SAT)     (SMT)
       ↓          ↓
   Scheduling  Boolean
   Resource    Arithmetic
   Optimization Logic
```

**Cascade Strategy:**
1. **Analyze constraints** → Classify by type (temporal/resource vs logical)
2. **Route to solver:**
   - Temporal + Resource → OR-Tools CP-SAT
   - Logical + Arithmetic → Z3 SMT
   - Mixed → Decompose, solve separately, verify consistency
3. **If infeasible** → Extract minimal unsat core, explain to user

**Hybrid Problems:**
- Solve scheduling with OR-Tools (get valid timeline)
- Verify logical constraints with Z3 (check invariants hold)
- Iterate if conflict (rare)

---

## Rationale

### Why OR-Tools (Primary)

**1. Scheduling Domain Excellence**
- CP-SAT optimized for scheduling (Google's use case: data center scheduling)
- Native support for interval variables (start, end, duration)
- No-overlap constraints (resource capacity)
- Precedence graphs (built-in)

**2. Performance**
- Best-in-class CP solver (MiniZinc Challenge winner 2018-2023)
- Parallel search (multi-core utilization)
- Incremental solving (add constraints without restart)
- Scales to 100K+ variables

**3. Open Source**
- Apache 2.0 license (free for commercial use)
- Active development (Google maintains)
- Large community (Stack Overflow, GitHub)

**4. Python Bindings**
- Official Python API (not third-party wrapper)
- Pythonic interface (not auto-generated C++ bindings)
- Excellent documentation, examples

**5. Optimization**
- Objective function support (minimize cost, time, violations)
- Multi-objective (lexicographic, weighted sum)
- Solution quality guarantees (optimal vs feasible)

**Example - Resource Capacity:**
```python
from ortools.sat.python import cp_model

model = cp_model.CpModel()

# Create interval variables (tasks)
task_a = model.NewIntervalVar(0, 5, 10, 'task_a')
task_b = model.NewIntervalVar(0, 5, 10, 'task_b')

# No overlap (resource capacity = 1)
model.AddNoOverlap([task_a, task_b])

# Solve
solver = cp_model.CpSolver()
status = solver.Solve(model)

if status == cp_model.OPTIMAL:
    print(f"Task A: {solver.Value(task_a.StartExpr())}")
    print(f"Task B: {solver.Value(task_b.StartExpr())}")
```

---

### Why Z3 (Secondary)

**1. Boolean Logic Excellence**
- SMT = SAT + Theories (boolean + arithmetic/bitvectors/arrays)
- Native if-then-else, implications
- Quantifiers (exists, forall) for complex rules

**2. Proof Certificates**
- Z3 returns **minimal unsat core** (smallest conflicting subset)
- Proof traces (why this conclusion?)
- Human-readable explanations (future: GPT interprets)

**3. Academic Pedigree**
- Microsoft Research (Leonardo de Moura, Nikolaj Bjørner)
- Used in program verification (Facebook Infer, Microsoft Dafny)
- Trusted for correctness-critical applications

**4. Composability**
- Theory solvers plug together (boolean + integer + real)
- Extensible (add custom theories)
- Integration with theorem provers (Lean, Coq)

**Example - Conditional Constraint:**
```python
from z3 import *

# Variables
turbo = Bool('turbo')
fuel_upgrade = Bool('fuel_upgrade')
budget_ok = Int('budget') <= 25000

# Constraint: If turbo, then fuel upgrade required
s = Solver()
s.add(Implies(turbo, fuel_upgrade))
s.add(budget_ok)

if s.check() == sat:
    print(s.model())
else:
    print("Infeasible:", s.unsat_core())
```

---

### Why Cascade Pattern (Multi-Solver)

**1. Strengths Complementary**
- OR-Tools: Scheduling, optimization, performance
- Z3: Logic, proofs, correctness

**2. Problem Decomposition Natural**
- Most TessIR problems separate cleanly
- Temporal dependencies → OR-Tools
- Logical rules → Z3
- Mixed problems → Solve in phases

**3. Precedent: Consensus Project (S03)**
- Steal from David's working code
- Multi-solver orchestration proven pattern
- Tribunal pattern (parallel voting) also available

**4. Failure Isolation**
- If OR-Tools times out → Try Z3
- If Z3 returns unknown → Fall back to OR-Tools
- Graceful degradation

**Example - Cascade:**
```python
def solve_plan(constraints: List[Constraint]) -> Solution:
    # Phase 1: Classify
    temporal = [c for c in constraints if is_temporal(c)]
    logical = [c for c in constraints if is_logical(c)]
    
    # Phase 2: Route
    if temporal and not logical:
        return solve_with_ortools(temporal)
    elif logical and not temporal:
        return solve_with_z3(logical)
    else:
        # Phase 3: Hybrid
        schedule = solve_with_ortools(temporal)
        if schedule.is_feasible:
            verified = verify_with_z3(logical, schedule)
            if verified:
                return schedule
            else:
                return explain_infeasibility(constraints)
```

---

## Alternatives Considered

### Gurobi (Commercial MIP)
**Pros:**
- Best-in-class commercial solver
- Excellent performance (integer programming)
- Multi-objective optimization
- Academic licenses available

**Cons:**
- **Cost:** $10K-$100K/year per core (prohibitive for early stage)
- **Licensing:** Requires license server, activation
- **Limited free tier:** Academic only (not commercial startup)
- **API:** More complex than OR-Tools

**Why Rejected:** Cost unjustifiable for V1. Consider for V2 if performance bottleneck proven.

---

### CPLEX (IBM Commercial)
**Pros:**
- Industry standard (Fortune 500 use)
- Mature, stable
- Similar performance to Gurobi

**Cons:**
- Similar cost structure to Gurobi
- Heavier API (less Pythonic)
- Slower innovation (IBM bureaucracy)

**Why Rejected:** Same cost issue as Gurobi.

---

### MiniZinc (Modeling Layer)
**Pros:**
- Declarative syntax (closer to TessIR spec)
- Solver-agnostic (swap backends)
- Academic adoption (teaching constraint programming)

**Cons:**
- Extra layer of indirection (TessIR → MiniZinc → Solver)
- Performance overhead (translation step)
- Less control over solver behavior
- Python bindings less mature

**Why Rejected:** Adds complexity without clear benefit. Better to use solvers directly.

---

### Choco (Java CP)
**Pros:**
- Open source Java solver
- Good for scheduling problems

**Cons:**
- Java ecosystem (we chose Python)
- Smaller community than OR-Tools
- Performance slightly worse (benchmarks)

**Why Rejected:** Python decision (ADR-001) makes OR-Tools better fit.

---

### Custom Solver (LEAN-OUT Violation)
**Pros:**
- Full control over algorithms
- Optimized for TessIR specifically
- Intellectual property advantage

**Cons:**
- **CRITICAL FLAW:** Violates LEAN-OUT principle (build intelligence, not plumbing)
- Reinventing 40+ years of research (CP, MIP, SMT)
- Huge time sink (6+ months to match OR-Tools)
- Maintenance burden (keep up with research)
- Unlikely to beat industrial solvers (Google/Microsoft teams)

**Why Rejected:** Fundamental violation of core philosophy. Use existing infrastructure.

---

### Single Solver (OR-Tools Only)
**Pros:**
- Simpler architecture (one integration)
- No orchestration complexity
- OR-Tools can handle logic (via integer encoding)

**Cons:**
- Suboptimal for logical constraints (Z3 better)
- Lose proof capabilities (minimal unsat core)
- Harder to explain infeasibility (no SMT reasoning)

**Why Rejected:** Small orchestration cost, big explanation benefit.

---

### Single Solver (Z3 Only)
**Pros:**
- Excellent for logical constraints
- Proof certificates
- Academic validation

**Cons:**
- Weaker for scheduling (no native intervals)
- Slower for optimization (no CP heuristics)
- Less Pythonic API

**Why Rejected:** Scheduling is core use case (OR-Tools stronger).

---

## Consequences

### Positive

**1. Best-of-Breed Performance**
- OR-Tools for what it's best at (scheduling)
- Z3 for what it's best at (logic, proofs)
- Avoid compromise (jack of all trades, master of none)

**2. Explanation Quality**
- Z3 minimal unsat core → "These 3 constraints conflict"
- OR-Tools objective → "Relaxing X reduces cost by $5K"
- Combined: Precise, actionable feedback

**3. Cost Savings**
- Both open-source (zero license cost)
- Can scale without per-core fees
- V1 budget preserved for engineering, not licenses

**4. Proven Pattern**
- Consensus project uses multi-solver (S03)
- Academic literature supports hybrid approaches
- Risk mitigation (if one solver fails, other available)

**5. Community Support**
- OR-Tools: 3K+ GitHub stars, active Google support
- Z3: 9K+ GitHub stars, Microsoft Research backing
- Large Stack Overflow communities

### Negative

**1. Orchestration Complexity**
- Must classify constraints (routing logic)
- Handle edge cases (mixed problems)
- Maintain two integrations (API changes)

**Mitigation:**
- Start simple (single solver paths)
- Add orchestration incrementally (Phase 2)
- Steal Consensus patterns (S03) - already solved problem
- Comprehensive tests (canonical suite validates both solvers)

**2. Solution Consistency Risk**
- OR-Tools says "feasible", Z3 says "infeasible"
- Rare but possible (solver bugs, floating point)

**Mitigation:**
- Validate cross-solver (OR-Tools solution checked by Z3)
- Log discrepancies, escalate to user
- Prefer conservative (if disagreement, report infeasible)

**3. Learning Curve**
- Team needs expertise in both solvers
- Different mental models (CP vs SMT)
- API differences (even though both Python)

**Mitigation:**
- Gradual rollout (OR-Tools first, Z3 later)
- Documentation/examples for each
- Code review (ensure patterns consistent)

### Neutral

**1. Future Solver Additions**
- Could add Gurobi later (if performance justifies cost)
- Could add specialized solvers (graph algorithms, ML)
- Architecture supports this (orchestra pattern)

**2. Academic Validation**
- Using best-in-class tools (not custom) = credibility
- Easier to publish research (reproducible)
- But: Less novelty (we didn't invent solver)

---

## Implementation Plan

### Phase 2: OR-Tools Integration (Months 4-5)
```python
# Core solver wrapper
class ORToolsSolver:
    def solve(self, constraints: List[Constraint]) -> Solution:
        model = cp_model.CpModel()
        
        # Translate TessIR → OR-Tools
        for c in constraints:
            if c.type == "precedence":
                self._add_precedence(model, c)
            elif c.type == "resource_capacity":
                self._add_no_overlap(model, c)
            # ... etc
        
        solver = cp_model.CpSolver()
        status = solver.Solve(model)
        
        return self._extract_solution(solver, status)
```

### Phase 2: Z3 Integration (Months 5-6)
```python
# Logic solver wrapper
class Z3Solver:
    def solve(self, constraints: List[Constraint]) -> Solution:
        s = Solver()
        
        # Translate TessIR → Z3
        for c in constraints:
            if c.type == "mutex":
                self._add_mutex(s, c)
            elif c.type == "implication":
                self._add_implication(s, c)
            # ... etc
        
        if s.check() == sat:
            return self._extract_solution(s.model())
        else:
            return self._explain_unsat(s.unsat_core())
```

### Phase 2: Orchestration (Month 6)
```python
# Multi-solver coordinator
class SolverOrchestrator:
    def solve(self, constraints: List[Constraint]) -> Solution:
        # Classify
        temporal = classify_temporal(constraints)
        logical = classify_logical(constraints)
        
        # Route
        if temporal and not logical:
            return self.ortools.solve(temporal)
        elif logical and not temporal:
            return self.z3.solve(logical)
        else:
            return self._solve_hybrid(temporal, logical)
```

---

## Validation Criteria

**Phase 2 Success Metrics:**
- [ ] All 50 canonical test scenarios pass (both solvers)
- [ ] OR-Tools p95 solve time <30 seconds (10K nodes)
- [ ] Z3 p95 solve time <10 seconds (1K constraints)
- [ ] Minimal unsat core generated for failures
- [ ] Explanation quality rated 4+/5 by users

**Performance Benchmarks:**
```
Problem Size: 1K entities, 5K relations, 10K constraints

OR-Tools:
  - Scheduling-only: <1 second
  - With optimization: <5 seconds
  
Z3:
  - Logic-only: <500ms
  - With arithmetic: <2 seconds
  
Hybrid:
  - Combined: <10 seconds (acceptable for V1)
```

---

## Future Enhancements (V2+)

### V1.1: Incremental Solving
- Add constraint without full re-solve
- OR-Tools supports this (Z3 limited)
- 10x faster for minor changes

### V1.2: Solution Diversity
- Generate multiple valid solutions
- User chooses based on preferences
- OR-Tools multi-solution API

### V2.0: Learned Heuristics
- ML guides solver search (hot paths)
- Historical data → better branching
- Requires V1 data collection

### V3.0: GPU Acceleration
- Parallelize constraint checking
- Explore CUDA solvers (research stage)
- Potential 100x speedup

---

## Related Decisions

- **ADR-001:** Python for V1 (OR-Tools Python API excellent)
- **Steal S03:** Multi-Solver Orchestration (Consensus pattern)

---

## References

- [OR-Tools Documentation](https://developers.google.com/optimization)
- [Z3 GitHub Repository](https://github.com/Z3Prover/z3)
- [CP-SAT Primer](https://developers.google.com/optimization/cp/cp_solver)
- [MiniZinc Challenge Results](https://www.minizinc.org/challenge/)
- [SMT-LIB Standard](http://smtlib.cs.uiowa.edu/)
- Genius Council Technical Review (Consensus on hybrid approach)

---

**Last Updated:** 2026-01-22  
**Status:** Accepted  
**Next Review:** After Phase 2 implementation (Month 6) - evaluate performance
