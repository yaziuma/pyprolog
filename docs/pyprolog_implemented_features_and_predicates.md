# PyProlog Implemented Features and Predicates List

## Overview

This document provides a detailed list of implemented features and predicates in the pyprolog project. PyProlog is a simple Prolog interpreter implemented in Python.

## Table of Contents

1. [Core Components](#core-components)
2. [Data Types](#data-types)
3. [Built-in Predicates](#built-in-predicates)
4. [Operators](#operators)
5. [Parser Features](#parser-features)
6. [Runtime Features](#runtime-features)
7. [I/O Features](#io-features)
8. [Usage Examples](#usage-examples)

## Core Components

### Main Classes

- **[`Runtime`](../pyprolog/runtime/interpreter.py:32)** - Main interpreter class
- **[`Parser`](../pyprolog/parser/parser.py)** - Prolog code parser
- **[`Scanner`](../pyprolog/parser/scanner.py)** - Lexical analyzer
- **[`LogicInterpreter`](../pyprolog/runtime/logic_interpreter.py)** - Logic inference engine
- **[`MathInterpreter`](../pyprolog/runtime/math_interpreter.py:12)** - Arithmetic evaluation engine

### Error Handling

- **[`PrologError`](../pyprolog/core/errors.py)** - Base exception class
- **[`InterpreterError`](../pyprolog/core/errors.py)** - Interpreter error
- **[`ScannerError`](../pyprolog/core/errors.py)** - Lexical analysis error
- **[`ParserError`](../pyprolog/core/errors.py)** - Parse error
- **[`CutException`](../pyprolog/core/errors.py)** - Cut exception

## Data Types

### Basic Data Types

| Type     | Class                                       | Description                                          |
| -------- | ------------------------------------------- | ---------------------------------------------------- | ---- |
| Atom     | [`Atom`](../pyprolog/core/types.py:16)      | String constants (e.g., `hello`, `world`)            |
| Variable | [`Variable`](../pyprolog/core/types.py:30)  | Logic variables (e.g., `X`, `Y`, `_Var`)             |
| Number   | [`Number`](../pyprolog/core/types.py:44)    | Integers and floats (e.g., `42`, `3.14`)             |
| String   | [`String`](../pyprolog/core/types.py:58)    | String literals (e.g., `'hello'`)                    |
| Term     | [`Term`](../pyprolog/core/types.py:72)      | Compound terms (e.g., `f(a, b)`, `person(john, 25)`) |
| List     | [`ListTerm`](../pyprolog/core/types.py:102) | List structures (e.g., `[1, 2, 3]`, `[H              | T]`) |

### Logic Structures

| Type | Class                                   | Description                                       |
| ---- | --------------------------------------- | ------------------------------------------------- |
| Fact | [`Fact`](../pyprolog/core/types.py:174) | Simple facts (e.g., `likes(mary, wine).`)         |
| Rule | [`Rule`](../pyprolog/core/types.py:155) | Logic rules (e.g., `happy(X) :- likes(X, wine).`) |

## Built-in Predicates

### Type Testing Predicates

| Predicate  | Arity | Implementation Class                                    | Description                    |
| ---------- | ----- | ------------------------------------------------------- | ------------------------------ |
| `var/1`    | 1     | [`VarPredicate`](../pyprolog/runtime/builtins.py:26)    | Test if argument is a variable |
| `atom/1`   | 1     | [`AtomPredicate`](../pyprolog/runtime/builtins.py:38)   | Test if argument is an atom    |
| `number/1` | 1     | [`NumberPredicate`](../pyprolog/runtime/builtins.py:50) | Test if argument is a number   |

### Term Manipulation Predicates

| Predicate   | Arity | Implementation Class                                     | Description                                  |
| ----------- | ----- | -------------------------------------------------------- | -------------------------------------------- |
| `functor/3` | 3     | [`FunctorPredicate`](../pyprolog/runtime/builtins.py:62) | Get/construct functor and arity of a term    |
| `arg/3`     | 3     | [`ArgPredicate`](../pyprolog/runtime/builtins.py:146)    | Get argument at specified position in a term |
| `=../2`     | 2     | [`UnivPredicate`](../pyprolog/runtime/builtins.py:179)   | Convert between term and list (univ)         |

### Dynamic Predicate Manipulation

| Predicate   | Arity | Implementation Class                                             | Description                               |
| ----------- | ----- | ---------------------------------------------------------------- | ----------------------------------------- |
| `asserta/1` | 1     | [`DynamicAssertAPredicate`](../pyprolog/runtime/builtins.py:283) | Add clause to beginning of knowledge base |
| `assertz/1` | 1     | [`DynamicAssertZPredicate`](../pyprolog/runtime/builtins.py:373) | Add clause to end of knowledge base       |
| `retract/1` | 1     | [`DynamicRetractPredicate`](../pyprolog/runtime/builtins.py:724) | Remove clause from knowledge base         |

### List Operation Predicates

| Predicate  | Arity | Implementation Class                                     | Description          |
| ---------- | ----- | -------------------------------------------------------- | -------------------- |
| `member/2` | 2     | [`MemberPredicate`](../pyprolog/runtime/builtins.py:463) | List membership test |
| `append/3` | 3     | [`AppendPredicate`](../pyprolog/runtime/builtins.py:491) | List concatenation   |

### Meta Predicates

| Predicate   | Arity | Implementation Class                                      | Description                                    |
| ----------- | ----- | --------------------------------------------------------- | ---------------------------------------------- |
| `findall/3` | 3     | [`FindallPredicate`](../pyprolog/runtime/builtins.py:556) | Collect all solutions (simplified bagof/setof) |

### I/O Predicates

| Predicate    | Arity | Implementation Class                                      | Description                                  |
| ------------ | ----- | --------------------------------------------------------- | -------------------------------------------- |
| `get_char/1` | 1     | [`GetCharPredicate`](../pyprolog/runtime/builtins.py:659) | Read one character from current input stream |

## Operators

### Arithmetic Operators

| Operator | Arity | Precedence | Associativity | Description      |
| -------- | ----- | ---------- | ------------- | ---------------- |
| `**`     | 2     | 200        | Right         | Exponentiation   |
| `-`      | 1     | 200        | None          | Unary minus      |
| `+`      | 1     | 200        | None          | Unary plus       |
| `*`      | 2     | 400        | Left          | Multiplication   |
| `/`      | 2     | 400        | Left          | Division         |
| `//`     | 2     | 400        | Left          | Integer division |
| `mod`    | 2     | 400        | Left          | Modulo           |
| `+`      | 2     | 500        | Left          | Addition         |
| `-`      | 2     | 500        | Left          | Subtraction      |

### Comparison Operators

| Operator | Arity | Precedence | Description           |
| -------- | ----- | ---------- | --------------------- |
| `=:=`    | 2     | 700        | Arithmetic equality   |
| `=\\=`   | 2     | 700        | Arithmetic inequality |
| `<`      | 2     | 700        | Less than             |
| `=<`     | 2     | 700        | Less than or equal    |
| `>`      | 2     | 700        | Greater than          |
| `>=`     | 2     | 700        | Greater than or equal |

### Logic Operators

| Operator | Arity | Precedence | Description                           |
| -------- | ----- | ---------- | ------------------------------------- |
| `=`      | 2     | 700        | Unification                           |
| `\\=`    | 2     | 700        | Unification failure                   |
| `==`     | 2     | 700        | Term equality                         |
| `\\==`   | 2     | 700        | Term inequality                       |
| `is`     | 2     | 700        | Arithmetic evaluation and unification |

### Control Operators

| Operator | Arity | Precedence | Description       |
| -------- | ----- | ---------- | ----------------- |
| `!`      | 0     | 1200       | Cut               |
| `->`     | 2     | 1050       | If-then           |
| `;`      | 2     | 1100       | OR (disjunction)  |
| `,`      | 2     | 1000       | AND (conjunction) |

### I/O Operators

| Operator | Arity | Description   |
| -------- | ----- | ------------- |
| `write`  | 1     | Write term    |
| `nl`     | 0     | Write newline |

## Parser Features

### Supported Syntax Elements

- **Atoms**: Identifiers starting with lowercase, quoted strings
- **Variables**: Identifiers starting with uppercase or `_`
- **Numbers**: Integers, floating-point numbers
- **Compound terms**: `functor(arg1, arg2, ...)`
- **Lists**: `[element1, element2, ...]`, `[Head|Tail]`
- **Operators**: Infix, prefix, postfix operators
- **Comments**: `%` line comments, `/* */` block comments

### Token Types

Defined token types are enumerated in [`TokenType`](../pyprolog/parser/token_type.py).

## Runtime Features

### Main Methods

| Method                                                                    | Description                                          |
| ------------------------------------------------------------------------- | ---------------------------------------------------- |
| [`Runtime.query(query_string)`](../pyprolog/runtime/interpreter.py:514)   | Execute query string and return list of solutions    |
| [`Runtime.add_rule(rule_string)`](../pyprolog/runtime/interpreter.py:610) | Add rule string to knowledge base                    |
| [`Runtime.consult(filename)`](../pyprolog/runtime/interpreter.py:636)     | Load Prolog file                                     |
| [`Runtime.execute(goal, env)`](../pyprolog/runtime/interpreter.py:317)    | Execute goal with environment and generate solutions |

### Unification Algorithm

Unification functionality implemented in [`LogicInterpreter`](../pyprolog/runtime/logic_interpreter.py) class:

- Variable and term unification
- Compound term unification
- Occurs check to prevent infinite loops

### Backtracking

- Choice point management
- Solution search order control
- Search pruning with cut

## I/O Features

### IOManager

[`IOManager`](../pyprolog/runtime/io_manager.py) class manages input/output:

- Standard input/output
- File I/O
- Stream management

### Supported Features

- Character-level input
- Term output
- Newline control

## Usage Examples

### Basic Usage

```python
from pyprolog import Runtime

# Initialize runtime
runtime = Runtime()

# Add facts
runtime.add_rule("likes(mary, wine).")
runtime.add_rule("likes(john, wine).")

# Add rules
runtime.add_rule("happy(X) :- likes(X, wine).")

# Execute query
results = runtime.query("happy(X)")
for result in results:
    print(f"X = {result['X']}")
```

### Arithmetic Operations

```python
# Arithmetic calculation
results = runtime.query("X is 3 + 4 * 2")
print(f"X = {results[0]['X']}")  # X = 11

# Comparison operation
results = runtime.query("5 > 3")
print(f"Success: {len(results) > 0}")  # Success: True
```

### List Operations

```python
# member predicate
results = runtime.query("member(X, [1, 2, 3])")
for result in results:
    print(f"X = {result['X']}")  # X = 1, X = 2, X = 3

# append predicate
results = runtime.query("append([1, 2], [3, 4], L)")
print(f"L = {results[0]['L']}")  # L = [1, 2, 3, 4]
```

## Test Specifications

### Test Coverage

PyProlog provides comprehensive tests in the following areas:

- **Core features**: [`tests/core/`](../tests/core/)
- **Parser**: [`tests/parser/`](../tests/parser/)
- **Runtime**: [`tests/runtime/`](../tests/runtime/)
- **Integration tests**: [`tests/integration/`](../tests/integration/)

### Major Test Cases

- Arithmetic operation boundary tests
- Comprehensive list operation tests
- Dynamic predicate manipulation tests
- Unification algorithm tests
- Recursive rule tests
- Meta predicate tests

## Limitations and Future Extensions

### Current Limitations

- DCG (Definite Clause Grammar) not supported
- Module system not implemented
- Some standard predicates not implemented (`bagof/3`, `setof/3`, etc.)
- Constraint Logic Programming (CLP) not supported

### Future Extension Candidates

- More built-in predicates
- Enhanced debugging features
- Performance optimizations
- Improved standard Prolog compatibility

---

**Note**: This document is created based on the current implementation status. For detailed specifications and usage, please refer to the corresponding source code and test cases.
