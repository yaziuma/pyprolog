from prolog.core_types import Variable # Variable をインポート
from prolog.logger import logger

def merge_bindings(bindings1, bindings2):
    logger.debug(f"merge_bindings called with bindings1: {bindings1}, bindings2: {bindings2}")
    if bindings1 is None or bindings2 is None:
        logger.debug("merge_bindings: One or both bindings are None, returning None.")
        return None

    merged_bindings = bindings1.copy()
    logger.debug(f"merge_bindings: Initial merged_bindings (copy of bindings1): {merged_bindings}")
    
    # 変数マッピング解決のための補助関数
    def resolve_binding_chain(var, bindings, visited=None):
        """変数の束縛チェーンをたどって最終的な値を取得"""
        if visited is None:
            visited = set()
            
        if var in visited:
            logger.warning(f"resolve_binding_chain: Circular reference detected for {var}. Returning var itself.")
            return var  # 循環を検出
            
        visited.add(var)
        
        value = bindings.get(var, None)
        if value is None or not isinstance(value, Variable):
            return value if value is not None else var
            
        return resolve_binding_chain(value, bindings, visited)

    # 変数グラフの作成
    var_graph = {}

    # bindings1 からグラフを初期構築
    for var, val in bindings1.items():
        if isinstance(var, Variable) and isinstance(val, Variable):
            if var not in var_graph:
                var_graph[var] = set()
            if val not in var_graph:
                var_graph[val] = set()
            var_graph[var].add(val)
            var_graph[val].add(var)
            logger.debug(f"merge_bindings: var_graph from b1: added edge {var}-{val}")

    # bindings2 を統合し、グラフを拡張
    for var_b, val_b in bindings2.items():
        if isinstance(var_b, Variable) and isinstance(val_b, Variable):
            # var_b と val_b を同値としてグラフに追加
            if var_b not in var_graph:
                var_graph[var_b] = set()
            if val_b not in var_graph:
                var_graph[val_b] = set()
            var_graph[var_b].add(val_b)
            var_graph[val_b].add(var_b)
            logger.debug(f"merge_bindings: var_graph from b2 (V-V): added edge {var_b}-{val_b}")

        # merged_bindings の更新ロジック
        if var_b in merged_bindings:
            val_a = merged_bindings[var_b]
            
            if isinstance(val_a, Variable) and isinstance(val_b, Variable):
                # 既にグラフに追加されているはず
                pass
            elif isinstance(val_a, Variable): # val_b は定数
                # val_a を val_b に束縛
                merged_bindings[val_a] = val_b
                logger.debug(f"merge_bindings: b2 conflict processing (V-C): {val_a} -> {val_b}")
            elif isinstance(val_b, Variable): # val_a は定数
                # val_b を val_a に束縛
                merged_bindings[val_b] = val_a
                logger.debug(f"merge_bindings: b2 conflict processing (C-V): {val_b} -> {val_a}")
            elif val_a != val_b: # 両方定数で値が異なる
                logger.debug(f"merge_bindings: Conflict! {var_b} is bound to {val_a} in b1 and {val_b} in b2. Returning None.")
                return None # 矛盾
        else:
            # var_b が bindings1 に存在しなかった場合、新しい束縛として追加
            merged_bindings[var_b] = val_b
            logger.debug(f"merge_bindings: b2 new binding: {var_b} -> {val_b}")

    # 変数グラフから最終的な merged_bindings を構築
    visited_nodes = set()
    final_merged_bindings = {}

    for node in var_graph:
        if node not in visited_nodes:
            component = set()
            q = [node]
            head = 0
            while head < len(q):
                curr = q[head]
                head += 1
                if curr not in visited_nodes:
                    visited_nodes.add(curr)
                    component.add(curr)
                    if curr in var_graph:
                        for neighbor in var_graph[curr]:
                            if neighbor not in visited_nodes:
                                q.append(neighbor)
            
            logger.debug(f"merge_bindings: var_graph component found: {component}")
            # このコンポーネント内の変数はすべて同値
            # コンポーネント内に定数への束縛があるか確認
            constant_binding_value = None
            
            for var_in_component in component:
                # merged_bindings から直接解決された値を確認
                resolved_value_for_component_var = resolve_binding_chain(var_in_component, merged_bindings)
                
                if resolved_value_for_component_var is not None and not isinstance(resolved_value_for_component_var, Variable):
                    if constant_binding_value is not None and constant_binding_value != resolved_value_for_component_var:
                        logger.debug(f"merge_bindings: Conflict in component {component}. Var {var_in_component} (resolved to {resolved_value_for_component_var}) conflicts with existing constant {constant_binding_value}. Returning None.")
                        return None # 矛盾
                    constant_binding_value = resolved_value_for_component_var
                    logger.debug(f"merge_bindings: var_graph component {component}: found constant binding via {var_in_component} -> {constant_binding_value}")

            if constant_binding_value is not None:
                # コンポーネント内の全変数をこの定数に束縛
                for var_in_component in component:
                    final_merged_bindings[var_in_component] = constant_binding_value
                logger.debug(f"merge_bindings: var_graph component {component}: all bound to constant {constant_binding_value}")
            else:
                # コンポーネント内の全ての変数間に双方向束縛を設定
                # 代表元として、コンポーネント内の最初の要素（またはソートされた最初の要素）を選ぶ
                representative = sorted(list(component), key=lambda v: v.name)[0] # 名前でソートして一貫性を保つ
                for v_in_comp in component:
                    if v_in_comp != representative:
                         final_merged_bindings[v_in_comp] = representative
                # 代表元自身も何かに束縛される必要がある場合があるが、ここでは他の変数への参照で十分
                # 必要であれば、代表元を自身に束縛する final_merged_bindings[representative] = representative も検討
                logger.debug(f"merge_bindings: var_graph component {component}: all bound to representative {representative}")


    # 既存の merged_bindings のうち、var_graph に含まれない束縛（主に定数への直接束縛）をfinalにコピー
    for k, v in merged_bindings.items():
        is_k_in_graph = isinstance(k, Variable) and k in var_graph
        
        if not is_k_in_graph: # キーがグラフにない変数、または非変数
            if k not in final_merged_bindings: # まだ final になければ追加
                 # ここで k が Variable の場合、その束縛チェーンを解決する
                 if isinstance(k, Variable):
                     final_value = resolve_binding_chain(k, merged_bindings)
                     if final_value is not None: # None でない場合のみ更新
                         final_merged_bindings[k] = final_value
                     # else: k は束縛されていないので、final_merged_bindings には追加しない
                 else: # k が非変数の場合（通常はありえないが念のため）
                     final_merged_bindings[k] = v
            # else: k は既に final_merged_bindings で処理されている（グラフ経由など）

    logger.debug(f"merge_bindings: Final merged_bindings from graph and non-graph part: {final_merged_bindings}")
    return final_merged_bindings
