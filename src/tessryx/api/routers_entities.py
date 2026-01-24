"""API router for entity operations."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from . import crud_entities
from .database import get_db
from .schemas import EntityCreate, EntityResponse, EntityUpdate, SuccessResponse

router = APIRouter(prefix="/entities", tags=["entities"])


@router.post("/", response_model=EntityResponse, status_code=status.HTTP_201_CREATED)
async def create_entity(
    entity: EntityCreate,
    db: AsyncSession = Depends(get_db),
) -> EntityResponse:
    """Create a new entity.
    
    Args:
        entity: Entity creation data
        db: Database session
        
    Returns:
        Created entity
    """
    db_entity = await crud_entities.create_entity(db, entity)
    return EntityResponse.model_validate(db_entity)


@router.get("/{entity_id}", response_model=EntityResponse)
async def get_entity(
    entity_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> EntityResponse:
    """Get entity by ID.
    
    Args:
        entity_id: Entity ID
        db: Database session
        
    Returns:
        Entity details
        
    Raises:
        HTTPException: If entity not found
    """
    db_entity = await crud_entities.get_entity(db, entity_id)
    if not db_entity:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Entity {entity_id} not found"
        )
    return EntityResponse.model_validate(db_entity)


@router.get("/", response_model=list[EntityResponse])
async def list_entities(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    entity_type: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
) -> list[EntityResponse]:
    """List entities with optional filtering.
    
    Args:
        skip: Number of records to skip
        limit: Maximum number of records to return
        entity_type: Optional filter by entity type
        db: Database session
        
    Returns:
        List of entities
    """
    db_entities = await crud_entities.get_entities(
        db, skip=skip, limit=limit, entity_type=entity_type
    )
    return [EntityResponse.model_validate(e) for e in db_entities]


@router.patch("/{entity_id}", response_model=EntityResponse)
async def update_entity(
    entity_id: UUID,
    entity_update: EntityUpdate,
    db: AsyncSession = Depends(get_db),
) -> EntityResponse:
    """Update an entity.
    
    Args:
        entity_id: Entity ID
        entity_update: Update data
        db: Database session
        
    Returns:
        Updated entity
        
    Raises:
        HTTPException: If entity not found
    """
    db_entity = await crud_entities.update_entity(db, entity_id, entity_update)
    if not db_entity:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Entity {entity_id} not found"
        )
    return EntityResponse.model_validate(db_entity)


@router.delete("/{entity_id}", response_model=SuccessResponse)
async def delete_entity(
    entity_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> SuccessResponse:
    """Delete an entity.
    
    Args:
        entity_id: Entity ID
        db: Database session
        
    Returns:
        Success message
        
    Raises:
        HTTPException: If entity not found
    """
    deleted = await crud_entities.delete_entity(db, entity_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Entity {entity_id} not found"
        )
    return SuccessResponse(message=f"Entity {entity_id} deleted successfully")
