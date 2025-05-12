chcp 65001
@echo off
REM バッチファイルのあるディレクトリに移動
cd /d "%~dp0"
git diff 1ef4f41426d4c1b0d6fb0eb9880208741c9a3f68 -- prolog > output_src_diff.txt
