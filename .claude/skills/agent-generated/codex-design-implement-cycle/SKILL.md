---
name: codex-design-implement-cycle
description: |
  Iterative design and implementation workflow using Codex as design partner.
  Consult Codex for design decisions, implement incrementally, get feedback,
  and refine. This creates a tight feedback loop between design thinking and
  practical implementation.
metadata:
  short-description: Design → Implement → Review → Refine with Codex
  confidence: 0.85
---

# Codex Design-Implement Cycle

**Iterative workflow with Codex as your design and review partner.**

## Purpose

For complex features or refactorings, this skill provides a systematic cycle:

1. **Design Phase**: Consult Codex for architecture/approach
2. **Implementation Phase**: Build incrementally
3. **Review Phase**: Get Codex feedback on implementation
4. **Refinement Phase**: Apply improvements and iterate

This prevents over-engineering and catches design issues early through
continuous feedback loops.

## When to Activate

### Trigger Phrases (Japanese)

- 「設計から実装まで反復的に進めて」
- 「Codexと相談しながら実装」
- 「設計レビューを繰り返す」
- 「段階的に実装してレビュー」
- 「Codexとペアプロで進める」

### Trigger Phrases (English)

- "Design and implement iteratively with Codex"
- "Pair program with Codex"
- "Iterative design and implementation"
- "Build with design reviews"
- "Incremental implementation with feedback"

### Scenarios

- Complex feature requiring multiple design decisions
- Large refactoring with architectural implications
- Uncertain about best implementation approach
- Need to explore trade-offs between alternatives
- High-risk changes requiring validation

## Workflow

### Cycle 1: Initial Design

1. **Define the problem clearly**
   - What needs to be built/refactored?
   - What are the constraints?
   - What are success criteria?

2. **Consult Codex for design approach** (via subagent recommended):
   ```bash
   codex exec --model gpt-5.2-codex --sandbox read-only --full-auto "
   Design approach for: {feature/refactoring}

   Requirements:
   {list requirements}

   Constraints:
   {list constraints}

   Propose:
   1. High-level architecture
   2. Component breakdown
   3. Interface designs
   4. Implementation approach
   5. Potential risks
   " 2>/dev/null
   ```

3. **Document initial design**
   - Save to `.claude/docs/design/{feature}-design-v1.md`
   - Include Codex recommendations and rationale

### Cycle 2: First Implementation

1. **Implement minimal viable version**
   - Focus on core functionality
   - Keep it simple
   - Make it testable

2. **Write tests first** (TDD):
   ```bash
   uv run pytest tests/test_{feature}.py -v
   ```

3. **Commit initial version**:
   ```bash
   git add {files}
   git commit -m "feat: Initial implementation of {feature}"
   ```

### Cycle 3: Review and Feedback

1. **Get Codex code review** (via subagent recommended):
   ```bash
   codex exec --model gpt-5.2-codex --sandbox read-only --full-auto "
   Review this implementation:

   {code or file paths}

   Evaluate:
   1. Does it match design intent?
   2. Code quality issues?
   3. Potential bugs or edge cases?
   4. Performance concerns?
   5. Suggested improvements?
   " 2>/dev/null
   ```

2. **Document review findings**
   - Add to design doc or create review notes
   - Prioritize feedback items

3. **Identify next iteration focus**
   - Critical issues first
   - Then improvements
   - Then optimizations

### Cycle 4: Refinement

1. **Apply feedback incrementally**
   - One improvement at a time
   - Test after each change
   - Commit each logical change

2. **For complex refactorings**, consult Codex again:
   ```bash
   codex exec --model gpt-5.2-codex --sandbox read-only --full-auto "
   Refactoring guidance needed:

   Current implementation: {description}
   Issue to address: {specific issue from review}

   How should I refactor this? Provide step-by-step approach.
   " 2>/dev/null
   ```

3. **Verify improvements**:
   ```bash
   uv run pytest --cov={module} -v
   uv run ruff check .
   ```

### Cycle 5: Iterate

1. **Repeat cycles 3-4** until:
   - All critical issues addressed
   - Code meets quality standards
   - Tests pass and coverage is adequate
   - Performance is acceptable

