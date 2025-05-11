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
        if isinstance(token_type, list):
            return self._peek_next().token_type in token_type
        return self._peek_next().token_type == token_type

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
        token = self._peek()
        if not self._token_matches(
            [
                TokenType.VARIABLE,
                TokenType.UNDERSCORE,
                TokenType.NUMBER,
                TokenType.FAIL,
                TokenType.WRITE,
                TokenType.NL,
                TokenType.TAB,
                TokenType.RETRACT,
                TokenType.ASSERTA,
                TokenType.ASSERTZ,
                TokenType.CUT,
                TokenType.ATOM,
            ]
        ):
            self._report(token.line, f'Bad atom name: {token.lexeme}')

        if self._is_type(token, TokenType.NUMBER):
            if (
                self._peek_next().token_type == TokenType.COLONMINUS
                or self._peek_next().token_type == TokenType.DOT
                or self._peek_next().token_type == TokenType.LEFTPAREN
            ):
                self._report(
                    self._peek().line,
                    f'Number cannot be a rule: {self._peek()}',
                )

        self._advance()
        return token

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

        token = self._parse_atom()
        predicate = token.lexeme
        if self._is_type(token, TokenType.VARIABLE) or self._is_type(
            token, TokenType.UNDERSCORE
        ):
            if self._is_type(token, TokenType.UNDERSCORE):
                result = Variable('_')
                logger.debug(f"Parser._parse_term: parsed underscore variable: {result}")
                return result

            if self._is_type(token, TokenType.VARIABLE):
                if self._peek().token_type == TokenType.IS:
                    result = self._parse_arithmetic(token)
                    logger.debug(f"Parser._parse_term: parsed arithmetic assignment: {result}")
                    return result

            result = self._create_variable(predicate)
            logger.debug(f"Parser._parse_term: created/got variable: {result}")
            return result

        if self._is_type(token, TokenType.FAIL):
            result = Fail()
            logger.debug(f"Parser._parse_term: parsed Fail builtin: {result}")
            return result

        if self._is_type(token, TokenType.CUT):
            result = Cut()
            logger.debug(f"Parser._parse_term: parsed Cut builtin: {result}")
            return result

        if self._is_type(token, TokenType.NL):
            result = Nl()
            logger.debug(f"Parser._parse_term: parsed Nl builtin: {result}")
            return result

        if self._is_type(token, TokenType.TAB):
            result = Tab()
            logger.debug(f"Parser._parse_term: parsed Tab builtin: {result}")
            return result

        if self._is_type(token, TokenType.NUMBER):
            number_value = token.literal
            result = Number(number_value)
            logger.debug(f"Parser._parse_term: parsed Number: {result}")
            return result

        if not self._token_matches(TokenType.LEFTPAREN):
            result = Term(predicate)
            logger.debug(f"Parser._parse_term: parsed simple atom Term: {result}")
            return result

        self._advance()
        args = []
        while not self._token_matches(TokenType.RIGHTPAREN):
            args.append(self._parse_term())
            if not self._token_matches(
                TokenType.COMMA
            ) and not self._token_matches(TokenType.RIGHTPAREN):
                self._report(
                    self._peek().line,
                    f'Expected , or ) in term but got {self._peek()}',
                )

            if self._token_matches(TokenType.COMMA):
                self._advance()

        self._advance()

        if is_single_param_buildin(token.token_type):
            result = self._parse_buildin_single_arg(predicate, args)
            logger.debug(f"Parser._parse_term: parsed single arg builtin: {result}")
            return result

        if self._is_type(token, TokenType.WRITE):
            result = Write(*args)
            logger.debug(f"Parser._parse_term: parsed Write builtin: {result}")
            return result

        result = Term(predicate, *args)
        logger.debug(f"Parser._parse_term: parsed structure Term: {result}")
        return result

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

        self._advance() # Consume the operator that was not DOT or COLONMINUS (e.g. comma for conjunction)
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
