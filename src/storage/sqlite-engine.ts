/**
 * TESSRYX SQLite Storage Engine
 * 
 * Production-grade storage implementation using SQLite for persistence.
 * 
 * Design Decisions:
 * - SQLite for zero-config persistence with ACID transactions
 * - JSON columns for flexible metadata and constraint storage
 * - Efficient indexes on frequently queried fields
 * - Full-text search support for node/edge queries
 * - Write-ahead logging (WAL) for concurrent read performance
 * 
 * Schema Design:
 * - nodes table: Core node data with JSON metadata
 * - edges table: Relationships with constraint arrays
 * - node_tags table: Many-to-many for efficient tag queries
 * - Indexes optimized for common query patterns
 */

import Database from 'better-sqlite3';
import { randomUUID } from 'crypto';
import {
  IStorageEngine,
  ITransaction,
  StorageConfig,
  StorageStats,
  StorageError,
  IntegrityReport,
  IntegrityError,
  IntegrityWarning,
  BatchOperation,
  BatchResult,
  generateNodeId,
  generateEdgeId,
  parseNodeId,
} from './interface.js';
import {
  DependencyNode,
  DependencyEdge,
  NodeQuery,
  EdgeQuery,
  TraversalOptions,
  DomainType,
  EdgeType,
  ResolutionStatus,
  IndexDefinition,
  STANDARD_INDEXES,
} from './schema.js';

// ============================================================================
// SQLITE STORAGE ENGINE
// ============================================================================

export class SQLiteStorageEngine implements IStorageEngine {
  private db: Database.Database | null = null;
  private config: StorageConfig;
  private initialized = false;

  constructor(config: StorageConfig) {
    this.config = {
      engine: 'sqlite',
      filePath: config.filePath || ':memory:',
      enableTransactions: config.enableTransactions ?? true,
      enableIndexes: config.enableIndexes ?? true,
      autoOptimize: config.autoOptimize ?? true,
      logLevel: config.logLevel || 'info',
      logQueries: config.logQueries ?? false,
      ...config,
    };
  }

  // ========================================
  // Lifecycle Management
  // ========================================

  async initialize(): Promise<void> {
    if (this.initialized) {
      return;
    }

    try {
      // Open database connection
      this.db = new Database(this.config.filePath!);

      // Enable WAL mode for better concurrent read performance
      this.db.pragma('journal_mode = WAL');
      
      // Enable foreign keys
      this.db.pragma('foreign_keys = ON');

      // Create schema
      this.createSchema();

      // Create indexes
      if (this.config.enableIndexes) {
        this.createStandardIndexes();
      }

      this.initialized = true;
      this.log('info', `SQLite storage initialized at ${this.config.filePath}`);
    } catch (error) {
      throw new StorageError(
        'Failed to initialize storage',
        'CONNECTION_ERROR',
        error
      );
    }
  }

  async close(): Promise<void> {
    if (!this.db) {
      return;
    }

    try {
      // Optimize on close if enabled
      if (this.config.autoOptimize) {
        await this.optimize();
      }

      this.db.close();
      this.db = null;
      this.initialized = false;
      this.log('info', 'SQLite storage closed');
    } catch (error) {
      throw new StorageError(
        'Failed to close storage',
        'CONNECTION_ERROR',
        error
      );
    }
  }

  async clear(): Promise<void> {
    this.ensureInitialized();

    try {
      this.db!.exec(`
        DELETE FROM node_tags;
        DELETE FROM edges;
        DELETE FROM nodes;
      `);
      
      this.log('warn', 'All data cleared from storage');
    } catch (error) {
      throw new StorageError(
        'Failed to clear storage',
        'UNKNOWN_ERROR',
        error
      );
    }
  }

  async getStats(): Promise<StorageStats> {
    this.ensureInitialized();

    try {
      const nodeCount = this.db!.prepare('SELECT COUNT(*) as count FROM nodes').get() as { count: number };
      const edgeCount = this.db!.prepare('SELECT COUNT(*) as count FROM edges').get() as { count: number };

      // Get nodes by domain
      const nodesByDomainRows = this.db!.prepare(`
        SELECT domain, COUNT(*) as count 
        FROM nodes 
        GROUP BY domain
      `).all() as Array<{ domain: DomainType; count: number }>;

      const nodesByDomain: Record<DomainType, number> = nodesByDomainRows.reduce(
        (acc, row) => {
          acc[row.domain] = row.count;
          return acc;
        },
        {} as Record<DomainType, number>
      );

      // Get edges by type
      const edgesByTypeRows = this.db!.prepare(`
        SELECT type, COUNT(*) as count 
        FROM edges 
        GROUP BY type
      `).all() as Array<{ type: EdgeType; count: number }>;

      const edgesByType: Record<EdgeType, number> = edgesByTypeRows.reduce(
        (acc, row) => {
          acc[row.type] = row.count;
          return acc;
        },
        {} as Record<EdgeType, number>
      );

      // Get resolution status counts
      const resolvedNodes = this.db!.prepare(`
        SELECT COUNT(*) as count 
        FROM nodes 
        WHERE json_extract(resolution, '$.status') = 'resolved'
      `).get() as { count: number };

      const unresolvedNodes = this.db!.prepare(`
        SELECT COUNT(*) as count 
        FROM nodes 
        WHERE json_extract(resolution, '$.status') = 'unresolved'
      `).get() as { count: number };

      const conflictedNodes = this.db!.prepare(`
        SELECT COUNT(*) as count 
        FROM nodes 
        WHERE json_extract(resolution, '$.status') = 'conflict'
      `).get() as { count: number };

      // Get storage size
      const pageCount = this.db!.pragma('page_count', { simple: true }) as number;
      const pageSize = this.db!.pragma('page_size', { simple: true }) as number;
      const storageSize = pageCount * pageSize;

      // Count indexes
      const indexCount = this.db!.prepare(`
        SELECT COUNT(*) as count 
        FROM sqlite_master 
        WHERE type = 'index' AND name NOT LIKE 'sqlite_%'
      `).get() as { count: number };

      // Count total constraints across all edges
      const constraintCountResult = this.db!.prepare(`
        SELECT SUM(json_array_length(constraints)) as count 
        FROM edges
      `).get() as { count: number | null };
      const constraintCount = constraintCountResult.count || 0;

      return {
        nodeCount: nodeCount.count,
        edgeCount: edgeCount.count,
        constraintCount,
        nodesByDomain,
        edgesByType,
        resolvedNodes: resolvedNodes.count,
        unresolvedNodes: unresolvedNodes.count,
        conflictedNodes: conflictedNodes.count,
        storageSize,
        indexCount: indexCount.count,
      };
    } catch (error) {
      throw new StorageError(
        'Failed to get storage stats',
        'UNKNOWN_ERROR',
        error
      );
    }
  }

