"""CRUD operations for entities."""

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..database.models import EntityModel
from .schemas import EntityCreate, EntityUpdate


async def create_entity(db: AsyncSession, entity: EntityCreate) -> EntityModel:
    """Create a new entity.
    
    Args:
        db: Database session
        entity: Entity creation data
        
    Returns:
        Created entity model
    """
    now = datetime.utcnow()
    db_entity = EntityModel(
        id=uuid4(),
        name=entity.name,
        type=entity.type,
        version=entity.version,
        parent_id=entity.parent_id,
        children_ids=[],
        attributes=entity.attributes,
        tags=entity.tags,
        created_at=now,
        updated_at=now,
    )
    db.add(db_entity)
    await db.flush()
    return db_entity


async def get_entity(db: AsyncSession, entity_id: UUID) -> EntityModel | None:
    """Get entity by ID.
    
    Args:
        db: Database session
        entity_id: Entity ID
        
    Returns:
        Entity model or None if not found
    """
    result = await db.execute(
        select(EntityModel).where(EntityModel.id == entity_id)
    )
    return result.scalar_one_or_none()


async def get_entities(
    db: AsyncSession,
    skip: int = 0,
    limit: int = 100,
    entity_type: str | None = None,
) -> list[EntityModel]:
    """Get list of entities with optional filtering.
    
    Args:
        db: Database session
        skip: Number of records to skip
        limit: Maximum number of records to return
        entity_type: Optional filter by entity type
        
    Returns:
        List of entity models
    """
    query = select(EntityModel)
    
    if entity_type:
        query = query.where(EntityModel.type == entity_type)
    
    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    return list(result.scalars().all())


async def update_entity(
    db: AsyncSession,
    entity_id: UUID,
    entity_update: EntityUpdate,
) -> EntityModel | None:
    """Update an entity.
    
    Args:
        db: Database session
        entity_id: Entity ID
        entity_update: Update data
        
    Returns:
        Updated entity model or None if not found
    """
    db_entity = await get_entity(db, entity_id)
    if not db_entity:
        return None
    
    # Update fields if provided
    update_data = entity_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_entity, field, value)
    
    db_entity.updated_at = datetime.utcnow()
    await db.flush()
    return db_entity


async def delete_entity(db: AsyncSession, entity_id: UUID) -> bool:
    """Delete an entity.
    
    Args:
        db: Database session
        entity_id: Entity ID
        
    Returns:
        True if deleted, False if not found
    """
    db_entity = await get_entity(db, entity_id)
    if not db_entity:
        return False
    
    await db.delete(db_entity)
    await db.flush()
    return True
