/**
 * TESSRYX Storage Interface
 * 
 * Defines the contract for the storage layer - the API that the rest of TESSRYX
 * uses to interact with the dependency graph database.
 * 
 * This interface is implementation-agnostic - we can swap out the underlying
 * storage engine (in-memory, SQLite, Neo4j, etc.) without changing the rest
 * of the system.
 * 
 * Design Principles:
 * - Simple, intuitive API
 * - Async-first (all operations return Promises)
 * - Type-safe with full TypeScript support
 * - Transaction support for atomic operations
 * - Efficient batch operations
 * - Rich query capabilities
 */

import {
  DependencyNode,
  DependencyEdge,
  Constraint,
  NodeQuery,
  EdgeQuery,
  TraversalOptions,
  BatchOperation,
  BatchResult,
  ResolutionState,
  ProvenanceInfo,
  IndexDefinition,
  DomainType,
  EdgeType,
} from './schema.js';

// ============================================================================
// STORAGE ENGINE INTERFACE
// ============================================================================

/**
 * The primary interface for interacting with TESSRYX's storage layer
 */
export interface IStorageEngine {
  // ========================================
  // Lifecycle Management
  // ========================================
  
  /**
   * Initialize the storage engine
   * Creates necessary tables/collections, indexes, etc.
   */
  initialize(): Promise<void>;
  
  /**
   * Close the storage engine gracefully
   * Flushes pending writes, closes connections
   */
  close(): Promise<void>;
  
  /**
   * Clear all data (dangerous - mainly for testing)
   */
  clear(): Promise<void>;
  
  /**
   * Get storage engine statistics
   */
  getStats(): Promise<StorageStats>;
  
  // ========================================
  // Node Operations
  // ========================================
  
  /**
   * Create a new node in the graph
   * Returns the created node with generated ID if not provided
   * 
   * @throws StorageError if node already exists (use upsertNode for update-or-create)
   */
  createNode(node: Partial<DependencyNode>): Promise<DependencyNode>;
  
  /**
   * Get a node by its ID
   * Returns null if not found
   */
  getNode(id: string): Promise<DependencyNode | null>;
  
  /**
   * Get a node by domain + identifier + version
   * More convenient than constructing the ID manually
   */
  getNodeByIdentity(
    domain: DomainType,
    identifier: string,
    version?: string
  ): Promise<DependencyNode | null>;
  
  /**
   * Update an existing node
   * Merges the provided data with existing node
   * 
   * @throws StorageError if node doesn't exist
   */
  updateNode(id: string, updates: Partial<DependencyNode>): Promise<DependencyNode>;
  
  /**
   * Create or update a node (upsert)
   * Creates if doesn't exist, updates if it does
   */
  upsertNode(node: Partial<DependencyNode>): Promise<DependencyNode>;
  
  /**
   * Delete a node and optionally its edges
   * 
   * @param cascade If true, also delete all edges connected to this node
   */
  deleteNode(id: string, cascade?: boolean): Promise<void>;
  
  /**
   * Query for nodes matching criteria
   * Returns array of matching nodes
   */
  queryNodes(query: NodeQuery): Promise<DependencyNode[]>;
  
  /**
   * Count nodes matching criteria (more efficient than queryNodes().length)
   */
  countNodes(query: NodeQuery): Promise<number>;
  
  // ========================================
  // Edge Operations
  // ========================================
  
  /**
   * Create a new edge between nodes
   * 
   * @throws StorageError if source or target node doesn't exist
   * @throws StorageError if edge already exists
   */
  createEdge(edge: Partial<DependencyEdge>): Promise<DependencyEdge>;
  
  /**
   * Get an edge by its ID
   */
  getEdge(id: string): Promise<DependencyEdge | null>;
  
  /**
   * Get all edges between two nodes (there may be multiple with different types)
   */
  getEdgesBetween(sourceId: string, targetId: string): Promise<DependencyEdge[]>;
  
  /**
   * Update an existing edge
   */
  updateEdge(id: string, updates: Partial<DependencyEdge>): Promise<DependencyEdge>;
  
  /**
   * Create or update an edge (upsert)
   */
  upsertEdge(edge: Partial<DependencyEdge>): Promise<DependencyEdge>;
  
  /**
   * Delete an edge
   * Updates source and target nodes to remove references
   */
  deleteEdge(id: string): Promise<void>;
  