2. **Final review with Codex**:
   ```bash
   codex exec --model gpt-5.2-codex --sandbox read-only --full-auto "
   Final review of {feature} implementation.

   Changes made: {summary}
   Tests: {test coverage info}

   Is this ready for production? Any remaining concerns?
   " 2>/dev/null
   ```

3. **Document final design**
   - Update design doc with actual implementation
   - Note deviations from initial design and why
   - Record lessons learned

## Files Involved

### Design Documents
- `.claude/docs/design/{feature}-design-v*.md` - Evolving design docs
- `.claude/docs/research/{topic}.md` - Research notes from Codex
- Design decision records

### Implementation Files
- Source files being developed/refactored
- Test files (TDD)
- Configuration files if needed

### Evidence Files (from project history)
- Dynamic directive investigation cycle (PRs #17, #18, #19, #20)
  - Multiple Codex consultations
  - Iterative spec refinement
  - Design evolved through feedback
- RecursionError analysis and fix (commit: 9550478)
  - Analysis → Codex review → Implementation → Verification

## Evidence

### Why This Is a Reusable Pattern

**From project git history:**

1. **Dynamic directive feature development**:
   - **Investigation phase** (PRs #17-#19):
     - Multiple Codex consultations: `investigate-codex-dynamic-declaration`
     - Created: `dynamic_directive_investigation.md`
     - Revised design based on feedback
   - **Specification phase** (PR #20):
     - Reevaluated registry placement
     - Spec review with Codex
   - **Implementation phase** (PRs #21-#22):
     - Created detailed plan
     - Implemented with two-registry approach
     - Merged successfully
   - **Pattern**: 6+ iterations from investigation to implementation

2. **RecursionError resolution**:
   - Analysis document created
   - Codex review of analysis
   - Iterative implementation (occurs_check refactoring)
   - Verification through benchmarks
   - **Pattern**: Design → Review → Implement → Verify

3. **Pattern characteristics**:
   - **Confidence score: 0.85** (proven effective)
   - Used across multiple feature types
   - Reduces implementation errors through early design validation
   - Catches issues before they become technical debt
   - Creates clear documentation trail

### Success Indicators

- Features require fewer post-merge fixes
- Design issues caught early in cycle
- Clear rationale for implementation decisions
- Better code quality from iterative refinement
- Team members can understand design evolution

## Integration with Other Skills

- **codex-system**: Core dependency for consultations
- **dynamic-spec-to-implementation**: Can be used within this cycle
- **tdd**: Test-first approach in implementation phase
- **design-tracker**: Record design decisions at each cycle
- **simplify**: Use Codex for simplification guidance

## Best Practices

### Do
- Keep cycles short (hours, not days)
- Commit after each verified improvement
- Document Codex feedback and how you addressed it
- Use subagent for Codex consultations to preserve main context
- Ask specific questions to Codex (not vague "review this")

### Don't
- Skip early design consultation (catches issues early)
- Implement everything before first review (too late for big changes)
- Ignore Codex feedback without documented reason
- Over-iterate on minor issues (diminishing returns)
- Forget to update design docs with actual implementation

## Quick Reference

### Phase Checklist

- [ ] Phase 1: Codex design consultation
- [ ] Phase 2: Minimal implementation + tests
- [ ] Phase 3: Codex code review
- [ ] Phase 4: Apply critical feedback
- [ ] Phase 5: Iterate until quality bar met
- [ ] Final: Update documentation

### When to Move to Next Cycle

| Current Phase | Move to Next When... |
|---------------|---------------------|
| Design | Have clear architectural approach |
| Implementation | Core functionality works with tests |
| Review | Have prioritized feedback list |
| Refinement | Critical issues addressed |
| Iteration | Quality standards met |

## Notes

- This cycle works best for medium-to-large features (> 200 lines)
- For small changes (< 50 lines), simpler workflows may be more efficient
- Use subagent pattern for Codex consultations to preserve main context
- Balance iteration with progress (don't over-optimize)
- Document the "why" behind design decisions, not just the "what"
