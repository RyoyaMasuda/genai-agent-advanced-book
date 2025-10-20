"""
Jinja2テンプレートエンジンの基本的な使い方デモ

Jinja2は、Pythonで使用できるテンプレートエンジンです。
動的なコンテンツ生成やプロンプトの作成に使用されます。

このスクリプトでは、Jinja2の基本的な使用方法を示します：
- テンプレートの作成
- 変数の埋め込み
- 条件分岐の使用
- テンプレートのレンダリング
"""

from jinja2 import Template


def main() -> None:
    """
    メイン処理
    
    Jinja2テンプレートの基本的な使用方法をデモンストレーションします。
    条件分岐と変数の埋め込み機能を示します。
    """
    # Jinja2テンプレートのソースコードを定義
    # {% if message %} ... {% endif %} で条件分岐
    # {{ message }} で変数の値を埋め込み
    source = """{% if message %}メッセージがあります: {{ message }}{% endif %}"""
    
    # テンプレートオブジェクトを作成
    template = Template(source=source)

    # 1. message引数を指定してテンプレートをレンダリング
    # 条件分岐がTrueになり、メッセージが表示される
    print("1.", template.render(message="hello"))
    
    # 2. message引数を指定せずにテンプレートをレンダリング
    # 条件分岐がFalseになり、何も表示されない
    print("2.", template.render())


if __name__ == "__main__":
    # スクリプトが直接実行された場合のみmain関数を呼び出す
    main()
