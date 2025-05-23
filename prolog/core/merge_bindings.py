from prolog.core.types import Variable # Variable 繧偵う繝ｳ繝昴・繝・
from prolog.util.logger import logger

def merge_bindings(bindings1, bindings2):
    logger.debug(f"merge_bindings called with bindings1: {bindings1}, bindings2: {bindings2}")
    if bindings1 is None or bindings2 is None:
        logger.debug("merge_bindings: One or both bindings are None, returning None.")
        return None

    merged_bindings = bindings1.copy()
    logger.debug(f"merge_bindings: Initial merged_bindings (copy of bindings1): {merged_bindings}")
    
    # 螟画焚繝槭ャ繝斐Φ繧ｰ隗｣豎ｺ縺ｮ縺溘ａ縺ｮ陬懷勧髢｢謨ｰ
    def resolve_binding_chain(var, bindings, visited=None):
        """螟画焚縺ｮ譚溽ｸ帙メ繧ｧ繝ｼ繝ｳ繧偵◆縺ｩ縺｣縺ｦ譛邨ら噪縺ｪ蛟､繧貞叙蠕・""
        if visited is None:
            visited = set()
            
        if var in visited:
            logger.warning(f"resolve_binding_chain: Circular reference detected for {var}. Returning var itself.")
            return var  # 蠕ｪ迺ｰ繧呈､懷・
            
        visited.add(var)
        
        value = bindings.get(var, None)
        if value is None or not isinstance(value, Variable):
            return value if value is not None else var
            
        return resolve_binding_chain(value, bindings, visited)

    # 螟画焚繧ｰ繝ｩ繝輔・菴懈・
    var_graph = {}

    # bindings1 縺九ｉ繧ｰ繝ｩ繝輔ｒ蛻晄悄讒狗ｯ・
    for var, val in bindings1.items():
        if isinstance(var, Variable) and isinstance(val, Variable):
            if var not in var_graph:
                var_graph[var] = set()
            if val not in var_graph:
                var_graph[val] = set()
            var_graph[var].add(val)
            var_graph[val].add(var)
            logger.debug(f"merge_bindings: var_graph from b1: added edge {var}-{val}")

    # bindings2 繧堤ｵｱ蜷医＠縲√げ繝ｩ繝輔ｒ諡｡蠑ｵ
    for var_b, val_b in bindings2.items():
        if isinstance(var_b, Variable) and isinstance(val_b, Variable):
            # var_b 縺ｨ val_b 繧貞酔蛟､縺ｨ縺励※繧ｰ繝ｩ繝輔↓霑ｽ蜉
            if var_b not in var_graph:
                var_graph[var_b] = set()
            if val_b not in var_graph:
                var_graph[val_b] = set()
            var_graph[var_b].add(val_b)
            var_graph[val_b].add(var_b)
            logger.debug(f"merge_bindings: var_graph from b2 (V-V): added edge {var_b}-{val_b}")

        # merged_bindings 縺ｮ譖ｴ譁ｰ繝ｭ繧ｸ繝・け
        if var_b in merged_bindings:
            val_a = merged_bindings[var_b]
            
            if isinstance(val_a, Variable) and isinstance(val_b, Variable):
                # 譌｢縺ｫ繧ｰ繝ｩ繝輔↓霑ｽ蜉縺輔ｌ縺ｦ縺・ｋ縺ｯ縺・
                pass
            elif isinstance(val_a, Variable): # val_b 縺ｯ螳壽焚
                # val_a 繧・val_b 縺ｫ譚溽ｸ・
                merged_bindings[val_a] = val_b
                logger.debug(f"merge_bindings: b2 conflict processing (V-C): {val_a} -> {val_b}")
            elif isinstance(val_b, Variable): # val_a 縺ｯ螳壽焚
                # val_b 繧・val_a 縺ｫ譚溽ｸ・
                merged_bindings[val_b] = val_a
                logger.debug(f"merge_bindings: b2 conflict processing (C-V): {val_b} -> {val_a}")
            elif val_a != val_b: # 荳｡譁ｹ螳壽焚縺ｧ蛟､縺檎焚縺ｪ繧・
                logger.debug(f"merge_bindings: Conflict! {var_b} is bound to {val_a} in b1 and {val_b} in b2. Returning None.")
                return None # 遏帷崟
        else:
            # var_b 縺・bindings1 縺ｫ蟄伜惠縺励↑縺九▲縺溷ｴ蜷医∵眠縺励＞譚溽ｸ帙→縺励※霑ｽ蜉
            merged_bindings[var_b] = val_b
            logger.debug(f"merge_bindings: b2 new binding: {var_b} -> {val_b}")

    # 螟画焚繧ｰ繝ｩ繝輔°繧画怙邨ら噪縺ｪ merged_bindings 繧呈ｧ狗ｯ・
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
            # 縺薙・繧ｳ繝ｳ繝昴・繝阪Φ繝亥・縺ｮ螟画焚縺ｯ縺吶∋縺ｦ蜷悟､
            # 繧ｳ繝ｳ繝昴・繝阪Φ繝亥・縺ｫ螳壽焚縺ｸ縺ｮ譚溽ｸ帙′縺ゅｋ縺狗｢ｺ隱・
            constant_binding_value = None
            
            for var_in_component in component:
                # merged_bindings 縺九ｉ逶ｴ謗･隗｣豎ｺ縺輔ｌ縺溷､繧堤｢ｺ隱・
                resolved_value_for_component_var = resolve_binding_chain(var_in_component, merged_bindings)
                
                if resolved_value_for_component_var is not None and not isinstance(resolved_value_for_component_var, Variable):
                    if constant_binding_value is not None and constant_binding_value != resolved_value_for_component_var:
                        logger.debug(f"merge_bindings: Conflict in component {component}. Var {var_in_component} (resolved to {resolved_value_for_component_var}) conflicts with existing constant {constant_binding_value}. Returning None.")
                        return None # 遏帷崟
                    constant_binding_value = resolved_value_for_component_var
                    logger.debug(f"merge_bindings: var_graph component {component}: found constant binding via {var_in_component} -> {constant_binding_value}")

            if constant_binding_value is not None:
                # 繧ｳ繝ｳ繝昴・繝阪Φ繝亥・縺ｮ蜈ｨ螟画焚繧偵％縺ｮ螳壽焚縺ｫ譚溽ｸ・
                for var_in_component in component:
                    final_merged_bindings[var_in_component] = constant_binding_value
                logger.debug(f"merge_bindings: var_graph component {component}: all bound to constant {constant_binding_value}")
            else:
                # 繧ｳ繝ｳ繝昴・繝阪Φ繝亥・縺ｮ蜈ｨ縺ｦ縺ｮ螟画焚髢薙↓蜿梧婿蜷第據邵帙ｒ險ｭ螳・
                # 莉｣陦ｨ蜈・→縺励※縲√さ繝ｳ繝昴・繝阪Φ繝亥・縺ｮ譛蛻昴・隕∫ｴ・医∪縺溘・繧ｽ繝ｼ繝医＆繧後◆譛蛻昴・隕∫ｴ・峨ｒ驕ｸ縺ｶ
                representative = sorted(list(component), key=lambda v: v.name)[0] # 蜷榊燕縺ｧ繧ｽ繝ｼ繝医＠縺ｦ荳雋ｫ諤ｧ繧剃ｿ昴▽
                for v_in_comp in component:
                    if v_in_comp != representative:
                         final_merged_bindings[v_in_comp] = representative
                # 莉｣陦ｨ蜈・・霄ｫ繧ゆｽ輔°縺ｫ譚溽ｸ帙＆繧後ｋ蠢・ｦ√′縺ゅｋ蝣ｴ蜷医′縺ゅｋ縺後√％縺薙〒縺ｯ莉悶・螟画焚縺ｸ縺ｮ蜿ら・縺ｧ蜊∝・
                # 蠢・ｦ√〒縺ゅｌ縺ｰ縲∽ｻ｣陦ｨ蜈・ｒ閾ｪ霄ｫ縺ｫ譚溽ｸ帙☆繧・final_merged_bindings[representative] = representative 繧よ､懆ｨ・
                logger.debug(f"merge_bindings: var_graph component {component}: all bound to representative {representative}")


    # 譌｢蟄倥・ merged_bindings 縺ｮ縺・■縲」ar_graph 縺ｫ蜷ｫ縺ｾ繧後↑縺・據邵幢ｼ井ｸｻ縺ｫ螳壽焚縺ｸ縺ｮ逶ｴ謗･譚溽ｸ幢ｼ峨ｒfinal縺ｫ繧ｳ繝斐・
    for k, v in merged_bindings.items():
        is_k_in_graph = isinstance(k, Variable) and k in var_graph
        
        if not is_k_in_graph: # 繧ｭ繝ｼ縺後げ繝ｩ繝輔↓縺ｪ縺・､画焚縲√∪縺溘・髱槫､画焚
            if k not in final_merged_bindings: # 縺ｾ縺 final 縺ｫ縺ｪ縺代ｌ縺ｰ霑ｽ蜉
                 # 縺薙％縺ｧ k 縺・Variable 縺ｮ蝣ｴ蜷医√◎縺ｮ譚溽ｸ帙メ繧ｧ繝ｼ繝ｳ繧定ｧ｣豎ｺ縺吶ｋ
                 if isinstance(k, Variable):
                     final_value = resolve_binding_chain(k, merged_bindings)
                     if final_value is not None: # None 縺ｧ縺ｪ縺・ｴ蜷医・縺ｿ譖ｴ譁ｰ
                         final_merged_bindings[k] = final_value
                     # else: k 縺ｯ譚溽ｸ帙＆繧後※縺・↑縺・・縺ｧ縲’inal_merged_bindings 縺ｫ縺ｯ霑ｽ蜉縺励↑縺・
                 else: # k 縺碁撼螟画焚縺ｮ蝣ｴ蜷茨ｼ磯壼ｸｸ縺ｯ縺ゅｊ縺医↑縺・′蠢ｵ縺ｮ縺溘ａ・・
                     final_merged_bindings[k] = v
            # else: k 縺ｯ譌｢縺ｫ final_merged_bindings 縺ｧ蜃ｦ逅・＆繧後※縺・ｋ・医げ繝ｩ繝慕ｵ檎罰縺ｪ縺ｩ・・

    logger.debug(f"merge_bindings: Final merged_bindings from graph and non-graph part: {final_merged_bindings}")
    return final_merged_bindings
