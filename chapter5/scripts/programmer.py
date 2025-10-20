"""
プログラマーノード実装

データ分析のためのコード生成・実行・レビューの一連のプロセスを
自己修正機能付きで実行するコア機能を提供します。

主な機能:
- データフレームの概要取得
- LLMを使用したコード生成
- E2B Sandboxでのコード実行
- 実行結果のレビューと自己修正
- 複数回の試行による改善
"""

import io

from e2b_code_interpreter import Sandbox
from loguru import logger

from src.models import DataThread
from src.modules import (
    describe_dataframe,
    execute_code,
    generate_code,
    generate_review,
    set_dataframe,
)


def programmer_node(
    data_file: str,
    user_request: str,
    process_id: str,
    model: str = "gpt-4o-mini-2024-07-18",
    n_trial: int = 3,
    idx: int = 0,
) -> tuple[int, list[DataThread]]:
    """
    プログラマーノードのメイン処理
    
    データ分析のためのコード生成・実行・レビューのサイクルを実行し、
    エラーが発生した場合は自己修正機能により改善を試みます。
    
    Args:
        data_file: 分析対象のCSVファイルのパス
        user_request: ユーザーの分析要求
        process_id: プロセスID（実行識別子）
        model: 使用するLLMモデル名
        n_trial: 最大試行回数（デフォルト: 3回）
        idx: タスクのインデックス
        
    Returns:
        tuple[int, list[DataThread]]: タスクインデックスと実行結果のリスト
    """
    # データフレームの概要情報を取得
    template_file = "src/prompts/describe_dataframe.jinja"
    with open(data_file, "rb") as fi:
        file_object = io.BytesIO(fi.read())
    data_info = describe_dataframe(file_object=file_object, template_file=template_file)
    
    # 実行結果を格納するリスト
    data_threads: list[DataThread] = []
    
    # E2B Sandboxを使用してコードを実行
    with Sandbox() as sandbox:
        # CSVファイルをデータフレームとしてSandboxに読み込み
        with open(data_file, "rb") as fi:
            set_dataframe(sandbox=sandbox, file_object=fi)
        
        # 最大n_trial回まで試行を繰り返す
        for thread_id in range(n_trial):
            # 5.4.1. コード生成フェーズ
            # 前回の実行結果があれば、それを参考にしてコードを改善
            previous_thread = data_threads[-1] if data_threads else None
            response = generate_code(
                data_info=data_info,
                user_request=user_request,
                previous_thread=previous_thread,  # 自己修正のための前回結果
                model=model,
            )
            program = response.content
            
            # 生成されたコードの詳細をログに出力
            logger.info(program.model_dump_json())
            
            # 5.4.2. コード実行フェーズ
            data_thread = execute_code(
                sandbox,
                process_id=process_id,
                thread_id=thread_id,
                code=program.code,  # 生成されたコードを実行
                user_request=user_request,
            )
            
            # 実行結果のログ出力
            if data_thread.stdout:
                logger.debug(f"{data_thread.stdout=}")
            if data_thread.stderr:
                logger.warning(f"{data_thread.stderr=}")
            
            # 5.4.3. レビュー生成フェーズ
            response = generate_review(
                user_request=user_request,
                data_info=data_info,
                data_thread=data_thread,
                model=model,
            )
            review = response.content
            
            # レビュー結果の詳細をログに出力
            logger.info(review.model_dump_json())
            
            # データスレッドにレビュー結果を追加
            data_thread.observation = review.observation  # レビューの観察結果
            data_thread.is_completed = review.is_completed  # 完了フラグ
            
            # 実行結果をリストに追加
            data_threads.append(data_thread)
            
            # 終了条件チェック
            if data_thread.is_completed:
                # タスクが完了した場合、成功ログを出力してループを終了
                logger.success(f"{user_request=}")
                logger.success(f"{program.code=}")
                logger.success(f"{review.observation=}")
                break
    
    # タスクインデックスと実行結果のリストを返す
    return idx, data_threads
