"""
コード実行スクリプト

E2B Sandboxを使用してPythonコードを実行し、
データフレームの操作をデモンストレーションします。

実行手順:
1. E2B Sandboxインスタンスを作成
2. CSVファイルをデータフレームとして読み込み
3. 指定されたPythonコードを実行
4. 実行結果をJSON形式で出力
"""

import io
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from e2b_code_interpreter import Sandbox

from rich import print

# src 下のファイルを読み込むために、sys.path にパスを追加
# これにより、srcディレクトリ内のモジュールをインポートできる
root_dir = Path(__file__).resolve().parents[1]
sys.path.append(str(root_dir))

from src.modules import execute_code, set_dataframe


# 環境変数を読み込み（E2B_API_KEYなど）
load_dotenv()


def main() -> None:
    """
    メイン処理
    
    E2B Sandboxを使用してデータフレームの操作を実行し、
    その結果をJSON形式で出力します。
    """
    # E2B Sandboxインスタンスを作成し、コンテキストマネージャーとして使用
    # with文を使用することで、リソースの適切な管理が保証される
    with Sandbox() as sandbox:
        # CSVファイルをデータフレームとしてSandboxに読み込み
        # set_dataframe関数を使用して、dfという変数名でデータフレームを作成
        with open("data/sample.csv", "rb") as fi:
            set_dataframe(sandbox=sandbox, file_object=io.BytesIO(fi.read()))
        
        # データフレームの形状（行数・列数）を確認するコードを実行
        data_thread = execute_code(
            sandbox=sandbox,  # E2B Sandboxインスタンス
            process_id="06_execute_code",  # プロセスID（実行識別子）
            thread_id=0,  # スレッドID（試行回数）
            code="print(df.shape)",  # 実行するPythonコード
        )
        
        # 実行結果をJSON形式で出力
        # data_threadには実行結果、標準出力、標準エラーなどが含まれる
        print(data_thread.model_dump_json(indent=4))


if __name__ == "__main__":
    # スクリプトが直接実行された場合のみmain関数を呼び出す
    main()
