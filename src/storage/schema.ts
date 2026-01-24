/**
 * TESSRYX Storage Schema
 * 
 * Universal graph database schema for dependency intelligence.
 * Supports multi-domain constraints, rich metadata, and resolution state tracking.
 * 
 * Design Principles:
 * - Domain-agnostic core with extensible domain-specific metadata
 * - Constraint-first: All edges carry constraint information
 * - Provenance tracking: Know where every piece of data came from
 * - Resolution state: Track what's been resolved and why
 * - Temporal awareness: Support version ranges and time-based constraints
 */

// ============================================================================
// CORE GRAPH PRIMITIVES
// ============================================================================

/**
 * Universal node representing any dependency entity across domains
 * 
 * Examples:
 * - NPM package: { domain: 'npm', identifier: 'react', version: '18.2.0' }
 * - Database table: { domain: 'database', identifier: 'users', version: 'v2' }
 * - API endpoint: { domain: 'api', identifier: '/api/users', version: '2.0' }
 */
export interface DependencyNode {
  // Core identity
  id: string;                    // Unique node identifier (hash of domain + identifier + version)
  domain: DomainType;            // Which domain this belongs to
  identifier: string;            // Domain-specific identifier (package name, file path, etc.)
  version?: string;              // Optional version (may be range, hash, tag, etc.)
  
  // Rich metadata
  metadata: NodeMetadata;
  
  // Graph relationships
  dependencies: EdgeReference[]; // Outgoing edges (this depends on...)
  dependents: EdgeReference[];   // Incoming edges (...depends on this)
  
  // Resolution state
  resolution: ResolutionState;
  
  // Provenance
  provenance: ProvenanceInfo;
}

export type DomainType = 
  | 'npm'           // JavaScript packages
  | 'python'        // Python packages
  | 'database'      // Database schemas/tables
  | 'api'           // API endpoints
  | 'service'       // Microservices
  | 'infrastructure' // Infrastructure components
  | 'calendar'      // Calendar/scheduling
  | 'generic';      // Fallback for unknown domains

export interface NodeMetadata {
  // Domain-agnostic properties
  name?: string;                 // Human-readable name
  description?: string;          // What this node represents
  tags: string[];                // Categorization tags
  
  // Domain-specific metadata (extensible)
  domainSpecific: Record<string, any>;
  
  // Lifecycle
  deprecated?: boolean;
  deprecationMessage?: string;
  sunset?: Date;                 // When this will be removed
  
  // Quality signals
  stability?: 'stable' | 'beta' | 'alpha' | 'experimental';
  securityScore?: number;        // 0-100 security assessment
  popularityScore?: number;      // Usage/adoption metric
}

/**
 * Edge representing a dependency relationship with constraints
 * 
 * Every edge is a constraint - it specifies how one node depends on another
 */
export interface DependencyEdge {
  id: string;                    // Unique edge identifier
  
  // Relationship
  source: string;                // Node ID that has the dependency
  target: string;                // Node ID being depended upon
  type: EdgeType;                // What kind of dependency
  
  // Constraints (the core intelligence)
  constraints: Constraint[];
  
  // Metadata
  metadata: EdgeMetadata;
  
  // Provenance
  provenance: ProvenanceInfo;
}

export type EdgeType =
  | 'requires'          // Hard dependency (must have)
  | 'recommends'        // Soft dependency (nice to have)
  | 'conflicts'         // Mutual exclusion
  | 'replaces'          // Supersedes/deprecates
  | 'provides'          // Fulfills requirement
  | 'enhances';         // Optional enhancement

export interface EdgeMetadata {
  // Relationship properties
  optional: boolean;             // Can be omitted
  development: boolean;          // Only needed in dev
  peer: boolean;                 // Must be provided by parent
  
  // Scope
  scope?: string;                // Where this applies (runtime, build, test, etc.)
  
  // Conditions
  conditional?: string;          // When this edge applies (env vars, feature flags)
  
  // Domain-specific
  domainSpecific: Record<string, any>;
}

/**
 * Reference to an edge from a node's perspective
 */
export interface EdgeReference {
  edgeId: string;
  nodeId: string;                // The other node in the relationship
  type: EdgeType;
  direction: 'outgoing' | 'incoming';
}

// ============================================================================
// CONSTRAINT SYSTEM
// ============================================================================

/**
 * Universal constraint representation
 * 
 * Based on our comprehensive constraint taxonomy from Phase 0.
 * Supports versioning, resources, temporal, logical, and custom constraints.
 */
export interface Constraint {
  id: string;
  category: ConstraintCategory;
  type: ConstraintType;
  
  // The actual constraint specification
  specification: ConstraintSpec;
  
  // Metadata
  severity: 'required' | 'recommended' | 'optional';
  priority: number;              // For conflict resolution (higher = more important)
  