  // ========================================
  // Node Operations
  // ========================================

  async createNode(node: Partial<DependencyNode>): Promise<DependencyNode> {
    this.ensureInitialized();

    try {
      // Generate ID if not provided
      const id = node.id || generateNodeId(
        node.domain!,
        node.identifier!,
        node.version
      );

      // Check if node already exists
      const existing = await this.getNode(id);
      if (existing) {
        throw new StorageError(
          `Node ${id} already exists`,
          'ALREADY_EXISTS'
        );
      }

      // Create complete node with defaults
      const completeNode: DependencyNode = {
        id,
        domain: node.domain!,
        identifier: node.identifier!,
        version: node.version,
        metadata: node.metadata || {
          tags: [],
          domainSpecific: {},
        },
        dependencies: node.dependencies || [],
        dependents: node.dependents || [],
        resolution: node.resolution || {
          status: 'unresolved',
          constraints: [],
          validated: false,
        },
        provenance: node.provenance || {
          source: 'user_defined',
          sourceIdentifier: 'manual',
          discoveredAt: new Date(),
          discoveredBy: 'user',
          confidence: 1.0,
          verified: false,
        },
      };

      // Insert into database
      const stmt = this.db!.prepare(`
        INSERT INTO nodes (
          id, domain, identifier, version,
          metadata, dependencies, dependents,
          resolution, provenance
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
      `);

      stmt.run(
        completeNode.id,
        completeNode.domain,
        completeNode.identifier,
        completeNode.version || null,
        JSON.stringify(completeNode.metadata),
        JSON.stringify(completeNode.dependencies),
        JSON.stringify(completeNode.dependents),
        JSON.stringify(completeNode.resolution),
        JSON.stringify(completeNode.provenance)
      );

      // Insert tags for efficient querying
      if (completeNode.metadata.tags.length > 0) {
        const tagStmt = this.db!.prepare(`
          INSERT INTO node_tags (node_id, tag) VALUES (?, ?)
        `);

        for (const tag of completeNode.metadata.tags) {
          tagStmt.run(completeNode.id, tag);
        }
      }

      this.log('debug', `Created node: ${id}`);
      return completeNode;
    } catch (error) {
      if (error instanceof StorageError) {
        throw error;
      }
      throw new StorageError(
        'Failed to create node',
        'UNKNOWN_ERROR',
        error
      );
    }
  }

  async getNode(id: string): Promise<DependencyNode | null> {
    this.ensureInitialized();

    try {
      const stmt = this.db!.prepare(`
        SELECT * FROM nodes WHERE id = ?
      `);

      const row = stmt.get(id) as any;
      if (!row) {
        return null;
      }

      return this.rowToNode(row);
    } catch (error) {
      throw new StorageError(
        'Failed to get node',
        'UNKNOWN_ERROR',
        error
      );
    }
  }

  async getNodeByIdentity(
    domain: DomainType,
    identifier: string,
    version?: string
  ): Promise<DependencyNode | null> {
    const id = generateNodeId(domain, identifier, version);
    return this.getNode(id);
  }

  async updateNode(id: string, updates: Partial<DependencyNode>): Promise<DependencyNode> {
    this.ensureInitialized();

    try {
      const existing = await this.getNode(id);
      if (!existing) {
        throw new StorageError(
          `Node ${id} not found`,
          'NOT_FOUND'
        );
      }

      // Merge updates
      const updated: DependencyNode = {
        ...existing,
        ...updates,
        id, // ID cannot be changed
        metadata: updates.metadata 
          ? { ...existing.metadata, ...updates.metadata }
          : existing.metadata,
      };

      // Update in database
      const stmt = this.db!.prepare(`
        UPDATE nodes 
        SET domain = ?, identifier = ?, version = ?,
            metadata = ?, dependencies = ?, dependents = ?,
            resolution = ?, provenance = ?
        WHERE id = ?
      `);

      stmt.run(
        updated.domain,
        updated.identifier,
        updated.version || null,
        JSON.stringify(updated.metadata),
        JSON.stringify(updated.dependencies),
        JSON.stringify(updated.dependents),
        JSON.stringify(updated.resolution),
        JSON.stringify(updated.provenance),
        id
      );

      // Update tags if changed
      if (updates.metadata?.tags) {
        // Delete old tags
        this.db!.prepare('DELETE FROM node_tags WHERE node_id = ?').run(id);

        // Insert new tags
        const tagStmt = this.db!.prepare(`
          INSERT INTO node_tags (node_id, tag) VALUES (?, ?)
        `);

        for (const tag of updated.metadata.tags) {
          tagStmt.run(id, tag);
        }
      }

      this.log('debug', `Updated node: ${id}`);
      return updated;
    } catch (error) {
      if (error instanceof StorageError) {
        throw error;
      }
      throw new StorageError(
        'Failed to update node',
        'UNKNOWN_ERROR',
        error
      );
    }
  }

