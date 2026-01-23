# ADR-001: Choose Python for V1 Implementation

**Status:** Accepted  
**Date:** 2026-01-22  
**Deciders:** David Kirsch, Genius Council (GPT, Gemini, Claude)  
**Tags:** #technology #v1 #implementation-language

---

## Context

TESSRYX requires an implementation language for the V1 kernel (TessIR + GraphOps + Solver integration). The language choice impacts development velocity, ecosystem availability, AI assistance quality, and long-term performance.

**Candidate Languages:**
- Python 3.12+
- Rust
- TypeScript/Node.js
- Go
- Java/Kotlin

**Key Requirements:**
1. Fast iteration during Phase 0-2 (specification → solver integration)
2. Rich ecosystem for constraint solving (OR-Tools, Z3)
3. Graph algorithms library availability
4. Strong AI-assisted development support
5. Easy prototyping and refactoring
6. Clear migration path to production-grade V2

**Timeline Considerations:**
- V1 target: 12 months (specification → Software Dev Domain Pack)
- V2 transition: After 6-12 months of production validation

---

## Decision

**We will use Python 3.12+ for the V1 implementation.**

**Specific Stack:**
- **Language:** Python 3.12+ (with type hints via Pydantic)
- **Graph:** NetworkX (in-memory graph library)
- **Solver:** OR-Tools (Google CP-SAT), Z3 (Microsoft SMT)
- **Database:** PostgreSQL (via SQLAlchemy)
- **API:** FastAPI + Pydantic
- **Testing:** Pytest + Hypothesis (property-based testing)
- **Type Checking:** mypy --strict
- **Migrations:** Alembic

**Migration Strategy:**
- V2 kernel rewrite in Rust (after V1 validation)
- Python bindings maintained via PyO3
- TessIR spec remains language-agnostic

---

## Rationale

### Why Python Wins for V1

**1. Development Velocity (Highest Priority for V1)**
- Rapid prototyping and iteration
- Concise syntax reduces boilerplate
- Dynamic typing with gradual static typing (Pydantic)
- Fast refactoring with minimal ceremony

**2. AI-Assisted Development**
- Claude/GPT/Gemini have extensive Python training data
- High-quality code generation and debugging support
- Large corpus of examples for constraint solving, graph algorithms
- Better AI assistance than Rust (less training data, more complex)

**3. Ecosystem Maturity**
- **OR-Tools:** First-class Python support, most examples in Python
- **Z3:** Official Python bindings, widely used in academic/research
- **NetworkX:** Battle-tested graph algorithms library (2003+)
- **SQLAlchemy:** Mature ORM with excellent PostgreSQL support
- **FastAPI:** Modern, fast, auto-generated OpenAPI docs

**4. Mathematical/Scientific Computing Heritage**
- NumPy, SciPy, pandas for data manipulation
- Jupyter notebooks for exploratory analysis
- Matplotlib, Plotly for visualization
- Well-established patterns for scientific software

**5. Lower Learning Curve**
- Easier for contributors to understand codebase
- Faster onboarding for future team members
- Community help readily available (Stack Overflow, Reddit)

**6. Proven Pattern**
- Many successful infrastructure projects start in Python, rewrite in Rust
- Examples: Dropbox (server core), Instagram (original), PyTorch (Python + C++)
- Validates assumptions before performance optimization

---

## Alternatives Considered

### Rust
**Pros:**
- Exceptional performance (10-100x faster than Python)
- Memory safety without garbage collection
- Excellent concurrency primitives
- No runtime, minimal dependencies

**Cons:**
- Steep learning curve (borrow checker, lifetimes)
- Slower development velocity (~3x more lines for same logic)
- Less mature constraint solving ecosystem (limited OR-Tools/Z3 bindings)
- Harder to refactor during exploratory phase
- AI assistance quality lower (less training data)

**Decision:** Rust for V2 kernel rewrite, not V1

---

### TypeScript/Node.js
**Pros:**
- Strong typing with excellent IDE support
- Single language for frontend + backend
- Mature ecosystem (npm)
- Good performance (V8 JIT)

**Cons:**
- Weaker scientific computing ecosystem
- No native OR-Tools bindings (must use C++ bridge)
- Z3 bindings immature
- NetworkX equivalent (cytoscape.js) more limited
- Asynchronous complexity for graph algorithms

**Decision:** TypeScript for future frontend, not kernel

---

### Go
**Pros:**
- Simple language, fast compilation
- Built-in concurrency (goroutines)
- Single binary deployment
- Growing ecosystem

