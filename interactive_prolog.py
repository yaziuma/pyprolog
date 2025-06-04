#!/usr/bin/env python3
"""
PyProlog Interactive Session Launcher
対話型Prologセッション起動ツール
"""

import sys
import os
import argparse
from pathlib import Path

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

try:
    from prolog.runtime.interpreter import Runtime
    from prolog.parser.parser import Parser
    from prolog.parser.scanner import Scanner
    from prolog.core.types import Variable, Rule
    from prolog.core.errors import InterpreterError, ScannerError, PrologError
    from colorama import Fore, Style, init
except ImportError as e:
    print(f"インポートエラー: {e}")
    print("必要な依存関係が不足している可能性があります。")
    sys.exit(1)


class SimplePrologInteractive:
    """シンプルな対話型Prologシステム"""
    
    def __init__(self):
        self.runtime = None
        self.session_history = []
        self.current_rules_file = None
        
        print(self._get_welcome_message())
    
    def _get_welcome_message(self):
        """ウェルカムメッセージを取得"""
        return f"""{Fore.CYAN}
╔════════════════════════════════════════════════════════════╗
║                  PyProlog 対話型システム                    ║
║                     Simple Interactive                    ║
╚════════════════════════════════════════════════════════════╝{Style.RESET_ALL}

{Fore.GREEN}使用方法:{Style.RESET_ALL}
  • Prologクエリを入力してください（例: likes(mary, X).）
  • {Fore.YELLOW}:help{Style.RESET_ALL} でコマンド一覧を表示
  • {Fore.YELLOW}:load <ファイル>{Style.RESET_ALL} でPrologファイルを読み込み
  • {Fore.YELLOW}:quit{Style.RESET_ALL} で終了
"""

    def _get_help_message(self):
        """ヘルプメッセージを取得"""
        return f"""{Fore.CYAN}━━━ PyProlog コマンド一覧 ━━━{Style.RESET_ALL}

{Fore.YELLOW}ファイル操作:{Style.RESET_ALL}
  :load <ファイル>     - Prologファイルを読み込み
  :reload             - 現在のファイルを再読み込み

{Fore.YELLOW}システム操作:{Style.RESET_ALL}
  :show_rules         - 現在読み込まれているルールを表示
  :clear              - 現在のルールをクリア
  :status             - システム状態を表示

{Fore.YELLOW}REPL制御:{Style.RESET_ALL}
  :help               - このヘルプを表示
  :quit, :exit        - システムを終了

{Fore.YELLOW}Prolog述語例:{Style.RESET_ALL}
  member(X, [1,2,3]).        - リストのメンバーチェック
  append([1,2], [3,4], L).   - リスト結合
  X is 2 + 3.                - 算術評価
"""

    def _format_success(self, text):
        return f"{Fore.GREEN}{text}{Style.RESET_ALL}"
    
    def _format_error(self, text):
        return f"{Fore.RED}{text}{Style.RESET_ALL}"
    
    def _format_warning(self, text):
        return f"{Fore.YELLOW}{text}{Style.RESET_ALL}"
    
    def _format_info(self, text):
        return f"{Fore.BLUE}{text}{Style.RESET_ALL}"

    def _init_runtime(self, rules_file=None):
        """ランタイムを初期化"""
        try:
            if rules_file and os.path.exists(rules_file):
                # ファイルからルールを読み込み
                with open(rules_file, 'r', encoding='utf-8') as f:
                    rules_text = f.read()
                
                # 各行を個別にパースしてみる
                rules_list = []
                for line in rules_text.strip().split('\n'):
                    line = line.strip()
                    if line and not line.startswith('%'):
                        try:
                            parsed_rule = Parser(Scanner(line).scan_tokens())._parse_rule()
                            if parsed_rule is not None:
                                rules_list.append(parsed_rule)
                        except Exception as e:
                            print(f"ルール '{line}' の解析に失敗: {e}")
                
                self.runtime = Runtime(rules_list)
                
                self.current_rules_file = rules_file
                print(self._format_success(f"ファイル '{rules_file}' を読み込みました"))
                return True
            else:
                # 空のランタイムを作成
                self.runtime = Runtime([])
                print(self._format_info("空のランタイムを初期化しました"))
                return True
                
        except Exception as e:
            print(self._format_error(f"ランタイム初期化エラー: {e}"))
            return False

    def _handle_command(self, command):
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
            self.runtime = Runtime([])
            self.current_rules_file = None
            print(self._format_success("ルールをクリアしました"))
        elif cmd == ':status':
            self._show_status()
        else:
            print(self._format_error(f"不明なコマンド: {cmd}"))
            print("':help' でコマンド一覧を確認してください")
        return True

    def _show_status(self):
        """システム状態を表示"""
        print(f"{Fore.CYAN}━━━ システム状態 ━━━{Style.RESET_ALL}")
        print(f"現在のファイル: {self.current_rules_file or '(なし)'}")
        print(f"読み込み済みルール数: {len(self.runtime.rules) if self.runtime else 0}")
        print(f"実行済みクエリ数: {len(self.session_history)}")
        print(f"ランタイム状態: {'初期化済み' if self.runtime else '未初期化'}")

    def _display_query_results(self, solutions):
        """クエリ結果を表示"""
        if not solutions:
            print(self._format_warning("解が見つかりませんでした"))
            return
        
        print(self._format_success(f"{len(solutions)} 件の解が見つかりました:"))
        
        for i, solution in enumerate(solutions, 1):
            if isinstance(solution, dict):
                if solution:
                    bindings = []
                    for var, value in solution.items():
                        if isinstance(var, Variable):
                            bindings.append(f"{var.name} = {value}")
                        else:
                            bindings.append(f"{var} = {value}")
                    print(f"  {i:2d}. {', '.join(bindings)}")
                else:
                    print(f"  {i:2d}. true")
            else:
                print(f"  {i:2d}. {solution}")

    def _execute_query(self, query_text):
        """クエリを実行"""
        if not self.runtime:
            self._init_runtime()
        
        try:
            self.session_history.append(query_text)
            
            if self.runtime is not None:
                solutions = self.runtime.query(query_text)
                self._display_query_results(solutions)
            else:
                print(self._format_error("ランタイムが初期化されていません"))
                
        except (InterpreterError, ScannerError, PrologError) as e:
            error_msg = f"Prologエラー: {str(e)}"
            print(self._format_error(error_msg))
        except Exception as e:
            error_msg = f"システムエラー: {str(e)}"
            print(self._format_error(error_msg))

    def run(self):
        """メインのREPLループを実行"""
        try:
            while True:
                try:
                    user_input = input("Prolog> ").strip()
                    
                    if not user_input:
                        continue
                    
                    if user_input.startswith(':'):
                        if not self._handle_command(user_input):
                            break
                    else:
                        self._execute_query(user_input)
                
                except KeyboardInterrupt:
                    print(f"\n{self._format_warning('割り込まれました (Ctrl+C)')}")
                    print("':quit' で終了、':help' でヘルプを表示")
                
        except KeyboardInterrupt:
            pass
        
        finally:
            print(f"\n{self._format_info('PyProlog セッションを終了します')}")
            if self.session_history:
                print(f"実行されたクエリ数: {len(self.session_history)}")