  async upsertNode(node: Partial<DependencyNode>): Promise<DependencyNode> {
    const id = node.id || generateNodeId(
      node.domain!,
      node.identifier!,
      node.version
    );

    const existing = await this.getNode(id);
    if (existing) {
      return this.updateNode(id, node);
    } else {
      return this.createNode({ ...node, id });
    }
  }

  async deleteNode(id: string, cascade = true): Promise<void> {
    this.ensureInitialized();

    try {
      const existing = await this.getNode(id);
      if (!existing) {
        throw new StorageError(
          `Node ${id} not found`,
          'NOT_FOUND'
        );
      }

      if (cascade) {
        // Delete all edges connected to this node
        this.db!.prepare('DELETE FROM edges WHERE source = ? OR target = ?').run(id, id);
      } else {
        // Check if node has edges
        const edgeCount = this.db!.prepare(`
          SELECT COUNT(*) as count 
          FROM edges 
          WHERE source = ? OR target = ?
        `).get(id, id) as { count: number };

        if (edgeCount.count > 0) {
          throw new StorageError(
            `Cannot delete node ${id} - has ${edgeCount.count} connected edges`,
            'CONSTRAINT_VIOLATION'
          );
        }
      }

      // Delete node tags
      this.db!.prepare('DELETE FROM node_tags WHERE node_id = ?').run(id);

      // Delete node
      this.db!.prepare('DELETE FROM nodes WHERE id = ?').run(id);

      this.log('debug', `Deleted node: ${id}`);
    } catch (error) {
      if (error instanceof StorageError) {
        throw error;
      }
      throw new StorageError(
        'Failed to delete node',
        'UNKNOWN_ERROR',
        error
      );
    }
  }

  async queryNodes(query: NodeQuery): Promise<DependencyNode[]> {
    this.ensureInitialized();

    try {
      let sql = 'SELECT DISTINCT n.* FROM nodes n';
      const params: any[] = [];
      const conditions: string[] = [];

      // Join with tags if needed
      if (query.tags && query.tags.length > 0) {
        sql += ' INNER JOIN node_tags nt ON n.id = nt.node_id';
        conditions.push(`nt.tag IN (${query.tags.map(() => '?').join(',')})`);
        params.push(...query.tags);
      }

      // Domain filter
      if (query.domain) {
        if (Array.isArray(query.domain)) {
          conditions.push(`n.domain IN (${query.domain.map(() => '?').join(',')})`);
          params.push(...query.domain);
        } else {
          conditions.push('n.domain = ?');
          params.push(query.domain);
        }
      }

      // Identifier filter
      if (query.identifier) {
        if (query.identifier instanceof RegExp) {
          // SQLite doesn't support regex directly, use LIKE for simple patterns
          const pattern = query.identifier.source.replace(/\.\*/g, '%').replace(/\./g, '_');
          conditions.push('n.identifier LIKE ?');
          params.push(pattern);
        } else {
          conditions.push('n.identifier = ?');
          params.push(query.identifier);
        }
      }

      // Version filter
      if (query.version) {
        conditions.push('n.version = ?');
        params.push(query.version);
      }

      // Deprecated filter
      if (query.deprecated !== undefined) {
        conditions.push(`json_extract(n.metadata, '$.deprecated') = ?`);
        params.push(query.deprecated ? 1 : 0);
      }

      // Stability filter
      if (query.stability) {
        conditions.push(`json_extract(n.metadata, '$.stability') = ?`);
        params.push(query.stability);
      }

      // Resolution status filter
      if (query.status) {
        if (Array.isArray(query.status)) {
          conditions.push(`json_extract(n.resolution, '$.status') IN (${query.status.map(() => '?').join(',')})`);
          params.push(...query.status);
        } else {
          conditions.push(`json_extract(n.resolution, '$.status') = ?`);
          params.push(query.status);
        }
      }

      // Has constraints filter
      if (query.hasConstraints !== undefined) {
        if (query.hasConstraints) {
          conditions.push(`EXISTS (
            SELECT 1 FROM edges e 
            WHERE (e.source = n.id OR e.target = n.id)
            AND json_array_length(e.constraints) > 0
          )`);
        } else {
          conditions.push(`NOT EXISTS (
            SELECT 1 FROM edges e 
            WHERE (e.source = n.id OR e.target = n.id)
            AND json_array_length(e.constraints) > 0
          )`);
        }
      }

      // Has conflicts filter
      if (query.hasConflicts !== undefined) {
        if (query.hasConflicts) {
          conditions.push(`json_array_length(json_extract(n.resolution, '$.conflicts')) > 0`);
        } else {
          conditions.push(`(
            json_extract(n.resolution, '$.conflicts') IS NULL
            OR json_array_length(json_extract(n.resolution, '$.conflicts')) = 0
          )`);
        }
      }

      // Add WHERE clause if we have conditions
      if (conditions.length > 0) {
        sql += ' WHERE ' + conditions.join(' AND ');
      }

      const stmt = this.db!.prepare(sql);
      const rows = stmt.all(...params) as any[];

      return rows.map(row => this.rowToNode(row));
    } catch (error) {
      throw new StorageError(
        'Failed to query nodes',
        'UNKNOWN_ERROR',
        error
      );
    }
  }

  async countNodes(query: NodeQuery): Promise<number> {
    const nodes = await this.queryNodes(query);
    return nodes.length;
  }

  // ========================================
  // Edge Operations
  // ========================================

