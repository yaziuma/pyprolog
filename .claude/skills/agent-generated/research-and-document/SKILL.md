---
name: research-and-document
description: |
  Systematic research workflow using Gemini for investigation, analysis, and
  documentation. Gather information, analyze findings, document results, and
  integrate insights into project knowledge base. Preserves research trails
  for future reference and decision-making.
metadata:
  short-description: Research → Analyze → Document → Integrate workflow
  confidence: 0.8
---

# Research and Document

**Systematic research workflow with Gemini as research specialist.**

> **詳細ルール**: `.claude/rules/gemini-delegation.md`

## Purpose

When facing unknown territories (new libraries, unfamiliar codebases, architectural
decisions requiring context), this skill provides a structured approach:

1. **Research Phase**: Use Gemini to gather comprehensive information
2. **Analysis Phase**: Process and synthesize findings
3. **Documentation Phase**: Create permanent knowledge artifacts
4. **Integration Phase**: Apply insights to project

This prevents repeated research and builds institutional knowledge.

## When to Activate

### Trigger Phrases (Japanese)

- 「調べて」「リサーチして」「調査して」
- 「〜について情報を集めて」
- 「コードベース全体を理解して」
- 「最新のドキュメントを確認して」
- 「このPDF/動画/音声を分析して」
- 「ライブラリを比較して」

### Trigger Phrases (English)

- "Research" "Investigate" "Look up"
- "Gather information about X"
- "Understand the codebase"
- "Check the latest documentation"
- "Analyze this PDF/video/audio"
- "Compare libraries"
- "What are best practices for X"

### Scenarios

- Pre-implementation research (library selection, architecture patterns)
- Understanding large/unfamiliar codebases
- Investigating errors or unexpected behavior
- Analyzing multimodal content (PDFs, videos, audio)
- Latest documentation/best practices lookup
- Technical feasibility research

## Workflow

### Phase 1: Research Scoping

1. **Define research question clearly**
   - What do you need to know?
   - Why do you need to know it?
   - What decisions depend on this research?

2. **Determine research type**:
   - **General research**: Best practices, library comparison
   - **Codebase analysis**: Repository-wide understanding
   - **Documentation lookup**: Latest official docs
   - **Multimodal**: PDF/video/audio analysis

3. **Choose appropriate Gemini command**:
   ```bash
   # General research
   gemini -p "{research question}" 2>/dev/null

   # Codebase analysis
   gemini -p "{question}" --include-directories . 2>/dev/null

   # Multimodal
   gemini -p "{extraction prompt}" < /path/to/file 2>/dev/null
   ```

### Phase 2: Execute Research (via Subagent)

**IMPORTANT: Use subagent to preserve main context.**

Use Task tool with `subagent_type='general-purpose'`:

```
Task tool parameters:
- subagent_type: "general-purpose"
- run_in_background: true
- prompt: |
    Research: {topic}

    1. Call Gemini CLI:
       gemini -p "{detailed research question in English}" 2>/dev/null

    2. Save full output to: .claude/docs/research/{topic}.md

    3. Return CONCISE summary (5-7 bullet points):
       - Key findings
       - Recommended approach
       - Important caveats
       - Links/references if provided
```

**Why subagent?**
- Preserves main orchestrator context
- Can save full Gemini output (often large)
- Returns only essential summary to main

### Phase 3: Analysis and Synthesis

1. **Review subagent summary**
   - Identify actionable insights
   - Note areas needing clarification
   - Highlight decision-critical information

2. **If more depth needed**, spawn additional subagent:
   ```
   Follow-up research on: {specific aspect}

   gemini -p "{focused question}" 2>/dev/null

   Append findings to .claude/docs/research/{topic}.md
   ```

3. **Cross-reference with existing knowledge**
   - Check `.claude/docs/` for related research
   - Identify conflicts or confirmations
   - Update understanding

### Phase 4: Documentation

1. **Create permanent research document**:
   ```
   .claude/docs/research/{topic}-YYYYMMDD.md
   ```

   **Structure**:
   ```markdown
   # Research: {Topic}

   **Date**: {YYYY-MM-DD}
   **Researcher**: {Gemini via Claude Code}
   **Purpose**: {Why this research was needed}

   ## Research Question

   {Clear statement of what was investigated}

   ## Key Findings

   {Bullet points of main discoveries}

   ## Recommended Approach

   {Actionable recommendations}

   ## Trade-offs and Caveats

   {Important considerations}

   ## References

   {Links, documentation, sources}

   ## Integration Notes

   {How this affects current project}

   ## Open Questions

   {What still needs investigation}
   ```

2. **Update project documentation if needed**:
   - Add to `CLAUDE.md` if workflow-relevant
   - Update library docs in `.claude/docs/libraries/`
   - Note in design docs if affecting architecture

3. **Create decision record if applicable**:
   - Use `design-tracker` skill for architecture decisions
   - Document: decision, context, alternatives, rationale

