"""First OR-Tools test - 3 tasks with precedence."""

from uuid import uuid4
from tessryx.core.constraint import Constraint
from tessryx.core.entity import Entity
from tessryx.kernel.solver import SolutionStatus
from tessryx.kernel.solver.or_tools_adapter import ORToolsSolver


def test_schedule_three_tasks_with_precedence():
    """Test scheduling 3 tasks: A -> B -> C"""
    solver = ORToolsSolver()

    # Create three tasks
    task_a = Entity(id=uuid4(), type="task", name="task_a", metadata={"duration": 2})
    task_b = Entity(id=uuid4(), type="task", name="task_b", metadata={"duration": 3})
    task_c = Entity(id=uuid4(), type="task", name="task_c", metadata={"duration": 1})

    # Precedence constraints
    constraint_ab = Constraint(
        id=uuid4(), type="precedence", entities=[task_a.id, task_b.id],
        parameters={}, priority="hard"
    )
    constraint_bc = Constraint(
        id=uuid4(), type="precedence", entities=[task_b.id, task_c.id],
        parameters={}, priority="hard"
    )

    # Solve
    solution = solver.solve(
        entities=[task_a, task_b, task_c],
        constraints=[constraint_ab, constraint_bc],
    )

    # Verify
    print(f"Solution status: {solution.status}")
    print(f"Solve time: {solution.solve_time_seconds:.3f}s")
    print(f"Assignments: {len(solution.assignments)}")
    if solution.proof:
        print(f"Proof: {solution.proof}")
    
    assert solution.status == SolutionStatus.OPTIMAL
    
    # Check assignments
    for assignment in solution.assignments:
        entity_name = next(e.name for e in [task_a, task_b, task_c] if e.id == assignment.entity_id)
        print(f"  {entity_name}.{assignment.attribute} = {assignment.value}")
    
    print("✅ Test passed!")

if __name__ == "__main__":
    test_schedule_three_tasks_with_precedence()
