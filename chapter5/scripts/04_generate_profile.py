"""
ペルソナ生成スクリプト

LLMを使用して、指定された役割（ロール）に基づいたペルソナ定義書を生成します。
プログラマの人格シミュレーションや役割特化型のAIアシスタント作成に使用されます。

実行手順:
1. ペルソナ要求（役割）を指定
2. LLMにペルソナ定義書の生成を依頼
3. 生成されたペルソナ定義書を整形
4. 結果を出力
"""

import re
import sys
from pathlib import Path

from jinja2 import Template
from loguru import logger


# src 下のファイルを読み込むために、sys.path にパスを追加
# これにより、srcディレクトリ内のモジュールをインポートできる
root_dir = Path(__file__).resolve().parents[1]
sys.path.append(str(root_dir))

from src.llms.apis import openai
from src.llms.models import LLMResponse


# ペルソナ生成用のプロンプトテンプレート
# Jinja2テンプレートを使用して、動的にペルソナ要求を埋め込む
PROMPT = """プログラマにおける人格シミュレーションを行うため、与えられたペルソナ要求から、そのペルソナ定義書を作成してください。
例えばペルソナ要求が "データサイエンティスト" である場合は、以下のように記述できます。

<ペルソナ定義書.例>
あなたは、データからルールを導き出し、ビジネスの意思決定を支援する優れたデータサイエンティストです。
PythonのAI・機械学習プログラミングに適した言語でデータマイニングを行うためのプログラムを開発し、データに基づいた合理的な意思決定をサポートします。
統計学などのデータ解析手法に基づいて、pandas, scikit-learn, matplotlib などのPythonライブラリを用いて大量のデータから法則性や関連性といった意味のある情報を抽出します。
</ペルソナ定義書.例>

生成対象となるペルソナは以下の通りです。
返答は "<ペルソナ定義書>\n" の文字列で開始すること。

<ペルソナ要求>
{{ role }}
</ペルソナ要求>"""


def generate_profile(
    role: str,
    model: str = "gpt-4o-mini-2024-07-18",
) -> LLMResponse:
    """
    指定された役割に基づいてペルソナ定義書を生成する
    
    Args:
        role: ペルソナの役割（例: "データサイエンティスト", "QAエンジニア"）
        model: 使用するLLMモデル名
        
    Returns:
        LLMResponse: 生成されたペルソナ定義書を含むレスポンス
    """
    # Jinja2テンプレートを使用してプロンプトを生成
    # {{ role }}の部分に実際の役割を埋め込む
    prompt_template = Template(source=PROMPT)
    message = prompt_template.render(role=role)
    
    # LLMを呼び出してペルソナ定義書を生成
    response = openai.generate_response(
        [{"role": "user", "content": message}],
        model=model,
    )
    
    # 生成されたテキストからHTMLタグを除去して整形
    # <ペルソナ定義書>などのタグを削除し、純粋なテキストのみを残す
    response.content = re.sub(r"<.*?>", "", response.content).strip()
    return response


def main() -> None:
    """
    メイン処理
    
    QAエンジニアのペルソナ定義書を生成し、
    その結果をログに出力します。
    """
    # 生成するペルソナの役割を指定
    role = "QAエンジニア"
    
    # ペルソナ定義書を生成
    response = generate_profile(role=role)
    
    # 生成されたペルソナ定義書をログに出力
    logger.info(response.content)


if __name__ == "__main__":
    # スクリプトが直接実行された場合のみmain関数を呼び出す
    main()
