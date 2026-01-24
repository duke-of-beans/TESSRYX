"""Shared type definitions for TessIR."""

from datetime import datetime
from typing import Any, TypeAlias
from uuid import UUID

# Type aliases for clarity
EntityID: TypeAlias = UUID
RelationID: TypeAlias = UUID
ConstraintID: TypeAlias = UUID
DateTime: TypeAlias = datetime
Metadata: TypeAlias = dict[str, Any]
