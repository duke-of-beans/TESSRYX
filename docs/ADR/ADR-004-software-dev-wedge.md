# ADR-004: Choose Software Development as Initial Wedge Market

**Status:** Accepted  
**Date:** 2026-01-22  
**Deciders:** David Kirsch, Genius Council (unanimous recommendation)  
**Tags:** #strategy #go-to-market #market-segment #wedge

---

## Context

TESSRYX's universal dependency intelligence works across many domains (software, operations, manufacturing, construction, supply chain). We must choose an initial "wedge" market for V1 to validate the product before expanding.

**Candidate Wedge Markets:**
1. Software Development (npm/pip/Maven dependency management)
2. Automotive Manufacturing (supply chain dependencies)
3. IT Operations (infrastructure dependencies)
4. Construction/AEC (BIM dependencies)
5. ERP Systems (business process dependencies)

**Evaluation Criteria:**
- Data availability (can we get dependency data easily?)
- Pain severity (how acute is the problem?)
- Market size (TAM, SAM, SOM)
- Sales cycle (how long to first customer?)
- Technical buyers (understand constraint solving?)
- Validation speed (days, weeks, or months?)

**Key Insight from Genius Council:**
"Automotive is sexy, but software dev is smart." - GPT-4

---

## Decision

**We will target Software Development as the initial wedge market for V1 (months 1-12).**

**Specific Focus:**
- **Primary:** npm (Node.js), pip (Python), Maven (Java) dependency conflicts
- **Use Cases:** Version incompatibility, security vulnerabilities, breaking changes
- **Distribution:** GitHub Action, CLI tool, VSCode extension
- **Pricing:** Freemium (1K API calls/month) → Paid ($49-$499/month)

**Expansion Sequence:**
1. **V1 (Months 1-12):** Software Development (validate core)
2. **V2 (Year 2 Q1-Q2):** IT Operations (ServiceNow, infrastructure)
3. **V2 (Year 2 Q3-Q4):** ERP/Manufacturing (SAP, Dynamics)
4. **V3 (Year 3+):** Construction/AEC, Supply Chain

---

## Rationale

### Why Software Development Wins

**1. Data Immediately Available**
- **Problem:** Don't have automotive supplier contracts, BIM models, ERP access
- **Solution:** GitHub APIs, npm registry, PyPI, Maven Central are public
- **Impact:** Can build domain pack in weeks, not months

**Example:**
```bash
# Fetch npm dependency graph
curl https://registry.npmjs.org/express/latest

# Result: Complete dependency tree in JSON (free, instant)
```

Contrast: Automotive supplier dependencies require NDAs, procurement access, months of relationship building.

**2. Pain is Acute + Universal**
- **"Dependency Hell":** Every developer has experienced version conflicts
- **Breaking Changes:** ~30% of npm updates cause issues (research)
- **Security Vulnerabilities:** Log4Shell, Heartbleed affect millions
- **Quantifiable Cost:** $500B+ globally (Consortium for IT Software Quality)

**Survey Data:**
- 78% of developers spend >2 hours/week on dependency issues (Stack Overflow 2023)
- 42% have abandoned projects due to unmaintainable dependencies

**3. Fast Validation Cycle**
- **Deploy:** GitHub Action in 1 day
- **Test:** Run on public repos immediately
- **Feedback:** Users report issues in hours/days
- **Iterate:** Ship fixes same day

Contrast: Automotive factory deployment = 3-6 month sales cycle + 6-12 month pilot.

**4. Technical Buyers (Low Friction)**
- **Audience:** Developers understand constraint solving, graph theory
- **Decision:** Individual contributors can adopt (no procurement)
- **Payment:** Credit card ($49/month) not enterprise contract
- **Viral:** "This GitHub Action saved me 3 hours" → organic growth

**5. Massive Market**
- **TAM:** 27 million developers globally (Stack Overflow)
- **SAM:** 10 million use npm/pip/Maven (target audience)
- **SOM:** 100K developers in first year (0.4% market share)

**Revenue Potential:**
- 100K free users (top of funnel)
- 10K paid users at $49/month = $490K MRR = $5.9M ARR (Year 1)
- 1K enterprise at $499/month = $499K MRR = $6M ARR (Year 2)

**6. Network Effects**
- **Validated Libraries:** Developers contribute dependency fixes
- **Community Curation:** Upvote/downvote dependency recommendations
- **Cross-Project Learning:** Package X always conflicts with Y (crowdsourced)

**7. Proven Pattern**
- **Precedents:** Dependabot, Snyk, Renovate (all started with software deps)
- **Expansion:** Snyk →  security, Renovate → infrastructure-as-code
- **Validation:** Market exists, willingness to pay proven

