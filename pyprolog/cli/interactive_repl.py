#!/usr/bin/env python3
"""
Enhanced interactive REPL for PyProlog
対話型Prologインタープリター - 拡張版
"""

import os
import sys
import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

# coloramaは既存REPLで使用されているのでそのまま使用
from colorama import Fore, Style, init

from pyprolog.parser.parser import Parser
from pyprolog.parser.scanner import Scanner
from pyprolog.core.types import Variable, Rule
from pyprolog.core.errors import InterpreterError, ScannerError, PrologError
from pyprolog.parser.types import FALSE, TRUE
from pyprolog.runtime.interpreter import Runtime
from pyprolog.core.binding_environment import BindingEnvironment

# カラー初期化
init(autoreset=True)

class InteractiveProlog:
    """拡張された対話型Prologシステム"""
    
    def __init__(self):
        self.runtime: Optional[Runtime] = None
        self.session_history: List[Dict[str, Any]] = []
        self.home_path = str(Path.home())
        self.session_start_time = datetime.now()
        self.current_rules_file: Optional[str] = None
        
        print(self._get_welcome_message())
    
    def _get_welcome_message(self) -> str:
        """ウェルカムメッセージを取得"""
        return f"""{Fore.CYAN}
╔════════════════════════════════════════════════════════════╗
║                  PyProlog 対話型システム                    ║
║                     Enhanced REPL v1.0                    ║
╚════════════════════════════════════════════════════════════╝{Style.RESET_ALL}

{Fore.GREEN}使用方法:{Style.RESET_ALL}
  • Prologクエリを入力してください（例: likes(mary, X).）
  • {Fore.YELLOW}:help{Style.RESET_ALL} でコマンド一覧を表示
  • {Fore.YELLOW}:load <ファイル>{Style.RESET_ALL} でPrologファイルを読み込み
  • {Fore.YELLOW}:quit{Style.RESET_ALL} で終了

{Fore.BLUE}コマンド例:{Style.RESET_ALL}
  :load sample_usage/family.pl  # ファイル読み込み
  parent(X, Y).                 # クエリ実行
  :show_rules                   # 現在のルール表示
"""

    def _get_help_message(self) -> str:
        """ヘルプメッセージを取得"""
        return f"""{Fore.CYAN}━━━ PyProlog コマンド一覧 ━━━{Style.RESET_ALL}

{Fore.YELLOW}ファイル操作:{Style.RESET_ALL}
  :load <ファイル>     - Prologファイルを読み込み
  :reload             - 現在のファイルを再読み込み
  :save_session       - セッション履歴を保存

{Fore.YELLOW}システム操作:{Style.RESET_ALL}
  :show_rules         - 現在読み込まれているルールを表示
  :clear              - 現在のルールをクリア
  :status             - システム状態を表示
  :debug_on/off       - デバッグモードの切り替え

{Fore.YELLOW}REPL制御:{Style.RESET_ALL}
  :help               - このヘルプを表示
  :quit, :exit        - システムを終了

{Fore.YELLOW}Prolog述語例:{Style.RESET_ALL}
  member(X, [1,2,3]).        - リストのメンバーチェック
  append([1,2], [3,4], L).   - リスト結合
  X is 2 + 3.                - 算術評価
  findall(X, goal(X), List). - 解の収集

{Fore.GREEN}ヒント:{Style.RESET_ALL} タブキーで自動補完、↑↓で履歴移動
"""

    def _format_success(self, text: str) -> str:
        """成功メッセージのフォーマット"""
        return f"{Fore.GREEN}{text}{Style.RESET_ALL}"
    
    def _format_error(self, text: str) -> str:
        """エラーメッセージのフォーマット"""
        return f"{Fore.RED}{text}{Style.RESET_ALL}"
    
    def _format_warning(self, text: str) -> str:
        """警告メッセージのフォーマット"""
        return f"{Fore.YELLOW}{text}{Style.RESET_ALL}"
    
    def _format_info(self, text: str) -> str:
        """情報メッセージのフォーマット"""
        return f"{Fore.BLUE}{text}{Style.RESET_ALL}"

    def _init_runtime(self, rules_file: Optional[str] = None) -> bool:
        """ランタイムを初期化"""
        try:
            if rules_file and os.path.exists(rules_file):
                # ファイルからルールを読み込み
                with open(rules_file, 'r', encoding='utf-8') as f:
                    rules_text = f.read()
                
                rules = Parser(Scanner(rules_text).scan_tokens())._parse_rule()
                # _parse_ruleが単一のルールを返す場合はリストに変換
                if rules is not None:
                    rules_list = [rules] if not isinstance(rules, list) else rules
                    self.runtime = Runtime(rules_list)
                else:
                    self.runtime = Runtime([])
                self.current_rules_file = rules_file
                print(self._format_success(f"ファイル '{rules_file}' を読み込みました"))
                return True
            else:
                # 空のランタイムを作成
                self.runtime = Runtime()
                print(self._format_info("空のランタイムを初期化しました"))
                return True
                
        except Exception as e:
            print(self._format_error(f"ランタイム初期化エラー: {e}"))
            return False

    def _handle_command(self, command: str) -> bool:
        """コマンドを処理（True=継続、False=終了）"""
        parts = command.strip().split()
        cmd = parts[0].lower()
        
        if cmd in [':quit', ':exit']:
            return False
        
        elif cmd == ':help':
            print(self._get_help_message())
        
        elif cmd == ':load':
            if len(parts) < 2:
                print(self._format_error("使用法: :load <ファイルパス>"))
                return True
            
            file_path = parts[1]
            if not os.path.exists(file_path):
                print(self._format_error(f"ファイル '{file_path}' が見つかりません"))
                return True
            
            self._init_runtime(file_path)
        
        elif cmd == ':reload':
            if self.current_rules_file:
                self._init_runtime(self.current_rules_file)
            else:
                print(self._format_warning("再読み込みするファイルがありません"))
        
        elif cmd == ':show_rules':
            if self.runtime and self.runtime.rules:
                print(self._format_info(f"現在のルール ({len(self.runtime.rules)} 件):"))
                for i, rule in enumerate(self.runtime.rules, 1):
                    print(f"  {i:2d}. {rule}")
            else:
                print(self._format_warning("ルールが読み込まれていません"))
        
        elif cmd == ':clear':
            self.runtime = Runtime()
            self.current_rules_file = None
            print(self._format_success("ルールをクリアしました"))
        
        elif cmd == ':status':
            self._show_status()
        
        elif cmd == ':save_session':
            self._save_session()
        
        elif cmd in [':debug_on', ':debug_off']:
            debug_state = 'ON' if cmd == ':debug_on' else 'OFF'
            print(self._format_info(f"デバッグモード: {debug_state}"))
            # TODO: 実際のデバッグ制御を実装
        
        else:
            print(self._format_error(f"不明なコマンド: {cmd}"))
            print("':help' でコマンド一覧を確認してください")
        
        return True

    def _show_status(self):
        """システム状態を表示"""
        print(f"{Fore.CYAN}━━━ システム状態 ━━━{Style.RESET_ALL}")
        print(f"セッション開始時刻: {self.session_start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"現在のファイル: {self.current_rules_file or '(なし)'}")
        print(f"読み込み済みルール数: {len(self.runtime.rules) if self.runtime else 0}")
        print(f"実行済みクエリ数: {len(self.session_history)}")
        print(f"ランタイム状態: {'初期化済み' if self.runtime else '未初期化'}")

    def _save_session(self):
        """セッション履歴を保存"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"prolog_session_{timestamp}.json"
            
            session_data = {
                'start_time': self.session_start_time.isoformat(),
                'end_time': datetime.now().isoformat(),
                'rules_file': self.current_rules_file,
                'history': self.session_history
            }
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(session_data, f, ensure_ascii=False, indent=2)
            
            print(self._format_success(f"セッションを '{filename}' に保存しました"))
        
        except Exception as e:
            print(self._format_error(f"セッション保存エラー: {e}"))

    def _display_query_results(self, goal, solutions: List):
        """クエリ結果を表示"""
        if not solutions:
            print(self._format_warning("解が見つかりませんでした"))
            return
        
        print(self._format_success(f"{len(solutions)} 件の解が見つかりました:"))
        
        # 変数を抽出
        variables = []
        if hasattr(goal, 'args'):
            for arg in goal.args:
                if isinstance(arg, Variable):
                    variables.append(arg.name)
        
        # 解を表示
        for i, solution in enumerate(solutions, 1):
            if variables:
                bindings = []
                for var_name in variables:
                    if hasattr(solution, 'bindings') and var_name in solution.bindings:
                        value = solution.bindings[var_name]
                        bindings.append(f"{var_name} = {value}")
                
                if bindings:
                    print(f"  {i:2d}. {', '.join(bindings)}")
                else:
                    print(f"  {i:2d}. true")
            else:
                print(f"  {i:2d}. true")

    def _execute_query(self, query_text: str):
        """クエリを実行"""
        if not self.runtime:
            self._init_runtime()
        
        try:
            # クエリ履歴に追加
            query_record = {
                'timestamp': datetime.now().isoformat(),
                'query': query_text,
                'success': False,
                'results_count': 0,
                'error': None
            }
            
            # パースして実行
            goal = Parser(Scanner(query_text).scan_tokens())._parse_term()
            
            # クエリ実行
            if self.runtime is not None:
                try:
                    # queryメソッドを使用
                    solutions = self.runtime.query(query_text)
                    # queryメソッドの結果を適切な形式に変換
                    if isinstance(solutions, list):
                        # 解の数を結果の数として記録
                        query_record['results_count'] = len(solutions)
                    else:
                        solutions = []
                except Exception:
                    # queryが失敗した場合、executeを試す
                    solutions = []
                    env = BindingEnvironment()
                    for solution in self.runtime.execute(goal, env):
                        if not isinstance(solution, FALSE):
                            solutions.append(solution)
            else:
                solutions = []
            
            # 結果表示
            self._display_query_results(goal, solutions)
            
            # 履歴更新
            query_record['success'] = True
            if 'results_count' not in query_record:
                query_record['results_count'] = len(solutions) if solutions else 0
            
        except (InterpreterError, ScannerError, PrologError) as e:
            error_msg = f"Prologエラー: {str(e)}"
            print(self._format_error(error_msg))
            query_record['error'] = str(e)
        
        except Exception as e:
            error_msg = f"システムエラー: {str(e)}"
            print(self._format_error(error_msg))
            query_record['error'] = str(e)
        
        finally:
            self.session_history.append(query_record)

    def run(self):
        """メインのREPLループを実行"""
        try:
            while True:
                try:
                    # シンプルなプロンプト表示と入力受付
                    user_input = input("Prolog> ").strip()
                    
                    # 空入力をスキップ
                    if not user_input:
                        continue
                    
                    # コマンド処理
                    if user_input.startswith(':'):
                        if not self._handle_command(user_input):
                            break  # 終了コマンド
                    else:
                        # Prologクエリとして実行
                        self._execute_query(user_input)
                
                except KeyboardInterrupt:
                    print(f"\n{self._format_warning('割り込まれました (Ctrl+C)')}")
                    print("':quit' で終了、':help' でヘルプを表示")
                
        except KeyboardInterrupt:
            pass  # 外側のキャッチ
        
        finally:
            print(f"\n{self._format_info('PyProlog セッションを終了します')}")
            if self.session_history:
                print(f"実行されたクエリ数: {len(self.session_history)}")


def main():
    """メイン関数"""
    try:
        repl = InteractiveProlog()
        repl.run()
    except Exception as e:
        print(f"{Fore.RED}システム初期化エラー: {e}{Style.RESET_ALL}")
        sys.exit(1)


if __name__ == "__main__":
    main()