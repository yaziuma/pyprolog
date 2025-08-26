"""
データエクスポーター

事実データを様々な形式でエクスポートする機能を提供
"""

import csv
import json
import os
from typing import List, Dict, Any, Union, Optional
from pathlib import Path
from pyprolog.core.types import Fact, Term, Atom, Variable, Number, PrologType
import logging

logger = logging.getLogger(__name__)


class DataExporter:
    """データエクスポーター"""
    
    def __init__(self, runtime=None):
        """
        エクスポーターを初期化
        
        Args:
            runtime: Runtime インスタンス（変数・ファンクターマッピング用）
        """
        self.runtime = runtime
    
    def export_to_csv(self, facts: List[Fact], filepath: str) -> bool:
        """
        CSV形式でエクスポート
        
        Args:
            facts: エクスポート対象の事実リスト
            filepath: 出力ファイルパス
            
        Returns:
            成功時True、失敗時False
        """
        try:
            # ディレクトリが存在しない場合は作成
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            
            if not facts:
                # 空ファイルを作成
                with open(filepath, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.writer(f)
                    writer.writerow(['functor', 'args'])  # 基本ヘッダー
                return True
            
            # 最大引数数を決定
            max_args = max(len(self._extract_args(fact.head)) for fact in facts)
            
            # ヘッダー行を生成
            headers = ['functor'] + [f'arg{i+1}' for i in range(max_args)]
            
            with open(filepath, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(headers)
                
                # 各事実を行として書き込み
                for fact in facts:
                    row = self._fact_to_csv_row(fact, max_args)
                    writer.writerow(row)
            
            logger.info(f"Exported {len(facts)} facts to CSV: {filepath}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to export CSV to {filepath}: {e}")
            return False
    
    def export_to_json(self, facts: List[Fact], filepath: str) -> bool:
        """
        JSON形式でエクスポート
        
        Args:
            facts: エクスポート対象の事実リスト
            filepath: 出力ファイルパス
            
        Returns:
            成功時True、失敗時False
        """
        try:
            # ディレクトリが存在しない場合は作成
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            
            # 各事実をJSON オブジェクトに変換
            json_data = []
            for fact in facts:
                json_obj = self._fact_to_json_object(fact)
                json_data.append(json_obj)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(json_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"Exported {len(facts)} facts to JSON: {filepath}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to export JSON to {filepath}: {e}")
            return False
    
    def export_to_tsv(self, facts: List[Fact], filepath: str) -> bool:
        """
        TSV形式でエクスポート
        
        Args:
            facts: エクスポート対象の事実リスト
            filepath: 出力ファイルパス
            
        Returns:
            成功時True、失敗時False
        """
        try:
            # ディレクトリが存在しない場合は作成
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            
            if not facts:
                # 空ファイルを作成
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write('functor\targs\n')  # 基本ヘッダー
                return True
            
            # 最大引数数を決定
            max_args = max(len(self._extract_args(fact.head)) for fact in facts)
            
            # ヘッダー行を生成
            headers = ['functor'] + [f'arg{i+1}' for i in range(max_args)]
            
            with open(filepath, 'w', encoding='utf-8') as f:
                # ヘッダー書き込み
                f.write('\t'.join(headers) + '\n')
                
                # 各事実を行として書き込み
                for fact in facts:
                    row = self._fact_to_csv_row(fact, max_args)  # CSV と同じ行データ
                    f.write('\t'.join(str(cell) for cell in row) + '\n')
            
            logger.info(f"Exported {len(facts)} facts to TSV: {filepath}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to export TSV to {filepath}: {e}")
            return False
    
    def _extract_args(self, term: Term) -> List[PrologType]:
        """
        項から引数リストを抽出
        
        Args:
            term: 対象の項
            
        Returns:
            引数のリスト
        """
        if isinstance(term, Term):
            return term.args
        else:
            return []  # Atomなど引数がない場合
    
    def _fact_to_csv_row(self, fact: Fact, max_args: int) -> List[str]:
        """
        事実をCSV行データに変換
        
        Args:
            fact: 変換対象の事実
            max_args: 最大引数数
            
        Returns:
            CSV行データ
        """
        head = fact.head
        
        # ファンクター名
        functor_name = self._get_functor_name(head)
        
        # 引数
        args = self._extract_args(head)
        arg_strings = [self._term_to_string(arg) for arg in args]
        
        # 不足分を空文字で埋める
        while len(arg_strings) < max_args:
            arg_strings.append('')
        
        return [functor_name] + arg_strings
    
    def _fact_to_json_object(self, fact: Fact) -> Dict[str, Any]:
        """
        事実をJSONオブジェクトに変換
        
        Args:
            fact: 変換対象の事実
            
        Returns:
            JSONオブジェクト（辞書）
        """
        head = fact.head
        
        # ファンクター名
        functor_name = self._get_functor_name(head)
        
        # 引数
        args = self._extract_args(head)
        json_args = [self._term_to_json_value(arg) for arg in args]
        
        return {
            'functor': functor_name,
            'args': json_args
        }
    
    def _get_functor_name(self, term: Term) -> str:
        """
        項からファンクター名を取得
        
        Args:
            term: 対象の項
            
        Returns:
            ファンクター名
        """
        if isinstance(term, Term):
            functor = term.functor
        elif isinstance(term, Atom):
            functor = term
        else:
            return str(term)
        
        if isinstance(functor, Atom):
            functor_name = functor.name
            
            # ファンクターマッピングで日本語復元を試行
            if self.runtime and hasattr(self.runtime, 'functor_mapper') and self.runtime.functor_mapper:
                original_name = self.runtime.functor_mapper.map_english_to_non_ascii(functor_name)
                return original_name
            
            return functor_name
        else:
            return str(functor)
    
    def _term_to_string(self, term: PrologType) -> str:
        """
        項を文字列に変換（エクスポート用）
        
        Args:
            term: 変換対象の項
            
        Returns:
            文字列表現
        """
        if isinstance(term, Atom):
            atom_name = term.name
            
            # ファンクターマッピングで日本語復元を試行
            if self.runtime and hasattr(self.runtime, 'functor_mapper') and self.runtime.functor_mapper:
                original_name = self.runtime.functor_mapper.map_english_to_non_ascii(atom_name)
                return original_name
            
            return atom_name
            
        elif isinstance(term, Variable):
            var_name = term.name
            
            # 変数マッピングで日本語復元を試行
            if self.runtime and hasattr(self.runtime, 'variable_mapper') and self.runtime.variable_mapper:
                original_name = self.runtime.variable_mapper.map_english_to_japanese(var_name)
                return original_name
            
            return var_name
            
        elif isinstance(term, Number):
            return str(term.value)
            
        elif isinstance(term, Term):
            # 複合項は簡易文字列表現
            functor_name = self._get_functor_name(term)
            if not term.args:
                return functor_name
            
            args_str = ','.join(self._term_to_string(arg) for arg in term.args)
            return f"{functor_name}({args_str})"
            
        else:
            return str(term)
    
    def _term_to_json_value(self, term: PrologType) -> Any:
        """
        項をJSON値に変換
        
        Args:
            term: 変換対象の項
            
        Returns:
            JSON値（適切な型）
        """
        if isinstance(term, Atom):
            atom_name = term.name
            
            # ファンクターマッピングで日本語復元を試行
            if self.runtime and hasattr(self.runtime, 'functor_mapper') and self.runtime.functor_mapper:
                original_name = self.runtime.functor_mapper.map_english_to_non_ascii(atom_name)
                return original_name
            
            return atom_name
            
        elif isinstance(term, Variable):
            var_name = term.name
            
            # 変数マッピングで日本語復元を試行
            if self.runtime and hasattr(self.runtime, 'variable_mapper') and self.runtime.variable_mapper:
                original_name = self.runtime.variable_mapper.map_english_to_japanese(var_name)
                return original_name
            
            return var_name
            
        elif isinstance(term, Number):
            return term.value
            
        elif isinstance(term, Term):
            # 複合項は構造化オブジェクトとして表現
            functor_name = self._get_functor_name(term)
            
            if not term.args:
                return functor_name
            
            json_args = [self._term_to_json_value(arg) for arg in term.args]
            
            # リスト構造の特別処理
            if functor_name == "." and len(json_args) == 2:
                # Prolog リストを JSON 配列に変換を試行
                try:
                    return self._prolog_list_to_json_array(term)
                except:
                    # 変換失敗時は通常の構造として扱う
                    pass
            
            return {
                'functor': functor_name,
                'args': json_args
            }
            
        else:
            return str(term)
    
    def _prolog_list_to_json_array(self, term: Term) -> List[Any]:
        """
        Prologリスト構造をJSON配列に変換
        
        Args:
            term: リスト構造のTerm
            
        Returns:
            JSON配列
        """
        result = []
        current = term
        
        while isinstance(current, Term) and isinstance(current.functor, Atom) and current.functor.name == ".":
            if len(current.args) >= 1:
                head = current.args[0]
                result.append(self._term_to_json_value(head))
                
                if len(current.args) >= 2:
                    tail = current.args[1]
                    
                    # 空リストで終端
                    if isinstance(tail, Atom) and tail.name == "[]":
                        break
                    # リスト続行
                    elif isinstance(tail, Term) and isinstance(tail.functor, Atom) and tail.functor.name == ".":
                        current = tail
                        continue
                    else:
                        # 不完全リスト - 通常の構造として扱う
                        raise ValueError("Improper list")
                else:
                    break
            else:
                break
        
        return result
    
    def get_format_from_file_spec(self, file_spec: PrologType) -> tuple:
        """
        ファイル指定から形式とパスを抽出
        
        Args:
            file_spec: ファイル指定（Atomまたは複合項）
            
        Returns:
            (format_name, filepath) のタプル
        """
        if isinstance(file_spec, Atom):
            # 単純なファイルパス - 拡張子から形式を推定
            filepath = file_spec.name
            if filepath.endswith('.json'):
                return ('json', filepath)
            elif filepath.endswith('.tsv'):
                return ('tsv', filepath)
            else:
                return ('csv', filepath)  # デフォルト
                
        elif isinstance(file_spec, Term):
            # 複合項形式: json('file.json'), csv('file.csv'), tsv('file.tsv')
            if isinstance(file_spec.functor, Atom):
                format_name = file_spec.functor.name
                
                if len(file_spec.args) == 1 and isinstance(file_spec.args[0], Atom):
                    filepath = file_spec.args[0].name
                    return (format_name, filepath)
        
        # 解析失敗時はデフォルト
        return ('csv', str(file_spec))
    
    def export_facts(self, facts: List[Fact], file_spec: PrologType) -> bool:
        """
        指定された形式で事実をエクスポート
        
        Args:
            facts: エクスポート対象の事実リスト
            file_spec: ファイル指定（形式含む）
            
        Returns:
            成功時True、失敗時False
        """
        try:
            format_name, filepath = self.get_format_from_file_spec(file_spec)
            
            if format_name.lower() == 'json':
                return self.export_to_json(facts, filepath)
            elif format_name.lower() == 'tsv':
                return self.export_to_tsv(facts, filepath)
            else:  # デフォルトはCSV
                return self.export_to_csv(facts, filepath)
                
        except Exception as e:
            logger.error(f"Failed to export facts: {e}")
            return False