"""
プログラマーノード実行スクリプト

programmer_node関数を使用して、データ分析のためのコード生成・実行・レビューの
一連のプロセスを実行します。自己修正機能により、エラーが発生した場合に
自動的にコードを改善します。

実行手順:
1. programmer_node関数を呼び出し
2. コード生成・実行・レビューのサイクルを実行
3. 実行結果を詳細に出力
"""

import sys
from pathlib import Path

from loguru import logger


# src 下のファイルを読み込むために、sys.path にパスを追加
# これにより、srcディレクトリ内のモジュールをインポートできる
root_dir = Path(__file__).resolve().parents[1]
sys.path.append(str(root_dir))

from scripts.programmer import programmer_node


def main() -> None:
    """
    メイン処理
    
    programmer_node関数を使用してデータ分析のためのコード生成・実行・レビューの
    一連のプロセスを実行し、その結果を詳細に出力します。
    """
    # programmer_node関数を実行
    # データファイル、ユーザー要求、プロセスIDを指定
    _, data_threads = programmer_node(
        data_file="data/sample.csv",  # 分析対象のCSVファイル
        # user_request="データ概要について教えて",  # コメントアウトされた要求
        user_request="スコアの分布を可視化して",  # 実際に使用される要求
        process_id="08_programmer",  # プロセスID（実行識別子）
    )

    # 実行結果の統計情報を出力
    logger.info(f"試行回数: {len(data_threads)}")
    
    # 各試行の詳細結果を出力
    for idx, data_thread in enumerate(data_threads):
        print("\n\n")
        print(f"##### {idx} #####")
        
        # 生成されたコードを出力
        print(data_thread.code)
        print("=" * 80)
        
        # 標準出力を出力
        print(data_thread.stdout)
        
        # 標準エラーを出力
        print(data_thread.stderr)
        print("-" * 80)
        
        # レビュー結果（観測結果）を出力
        print(data_thread.observation)
        
        # 完了フラグを出力
        print(f"is_completed: {data_thread.is_completed}")


if __name__ == "__main__":
    # スクリプトが直接実行された場合のみmain関数を呼び出す
    main()
