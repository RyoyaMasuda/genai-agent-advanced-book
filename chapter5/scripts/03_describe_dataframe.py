"""
データフレーム概要生成スクリプト

CSVファイルを読み込み、データフレームの詳細な概要情報を生成します。
Jinja2テンプレートを使用して、データの情報を構造化された形式で出力します。

実行手順:
1. CSVファイルを読み込み
2. データフレームの基本情報を取得
3. サンプルデータと統計情報を生成
4. テンプレートを使用して概要を整形
5. 結果を出力
"""

import io
import sys
from pathlib import Path

import pandas as pd
from loguru import logger


# src 下のファイルを読み込むために、sys.path にパスを追加
# これにより、srcディレクトリ内のモジュールをインポートできる
root_dir = Path(__file__).resolve().parents[1]
sys.path.append(str(root_dir))

from src.llms.utils import load_template


def describe_dataframe(
    file_object: io.BytesIO,
    template_file: str,
) -> str:
    """
    データフレームの詳細な概要情報を生成する
    
    Args:
        file_object: CSVファイルのBytesIOオブジェクト
        template_file: 概要情報を整形するためのJinja2テンプレートファイルのパス
        
    Returns:
        str: データフレームの概要情報（テンプレートで整形済み）
    """
    # CSVファイルからデータフレームを作成
    df = pd.read_csv(file_object)
    
    # データフレームの基本情報を文字列として取得
    # StringIOを使用してdf.info()の出力をキャプチャ
    buf = io.StringIO()
    df.info(buf=buf)
    df_info = buf.getvalue()
    
    # Jinja2テンプレートを読み込み
    template = load_template(template_file)
    
    # テンプレートにデータを渡してレンダリング
    return template.render(
        df_info=df_info,  # データフレームの基本情報
        df_sample=df.sample(5).to_markdown(),  # ランダムサンプル5行（Markdown形式）
        df_describe=df.describe().to_markdown(),  # 統計情報（Markdown形式）
    )


def main() -> None:
    """
    メイン処理
    
    サンプルCSVファイルを読み込み、データフレームの概要情報を生成し、
    その結果をログに出力します。
    """
    # 設定値の定義
    data_file = "data/sample.csv"  # 分析対象のCSVファイル
    template_file = "src/prompts/describe_dataframe.jinja"  # 概要情報のテンプレート

    # CSVファイルをバイナリモードで読み込み、BytesIOオブジェクトとして渡す
    # describe_dataframe関数はBytesIOオブジェクトを期待している
    with open(data_file, "rb") as fi:
        file_object = io.BytesIO(fi.read())
    
    # データフレームの概要情報を生成
    data_info = describe_dataframe(file_object=file_object, template_file=template_file)
    
    # 生成された概要情報をログに出力
    logger.info(data_info)


if __name__ == "__main__":
    # スクリプトが直接実行された場合のみmain関数を呼び出す
    main()