  async createEdge(edge: Partial<DependencyEdge>): Promise<DependencyEdge> {
    this.ensureInitialized();

    try {
      // Validate source and target exist
      const source = await this.getNode(edge.source!);
      const target = await this.getNode(edge.target!);

      if (!source) {
        throw new StorageError(
          `Source node ${edge.source} not found`,
          'NOT_FOUND'
        );
      }

      if (!target) {
        throw new StorageError(
          `Target node ${edge.target} not found`,
          'NOT_FOUND'
        );
      }

      // Generate ID if not provided
      const id = edge.id || generateEdgeId(
        edge.source!,
        edge.target!,
        edge.type!
      );

      // Check if edge already exists
      const existing = await this.getEdge(id);
      if (existing) {
        throw new StorageError(
          `Edge ${id} already exists`,
          'ALREADY_EXISTS'
        );
      }

      // Create complete edge with defaults
      const completeEdge: DependencyEdge = {
        id,
        source: edge.source!,
        target: edge.target!,
        type: edge.type!,
        constraints: edge.constraints || [],
        metadata: edge.metadata || {
          optional: false,
          development: false,
          peer: false,
          domainSpecific: {},
        },
        provenance: edge.provenance || {
          source: 'user_defined',
          sourceIdentifier: 'manual',
          discoveredAt: new Date(),
          discoveredBy: 'user',
          confidence: 1.0,
          verified: false,
        },
      };

      // Insert into database
      const stmt = this.db!.prepare(`
        INSERT INTO edges (
          id, source, target, type,
          constraints, metadata, provenance
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
      `);

      stmt.run(
        completeEdge.id,
        completeEdge.source,
        completeEdge.target,
        completeEdge.type,
        JSON.stringify(completeEdge.constraints),
        JSON.stringify(completeEdge.metadata),
        JSON.stringify(completeEdge.provenance)
      );

      // Update source node's dependencies
      source.dependencies.push({
        edgeId: id,
        nodeId: target.id,
        type: completeEdge.type,
        direction: 'outgoing',
      });
      await this.updateNode(source.id, { dependencies: source.dependencies });

      // Update target node's dependents
      target.dependents.push({
        edgeId: id,
        nodeId: source.id,
        type: completeEdge.type,
        direction: 'incoming',
      });
      await this.updateNode(target.id, { dependents: target.dependents });

      this.log('debug', `Created edge: ${id}`);
      return completeEdge;
    } catch (error) {
      if (error instanceof StorageError) {
        throw error;
      }
      throw new StorageError(
        'Failed to create edge',
        'UNKNOWN_ERROR',
        error
      );
    }
  }

  async getEdge(id: string): Promise<DependencyEdge | null> {
    this.ensureInitialized();

    try {
      const stmt = this.db!.prepare('SELECT * FROM edges WHERE id = ?');
      const row = stmt.get(id) as any;

      if (!row) {
        return null;
      }

      return this.rowToEdge(row);
    } catch (error) {
      throw new StorageError(
        'Failed to get edge',
        'UNKNOWN_ERROR',
        error
      );
    }
  }

  async getEdgesBetween(sourceId: string, targetId: string): Promise<DependencyEdge[]> {
    this.ensureInitialized();

    try {
      const stmt = this.db!.prepare(`
        SELECT * FROM edges 
        WHERE source = ? AND target = ?
      `);

      const rows = stmt.all(sourceId, targetId) as any[];
      return rows.map(row => this.rowToEdge(row));
    } catch (error) {
      throw new StorageError(
        'Failed to get edges between nodes',
        'UNKNOWN_ERROR',
        error
      );
    }
  }

  async updateEdge(id: string, updates: Partial<DependencyEdge>): Promise<DependencyEdge> {
    this.ensureInitialized();

    try {
      const existing = await this.getEdge(id);
      if (!existing) {
        throw new StorageError(
          `Edge ${id} not found`,
          'NOT_FOUND'
        );
      }

      // Merge updates
      const updated: DependencyEdge = {
        ...existing,
        ...updates,
        id, // ID cannot be changed
        source: existing.source, // Source cannot be changed
        target: existing.target, // Target cannot be changed
        metadata: updates.metadata
          ? { ...existing.metadata, ...updates.metadata }
          : existing.metadata,
      };

      // Update in database
      const stmt = this.db!.prepare(`
        UPDATE edges 
        SET type = ?, constraints = ?, metadata = ?, provenance = ?
        WHERE id = ?
      `);

      stmt.run(
        updated.type,
        JSON.stringify(updated.constraints),
        JSON.stringify(updated.metadata),
        JSON.stringify(updated.provenance),
        id
      );

      this.log('debug', `Updated edge: ${id}`);
      return updated;
    } catch (error) {
      if (error instanceof StorageError) {
        throw error;
      }
      throw new StorageError(
        'Failed to update edge',
        'UNKNOWN_ERROR',
        error
      );
    }
  }

  async upsertEdge(edge: Partial<DependencyEdge>): Promise<DependencyEdge> {
    const id = edge.id || generateEdgeId(
      edge.source!,
      edge.target!,
      edge.type!
    );

    const existing = await this.getEdge(id);
    if (existing) {
      return this.updateEdge(id, edge);
    } else {
      return this.createEdge({ ...edge, id });
    }
  }

  async deleteEdge(id: string): Promise<void> {
    this.ensureInitialized();

    try {
      const existing = await this.getEdge(id);
      if (!existing) {
        throw new StorageError(
          `Edge ${id} not found`,
          'NOT_FOUND'
        );
      }

      // Update source node to remove dependency reference
      const source = await this.getNode(existing.source);
      if (source) {
        source.dependencies = source.dependencies.filter(d => d.edgeId !== id);
        await this.updateNode(source.id, { dependencies: source.dependencies });
      }

      // Update target node to remove dependent reference
      const target = await this.getNode(existing.target);
      if (target) {
        target.dependents = target.dependents.filter(d => d.edgeId !== id);
        await this.updateNode(target.id, { dependents: target.dependents });
      }

      // Delete edge
      this.db!.prepare('DELETE FROM edges WHERE id = ?').run(id);

      this.log('debug', `Deleted edge: ${id}`);
    } catch (error) {
      if (error instanceof StorageError) {
        throw error;
      }
      throw new StorageError(
        'Failed to delete edge',
        'UNKNOWN_ERROR',
        error
      );
    }
  }