def main():
    """メイン関数"""
    parser = argparse.ArgumentParser(
        description="PyProlog 対話型システム",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用例:
  python interactive_prolog.py                    # 空のセッションを開始
  python interactive_prolog.py -f family.pl      # ファイルを読み込んで開始
  python interactive_prolog.py --demo            # デモモードで開始

対話中に使用可能なコマンド:
  :help          - ヘルプを表示
  :load <file>   - Prologファイルを読み込み
  :show_rules    - 現在のルールを表示
  :quit          - 終了
        """
    )
    
    parser.add_argument(
        '-f', '--file',
        type=str,
        help='起動時に読み込むPrologファイル'
    )
    
    parser.add_argument(
        '--demo',
        action='store_true',
        help='デモデータで開始'
    )
    
    parser.add_argument(
        '--simple',
        action='store_true',
        help='シンプルモードで起動（デフォルト）'
    )
    
    args = parser.parse_args()
    
    # カラー初期化
    init(autoreset=True)
    
    try:
        # 対話システムを起動
        repl = SimplePrologInteractive()
        
        # ファイルが指定された場合は読み込み
        if args.file:
            if os.path.exists(args.file):
                repl._init_runtime(args.file)
            else:
                print(f"{Fore.RED}エラー: ファイル '{args.file}' が見つかりません{Style.RESET_ALL}")
                return 1
        
        # デモモードの場合
        elif args.demo:
            print(f"{Fore.CYAN}デモモードで起動します...{Style.RESET_ALL}")
            # デモデータを作成
            demo_rules = """parent(tom, bob).
parent(tom, liz).
parent(bob, ann).
parent(bob, pat).
parent(pat, jim).
grandparent(X, Z) :- parent(X, Y), parent(Y, Z).
likes(mary, food).
likes(mary, wine).
likes(john, wine).
likes(john, mary).
happy(X) :- likes(X, wine)."""
            
            # 一時ファイルに保存して読み込み
            import tempfile
            with tempfile.NamedTemporaryFile(mode='w', suffix='.pl', delete=False, encoding='utf-8') as f:
                f.write(demo_rules)
                demo_file = f.name
            
            repl._init_runtime(demo_file)
            os.unlink(demo_file)  # 一時ファイルを削除
            
            print(f"{Fore.GREEN}デモデータが読み込まれました。{Style.RESET_ALL}")
            print(f"{Fore.YELLOW}試してみてください:{Style.RESET_ALL}")
            print("  parent(X, Y).")
            print("  grandparent(X, Y).")
            print("  happy(X).")
            print()
        
        # REPLを開始
        repl.run()
        return 0
        
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}ユーザーによって中断されました{Style.RESET_ALL}")
        return 0
    except Exception as e:
        print(f"{Fore.RED}エラー: {e}{Style.RESET_ALL}")
        return 1

if __name__ == "__main__":
    sys.exit(main())