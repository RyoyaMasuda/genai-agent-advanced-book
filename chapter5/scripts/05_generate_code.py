"""
コード生成スクリプト

データフレームの概要を取得し、ユーザーの要求に基づいて
データ分析用のPythonコードを生成するデモスクリプトです。

実行手順:
1. CSVファイルを読み込み
2. データフレームの概要情報を取得
3. LLMを使用してコードを生成
4. 生成されたコードをJSON形式で出力
"""

import io
import sys
from pathlib import Path

from loguru import logger


# src 下のファイルを読み込むために、sys.path にパスを追加
# これにより、srcディレクトリ内のモジュールをインポートできる
root_dir = Path(__file__).resolve().parents[1]
sys.path.append(str(root_dir))

from src.modules import describe_dataframe, generate_code
from src.models import Program


def main() -> None:
    """
    メイン処理
    
    データファイルを読み込み、データの概要を取得し、
    ユーザーの要求に基づいてコードを生成します。
    """
    # 設定値の定義
    data_path = "data/sample.csv"  # 分析対象のCSVファイル
    template_file = "src/prompts/generate_code.jinja"  # プロンプトテンプレート
    user_request = "データの概要について教えて"  # ユーザーの分析要求

    # CSVファイルをバイナリモードで読み込み、BytesIOオブジェクトとして渡す
    # describe_dataframe関数はBytesIOオブジェクトを期待している
    with open(data_path, "rb") as fi:
        file_object = io.BytesIO(fi.read())
    
    # データフレームの概要情報を取得
    # テンプレートファイルを使用してデータの詳細情報を整形
    data_info = describe_dataframe(file_object=file_object, template_file=template_file)

    # LLMを使用してコードを生成
    # データの概要情報とユーザーの要求を基に、分析用のPythonコードを生成
    response = generate_code(
        data_info=data_info,
        user_request=user_request,
    )
    
    # 生成されたコードの内容を取得
    program = response.content
    
    # 生成されたコードを適切な形式で出力
    # Programモデルの場合はJSON形式、その他の場合は文字列として出力
    if isinstance(program, Program):
        # Programモデル（構造化された出力）の場合
        # achievement_condition, execution_plan, codeが含まれる
        logger.info("=== 生成されたコード ===")
        logger.info(program.model_dump_json(indent=4))
    elif isinstance(program, dict):
        # 辞書形式の場合（フォールバック）
        import json
        logger.info("=== 生成されたコード（辞書形式） ===")
        logger.info(json.dumps(program, indent=4, ensure_ascii=False))
    else:
        # 文字列形式の場合（フォールバック）
        logger.info("=== 生成されたコード（文字列形式） ===")
        logger.info(program)


if __name__ == "__main__":
    # スクリプトが直接実行された場合のみmain関数を呼び出す
    main()
