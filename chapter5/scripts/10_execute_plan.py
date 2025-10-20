"""
計画実行スクリプト

データ分析の計画を生成し、複数のタスクを並行して実行します。
各タスクの結果を画像やテキストファイルとして保存します。

実行手順:
1. データフレームの概要を取得
2. LLMを使用して分析計画を生成
3. 各タスクを並行して実行
4. 実行結果をファイルとして保存
"""

import base64
import io
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from io import BytesIO
from pathlib import Path

from loguru import logger
from PIL import Image


# src 下のファイルを読み込むために、sys.path にパスを追加
# これにより、srcディレクトリ内のモジュールをインポートできる
root_dir = Path(__file__).resolve().parents[1]
sys.path.append(str(root_dir))

from scripts.programmer import programmer_node
from src.models import Plan
from src.modules import (
    describe_dataframe,
    generate_plan,
)


def main() -> None:
    """
    メイン処理
    
    データ分析の計画を生成し、複数のタスクを並行して実行し、
    その結果をファイルとして保存します。
    """
    # 設定値の定義
    data_file = "data/sample.csv"  # 分析対象のCSVファイル
    template_file = "src/prompts/generate_plan.jinja"  # 計画生成用テンプレート
    user_request = "scoreを最大化するための広告キャンペーンを検討したい"  # ユーザーの要求
    output_dir = "outputs/tmp"  # 出力ディレクトリ
    
    # 出力ディレクトリを作成（存在しない場合）
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    
    # 計画生成フェーズ
    # CSVファイルを読み込み、データフレームの概要情報を取得
    with open(data_file, "rb") as fi:
        file_object = io.BytesIO(fi.read())
    data_info = describe_dataframe(file_object=file_object, template_file=template_file)
    
    # LLMを使用して分析計画を生成
    response = generate_plan(
        data_info=data_info,
        user_request=user_request,
        model="gpt-4o-mini-2024-07-18",
    )
    plan: Plan = response.content

    # 各計画の実行フェーズ
    # ThreadPoolExecutorを使用して複数のタスクを並行実行
    with ThreadPoolExecutor() as executor:
        # 各タスクに対してprogrammer_nodeを実行するFutureオブジェクトを作成
        futures = [
            executor.submit(
                programmer_node,
                data_file=data_file,
                user_request=task.hypothesis,  # 各タスクの仮説をユーザー要求として使用
                # model="o3-mini-2025-01-31",  # コメントアウトされたモデル
                model="gpt-4o-2024-11-20",  # 使用するLLMモデル
                process_id=f"sample-{idx}",  # プロセスID（タスク識別子）
                idx=idx,  # タスクのインデックス
            )
            for idx, task in enumerate(plan.tasks)  # 計画の各タスクに対して
        ]
        # 完了したタスクから順番に結果を取得
        _results = [future.result() for future in as_completed(futures)]

    # 実行結果の保存フェーズ
    # タスクのインデックス順にソートして結果を保存
    for _, data_threads in sorted(_results, key=lambda x: x[0]):
        data_thread = data_threads[-1]  # 最後の（成功した）スレッドを取得
        output_file = f"{output_dir}/{data_thread.process_id}_{data_thread.thread_id}."
        
        if data_thread.is_completed:
            # タスクが完了している場合、結果をファイルとして保存
            for i, res in enumerate(data_thread.results):
                if res["type"] == "png":
                    # PNG画像の場合、Base64デコードして画像ファイルとして保存
                    image = Image.open(BytesIO(base64.b64decode(res["content"])))
                    image.save(f"{output_file}_{i}.png")
                else:
                    # テキストの場合、テキストファイルとして保存
                    with open(f"{output_file}_{i}.txt", "w") as f:
                        f.write(res["content"])
        else:
            # タスクが完了していない場合、警告を出力
            logger.warning(f"{data_thread.user_request=} is not completed.")


if __name__ == "__main__":
    # スクリプトが直接実行された場合のみmain関数を呼び出す
    main()
