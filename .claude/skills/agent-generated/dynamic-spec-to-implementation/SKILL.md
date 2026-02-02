---
name: dynamic-spec-to-implementation
description: |
  Transform specification documents into actionable implementation plans and execute
  them systematically. This skill covers the full cycle from spec analysis, design
  consultation with Codex, creating detailed plans, and implementing features with
  iterative verification.
metadata:
  short-description: Spec → Design → Plan → Implementation workflow
  confidence: 0.9
---

# Dynamic Spec to Implementation

**Systematic workflow for converting specifications into working implementations.**

## Purpose

When given a specification document (technical spec, feature requirement, design doc),
this skill guides you through:

1. Analyzing the specification thoroughly
2. Consulting Codex for design decisions
3. Creating a detailed implementation plan
4. Executing the plan with verification steps
5. Handling implementation issues iteratively

This prevents ad-hoc implementation and ensures alignment with requirements.

## When to Activate

### Trigger Phrases (Japanese)

- 「仕様から実装して」
- 「この仕様書を実装する」
- 「スペックに基づいて作る」
- 「仕様を実装計画に落とし込む」
- 「設計から実装まで進めて」

### Trigger Phrases (English)

- "Implement based on this spec"
- "Build from specification"
- "Spec to implementation"
- "Follow this design document"
- "Create implementation plan from spec"

### Scenarios

- User provides a markdown spec document (e.g., `docs/design/*.md`)
- Feature requests with clear requirements
- Technical design documents need implementation
- Multi-step features requiring systematic approach

## Workflow

### Phase 1: Specification Analysis

1. **Read the spec document** thoroughly
   - Extract requirements, constraints, architecture
   - Identify affected components and files
   - Note open questions or ambiguities

2. **Consult Codex for design validation**
   ```bash
   codex exec --model gpt-5.2-codex --sandbox read-only --full-auto "
   Review this specification for implementation:

   {spec content or summary}

   Evaluate:
   1. Is the design sound?
   2. Implementation approach recommendations?
   3. Potential pitfalls?
   4. Alternative approaches?
   " 2>/dev/null
   ```

3. **Create implementation plan document**
   - Save to `.claude/docs/design/implementation-plan-{feature}.md`
   - Include: purpose, scope, files, steps, risks

### Phase 2: Design Decisions

1. **Break down into implementable tasks**
   - Each task is independently testable
   - Order by dependencies
   - Identify high-risk tasks first

2. **For each complex design decision**, consult Codex:
   ```bash
   codex exec --model gpt-5.2-codex --sandbox read-only --full-auto "
   Design decision needed for: {specific aspect}

   Context: {relevant info}
   Options: {list alternatives}

   Recommend best approach and explain trade-offs.
   " 2>/dev/null
   ```

3. **Document decisions** in implementation plan

### Phase 3: Implementation

1. **Execute plan step-by-step**
   - Implement one task at a time
   - Run tests after each task
   - Commit after each verified step

2. **For implementation issues**:
   - First attempt to debug
   - If not obvious, consult Codex:
     ```bash
     codex exec --model gpt-5.2-codex --sandbox read-only --full-auto "
     Debug issue during implementation:

     Task: {what was being implemented}
     Error: {error message}
     Code: {relevant code}

     Analyze root cause and suggest fix.
     " 2>/dev/null
     ```

3. **Verify each step**
   - Unit tests pass
   - Integration tests pass
   - Manual verification if needed

### Phase 4: Iteration

1. **Review implementation against spec**
2. **Run full test suite**: `uv run pytest`
3. **Update documentation** if needed
4. **Create PR** with summary of changes

## Files Involved

### Input Files
- `docs/design/*.md` - Specification documents
- `docs/dynamic_directive/*.md` - Feature specifications
- `.claude/docs/design/*.md` - Internal design docs

### Output Files
- `.claude/docs/design/implementation-plan-*.md` - Implementation plans
- Source files modified per plan
- Test files created/updated

### Evidence Files (from project history)
- `docs/dynamic_directive/dynamic_directive_spec_and_plan.md`
- Dynamic directive implementation (commits: a2feddc, f93c097)
- RecursionError fix following analysis (commit: 9550478)

## Evidence

### Why This Is a Reusable Pattern

**From project git history:**

1. **Dynamic directive feature** (PRs #21, #22):
   - Started with spec: `dynamic_directive_spec_and_plan.md`
   - Created implementation plan: `dynamic_directive_implementation_plan`
   - Consulted Codex multiple times for design decisions
   - Implemented with two-registry approach (commit: b9c0b85)
   - Result: Feature delivered matching specification

2. **RecursionError fix** (commit: 9550478):
   - Analysis document created first
   - Codex consultation for design review
   - Iterative implementation with occurs_check refactoring
   - Verification through benchmark tests

3. **Pattern characteristics**:
   - **Confidence score: 0.9** (high success rate)
   - Used for 2+ major features in recent history
   - Clear documentation trail
   - Systematic approach reduces implementation errors
   - Codex consultation at decision points improves quality

### Success Indicators

- Features implemented match specifications
- Fewer back-and-forth revisions
- Clear audit trail from spec to code
- Reduced debugging time through design validation
- Systematic approach catches edge cases early

## Integration with Other Skills

- **codex-system**: Used throughout for design validation
- **plan**: Creates the implementation plan document
- **tdd**: Test-first approach during implementation
- **design-tracker**: Updates design decisions

## Notes

- Always read spec thoroughly before starting
- Don't skip Codex consultation for complex decisions
- Keep implementation plan updated as you progress
- Commit frequently with clear messages
- Link commits/PRs back to original spec document