  async queryEdges(query: EdgeQuery): Promise<DependencyEdge[]> {
    this.ensureInitialized();

    try {
      let sql = 'SELECT * FROM edges WHERE 1=1';
      const params: any[] = [];

      // Source filter
      if (query.source) {
        if (Array.isArray(query.source)) {
          sql += ` AND source IN (${query.source.map(() => '?').join(',')})`;
          params.push(...query.source);
        } else {
          sql += ' AND source = ?';
          params.push(query.source);
        }
      }

      // Target filter
      if (query.target) {
        if (Array.isArray(query.target)) {
          sql += ` AND target IN (${query.target.map(() => '?').join(',')})`;
          params.push(...query.target);
        } else {
          sql += ' AND target = ?';
          params.push(query.target);
        }
      }

      // Type filter
      if (query.type) {
        if (Array.isArray(query.type)) {
          sql += ` AND type IN (${query.type.map(() => '?').join(',')})`;
          params.push(...query.type);
        } else {
          sql += ' AND type = ?';
          params.push(query.type);
        }
      }

      // Optional filter
      if (query.optional !== undefined) {
        sql += ` AND json_extract(metadata, '$.optional') = ?`;
        params.push(query.optional ? 1 : 0);
      }

      // Development filter
      if (query.development !== undefined) {
        sql += ` AND json_extract(metadata, '$.development') = ?`;
        params.push(query.development ? 1 : 0);
      }

      // Scope filter
      if (query.scope) {
        sql += ` AND json_extract(metadata, '$.scope') = ?`;
        params.push(query.scope);
      }

      // Constraint category filter
      if (query.constraintCategory) {
        sql += ` AND EXISTS (
          SELECT 1 FROM json_each(constraints) 
          WHERE json_extract(value, '$.category') = ?
        )`;
        params.push(query.constraintCategory);
      }

      // Constraint type filter
      if (query.constraintType) {
        sql += ` AND EXISTS (
          SELECT 1 FROM json_each(constraints) 
          WHERE json_extract(value, '$.type') = ?
        )`;
        params.push(query.constraintType);
      }

      const stmt = this.db!.prepare(sql);
      const rows = stmt.all(...params) as any[];

      return rows.map(row => this.rowToEdge(row));
    } catch (error) {
      throw new StorageError(
        'Failed to query edges',
        'UNKNOWN_ERROR',
        error
      );
    }
  }

  async countEdges(query: EdgeQuery): Promise<number> {
    const edges = await this.queryEdges(query);
    return edges.length;
  }

  // ========================================
  // Graph Traversal
  // ========================================

  async getDependencies(
    nodeId: string,
    options?: Partial<TraversalOptions>
  ): Promise<DependencyNode[]> {
    return this.traverse(nodeId, {
      direction: 'forward',
      maxDepth: options?.maxDepth ?? 1,
      ...options,
    });
  }

  async getDependents(
    nodeId: string,
    options?: Partial<TraversalOptions>
  ): Promise<DependencyNode[]> {
    return this.traverse(nodeId, {
      direction: 'backward',
      maxDepth: options?.maxDepth ?? 1,
      ...options,
    });
  }

  async traverse(
    startNodeId: string,
    options: TraversalOptions
  ): Promise<DependencyNode[]> {
    this.ensureInitialized();

    const visited = new Set<string>();
    const result: DependencyNode[] = [];

    const traverseRecursive = async (
      nodeId: string,
      depth: number
    ): Promise<void> => {
      // Check max depth
      if (options.maxDepth !== undefined && depth > options.maxDepth) {
        return;
      }

      // Check if already visited
      if (visited.has(nodeId)) {
        return;
      }

      // Get node
      const node = await this.getNode(nodeId);
      if (!node) {
        return;
      }

      // Check stop condition
      if (options.stopCondition && options.stopCondition(node, depth)) {
        return;
      }

      // Check filter
      if (options.filter && !options.filter(node)) {
        return;
      }

      visited.add(nodeId);
      result.push(node);

      // Get edges based on direction
      let edges: DependencyEdge[] = [];

      if (options.direction === 'forward' || options.direction === 'both') {
        const forwardEdges = await this.queryEdges({ source: nodeId });
        edges.push(...forwardEdges);
      }

      if (options.direction === 'backward' || options.direction === 'both') {
        const backwardEdges = await this.queryEdges({ target: nodeId });
        edges.push(...edges);
      }

      // Filter edges by type if specified
      if (options.includeTypes) {
        edges = edges.filter(e => options.includeTypes!.includes(e.type));
      }

      if (options.excludeTypes) {
        edges = edges.filter(e => !options.excludeTypes!.includes(e.type));
      }

      // Apply edge filter if provided
      if (options.filter) {
        edges = edges.filter(e => {
          const otherNodeId = e.source === nodeId ? e.target : e.source;
          return options.filter!(node, e);
        });
      }

      // Traverse connected nodes
      for (const edge of edges) {
        const nextNodeId = edge.source === nodeId ? edge.target : edge.source;
        await traverseRecursive(nextNodeId, depth + 1);
      }
    };

    await traverseRecursive(startNodeId, 0);

    // Remove the start node from results (it's depth 0)
    return result.slice(1);
  }

