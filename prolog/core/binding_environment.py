from prolog.core.types import Variable

class BindingEnvironment:
    """螟画焚繝舌う繝ｳ繝・ぅ繝ｳ繧ｰ繧剃ｸ蜈・ｮ｡逅・☆繧狗腸蠅・

    Union-Find繧｢繝ｫ繧ｴ繝ｪ繧ｺ繝繧剃ｽｿ逕ｨ縺励※縲∝､画焚蜷悟｣ｫ縺ｮ邨ｱ蜷医→蜉ｹ邇・噪縺ｪ讀懃ｴ｢繧呈署萓帙＠縺ｾ縺吶・
    繝舌ャ繧ｯ繝医Λ繝・け縺ｮ縺溘ａ縺ｮ繝√ぉ繝・け繝昴う繝ｳ繝域ｩ溯・繧ょ性縺ｾ繧後※縺・∪縺吶・
    """
    
    def __init__(self):
        # 螟画焚縺九ｉ莉｣陦ｨ蜈・､画焚縺ｸ縺ｮ繝槭ャ繝斐Φ繧ｰ
        self.parent = {}
        # 螟画焚縺九ｉ蜈ｷ菴鍋噪縺ｪ蛟､縺ｸ縺ｮ繝槭ャ繝斐Φ繧ｰ
        self.value = {}
        # 繝舌ャ繧ｯ繝医Λ繝・け逕ｨ縺ｮ繝医Ξ繧､繝ｫ・亥､画峩縺輔ｌ縺溷､画焚縺ｮ繧ｹ繧ｿ繝・け・・
        self.trail = []
        # 繝医Ξ繧､繝ｫ縺ｮ繝√ぉ繝・け繝昴う繝ｳ繝茨ｼ医ヰ繝・け繝医Λ繝・け菴咲ｽｮ・・
        self.trail_marks = []
        # 繧ｹ繧ｳ繝ｼ繝悠D逕ｨ縺ｮ繧ｫ繧ｦ繝ｳ繧ｿ繝ｼ
        self._next_scope_id = 0
        
    def get_next_scope_id(self):
        """荳諢上・繧ｹ繧ｳ繝ｼ繝悠D繧堤函謌舌＠縺ｦ霑斐☆"""
        scope_id = self._next_scope_id
        self._next_scope_id += 1
        return scope_id

    def find(self, var):
        """螟画焚縺ｮ莉｣陦ｨ蜈・ｒ讀懃ｴ｢縺吶ｋ・医ヱ繧ｹ蝨ｧ邵ｮ繧｢繝ｫ繧ｴ繝ｪ繧ｺ繝・・

        Args:
            var: 讀懃ｴ｢縺吶ｋ螟画焚

        Returns:
            螟画焚縺ｮ莉｣陦ｨ蜈・ｼ郁・霄ｫ縺御ｻ｣陦ｨ蜈・・蝣ｴ蜷医・閾ｪ霄ｫ・・
        """
        if not isinstance(var, Variable):
            return var
            
        # 譛ｪ逋ｻ骭ｲ縺ｮ螟画焚縺ｯ閾ｪ霄ｫ縺御ｻ｣陦ｨ蜈・
        if var not in self.parent:
            self.parent[var] = var
            return var
            
        # 繝代せ蝨ｧ邵ｮ・壽､懃ｴ｢荳ｭ縺ｫ騾夐℃縺励◆繝弱・繝峨・隕ｪ繧堤峩謗･繝ｫ繝ｼ繝医↓險ｭ螳・
        if self.parent[var] != var:
            self.parent[var] = self.find(self.parent[var])
        return self.parent[var]
        
    def unify(self, var1, var2):
        """莠後▽縺ｮ螟画焚繧貞腰荳蛹悶☆繧・

        Args:
            var1: 蜊倅ｸ蛹悶☆繧句､画焚1
            var2: 蜊倅ｸ蛹悶☆繧句､画焚2

        Returns:
            bool: 蜊倅ｸ蛹悶↓謌仙粥縺励◆縺九←縺・°
        """
        # 螟画焚莉･螟悶・繧ｪ繝悶ず繧ｧ繧ｯ繝医・蝣ｴ蜷医・逶ｴ謗･豈碑ｼ・
        if not isinstance(var1, Variable) and not isinstance(var2, Variable):
            return var1 == var2
            
        # 莉｣陦ｨ蜈・ｒ隕九▽縺代ｋ
        root1 = self.find(var1)
        root2 = self.find(var2)
        
        # 縺吶〒縺ｫ蜷後§莉｣陦ｨ蜈・↑繧画・蜉・
        if root1 == root2:
            return True
            
        # 荳｡譁ｹ縺悟､画焚縺ｮ蝣ｴ蜷医・邨ｱ蜷・
        if isinstance(root1, Variable) and isinstance(root2, Variable):
            self._record_trail(root1)  # 繝舌ャ繧ｯ繝医Λ繝・け逕ｨ縺ｫ險倬鹸
            self.parent[root1] = root2
            return True
            
        # 荳譁ｹ縺悟､画焚縲∽ｸ譁ｹ縺悟､縺ｮ蝣ｴ蜷・
        if isinstance(root1, Variable):
            self._record_trail(root1)  # 繝舌ャ繧ｯ繝医Λ繝・け逕ｨ縺ｫ險倬鹸
            self.value[root1] = root2
            return True
            
        if isinstance(root2, Variable):
            self._record_trail(root2)  # 繝舌ャ繧ｯ繝医Λ繝・け逕ｨ縺ｫ險倬鹸
            self.value[root2] = root1
            return True
            
        # 荳｡譁ｹ縺悟､縺ｮ蝣ｴ蜷医・遲峨＠縺・°縺ｩ縺・°縺ｧ蛻､螳・
        return root1 == root2
        
    def get_value(self, var):
        """螟画焚縺ｮ蛟､繧貞叙蠕励☆繧・

        Args:
            var: 蛟､繧貞叙蠕励☆繧句､画焚

        Returns:
            螟画焚縺ｮ蛟､・医ヰ繧､繝ｳ繝・ぅ繝ｳ繧ｰ縺後↑縺代ｌ縺ｰ螟画焚閾ｪ霄ｫ・・
        """
        if not isinstance(var, Variable):
            return var
            
        root = self.find(var)
        return self.value.get(root, root)
        
    def _record_trail(self, var):
        """繝舌ャ繧ｯ繝医Λ繝・け逕ｨ縺ｫ螟画焚繧偵ヨ繝ｬ繧､繝ｫ縺ｫ險倬鹸縺吶ｋ

        Args:
            var: 險倬鹸縺吶ｋ螟画焚
        """
        self.trail.append(var)
        
    def mark_trail(self):
        """迴ｾ蝨ｨ縺ｮ繝医Ξ繧､繝ｫ菴咲ｽｮ繧偵・繝ｼ繧ｯ縺吶ｋ・医ヰ繝・け繝医Λ繝・け逕ｨ・・

        Returns:
            int: 繝√ぉ繝・け繝昴う繝ｳ繝医・菴咲ｽｮ
        """
        mark = len(self.trail)
        self.trail_marks.append(mark)
        return mark
        
    def backtrack_to_mark(self):
        """譛蠕後・繝槭・繧ｯ縺ｾ縺ｧ繝舌ャ繧ｯ繝医Λ繝・け縺吶ｋ
        
        Returns:
            bool: 繝舌ャ繧ｯ繝医Λ繝・け縺悟庄閭ｽ縺縺｣縺溘°縺ｩ縺・°
        """
        if not self.trail_marks:
            return False
            
        mark = self.trail_marks.pop()
        return self.backtrack(mark)
        
    def backtrack(self, position):
        """謖・ｮ壻ｽ咲ｽｮ縺ｾ縺ｧ繝舌ャ繧ｯ繝医Λ繝・け縺吶ｋ

        Args:
            position: 繝舌ャ繧ｯ繝医Λ繝・け蜈医・菴咲ｽｮ

        Returns:
            bool: 繝舌ャ繧ｯ繝医Λ繝・け縺悟庄閭ｽ縺縺｣縺溘°縺ｩ縺・°
        """
        if position < 0 or position > len(self.trail):
            return False
            
        # 繝医Ξ繧､繝ｫ縺ｮ譛ｫ蟆ｾ縺九ｉ蜃ｦ逅・
        while len(self.trail) > position:
            var = self.trail.pop()
            if var in self.value:
                del self.value[var]
            if var in self.parent:
                self.parent[var] = var  # 閾ｪ霄ｫ繧定ｦｪ縺ｫ謌ｻ縺・
                
        return True
        
    def copy(self):
        """繝舌う繝ｳ繝・ぅ繝ｳ繧ｰ迺ｰ蠅・・繧ｳ繝斐・繧剃ｽ懈・縺吶ｋ

        Returns:
            BindingEnvironment: 繧ｳ繝斐・縺輔ｌ縺溽腸蠅・
        """
        new_env = BindingEnvironment()
        new_env.parent = self.parent.copy()
        new_env.value = self.value.copy()
        # 繝医Ξ繧､繝ｫ縺ｯ繧ｳ繝斐・縺励↑縺・ｼ域眠縺励＞螻･豁ｴ縺九ｉ蟋九ａ繧具ｼ・
        return new_env
        
    def __str__(self):
        bindings = {}
        for var in self.parent:
            value = self.get_value(var)
            if value != var:  # 閾ｪ霄ｫ莉･螟悶↓繝舌う繝ｳ繝峨＆繧後※縺・ｋ蝣ｴ蜷医・縺ｿ
                bindings[str(var)] = str(value)
        return str(bindings)
