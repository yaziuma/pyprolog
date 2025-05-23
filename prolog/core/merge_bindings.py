# prolog/core/merge_bindings.py
from prolog.core.types import Variable
from prolog.util.logger import logger


def merge_bindings(bindings1, bindings2=None):
    """バインディングを結合する（後方互換性を保持）

    Args:
        bindings1: 最初のバインディング（辞書またはBindingEnvironment）
        bindings2: 2番目のバインディング（辞書またはBindingEnvironment、オプション）

    Returns:
        結合されたバインディング辞書またはBindingEnvironment

    注意:
        - 両方が辞書の場合：辞書を返す
        - どちらかがBindingEnvironmentの場合：BindingEnvironmentを返す
        - 競合する場合はbindings2が優先される
    """
    # BindingEnvironmentの検出
    from prolog.core.binding_environment import BindingEnvironment

    # bindings1がNoneの場合の処理
    if bindings1 is None:
        if bindings2 is None:
            return {}
        return bindings2

    # bindings2がNoneの場合の処理
    if bindings2 is None:
        return bindings1

    # 両方がBindingEnvironmentの場合
    if isinstance(bindings1, BindingEnvironment) and isinstance(
        bindings2, BindingEnvironment
    ):
        logger.debug("merge_bindings: Both are BindingEnvironment instances")
        # 新しい環境を作成し、両方の内容を統合
        merged_env = bindings1.copy()

        # bindings2の内容をmerged_envに統合
        for var in bindings2.parent:
            if var != bindings2.parent[var]:  # 自分自身以外にバインドされている場合
                root_value = bindings2.get_value(var)
                if root_value != var:
                    merged_env.unify(var, root_value)

        return merged_env

    # 一方がBindingEnvironment、もう一方が辞書の場合
    if isinstance(bindings1, BindingEnvironment):
        logger.debug(
            "merge_bindings: bindings1 is BindingEnvironment, bindings2 is dict"
        )
        merged_env = bindings1.copy()

        # 辞書の内容をBindingEnvironmentに統合
        for var, value in bindings2.items():
            merged_env.unify(var, value)

        return merged_env

    if isinstance(bindings2, BindingEnvironment):
        logger.debug(
            "merge_bindings: bindings1 is dict, bindings2 is BindingEnvironment"
        )
        merged_env = bindings2.copy()

        # 辞書の内容をBindingEnvironmentに統合
        for var, value in bindings1.items():
            merged_env.unify(var, value)

        return merged_env

    # 両方が辞書の場合（従来の動作）
    logger.debug("merge_bindings: Both are dictionaries")
    if not isinstance(bindings1, dict) or not isinstance(bindings2, dict):
        logger.warning(
            f"merge_bindings: Unexpected types: {type(bindings1)}, {type(bindings2)}"
        )
        return bindings1 if bindings1 is not None else bindings2

    # 辞書のマージ処理
    merged = bindings1.copy()

    for var, value in bindings2.items():
        if var in merged:
            # 競合がある場合、値の整合性をチェック
            existing_value = merged[var]

            # 両方が同じ値の場合は問題なし
            if existing_value == value:
                continue

            # 一方が変数で他方が具体値の場合、具体値を優先
            if isinstance(existing_value, Variable) and not isinstance(value, Variable):
                merged[var] = value
            elif not isinstance(existing_value, Variable) and isinstance(
                value, Variable
            ):
                # 既存の値が具体値なので変更しない
                continue

            # 両方が具体値で異なる場合は警告を出してbindings2を優先
            elif not isinstance(existing_value, Variable) and not isinstance(
                value, Variable
            ):
                logger.warning(
                    f"merge_bindings: Conflicting bindings for {var}: {existing_value} vs {value}. "
                    f"Using {value} from bindings2."
                )
                merged[var] = value

            # 両方が変数の場合もbindings2を優先
            else:
                merged[var] = value
        else:
            merged[var] = value

    return merged


def bindings_to_dict(bindings):
    """BindingEnvironmentまたは辞書を辞書形式に変換する

    Args:
        bindings: BindingEnvironmentインスタンスまたは辞書

    Returns:
        dict: バインディング辞書
    """
    from prolog.core.binding_environment import BindingEnvironment

    if bindings is None:
        return {}

    if isinstance(bindings, dict):
        return bindings.copy()

    if isinstance(bindings, BindingEnvironment):
        result = {}
        for var in bindings.parent:
            value = bindings.get_value(var)
            if value != var:  # 自分自身以外にバインドされている場合のみ
                result[var] = value
        return result

    logger.warning(f"bindings_to_dict: Unexpected type: {type(bindings)}")
    return {}


def dict_to_binding_environment(bindings_dict):
    """辞書をBindingEnvironmentに変換する

    Args:
        bindings_dict: バインディング辞書

    Returns:
        BindingEnvironment: 新しいバインディング環境
    """
    from prolog.core.binding_environment import BindingEnvironment

    env = BindingEnvironment()

    if bindings_dict:
        for var, value in bindings_dict.items():
            env.unify(var, value)

    return env


def unify_with_bindings(term1, term2, bindings=None):
    """2つの項を既存のバインディングに基づいて単一化する

    Args:
        term1: 単一化する項1
        term2: 単一化する項2
        bindings: 既存のバインディング（辞書またはBindingEnvironment、オプション）

    Returns:
        tuple: (成功したかどうか, 更新されたバインディング)
    """
    from prolog.core.binding_environment import BindingEnvironment

    # バインディング環境の準備
    if isinstance(bindings, BindingEnvironment):
        env = bindings.copy()
    elif isinstance(bindings, dict):
        env = dict_to_binding_environment(bindings)
    else:
        env = BindingEnvironment()

    # 単一化を試行
    success = env.unify(term1, term2)

    # 結果を返す（元のバインディングの形式に合わせる）
    if isinstance(bindings, dict):
        return success, bindings_to_dict(env)
    else:
        return success, env


def apply_substitution(term, bindings):
    """項にバインディングを適用して置換する

    Args:
        term: 置換する項
        bindings: バインディング（辞書またはBindingEnvironment）

    Returns:
        置換された項
    """
    from prolog.core.binding_environment import BindingEnvironment

    if hasattr(term, "substitute"):
        return term.substitute(bindings)

    # BindingEnvironmentの場合の直接処理
    if isinstance(bindings, BindingEnvironment):
        return bindings.get_value(term)

    # 辞書の場合
    if isinstance(bindings, dict) and term in bindings:
        return bindings[term]

    return term
