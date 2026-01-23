# ADR-002: Choose PostgreSQL First (Defer Neo4j Decision)

**Status:** Accepted  
**Date:** 2026-01-22  
**Deciders:** David Kirsch, Claude (synthesizing GPT vs Gemini disagreement)  
**Tags:** #database #storage #architecture #v1

---

## Context

TESSRYX needs a persistence layer for entities, relations, constraints, provenance, and version history. The database choice impacts query performance, development complexity, and operational costs.

**Core Requirements:**
1. Store graph-like data (entities with typed relations)
2. Complex queries (blast radius, cycles, topological sort)
3. Transaction support (ACID guarantees)
4. Version history (time-series data)
5. Provenance tracking (metadata-heavy)
6. API-driven access patterns (not ad-hoc queries)
7. Cost-effective for early stage (free/cheap hosting)

**Candidate Databases:**
- PostgreSQL (relational + JSONB + extensions)
- Neo4j (native graph database)
- Hybrid: Postgres + Neo4j
- Other: MongoDB, DynamoDB, Cassandra

**Genius Council Disagreement:**
- **GPT-4:** Recommended Neo4j immediately (native graph performance)
- **Gemini 2.0:** Recommended Postgres first (defer expensive decision)
- **Claude:** Synthesized to "Postgres first, migrate if needed"

---

## Decision

**We will use PostgreSQL for V1, with explicit migration path to Neo4j if/when needed.**

**Specific Configuration:**
- **Database:** PostgreSQL 15+ (or Supabase managed)
- **ORM:** SQLAlchemy (Python)
- **Migrations:** Alembic
- **Extensions:** pg_trgm (text search), pgvector (future embeddings)
- **Hosting:** Supabase free tier → Railway.app/Render (when scaling)

**Neo4j Migration Triggers (Phase 2-3):**
- Traversal queries exceed 1 second p95 latency
- Graph size >100K nodes AND frequent deep traversals
- Need for real-time graph algorithms (betweenness centrality, PageRank)

**Hybrid Strategy (If Needed):**
- Hot path: Neo4j (fast graph traversals)
- Cold storage: Postgres (provenance, versions, compliance)
- Sync via event sourcing (eventual consistency)

---

## Rationale

### Why Postgres First

**1. Defer Expensive Decision**
- **Problem:** We don't know usage patterns yet
- **Solution:** Use flexible schema (JSONB), measure real workloads
- **Benefit:** Avoid premature optimization, gather evidence

**2. Lower Operational Complexity**
- **Postgres:** Single database, mature tooling, wide hosting options
- **Neo4j:** Additional service, specialized knowledge, higher costs
- **Impact:** Faster deployment, simpler architecture

**3. Cost Efficiency**
- **Postgres:** Supabase free tier (500MB), Railway $5/month
- **Neo4j:** AuraDB $65/month minimum (no free tier)
- **Savings:** ~$780/year during validation phase

**4. Rich Data Types**
- **JSONB:** Flexible schema for metadata
- **Arrays:** Store UUIDs, tags, evidence lists
- **HSTORE:** Key-value pairs for properties
- **Temporal:** Built-in timestamp types, time-series support

**5. Transaction Guarantees**
- **ACID:** Critical for consistency (version commits, constraint updates)
- **Isolation levels:** Prevent race conditions in concurrent writes
- **Rollback:** Easy error recovery during development

**6. Mature Ecosystem**
- **SQLAlchemy:** Battle-tested ORM, excellent docs
- **Alembic:** Robust migrations, version control
- **pg_admin:** Visual query builder, schema inspection
- **Backup/restore:** Standard tools (pg_dump, pg_restore)

**7. API-First Architecture Mitigates Graph DB Need**
- Most queries go through defined operations (not ad-hoc Cypher)
- In-memory NetworkX for graph algorithms during solve
- Database primarily for persistence, not computation

### Why Not Neo4j Day One

**1. Unknown Query Patterns**
- **Risk:** Build for graph traversals, but users mostly fetch entities by ID
- **Consequence:** Paying for performance we don't use
- **Mitigation:** Profile with Postgres, upgrade if needed

**2. Schema Evolution Uncertainty**
- **Early Stage:** TessIR spec still evolving (constraints, provenance)
- **Graph DB:** Schema changes harder (relationship types, indexes)
- **Relational:** Alembic migrations well-understood

