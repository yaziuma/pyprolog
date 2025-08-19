"""
依存関係グラフ

Prolog述語間の呼び出し関係を管理し、到達可能性解析や循環検出を提供します。
"""
from typing import Dict, Set, List, Optional, Tuple
from collections import deque, defaultdict
from pyprolog.util.logger import get_logger

logger = get_logger(__name__)


class DependencyGraph:
    """述語間の依存関係グラフ"""
    
    def __init__(self):
        self.nodes: Set[str] = set()  # predicate/arity
        self.edges: Dict[str, Set[str]] = defaultdict(set)  # caller -> callees
        self.reverse_edges: Dict[str, Set[str]] = defaultdict(set)  # callee -> callers
    
    def add_node(self, predicate_key: str) -> None:
        """ノード（述語）を追加"""
        self.nodes.add(predicate_key)
        logger.debug(f"グラフノード追加: {predicate_key}")
    
    def add_edge(self, caller: str, callee: str) -> None:
        """エッジ（依存関係）を追加"""
        self.nodes.add(caller)
        self.nodes.add(callee)
        self.edges[caller].add(callee)
        self.reverse_edges[callee].add(caller)
        logger.debug(f"依存関係追加: {caller} -> {callee}")
    
    def get_dependencies(self, predicate_key: str) -> Set[str]:
        """指定された述語の依存先を取得"""
        return self.edges.get(predicate_key, set())
    
    def get_dependents(self, predicate_key: str) -> Set[str]:
        """指定された述語に依存する述語を取得"""
        return self.reverse_edges.get(predicate_key, set())
    
    def get_reachable_from(self, start_nodes: Set[str]) -> Set[str]:
        """開始ノードから到達可能なノードを取得"""
        reachable = set()
        queue = deque(start_nodes)
        visited = set()
        
        while queue:
            current = queue.popleft()
            if current in visited:
                continue
            
            visited.add(current)
            reachable.add(current)
            
            # 依存先を追加
            for dependent in self.edges.get(current, set()):
                if dependent not in visited:
                    queue.append(dependent)
        
        logger.debug(f"到達可能ノード数: {len(reachable)} (開始: {len(start_nodes)})")
        return reachable
    
    def get_unreachable_nodes(self, entry_points: Set[str]) -> Set[str]:
        """エントリーポイントから到達不可能なノードを取得"""
        reachable = self.get_reachable_from(entry_points)
        unreachable = self.nodes - reachable
        
        logger.debug(f"到達不可能ノード数: {len(unreachable)}")
        return unreachable
    
    def detect_cycles(self) -> List[List[str]]:
        """循環依存を検出"""
        cycles = []
        visited = set()
        rec_stack = set()
        
        def dfs_cycle_detection(node: str, path: List[str]) -> bool:
            if node in rec_stack:
                # 循環を発見
                cycle_start = path.index(node)
                cycle = path[cycle_start:] + [node]
                cycles.append(cycle)
                return True
            
            if node in visited:
                return False
            
            visited.add(node)
            rec_stack.add(node)
            path.append(node)
            
            for neighbor in self.edges.get(node, set()):
                if dfs_cycle_detection(neighbor, path):
                    pass  # 循環を発見したが、他の循環も探す
            
            rec_stack.remove(node)
            path.pop()
            return False
        
        for node in self.nodes:
            if node not in visited:
                dfs_cycle_detection(node, [])
        
        logger.debug(f"循環依存検出: {len(cycles)} 個")
        return cycles
    
    def topological_sort(self) -> Optional[List[str]]:
        """トポロジカルソート（循環がある場合はNone）"""
        in_degree = defaultdict(int)
        
        # 入次数を計算
        for node in self.nodes:
            in_degree[node] = 0
        
        for caller, callees in self.edges.items():
            for callee in callees:
                in_degree[callee] += 1
        
        # 入次数0のノードから開始
        queue = deque([node for node in self.nodes if in_degree[node] == 0])
        result = []
        
        while queue:
            current = queue.popleft()
            result.append(current)
            
            for neighbor in self.edges.get(current, set()):
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)
        
        # 全てのノードが処理されたかチェック（循環がないか）
        if len(result) != len(self.nodes):
            logger.warning("循環依存のためトポロジカルソートに失敗")
            return None
        
        return result
    
    def get_strongly_connected_components(self) -> List[List[str]]:
        """強連結成分を取得（Kosarajuのアルゴリズム）"""
        visited = set()
        stack = []
        
        # 第1回DFS: 完了順序でスタックに積む
        def dfs1(node: str):
            if node in visited:
                return
            visited.add(node)
            for neighbor in self.edges.get(node, set()):
                dfs1(neighbor)
            stack.append(node)
        
        for node in self.nodes:
            dfs1(node)
        
        # 第2回DFS: 逆グラフで強連結成分を探索
        visited.clear()
        components = []
        
        def dfs2(node: str, component: List[str]):
            if node in visited:
                return
            visited.add(node)
            component.append(node)
            for neighbor in self.reverse_edges.get(node, set()):
                dfs2(neighbor, component)
        
        while stack:
            node = stack.pop()
            if node not in visited:
                component = []
                dfs2(node, component)
                if component:
                    components.append(component)
        
        logger.debug(f"強連結成分数: {len(components)}")
        return components
    
    def get_path(self, start: str, end: str) -> Optional[List[str]]:
        """2つのノード間のパスを取得（BFS）"""
        if start not in self.nodes or end not in self.nodes:
            return None
        
        queue = deque([(start, [start])])
        visited = {start}
        
        while queue:
            current, path = queue.popleft()
            
            if current == end:
                return path
            
            for neighbor in self.edges.get(current, set()):
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append((neighbor, path + [neighbor]))
        
        return None
    
    def get_statistics(self) -> Dict[str, int]:
        """グラフ統計情報を取得"""
        total_edges = sum(len(callees) for callees in self.edges.values())
        cycles = self.detect_cycles()
        components = self.get_strongly_connected_components()
        
        # 孤立ノード（入次数も出次数も0）
        isolated_nodes = [
            node for node in self.nodes 
            if not self.edges.get(node) and not self.reverse_edges.get(node)
        ]
        
        return {
            "total_nodes": len(self.nodes),
            "total_edges": total_edges,
            "cycles": len(cycles),
            "strongly_connected_components": len(components),
            "isolated_nodes": len(isolated_nodes)
        }