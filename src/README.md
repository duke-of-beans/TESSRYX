# TESSRYX Core - Python Implementation

Python implementation of the TessIR specification (universal dependency intelligence).

## Project Structure

```
src/tessryx/
├── __init__.py
├── py.typed                 # PEP 561 type marker
├── core/                    # Core TessIR primitives
│   ├── __init__.py
│   ├── entity.py           # Entity definition
│   ├── relation.py         # Relation definition
│   ├── constraint.py       # Constraint system
│   ├── provenance.py       # Provenance tracking
│   └── types.py            # Shared type definitions
├── kernel/                  # Graph operations and solving
│   ├── __init__.py
│   ├── graph_ops.py        # Graph algorithms (SCC, topo sort, blast radius)
│   ├── solver_ops.py       # Constraint solving orchestration
│   └── explain_ops.py      # Explanation generation
└── utils/                   # Utilities
    ├── __init__.py
    └── uuid_utils.py       # UUID generation helpers
```

## Installation

```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows

# Install in development mode
pip install -e ".[dev]"
```

## Development

```bash
# Run tests
pytest

# Type checking
mypy src/tessryx

# Code formatting
black src/tessryx tests
ruff check src/tessryx tests

# All checks
pytest && mypy src/tessryx && ruff check src/tessryx tests
```

## Quick Start

```python
from tessryx.core import Entity, Relation, Constraint
from uuid import uuid4

# Create entities
app = Entity(
    id=uuid4(),
    type="package",
    name="my-app",
    version="1.0.0"
)

react = Entity(
    id=uuid4(),
    type="package",
    name="react",
    version="18.2.0"
)

# Create relation
dependency = Relation(
    id=uuid4(),
    type="requires",
    from_entity=app.id,
    to_entity=react.id,
    strength=1.0
)

print(f"{app.name} requires {react.name}")
```

## License

MIT