  /**
   * Query for edges matching criteria
   */
  queryEdges(query: EdgeQuery): Promise<DependencyEdge[]>;
  
  /**
   * Count edges matching criteria
   */
  countEdges(query: EdgeQuery): Promise<number>;
  
  // ========================================
  // Graph Traversal
  // ========================================
  
  /**
   * Get all dependencies of a node (outgoing edges)
   * 
   * @param depth How many levels deep to traverse (default: 1)
   * @param includeTransitive If true, returns all transitive dependencies
   */
  getDependencies(
    nodeId: string,
    options?: Partial<TraversalOptions>
  ): Promise<DependencyNode[]>;
  
  /**
   * Get all dependents of a node (incoming edges)
   * 
   * @param depth How many levels deep to traverse (default: 1)
   */
  getDependents(
    nodeId: string,
    options?: Partial<TraversalOptions>
  ): Promise<DependencyNode[]>;
  
  /**
   * Traverse the graph starting from a node
   * Returns nodes in traversal order
   */
  traverse(
    startNodeId: string,
    options: TraversalOptions
  ): Promise<DependencyNode[]>;
  
  /**
   * Find all paths between two nodes
   * Returns array of paths, where each path is an array of node IDs
   */
  findPaths(
    sourceId: string,
    targetId: string,
    maxPaths?: number
  ): Promise<string[][]>;
  
  /**
   * Detect cycles in the graph
   * Returns arrays of node IDs forming cycles
   */
  detectCycles(startNodeId?: string): Promise<string[][]>;
  
  /**
   * Get the subgraph containing a node and its neighbors
   * 
   * @param radius How many hops to include (default: 1)
   */
  getSubgraph(
    nodeId: string,
    radius?: number
  ): Promise<{ nodes: DependencyNode[]; edges: DependencyEdge[] }>;
  
  // ========================================
  // Batch Operations
  // ========================================
  
  /**
   * Execute multiple operations in a batch
   * More efficient than individual operations
   */
  executeBatch(operations: BatchOperation[]): Promise<BatchResult>;
  
  /**
   * Import a graph from an external source
   * Efficiently loads nodes and edges in bulk
   */
  importGraph(data: {
    nodes: Partial<DependencyNode>[];
    edges: Partial<DependencyEdge>[];
  }): Promise<BatchResult>;
  
  /**
   * Export the entire graph or a subgraph
   */
  exportGraph(nodeIds?: string[]): Promise<{
    nodes: DependencyNode[];
    edges: DependencyEdge[];
  }>;
  
  // ========================================
  // Transaction Support
  // ========================================
  
  /**
   * Begin a transaction
   * All operations will be atomic until commit() or rollback()
   */
  beginTransaction(): Promise<ITransaction>;
  
  // ========================================
  // Index Management
  // ========================================
  
  /**
   * Create an index for faster queries
   */
  createIndex(index: IndexDefinition): Promise<void>;
  
  /**
   * Drop an index
   */
  dropIndex(indexName: string): Promise<void>;
  
  /**
   * List all indexes
   */
  listIndexes(): Promise<IndexDefinition[]>;
  
  // ========================================
  // Optimization & Maintenance
  // ========================================
  
  /**
   * Optimize the storage engine
   * Compacts data, rebuilds indexes, etc.
   */
  optimize(): Promise<void>;
  
  /**
   * Validate graph integrity
   * Checks for orphaned edges, invalid references, etc.
   */
  validateIntegrity(): Promise<IntegrityReport>;
  
  /**
   * Create a backup of the storage
   */
  backup(destination: string): Promise<void>;
  
  /**
   * Restore from a backup
   */
  restore(source: string): Promise<void>;
}

// ============================================================================
// TRANSACTION INTERFACE
// ============================================================================

/**
 * Transaction interface for atomic operations
 */
export interface ITransaction {
  /**
   * Commit the transaction
   * All changes become permanent
   */
  commit(): Promise<void>;
  
  /**
   * Rollback the transaction
   * All changes are discarded
   */
  rollback(): Promise<void>;
  
  /**
   * Check if transaction is still active
   */
  isActive(): boolean;
  
  // All regular storage operations available in transaction context
  createNode(node: Partial<DependencyNode>): Promise<DependencyNode>;
  getNode(id: string): Promise<DependencyNode | null>;
  updateNode(id: string, updates: Partial<DependencyNode>): Promise<DependencyNode>;
  deleteNode(id: string, cascade?: boolean): Promise<void>;
  
