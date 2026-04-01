from pyprolog.core.errors import InvalidCliArgsError
from pyprolog.core.types import (
    Atom,
    ListTerm,
    Number,
    PrologType,
    String,
    Term,
    Variable,
)


def normalize_cli_args(args_term: PrologType) -> list[str]:
    items = _flatten_prolog_list(args_term)
    normalized: list[str] = []

    for item in items:
        if isinstance(item, Variable):
            raise InvalidCliArgsError("unbound variable is not allowed in Args")
        if isinstance(item, Atom):
            normalized.append(item.name)
            continue
        if isinstance(item, String):
            normalized.append(item.value)
            continue
        if isinstance(item, Number):
            normalized.append(str(item.value))
            continue
        if isinstance(item, (Term, ListTerm)):
            raise InvalidCliArgsError(
                "only atom/string/number are allowed in Args"
            )
        raise InvalidCliArgsError("unsupported argument type in Args")

    return normalized


def _flatten_prolog_list(term: PrologType) -> list[PrologType]:
    if isinstance(term, Atom) and term.name == "[]":
        return []

    if isinstance(term, ListTerm):
        if term.tail is not None and not (
            isinstance(term.tail, Atom) and term.tail.name == "[]"
        ):
            raise InvalidCliArgsError("nested list or improper list is not allowed")
        return list(term.elements)

    items: list[PrologType] = []
    current = term

    while isinstance(current, Term) and isinstance(current.functor, Atom):
        if current.functor.name != "." or len(current.args) != 2:
            raise InvalidCliArgsError("Args must be a list")
        head, tail = current.args
        if isinstance(head, (Term, ListTerm)):
            raise InvalidCliArgsError("nested list or compound term is not allowed")
        items.append(head)
        current = tail

    if isinstance(current, Atom) and current.name == "[]":
        return items

    if isinstance(current, Variable):
        raise InvalidCliArgsError("Args must be a bound list")

    raise InvalidCliArgsError("Args must be a proper list")
