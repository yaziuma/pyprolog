from prolog.token_type import TokenType
# Ensure interpreter import is safe (it should be if interpreter uses method-local imports for Parser)
from .interpreter import Conjunction, Rule
from .types import Arithmetic, Logic, Variable, Term, TRUE, Number, Dot, Bar
from .builtins import Fail, Write, Nl, Tab, Retract, AssertA, AssertZ, Cut
from .expression import BinaryExpression, PrimaryExpression
from prolog.logger import logger

logger.debug("parser.py loaded (new version)")

def default_error_handler(line, message):
    print(f'Line[{line}] Error: {message}')
    raise Exception('Parser error')


def is_single_param_buildin(token_type):
    st = set([TokenType.RETRACT, TokenType.ASSERTA, TokenType.ASSERTZ])
    if token_type in st:
        return True
    return False


class Parser:
    def __init__(self, tokens, report=default_error_handler):
        logger.debug(f"Parser initialized with tokens (first 5): {tokens[:5]}{'...' if len(tokens) > 5 else ''}")
        self._current = 0
        self._is_done = False
        self._scope = {}
        self._tokens = tokens
        self._report = report

    def _peek(self):
        return self._tokens[self._current]

    def _peek_next(self):
        return self._tokens[self._current + 1]

    def _is_at_end(self):
        return self._peek().token_type == TokenType.EOF

    def _previous(self):
        return self._tokens[self._current - 1]

    def _advance(self):
        self._current += 1
        if self._is_at_end():
            self._is_done = True
        return self._previous()

    def _token_matches(self, token_type):
        if isinstance(token_type, list):
            return self._peek().token_type in token_type
        return self._peek().token_type == token_type

    def _next_token_matches(self, token_type):
        if self._current + 1 >= len(self._tokens):
            return False # Next token does not exist, so it cannot match
        
        next_token = self._tokens[self._current + 1] # Effectively self._peek_next()
        if isinstance(token_type, list):
            return next_token.token_type in token_type
        return next_token.token_type == token_type

    def _is_type(self, token, token_type):
        return token.token_type == token_type

    def _create_variable(self, name, has_arithmetic_exp=None):
        variable = self._scope.get(name, None)
        if variable is None:
            if has_arithmetic_exp is None:
                variable = Variable(name)
            else:
                variable = Arithmetic(name, has_arithmetic_exp)
            self._scope[name] = variable
        elif isinstance(variable, Variable) and has_arithmetic_exp is not None:
            variable = Arithmetic(name, has_arithmetic_exp)
        return variable

    def _parse_primary(self):
        token = self._peek()

        if self._is_type(token, TokenType.NUMBER):
            self._advance()
            number_value = token.literal
            return PrimaryExpression(Number(number_value))
        elif self._is_type(token, TokenType.VARIABLE):
            self._advance()
            return PrimaryExpression(self._create_variable(token.lexeme))
        elif self._is_type(token, TokenType.LEFTPAREN):
            self._advance()
            expr = self._parse_expression()

            prev_token = self._advance()  # consume ')'
            if prev_token.token_type != TokenType.RIGHTPAREN:
                self._report(
                    self._peek().line, f'Expected ")" after expression: {expr}'
                )
            return expr

        self._report(
            self._peek().line, f'Expected number or variable but got: {token}'
        )

    def _parse_equality(self):
        expr = self._parse_comperison()

        while self._token_matches([TokenType.EQUALEQUAL, TokenType.EQUALSLASH]):
            self._advance()
            operator = self._previous().lexeme
            right = self._parse_comperison()
            expr = BinaryExpression(expr, operator, right)
        return expr

    def _parse_comperison(self):
        expr = self._parse_addition()

        while self._token_matches(
            [
                TokenType.GREATER,
                TokenType.GREATEREQUAL,
                TokenType.LESS,
                TokenType.EQUALLESS,
            ]
        ):
            self._advance()
            operator = self._previous().lexeme
            right = self._parse_addition()
            expr = BinaryExpression(expr, operator, right)
        return expr

    def _parse_addition(self):
        expr = self._parse_multiplication()

        while self._token_matches([TokenType.MINUS, TokenType.PLUS]):
            self._advance()
            operator = self._previous().lexeme
            right = self._parse_multiplication()
            expr = BinaryExpression(expr, operator, right)
        return expr

    def _parse_multiplication(self):
        expr = self._parse_primary()

        while self._token_matches([TokenType.SLASH, TokenType.STAR]):
            self._advance()
            operator = self._previous().lexeme
            right = self._parse_primary()
            expr = BinaryExpression(expr, operator, right)
        return expr

    def _parse_expression(self):
        return self._parse_equality()

    def _parse_arithmetic(self, token):
        self._advance()  # consume IS

        return self._create_variable(token.lexeme, self._parse_expression())

    def _parse_logic(self):
        return Logic(self._parse_equality())

    def _parse_atom(self):
        token = self._advance() # Consume the token

        if self._is_type(token, TokenType.TRUE):
            return TRUE()
        if self._is_type(token, TokenType.FAIL):
            return Fail()
        if self._is_type(token, TokenType.CUT): # Assuming CUT token is for '!'
            return Cut()
        
        # Check for other valid atom types, similar to original logic but after advancing
        # and after checking special atoms.
        if not self._is_type(token, TokenType.ATOM) and \
           not self._is_type(token, TokenType.VARIABLE) and \
           not self._is_type(token, TokenType.UNDERSCORE) and \
           not self._is_type(token, TokenType.NUMBER) and \
           not self._is_type(token, TokenType.WRITE) and \
           not self._is_type(token, TokenType.NL) and \
           not self._is_type(token, TokenType.TAB) and \
           not self._is_type(token, TokenType.RETRACT) and \
           not self._is_type(token, TokenType.ASSERTA) and \
           not self._is_type(token, TokenType.ASSERTZ):
            # If it's not any of the special atoms or other known valid types for an atom context
            self._report(token.line, f'Bad atom name or unexpected token: {token.lexeme} of type {token.token_type}')
            return None # Or raise error

        # If it's a number token used as an atom (e.g. in p(1)), it's an error if it starts a rule or is a predicate name.
        # This check might be better placed where predicates/rules are formed.
        # For now, let's assume if it passed the TokenType checks, it's a valid lexeme for an atom/term component.
        # The original code returned the token, the plan implies returning specific types (TRUE, Fail, Cut)
        # For generic atoms (like 'abc'), we should return a Term or the token itself if _parse_term handles it.
        # Let's return the token for now, and _parse_term will decide what to do.
        # However, the plan's _parse_atom returns TRUE() or Fail().
        # This suggests _parse_atom should directly return these types.
        # For a generic atom string, it should probably return a Term(token.lexeme) or just the token.
        # The existing _parse_term uses the result of _parse_atom (which was a token) to get token.lexeme.
        # Let's adjust to return the token if not a special atom, to align with _parse_term's expectation.
        # Or, _parse_term needs to be adjusted.
        # For now, returning the token for non-special atoms.
        # The plan's _parse_atom was:
        # if token.lexeme == 'true': return TRUE()
        # if token.lexeme == 'fail': return Fail()
        # This implies the scanner might not tokenize 'true' to TokenType.TRUE.
        # But we modified the scanner to do so. So checking token.token_type is correct.

        # If it's a generic ATOM token, or VARIABLE/NUMBER used in a context where an atom is expected
        # (e.g. as a predicate name or argument), _parse_term will handle it.
        # The primary role here is to convert special tokens (TRUE, FAIL, CUT) to their respective objects.
        # For other atom-like tokens, return the token itself for _parse_term to process.
        if self._is_type(token, TokenType.ATOM) or \
           self._is_type(token, TokenType.VARIABLE) or \
           self._is_type(token, TokenType.UNDERSCORE) or \
           self._is_type(token, TokenType.NUMBER) or \
           self._is_type(token, TokenType.WRITE) or \
           self._is_type(token, TokenType.NL) or \
           self._is_type(token, TokenType.TAB) or \
           self._is_type(token, TokenType.RETRACT) or \
           self._is_type(token, TokenType.ASSERTA) or \
           self._is_type(token, TokenType.ASSERTZ):
            return token # Return the token for further processing by _parse_term

        # Should not be reached if the checks above are comprehensive
        self._report(token.line, f'Unhandled token in _parse_atom: {token.lexeme}')
        return None

    def _parse_buildin_single_arg(self, predicate, args):
        if len(args) != 1:
            self._report(
                self._peek().line, f'{predicate} requires exactly one argument'
            )
        if predicate == 'retract':
            return Retract(args[0])
        if predicate == 'asserta':
            return AssertA(args[0])
        if predicate == 'assertz':
            return AssertZ(args[0])

    def _parse_list(self):
        logger.debug(f"Parser._parse_list entered. Current token: {self._peek()}")
        dot_list = []
        dot_tail = None
        self._advance()  # consume '['

        # Handle empty list: []
        if self._token_matches(TokenType.RIGHTBRACKET):
            self._advance()  # consume ']'
            result = Dot.from_list([])
            logger.debug(f"Parser._parse_list: parsed empty list: {result}")
            return result

        while not self._token_matches(TokenType.RIGHTBRACKET):
            if self._token_matches(TokenType.BAR):
                self._advance()  # consume '|'
                dot_tail = self._parse_term() # Parse the tail term
                # After | Tail, we expect a closing bracket
                if not self._token_matches(TokenType.RIGHTBRACKET):
                    self._report(self._peek().line, f"Expected ']' after | Tail in list, but got {self._peek()}")
                break  # Tail part is parsed, exit loop for elements

            # Parse list element
            list_element = None
            if self._token_matches(TokenType.LEFTBRACKET):
                list_element = self._parse_list()
            else:
                list_element = self._parse_term()
            dot_list.append(list_element)

            if self._token_matches(TokenType.COMMA):
                self._advance()  # consume ','
                # Check for trailing comma before ']' e.g. [a,]
                if self._token_matches(TokenType.RIGHTBRACKET):
                    self._report(self._peek().line, "Unexpected ']' after comma in list.")
            elif not self._token_matches(TokenType.RIGHTBRACKET) and not self._token_matches(TokenType.BAR):
                # If not a comma, and not a closing bracket, and not a bar (handled above), it's an error
                self._report(self._peek().line, f"Expected ',' or '|' or ']' in list element sequence, but got {self._peek()}")

        if not self._token_matches(TokenType.RIGHTBRACKET):
             # This case should ideally be caught by checks within the loop or before it.
             # If loop exited due to BAR, RIGHTBRACKET is expected.
             # If loop exited due to RIGHTBRACKET, then this check is redundant.
             # However, as a safeguard:
            self._report(self._peek().line, f"List not properly closed. Expected ']', got {self._peek()}")

        self._advance()  # consume right bracket

        if dot_tail is None:
            result = Dot.from_list(dot_list)
            logger.debug(f"Parser._parse_list: parsed proper list: {result}")
            return result
        else:
            # If dot_tail is present, dot_list contains elements before the |
            result = Bar(Dot.from_list(dot_list), dot_tail)
            logger.debug(f"Parser._parse_list: parsed list with tail: {result}")
            return result

    def _parse_term(self):
        logger.debug(f"Parser._parse_term entered. Current token: {self._peek()}")
        if self._token_matches(TokenType.LEFTPAREN):
            self._advance()
            args = []
            while not self._token_matches(TokenType.RIGHTPAREN):
                args.append(self._parse_term())
                if not self._token_matches(
                    TokenType.COMMA
                ) and not self._token_matches(TokenType.RIGHTPAREN):
                    self._report(
                        self._peek().line,
                        f'Expecter , or ) in term but got {self._peek()}',
                    )
                if self._token_matches(TokenType.COMMA):
                    self._advance()

            self._advance()
            result = Conjunction(args)
            logger.debug(f"Parser._parse_term: parsed conjunction in parens: {result}")
            return result

        if self._next_token_matches(
            [
                TokenType.EQUALEQUAL,
                TokenType.EQUALSLASH,
                TokenType.EQUALLESS,
                TokenType.LESS,
                TokenType.GREATEREQUAL,
                TokenType.GREATER,
            ]
        ):
            result = self._parse_logic()
            logger.debug(f"Parser._parse_term: parsed logic expression: {result}")
            return result

        if self._token_matches(TokenType.LEFTBRACKET):
            result = self._parse_list()
            logger.debug(f"Parser._parse_term: parsed list: {result}")
            return result

        # Call _parse_atom to get either a special object (TRUE, Fail, Cut) or a token
        atom_or_builtin_obj = self._parse_atom()

        # Handle cases where _parse_atom returns a special builtin object
        if isinstance(atom_or_builtin_obj, (TRUE, Fail, Cut)):
            # These are typically standalone terms. If followed by '(', it's a syntax error.
            if self._token_matches(TokenType.LEFTPAREN):
                self._report(self._peek().line, f"Special term '{type(atom_or_builtin_obj).__name__}' cannot be used as a functor.")
                return None # Or raise an error
            # logger.debug(f"Parser._parse_term: parsed special builtin: {atom_or_builtin_obj}") # Redundant with _parse_atom log
            return atom_or_builtin_obj

        # If _parse_atom reported an error and returned None
        if atom_or_builtin_obj is None:
            logger.debug("Parser._parse_term: _parse_atom returned None, propagating.")
            return None

        # At this point, atom_or_builtin_obj should be a regular Token (ATOM, VARIABLE, NUMBER, etc.)
        token = atom_or_builtin_obj
        # Ensure token is not None again, just in case (though covered above)
        if token is None: # Should not happen if logic above is correct
             self._report(self._peek().line, "Internal parser error: token became None unexpectedly.")
             return None

        # token is atom_or_builtin_obj, which is a Token object here.
        # predicate is used for ATOM and VARIABLE tokens.
        predicate = token.lexeme if hasattr(token, 'lexeme') and token.token_type in [TokenType.ATOM, TokenType.VARIABLE, TokenType.WRITE, TokenType.RETRACT, TokenType.ASSERTA, TokenType.ASSERTZ] else None

        # Stage 1: Parse a potential left-hand-side term (could be simple or complex)
        lhs_term = None
        if self._is_type(token, TokenType.VARIABLE) or self._is_type(token, TokenType.UNDERSCORE):
            if self._is_type(token, TokenType.UNDERSCORE):
                lhs_term = Variable('_')
            elif self._peek().token_type == TokenType.IS: # X is ...
                lhs_term = self._parse_arithmetic(token) # token is the variable token
            else:
                lhs_term = self._create_variable(token.lexeme) # Use token.lexeme directly for var name
        elif self._is_type(token, TokenType.NL):
            lhs_term = Nl()
        elif self._is_type(token, TokenType.TAB):
            lhs_term = Tab()
        elif self._is_type(token, TokenType.NUMBER):
            lhs_term = Number(token.literal) # Use token.literal for numbers
        elif self._is_type(token, TokenType.ATOM) or \
             self._is_type(token, TokenType.WRITE) or \
             is_single_param_buildin(token.token_type): # ATOM, WRITE, RETRACT, ASSERTA, ASSERTZ
            
            # 'predicate' here should be token.lexeme
            current_predicate_name = token.lexeme 

            if not self._token_matches(TokenType.LEFTPAREN): # Simple atom/builtin name
                # For NL and TAB tokens, specific objects are preferred over Term(predicate)
                if self._is_type(token, TokenType.NL): lhs_term = Nl()
                elif self._is_type(token, TokenType.TAB): lhs_term = Tab()
                else: lhs_term = Term(current_predicate_name)
            else: # Structure: predicate(...)
                self._advance() # Consume '('
                args = []
                while not self._token_matches(TokenType.RIGHTPAREN):
                    parsed_arg = self._parse_term() # Recursive call
                    if parsed_arg is None: # Propagate parsing error
                        return None
                    args.append(parsed_arg)
                    if not self._token_matches(TokenType.COMMA) and not self._token_matches(TokenType.RIGHTPAREN):
                        self._report(self._peek().line, f'Expected , or ) in term arguments for {current_predicate_name}, but got {self._peek()}')
                        return None
                    if self._token_matches(TokenType.COMMA):
                        self._advance()
                self._advance() # Consume ')'

                if is_single_param_buildin(token.token_type):
                    lhs_term = self._parse_buildin_single_arg(current_predicate_name, args)
                elif self._is_type(token, TokenType.WRITE):
                    lhs_term = Write(*args)
                else:
                    lhs_term = Term(current_predicate_name, *args) # Generic structure
        else:
            self._report(token.line, f"Parser._parse_term: Unhandled token type {token.token_type} ({token.lexeme if hasattr(token, 'lexeme') else 'N/A'}) for LHS parsing.")
            return None

        if lhs_term is None:
            self._report(self._peek().line, f"Parser._parse_term: Could not determine LHS from token {token}")
            return None
        
        logger.debug(f"Parser._parse_term: Parsed LHS: {lhs_term}")

        # Stage 2: Check if this LHS is followed by an '=' operator
        if self._token_matches(TokenType.EQUAL):
            self._advance() # Consume '='
            rhs_term = self._parse_term() # Recursive call for RHS
            if rhs_term is None:
                self._report(self._peek().line, "Missing or invalid right-hand side for '=' operator.")
                return None
            
            equality_term = Term("=", lhs_term, rhs_term)
            logger.debug(f"Parser._parse_term: Parsed equality term: {equality_term}")
            return equality_term
        
        # If not followed by '=', then the lhs_term is the complete term.
        logger.debug(f"Parser._parse_term: Parsed term (no '=' found after LHS): {lhs_term}")
        return lhs_term

    def _parse_rule(self):
        logger.debug(f"Parser._parse_rule entered. Current token: {self._peek()}")
        head = self._parse_term()

        if self._token_matches(TokenType.DOT):
            self._advance()
            result = Rule(head, TRUE())
            logger.debug(f"Parser._parse_rule: parsed fact: {result}")
            return result

        if not self._token_matches(TokenType.COLONMINUS):
            self._report(
                self._peek().line, f'Expected :- in rule but got {self._peek()}'
            )

        self._advance()
        args = []
        while not self._token_matches(TokenType.DOT):
            args.append(self._parse_term())
            if not self._token_matches(
                TokenType.COMMA
            ) and not self._token_matches(TokenType.DOT):
                self._report(
                    self._peek().line,
                    f'Expected , or . in term but got {self._peek()}',
                )

            if self._token_matches(TokenType.COMMA):
                self._advance()

        self._advance()
        body = None
        if len(args) == 1:
            body = args[0]
        else:
            body = Conjunction(args)

        result = Rule(head, body)
        logger.debug(f"Parser._parse_rule: parsed rule: {result}")
        return result

    def _all_vars(self, terms):
        variables = []
        for term in terms:
            if isinstance(term, Term):
                for arg in term.args:
                    if isinstance(arg, Variable):
                        if arg not in variables:
                            variables.append(arg)
        return variables

    def _parse_query(self):
        logger.debug(f"Parser._parse_query entered. Current token: {self._peek()}")
        head_term = self._parse_term() # Renamed to avoid conflict with 'head' variable for Rule

        if self._token_matches(TokenType.DOT):
            self._advance()
            logger.debug(f"Parser._parse_query: parsed simple query (term): {head_term}")
            return head_term

        if self._token_matches(TokenType.COLONMINUS):
            self._report(self._peek().line, 'Cannot use rule as a query')

        # self._advance() # Consume the operator that was not DOT or COLONMINUS (e.g. comma for conjunction) # Problematic: caused IndexError for simple queries like "goal"
        args = [head_term]
        while not self._token_matches(TokenType.DOT):
            term_in_conj = self._parse_term()
            if term_in_conj is None: # Error during parsing term in conjunction
                 logger.error(f"Parser._parse_query: Failed to parse term in conjunction at {self._peek()}")
                 # Decide error handling: stop or try to continue? For now, stop.
                 return None # Or raise error
            args.append(term_in_conj)

            if not self._token_matches(TokenType.COMMA) and not self._token_matches(TokenType.DOT):
                self._report(
                    self._peek().line,
                    f'Expected , or . in query conjunction but got {self._peek()}',
                )
                # Potentially return None or raise error to stop further processing of this malformed query
                return None

            if self._token_matches(TokenType.COMMA):
                self._advance()
                if self._token_matches(TokenType.DOT): # e.g. query(X),.
                    self._report(self._peek().line, "Unexpected '.' after comma in query conjunction.")
                    return None


        self._advance() # Consume DOT

        query_head_vars = self._all_vars(args) # Use the collected args for var extraction
        if query_head_vars:
            query_rule_head = Term('##', *query_head_vars)
        else:
            query_rule_head = Term('##') # No vars, e.g. true. or p(a).

        result = Rule(query_rule_head, Conjunction(args))
        logger.debug(f"Parser._parse_query: parsed query as rule: {result}")
        return result

    def parse_rules(self):
        logger.debug("Parser.parse_rules (public) called")
        rules = []
        while not self._is_done and self._peek().token_type != TokenType.EOF : # Added EOF check
            self._scope = {} # Reset scope for each rule
            rule = self._parse_rule()
            if rule:
                rules.append(rule)
            elif not self._is_done and self._peek().token_type != TokenType.EOF :
                # If _parse_rule returned None but we are not at EOF, there might be an unhandled error or empty input.
                # Attempt to advance past problematic token if synchronization is desired.
                # For now, just log and break to avoid infinite loop on bad input.
                logger.warning(f"Parser.parse_rules: _parse_rule returned None. Next token: {self._peek()}. Stopping.")
                break
        logger.debug(f"Parser.parse_rules (public) returning: {rules}")
        return rules

    def parse_terms(self):
        logger.debug("Parser.parse_terms (public) called")
        self._scope = {} # Reset scope
        # This method in original pieprolog seems to parse only one term.
        # The test cases might expect this to parse a sequence for conjunctions or list elements.
        # The previous version of this code in my thought process was more elaborate.
        # Let's stick to parsing a single top-level term as per current file structure.
        # If a sequence is needed, the caller should loop or use a different method.
        if self._is_done or self._peek().token_type == TokenType.EOF:
            logger.debug("Parser.parse_terms (public): No tokens or EOF. Returning None.")
            return None
        
        term = self._parse_term()
        # Optionally, consume a trailing dot if present, as queries/facts do.
        # if self._token_matches(TokenType.DOT):
        #    self._advance()
        logger.debug(f"Parser.parse_terms (public) returning: {term}")
        return term


    def parse_query(self):
        logger.debug("Parser.parse_query (public) called")
        self._scope = {} # Reset scope
        if self._is_done or self._peek().token_type == TokenType.EOF:
            logger.debug("Parser.parse_query (public): No tokens or EOF. Returning None.")
            return None

        query = self._parse_query() # Calls the internal _parse_query
        logger.debug(f"Parser.parse_query (public) returning: {query}")
        return query
