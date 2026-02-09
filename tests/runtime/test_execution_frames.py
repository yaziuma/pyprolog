"""Unit tests for execution frame data structures.

Tests frame creation, state transitions, and stack operations without
requiring full interpreter integration.
"""

from pyprolog.core.binding_environment import BindingEnvironment
from pyprolog.core.types import Atom, Term, Variable
from pyprolog.runtime.execution_frames import (
    ChoicePoint,
    ExecutionState,
    FrameType,
    GoalFrame,
    GoalSeqFrame,
    OperatorFrame,
)


class TestFrameType:
    """Test FrameType enum."""

    def test_frame_type_values(self):
        """Verify all frame types are defined."""
        assert FrameType.GOAL
        assert FrameType.GOAL_SEQ
        assert FrameType.OPERATOR
        assert FrameType.CHOICE_POINT


class TestGoalFrame:
    """Test GoalFrame creation and behavior."""

    def test_goal_frame_initialization(self):
        """Test GoalFrame creation and basic properties."""
        goal = Term(Atom("member"), [Variable("X"), Term(Atom("[]"), [])])
        env = BindingEnvironment()
        frame = GoalFrame(env=env, goal=goal)

        assert frame.frame_type == FrameType.GOAL
        assert frame.goal == goal
        assert frame.env == env
        assert frame.solutions is None

    def test_goal_frame_can_backtrack(self):
        """Test can_backtrack returns True when solutions iterator exists."""
        env = BindingEnvironment()
        frame = GoalFrame(env=env, goal=Atom("test"))

        # Before step: no solutions yet
        assert frame.solutions is None
        assert not frame.can_backtrack()

        # After setting solutions (simulated)
        frame.solutions = iter([env])
        assert frame.can_backtrack()

    def test_goal_frame_step_returns_none_when_exhausted(self):
        """Test step returns None when solutions exhausted."""
        env = BindingEnvironment()
        frame = GoalFrame(env=env, goal=Atom("test"))

        # Simulate exhausted iterator
        frame.solutions = iter([])

        result = frame.step(None)  # type: ignore
        assert result is None


class TestGoalSeqFrame:
    """Test GoalSeqFrame for goal sequences."""

    def test_goal_seq_frame_initialization(self):
        """Test GoalSeqFrame creation."""
        goals = [
            Term(Atom("a"), [Variable("X")]),
            Term(Atom("b"), [Variable("X")]),
            Term(Atom("c"), [Variable("X")]),
        ]
        env = BindingEnvironment()
        frame = GoalSeqFrame(env=env, goals=goals)

        assert frame.frame_type == FrameType.GOAL_SEQ
        assert frame.goals == goals
        assert not frame.initialized
        assert frame.env == env

    def test_goal_seq_frame_advancement(self):
        """Test GoalSeqFrame tracks progress through goals."""
        goals = [
            Term(Atom("a"), [Variable("X")]),
            Term(Atom("b"), [Variable("X")]),
            Term(Atom("c"), [Variable("X")]),
        ]
        env = BindingEnvironment()
        frame = GoalSeqFrame(env=env, goals=goals)

        # V2: GoalSeqFrame uses goal_stack internally, no current_index
        assert frame.goals == goals
        assert not frame.initialized
        assert frame.goal_stack == []

    def test_goal_seq_frame_step_completion(self):
        """Test step returns env when all goals completed."""
        goals = []
        env = BindingEnvironment()
        frame = GoalSeqFrame(env=env, goals=goals)

        # Empty goals: step should return env immediately
        result = frame.step(None)  # type: ignore
        assert result == env

    def test_goal_seq_frame_step_not_done(self):
        """Test step returns None when more goals remain (exhausted)."""
        goals = [Atom("a"), Atom("b")]
        env = BindingEnvironment()
        frame = GoalSeqFrame(env=env, goals=goals)

        # V2: After initialization, step needs interpreter to execute goals
        # For unit test without interpreter, we simulate exhausted state
        frame.initialized = True
        frame.goal_stack = []  # All goals exhausted

        result = frame.step(None)  # type: ignore
        assert result is None

    def test_goal_seq_frame_cannot_backtrack(self):
        """Test goal sequences can backtrack when goal_stack is not empty."""
        goals = [Atom("a"), Atom("b")]
        env = BindingEnvironment()
        frame = GoalSeqFrame(env=env, goals=goals)

        # V2: can_backtrack checks len(goal_stack) > 0
        assert not frame.can_backtrack()  # Initially empty

        # Simulate goal_stack with an item
        frame.goal_stack = [(0, iter([env]))]
        assert frame.can_backtrack()