**3. Development Velocity**
- **Learning Curve:** Cypher query language, graph modeling patterns
- **AI Assistance:** Less training data for Neo4j vs Postgres
- **Community:** Smaller Neo4j community for troubleshooting

**4. Hybrid Complexity**
- **If Wrong:** Adding Neo4j later is easier than removing it
- **Sync Overhead:** Dual-write complexity, eventual consistency bugs
- **Operational Burden:** Two databases to monitor, backup, scale

---

## Alternatives Considered

### Neo4j from Day One
**Pros:**
- Native graph queries (Cypher)
- Optimized for traversals (pointers, not joins)
- Visual query builder (Neo4j Bloom)
- Graph algorithms library (PageRank, community detection)

**Cons:**
- Higher operational cost ($65-$200/month)
- Steeper learning curve (Cypher, graph modeling)
- Specialized knowledge required (harder to hire)
- Overkill if access patterns are simple (fetch by ID)
- Harder to change schema during early iteration

**Decision:** Defer until proven necessary (Phase 2-3)

---

### MongoDB (Document Store)
**Pros:**
- Flexible schema (BSON)
- Horizontal scaling (sharding)
- Good for JSON-like data

**Cons:**
- Weak transaction guarantees (before v4.0)
- No native graph algorithms
- Poor support for relations (manual joins)
- Not optimal for highly connected data

**Decision:** Not suitable for graph-centric workload

---

### DynamoDB / Cassandra (Wide-Column)
**Pros:**
- Massive scalability (distributed)
- Predictable low latency

**Cons:**
- Limited query flexibility (partition key required)
- No transactions across partitions (Cassandra)
- Poor fit for graph traversals
- Cost at small scale higher than Postgres

**Decision:** Over-engineered for V1 scale

---

### Hybrid: Postgres + Neo4j from Day One
**Pros:**
- Best of both worlds (relational + graph)
- Postgres for provenance/versions, Neo4j for traversals

**Cons:**
- Dual-write complexity (consistency challenges)
- Operational burden (2x monitoring, backup, deploy)
- Development overhead (sync logic, conflict resolution)
- Premature for unknown workload

**Decision:** Only if single DB proves insufficient

---

## Consequences

### Positive

**1. Fast Iteration**
- Change schema with Alembic migrations
- JSONB allows property additions without migrations
- Rollback errors easily during development

**2. Cost Savings**
- Free tier for Phase 0-1 (Supabase)
- $5-20/month for Phase 2-3 (Railway)
- Reinvest savings into feature development

**3. Simplified Operations**
- Single database to monitor
- Standard backup procedures
- Wide hosting options (AWS RDS, Railway, Render, Supabase)

**4. Clear Decision Point**
- Profile real workloads
- Measure traversal latency empirically
- Upgrade only if bottleneck proven

### Negative

**1. Traversal Query Performance**
- Recursive CTEs slower than native graph pointers
- Deep traversals (>5 hops) may hit 1-2 second latency

**Mitigation:**
- In-memory NetworkX for algorithmic work (SCC, topo sort)
- Database primarily for persistence, not computation
- Optimize hot queries with indexes, materialized views
- If still slow, migrate to Neo4j (evidence-based decision)

**2. Migration Risk (If Neo4j Needed)**
- Schema translation (tables → nodes/edges)
- Data migration scripts (ETL)
- Application code refactor (SQLAlchemy → Neo4j driver)

**Mitigation:**
- Design clear abstraction layer (Repository pattern)
- TessIR operations stay the same (swap implementation)
- Test suite validates behavior during migration
- Phased rollout (hybrid mode, then full cutover)

**3. Graph Algorithm Limitations**
- Postgres lacks native PageRank, betweenness centrality
- Community detection, graph coloring not built-in

**Mitigation:**
- Use NetworkX in-memory for algorithms
- Materialize results to Postgres
- Only load relevant subgraph (not entire graph)
- V2 Rust kernel optimizes this further

### Neutral

**1. Technical Debt?**
- Some see deferral as debt
- We see it as evidence-based engineering

**2. Future Neo4j Migration**
- May happen in Phase 2-3 (months 4-8)
- Estimated effort: 2-3 weeks
- Acceptable risk given cost savings

---

## Schema Design (Postgres)

