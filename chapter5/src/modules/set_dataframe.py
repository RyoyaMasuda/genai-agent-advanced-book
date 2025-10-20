"""
データフレーム設定モジュール

E2B Sandbox環境にCSVファイルをアップロードし、
pandasを使用してデータフレームとして読み込む機能を提供します。

このモジュールは、リモートのSandbox環境でデータ分析を行うために
ローカルのCSVファイルをリモート環境に転送し、データフレームとして
利用可能にする役割を担います。
"""

import io

from e2b_code_interpreter import Sandbox
from e2b_code_interpreter.models import Execution


def set_dataframe(
    sandbox: Sandbox,
    file_object: io.BytesIO,
    timeout: int = 1200,
    remote_data_path: str = "/home/data.csv",
) -> Execution:
    """
    E2B Sandbox環境にCSVファイルをアップロードし、データフレームとして読み込む
    
    Args:
        sandbox: E2B Sandboxインスタンス
        file_object: アップロードするCSVファイルのBytesIOオブジェクト
        timeout: コード実行のタイムアウト時間（秒、デフォルト: 1200秒）
        remote_data_path: リモート環境でのファイル保存パス（デフォルト: "/home/data.csv"）
        
    Returns:
        Execution: データフレーム読み込みの実行結果
        
    Note:
        この関数は以下の処理を順次実行します：
        1. CSVファイルをリモート環境に書き込み
        2. pandasを使用してデータフレームとして読み込み
        3. 'df'という変数名でデータフレームを利用可能にする
    """
    # CSVファイルをリモート環境の指定パスに書き込み
    # file_objectの内容をremote_data_pathに保存
    sandbox.files.write(remote_data_path, file_object)
    
    # pandasを使用してCSVファイルをデータフレームとして読み込み
    # 'df'という変数名でデータフレームを作成し、後続の処理で利用可能にする
    return sandbox.run_code(
        f"import pandas as pd; df = pd.read_csv('{remote_data_path}')",
        timeout=timeout,
    )