  async findPaths(
    sourceId: string,
    targetId: string,
    maxPaths = 10
  ): Promise<string[][]> {
    this.ensureInitialized();

    const paths: string[][] = [];
    const visited = new Set<string>();

    const findPathsRecursive = async (
      currentId: string,
      path: string[]
    ): Promise<void> => {
      // Check if we've reached the target
      if (currentId === targetId) {
        paths.push([...path, currentId]);
        return;
      }

      // Check if we've found enough paths
      if (paths.length >= maxPaths) {
        return;
      }

      // Avoid cycles
      if (visited.has(currentId)) {
        return;
      }

      visited.add(currentId);
      path.push(currentId);

      // Get outgoing edges
      const edges = await this.queryEdges({ source: currentId });

      for (const edge of edges) {
        await findPathsRecursive(edge.target, [...path]);

        if (paths.length >= maxPaths) {
          break;
        }
      }

      visited.delete(currentId);
    };

    await findPathsRecursive(sourceId, []);

    return paths;
  }

  async detectCycles(startNodeId?: string): Promise<string[][]> {
    this.ensureInitialized();

    const cycles: string[][] = [];
    const visited = new Set<string>();
    const recursionStack = new Set<string>();

    const detectCyclesRecursive = async (
      nodeId: string,
      path: string[]
    ): Promise<void> => {
      visited.add(nodeId);
      recursionStack.add(nodeId);
      path.push(nodeId);

      // Get outgoing edges
      const edges = await this.queryEdges({ source: nodeId });

      for (const edge of edges) {
        const targetId = edge.target;

        if (!visited.has(targetId)) {
          await detectCyclesRecursive(targetId, [...path]);
        } else if (recursionStack.has(targetId)) {
          // Found a cycle
          const cycleStart = path.indexOf(targetId);
          const cycle = path.slice(cycleStart);
          cycle.push(targetId); // Complete the cycle
          cycles.push(cycle);
        }
      }

      recursionStack.delete(nodeId);
    };

    if (startNodeId) {
      // Detect cycles from specific node
      await detectCyclesRecursive(startNodeId, []);
    } else {
      // Detect all cycles in graph
      const allNodes = await this.queryNodes({});

      for (const node of allNodes) {
        if (!visited.has(node.id)) {
          await detectCyclesRecursive(node.id, []);
        }
      }
    }

    return cycles;
  }

  async getSubgraph(
    nodeId: string,
    radius = 1
  ): Promise<{ nodes: DependencyNode[]; edges: DependencyEdge[] }> {
    this.ensureInitialized();

    // Get all nodes within radius
    const nodes = await this.traverse(nodeId, {
      direction: 'both',
      maxDepth: radius,
    });

    // Add the center node
    const centerNode = await this.getNode(nodeId);
    if (centerNode) {
      nodes.unshift(centerNode);
    }

    // Get all edges between these nodes
    const nodeIds = new Set(nodes.map(n => n.id));
    const allEdges = await this.queryEdges({});
    const edges = allEdges.filter(
      e => nodeIds.has(e.source) && nodeIds.has(e.target)
    );

    return { nodes, edges };
  }

  // ========================================
  // Batch Operations
  // ========================================

  async executeBatch(operations: BatchOperation[]): Promise<BatchResult> {
    this.ensureInitialized();

    const result: BatchResult = {
      successful: 0,
      failed: 0,
      errors: [],
    };

    // Use transaction for atomic batch operations
    const transaction = await this.beginTransaction();

    try {
      for (const op of operations) {
        try {
          if (op.entity === 'node') {
            if (op.type === 'create') {
              await transaction.createNode(op.data as Partial<DependencyNode>);
            } else if (op.type === 'update') {
              const nodeId = (op.data as any).id;
              await transaction.updateNode(nodeId, op.data as Partial<DependencyNode>);
            } else if (op.type === 'delete') {
              const nodeId = (op.data as any).id;
              await transaction.deleteNode(nodeId);
            }
          } else if (op.entity === 'edge') {
            if (op.type === 'create') {
              await transaction.createEdge(op.data as Partial<DependencyEdge>);
            } else if (op.type === 'update') {
              const edgeId = (op.data as any).id;
              await transaction.updateEdge(edgeId, op.data as Partial<DependencyEdge>);
            } else if (op.type === 'delete') {
              const edgeId = (op.data as any).id;
              await transaction.deleteEdge(edgeId);
            }
          }

          result.successful++;
        } catch (error) {
          result.failed++;
          result.errors.push({
            operation: op,
            error: error instanceof Error ? error.message : String(error),
          });
        }
      }

      await transaction.commit();
    } catch (error) {
      await transaction.rollback();
      throw error;
    }

    return result;
  }

  async importGraph(data: {
    nodes: Partial<DependencyNode>[];
    edges: Partial<DependencyEdge>[];
  }): Promise<BatchResult> {
    const operations: BatchOperation[] = [
      ...data.nodes.map(node => ({
        type: 'create' as const,
        entity: 'node' as const,
        data: node,
      })),
      ...data.edges.map(edge => ({
        type: 'create' as const,
        entity: 'edge' as const,
        data: edge,
      })),
    ];

    return this.executeBatch(operations);
  }

  async exportGraph(nodeIds?: string[]): Promise<{
    nodes: DependencyNode[];
    edges: DependencyEdge[];
  }> {
    this.ensureInitialized();

    let nodes: DependencyNode[];

    if (nodeIds) {
      // Export specific nodes
      nodes = [];
      for (const id of nodeIds) {
        const node = await this.getNode(id);
        if (node) {
          nodes.push(node);
        }
      }
    } else {
      // Export all nodes
      nodes = await this.queryNodes({});
    }

    // Get all edges between exported nodes
    const nodeIdSet = new Set(nodes.map(n => n.id));
    const allEdges = await this.queryEdges({});
    const edges = allEdges.filter(
      e => nodeIdSet.has(e.source) && nodeIdSet.has(e.target)
    );

    return { nodes, edges };
  }

