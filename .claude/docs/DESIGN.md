# Project Design Document

> This document tracks design decisions made during conversations.
> Updated automatically by the `design-tracker` skill.

## Overview

pyprologは日本語変数名サポートと高度な開発ツールを備えたPython実装のPrologインタプリタです。

現在、Dynamic Directive機能の実装を進めています。この機能により、述語の動的宣言と存在判定の意味論を明確化します。

## Architecture

### Dynamic Directive System

**2レジストリアーキテクチャ**:

```
LogicInterpreter
├── dynamic_registry: Set[(name, arity)]
│   └── Purpose: Track declared predicates (persistent)
└── defined_registry: Set[(name, arity)]
    └── Purpose: Track currently defined predicates (removed on retract)

Parser
└── directives: List[(type, name, arity)]
    └── Purpose: Store parsed directives for later application

Data Flow:
1. Parser.parse() → captures :- dynamic(p/1) → stores in directives
2. Runtime.consult() → applies directives first → then adds rules
3. add_rule() → updates defined_registry
4. remove_rule() → removes from defined_registry when last clause deleted
5. solve_goal() → checks both registries for existence
```

## Implementation Plan

### Patterns & Approaches

<!-- Design patterns, architectural approaches -->

| Pattern | Purpose | Notes |
|---------|---------|-------|
| | | |

### Libraries & Roles

<!-- Libraries and their responsibilities -->

| Library | Role | Version | Notes |
|---------|------|---------|-------|
| | | | |

### Key Decisions

<!-- Important decisions and their rationale -->

| Decision | Rationale | Alternatives Considered | Date |
|----------|-----------|------------------------|------|
| Syntax: `:- dynamic(p/1).` (with parentheses) | Current parser can handle this format as `dynamic` functor with `p/1` arg. Bracket-less syntax would require directive-specific parser. | `:- dynamic p/1.` (rejected: parser incompatibility) | 2026-02-02 |
| Two-registry approach (dynamic_registry + defined_registry) | Separates declaration from definition. Enables clear semantics: declared predicates fail when empty, undeclared predicates error when empty. Prevents semantic ambiguity where non-declared predicates would persist after retract. | Single persistent registry (rejected: semantic ambiguity) | 2026-02-02 |
| Existence check: `if key not in (defined ∪ dynamic)` | Guards against undefined predicates while allowing declared-but-empty predicates to fail gracefully. | Registry-only check (rejected: doesn't handle undeclared predicates correctly) | 2026-02-02 |
| defined_registry removed on retract (last clause) | Reflects actual state: predicate has no clauses. Without removal, retracted undeclared predicates would incorrectly fail instead of error. | Never remove from defined_registry (rejected: breaks undeclared semantics) | 2026-02-02 |

## TODO

<!-- Features to implement -->

- [ ] 

## Open Questions

<!-- Unresolved issues, things to investigate -->

- [ ] 

## Changelog

| Date | Changes |
|------|---------|
| 2026-02-02 | Added Dynamic Directive v2 design: two-registry approach, parenthesized syntax `:- dynamic(p/1).`, clear existence semantics |
| | Initial |
