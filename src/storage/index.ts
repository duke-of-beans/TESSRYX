/**
 * TESSRYX Storage Module
 * 
 * Main entry point for the storage layer.
 * Exports all public interfaces and provides factory functions.
 */

// Export all types and interfaces
export * from './schema.js';
export * from './interface.js';
export * from './sqlite-engine.js';

// Re-export commonly used types for convenience
export type {
  DependencyNode,
  DependencyEdge,
  Constraint,
  NodeMetadata,
  EdgeMetadata,
  ResolutionState,
  ProvenanceInfo,
} from './schema.js';

export type {
  IStorageEngine,
  ITransaction,
  StorageConfig,
  StorageStats,
  IntegrityReport,
} from './interface.js';

import { SQLiteStorageEngine } from './sqlite-engine.js';
import { IStorageEngine, StorageConfig, StorageError } from './interface.js';

/**
 * Create a storage engine based on configuration
 * 
 * Currently supports:
 * - SQLite (recommended for most use cases)
 * - In-memory SQLite (for testing)
 * 
 * Future engines:
 * - PostgreSQL (for larger deployments)
 * - Neo4j (for advanced graph queries)
 */
export async function createStorageEngine(
  config: StorageConfig
): Promise<IStorageEngine> {
  // Determine engine type
  const engineType = config.engine || 'sqlite';

  let engine: IStorageEngine;

  switch (engineType) {
    case 'sqlite':
      engine = new SQLiteStorageEngine(config);
      break;

    case 'memory':
      // Use in-memory SQLite
      engine = new SQLiteStorageEngine({
        ...config,
        engine: 'sqlite',
        filePath: ':memory:',
      });
      break;

    case 'postgres':
    case 'neo4j':
      throw new StorageError(
        `Engine type '${engineType}' not yet implemented`,
        'UNKNOWN_ERROR'
      );

    default:
      throw new StorageError(
        `Unknown engine type: ${engineType}`,
        'UNKNOWN_ERROR'
      );
  }

  // Initialize the engine
  await engine.initialize();

  return engine;
}

/**
 * Create a storage engine with default configuration
 * Uses SQLite with a file in the current directory
 */
export async function createDefaultStorage(
  filePath = './tessryx.db'
): Promise<IStorageEngine> {
  return createStorageEngine({
    engine: 'sqlite',
    filePath,
    enableTransactions: true,
    enableIndexes: true,
    autoOptimize: true,
    logLevel: 'info',
  });
}

/**
 * Create an in-memory storage engine for testing
 */
export async function createMemoryStorage(): Promise<IStorageEngine> {
  return createStorageEngine({
    engine: 'memory',
    enableTransactions: true,
    enableIndexes: true,
    autoOptimize: false,
    logLevel: 'warn',
  });
}