  // ========================================
  // Transaction Support
  // ========================================

  async beginTransaction(): Promise<ITransaction> {
    this.ensureInitialized();

    // SQLite transactions are managed through the database instance
    // We'll create a wrapper that delegates to this instance
    return new SQLiteTransaction(this);
  }

  // ========================================
  // Index Management
  // ========================================

  async createIndex(index: IndexDefinition): Promise<void> {
    this.ensureInitialized();

    try {
      const table = index.entity === 'node' ? 'nodes' : 'edges';
      const unique = index.unique ? 'UNIQUE' : '';
      
      // Build index expression based on fields
      const fieldExprs = index.fields.map(field => {
        if (field.startsWith('metadata.') || field.startsWith('resolution.')) {
          return `json_extract(${field.split('.')[0]}, '$.${field.split('.').slice(1).join('.')}')`;
        }
        return field;
      }).join(', ');

      const sql = `
        CREATE ${unique} INDEX IF NOT EXISTS ${index.name}
        ON ${table} (${fieldExprs})
      `;

      this.db!.exec(sql);

      this.log('debug', `Created index: ${index.name}`);
    } catch (error) {
      throw new StorageError(
        'Failed to create index',
        'UNKNOWN_ERROR',
        error
      );
    }
  }

  async dropIndex(indexName: string): Promise<void> {
    this.ensureInitialized();

    try {
      this.db!.exec(`DROP INDEX IF EXISTS ${indexName}`);
      this.log('debug', `Dropped index: ${indexName}`);
    } catch (error) {
      throw new StorageError(
        'Failed to drop index',
        'UNKNOWN_ERROR',
        error
      );
    }
  }

  async listIndexes(): Promise<IndexDefinition[]> {
    this.ensureInitialized();

    try {
      const rows = this.db!.prepare(`
        SELECT name, sql 
        FROM sqlite_master 
        WHERE type = 'index' AND name NOT LIKE 'sqlite_%'
      `).all() as Array<{ name: string; sql: string }>;

      // Parse index definitions from SQL (simplified)
      return rows.map(row => ({
        name: row.name,
        entity: row.name.startsWith('node_') ? 'node' : 'edge',
        fields: [], // Would need proper SQL parsing to extract fields
        unique: row.sql.includes('UNIQUE'),
      }));
    } catch (error) {
      throw new StorageError(
        'Failed to list indexes',
        'UNKNOWN_ERROR',
        error
      );
    }
  }

  // ========================================
  // Optimization & Maintenance
  // ========================================

  async optimize(): Promise<void> {
    this.ensureInitialized();

    try {
      // Analyze tables for query optimization
      this.db!.exec('ANALYZE');

      // Vacuum to reclaim space
      this.db!.exec('VACUUM');

      this.log('info', 'Storage optimized');
    } catch (error) {
      throw new StorageError(
        'Failed to optimize storage',
        'UNKNOWN_ERROR',
        error
      );
    }
  }

  async validateIntegrity(): Promise<IntegrityReport> {
    this.ensureInitialized();

    const errors: IntegrityError[] = [];
    const warnings: IntegrityWarning[] = [];

    try {
      // Check for orphaned edges (edges with non-existent nodes)
      const orphanedEdges = this.db!.prepare(`
        SELECT e.id, e.source, e.target
        FROM edges e
        LEFT JOIN nodes n1 ON e.source = n1.id
        LEFT JOIN nodes n2 ON e.target = n2.id
        WHERE n1.id IS NULL OR n2.id IS NULL
      `).all() as Array<{ id: string; source: string; target: string }>;

      for (const edge of orphanedEdges) {
        errors.push({
          type: 'orphaned_edge',
          entity: 'edge',
          entityId: edge.id,
          description: `Edge references non-existent nodes: ${edge.source} -> ${edge.target}`,
          fix: `DELETE FROM edges WHERE id = '${edge.id}'`,
        });
      }

      // Check for nodes with deprecated status but no deprecation message
      const deprecatedWithoutMessage = this.db!.prepare(`
        SELECT id FROM nodes
        WHERE json_extract(metadata, '$.deprecated') = 1
        AND (
          json_extract(metadata, '$.deprecationMessage') IS NULL
          OR json_extract(metadata, '$.deprecationMessage') = ''
        )
      `).all() as Array<{ id: string }>;

      for (const node of deprecatedWithoutMessage) {
        warnings.push({
          type: 'deprecated_node',
          entity: 'node',
          entityId: node.id,
          description: 'Deprecated node missing deprecation message',
        });
      }

      // Check for unresolved conflicts
      const unresolvedConflicts = this.db!.prepare(`
        SELECT id FROM nodes
        WHERE json_extract(resolution, '$.status') = 'conflict'
        AND json_array_length(json_extract(resolution, '$.conflicts')) > 0
      `).all() as Array<{ id: string }>;

      for (const node of unresolvedConflicts) {
        warnings.push({
          type: 'unresolved_conflict',
          entity: 'node',
          entityId: node.id,
          description: 'Node has unresolved conflicts',
        });
      }

      // Get counts
      const nodeCount = this.db!.prepare('SELECT COUNT(*) as count FROM nodes').get() as { count: number };
      const edgeCount = this.db!.prepare('SELECT COUNT(*) as count FROM edges').get() as { count: number };
      
      // Count total constraints
      const constraintCountResult = this.db!.prepare(`
        SELECT SUM(json_array_length(constraints)) as count 
        FROM edges
      `).get() as { count: number | null };
      const constraintCount = constraintCountResult.count || 0;

      return {
        valid: errors.length === 0,
        errors,
        warnings,
        nodesChecked: nodeCount.count,
        edgesChecked: edgeCount.count,
        constraintsChecked: constraintCount,
      };
    } catch (error) {
      throw new StorageError(
        'Failed to validate integrity',
        'UNKNOWN_ERROR',
        error
      );
    }
  }

