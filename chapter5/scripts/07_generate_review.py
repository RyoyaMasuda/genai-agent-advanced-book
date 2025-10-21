"""
コードレビュー生成スクリプト

データフレームの概要を取得し、コードを実行した後、
LLMを使用してコードの実行結果をレビューし、改善点を提案します。

実行手順:
1. CSVファイルからデータフレームの概要を取得
2. E2B Sandboxでコードを実行
3. LLMを使用して実行結果をレビュー
4. レビュー結果を出力
"""

import io
import sys
from pathlib import Path

from dotenv import load_dotenv
from e2b_code_interpreter import Sandbox
from loguru import logger


# src 下のファイルを読み込むために、sys.path にパスを追加
# これにより、srcディレクトリ内のモジュールをインポートできる
root_dir = Path(__file__).resolve().parents[1]
sys.path.append(str(root_dir))

from src.modules import (
    describe_dataframe,
    execute_code,
    generate_review,
    set_dataframe,
)


# 環境変数を読み込み（E2B_API_KEYなど）
load_dotenv()


def main() -> None:
    """
    メイン処理
    
    データフレームの概要を取得し、コードを実行した後、
    LLMを使用してコードの実行結果をレビューします。
    """
    # 設定値の定義
    process_id = "07_generate_review"  # プロセスID（実行識別子）
    data_path = "data/sample.csv"  # 分析対象のCSVファイル
    template_file = "src/prompts/generate_review.jinja"  # レビュー生成用テンプレート
    user_request = "データフレームのサイズを確認する"  # ユーザーの要求

    # CSVファイルを読み込み、データフレームの概要情報を取得
    with open(data_path, "rb") as fi:
        file_object = io.BytesIO(fi.read())
    data_info = describe_dataframe(file_object=file_object, template_file=template_file)

    # E2B Sandboxを使用してコードを実行
    with Sandbox() as sandbox:
        # CSVファイルをデータフレームとしてSandboxに読み込み
        with open(data_path, "rb") as fi:
            set_dataframe(sandbox=sandbox, file_object=io.BytesIO(fi.read()))
        
        # データフレームの形状を確認するコードを実行
        data_thread = execute_code(
            process_id=process_id,
            thread_id=0,
            sandbox=sandbox,
            user_request=user_request,
            code="print(df.shape)",  # 実行するPythonコード
        )
        
        # 実行結果をログに出力
        logger.info(data_thread.model_dump())

    # LLMを使用してコードの実行結果をレビュー
    # ユーザーの要求、データの概要、実行結果を基にレビューを生成
    response = generate_review(
        user_request=user_request,
        data_info=data_info,
        data_thread=data_thread,
    )
    
    # レビュー結果を取得し、JSON形式で出力
    review = response.content
    if isinstance(review, dict):
        import json
        logger.info(json.dumps(review, indent=4, ensure_ascii=False))
    else:
        logger.info(str(review))


if __name__ == "__main__":
    # スクリプトが直接実行された場合のみmain関数を呼び出す
    main()