---

## Alternatives Considered

### Automotive Manufacturing
**Pros:**
- David's domain expertise (VP Operations, cannabis manufacturing)
- High-value contracts ($500K-$5M deals)
- Complex dependencies (perfect TESSRYX showcase)
- Regulatory compliance (safety-critical)

**Cons:**
- **Data Access:** Suppliers guard data fiercely (competitive advantage)
- **Sales Cycle:** 12-18 months (RFP, pilot, procurement)
- **Validation:** Slow feedback (months to see impact)
- **Adoption Risk:** Factory changes costly, risk-averse culture
- **Market Entry:** Need industry relationships, certifications

**Why Rejected:**
- **Critical Flaw:** Cannot build without data access
- **Risk:** Bet entire company on 2-3 enterprise deals (eggs in one basket)
- **Timing:** Better as expansion market after validation

---

### IT Operations
**Pros:**
- Significant market (every company has IT ops)
- Integration points (ServiceNow, Datadog, PagerDuty)
- Recurring revenue (SaaS-friendly)
- Mid-market + enterprise buyers

**Cons:**
- **Competitive:** Existing tools (Terraform, CloudFormation) have adjacency
- **Adoption:** Requires integration with proprietary systems
- **Data:** Configuration management data not as accessible as npm
- **Use Case:** Less acute than software deps (workarounds exist)

**Why Deferred:** Good second market (Year 2), not first.

---

### Construction/AEC
**Pros:**
- Huge market ($10 trillion construction industry)
- Complex dependencies (BIM data, supply chain)
- Regulatory requirements (building codes, permits)

**Cons:**
- **BIM Access:** Proprietary formats (Revit, ArchiCAD)
- **Sales Cycle:** 18-24 months (construction timelines)
- **Domain Expertise:** Need to learn industry deeply
- **Tech Adoption:** Industry slower than software (risk-averse)

**Why Deferred:** Compelling long-term (Year 3+), too slow for validation.

---

### ERP Systems (SAP, Dynamics, Oracle)
**Pros:**
- Enterprise budgets ($100K+ contracts)
- Integration opportunity (become SAP partner)
- Existing dependency data (supply chain, procurement)

**Cons:**
- **Integration Complexity:** ERP APIs difficult, expensive
- **Sales Cycle:** 12-18 months (enterprise procurement)
- **Chicken-Egg:** Need customer to get ERP access, but need product to get customer
- **Competition:** SAP/Oracle might build competing features

**Why Deferred:** Better as Year 2 expansion after proving software dev.

---

## Consequences

### Positive

**1. Fast Time to First Customer**
- Launch GitHub Action Month 4
- First paying customer Month 5-6 (target)
- 100 paying customers Month 12 (target)

**2. Rapid Iteration**
- Daily deployments (SaaS + GitHub Action)
- Real-time feedback (GitHub issues, Discord)
- A/B testing (different pricing, features)

**3. Low Customer Acquisition Cost**
- Content marketing (blog posts, demos)
- GitHub presence (stars, forks, activity)
- Conference talks (PyCon, JSConf)
- Viral growth (developers share tools)

**4. Proof of Concept for Other Domains**
- Software dev validates core technology
- Case studies convince enterprises (automotive, construction)
- "We solved npm hell" → "We can solve your supplier hell"

**5. Developer Community**
- Enthusiast contributors (OSS maintainers)
- Educational use cases (universities teaching dependency management)
- Talent pipeline (hire from community)

### Negative

**1. Lower Contract Value**
- $49-$499/month (vs automotive $500K deals)
- Need volume to hit revenue targets (100s-1000s of customers)
- More churn risk (monthly subscriptions)

**Mitigation:**
- Freemium converts well (10% conversion target)
- Annual plans reduce churn (20% discount)
- Enterprise tier ($999+/month) for large orgs

**2. Competitive Landscape**
- Renovate, Dependabot exist (renovatebot.com, github.com/dependabot)
- Snyk, Socket.dev have adjacency (security focus)
- Need clear differentiation

**Mitigation:**
- **TESSRYX Advantage:** Constraint solving (proves feasibility, not just alerts)
- **TESSRYX Advantage:** Multi-path analysis (finds alternative solutions)
- **TESSRYX Advantage:** Cross-language (npm + pip + Maven unified)

**3. Feature Creep Risk**
- Developers will request many features
- Easy to lose focus (become generic tool)

**Mitigation:**
- Clear product principles (dependency intelligence, not project management)
- Ruthless prioritization (constraint solving core, everything else secondary)