  // Provenance
  source: string;                // Where this constraint came from
  reason?: string;               // Why this constraint exists
}

export type ConstraintCategory =
  | 'version'
  | 'resource'
  | 'temporal'
  | 'logical'
  | 'custom';

export type ConstraintType =
  // Version constraints
  | 'semantic_range'      // ^1.2.3, ~2.0.0, >=3.0.0
  | 'exact_version'       // 1.2.3
  | 'version_set'         // 1.2.3 || 2.0.0
  | 'git_ref'             // commit hash, branch, tag
  
  // Resource constraints
  | 'memory_limit'
  | 'cpu_limit'
  | 'disk_space'
  | 'network_bandwidth'
  | 'concurrent_limit'
  
  // Temporal constraints
  | 'time_window'         // Must occur within timeframe
  | 'before'              // Must happen before X
  | 'after'               // Must happen after X
  | 'duration'            // Max/min duration
  
  // Logical constraints
  | 'mutex'               // Mutually exclusive
  | 'requires_all'        // AND relationship
  | 'requires_any'        // OR relationship
  | 'requires_none'       // NOT relationship
  
  // Custom domain-specific
  | 'custom';

/**
 * Constraint specification - the actual constraint data
 * 
 * Highly extensible to support domain-specific needs
 */
export interface ConstraintSpec {
  // For version constraints
  versionRange?: string;
  versionOperator?: '<' | '<=' | '=' | '>=' | '>' | '!=' | '^' | '~';
  versions?: string[];           // For version sets
  
  // For resource constraints
  minValue?: number;
  maxValue?: number;
  unit?: string;                 // 'MB', 'GB', 'ms', 'connections', etc.
  
  // For temporal constraints
  startTime?: Date;
  endTime?: Date;
  duration?: number;
  durationUnit?: 'ms' | 's' | 'm' | 'h' | 'd';
  
  // For logical constraints
  targetNodes?: string[];        // Node IDs this constraint references
  
  // Custom constraint data
  custom?: Record<string, any>;
  
  // Human-readable expression
  expression: string;            // "^1.2.3", "<= 100MB", "9am-5pm", etc.
}

// ============================================================================
// RESOLUTION STATE
// ============================================================================

/**
 * Tracks the resolution state of a node or edge
 * 
 * Records what decisions have been made and why
 */
export interface ResolutionState {
  status: ResolutionStatus;
  
  // Resolution details
  resolvedVersion?: string;      // What version was selected
  resolvedAt?: Date;             // When resolution happened
  resolvedBy?: string;           // What resolver made the decision
  
  // Decision rationale
  reason?: string;               // Why this resolution was chosen
  constraints: ResolvedConstraint[]; // Which constraints were satisfied
  
  // Conflicts
  conflicts?: ConflictInfo[];    // Any conflicts encountered
  
  // Validation
  validated: boolean;            // Has this been validated
  validationErrors?: string[];   // Any validation failures
}

export type ResolutionStatus =
  | 'unresolved'        // Not yet processed
  | 'resolving'         // Currently being resolved
  | 'resolved'          // Successfully resolved
  | 'conflict'          // Has unresolvable conflicts
  | 'invalid'           // Failed validation
  | 'skipped';          // Intentionally skipped

export interface ResolvedConstraint {
  constraintId: string;
  satisfied: boolean;
  value?: any;                   // The resolved value
  reason?: string;               // Why/how it was satisfied
}

export interface ConflictInfo {
  conflictType: 'version' | 'resource' | 'temporal' | 'logical';
  description: string;
  involvedNodes: string[];       // Node IDs in conflict
  involvedConstraints: string[]; // Constraint IDs in conflict
  resolution?: string;           // How conflict was resolved (if at all)
  overridden?: boolean;          // Was this conflict force-resolved
}

// ============================================================================
// PROVENANCE & METADATA
// ============================================================================

/**
 * Tracks where data came from and how confident we are
 */
export interface ProvenanceInfo {
  // Source information
  source: DataSource;
  sourceIdentifier: string;      // File path, URL, package.json, etc.
  
  // Discovery
  discoveredAt: Date;
  discoveredBy: string;          // Which parser/analyzer found this
  
  // Confidence
  confidence: number;            // 0-1 confidence score
  confidenceReason?: string;     // Why this confidence level
  
  // Lineage
  derivedFrom?: string[];        // Parent data sources
  
  // Validation
  verified: boolean;             // Has this been verified
  verificationMethod?: string;   // How it was verified
}