  async backup(destination: string): Promise<void> {
    this.ensureInitialized();

    try {
      // Use SQLite backup API
      await this.db!.backup(destination);
      this.log('info', `Backup created at ${destination}`);
    } catch (error) {
      throw new StorageError(
        'Failed to create backup',
        'UNKNOWN_ERROR',
        error
      );
    }
  }

  async restore(source: string): Promise<void> {
    this.ensureInitialized();

    try {
      // Close current database
      await this.close();

      // Copy backup file to current location
      const fs = await import('fs/promises');
      await fs.copyFile(source, this.config.filePath!);

      // Reopen database
      await this.initialize();

      this.log('info', `Restored from backup ${source}`);
    } catch (error) {
      throw new StorageError(
        'Failed to restore from backup',
        'UNKNOWN_ERROR',
        error
      );
    }
  }

  // ========================================
  // Private Helper Methods
  // ========================================

  private createSchema(): void {
    this.db!.exec(`
      -- Nodes table
      CREATE TABLE IF NOT EXISTS nodes (
        id TEXT PRIMARY KEY,
        domain TEXT NOT NULL,
        identifier TEXT NOT NULL,
        version TEXT,
        metadata TEXT NOT NULL,
        dependencies TEXT NOT NULL,
        dependents TEXT NOT NULL,
        resolution TEXT NOT NULL,
        provenance TEXT NOT NULL,
        UNIQUE(domain, identifier, version)
      );

      -- Edges table
      CREATE TABLE IF NOT EXISTS edges (
        id TEXT PRIMARY KEY,
        source TEXT NOT NULL,
        target TEXT NOT NULL,
        type TEXT NOT NULL,
        constraints TEXT NOT NULL,
        metadata TEXT NOT NULL,
        provenance TEXT NOT NULL,
        FOREIGN KEY (source) REFERENCES nodes(id) ON DELETE CASCADE,
        FOREIGN KEY (target) REFERENCES nodes(id) ON DELETE CASCADE
      );

      -- Node tags for efficient tag queries
      CREATE TABLE IF NOT EXISTS node_tags (
        node_id TEXT NOT NULL,
        tag TEXT NOT NULL,
        PRIMARY KEY (node_id, tag),
        FOREIGN KEY (node_id) REFERENCES nodes(id) ON DELETE CASCADE
      );
    `);
  }

  private createStandardIndexes(): void {
    for (const index of STANDARD_INDEXES) {
      this.createIndex(index).catch(err => {
        this.log('warn', `Failed to create index ${index.name}: ${err.message}`);
      });
    }
  }

  private rowToNode(row: any): DependencyNode {
    return {
      id: row.id,
      domain: row.domain,
      identifier: row.identifier,
      version: row.version,
      metadata: JSON.parse(row.metadata),
      dependencies: JSON.parse(row.dependencies),
      dependents: JSON.parse(row.dependents),
      resolution: JSON.parse(row.resolution),
      provenance: JSON.parse(row.provenance),
    };
  }

  private rowToEdge(row: any): DependencyEdge {
    return {
      id: row.id,
      source: row.source,
      target: row.target,
      type: row.type,
      constraints: JSON.parse(row.constraints),
      metadata: JSON.parse(row.metadata),
      provenance: JSON.parse(row.provenance),
    };
  }

  private ensureInitialized(): void {
    if (!this.initialized || !this.db) {
      throw new StorageError(
        'Storage engine not initialized',
        'CONNECTION_ERROR'
      );
    }
  }

  private log(level: string, message: string): void {
    if (this.config.logLevel === 'debug' || level !== 'debug') {
      console.log(`[SQLiteStorage] [${level.toUpperCase()}] ${message}`);
    }
  }
}

// ============================================================================
// SQLITE TRANSACTION
// ============================================================================

class SQLiteTransaction implements ITransaction {
  private engine: SQLiteStorageEngine;
  private active = true;

  constructor(engine: SQLiteStorageEngine) {
    this.engine = engine;
    (engine as any).db.exec('BEGIN TRANSACTION');
  }

  async commit(): Promise<void> {
    if (!this.active) {
      throw new StorageError(
        'Transaction is not active',
        'TRANSACTION_ERROR'
      );
    }

    (this.engine as any).db.exec('COMMIT');
    this.active = false;
  }

  async rollback(): Promise<void> {
    if (!this.active) {
      throw new StorageError(
        'Transaction is not active',
        'TRANSACTION_ERROR'
      );
    }

    (this.engine as any).db.exec('ROLLBACK');
    this.active = false;
  }

  isActive(): boolean {
    return this.active;
  }

  // Delegate all operations to the engine
  async createNode(node: Partial<DependencyNode>): Promise<DependencyNode> {
    return this.engine.createNode(node);
  }

  async getNode(id: string): Promise<DependencyNode | null> {
    return this.engine.getNode(id);
  }

  async updateNode(id: string, updates: Partial<DependencyNode>): Promise<DependencyNode> {
    return this.engine.updateNode(id, updates);
  }

  async deleteNode(id: string, cascade?: boolean): Promise<void> {
    return this.engine.deleteNode(id, cascade);
  }

  async createEdge(edge: Partial<DependencyEdge>): Promise<DependencyEdge> {
    return this.engine.createEdge(edge);
  }

  async getEdge(id: string): Promise<DependencyEdge | null> {
    return this.engine.getEdge(id);
  }

  async updateEdge(id: string, updates: Partial<DependencyEdge>): Promise<DependencyEdge> {
    return this.engine.updateEdge(id, updates);
  }

  async deleteEdge(id: string): Promise<void> {
    return this.engine.deleteEdge(id);
  }
}
