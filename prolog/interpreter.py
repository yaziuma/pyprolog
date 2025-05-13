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
                # ベースケース: 全てのゴールが成功
                # ここで self.substitute(bindings) を yield するのは、
                # 結合全体の置換結果を返すため。
                # しかし、Prolog の結合の成功は通常、最終的な束縛のセットで示される。
                # Runtime.query が最終的な束縛を構築するため、ここでは単に成功を示すか、
                # 最後のゴールの結果を伝播させる。
                # ここでは、仕様書には直接の指示がないため、既存の動作を維持しつつ、
                # 束縛のコピーと適用の修正に注力する。
                # 最終的な結果は Runtime.query で処理されるため、
                # ここでは成功した束縛を伴う何らかのシグナル (例えば TRUE() や具体的な項) を返す。
                # 既存のコードは res_sub (置換された結合) を返している。
                res_sub = self.substitute(bindings)
                logger.debug(f"Conjunction.solutions: base case, yielding substituted conjunction: {res_sub}")
                yield res_sub # または yield TRUE() や yield bindings など、設計による
            else:
                arg = self.args[index]
                logger.debug(f"Conjunction.solutions: processing arg[{index}] = {arg}")

                # バックトラックと変数束縛を正しく管理するために、束縛のコピーを作成 (仕様書 4)
                current_goal_bindings = bindings.copy() # このゴール評価用の束縛

                if self._is_cut(arg): 
                    logger.debug(f"Conjunction.solutions: arg is CUT {arg}")
                    # CUT の場合、現在の束縛で後続のゴールを評価
                    # CUT の実行自体が runtime.execute で処理される
                    for _ in runtime.execute(arg.substitute(current_goal_bindings)): # CUT の実行
                        logger.debug(f"Conjunction.solutions: Executing goals after CUT for bindings: {current_goal_bindings}")
                        yield from solutions(index + 1, current_goal_bindings) # CUT後のゴールへ
                        logger.debug("Conjunction.solutions: Yielding CUT signal after solutions for goals post-cut.")
                        yield CUT() # CUTシグナルを伝播
                        return 

                elif self._is_fail(arg): 
                    logger.debug(f"Conjunction.solutions: arg is FAIL {arg}, yielding FALSE")
                    yield FALSE()
                    # Failオブジェクトに対してquery()を呼び出す必要はない
                    return  # この結合パスには解がない - 失敗したため
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
                    # arg を評価する前に、現在の束縛 (current_goal_bindings) で置換する
                    substituted_arg = arg.substitute(current_goal_bindings)
                    logger.debug(f"Conjunction.solutions: Substituted arg for execution: {substituted_arg}")

                    for item in runtime.execute(substituted_arg): # substituted_arg を実行
                        logger.debug(f"Conjunction.solutions: item from runtime.execute({substituted_arg}): {item}")
                        if isinstance(item, FALSE): 
                            logger.debug("Conjunction.solutions: item is FALSE, this conjunction path fails for this item.")
                            continue # この解は失敗、次の解を試す (バックトラック)

                        if isinstance(item, CUT): 
                            logger.error("Conjunction.solutions: Unexpected CUT signal received from runtime.execute on a general term that is not a !.")
                            # CUT が execute から返ってきた場合、それを伝播させる
                            yield item 
                            return # この Conjunction の評価を終了

                        # item は解決された項 (例: p(a) )
                        # arg は元のゴール (例: p(X) )
                        # substituted_arg は束縛適用後のゴール (例: p(X) または p(Y) if X was bound to Y)
                        # ここで match するのは、元の arg と item
                        # そして、その結果を current_goal_bindings とマージする
                        match_result_for_arg = arg.match(item) # arg と item のマッチング
                        if match_result_for_arg is None:
                            # substituted_arg と item のマッチも試す (より具体的なケース)
                            match_result_for_arg = substituted_arg.match(item)

                        if match_result_for_arg is not None:
                            # 各ゴールの評価後に束縛の適用を確保 (仕様書 4)
                            # 新しい束縛と、このゴール評価開始時の束縛 (current_goal_bindings) をマージ
                            unified_bindings = merge_bindings(match_result_for_arg, current_goal_bindings)
                            logger.debug(f"Conjunction.solutions: unified bindings for arg '{arg}' (or '{substituted_arg}') and item '{item}': {unified_bindings} (from match: {match_result_for_arg}, original_for_goal: {current_goal_bindings})")
                            
                            if unified_bindings is not None:
                                logger.debug(f"Conjunction.solutions: proceeding to next arg with unified bindings: {unified_bindings}")
                                # 次のゴールに進む前に、統合された束縛を使用 (仕様書 4)
                                yield from solutions(index + 1, unified_bindings)
                            else:
                                logger.debug(f"Conjunction.solutions: unification (merge_bindings) failed after successful match for {arg}/{substituted_arg} and {item}. Trying next item.")
                        else:
                            logger.debug(f"Conjunction.solutions: match failed for {arg}/{substituted_arg} and {item}. Trying next item.")
                    
                    # このゴール (arg) に対する全ての解を試し終わったら、このパスは終了
                    logger.debug(f"Conjunction.solutions: runtime.execute for {substituted_arg} (from arg {arg}) exhausted for bindings {current_goal_bindings}.")
                    return # この return が重要。現在の arg で解が見つからなければバックトラック

        logger.debug("Conjunction.query: starting solutions generator with initial empty bindings")
        yield from solutions(0, {}) # 初期束縛は空

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
            query_vars = find_variables(parsed_query)

        seen_vars = set()
        unique_query_vars = []
        for var in query_vars:
            if var.name not in seen_vars:
                unique_query_vars.append(var)
                seen_vars.add(var.name)
        query_vars = unique_query_vars

        logger.debug(f"Runtime.query: Found variables in query: {[var.name for var in query_vars if var is not None]}")
        
        solution_count = 0
        for solution_item in self.execute(parsed_query): 
            logger.debug(f"Runtime.query: solution_item from execute: {solution_item}, type: {type(solution_item)}")
            
            if isinstance(solution_item, FALSE) or solution_item is None:
                logger.debug("Runtime.query: solution_item is FALSE or None, skipping.")
                continue
            if isinstance(solution_item, CUT):
                logger.warning("Runtime.query: CUT signal reached top-level query. This should ideally be handled internally.")
                break

            current_bindings = {}
            # 単一化の特殊ソリューションからバインディングを抽出
            if isinstance(solution_item, Term) and solution_item.pred == "=" and hasattr(solution_item, "bindings"):
                for var, val in solution_item.bindings.items():
                    if var in query_vars: # query_vars に含まれる変数のみを束縛対象とする
                        current_bindings[var] = val
                logger.debug(f"Runtime.query: Yielding bindings from unification: {current_bindings}")
                solution_count += 1
                yield current_bindings
                continue # 次のソリューションアイテムへ

            if query_vars:
                original_query_structure = parsed_query
                if isinstance(parsed_query, Rule) and parsed_query.head.pred == "##":
                    original_query_structure = parsed_query.head # クエリが ##(Vars) :- Body の場合、##(Vars) を使う

                if isinstance(solution_item, Term) and solution_item.pred == "##": # ##(Vars) 形式の解
                    if len(query_vars) == len(solution_item.args):
                        for i, var_obj in enumerate(query_vars):
                            current_bindings[var_obj] = solution_item.args[i]
                    else:
                        logger.error(f"Runtime.query: Mismatch in query_vars ({[v.name for v in query_vars]}) and solution_item.args ({solution_item.args}) for ## term")
                
                # 通常の項のマッチング (単一化以外のケース)
                elif isinstance(solution_item, Term) and isinstance(original_query_structure, Term):
                    match_result_bindings = original_query_structure.match(solution_item)
                    if match_result_bindings is not None:
                        for q_var in query_vars: # query_vars に含まれる変数のみを束縛対象とする
                            if q_var in match_result_bindings:
                                current_bindings[q_var] = match_result_bindings[q_var]
                    else:
                        # マッチしなかった場合でも、solution_item が TRUE なら空の束縛を返すことがある
                        # ただし、ここでは query_vars があるので、何らかの束縛が期待される
                        logger.warning(f"Runtime.query: Could not match original query structure {original_query_structure} with solution {solution_item}")
                
                # 束縛が見つかったか、あるいは元々変数がなかった場合（後者は通常下のelif TRUEで処理されるが念のため）
                if current_bindings or not query_vars: # not query_vars は ground query の成功を示す
                    logger.debug(f"Runtime.query: Yielding bindings: {current_bindings}")
                    solution_count +=1
                    yield current_bindings
            
            elif isinstance(solution_item, TRUE): # prolog.types.TRUE の場合 (変数なしクエリの成功など)
                logger.debug("Runtime.query: TRUE result, yielding empty bindings {}")
                solution_count += 1
                yield {} # 空の辞書を返す
            elif isinstance(solution_item, dict): # dictオブジェクトが直接返された場合
                logger.debug(f"Runtime.query: Dict solution received: {solution_item}")
                solution_count += 1
                yield solution_item
            # 変数なしクエリで具体的な項が返ってきた場合も成功とみなし、空の束縛を返す
            elif isinstance(solution_item, Term) and not query_vars:
                logger.debug("Runtime.query: Term result for ground query (no vars), yielding empty bindings {}")
                solution_count +=1
                yield {}
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

        # '=' 演算子の特別処理 (仕様書 2)
        if isinstance(goal_term, Term) and goal_term.pred == '=' and len(goal_term.args) == 2:
            lhs, rhs = goal_term.args
            match_result = lhs.match(rhs)
            if match_result is not None:
                # 単一化に成功した場合、TRUEを返す代わりに適用されたバインディングを含む
                # 特殊なソリューションオブジェクトを返す
                special_solution = Term("=", lhs.substitute(match_result), rhs.substitute(match_result))
                special_solution.bindings = match_result  # バインディング情報を保持
                yield special_solution
            return  # 単一化の処理が完了したら他のルールを試さない

        for db_rule in self.all_rules(query_rule_obj):
            logger.debug(f"Runtime.evaluate_rules: Trying DB rule: {db_rule}")

            match_bindings = db_rule.head.match(goal_term)
            logger.debug(f"Runtime.evaluate_rules: Match attempt of {db_rule.head} with {goal_term} -> bindings: {match_bindings}")

            if match_bindings is not None:
                logger.debug(f"Runtime.evaluate_rules: Match success. DB rule head: {db_rule.head}, Goal: {goal_term}")
                substituted_rule_head = db_rule.head.substitute(match_bindings)
                substituted_rule_body = db_rule.body.substitute(match_bindings)
                logger.debug(f"Runtime.evaluate_rules: Substituted DB rule head: {substituted_rule_head}, body: {substituted_rule_body}")

                # ルールのボディで '=' が使われるケースの特別処理 (仕様書 5)
                if isinstance(substituted_rule_body, Term) and substituted_rule_body.pred == '=':
                    lhs, rhs = substituted_rule_body.args
                    # ここでの match_result は、ボディの '=' が成功した場合の束縛
                    body_match_result = lhs.match(rhs)
                    if body_match_result is not None:
                        # 単一化が成功したら、その束縛をヘッドに適用して返す
                        # 元の match_bindings (ヘッドとゴールのマッチ) と body_match_result (ボディの=のマッチ)
                        # をマージする必要があるかもしれません。
                        # しかし、仕様書では match_result (おそらく body_match_result を指す) のみを使用しています。
                        # これは、ボディの '=' がヘッドの変数を束縛する場合を想定している可能性があります。
                        # 例: p(X) :- X = a.  goal p(Y) -> Y=a
                        # ここでは、仕様書通り body_match_result を使用します。
                        # 注意: この match_result は、元の goal_term と rule.head のマッチング (match_bindings)
                        # によって既に束縛された変数をさらに束縛する可能性があります。
                        # 既存の束縛と矛盾しないようにマージするのがより堅牢ですが、
                        # 仕様書は substituted_rule_head.substitute(match_result) となっています。
                        # ここでの match_result は body_match_result を指すと解釈します。
                        final_head = substituted_rule_head.substitute(body_match_result)
                        # さらに、元の goal_term とのマッチングで得られた束縛 (match_bindings) も考慮に入れるべきです。
                        # 例えば、goal が p(A) で、ルールが p(X) :- X = b. の場合、
                        # match_bindings は {X: A}。body_match_result は {X: b} (もしXが未束縛なら)。
                        # この場合、A=b となるべきです。
                        # より正確には、マージされた束縛を適用すべきです。
                        # merged_bindings_for_head = merge_bindings(match_bindings, body_match_result)
                        # if merged_bindings_for_head is not None:
                        #    yield substituted_rule_head.substitute(merged_bindings_for_head)
                        # しかし、仕様書は単純な substitute(match_result) です。
                        # ここでは、仕様書に従い、body_match_result のみで置換します。
                        # これが意図した動作であると仮定します。
                        yield final_head
                    return # ボディが '=' の場合は、その評価で終了

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
                            bindings_from_body = substituted_rule_body.match(body_solution_item)
                            if bindings_from_body is None: bindings_from_body = {}
                            
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
    
        # TRUE と Fail オブジェクトの特別な処理
        if isinstance(query_obj, TRUE): # prolog.types.TRUE
            logger.debug("Runtime.execute: query_obj is TRUE, calling TRUE.query()")
            yield from query_obj.query(self)  # TRUE.queryメソッドを呼び出す
            return
        
        if isinstance(query_obj, Fail): # prolog.builtins.Fail
            logger.debug("Runtime.execute: query_obj is Fail, yielding nothing (failure)")
            return  # 何もyieldせずにリターン = 失敗
            
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
                logger.debug(f"Runtime.execute: query_obj is Rule. Head: {query_obj.head}, Body: {query_obj.body}")
                for body_solution_bindings_or_term in query_obj.body.query(self): 
                    if isinstance(body_solution_bindings_or_term, FALSE):
                        continue
                    if isinstance(body_solution_bindings_or_term, CUT): 
                        yield CUT()
                        return

                    bindings_from_body = query_obj.body.match(body_solution_bindings_or_term)
                    if bindings_from_body is None: bindings_from_body = {}
                    
                    yield query_obj.head.substitute(bindings_from_body)

            else: 
                logger.debug(f"Runtime.execute: query_obj is Term: {query_obj}. Goal to evaluate is same.")
                goal_to_evaluate = query_obj
                yield from self.evaluate_rules(query_obj, goal_to_evaluate) 
        logger.debug(f"Runtime.execute for query_obj: {query_obj} finished.")
