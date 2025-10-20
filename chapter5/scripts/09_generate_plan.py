"""
計画生成スクリプト

データフレームの概要を取得し、ユーザーの要求に基づいて
データ分析のための実行計画を生成します。

実行手順:
1. CSVファイルを読み込み
2. データフレームの概要情報を取得
3. LLMを使用して分析計画を生成
4. 生成された計画をJSON形式で出力
"""

import io
import sys
from pathlib import Path

from loguru import logger


# src 下のファイルを読み込むために、sys.path にパスを追加
# これにより、srcディレクトリ内のモジュールをインポートできる
root_dir = Path(__file__).resolve().parents[1]
sys.path.append(str(root_dir))

from src.modules import describe_dataframe, generate_plan


def main() -> None:
    """
    メイン処理
    
    データファイルを読み込み、データの概要を取得し、
    ユーザーの要求に基づいて分析計画を生成します。
    """
    # 設定値の定義
    data_path = "data/sample.csv"  # 分析対象のCSVファイル
    template_file = "src/prompts/generate_plan.jinja"  # 計画生成用テンプレート
    user_request = "scoreを最大化するための広告キャンペーンを検討したい"  # ユーザーの要求

    # CSVファイルをバイナリモードで読み込み、BytesIOオブジェクトとして渡す
    # describe_dataframe関数はBytesIOオブジェクトを期待している
    with open(data_path, "rb") as fi:
        file_object = io.BytesIO(fi.read())
    
    # データフレームの概要情報を取得
    # テンプレートファイルを使用してデータの詳細情報を整形
    data_info = describe_dataframe(file_object=file_object, template_file=template_file)

    # LLMを使用して分析計画を生成
    # データの概要情報とユーザーの要求を基に、分析のための実行計画を生成
    response = generate_plan(
        data_info=data_info,
        user_request=user_request,
        model="gpt-4o-mini-2024-07-18",
    )
    
    # 生成された計画の内容を取得
    plan = response.content
    
    # 生成された計画をJSON形式で出力
    # planには分析の目的、仮説、実行手順などが含まれる
    logger.info(plan.model_dump_json(indent=4))


if __name__ == "__main__":
    # スクリプトが直接実行された場合のみmain関数を呼び出す
    main()
