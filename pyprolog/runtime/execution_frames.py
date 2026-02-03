"""Execution frame data structures for iterative goal execution.

This module provides the data structures needed to convert the recursive
execute/evaluator/_execute_goal_sequence mutual recursion into an explicit
stack-based iterative approach.

Key components:
- Frame: Base class for execution stack frames
- GoalFrame: Executes a single goal
- GoalSeqFrame: Executes a sequence of goals (conjunction)
- OperatorFrame: Handles logical operators (,/2, ;/2, \\+/1)
- ChoicePoint: Backtracking checkpoint
- ExecutionState: Unified execution state with stack and choice points
"""

from __future__ import annotations
from dataclasses import dataclass, field
from abc import ABC, abstractmethod
from typing import Iterator, Optional, List, TYPE_CHECKING
from enum import Enum, auto

from pyprolog.core.types import PrologType
from pyprolog.core.binding_environment import BindingEnvironment

if TYPE_CHECKING:
    from pyprolog.runtime.interpreter import Interpreter


class FrameType(Enum):
    """Frame type discriminator for pattern matching."""

    GOAL = auto()
    GOAL_SEQ = auto()
    OPERATOR = auto()
    CHOICE_POINT = auto()


@dataclass
class Frame(ABC):
    """Base class for execution stack frames.

    Each frame represents a unit of execution in the iterative interpreter.
    Frames maintain their own state and can produce multiple results through
    backtracking.
    """

    frame_type: FrameType
    env: BindingEnvironment

    @abstractmethod
    def step(self, interpreter: Interpreter) -> Optional[BindingEnvironment]:
        """Execute one step of this frame.

        Args:
            interpreter: The interpreter instance for accessing execution methods

        Returns:
            - BindingEnvironment: Frame produced a result, yield this environment
            - None: Frame needs more work or should be popped

        Raises:
            StopIteration: Frame exhausted all alternatives
        """
        pass

    @abstractmethod
    def can_backtrack(self) -> bool:
        """Check if this frame has more alternatives to try.

        Returns:
            True if frame can produce more results on backtracking
        """
        pass


@dataclass
class GoalFrame(Frame):
    """Frame for executing a single goal.

    Encapsulates:
    - The goal to execute
    - Iterator over solutions
    - Current solution binding environment

    The frame lazily initializes the solutions iterator on first step(),
    then produces solutions one at a time on subsequent calls.
    """

    goal: Optional[PrologType] = None
    solutions: Optional[Iterator[BindingEnvironment]] = None
    frame_type: FrameType = field(default=FrameType.GOAL, init=False)

    def step(self, interpreter: Interpreter) -> Optional[BindingEnvironment]:
        """Get next solution from goal execution.

        First call initializes the solutions iterator.
        Subsequent calls pull next solution.

        Returns:
            Next binding environment or None if exhausted
        """
        if self.solutions is None:
            # First call: initialize solutions iterator
            # Use interpreter's internal method to execute this single goal
            self.solutions = interpreter._execute_single_goal(self.goal, self.env)

        try:
            next_env = next(self.solutions)
            return next_env
        except StopIteration:
            return None  # Signal to pop this frame

    def can_backtrack(self) -> bool:
        """Check if goal has more solutions."""
        return self.solutions is not None


@dataclass
class GoalSeqFrame(Frame):
    """Frame for executing a sequence of goals (conjunction).

    Tracks:
    - Remaining goals to execute
    - Current goal index
    - Whether sequence completion should yield result

    The frame coordinates execution of multiple goals in sequence.
    Each goal must succeed before proceeding to the next.
    """

    goals: List[PrologType] = field(default_factory=list)
    current_index: int = 0
    frame_type: FrameType = field(default=FrameType.GOAL_SEQ, init=False)

    def step(self, interpreter: Interpreter) -> Optional[BindingEnvironment]:
        """Process goal sequence.

        Returns:
        - None: Need to push next goal frame (not done yet)
        - env: Sequence complete, yield this environment
        """
        if self.current_index >= len(self.goals):
            # All goals succeeded
            return self.env

        # Need to execute next goal
        return None  # Signals: push GoalFrame for goals[current_index]

    def advance(self, result_env: BindingEnvironment):
        """Advance to next goal after current goal succeeded.

        Args:
            result_env: The binding environment from the successful goal
        """
        self.env = result_env
        self.current_index += 1

    def can_backtrack(self) -> bool:
        """Goal sequences don't backtrack themselves; child goals do."""
        return False


@dataclass
class OperatorFrame(Frame):
    """Frame for logical operators (,/2, ;/2, \\+/1).

    Handles:
    - Conjunction (,): Flattened into GoalSeqFrame
    - Disjunction (;): Two alternative branches
    - Negation (\\+): Success on failure check

    State machine tracks which branch/phase of operator execution.
    """

    operator: str = ""
    args: List[PrologType] = field(default_factory=list)
    state: str = "initial"  # "initial", "left", "right", "done"
    left_tried: bool = False
    frame_type: FrameType = field(default=FrameType.OPERATOR, init=False)

    def step(self, interpreter: Interpreter) -> Optional[BindingEnvironment]:
        """Execute operator-specific logic.

        Returns:
            Binding environment on success, None for state transitions
        """
        if self.operator == ",":
            # Conjunction: should be flattened to GoalSeqFrame
            # This is a fallback/transition case
            from pyprolog.core.types import Term, Atom

            goals = interpreter._flatten_conjunction(Term(Atom(","), self.args))
            return None  # Signal: replace with GoalSeqFrame(goals)

        elif self.operator == ";":
            # Disjunction: try left, then right
            if self.state == "initial":
                self.state = "left"
                return None  # Signal: push left goal
            elif self.state == "left":
                # Left branch exhausted, try right
                self.state = "right"
                return None  # Signal: push right goal
            else:
                return None  # Both branches exhausted, pop frame

        elif self.operator == "\\+":
            # Negation: succeed if goal fails
            if self.state == "initial":
                self.state = "checking"
                return None  # Signal: push goal to check failure
            else:
                # Goal failed, negation succeeds
                return self.env

        return None

    def can_backtrack(self) -> bool:
        """Disjunction can backtrack between branches."""
        return self.operator == ";" and self.state == "left"