**4. Automotive Pivot Delayed**
- David's domain expertise underutilized initially
- Potential regret if software dev doesn't work

**Mitigation:**
- Validate quickly (6 months to Product-Market Fit test)
- Automotive remains strategic (Year 2-3 expansion)
- Learning from software dev applies to automotive

### Neutral

**1. Domain Expertise Learning**
- Need to deeply understand npm, pip, Maven ecosystems
- Requires research, experimentation
- But: Easier to learn than automotive supply chain

**2. Developer-First Culture**
- Affects hiring (need devs who love tools)
- Affects marketing (GitHub, not trade shows)
- Actually aligns well with technical founding team

---

## Go-To-Market Strategy

### Phase 1: Open Source Release (Month 4)
- Publish TessIR spec + reference implementation
- Launch GitHub Action (free tier)
- Blog post: "Solving Dependency Hell with Constraint Solving"
- Post on HN, Reddit r/programming, Dev.to

**Target:** 1K GitHub stars, 100 free users

### Phase 2: Freemium SaaS (Month 6)
- Web app: Upload package.json, see dependency conflicts
- API: 1K calls/month free, $49/month for 10K calls
- CLI tool: `tessryx validate package.json`
- VSCode extension: Real-time dependency validation

**Target:** 10K free users, 100 paying customers

### Phase 3: Enterprise Features (Month 9)
- Team collaboration (shared dependency libraries)
- SSO integration (Okta, Auth0)
- Audit logs, compliance reports
- Premium support (Slack channel, 4-hour SLA)

**Target:** 10 enterprise customers at $499-$999/month

### Phase 4: Expansion Markets (Year 2)
- IT Ops domain pack (Terraform, Kubernetes)
- Cross-language unified view (npm + pip + Maven)
- CI/CD integrations (Jenkins, CircleCI, GitLab)

**Target:** $1M ARR, 1K paying customers

---

## Validation Criteria

**3-Month Checkpoint (Software Dev PMF Test):**
- [ ] 1K+ GitHub stars on open-source repos
- [ ] 100+ active free users (GitHub Action runs)
- [ ] 10+ paying customers (any tier)
- [ ] Positive NPS (>30)
- [ ] Users report time savings (quantified)

**6-Month Go/No-Go Decision:**
- [ ] 10K+ free users
- [ ] 100+ paying customers
- [ ] $5K+ MRR
- [ ] <5% monthly churn
- [ ] 3+ case studies (blog posts, testimonials)

**If Fail:** Pivot to IT Ops or explore automotive (reassess)

**12-Month Success Metrics:**
- [ ] 100K+ free users
- [ ] 1K+ paying customers
- [ ] $50K+ MRR ($600K ARR)
- [ ] Featured on GitHub Marketplace (top 10 in category)
- [ ] Conference talk accepted (PyCon, JSConf, StrangeLoop)

---

## Expansion Roadmap

### Year 2: IT Operations
- ServiceNow connector (CMDB dependencies)
- Terraform/Kubernetes (infrastructure-as-code)
- Datadog/PagerDuty (incident causality)

**Lever:** "Solved software deps, now ops deps"

### Year 2-3: ERP/Manufacturing
- SAP integration (supply chain dependencies)
- Microsoft Dynamics (business process flows)
- Oracle E-Business Suite

**Lever:** "Saved developers $X, now save procurement $Y"

### Year 3+: Construction/AEC
- BIM integration (Revit, Autodesk)
- Project management (Procore, PlanGrid)
- Regulatory compliance (building codes)

**Lever:** "Complex industries trust us (auto, ERP), now construction"

---

## Related Decisions

- **ADR-003:** Open TessIR spec (accelerates software dev adoption)
- **ADR-001:** Python for V1 (aligns with dev tools ecosystem)
- **ADR-005:** Solver strategy (critical for dependency conflict resolution)

---

## References

- [Stack Overflow Developer Survey 2023](https://survey.stackoverflow.co/2023/)
- [The Cost of Poor Software Quality (CISQ)](https://www.it-cisq.org/)
- [Wedge Strategy Framework](https://www.nfx.com/post/10-pitfalls-wedge-strategy)
- [Dependabot Case Study](https://github.blog/news-insights/company-news/github-acquires-dependabot/)
- [Snyk Funding History](https://www.crunchbase.com/organization/snyk)
- Genius Council Synthesis (unanimous recommendation)

---

**Last Updated:** 2026-01-22  
**Status:** Accepted  
**Next Review:** Month 6 (Go/No-Go decision based on PMF metrics)
