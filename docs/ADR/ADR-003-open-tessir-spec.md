# ADR-003: Publish TessIR as Open Standard

**Status:** Accepted  
**Date:** 2026-01-22  
**Deciders:** David Kirsch, Genius Council (GPT explicit recommendation)  
**Tags:** #strategy #open-source #ecosystem #standard

---

## Context

TESSRYX's core value is the TessIR intermediate representation - a universal format for dependency intelligence. We must decide whether to keep TessIR proprietary or publish it as an open standard.

**Strategic Questions:**
1. Can we build defensible moat with open spec?
2. Does openness accelerate or hinder adoption?
3. What do we monetize if spec is free?
4. Risk of competitors using our spec?

**Industry Precedents:**
- **Open Standards:** JSON Schema, OpenAPI, GraphQL, LLVM IR
- **Closed Standards:** AWS CloudFormation, Azure Resource Manager
- **Hybrid:** Docker (spec open, Docker Inc proprietary features)

**Genius Council Input:**
- **GPT-4:** Explicit recommendation to publish as open standard
- **Gemini 2.0:** Agreed, emphasized ecosystem benefits
- **Claude:** Synthesized strategic positioning

---

## Decision

**We will publish TessIR v1.0 as an open standard under permissive license (Apache 2.0).**

**What's Open:**
- TessIR specification (complete formal document)
- Reference implementation (Python, MIT license)
- Conformance test suite (50 scenarios)
- Domain Pack template
- API specification (OpenAPI)

**What's Proprietary (Commercial):**
- **Validated Domain Packs:** Professionally curated, community-verified
- **Enterprise Connectors:** SAP, Oracle, ServiceNow, BIM systems
- **SaaS Platform:** Managed hosting, collaboration, API access
- **Professional Services:** Custom domain packs, integration, training
- **Advanced Features:** Real-time sync, enterprise SSO, compliance audit logs

**License Strategy:**
- **Spec:** Creative Commons CC-BY 4.0 (attribution required)
- **Reference Impl:** MIT License (maximum permissiveness)
- **Domain Packs:** Mix of MIT (basic) + commercial (verified)

---

## Rationale

### Why Open Wins

**1. Become "The Standard" (Network Effects)**
- **Goal:** TessIR becomes the "JSON Schema of dependencies"
- **Mechanism:** Developers adopt because it's open, safe, universal
- **Outcome:** We don't own the spec, we own the *ecosystem*
- **Precedent:** JSON Schema (specification org), actual tools monetized separately

**2. Accelerate Ecosystem Growth**
- **Contributors:** Universities, researchers, open-source devs can extend
- **Integrations:** Third parties build adapters, importers, tooling
- **Validation:** More eyes = fewer bugs, better design
- **Network Effect:** More users → better domain packs → more users

**3. Trust Through Transparency**
- **Problem:** Dependency intelligence requires trust (critical infrastructure)
- **Solution:** Open spec → auditable, no lock-in, community governance
- **Impact:** Enterprises more willing to adopt (not locked to one vendor)

**4. Competitive Differentiation**
- **What We Sell:** Implementation quality, validated data, convenience
- **Not:** The format itself (commodity)
- **Analogy:** PostgreSQL (open) vs AWS RDS (managed), Supabase (platform)

**5. Regulatory/Compliance Advantage**
- **Open Standard:** Easier to get approved by risk/compliance teams
- **Auditable:** Security teams can review spec, validate implementation
- **No Lock-In:** Enterprises demand interoperability, data portability

**6. Academic/Research Adoption**
- **Citations:** Papers reference TessIR as standard
- **Validation:** Academic rigor improves quality
- **Talent Pipeline:** Students learn TessIR, join industry pre-trained

**7. Strategic Moat Is Implementation, Not Spec**
- **Real Moat:** Validated dependency libraries (crowd-sourced + curated)
- **Real Moat:** Provenance infrastructure (trust layer)
- **Real Moat:** Domain pack ecosystem (network effects)
- **Real Moat:** Solver performance (engineering excellence)
- **Spec Itself:** Commodity (like HTTP, JSON, SQL)