class TestOperatorFrame:
    """Test OperatorFrame for logical operators."""

    def test_operator_frame_initialization(self):
        """Test OperatorFrame creation."""
        args = [Atom("a"), Atom("b")]
        env = BindingEnvironment()
        frame = OperatorFrame(env=env, operator=";", args=args)

        assert frame.frame_type == FrameType.OPERATOR
        assert frame.operator == ";"
        assert frame.args == args
        assert frame.state == "initial"
        assert not frame.left_tried

    def test_disjunction_can_backtrack(self):
        """Test disjunction can backtrack when in left state."""
        env = BindingEnvironment()
        frame = OperatorFrame(env=env, operator=";", args=[])

        # Initial state: cannot backtrack yet
        assert not frame.can_backtrack()

        # Left state: can backtrack to right
        frame.state = "left"
        assert frame.can_backtrack()

        # Right state: cannot backtrack
        frame.state = "right"
        assert not frame.can_backtrack()

    def test_conjunction_cannot_backtrack(self):
        """Test conjunction (,) doesn't backtrack at operator level."""
        env = BindingEnvironment()
        frame = OperatorFrame(env=env, operator=",", args=[])

        assert not frame.can_backtrack()

    def test_negation_cannot_backtrack(self):
        """Test negation (\\+) doesn't backtrack."""
        env = BindingEnvironment()
        frame = OperatorFrame(env=env, operator="\\+", args=[])

        assert not frame.can_backtrack()


class TestChoicePoint:
    """Test ChoicePoint for backtracking."""

    def test_choice_point_creation(self):
        """Test ChoicePoint initialization."""
        env = BindingEnvironment()
        alternative = GoalFrame(env=env, goal=Atom("alternative"))
        cp = ChoicePoint(stack_depth=2, alternative_frame=alternative)

        assert cp.stack_depth == 2
        assert cp.alternative_frame == alternative

    def test_choice_point_restore(self):
        """Test ChoicePoint stack restoration."""
        env = BindingEnvironment()
        stack = [
            GoalFrame(env=env, goal=Atom("a")),
            GoalFrame(env=env, goal=Atom("b")),
            GoalFrame(env=env, goal=Atom("c")),
        ]

        alternative = GoalFrame(env=env, goal=Atom("d"))
        cp = ChoicePoint(stack_depth=2, alternative_frame=alternative)

        cp.restore(stack)

        # Stack should be truncated to depth 2, then alternative pushed
        assert len(stack) == 3
        assert stack[-1].goal == Atom("d")
        assert stack[0].goal == Atom("a")
        assert stack[1].goal == Atom("b")

    def test_choice_point_restore_empty_stack(self):
        """Test restore when stack is deeper than checkpoint."""
        env = BindingEnvironment()
        stack = [
            GoalFrame(env=env, goal=Atom("a")),
            GoalFrame(env=env, goal=Atom("b")),
            GoalFrame(env=env, goal=Atom("c")),
            GoalFrame(env=env, goal=Atom("d")),
            GoalFrame(env=env, goal=Atom("e")),
        ]

        alternative = GoalFrame(env=env, goal=Atom("alt"))
        cp = ChoicePoint(stack_depth=1, alternative_frame=alternative)

        cp.restore(stack)

        # Should truncate to depth 1, then push alternative
        assert len(stack) == 2
        assert stack[0].goal == Atom("a")
        assert stack[1].goal == Atom("alt")


