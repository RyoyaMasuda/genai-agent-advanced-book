"""
E2B Sandbox の基本的な使い方デモ

E2B Sandboxは、セキュアなクラウド環境でPythonコードを実行できるサービスです。
このスクリプトでは、E2B Sandboxの基本的な使用方法を示します。

実行手順:
1. 環境変数を読み込み
2. Sandboxインスタンスを作成
3. 簡単なPythonコードを実行
4. 実行結果を出力
"""

from dotenv import load_dotenv
from e2b_code_interpreter import Sandbox
from loguru import logger


def main() -> None:
    """
    メイン処理
    
    E2B Sandboxを使用してPythonコードを実行し、
    その結果をログに出力します。
    """
    # 環境変数を読み込み（E2B_API_KEYなど）
    load_dotenv()
    
    # E2B Sandboxインスタンスを作成し、コンテキストマネージャーとして使用
    # with文を使用することで、リソースの適切な管理が保証される
    with Sandbox() as sandbox:
        # 簡単なPythonコードを実行
        # "Hello World!"を出力するコードを実行
        execution = sandbox.run_code("print('Hello World!')")
    
    # 実行結果の標準出力をログに出力
    # execution.logs.stdoutはリスト形式なので、改行で結合して出力
    logger.info("\n".join(execution.logs.stdout))


if __name__ == "__main__":
    # スクリプトが直接実行された場合のみmain関数を呼び出す
    main()