### Entity Storage
```sql
CREATE TABLE entities (
    id UUID PRIMARY KEY,
    type VARCHAR(50) NOT NULL,
    name TEXT NOT NULL,
    version VARCHAR(50),
    parent_id UUID REFERENCES entities(id),
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_entities_type ON entities(type);
CREATE INDEX idx_entities_parent ON entities(parent_id);
CREATE INDEX idx_entities_metadata ON entities USING GIN(metadata);
```

### Relation Storage
```sql
CREATE TABLE relations (
    id UUID PRIMARY KEY,
    type VARCHAR(50) NOT NULL,
    from_entity_id UUID REFERENCES entities(id) ON DELETE CASCADE,
    to_entity_id UUID REFERENCES entities(id) ON DELETE CASCADE,
    strength FLOAT DEFAULT 1.0,
    contract JSONB,
    provenance JSONB NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_relations_from ON relations(from_entity_id);
CREATE INDEX idx_relations_to ON relations(to_entity_id);
CREATE INDEX idx_relations_type ON relations(type);
```

### Graph Traversal Query (Recursive CTE)
```sql
-- Blast radius (all downstream dependencies)
WITH RECURSIVE downstream AS (
    SELECT to_entity_id, 1 as depth
    FROM relations
    WHERE from_entity_id = $1
    
    UNION
    
    SELECT r.to_entity_id, d.depth + 1
    FROM relations r
    INNER JOIN downstream d ON r.from_entity_id = d.to_entity_id
    WHERE d.depth < $2  -- max depth limit
)
SELECT DISTINCT to_entity_id FROM downstream;
```

**Performance:** 5-10ms for depth 3-4, 50-100ms for depth 5-6 (needs profiling)

---

## Migration Strategy (If Needed)

### Phase 1: Profiling (Month 3-4)
```python
# Instrument slow queries
import time

@profile_query
def blast_radius(entity_id: UUID, max_depth: int):
    start = time.perf_counter()
    result = db.execute(recursive_cte_query)
    duration = time.perf_counter() - start
    
    if duration > 1.0:  # Trigger warning
        log.warning(f"Slow traversal: {duration:.2f}s for depth {max_depth}")
    
    return result
```

### Phase 2: Decision Point (Month 4-6)
**Metrics to Track:**
- Traversal query p95 latency (target: <500ms)
- Average graph depth queried (if >5, consider Neo4j)
- Query frequency (if >100/sec, consider Neo4j)

**Threshold for Migration:**
- p95 >1 second AND depth >5 AND frequency >50/sec

### Phase 3: Hybrid Architecture (Month 6-8)
```yaml
# Event-driven sync
Postgres (source of truth):
  - Write all data here
  - Emit events on changes

Neo4j (read replica):
  - Subscribe to events
  - Build graph index
  - Serve traversal queries
  
Sync:
  - Event bus (Kafka / Redis Streams)
  - Eventual consistency (acceptable for graph queries)
```

### Phase 4: Full Migration (Month 8-10)
- All writes go to Neo4j
- Postgres remains for provenance archive
- Benchmark performance gains (should see 10-50x improvement)

---

## Validation Criteria

**Postgres Success Metrics:**
- [ ] Traversal p95 <500ms for depth 3-4
- [ ] Schema migrations smooth (<1 min downtime)
- [ ] Query complexity manageable (no >10 join queries)
- [ ] Storage cost <$20/month for 100K entities

**Neo4j Migration Triggers:**
- [ ] Traversal p95 >1 second consistently
- [ ] Depth >5 queries common (>20% of traffic)
- [ ] Users complain about graph query speed

---

## Related Decisions

- **ADR-001:** Python for V1 (SQLAlchemy + Postgres)
- **ADR-005:** Solver strategy (in-memory NetworkX + OR-Tools)

---

## References

- [PostgreSQL 15 Documentation](https://www.postgresql.org/docs/15/)
- [Neo4j vs Relational Databases](https://neo4j.com/developer/graph-db-vs-rdbms/)
- [Supabase Pricing](https://supabase.com/pricing)
- [Railway Postgres](https://railway.app/template/postgres)
- Genius Council Synthesis (GPT vs Gemini disagreement, Claude resolution)

---

**Last Updated:** 2026-01-22  
**Status:** Accepted  
**Next Review:** After Phase 1 (Month 3) - profile workload, revisit decision
