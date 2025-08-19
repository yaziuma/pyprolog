"""
シンボルテーブル

Prologプログラムの述語定義と参照を管理します。
"""
from dataclasses import dataclass, field
from typing import Dict, List, Set, Union, Optional
from pyprolog.core.rule import Rule
from pyprolog.core.fact import Fact
from pyprolog.util.logger import get_logger

logger = get_logger(__name__)


@dataclass
class PredicateInfo:
    """述語情報を表すクラス"""
    name: str
    arity: int
    definition: Union[Rule, Fact]
    file_path: Optional[str]
    line_number: int
    is_builtin: bool = False
    references: List['PredicateReference'] = field(default_factory=list)
    
    def __str__(self) -> str:
        return f"{self.name}/{self.arity}"


@dataclass
class PredicateReference:
    """述語参照を表すクラス"""
    name: str
    arity: int
    referenced_in: Union[Rule, Fact]
    file_path: Optional[str]
    line_number: int
    context: str  # "head" or "body"
    
    def __str__(self) -> str:
        return f"{self.name}/{self.arity} (referenced in {self.context})"


class SymbolTable:
    """Prologプログラムのシンボルテーブル"""
    
    def __init__(self):
        self.predicates: Dict[str, List[PredicateInfo]] = {}
        self.builtins: Set[str] = set()
        self.user_defined: Set[str] = set()
        self._init_builtins()
    
    def _init_builtins(self):
        """ビルトイン述語を初期化"""
        builtin_predicates = [
            "var/1", "atom/1", "number/1", "functor/3", "arg/3", "=../2",
            "asserta/1", "assertz/1", "retract/1", "member/2", "append/3",
            "findall/3", "get_char/1", "write/1", "nl/0", "is/2",
            "=/2", "=:=/2", "=\\=/2", "</2", "=</2", ">/2", ">=/2",
            "true/0", "fail/0", "!/0", "length/2", "reverse/2",
            "sort/2", "bagof/3", "setof/3", "call/1", "once/1",
            "repeat/0", "halt/0", "halt/1", "read/1", "peek_char/1",
            "at_end_of_stream/0", "read_line/1"
        ]
        
        for predicate in builtin_predicates:
            self.builtins.add(predicate)
    
    def add_predicate(self, name: str, arity: int, rule_or_fact: Union[Rule, Fact], 
                     file_path: Optional[str] = None, line_number: int = 0) -> None:
        """述語定義を追加"""
        key = predicate_key(name, arity)
        
        predicate_info = PredicateInfo(
            name=name,
            arity=arity,
            definition=rule_or_fact,
            file_path=file_path,
            line_number=line_number
        )
        
        if key not in self.predicates:
            self.predicates[key] = []
        
        self.predicates[key].append(predicate_info)
        self.user_defined.add(key)
        
        logger.debug(f"述語定義を追加: {key}")
    
    def add_reference(self, name: str, arity: int, referenced_in: Union[Rule, Fact],
                     file_path: Optional[str] = None, line_number: int = 0, context: str = "body") -> None:
        """述語参照を追加"""
        key = predicate_key(name, arity)
        
        reference = PredicateReference(
            name=name,
            arity=arity,
            referenced_in=referenced_in,
            file_path=file_path,
            line_number=line_number,
            context=context
        )
        
        # 定義が存在する場合は参照を追加
        if key in self.predicates:
            for predicate_info in self.predicates[key]:
                predicate_info.references.append(reference)
        
        logger.debug(f"述語参照を追加: {key} in {context}")
    
    def get_predicate_info(self, name: str, arity: int) -> Optional[List[PredicateInfo]]:
        """述語情報を取得"""
        key = predicate_key(name, arity)
        return self.predicates.get(key)
    
    def is_defined(self, name: str, arity: int) -> bool:
        """述語が定義されているかチェック"""
        key = predicate_key(name, arity)
        return key in self.predicates or key in self.builtins
    
    def is_builtin(self, name: str, arity: int) -> bool:
        """ビルトイン述語かチェック"""
        key = predicate_key(name, arity)
        return key in self.builtins
    
    def get_all_predicates(self) -> List[PredicateInfo]:
        """全ての述語情報を取得"""
        all_predicates = []
        for predicate_list in self.predicates.values():
            all_predicates.extend(predicate_list)
        return all_predicates
    
    def get_undefined_references(self) -> List[PredicateReference]:
        """未定義述語への参照を取得"""
        undefined_refs = []
        
        # 全ての参照をチェック
        for predicate_list in self.predicates.values():
            for predicate_info in predicate_list:
                for ref in predicate_info.references:
                    if not self.is_defined(ref.name, ref.arity):
                        undefined_refs.append(ref)
        
        return undefined_refs
    
    def get_multiple_definitions(self) -> Dict[str, List[PredicateInfo]]:
        """複数定義のある述語を取得"""
        multiple_defs = {}
        
        for key, predicate_list in self.predicates.items():
            if len(predicate_list) > 1:
                multiple_defs[key] = predicate_list
        
        return multiple_defs
    
    def get_unreferenced_predicates(self) -> List[PredicateInfo]:
        """参照されていない述語を取得"""
        unreferenced = []
        
        for predicate_list in self.predicates.values():
            for predicate_info in predicate_list:
                if not predicate_info.references:
                    unreferenced.append(predicate_info)
        
        return unreferenced
    
    def get_statistics(self) -> Dict[str, int]:
        """統計情報を取得"""
        total_predicates = len(self.predicates)
        total_definitions = sum(len(plist) for plist in self.predicates.values())
        total_references = sum(
            len(p.references) 
            for plist in self.predicates.values() 
            for p in plist
        )
        
        return {
            "total_predicates": total_predicates,
            "total_definitions": total_definitions,
            "total_references": total_references,
            "builtin_predicates": len(self.builtins),
            "user_defined_predicates": len(self.user_defined)
        }


def predicate_key(name: str, arity: int) -> str:
    """述語キーを生成"""
    return f"{name}/{arity}"