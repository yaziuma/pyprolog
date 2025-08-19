# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

PyProlog is a Prolog interpreter implemented in Python that supports Japanese variable names and includes comprehensive built-in predicates. The project uses `uv` for package management and provides both CLI and library interfaces.

## Development Commands

### Environment Setup
```bash
# Create and activate virtual environment
uv venv
source .venv/bin/activate  # macOS/Linux
# .\.venv\Scripts\activate  # Windows

# Install dependencies
uv sync

# Install development dependencies
uv add --dev ruff pytest pytest-cov
```

### Running the Interpreter
```bash
# Run CLI with a Prolog file
uvx python -m pyprolog.cli.prolog tests/data/puzzle1.prolog

# Or use the installed script
pyprolog tests/data/puzzle1.prolog
```

### Testing and Quality Assurance
```bash
# Run all tests with coverage
uvx pytest --cov=pyprolog tests

# Run specific test modules
uvx pytest tests/runtime/test_interpreter.py
uvx pytest tests/parser/test_parser.py

# Lint code
uvx ruff check .

# Format code
uvx ruff format .

# Auto-fix linting issues
uvx ruff check . --fix
```

## Architecture Overview

### Core Components

**Parser Layer** (`pyprolog/parser/`):
- `Scanner`: Tokenizes Prolog source code, handles Japanese characters
- `Parser`: Builds AST from tokens, supports operator precedence
- `Token`/`TokenType`: Token representation and classification

**Core Types** (`pyprolog/core/`):
- `Variable`, `Term`, `Rule`: Core Prolog data structures
- `BindingEnvironment`: Variable binding management
- Error classes: `InterpreterError`, `ScannerError`, `ParserError`

**Runtime System** (`pyprolog/runtime/`):
- `Runtime`: Main interpreter class with query execution
- `LogicInterpreter`: Unification and backtracking engine
- `MathInterpreter`: Arithmetic evaluation
- `builtins.py`: Built-in predicates (type testing, list ops, meta predicates)

**Utilities** (`pyprolog/util/`):
- `variable_mapper.py`: Japanese variable name mapping
- `logger.py`: Logging configuration

### Key Design Patterns

**Interpreter Pattern**: Each runtime component handles specific aspects of Prolog execution
**Visitor Pattern**: Parser traverses AST to build runtime structures  
**Generator Pattern**: Query execution yields solutions lazily for backtracking
**Strategy Pattern**: Different interpreters handle logic vs arithmetic evaluation

### Japanese Language Support

The interpreter supports Japanese variable names through `variable_mapper.py`:
- Maps Japanese characters to internal variable representations
- Preserves original names for user output
- Test files in `tests/japanese/` verify this functionality

### Built-in Predicates

Extensive built-in predicate library includes:
- Type testing: `var/1`, `atom/1`, `number/1`
- Term manipulation: `functor/3`, `arg/3`, `=../2` (univ)
- Dynamic predicates: `asserta/1`, `assertz/1`, `retract/1`
- List operations: `member/2`, `append/3`
- Meta predicates: `findall/3`
- I/O predicates: `get_char/1`, `write/1`, `nl/0`

### Error Handling

Comprehensive error system with specific exception types:
- Parse errors include token position information
- Runtime errors preserve stack context
- Cut exceptions handle Prolog cut semantics

## Testing Structure

Tests are organized by component:
- `tests/core/`: Core type and binding tests
- `tests/parser/`: Scanner and parser tests  
- `tests/runtime/`: Interpreter and built-in predicate tests
- `tests/japanese/`: Japanese language support tests
- `tests/integration/`: End-to-end functionality tests

Key test files:
- `test_enhanced_runtime.py`: Extended interpreter features
- `test_arithmetic_edge_cases.py`: Math operation boundary conditions
- `test_medical_diagnosis_jp.py`: Japanese language integration test

## Configuration

Logging configuration in `pyprolog/config/logging/`:
- `debug.conf`: Verbose logging for development
- `production.conf`: Minimal logging for production
- `test.conf`: Test-specific logging settings

## Package Structure

The project follows standard Python packaging:
- `pyproject.toml`: Project metadata, dependencies, and build configuration
- Package exports main classes through `__init__.py` files
- CLI entry point: `pyprolog.cli.prolog:main`
- Library usage: Import from `pyprolog` package

## Common Development Tasks

**Adding Built-in Predicates**: Extend `runtime/builtins.py` with new predicate classes
**Parser Extensions**: Modify `parser/parser.py` and update `token_type.py` for new syntax
**Runtime Features**: Add logic to `runtime/interpreter.py` or create specialized interpreters
**Japanese Support**: Update `util/variable_mapper.py` for new character mappings

## Sample Usage Patterns

The `sample_usage/` directory contains examples:
- `basic_usage.py`: Library usage patterns
- `arithmetic_sample.py`: Math operations
- Prolog files demonstrate various language features

## Known Limitations and Solutions

### Current Implementation Limits

Based on comprehensive analysis (see `docs/pyprolog_limitations_analysis.md`), PyProlog has the following known issues:

**Large Knowledge Base Handling**:
- Files with 75+ rules may experience performance degradation
- Complex nested structures in large KBs can cause goal execution failures
- Parse errors may occur with specific syntax patterns in large files

**Complex Unification Scenarios**:
- While basic unification works perfectly, some complex compound term assignments may fail in large KB contexts
- Variable scoping issues can occur with multiple predicates using similar variable names

### Working Patterns (Verified Functional)

✅ **Fully Functional**:
- Basic unification: `X = hello`, `Result = [a, b, c]`
- Simple rules: `rule(X) :- X = value`
- Built-in predicates: `write/1`, `member/2`, `append/3`, arithmetic operators
- Compound terms: `diagnosis(disease, probability)`
- List operations: `[H|T]` patterns, list concatenation
- Japanese variable names and Unicode support
- All 70 defined operators with proper precedence

✅ **Arithmetic and Logic**:
- All comparison operators: `=:=`, `=\=`, `<`, `=<`, `>`, `>=`
- Arithmetic evaluation: `is/2`, `+`, `-`, `*`, `/`, `mod`, `**`
- Type testing: `var/1`, `atom/1`, `number/1`

### Debugging Complex Issues

When encountering goal execution failures:

1. **Test in isolation**: Extract problematic predicates to separate files
2. **Enable debug logging**: Set logging level to DEBUG for detailed execution traces
3. **Check parse errors**: Look for "Parse error" messages in logs
4. **Simplify structures**: Break complex compound terms into simpler parts

### Performance Optimization Tips

- Keep KB files under 50 rules for optimal performance
- Use simple variable names to avoid scoping conflicts
- Test complex predicates incrementally
- Use the working English medical diagnosis examples in `tests/integration/` as templates