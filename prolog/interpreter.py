import io
from .types import (
    TermFunction,
    Variable,
    Term,
    merge_bindings,
    Arithmetic,
    Logic,
    FALSE,
    TRUE,
    CUT, # This is the CUT Term from types.py
)
from .builtins import Write, Nl, Tab, Fail, Cut as BuiltinCut, Retract, AssertA, AssertZ # Renamed to avoid clash with types.CUT
from prolog.token_type import TokenType
from prolog.logger import logger

logger.debug("interpreter.py loaded")

# Scanner and Parser will be imported inside methods to break circular dependency
# from prolog.scanner import Scanner # Moved
# from prolog.parser import Parser   # Moved

class Rule:
    def __init__(self, head, body):
        # logger.debug(f"Rule initialized with head: {head}, body: {body}") # Can be verbose
        self.head = head
        self.body = body

    def __str__(self):
        if isinstance(self.body, TRUE):
            return f'{self.head}.'
        return f'{self.head} :- {self.body}.'


    def __repr__(self):
        return str(self)

class Conjunction(Term):
    def __init__(self, args):
        # logger.debug(f"Conjunction initialized with args: {args}") # Can be verbose
        super().__init__(None, *args)

    def _is_builtin(self, arg):
        if (
            isinstance(arg, Write)
            or isinstance(arg, Nl)
            or isinstance(arg, Tab)
        ):
            return True
        return False

    def _is_db_builtin(self, arg):
        if (
            isinstance(arg, Retract)
            or isinstance(arg, AssertA)
            or isinstance(arg, AssertZ)
        ):
            return True
        return False

    def _is_fail(self, arg):
        if isinstance(arg, Fail):
            return True
        return False

    def _is_cut(self, arg):
        # Checks if the argument is an instance of prolog.builtins.Cut
        if isinstance(arg, BuiltinCut): 
            return True
        return False

    def query(self, runtime):
        logger.debug(f"Conjunction.query called for args: {self.args}")
        def solutions(index, bindings):
            logger.debug(f"Conjunction.solutions: index={index}, bindings={bindings}, total_args={len(self.args)}")
            if index >= len(self.args):
                res_sub = self.substitute(bindings)
                logger.debug(f"Conjunction.solutions: base case, yielding substituted conjunction: {res_sub}")
                yield res_sub
            else:
                arg = self.args[index]
                logger.debug(f"Conjunction.solutions: processing arg[{index}] = {arg}")
                if self._is_cut(arg): 
                    logger.debug(f"Conjunction.solutions: arg is CUT {arg}")
                    for _ in runtime.execute(arg.substitute(bindings)): 
                        logger.debug(f"Conjunction.solutions: Executing goals after CUT for bindings: {bindings}")
                        yield from solutions(index + 1, bindings)
                        logger.debug("Conjunction.solutions: Yielding CUT signal after solutions for goals post-cut.")
                        yield CUT() 
                        return 

                elif self._is_fail(arg): 
                    logger.debug(f"Conjunction.solutions: arg is FAIL {arg}, yielding FALSE")
                    yield FALSE()
                elif self._is_builtin(arg): 
                    logger.debug(f"Conjunction.solutions: arg is IO builtin {arg}, executing its query")
                    _ = list(arg.query(runtime, bindings))  
                    logger.debug(f"Conjunction.solutions: IO builtin executed, proceeding to next arg with bindings: {bindings}")
                    yield from solutions(index + 1, bindings)
                elif self._is_db_builtin(arg): 
                    logger.debug(f"Conjunction.solutions: arg is DB builtin {arg}, executing its query")
                    _ = list(arg.query(runtime, bindings))  
                    logger.debug(f"Conjunction.solutions: DB builtin executed, proceeding to next arg with bindings: {bindings}")
                    yield from solutions(index + 1, bindings)
                elif isinstance(arg, Arithmetic):
                    logger.debug(f"Conjunction.solutions: arg is Arithmetic {arg}")
                    val = arg.substitute(bindings).evaluate()
                    unified = merge_bindings({arg.var: val}, bindings)
                    if unified is None: 
                        logger.error(f"Conjunction.solutions: Arithmetic merge_bindings failed for {arg.var}={val} with {bindings}")
                        return
                    logger.debug(f"Conjunction.solutions: Arithmetic evaluated, proceeding with unified bindings: {unified}")
                    yield from solutions(index + 1, unified)
                elif isinstance(arg, Logic):
                    logger.debug(f"Conjunction.solutions: arg is Logic {arg}, evaluating")
                    eval_result = arg.substitute(bindings).evaluate()
                    logger.debug(f"Conjunction.solutions: Logic evaluated to {eval_result}, yielding it.")
                    if eval_result: # If logic expression is true
                        yield from solutions(index + 1, bindings)
                    else: # If logic expression is false, this path fails
                        logger.debug(f"Conjunction.solutions: Logic expression {arg} evaluated to False. Path fails.")
                        return
                else: 
                    logger.debug(f"Conjunction.solutions: arg is general term {arg}, calling runtime.execute")
                    for item in runtime.execute(arg.substitute(bindings)):
                        logger.debug(f"Conjunction.solutions: item from runtime.execute({arg.substitute(bindings)}): {item}")
                        if isinstance(item, FALSE): 
                            logger.debug("Conjunction.solutions: item is FALSE, this conjunction path fails.")
                            continue 

                        if isinstance(item, CUT): 
                            logger.error("Conjunction.solutions: Unexpected CUT signal received from runtime.execute on a general term.")
                            yield item 
                            return

                        unified = merge_bindings(arg.match(item), bindings)
                        logger.debug(f"Conjunction.solutions: unified bindings for {arg} and {item}: {unified} (original: {bindings})")
                        if unified is not None:
                            logger.debug(f"Conjunction.solutions: proceeding to next arg with unified bindings: {unified}")
                            yield from solutions(index + 1, unified)
                        else:
                            logger.debug(f"Conjunction.solutions: unification failed for {arg} and {item}, trying next item.")
                    logger.debug(f"Conjunction.solutions: runtime.execute for {arg} exhausted for bindings {bindings}.")
                    return 

        logger.debug("Conjunction.query: starting solutions generator")
        yield from solutions(0, {})

    def substitute(self, bindings):
        return Conjunction(
            map((lambda arg: arg.substitute(bindings)), self.args)
        )