---

## Alternatives Considered

### Proprietary Spec (Closed)
**Pros:**
- Control over evolution
- Can charge for spec access
- Competitors can't use directly

**Cons:**
- Slower adoption (trust issues)
- No community contributions
- Reinventing wheel (others build competing specs)
- Compliance/approval harder (black box)
- Academic research limited (no citation)

**Why Rejected:** Fundamentally misunderstands value creation. Standard itself has little value; ecosystem has all the value.

---

### Hybrid: Core Open, Extensions Closed
**Pros:**
- Open core for adoption
- Monetize advanced features (constraint types, solver extensions)

**Cons:**
- Confusion about what's open vs closed
- Community fragments (OSS vs commercial)
- Trust diminished (bait-and-switch perception)
- Hard to define boundary (where's the line?)

**Why Rejected:** Worse of both worlds. Better to be fully open and monetize services/data.

---

### Permissive License (BSD/MIT) for Everything
**Pros:**
- Maximum freedom
- No restrictions on commercial use
- GitHub-friendly

**Cons:**
- Miss opportunity for attribution
- Competitors can fork without credit

**Why Rejected:** CC-BY 4.0 for spec ensures attribution while staying open. MIT for code is fine (standard practice).

---

### Copyleft License (GPL) for Reference Implementation
**Pros:**
- Forces derivatives to stay open
- Prevents closed-source forks

**Cons:**
- Enterprises avoid GPL (legal concerns)
- Limits commercial ecosystem
- Discourages proprietary integrations

**Why Rejected:** GPL achieves openness through coercion. We want opt-in openness through value.

---

## Consequences

### Positive

**1. Faster Adoption**
- No sales friction ("it's an open standard, we can audit it")
- Developers trust open > closed (default)
- CIOs feel safe (no vendor lock-in)

**2. Community Contributions**
- PhD students publish papers on TessIR extensions
- Open-source devs build tooling, integrations
- Bug reports, security audits from community

**3. Academic Validation**
- Universities teach TessIR in courses
- Research papers cite specification
- Conferences present on TessIR applications

**4. Interoperability**
- Multiple implementations (Python, Rust, Go, Java)
- Cross-tool compatibility (import/export)
- Standards body formation potential (future)

**5. Strategic Positioning**
- TESSRYX becomes "the experts on TessIR"
- Consultancy opportunities (custom implementations)
- Conference talks, book deals, thought leadership

### Negative

**1. Competitors Can Use Our Spec**
- **Risk:** Another company builds on TessIR, competes directly
- **Mitigation:** Implementation quality, validated data, network effects
- **Reality:** Better they use our standard than invent competing one

**Example:** PostgreSQL open → AWS RDS, Supabase, Neon profit

**2. No Spec Licensing Revenue**
- **Lost:** Can't charge per-deployment licensing fees
- **Gain:** Ecosystem grows faster, services/data monetize better

**Example:** Terraform open spec → HashiCorp makes $200M+ on services

**3. Governance Burden**
- **Issue:** Who decides TessIR v2.0 features?
- **Solution:** Benevolent dictator (David) for v1-2, community RFC process v3+
- **Precedent:** Python PEPs, Rust RFCs, TypeScript proposals

**4. Attribution Challenges**
- **Risk:** Companies use TessIR, don't credit TESSRYX
- **Mitigation:** CC-BY 4.0 requires attribution (legally)
- **Reality:** Most users will credit anyway (community norm)

### Neutral

**1. Requires Public Roadmap**
- Open spec = public evolution
- Competitors see our direction
- But also: community input improves decisions

**2. Version Backward Compatibility**
- Open standard means breaking changes costly
- Forces us to design well first time
- Actually good discipline (prevents technical debt)

---

## Monetization Strategy (Given Open Spec)

### Revenue Model Overview
```
Open (Free):
  - TessIR specification
  - Reference Python implementation
  - 50 canonical test scenarios
  - Basic software dev domain pack

Freemium (SaaS):
  - API access (1K calls/month free)
  - Basic web UI
  - Community support

Paid (Tiered):
  - Verified domain packs ($99-$499/pack)
  - API access (10K-1M calls/month: $49-$499/mo)
  - Enterprise connectors (SAP, Oracle: $999+/mo)
  - Professional services (custom: $5K-$50K projects)
```

### Ecosystem Revenue Opportunities
1. **Training/Certification:** "Certified TessIR Architect" program
2. **Consulting:** Help enterprises adopt TessIR
3. **Managed Hosting:** "TessIR Cloud" (like Supabase for Postgres)
4. **Validated Libraries:** Crowd-sourced + curated dependency data
5. **Enterprise Features:** SSO, audit logs, compliance reports

---

## Implementation Plan

### Phase 1: Initial Publication (Month 4)
- [ ] Publish TessIR v1.0 specification (GitHub, website)
- [ ] Release reference Python implementation (MIT license)
- [ ] Announce on HN, Reddit r/programming, Twitter
- [ ] Submit to standards aggregators (specifications.org)

### Phase 2: Community Building (Months 5-8)
- [ ] Create Discord/Slack for community
- [ ] Host monthly community calls
- [ ] Publish blog posts on TessIR use cases
- [ ] Speak at conferences (PyCon, FOSDEM, StrangeLoop)

### Phase 3: Governance Formalization (Months 9-12)
- [ ] RFC process for TessIR v2.0 features
- [ ] Contributor guidelines
- [ ] Trademark policy (protect "TessIR" name)
- [ ] Consider foundation (Apache, Linux Foundation)

### Phase 4: Ecosystem Growth (Year 2)
- [ ] Official implementations in Rust, Go, Java
- [ ] Integration with popular tools (CI/CD, IDEs)
- [ ] Annual TessIR conference ("TessRyxConf")

---

## Validation Criteria

**Success Metrics (12 months):**
- [ ] 100+ GitHub stars on spec repo
- [ ] 10+ community-contributed domain packs
- [ ] 3+ independent implementations (not by TESSRYX)
- [ ] 5+ academic papers citing TessIR
- [ ] 1+ enterprise adoption (Fortune 1000)

**Failure Signals (re-evaluate if):**
- Zero community contributions after 6 months
- Competitors build closed alternatives (spec ignored)
- Users prefer proprietary formats (resistance to open)

---

## Risk Mitigation

### Competitor Uses TessIR, Competes
**Mitigation:**
- Focus on implementation quality (10x better than others)
- Build validated dependency libraries (network effect)
- Offer best managed service (convenience)
- Brand recognition ("We invented TessIR")

### Spec Forks/Fragmentation
**Mitigation:**
- Strong governance (benevolent dictator, clear RFC process)
- Fast iteration (v1.1, v1.2 addressing community needs)
- Conformance test suite (certify implementations)
- Trademark protection on "TessIR" name

### Attribution Not Given
**Mitigation:**
- CC-BY 4.0 legally requires attribution
- Community policing (call out violators)
- Most organizations respect norms (risk reputation)

---

## Related Decisions

- **ADR-004:** Software Development wedge (open spec enables fast adoption)
- Revenue model in DNA.md (open core, paid services)

---

## References

- [The Cathedral and the Bazaar](http://www.catb.org/esr/writings/cathedral-bazaar/) (Eric Raymond)
- [Open Standards vs Open Source](https://opensource.com/article/17/11/open-standards-vs-open-source)
- [JSON Schema as Open Standard](https://json-schema.org/)
- [OpenAPI Initiative](https://www.openapis.org/)
- [GraphQL Specification](https://spec.graphql.org/)
- Genius Council Synthesis (GPT explicit recommendation)

---

**Last Updated:** 2026-01-22  
**Status:** Accepted  
**Next Review:** After Phase 1 release (Month 4) - track adoption metrics
