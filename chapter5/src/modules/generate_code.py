"""
コード生成モジュール

データ分析のためのPythonコードを生成する機能を提供します。
LLMを使用してユーザーの要求に基づいたコードを生成し、
前回の実行結果があればそれを参考にしてコードを改善します。
"""

import os
from src.llms.apis import openai
from src.llms.models import LLMResponse
from src.llms.utils import load_template
from src.models import DataThread, Program
from dotenv import load_dotenv

load_dotenv("/home/ryoyamasuda/Documents/genai-agent-advanced-book/chapter5/.env")

# Azure OpenAIのモデル名を取得, OpenAIの場合はデフォルト値を使用
model = os.getenv("AZURE_OPENAI_GPT4O-MINI_DEPLOYMENT_NAME", "gpt-4o-mini-2024-07-18")

def generate_code(
    data_info: str,
    user_request: str,
    remote_save_dir: str = "outputs/process_id/id",
    previous_thread: DataThread | None = None,
    model: str = model,
    template_file: str = "src/prompts/generate_code.jinja",
) -> LLMResponse:
    """
    データ分析用のPythonコードを生成する
    
    Args:
        data_info: データフレームの概要情報（describe_dataframeの出力）
        user_request: ユーザーからの分析要求
        remote_save_dir: リモート保存ディレクトリのパス
        previous_thread: 前回の実行結果（エラー修正時に使用）
        model: 使用するLLMモデル名
        template_file: プロンプトテンプレートファイルのパス
        
    Returns:
        LLMResponse: 生成されたコードとメタデータを含むレスポンス
    """
    # プロンプトテンプレートを読み込み、データ情報と保存先を設定
    template = load_template(template_file)
    system_message = template.render(
        data_info=data_info,
        remote_save_dir=remote_save_dir,
    )
    
    # 基本的なメッセージ構成：システムプロンプト + ユーザー要求
    messages = [
        {"role": "system", "content": system_message},
        {"role": "user", "content": f"タスク要求: {user_request}"},
    ]
    
    # 自己修正機能：前回の実行結果があれば、それを参考にしてコードを改善
    if previous_thread:
        # 前回生成されたコードを追加（アシスタントの回答として）
        # これによりLLMは前回のコードを理解し、改善点を把握できる
        if previous_thread.code:
            messages.append({"role": "assistant", "content": previous_thread.code})
        
        # 前回の実行結果（標準出力・標準エラー）を追加
        # エラーメッセージや出力結果から問題点を特定し、修正できる
        if previous_thread.stdout and previous_thread.stderr:
            messages.extend(
                [
                    {"role": "system", "content": f"stdout: {previous_thread.stdout}"},
                    {"role": "system", "content": f"stderr: {previous_thread.stderr}"},
                ],
            )
        
        # 前回の観測結果（レビュー結果など）を追加
        # 人間によるフィードバックがあれば、それを反映してコードを再生成
        if previous_thread.observation:
            messages.append(
                {
                    "role": "user",
                    "content": f"以下を参考にして、ユーザー要求を満たすコードを再生成してください: {previous_thread.observation}",
                },
            )
    
    # LLMを呼び出してコードを生成
    # Programモデルを使用して構造化された出力（達成条件、実行計画、コード）を取得
    return openai.generate_response(
        messages,
        model=model,
        response_format=Program,
    )