@dataclass
class ChoicePoint:
    """Checkpoint for backtracking.

    Records:
    - Stack state before a choice
    - Alternative to try on backtracking

    When backtracking, the stack is restored to the checkpoint depth
    and the alternative frame is pushed.
    """

    stack_depth: int
    alternative_frame: Frame

    def restore(self, stack: List[Frame]):
        """Restore stack to choice point and push alternative.

        Args:
            stack: The execution stack to restore
        """
        # Truncate stack to checkpoint
        while len(stack) > self.stack_depth:
            stack.pop()
        # Push alternative frame
        stack.append(self.alternative_frame)


@dataclass
class ExecutionState:
    """Complete execution state for iterative loop.

    Contains:
    - Main execution stack
    - Choice point stack (for backtracking)
    - Cut barrier (for !/0 handling)

    This encapsulates all state needed for the iterative interpreter,
    replacing the implicit call stack of the recursive implementation.
    """

    stack: List[Frame] = field(default_factory=list)
    choice_points: List[ChoicePoint] = field(default_factory=list)
    cut_barrier: Optional[int] = None  # Stack depth at cut

    def push_goal(self, goal: PrologType, env: BindingEnvironment) -> None:
        """Push a new goal frame with logical operator detection.

        Routes goals to appropriate frame types:
        - Conjunction (,/2): GoalSeqFrame for sequential execution
        - Disjunction (;/2): OperatorFrame (handled by operator evaluator)
        - Negation (\+/1): OperatorFrame (handled by operator evaluator)
        - Atomic goals: GoalFrame (executed by _execute_single_goal)

        Args:
            goal: The goal to execute
            env: The binding environment
        """
        from pyprolog.core.types import Term, Atom

        # Detect logical operators
        if isinstance(goal, Term) and isinstance(goal.functor, Atom):
            functor_name = goal.functor.name

            # Conjunction: expand to GoalSeqFrame
            if functor_name == "," and len(goal.args) == 2:
                # Flatten conjunction into sequence
                goals = []
                self._flatten_conjunction(goal, goals)
                self.stack.append(GoalSeqFrame(env=env, goals=goals))
                return

            # Disjunction and Negation: use OperatorFrame
            # (These will be handled by operator evaluators in execute())
            if functor_name in (";", "\\+"):
                # For now, create GoalFrame and let it fail with assertion
                # Phase 4 will properly route these through execute()
                self.stack.append(GoalFrame(env=env, goal=goal))
                return

        # Default: atomic goal
        self.stack.append(GoalFrame(env=env, goal=goal))

    def _flatten_conjunction(
        self, goal: PrologType, result: list[PrologType]
    ) -> None:
        """Flatten nested conjunction into a flat list.

        Args:
            goal: Goal to flatten
            result: List to append flattened goals to
        """
        from pyprolog.core.types import Term, Atom

        if isinstance(goal, Term) and isinstance(goal.functor, Atom):
            if goal.functor.name == "," and len(goal.args) == 2:
                # Recursively flatten left and right
                self._flatten_conjunction(goal.args[0], result)
                self._flatten_conjunction(goal.args[1], result)
                return

        # Base case: not a conjunction, add as-is
        result.append(goal)

    def push_goal_sequence(
        self, goals: List[PrologType], env: BindingEnvironment
    ) -> Optional[BindingEnvironment]:
        """Push a goal sequence frame.

        Args:
            goals: List of goals to execute in sequence
            env: The binding environment

        Returns:
            Environment if empty sequence, None otherwise
        """
        if not goals:
            # Empty sequence: immediately yield env
            return env
        self.stack.append(GoalSeqFrame(env=env, goals=goals, current_index=0))
        return None

    def push_choice_point(self, alternative: Frame) -> None:
        """Record a backtracking choice point.

        Args:
            alternative: The alternative frame to try on backtracking
        """
        cp = ChoicePoint(stack_depth=len(self.stack), alternative_frame=alternative)
        self.choice_points.append(cp)

    def backtrack(self) -> bool:
        """Backtrack to most recent choice point.

        Returns:
            True if backtracking successful, False if no more choice points.
        """
        if not self.choice_points:
            return False

        cp = self.choice_points.pop()
        cp.restore(self.stack)
        return True

    def apply_cut(self) -> None:
        """Apply cut: remove choice points up to barrier."""
        if self.cut_barrier is not None:
            # Remove choice points above cut barrier
            self.choice_points = [
                cp for cp in self.choice_points if cp.stack_depth < self.cut_barrier
            ]

    def __repr__(self) -> str:
        """Debug representation of execution state."""
        return (
            f"ExecutionState(\n"
            f"  stack={len(self.stack)} frames,\n"
            f"  choice_points={len(self.choice_points)},\n"
            f"  cut_barrier={self.cut_barrier}\n"
            f")"
        )
