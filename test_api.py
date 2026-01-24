"""Quick test of the API endpoints."""

import asyncio
from uuid import uuid4

import httpx


async def test_api() -> None:
    """Test basic API functionality."""
    base_url = "http://localhost:8000"
    
    async with httpx.AsyncClient() as client:
        # Test health endpoint
        print("Testing health endpoint...")
        response = await client.get(f"{base_url}/health")
        print(f"Health: {response.json()}")
        
        # Test root endpoint
        print("\nTesting root endpoint...")
        response = await client.get(f"{base_url}/")
        print(f"Root: {response.json()}")
        
        # Create an entity
        print("\nCreating entity...")
        entity_data = {
            "name": "Test Entity",
            "type": "component",
            "version": "1.0.0",
            "attributes": {"test": True},
            "tags": ["example", "test"]
        }
        response = await client.post(f"{base_url}/entities/", json=entity_data)
        entity = response.json()
        entity_id = entity["id"]
        print(f"Created entity: {entity_id}")
        
        # Get the entity
        print("\nGetting entity...")
        response = await client.get(f"{base_url}/entities/{entity_id}")
        print(f"Entity: {response.json()['name']}")
        
        # List entities
        print("\nListing entities...")
        response = await client.get(f"{base_url}/entities/")
        entities = response.json()
        print(f"Found {len(entities)} entities")
        
        # Update entity
        print("\nUpdating entity...")
        update_data = {"name": "Updated Test Entity"}
        response = await client.patch(f"{base_url}/entities/{entity_id}", json=update_data)
        print(f"Updated: {response.json()['name']}")
        
        # Delete entity
        print("\nDeleting entity...")
        response = await client.delete(f"{base_url}/entities/{entity_id}")
        print(f"Deleted: {response.json()['message']}")
        
        print("\n✅ All tests passed!")


if __name__ == "__main__":
    asyncio.run(test_api())