class TestExecutionState:
    """Test ExecutionState for unified stack management."""

    def test_execution_state_initialization(self):
        """Test ExecutionState creation."""
        state = ExecutionState()

        assert state.stack == []
        assert state.choice_points == []
        assert state.cut_barrier is None

    def test_push_goal(self):
        """Test pushing a goal frame."""
        state = ExecutionState()
        env = BindingEnvironment()
        goal = Atom("test")

        state.push_goal(goal, env)

        assert len(state.stack) == 1
        assert isinstance(state.stack[0], GoalFrame)
        assert state.stack[0].goal == goal
        assert state.stack[0].env == env

    def test_push_goal_sequence(self):
        """Test pushing a goal sequence frame."""
        state = ExecutionState()
        env = BindingEnvironment()
        goals = [Atom("a"), Atom("b"), Atom("c")]

        result = state.push_goal_sequence(goals, env)

        assert result is None  # Not empty sequence
        assert len(state.stack) == 1
        assert isinstance(state.stack[0], GoalSeqFrame)
        assert state.stack[0].goals == goals
        assert not state.stack[0].initialized

    def test_push_goal_sequence_empty(self):
        """Test pushing empty goal sequence returns env immediately."""
        state = ExecutionState()
        env = BindingEnvironment()
        goals = []

        result = state.push_goal_sequence(goals, env)

        assert result == env
        assert len(state.stack) == 0  # No frame pushed

    def test_push_choice_point(self):
        """Test recording a choice point."""
        state = ExecutionState()
        env = BindingEnvironment()

        # Push some frames first
        state.push_goal(Atom("a"), env)
        state.push_goal(Atom("b"), env)

        # Record choice point
        alternative = GoalFrame(env=env, goal=Atom("alt"))
        state.push_choice_point(alternative)

        assert len(state.choice_points) == 1
        assert state.choice_points[0].stack_depth == 2
        assert state.choice_points[0].alternative_frame == alternative

    def test_backtrack_success(self):
        """Test successful backtracking."""
        state = ExecutionState()
        env = BindingEnvironment()

        # Set up initial stack
        state.push_goal(Atom("a"), env)
        state.push_goal(Atom("b"), env)

        # Record choice point at depth 2
        alternative = GoalFrame(env=env, goal=Atom("alt"))
        state.push_choice_point(alternative)

        # Push more frames
        state.push_goal(Atom("c"), env)
        state.push_goal(Atom("d"), env)

        # Backtrack
        result = state.backtrack()

        assert result is True
        assert len(state.stack) == 3  # Restored to depth 2 + alternative
        assert state.stack[-1].goal == Atom("alt")
        assert len(state.choice_points) == 0  # Choice point consumed

    def test_backtrack_failure(self):
        """Test backtracking with no choice points."""
        state = ExecutionState()

        result = state.backtrack()

        assert result is False
        assert len(state.stack) == 0

    def test_apply_cut(self):
        """Test cut removes choice points above barrier."""
        state = ExecutionState()
        env = BindingEnvironment()

        # Create multiple choice points at different depths
        state.stack = [GoalFrame(env=env, goal=Atom("frame"))]

        cp1 = ChoicePoint(stack_depth=1, alternative_frame=GoalFrame(env=env, goal=Atom("alt1")))
        cp2 = ChoicePoint(stack_depth=3, alternative_frame=GoalFrame(env=env, goal=Atom("alt2")))
        cp3 = ChoicePoint(stack_depth=5, alternative_frame=GoalFrame(env=env, goal=Atom("alt3")))

        state.choice_points = [cp1, cp2, cp3]
        state.cut_barrier = 3

        state.apply_cut()

        # Only cp1 should remain (depth < 3)
        assert len(state.choice_points) == 1
        assert state.choice_points[0] == cp1

    def test_apply_cut_no_barrier(self):
        """Test cut does nothing when no barrier set."""
        state = ExecutionState()
        env = BindingEnvironment()

        cp1 = ChoicePoint(stack_depth=1, alternative_frame=GoalFrame(env=env, goal=Atom("alt1")))
        cp2 = ChoicePoint(stack_depth=3, alternative_frame=GoalFrame(env=env, goal=Atom("alt2")))

        state.choice_points = [cp1, cp2]
        state.cut_barrier = None

        state.apply_cut()

        # Nothing should change
        assert len(state.choice_points) == 2

    def test_repr(self):
        """Test string representation."""
        state = ExecutionState()
        env = BindingEnvironment()

        state.push_goal(Atom("a"), env)
        state.push_goal(Atom("b"), env)
        state.push_choice_point(GoalFrame(env=env, goal=Atom("alt")))
        state.cut_barrier = 2

        repr_str = repr(state)

        assert "ExecutionState" in repr_str
        assert "stack=2 frames" in repr_str
        assert "choice_points=1" in repr_str
        assert "cut_barrier=2" in repr_str


class TestFrameIntegration:
    """Integration tests for frame interactions."""

    def test_goal_seq_with_multiple_goals(self):
        """Test goal sequence frame with multiple goals."""
        env = BindingEnvironment()
        goals = [
            Atom("goal1"),
            Atom("goal2"),
            Atom("goal3"),
        ]

        frame = GoalSeqFrame(env=env, goals=goals)

        # V2: GoalSeqFrame requires interpreter for step()
        # Unit test without interpreter: verify initialization
        assert frame.goals == goals
        assert not frame.initialized
        assert frame.goal_stack == []

        # Simulate empty goals (completed)
        frame_empty = GoalSeqFrame(env=env, goals=[])
        result = frame_empty.step(None)  # type: ignore
        assert result == env

    def test_execution_state_complex_workflow(self):
        """Test complex execution state workflow."""
        state = ExecutionState()
        env = BindingEnvironment()

        # Push initial goal
        state.push_goal(Atom("start"), env)
        assert len(state.stack) == 1

        # Push goal sequence
        state.push_goal_sequence([Atom("a"), Atom("b")], env)
        assert len(state.stack) == 2

        # Record choice point
        alt = GoalFrame(env=env, goal=Atom("alternative"))
        state.push_choice_point(alt)
        assert len(state.choice_points) == 1

        # Push more goals
        state.push_goal(Atom("c"), env)
        state.push_goal(Atom("d"), env)
        assert len(state.stack) == 4

        # Backtrack to choice point
        result = state.backtrack()
        assert result is True
        assert len(state.stack) == 3  # Restored to choice point depth + alt
        assert state.stack[-1].goal == Atom("alternative")

        # No more choice points
        result = state.backtrack()
        assert result is False
