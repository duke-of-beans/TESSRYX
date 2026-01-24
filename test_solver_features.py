"""Test mutex, choice, alternatives, and unsat cores."""

from uuid import uuid4
from tessryx.core.constraint import Constraint
from tessryx.core.entity import Entity
from tessryx.kernel.solver import SolutionStatus, ORToolsSolver


def test_mutex_constraint():
    """Test mutex: tasks A and B cannot overlap."""
    solver = ORToolsSolver()
    
    # Two tasks that would overlap if scheduled in parallel
    task_a = Entity(id=uuid4(), type="task", name="task_a", metadata={"duration": 5})
    task_b = Entity(id=uuid4(), type="task", name="task_b", metadata={"duration": 3})
    
    # Mutex: they cannot overlap
    mutex = Constraint(
        id=uuid4(), type="mutex", entities=[task_a.id, task_b.id],
        parameters={}, priority="hard"
    )
    
    solution = solver.solve(entities=[task_a, task_b], constraints=[mutex])
    
    assert solution.status == SolutionStatus.OPTIMAL
    
    # Get times
    a_start = solution.get_assignment(task_a.id, "start_time").value
    a_end = solution.get_assignment(task_a.id, "end_time").value
    b_start = solution.get_assignment(task_b.id, "start_time").value
    b_end = solution.get_assignment(task_b.id, "end_time").value
    
    # Verify no overlap: either A before B or B before A
    no_overlap = (a_end <= b_start) or (b_end <= a_start)
    assert no_overlap, f"Tasks overlap: A=[{a_start},{a_end}], B=[{b_start},{b_end}]"
    
    print(f"✅ Mutex test passed: A=[{a_start},{a_end}], B=[{b_start},{b_end}]")


def test_choice_constraint():
    """Test choice: exactly one task from set must be selected."""
    solver = ORToolsSolver()
    
    # Three tasks, only one can be selected
    task_a = Entity(id=uuid4(), type="task", name="task_a", metadata={"duration": 2})
    task_b = Entity(id=uuid4(), type="task", name="task_b", metadata={"duration": 3})
    task_c = Entity(id=uuid4(), type="task", name="task_c", metadata={"duration": 1})
    
    # Choice: exactly one
    choice = Constraint(
        id=uuid4(), type="choice",
        entities=[task_a.id, task_b.id, task_c.id],
        parameters={}, priority="hard"
    )
    
    solution = solver.solve(entities=[task_a, task_b, task_c], constraints=[choice])
    
    print(f"Choice solution status: {solution.status}")
    if solution.proof:
        print(f"Proof: {solution.proof}")
    
    assert solution.status == SolutionStatus.OPTIMAL
    
    # Count how many tasks were selected using the boolean variables
    selected_count = 0
    for task in [task_a, task_b, task_c]:
        selected_assignment = solution.get_assignment(task.id, "selected")
        if selected_assignment and selected_assignment.value == 1:
            selected_count += 1
            print(f"  Selected: {task.name}")
    
    assert selected_count == 1, f"Expected 1 selected, got {selected_count}"
    print(f"✅ Choice test passed: exactly 1 task selected")


def test_alternative_generation():
    """Test finding multiple alternative solutions."""
    solver = ORToolsSolver()
    
    # Simple problem with multiple valid solutions
    task_a = Entity(id=uuid4(), type="task", name="task_a", metadata={"duration": 2})
    task_b = Entity(id=uuid4(), type="task", name="task_b", metadata={"duration": 2})
    
    # No constraints - many possible schedules
    solution_set = solver.find_alternatives(
        entities=[task_a, task_b],
        constraints=[],
        max_solutions=3
    )
    
    assert solution_set.optimal.status in (SolutionStatus.OPTIMAL, SolutionStatus.FEASIBLE)
    assert solution_set.total_feasible >= 1
    
    print(f"✅ Alternative generation: found {solution_set.total_feasible} solutions")
    print(f"  Optimal: {solution_set.optimal.assignments[:2]}")
    if solution_set.alternatives:
        print(f"  Alternatives: {len(solution_set.alternatives)}")


def test_unsat_core():
    """Test finding minimal conflicting constraints."""
    solver = ORToolsSolver()
    
    # Create impossible problem: A before B, B before C, C before A (cycle)
    task_a = Entity(id=uuid4(), type="task", name="task_a", metadata={"duration": 1})
    task_b = Entity(id=uuid4(), type="task", name="task_b", metadata={"duration": 1})
    task_c = Entity(id=uuid4(), type="task", name="task_c", metadata={"duration": 1})
    
    constraints = [
        Constraint(id=uuid4(), type="precedence", entities=[task_a.id, task_b.id], parameters={}, priority="hard"),
        Constraint(id=uuid4(), type="precedence", entities=[task_b.id, task_c.id], parameters={}, priority="hard"),
        Constraint(id=uuid4(), type="precedence", entities=[task_c.id, task_a.id], parameters={}, priority="hard"),  # Creates cycle
    ]
    
    core = solver.find_unsat_core(entities=[task_a, task_b, task_c], constraints=constraints)
    
    assert len(core.conflicting_constraints) > 0
    assert len(core.suggested_relaxations) > 0
    
    print(f"✅ Unsat core found: {len(core.conflicting_constraints)} conflicting constraints")
    print(f"  Explanation: {core.explanation}")
    print(f"  Suggested fixes: {core.suggested_relaxations[0]}")


if __name__ == "__main__":
    test_mutex_constraint()
    test_choice_constraint()
    test_alternative_generation()
    test_unsat_core()
    print("\n🎉 All solver features working!")
