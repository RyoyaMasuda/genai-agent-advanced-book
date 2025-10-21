"""
レビュー生成モジュール

LLMを使用して、実行されたコードの結果をレビューし、
改善点や完了判定を行う機能を提供します。

このモジュールは、コードの実行結果（標準出力、標準エラー、結果データ）を
分析し、ユーザーの要求に対する達成度を評価し、必要に応じて
改善提案を行う役割を担います。
"""

import os
from src.llms.apis import openai
from src.llms.models import LLMResponse
from src.llms.utils import load_template
from src.models import DataThread, Review
from dotenv import load_dotenv

load_dotenv()
model = os.getenv("AZURE_OPENAI_GPT4O-MINI_DEPLOYMENT_NAME", "gpt-4o-mini-2024-07-18")

def generate_review(
    data_info: str,
    user_request: str,
    data_thread: DataThread,
    has_results: bool = False,
    remote_save_dir: str = "outputs/process_id/id",
    model: str = model,
    template_file: str = "src/prompts/generate_review.jinja",
) -> LLMResponse:
    """
    コードの実行結果をレビューし、改善点や完了判定を生成する
    
    Args:
        data_info: データフレームの概要情報
        user_request: ユーザーの分析要求
        data_thread: 実行されたコードの結果を含むデータスレッド
        has_results: 結果データ（画像・テキスト）を含むかどうか
        remote_save_dir: リモート保存ディレクトリのパス
        model: 使用するLLMモデル名
        template_file: レビュー生成用のプロンプトテンプレートファイルのパス
        
    Returns:
        LLMResponse: レビュー結果を含むレスポンス（Reviewモデル）
        
    Note:
        この関数は以下の処理を実行します：
        1. プロンプトテンプレートを読み込み、システム指示を生成
        2. 結果データがある場合、画像をBase64形式で変換
        3. 会話履歴を構築（システム指示、ユーザー要求、実行コード、結果）
        4. LLMを呼び出してレビューを生成
    """
    # プロンプトテンプレートを読み込み、システム指示を生成
    template = load_template(template_file)
    system_instruction = template.render(
        data_info=data_info,
        remote_save_dir=remote_save_dir,
    )
    
    # LLMとの会話履歴を構築
    messages = [
        {"role": "system", "content": system_instruction},  # システム指示
        {"role": "user", "content": user_request},  # ユーザーの要求
        {"role": "assistant", "content": data_thread.code},  # 実行されたコード
    ]
    
    # 結果データがある場合の処理
    if has_results:
        # 実行結果をLLMが理解できる形式に変換
        results = [
            {
                "type": "image_url",
                "image_url": {"url": f"data:image/jpeg;base64,{res['content']}"},
            }
            if res["type"] == "png"  # PNG画像の場合、Base64形式で画像URLとして設定
            else {"type": "text", "text": res["content"]}  # テキストの場合、そのまま設定
            for res in data_thread.results
        ]
        messages.append({"role": "system", "content": results})  # 結果データを追加
    
    # 残りのメッセージを追加
    messages.extend([
        {"role": "system", "content": f"stdout: {data_thread.stdout}"},  # 標準出力
        {"role": "system", "content": f"stderr: {data_thread.stderr}"},  # 標準エラー
        {
            "role": "user",
            "content": "実行結果に対するフィードバックを提供してください。",  # レビュー要求
        },
    ])
    
    # LLMを呼び出してレビューを生成
    # Reviewモデルを使用して構造化された出力を取得
    return openai.generate_response(
        messages,
        model=model,
        response_format=Review,
    )
