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

from abc import ABC, abstractmethod
from collections.abc import Iterator
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import TYPE_CHECKING

from pyprolog.core.binding_environment import BindingEnvironment
from pyprolog.core.types import PrologType

if TYPE_CHECKING:
    from pyprolog.runtime.interpreter import Interpreter


@dataclass
class PushFrame:
    """step() return value: Request to push a child goal onto the stack.

    The while loop determines the goal type and creates appropriate frame.
    """

    goal: PrologType
    env: BindingEnvironment


@dataclass
class YieldEnv:
    """step() return value: Request to yield a solution."""

    env: BindingEnvironment


class FrameType(Enum):
    """Frame type discriminator for pattern matching."""

    GOAL = auto()
    GOAL_SEQ = auto()
    OPERATOR = auto()
    CHOICE_POINT = auto()
    NEGATION = auto()
    CONJUNCTION = auto()
    BODY = auto()
    DISJUNCTION = auto()


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
    def step(self, interpreter: Interpreter) -> PushFrame | YieldEnv | None:
        """Execute one step of this frame.

        Args:
            interpreter: The interpreter instance for accessing execution methods

        Returns:
            - PushFrame: Push a child goal onto the stack
            - YieldEnv: Yield a solution environment
            - None: Internal state transition (loop will call step() again)

        Raises:
            StopIteration: Frame exhausted all alternatives
            CutException: Cut occurred
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
    """Frame for executing a single atomic goal — fully frame-driven version.

    State machine: init → try_clause → wait_body → try_clause → ... → done
    Clause candidates are iterated internally.
    Body execution is delegated to the stack via PushFrame (no recursion).
    """

    goal: PrologType | None = None
    state: str = "init"
    _clause_iter: Iterator | None = field(default=None, repr=False)
    frame_type: FrameType = field(default=FrameType.GOAL, init=False)

    def step(self, interpreter: Interpreter) -> PushFrame | YieldEnv | None:
        """Execute one step of goal resolution.

        Returns:
            - PushFrame: Delegate body execution to stack
            - YieldEnv: Solution from builtin predicate
            - None: Internal state transition

        Raises:
            StopIteration: All clauses exhausted
        """
        if self.state == "init":
            # Request clause candidates from interpreter
            self._clause_iter = interpreter.logic_interpreter._solve_goal_for_frame(
                self.goal, self.env
            )
            self.state = "try_clause"
            return None  # Next step() will try first clause

        elif self.state == "try_clause":
            try:
                result = next(self._clause_iter)
                # result is PushFrame (user-defined predicate body)
                # or YieldEnv (builtin solution)
                if isinstance(result, PushFrame):
                    self.state = "wait_body"
                return result
            except StopIteration:
                raise  # All clauses failed

        elif self.state == "wait_body":
            # Body frame popped with StopIteration → came back here
            # This clause exhausted all solutions → try next clause
            self.state = "try_clause"
            return None  # Next step() will try next clause

        else:
            raise StopIteration

    def can_backtrack(self) -> bool:
        """Check if goal has more clauses to try."""
        return self._clause_iter is not None and self.state != "done"


@dataclass
class GoalSeqFrame(Frame):
    """Frame for executing a sequence of goals (conjunction).

    Implements backtracking-aware conjunction using an internal stack
    of (index, iterator) pairs, mirroring _execute_goal_sequence logic.

    This approach enables proper Prolog conjunction semantics:
    - When the last goal exhausts, backtrack to previous goal
    - Previous goal's next solution re-initiates subsequent goals
    """

    goals: list[PrologType] = field(default_factory=list)
    goal_stack: list[tuple[int, Iterator[BindingEnvironment]]] = field(
        default_factory=list
    )
    frame_type: FrameType = field(default=FrameType.GOAL_SEQ, init=False)
    initialized: bool = False

    def step(self, interpreter: Interpreter) -> BindingEnvironment | None:
        """Execute conjunction with proper backtracking.

        Returns:
        - BindingEnvironment: A solution was found
        - None: Conjunction exhausted all possibilities
        """
        # Initialize on first call
        if not self.initialized:
            if not self.goals:
                return self.env
            # Start with first goal
            first_iter = interpreter.execute(self.goals[0], self.env)
            self.goal_stack.append((0, first_iter))
            self.initialized = True

        # Process goal stack (same logic as _execute_goal_sequence)
        while self.goal_stack:
            index, iterator = self.goal_stack[-1]

            try:
                next_env = next(iterator)
            except StopIteration:
                # Current goal exhausted, backtrack
                self.goal_stack.pop()
                continue

            # Check if last goal
            if index == len(self.goals) - 1:
                # All goals succeeded, return solution
                return next_env

            # Push next goal
            next_index = index + 1
            next_iter = interpreter.execute(self.goals[next_index], next_env)
            self.goal_stack.append((next_index, next_iter))

        # All goals exhausted
        return None

    def can_backtrack(self) -> bool:
        """Check if backtracking is possible."""
        return len(self.goal_stack) > 0


@dataclass
class NegationFrame(Frame):
    """Frame for negation as failure (\\+/1) — inner_goal success/failure check.

    inner_goal succeeds → negation fails (StopIteration)
    inner_goal fails → negation succeeds (YieldEnv)
    CutException is absorbed (Cut barrier)

    Note: inner_goal is executed via PushFrame delegation to maintain explicit stack.
    State machine ensures proper cut isolation and backtracking behavior.
    """

    inner_goal: PrologType | None = None
    checked: bool = False
    solution_found: bool = False
    inner_started: bool = False  # Tracks if inner goal execution has been initiated
    inner_succeeded: bool = False  # Tracks if inner goal produced a solution
    entry_stack_depth: int = 0  # Stack depth at entry (for restoration on failure)
    entry_choice_depth: int = 0  # Choice point depth at entry (for cut isolation)
    frame_type: FrameType = field(default=FrameType.NEGATION, init=False)

    def step(self, interpreter: Interpreter) -> PushFrame | YieldEnv | None:
        """Execute negation as failure logic with explicit frame delegation.

        State machine:
        1. First call: Set inner_started, return None (execute_iterative will push inner goal)
        2. Inner goal completion: Check inner_succeeded
           - If succeeded: negation fails (StopIteration)
           - If failed: negation succeeds (YieldEnv)

        Returns:
            - None: Signal to push inner goal onto stack
            - YieldEnv: Negation succeeded (inner goal failed)

        Raises:
            StopIteration: Negation failed (inner goal succeeded) or already checked
        """
        if self.checked:
            raise StopIteration

        # Mark as started for execute_iterative
        if not self.inner_started:
            self.inner_started = True
            return None  # Signal: execute_iterative will push inner_goal

        # Inner goal execution completed, check result
        self.checked = True

        if not self.inner_succeeded:
            return YieldEnv(env=self.env)  # negation succeeds
        else:
            raise StopIteration  # negation fails

    def record_success(self) -> None:
        """Record that inner goal succeeded (called by execute_iterative)."""
        self.inner_succeeded = True

    def can_backtrack(self) -> bool:
        """Negation frames don't backtrack themselves."""
        return False


