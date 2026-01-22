# ベンチマークテストの実行

軽量もしくは重量なベンチマークテストを実行して報告

1. ユーザから軽量/重量のどちらを実施するかを聴取

軽量=bench_light
重量=bench_heavy

2. テスト実施

uv run python -m cProfile -s cumtime -m pytest -m {選択したテスト} -o addopts= > .claude/tmp/profile_{選択したテスト}.txt

3. 結果を分析

テスト結果を分析してユーザに報告