### Phase 5: Integration and Action

1. **Apply research findings**:
   - Update implementation plans
   - Inform design decisions
   - Guide library selection

2. **If research leads to Codex consultation**:
   ```
   Research complete. Now consult Codex for design decision:

   codex exec --model gpt-5.2-codex --sandbox read-only --full-auto "
   Based on research findings:
   {summary from Gemini}

   Design decision needed:
   {specific decision}

   Recommend approach considering trade-offs.
   " 2>/dev/null
   ```

3. **Update task context** with research insights

## Files Involved

### Research Output Files
- `.claude/docs/research/{topic}-{date}.md` - Main research documents
- `.claude/docs/research/codebase-analysis-*.md` - Codebase understanding
- `.claude/docs/research/library-comparison-*.md` - Library evaluations

### Integration Files
- `.claude/docs/libraries/*.md` - Library documentation updates
- `.claude/docs/design/*.md` - Design decisions informed by research
- `CLAUDE.md` - Project-level guidance updates

### Evidence Files (from project history)
- `.claude/docs/research/recursion-error-analysis.md` - Error investigation
- Dynamic directive investigation docs (multiple versions)
- Codex investigation results from PRs #17-#19

## Evidence

### Why This Is a Reusable Pattern

**From project git history:**

1. **Dynamic directive investigation**:
   - Multiple research iterations (PRs #17-#19)
   - Created investigation documents
   - Codex consultations for Prolog-specific questions
   - Results informed specification and implementation
   - **Pattern**: Research → Document → Design → Implement

2. **RecursionError investigation**:
   - Created: `recursion-error-analysis.md`
   - Researched occurs_check implementations
   - Documented findings and Codex review
   - Led to successful refactoring (commit: 9550478)
   - **Pattern**: Error → Research → Analysis → Fix

3. **Pattern characteristics**:
   - **Confidence score: 0.8** (effective but context-dependent)
   - Used for complex investigations
   - Creates knowledge artifacts for future reference
   - Prevents repeated research on same topics
   - Enables better decision-making through comprehensive information

### Success Indicators

- Research documents referenced in later work
- Faster decision-making due to documented findings
- Fewer "we already researched this" situations
- Clear rationale trail for project decisions
- Team members can onboard faster with research docs

## Integration with Other Skills

- **gemini-system**: Core research tool
- **codex-system**: Post-research design decisions
- **design-tracker**: Record decisions informed by research
- **dynamic-spec-to-implementation**: Research informs specification
- **codex-design-implement-cycle**: Research precedes design phase

## Gemini vs Codex: Choose the Right Tool

| Task | Gemini | Codex |
|------|--------|-------|
| Library research | ✓ | |
| Latest documentation | ✓ | |
| Codebase understanding | ✓ | |
| Best practices (2026) | ✓ | |
| Video/Audio/PDF | ✓ | |
| Design decisions | | ✓ |
| Debugging | | ✓ |
| Code implementation | | ✓ |

**Workflow**: Gemini (research) → Codex (design decision) → Implementation

## Best Practices

### Do
- Use subagent for Gemini consultations (preserves main context)
- Ask Gemini in English (better results)
- Save full Gemini output to files (large, preserve for reference)
- Return only summary to main orchestrator
- Create dated research documents
- Cross-reference with existing research
- Link research to resulting decisions

### Don't
- Call Gemini directly in main for large research (consumes context)
- Skip documentation step (lose research value)
- Research what you already know (check `.claude/docs/` first)
- Use Gemini for design decisions (use Codex instead)
- Forget to integrate findings into project

## Quick Reference

### Research Type Decision Tree

```
Need information?
├─ About design/implementation approach? → Codex
├─ About library/best practices? → Gemini
├─ About this codebase? → Gemini (codebase analysis)
├─ From PDF/video/audio? → Gemini (multimodal)
└─ Latest docs/breaking changes? → Gemini (search grounding)
```

### Subagent Pattern Template

```
Task tool:
- subagent_type: "general-purpose"
- run_in_background: true
- prompt: |
    Research: {topic}

    gemini -p "Research question in English" 2>/dev/null

    Save to .claude/docs/research/{topic}.md
    Return 5-7 key bullet points.
```

### File Naming Convention

- `research/{topic}-{YYYYMMDD}.md` - General research
- `research/lib-{library-name}-{YYYYMMDD}.md` - Library research
- `research/codebase-analysis-{YYYYMMDD}.md` - Codebase understanding
- `research/{error-type}-analysis-{YYYYMMDD}.md` - Error investigation

## Notes

- Gemini has 1M token context window (can analyze entire repos)
- Always use subagent for large research (context preservation)
- Research documents are valuable project assets (maintain quality)
- Link research to decisions (creates audit trail)
- Update research when information becomes outdated
- Consider using `gemini-system` skill for structured research workflow