**Cons:**
- No OR-Tools bindings (must use C++ bridge)
- Z3 bindings unofficial, limited
- Graph algorithms library less mature
- Generic constraints solving patterns less established

**Decision:** Not suitable for constraint solving domain

---

### Java/Kotlin
**Pros:**
- OR-Tools Java bindings available
- Mature JVM ecosystem
- Strong typing
- Good performance

**Cons:**
- Verbose compared to Python (2-3x more boilerplate)
- JVM startup time and memory overhead
- Less natural for scientific computing
- AI assistance quality moderate

**Decision:** Not optimal for rapid iteration

---

## Consequences

### Positive

**1. Fast Time to Market**
- Can iterate on TessIR spec and implementation simultaneously
- Quick experimentation with constraint solving strategies
- Rapid prototyping of Domain Packs

**2. Rich Debugging Experience**
- Interactive Python shell (IPython)
- Jupyter notebooks for testing scenarios
- Excellent stack traces and error messages

**3. Strong Community Support**
- Large Python community for troubleshooting
- Active OR-Tools and Z3 communities
- Many examples and tutorials available

**4. Clear Migration Path**
- Python V1 validates all design decisions
- Rust V2 becomes "optimized reimplementation"
- Can measure performance gains empirically (10x? 50x? 100x?)

### Negative

**1. Performance Limitations**
- Python ~100x slower than Rust for compute-intensive tasks
- GIL (Global Interpreter Lock) limits multi-threading
- Higher memory usage (~10x vs Rust)

**Mitigation:**
- Profile early, optimize hot paths with Cython/Numba
- OR-Tools and Z3 are C++ under the hood (fast)
- NetworkX operations are C-optimized
- Most time will be spent in solver, not Python
- V2 Rust rewrite addresses this permanently

**2. Runtime Dependencies**
- Requires Python 3.12+ runtime
- ~100MB+ deployment size (vs Rust 10MB single binary)
- Dependency management (virtual environments, pip)

**Mitigation:**
- Docker containers standardize environment
- Railway/Render handle deployment complexity
- V1 is for validation, not massive scale

**3. Type Safety Weaker Than Rust/TypeScript**
- Runtime errors possible despite type hints
- Pydantic catches many errors, but not all

**Mitigation:**
- mypy --strict enforced (CI fails on type errors)
- Comprehensive test suite (Pytest + Hypothesis)
- Fast iteration allows quick bug fixing

### Neutral

**1. Two-Language Strategy**
- Python for V1 (months 1-12)
- Rust for V2 (year 2+)
- Requires rewrite, but validates design first

**2. Team Hiring**
- Python developers easier to find than Rust
- But may need Rust expertise for V2 transition

---

## Implementation Notes

### Type Safety Strategy
```python
from pydantic import BaseModel, Field
from typing import UUID, Literal

class Entity(BaseModel):
    id: UUID
    type: str
    name: str
    version: str | None = None
    
    class Config:
        frozen = True  # Immutable
```

### Performance Monitoring
```python
import cProfile
import pstats

# Profile hot paths early
with cProfile.Profile() as pr:
    blast_radius(changed_entities)
    
stats = pstats.Stats(pr)
stats.sort_stats('cumtime')
stats.print_stats(10)
```

### Rust Migration Planning
- Keep TessIR spec implementation-agnostic
- Design clear module boundaries (easy to port)
- Document algorithms precisely (not just code)
- Create comprehensive test suite (runs on Rust V2)

---

## Validation Criteria

**V1 Success Metrics (Python must achieve):**
- [ ] All 50 canonical test scenarios passing
- [ ] Solve 10K node graphs in <30 seconds
- [ ] API <500ms p95 latency
- [ ] Zero technical debt (no TODOs, placeholders)
- [ ] 90%+ test coverage

**V2 Transition Triggers:**
- [ ] Performance bottleneck identified in Python
- [ ] User base demands <5s solve times
- [ ] Need to scale to 100K+ node graphs
- [ ] Cost savings justify rewrite effort

---

## Related Decisions

- **ADR-002:** Database choice (Postgres first)
- **ADR-005:** Constraint solver strategy (OR-Tools + Z3)

---

## References

- [Python 3.12 Release Notes](https://docs.python.org/3/whatsnew/3.12.html)
- [OR-Tools Python Documentation](https://developers.google.com/optimization/introduction/python)
- [Z3 Python API](https://z3prover.github.io/api/html/namespacez3py.html)
- [NetworkX Documentation](https://networkx.org/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- Genius Council Synthesis (2026-01-19)

---

**Last Updated:** 2026-01-22  
**Status:** Accepted  
**Next Review:** After Phase 1 implementation (Month 3)