export type DataSource =
  | 'package_manifest'   // package.json, pyproject.toml, etc.
  | 'lock_file'          // package-lock.json, poetry.lock, etc.
  | 'source_code'        // Parsed from actual code
  | 'api_spec'           // OpenAPI, GraphQL schema, etc.
  | 'database_schema'    // SQL DDL, migrations, etc.
  | 'configuration'      // Config files
  | 'documentation'      // Extracted from docs
  | 'runtime_analysis'   // Observed at runtime
  | 'user_defined'       // Manually specified
  | 'inferred';          // Derived from other data

// ============================================================================
// GRAPH OPERATIONS
// ============================================================================

/**
 * Query parameters for finding nodes
 */
export interface NodeQuery {
  domain?: DomainType | DomainType[];
  identifier?: string | RegExp;
  version?: string;
  tags?: string[];
  
  // Metadata filters
  deprecated?: boolean;
  stability?: NodeMetadata['stability'];
  
  // Resolution filters
  status?: ResolutionStatus | ResolutionStatus[];
  
  // Graph filters
  hasConstraints?: boolean;
  hasConflicts?: boolean;
}

/**
 * Query parameters for finding edges
 */
export interface EdgeQuery {
  source?: string | string[];
  target?: string | string[];
  type?: EdgeType | EdgeType[];
  
  // Metadata filters
  optional?: boolean;
  development?: boolean;
  scope?: string;
  
  // Constraint filters
  constraintCategory?: ConstraintCategory;
  constraintType?: ConstraintType;
}

/**
 * Graph traversal options
 */
export interface TraversalOptions {
  direction: 'forward' | 'backward' | 'both';
  maxDepth?: number;
  includeTypes?: EdgeType[];
  excludeTypes?: EdgeType[];
  
  // Filtering
  filter?: (node: DependencyNode, edge?: DependencyEdge) => boolean;
  
  // Termination
  stopCondition?: (node: DependencyNode, depth: number) => boolean;
}

// ============================================================================
// BATCH OPERATIONS
// ============================================================================

/**
 * Batch update for efficient bulk operations
 */
export interface BatchOperation {
  type: 'create' | 'update' | 'delete';
  entity: 'node' | 'edge';
  data: Partial<DependencyNode | DependencyEdge>;
  conditions?: Record<string, any>;
}

export interface BatchResult {
  successful: number;
  failed: number;
  errors: Array<{ operation: BatchOperation; error: string }>;
}

// ============================================================================
// INDEXES & OPTIMIZATION
// ============================================================================

/**
 * Index definitions for query optimization
 */
export interface IndexDefinition {
  name: string;
  entity: 'node' | 'edge';
  fields: string[];
  unique?: boolean;
  sparse?: boolean;
}

/**
 * Standard indexes we'll create
 */
export const STANDARD_INDEXES: IndexDefinition[] = [
  // Node indexes
  { name: 'node_domain_identifier', entity: 'node', fields: ['domain', 'identifier'] },
  { name: 'node_domain_identifier_version', entity: 'node', fields: ['domain', 'identifier', 'version'], unique: true },
  { name: 'node_resolution_status', entity: 'node', fields: ['resolution.status'] },
  { name: 'node_tags', entity: 'node', fields: ['metadata.tags'] },
  
  // Edge indexes
  { name: 'edge_source', entity: 'edge', fields: ['source'] },
  { name: 'edge_target', entity: 'edge', fields: ['target'] },
  { name: 'edge_type', entity: 'edge', fields: ['type'] },
  { name: 'edge_source_target', entity: 'edge', fields: ['source', 'target'] },
];

// ============================================================================
// TYPE GUARDS
// ============================================================================

export function isDependencyNode(obj: any): obj is DependencyNode {
  return (
    typeof obj === 'object' &&
    typeof obj.id === 'string' &&
    typeof obj.domain === 'string' &&
    typeof obj.identifier === 'string' &&
    typeof obj.metadata === 'object' &&
    Array.isArray(obj.dependencies) &&
    Array.isArray(obj.dependents) &&
    typeof obj.resolution === 'object' &&
    typeof obj.provenance === 'object'
  );
}

export function isDependencyEdge(obj: any): obj is DependencyEdge {
  return (
    typeof obj === 'object' &&
    typeof obj.id === 'string' &&
    typeof obj.source === 'string' &&
    typeof obj.target === 'string' &&
    typeof obj.type === 'string' &&
    Array.isArray(obj.constraints) &&
    typeof obj.metadata === 'object' &&
    typeof obj.provenance === 'object'
  );
}

export function isConstraint(obj: any): obj is Constraint {
  return (
    typeof obj === 'object' &&
    typeof obj.id === 'string' &&
    typeof obj.category === 'string' &&
    typeof obj.type === 'string' &&
    typeof obj.specification === 'object' &&
    typeof obj.severity === 'string' &&
    typeof obj.priority === 'number' &&
    typeof obj.source === 'string'
  );
}