@dataclass
class DisjunctionFrame(Frame):
    """Frame for disjunction (;/2) — fully frame-driven version.

    State machine: init_left → wait_left → init_right → wait_right → done
    Child frames' YieldEnv are yielded directly by the while loop (not through DisjunctionFrame).
    Child frame StopIteration → pop → DisjunctionFrame.step() is called.

    CutException handling:
    - DisjunctionFrame does NOT catch CutException
    - While loop catches it and pops frames up to the disjunction
    - Right branch is skipped (because DisjunctionFrame is popped)
    """

    left_goal: PrologType | None = None
    right_goal: PrologType | None = None
    state: str = "init_left"
    frame_type: FrameType = field(default=FrameType.DISJUNCTION, init=False)

    def step(self, interpreter: Interpreter) -> PushFrame | YieldEnv | None:
        """Execute disjunction state machine.

        Returns:
            - PushFrame: Push left or right child goal
            - None: Internal state transition

        Raises:
            StopIteration: Both branches exhausted
        """
        if self.state == "init_left":
            self.state = "wait_left"
            return PushFrame(goal=self.left_goal, env=self.env)

        elif self.state == "wait_left":
            # Child frame (left) popped with StopIteration → came back here
            # Left exhausted → move to right
            self.state = "init_right"
            return self.step(interpreter)  # Immediately transition to init_right

        elif self.state == "init_right":
            self.state = "wait_right"
            return PushFrame(goal=self.right_goal, env=self.env)

        elif self.state == "wait_right":
            # Right also exhausted
            self.state = "done"
            raise StopIteration

        else:
            raise StopIteration

    def can_backtrack(self) -> bool:
        """Check if disjunction has more alternatives."""
        return self.state not in ("done", "wait_right")


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
    args: list[PrologType] = field(default_factory=list)
    state: str = "initial"  # "initial", "left", "right", "done"
    left_tried: bool = False
    frame_type: FrameType = field(default=FrameType.OPERATOR, init=False)

    def step(self, interpreter: Interpreter) -> BindingEnvironment | None:
        """Execute operator-specific logic.

        Returns:
            Binding environment on success, None for state transitions
        """
        if self.operator == ",":
            # Conjunction: should be flattened to GoalSeqFrame
            # This is a fallback/transition case (unused in v2)
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

    def restore(self, stack: list[Frame]):
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

    stack: list[Frame] = field(default_factory=list)
    choice_points: list[ChoicePoint] = field(default_factory=list)
    cut_barrier: int | None = None  # Stack depth at cut

    def push_goal(self, goal: PrologType, env: BindingEnvironment) -> None:
        """Push a new goal frame with logical operator detection.

        Routes goals to appropriate frame types:
        - Conjunction (,/2): GoalSeqFrame for sequential execution
        - Disjunction (;/2): ChoicePoint with two alternatives
        - Negation (\\+/1): NegationFrame with inner goal
        - Atomic goals: GoalFrame (executed by _execute_single_goal)

        Args:
            goal: The goal to execute
            env: The binding environment
        """
        from pyprolog.core.types import Atom, Term

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

            # Disjunction: create choice point with two alternatives
            if functor_name == ";" and len(goal.args) == 2:
                left_goal, right_goal = goal.args[0], goal.args[1]
                # Push right alternative as choice point
                right_frame = GoalFrame(env=env.copy(), goal=right_goal)
                self.push_choice_point(right_frame)
                # Push left alternative immediately
                self.push_goal(left_goal, env)
                return

            # Negation: create NegationFrame
            if functor_name == "\\+" and len(goal.args) == 1:
                inner_goal = goal.args[0]
                negation_frame = NegationFrame(
                    env=env,
                    inner_goal=inner_goal,
                    entry_stack_depth=len(
                        self.stack
                    ),  # Now matches NegationFrame fields
                    entry_choice_depth=len(
                        self.choice_points
                    ),  # Now matches NegationFrame fields
                )
                self.stack.append(negation_frame)
                return

        # Default: atomic goal
        self.stack.append(GoalFrame(env=env, goal=goal))

    def _flatten_conjunction(self, goal: PrologType, result: list[PrologType]) -> None:
        """Flatten nested conjunction into a flat list.

        Args:
            goal: Goal to flatten
            result: List to append flattened goals to
        """
        from pyprolog.core.types import Atom, Term

        if isinstance(goal, Term) and isinstance(goal.functor, Atom):
            if goal.functor.name == "," and len(goal.args) == 2:
                # Recursively flatten left and right
                self._flatten_conjunction(goal.args[0], result)
                self._flatten_conjunction(goal.args[1], result)
                return

        # Base case: not a conjunction, add as-is
        result.append(goal)

    def push_goal_sequence(
        self, goals: list[PrologType], env: BindingEnvironment
    ) -> BindingEnvironment | None:
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
        self.stack.append(GoalSeqFrame(env=env, goals=goals))
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
