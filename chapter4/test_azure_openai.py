#!/usr/bin/env python3
"""
Azure OpenAI の設定をテストするスクリプト
"""
from openai import OpenAI
from src.configs import Settings


def test_settings():
    """設定が正しく読み込まれているかテスト"""
    print("=" * 60)
    print("1. 設定の読み込みテスト")
    print("=" * 60)
    
    settings = Settings()
    
    # Azure OpenAI の設定確認
    if settings.azure_openai_api_key:
        print("✅ Azure OpenAI の設定が見つかりました")
        print(f"   Endpoint: {settings.azure_openai_endpoint}")
        print(f"   Deployment: {settings.azure_openai_deployment_name}")
        print(f"   Embedding Deployment: {settings.azure_openai_embedding_deployment_name}")
        print(f"   API Version: {settings.azure_openai_api_version}")
        return settings, True
    elif settings.openai_api_key:
        print("✅ OpenAI の設定が見つかりました")
        print(f"   Model: {settings.openai_model}")
        return settings, False
    else:
        print("❌ OpenAI または Azure OpenAI の設定が見つかりません")
        print("   .env ファイルを確認してください")
        return None, None


def test_chat_completion(settings: Settings, is_azure: bool):
    """チャット補完のテスト"""
    print("\n" + "=" * 60)
    print("2. チャット補完テスト")
    print("=" * 60)
    
    try:
        # クライアントの初期化
        if is_azure:
            print(f"Azure OpenAI に接続中...")
            client = OpenAI(
                api_key=settings.azure_openai_api_key,
                base_url=f"{settings.azure_openai_endpoint}/openai/deployments/{settings.azure_openai_deployment_name}",
                default_query={"api-version": settings.azure_openai_api_version},
            )
        else:
            print(f"OpenAI に接続中...")
            client = OpenAI(api_key=settings.openai_api_key)
        
        # 簡単なテストメッセージ
        print("テストメッセージを送信中...")
        response = client.chat.completions.create(
            model=settings.openai_model if not is_azure else settings.azure_openai_deployment_name,
            messages=[
                {"role": "system", "content": "あなたは親切なアシスタントです。"},
                {"role": "user", "content": "こんにちは！元気ですか？"}
            ],
            max_tokens=50
        )
        
        print("✅ チャット補完が成功しました")
        print(f"   応答: {response.choices[0].message.content}")
        return True
        
    except Exception as e:
        print(f"❌ チャット補完でエラーが発生しました")
        print(f"   エラー内容: {str(e)}")
        return False


def test_embedding(settings: Settings, is_azure: bool):
    """Embedding のテスト"""
    print("\n" + "=" * 60)
    print("3. Embedding生成テスト")
    print("=" * 60)
    
    try:
        # クライアントの初期化
        if is_azure:
            print(f"Azure OpenAI (Embedding) に接続中...")
            client = OpenAI(
                api_key=settings.azure_openai_api_key,
                base_url=f"{settings.azure_openai_endpoint}/openai/deployments/{settings.azure_openai_embedding_deployment_name}",
                default_query={"api-version": settings.azure_openai_api_version},
            )
        else:
            print(f"OpenAI (Embedding) に接続中...")
            client = OpenAI(api_key=settings.openai_api_key)
        
        # テストテキスト
        test_text = "これはテストです"
        print(f"テストテキストをベクトル化中: '{test_text}'")
        
        embedding = client.embeddings.create(
            model="text-embedding-3-small",
            input=test_text
        )
        
        vector = embedding.data[0].embedding
        print(f"✅ Embedding生成が成功しました")
        print(f"   ベクトル次元数: {len(vector)}")
        print(f"   最初の5要素: {vector[:5]}")
        return True
        
    except Exception as e:
        print(f"❌ Embedding生成でエラーが発生しました")
        print(f"   エラー内容: {str(e)}")
        return False


def main():
    print("\n🔍 Azure OpenAI 設定テストを開始します\n")
    
    # 1. 設定の読み込み
    settings, is_azure = test_settings()
    
    if settings is None:
        print("\n❌ テスト失敗: 設定が読み込めませんでした")
        return
    
    # 2. チャット補完テスト
    chat_ok = test_chat_completion(settings, is_azure)
    
    # 3. Embedding テスト
    embedding_ok = test_embedding(settings, is_azure)
    
    # 結果サマリー
    print("\n" + "=" * 60)
    print("テスト結果サマリー")
    print("=" * 60)
    print(f"設定読み込み: ✅")
    print(f"チャット補完: {'✅' if chat_ok else '❌'}")
    print(f"Embedding生成: {'✅' if embedding_ok else '❌'}")
    
    if chat_ok and embedding_ok:
        print("\n🎉 すべてのテストが成功しました！")
        if is_azure:
            print("   Azure OpenAI が正しく動作しています。")
        else:
            print("   OpenAI が正しく動作しています。")
    else:
        print("\n⚠️  一部のテストが失敗しました。")
        print("   .env ファイルの設定を確認してください。")


if __name__ == "__main__":
    main()