  createEdge(edge: Partial<DependencyEdge>): Promise<DependencyEdge>;
  getEdge(id: string): Promise<DependencyEdge | null>;
  updateEdge(id: string, updates: Partial<DependencyEdge>): Promise<DependencyEdge>;
  deleteEdge(id: string): Promise<void>;
}

// ============================================================================
// SUPPORTING TYPES
// ============================================================================

/**
 * Storage engine statistics
 */
export interface StorageStats {
  // Counts
  nodeCount: number;
  edgeCount: number;
  constraintCount: number;
  
  // By domain
  nodesByDomain: Record<DomainType, number>;
  edgesByType: Record<EdgeType, number>;
  
  // Resolution state
  resolvedNodes: number;
  unresolvedNodes: number;
  conflictedNodes: number;
  
  // Storage metrics
  storageSize: number;           // Bytes
  indexCount: number;
  
  // Performance
  avgQueryTime?: number;         // Milliseconds
  cacheHitRate?: number;         // 0-1
}

/**
 * Integrity validation report
 */
export interface IntegrityReport {
  valid: boolean;
  errors: IntegrityError[];
  warnings: IntegrityWarning[];
  
  // Statistics
  nodesChecked: number;
  edgesChecked: number;
  constraintsChecked: number;
}

export interface IntegrityError {
  type: 'orphaned_edge' | 'invalid_reference' | 'missing_constraint' | 'corrupted_data';
  entity: 'node' | 'edge';
  entityId: string;
  description: string;
  
  // Suggested fix
  fix?: string;
}

export interface IntegrityWarning {
  type: 'deprecated_node' | 'unresolved_conflict' | 'low_confidence' | 'missing_metadata';
  entity: 'node' | 'edge';
  entityId: string;
  description: string;
}

/**
 * Storage error types
 */
export class StorageError extends Error {
  constructor(
    message: string,
    public code: StorageErrorCode,
    public details?: any
  ) {
    super(message);
    this.name = 'StorageError';
  }
}

export type StorageErrorCode =
  | 'NOT_FOUND'
  | 'ALREADY_EXISTS'
  | 'INVALID_DATA'
  | 'CONSTRAINT_VIOLATION'
  | 'TRANSACTION_ERROR'
  | 'CONNECTION_ERROR'
  | 'PERMISSION_ERROR'
  | 'STORAGE_FULL'
  | 'CORRUPTED_DATA'
  | 'UNKNOWN_ERROR';

// ============================================================================
// FACTORY & CONFIGURATION
// ============================================================================

/**
 * Configuration for storage engine
 */
export interface StorageConfig {
  // Engine type
  engine: 'memory' | 'sqlite' | 'postgres' | 'neo4j';
  
  // Connection details
  connectionString?: string;
  host?: string;
  port?: number;
  database?: string;
  username?: string;
  password?: string;
  
  // File-based storage
  filePath?: string;
  
  // Performance tuning
  cacheSize?: number;            // Cache size in MB
  maxConnections?: number;
  queryTimeout?: number;         // Milliseconds
  
  // Features
  enableTransactions?: boolean;
  enableIndexes?: boolean;
  autoOptimize?: boolean;
  
  // Logging
  logLevel?: 'debug' | 'info' | 'warn' | 'error';
  logQueries?: boolean;
}

/**
 * Factory function to create storage engine
 */
export async function createStorageEngine(
  config: StorageConfig
): Promise<IStorageEngine> {
  // Will be implemented with actual storage engines
  throw new Error('Not yet implemented');
}

// ============================================================================
// HELPER UTILITIES
// ============================================================================

/**
 * Generate a unique ID for a node based on its identity
 */
export function generateNodeId(
  domain: DomainType,
  identifier: string,
  version?: string
): string {
  const parts = [domain, identifier];
  if (version) {
    parts.push(version);
  }
  return parts.join(':');
}

/**
 * Generate a unique ID for an edge
 */
export function generateEdgeId(
  sourceId: string,
  targetId: string,
  type: EdgeType
): string {
  return `${sourceId}:${type}:${targetId}`;
}

/**
 * Parse a node ID back into its components
 */
export function parseNodeId(id: string): {
  domain: DomainType;
  identifier: string;
  version?: string;
} {
  const parts = id.split(':');
  return {
    domain: parts[0] as DomainType,
    identifier: parts[1],
    version: parts[2],
  };
}