class Runtime:
    def __init__(self, rules):
        logger.debug(f"Runtime initialized with rules (count: {len(rules)}): {rules[:3]}{'...' if len(rules) > 3 else ''}")
        self.rules = rules
        self.stream = io.StringIO()
        self.stream_pos = 0

    def __del__(self):
        logger.debug("Runtime.__del__ called")
        self.stream.close()

    def stream_write(self, text):
        self.stream.write(text)

    def stream_read(self):
        self.stream.seek(self.stream_pos)
        line = self.stream.read()
        self.stream_pos = self.stream.tell()
        return line

    def reset_stream(self):
        logger.debug("Runtime.reset_stream called")
        self.stream.seek(0)
        self.stream.truncate(0)
        self.stream_pos = 0

    def consult_rules(self, rules_str):
        from prolog.scanner import Scanner
        from prolog.parser import Parser
        logger.debug(f"Runtime.consult_rules called with: {rules_str[:100]}{'...' if len(rules_str) > 100 else ''}")
        if not rules_str.strip():
            logger.debug("Runtime.consult_rules: empty string, returning.")
            return

        tokens = Scanner(rules_str).tokenize()
        logger.debug(f"Runtime.consult_rules: tokens (first 5): {tokens[:5]}{'...' if len(tokens) > 5 else ''}")
        if not tokens or (len(tokens) == 1 and tokens[0].token_type == TokenType.EOF):
            logger.debug("Runtime.consult_rules: no relevant tokens, returning.")
            return
        
        new_rules = Parser(tokens).parse_rules()
        logger.debug(f"Runtime.consult_rules: parsed new rules (count {len(new_rules)}): {new_rules[:3]}{'...' if len(new_rules) > 3 else ''}")
        self.rules.extend(new_rules)
        logger.debug(f"Runtime.consult_rules: total rules now: {len(self.rules)}")

    def query(self, query_str):
        from prolog.scanner import Scanner
        from prolog.parser import Parser
        logger.debug(f"Runtime.query called with: '{query_str}'")
        tokens = Scanner(query_str).tokenize()
        logger.debug(f"Runtime.query: tokens (first 5): {tokens[:5]}{'...' if len(tokens) > 5 else ''}")

        if not tokens or (len(tokens) == 1 and tokens[0].token_type == TokenType.EOF):
            logger.debug("Runtime.query: no relevant tokens, returning (no solutions).")
            return

        parsed_query = Parser(tokens).parse_query()
        logger.debug(f"Runtime.query: parsed_query: {parsed_query}, type: {type(parsed_query)}")

        # 変数収集方法の修正
        query_vars = []
        
        # 直接クエリを探索して変数を見つける関数
        def find_variables(term):
            if isinstance(term, Variable):
                if term.name != '_':  # アンダースコア変数は除外
                    # 重複を避けるためにリストに追加する前に確認
                    if term not in query_vars:
                         return [term]
                return []
            elif isinstance(term, Term): # TermにはConjunctionも含まれる
                vars_list = []
                for arg in term.args:
                    found_in_arg = find_variables(arg)
                    for v in found_in_arg:
                        if v not in vars_list: # Conjunction内で重複を避ける
                           vars_list.append(v)
                return vars_list
            elif isinstance(term, Rule): # Ruleオブジェクトの場合 (通常はparsed_queryがこれ)
                vars_list = []
                # Ruleのheadから変数を探す
                if hasattr(term, 'head') and term.head is not None:
                    head_vars = find_variables(term.head)
                    for v_h in head_vars:
                        if v_h not in vars_list: vars_list.append(v_h)
                # Ruleのbodyから変数を探す (Conjunctionの場合も考慮)
                if hasattr(term, 'body') and term.body is not None:
                    body_vars = find_variables(term.body) # term.bodyがConjunctionならそのargsが探索される
                    for v_b in body_vars:
                        if v_b not in vars_list: vars_list.append(v_b)
                return vars_list
            return []
        
        # クエリから変数を収集
        # parsed_query は Term (単一ゴール) または Rule (##(Vars):- Body の形)
        if isinstance(parsed_query, Term): # e.g. p(X). or p(X,Y).
            query_vars = find_variables(parsed_query)
        elif isinstance(parsed_query, Rule): # e.g. query_is_rule(X) :- body(X).
                                         # or ##(X) :- p(X). (parserが作るクエリ形式)
            # Ruleの場合、そのheadとbodyの両方から変数を集める必要があるかもしれない。
            # 特に、parserが作る Rule(Term("##", Vars), BodyConjunction) の形式では、
            # Varsがクエリのトップレベル変数を保持している。
            # しかし、より一般的な find_variables を parsed_query 全体に適用する方が堅牢かもしれない。
            query_vars = find_variables(parsed_query)


        # query_varsリスト内の重複を削除し、元の順序を保持
        seen_vars = set()
        unique_query_vars = []
        for var in query_vars:
            if var.name not in seen_vars:
                unique_query_vars.append(var)
                seen_vars.add(var.name)
        query_vars = unique_query_vars

        logger.debug(f"Runtime.query: Found variables in query: {[var.name for var in query_vars if var is not None]}")
        
        solution_count = 0
        for solution_item in self.execute(parsed_query): # self.executeは通常、具体化されたヘッド項を返す
            logger.debug(f"Runtime.query: solution_item from execute: {solution_item}, type: {type(solution_item)}")
            if isinstance(solution_item, FALSE) or solution_item is None:
                logger.debug("Runtime.query: solution_item is FALSE or None, skipping.")
                continue
            if isinstance(solution_item, CUT): # types.CUT
                logger.warning("Runtime.query: CUT signal reached top-level query. This should ideally be handled internally.")
                # 通常、CUTは evaluate_rules で処理され、ここまで到達しないはず
                break # CUTは通常、親の選択ポイントを削除するので、クエリレベルでは解の生成を停止

            current_bindings = {}
            if query_vars:
                # solution_item (具体化されたヘッド) と元の parsed_query (のヘッド部分) を比較してバインディングを抽出
                # parsed_queryがTermの場合、それが直接のゴール
                # parsed_queryがRuleの場合、parsed_query.headが元のクエリの構造を持つことが多い（特に##ヘッドの場合）
                
                original_query_structure = parsed_query
                if isinstance(parsed_query, Rule) and parsed_query.head.pred == "##":
                    # ##(V1, V2) :- goal(V1, V2). のような場合、
                    # solution_item は goal(val1, val2) のような形ではなく、##(val1, val2) の形で返ってくる。
                    # この場合、solution_item.args と query_vars (##の引数だったもの) を対応させる。
                    original_query_structure = parsed_query.head


                # solution_item (具体化されたゴール) と original_query_structure (変数が含まれる元のゴール) をマッチング
                # ここでは、solution_item が具体化されたバージョンであると仮定し、
                # query_vars に含まれる各変数について、対応する値を見つける。
                # これは、solution_item を再度 original_query_structure とマッチさせることで実現できる。
                # ただし、solution_item は既に具体化されているため、
                # original_query_structure.match(solution_item) を行うと、
                # original_query_structure内の変数がsolution_itemの対応する部分に束縛される。
                
                # もし solution_item が ##(val1, val2) の形で、query_vars が [V1, V2] なら、
                # V1=val1, V2=val2 のような束縛を得たい。
                
                # 以前のロジック: solution_item.pred == "##" の場合
                if isinstance(solution_item, Term) and solution_item.pred == "##":
                    if len(query_vars) == len(solution_item.args):
                        for i, var_obj in enumerate(query_vars):
                             # query_varsの順序とsolution_item.argsの順序が対応すると仮定
                            current_bindings[var_obj] = solution_item.args[i]
                    else:
                        logger.error(f"Runtime.query: Mismatch in query_vars ({[v.name for v in query_vars]}) and solution_item.args ({solution_item.args}) for ## term")
                elif isinstance(solution_item, Term) and isinstance(original_query_structure, Term):
                    # 一般的なケース: solution_item は p(a,b) で original_query_structure は p(X,Y)
                    # original_query_structure.match(solution_item) を使って束縛を得る
                    match_result_bindings = original_query_structure.match(solution_item)
                    if match_result_bindings is not None:
                        # query_vars に含まれる変数のみを抽出
                        for q_var in query_vars:
                            if q_var in match_result_bindings:
                                current_bindings[q_var] = match_result_bindings[q_var]
                    else:
                        logger.warning(f"Runtime.query: Could not match original query structure {original_query_structure} with solution {solution_item}")


                if current_bindings or not query_vars: # 変数がないクエリでも空の束縛は解とみなす
                    logger.debug(f"Runtime.query: Yielding bindings: {current_bindings}")
                    solution_count +=1
                    yield current_bindings
                # else:
                    # クエリに変数はあるが、この解からは束縛が得られなかった場合。
                    # これは通常、解がないことを意味するか、束縛抽出ロジックの問題。
                    # logger.warning(f"Runtime.query: No bindings extracted for solution: {solution_item} with query_vars: {[v.name for v in query_vars]}")
                    # この場合、空の解 {} を返すべきか、何も返さないべきか。
                    # Prologでは通常、変数が束縛されない解は表示されない。
                    # しかし、テストケースが {} を期待している場合がある。
                    # ここでは、束縛がなければ解として数えないようにする。
                    # ただし、`sum_list_basic([], Sum)` で `[{}]` が返る問題は、
                    # `query_vars` が空だったことが原因。`query_vars` が正しく設定されれば、
                    # `current_bindings` が `{Sum: 0}` となるはず。

            elif isinstance(solution_item, TRUE) or isinstance(solution_item, Term): # 変数なしクエリで成功した場合
                logger.debug("Runtime.query: Yielding empty bindings for ground query success: {}")
                solution_count +=1
                yield {} # 空の辞書を解として返す
        logger.info(f"Runtime.query for '{query_str}' finished. Total solutions yielded: {solution_count}")


    def register_function(self, func, predicate, arity):
        logger.debug(f"Runtime.register_function: func={func}, predicate='{predicate}', arity={arity}")
        args = []
        for i in range(arity):
            args.append(f'placeholder_{i}')
        tf = TermFunction(func, predicate, *args)
        self.rules.append(Rule(tf, TRUE()))

    def insert_rule_left(self, entry):
        if isinstance(entry, Term):
            entry = Rule(entry, TRUE())
        for i, item in enumerate(self.rules):
            if entry.head.pred == item.head.pred:
                self.rules.insert(i, entry)
                return
        self.rules.append(entry)

    def insert_rule_right(self, entry):
        if isinstance(entry, Term):
            entry = Rule(entry, TRUE())
        last_index = -1
        for i, item in enumerate(self.rules):
            if entry.head.pred == item.head.pred:
                last_index = i

        if last_index == -1:
            self.rules.append(entry)
        else:
            self.rules.insert(last_index + 1, entry)

    def remove_rule(self, rule):
        if isinstance(rule, Term):
            rule = Rule(rule, TRUE())
        for i, item in enumerate(self.rules):
            if (
                rule.head.pred == item.head.pred
                and len(rule.head.args) == len(item.head.args)
                and all(
                    [
                        (
                            x.pred == y.pred
                            if isinstance(x, Term)
                            and isinstance(y, Term)  # noqa
                            else (
                                x.name == y.name
                                if isinstance(x, Variable)
                                and isinstance(y, Variable)  # noqa
                                else False
                            )
                        )
                        for x, y in zip(rule.head.args, item.head.args)
                    ]
                )
            ):
                self.rules.pop(i)
                break

    def all_rules(self, query):
        rules = self.rules[:]
        if isinstance(query, Rule):
            return rules + [query]
        return rules

    def evaluate_rules(self, query_rule_obj, goal_term): 
        logger.debug(f"Runtime.evaluate_rules: query_rule_obj={query_rule_obj}, goal_term={goal_term}")
        for db_rule in self.all_rules(query_rule_obj):
            logger.debug(f"Runtime.evaluate_rules: Trying DB rule: {db_rule}")

            match_bindings = db_rule.head.match(goal_term)
            logger.debug(f"Runtime.evaluate_rules: Match attempt of {db_rule.head} with {goal_term} -> bindings: {match_bindings}")

            if match_bindings is not None:
                logger.debug(f"Runtime.evaluate_rules: Match success. DB rule head: {db_rule.head}, Goal: {goal_term}")
                substituted_rule_head = db_rule.head.substitute(match_bindings)
                substituted_rule_body = db_rule.body.substitute(match_bindings)
                logger.debug(f"Runtime.evaluate_rules: Substituted DB rule head: {substituted_rule_head}, body: {substituted_rule_body}")

                if isinstance(substituted_rule_body, Arithmetic):
                    logger.debug(f"Runtime.evaluate_rules: Body is Arithmetic: {substituted_rule_body}")
                    if hasattr(substituted_rule_body, 'var') and isinstance(substituted_rule_body.var, Variable):
                        var_to_bind = substituted_rule_body.var
                        value = substituted_rule_body.evaluate()
                        
                        final_head_for_arith = substituted_rule_head.substitute({var_to_bind: value})
                        logger.debug(f"Runtime.evaluate_rules: Arithmetic body evaluated. Yielding: {final_head_for_arith}")
                        yield final_head_for_arith
                    else:
                        logger.warning(f"Runtime.evaluate_rules: Arithmetic body {substituted_rule_body} does not have expected 'var' attribute.")

                else: 
                    logger.debug(f"Runtime.evaluate_rules: Body is not Arithmetic. Calling body.query for: {substituted_rule_body}")
                    for body_solution_item in substituted_rule_body.query(self):
                        logger.debug(f"Runtime.evaluate_rules: Item from body.query: {body_solution_item}")
                        if isinstance(body_solution_item, CUT): 
                            logger.debug("Runtime.evaluate_rules: CUT signal received from body.query. Yielding CUT and returning.")
                            yield body_solution_item
                            return
                        
                        if not isinstance(body_solution_item, FALSE):
                            # body_solution_item は、具体化された body の一部または全体。
                            # substituted_rule_head と body_solution_item から最終的な束縛をマージする必要がある。
                            # body_solution_item が具体化された body 全体の場合、
                            # substituted_rule_body.match(body_solution_item) で body 内の変数の束縛を得る。
                            bindings_from_body = substituted_rule_body.match(body_solution_item)
                            if bindings_from_body is None: bindings_from_body = {}

                            # match_bindings (headとgoalのマッチ) と bindings_from_body (bodyの実行結果) をマージ
                            # ただし、変数のスコープに注意。
                            # substituted_rule_head は既に match_bindings で部分的に具体化されている。
                            # ここで必要なのは、body_solution_item に含まれる情報で substituted_rule_head をさらに具体化すること。
                            
                            # substituted_rule_head を body_solution_item (の束縛) でさらに具体化
                            final_solution_head = substituted_rule_head.substitute(bindings_from_body)
                            
                            logger.debug(f"Runtime.evaluate_rules: Yielding successful head: {final_solution_head}")
                            yield final_solution_head
                        elif isinstance(body_solution_item, FALSE):
                            logger.debug("Runtime.evaluate_rules: Body solution was FALSE. Trying next body solution or backtracking.")
            else:
                logger.debug(f"Runtime.evaluate_rules: Match failed for DB rule {db_rule.head} with goal {goal_term}")
        logger.debug(f"Runtime.evaluate_rules: All DB rules tried for goal_term={goal_term}. Finished.")

    def execute(self, query_obj): 
        logger.debug(f"Runtime.execute called with query_obj: {query_obj}")
        goal_to_evaluate = query_obj
        if isinstance(query_obj, Arithmetic):
            logger.debug(f"Runtime.execute: query_obj is Arithmetic: {query_obj}")
            if hasattr(query_obj, 'var') and isinstance(query_obj.var, Variable):
                value = query_obj.evaluate()
                logger.debug(f"Runtime.execute: Arithmetic {query_obj} (with var) evaluated to {value}. Yielding value.")
                yield value 
            else: 
                value = query_obj.evaluate()
                logger.debug(f"Runtime.execute: Arithmetic {query_obj} (ground) evaluated to {value}. Yielding value.")
                yield value

        else: 
            if isinstance(query_obj, Rule):
                # parsed_query が Rule(Term("##", Vars), BodyConjunction) の場合、
                # goal_to_evaluate は Term("##", Vars) ではなく、BodyConjunction を評価し、
                # その結果を Term("##", Vars) に適用して返す必要がある。
                # evaluate_rules は、与えられた goal_term (ここでは query_obj.head) とDBのルールヘッドをマッチさせる。
                # そして、DBルールのボディを実行し、その結果をDBルールヘッドに適用して返す。
                # クエリ Rule(H, B) の場合、B を実行し、その結果を H に適用して返す。
                
                # query_obj が Rule(H, B) の場合、B を実行し、その結果の束縛を H に適用する。
                # H が ##(Vars) の場合、最終的に ##(BoundVars) が返る。
                logger.debug(f"Runtime.execute: query_obj is Rule. Head: {query_obj.head}, Body: {query_obj.body}")
                # query_obj.body を実行し、その各解 (束縛のセット) を query_obj.head に適用する
                for body_solution_bindings_or_term in query_obj.body.query(self): # body.query は解の項または束縛を返す
                    if isinstance(body_solution_bindings_or_term, FALSE):
                        continue
                    if isinstance(body_solution_bindings_or_term, CUT): # types.CUT
                        yield CUT()
                        return

                    # body_solution_bindings_or_term は、具体化された body の項であると期待される。
                    # (Conjunction.query は substitute(bindings) された項を返す)
                    # この具体化された body 項と、元の query_obj.body (変数を含む) をマッチさせて束縛を得る。
                    bindings_from_body = query_obj.body.match(body_solution_bindings_or_term)
                    if bindings_from_body is None: bindings_from_body = {}
                    
                    # 得られた束縛を query_obj.head に適用する
                    yield query_obj.head.substitute(bindings_from_body)

            else: # query_obj is a simple Term (e.g. a fact `p(a)` used as a query, or a subgoal term)
                logger.debug(f"Runtime.execute: query_obj is Term: {query_obj}. Goal to evaluate is same.")
                goal_to_evaluate = query_obj
                yield from self.evaluate_rules(query_obj, goal_to_evaluate) # query_obj はここでは単なる Term
        logger.debug(f"Runtime.execute for query_obj: {query_obj} finished.")
