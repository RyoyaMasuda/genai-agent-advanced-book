"""
レポート生成スクリプト

データ分析の計画を生成し、複数のタスクを並行して実行した後、
実行結果を統合して最終的な分析レポートを生成します。

実行手順:
1. コマンドライン引数を解析
2. データフレームの概要を取得
3. LLMを使用して分析計画を生成
4. 各タスクを並行して実行
5. 実行結果を統合してレポートを生成
"""

import argparse
import io
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path


# src 下のファイルを読み込むために、sys.path にパスを追加
# これにより、srcディレクトリ内のモジュールをインポートできる
root_dir = Path(__file__).resolve().parents[1]
sys.path.append(str(root_dir))

from scripts.programmer import programmer_node
from src.models import Plan
from src.modules import (
    describe_dataframe,
    generate_plan,
    generate_report,
)


def main() -> None:
    """
    メイン処理
    
    コマンドライン引数を解析し、データ分析の計画を生成・実行し、
    最終的な分析レポートを生成します。
    """
    # コマンドライン引数の解析
    parser = argparse.ArgumentParser(description="データ分析レポート生成スクリプト")
    parser.add_argument("--data_file", type=str, default="data/sample.csv", help="分析対象のCSVファイル")
    parser.add_argument(
        "--user_request",
        type=str,
        default="scoreを最大化するための広告キャンペーンを検討したい",
        help="ユーザーの分析要求"
    )
    parser.add_argument("--process_id", type=str, default="sample", help="プロセスID")
    parser.add_argument("--model", type=str, default="gpt-4o-mini-2024-07-18", help="使用するLLMモデル")
    args = parser.parse_args()

    # 出力ディレクトリの設定と作成
    output_dir = Path("outputs") / args.process_id
    output_dir.mkdir(parents=True, exist_ok=True)

    # 計画生成フェーズ
    # CSVファイルを読み込み、データフレームの概要情報を取得
    with open(args.data_file, "rb") as fi:
        file_object = io.BytesIO(fi.read())
    data_info = describe_dataframe(file_object=file_object)
    
    # LLMを使用して分析計画を生成
    response = generate_plan(
        data_info=data_info,
        user_request=args.user_request,
        model=args.model,
    )
    plan: Plan = response.content

    # 各計画の実行フェーズ
    # ThreadPoolExecutorを使用して複数のタスクを並行実行
    with ThreadPoolExecutor() as executor:
        # 各タスクに対してprogrammer_nodeを実行するFutureオブジェクトを作成
        futures = [
            executor.submit(
                programmer_node,
                data_file=args.data_file,
                user_request=task.hypothesis,  # 各タスクの仮説をユーザー要求として使用
                model=args.model,  # 使用するLLMモデル
                process_id=f"sample-{idx}",  # プロセスID（タスク識別子）
                idx=idx,  # タスクのインデックス
            )
            for idx, task in enumerate(plan.tasks)  # 計画の各タスクに対して
        ]
        # 完了したタスクから順番に結果を取得
        _results = [future.result() for future in as_completed(futures)]

    # 実行結果の統合フェーズ
    # 各タスクの最後の（成功した）スレッドを収集
    process_data_threads = []
    for _, data_threads in sorted(_results, key=lambda x: x[0]):
        process_data_threads.append(data_threads[-1])

    # 最終レポート生成フェーズ
    # データの概要、ユーザー要求、実行結果を統合してレポートを生成
    response = generate_report(
        data_info=data_info,
        user_request=args.user_request,
        process_data_threads=process_data_threads,
        model=args.model,
        output_dir=output_dir,
    )


if __name__ == "__main__":
    # スクリプトが直接実行された場合のみmain関数を呼び出す
    main()
