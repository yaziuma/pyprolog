# 1. 各Pythonファイルの冒頭に以下を追加（文字エンコーディング対策）
import sys
import io
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(
        sys.stdout.buffer, 
        encoding='utf-8', 
        errors='replace'
    )

# 3. 使用例
# safe_print("PyProlog計算処理サンプル")  # 文字化けしても出力される
# safe_print("PyProlog Basic Usage Sample")  # より安全

# 4. バッチファイルでの環境設定
# run_samples.batに以下を追加：
# set PYTHONIOENCODING=utf-8

# 5. 変数値取得の完全修正
def safe_get_variable_value(result_dict, var_name):
    """より堅牢な変数値取得"""
    # 複数の方法で変数値を検索
    for key, value in result_dict.items():
        # 1. Variable オブジェクトの name 属性
        if hasattr(key, 'name') and key.name == var_name:
            return value
        # 2. 文字列表現での比較
        if str(key) == var_name:
            return value
        # 3. repr での比較
        if repr(key) == var_name:
            return value
    
    # 辞書キーでの直接検索
    if var_name in result_dict:
        return result_dict[var_name]
    
    return None  # 'unknown' ではなく None を返す

safe_get_variable = safe_get_variable_value