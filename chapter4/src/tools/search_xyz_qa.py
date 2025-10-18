# LangChainのtoolデコレーターをインポート（ツールとして関数を登録するため）
from langchain.tools import tool
# OpenAI APIクライアントをインポート（Embeddingの生成に使用）
from openai import OpenAI
# Pydanticの基底クラスとFieldをインポート（入力スキーマの定義と検証に使用）
from pydantic import BaseModel, Field
# Qdrant（ベクトルデータベース）のクライアントをインポート
from qdrant_client import QdrantClient

# アプリケーション設定（API キーなど）を読み込むためのモジュール
from src.configs import Settings
# カスタムロガーのセットアップ関数をインポート
from src.custom_logger import setup_logger
# 検索結果を格納するデータモデルをインポート
from src.models import SearchOutput

# 検索結果の最大取得数（類似度の高い上位3件を取得）
MAX_SEARCH_RESULTS = 3

# このモジュール用のロガーを初期化
logger = setup_logger(__name__)


# 入力スキーマを定義するクラス
# Pydanticを使って、ツールへの入力パラメータを型安全に定義
class SearchQueryInput(BaseModel):
    # 検索クエリ文字列（ユーザーの質問や検索したい内容）
    query: str = Field(description="検索クエリ")


# LangChainのtoolデコレーターを使って、検索機能をツール化
# args_schemaで入力スキーマを指定することで、LLMがツールの使い方を理解できる
@tool(args_schema=SearchQueryInput)
def search_xyz_qa(query: str) -> list[SearchOutput]:
    """
    XYZシステムの過去の質問回答ペアを検索する関数。
    ベクトル検索を使って、入力されたクエリに意味的に類似した質問回答ペアを取得する。
    キーワード検索では見つからない類似の質問や言い換え表現にも対応可能。
    """

    # 検索処理の開始をログに記録
    logger.info(f"Searching XYZ QA by query: {query}")

    # Qdrantクライアントのインスタンスを作成し、ローカルのQdrantに接続
    # Qdrantはベクトル検索に特化したデータベース
    qdrant_client = QdrantClient("http://localhost:6333")

    # 設定ファイルから各種設定値（API キーなど）を読み込む
    settings = Settings()
    
    # OpenAI APIクライアントを初期化（Embedding生成に使用）
    # Azure OpenAIの設定がある場合はAzure OpenAIを使用、なければ通常のOpenAIを使用
    if settings.azure_openai_api_key:
        # Azure OpenAI用の初期化（Embedding用デプロイメントを使用）
        openai_client = OpenAI(
            api_key=settings.azure_openai_api_key,
            base_url=f"{settings.azure_openai_endpoint}/openai/deployments/{settings.azure_openai_embedding_deployment_name}",
            default_query={"api-version": settings.azure_openai_api_version},
        )
    else:
        # 通常のOpenAI用の初期化
        openai_client = OpenAI(api_key=settings.openai_api_key)

    # クエリテキストをベクトル化する処理の開始をログに記録
    logger.info("Generating embedding vector from input query")
    # OpenAIのEmbedding APIを使って、入力クエリをベクトル（数値の配列）に変換
    # text-embedding-3-small モデルを使用（高速かつコスト効率が良い）
    # ベクトル化することで、意味的に類似したテキストを数学的に比較できる
    query_vector = (
        openai_client.embeddings.create(input=query, model="text-embedding-3-small")
        .data[0]
        .embedding
    )

    # Qdrantでベクトル検索を実行
    # collection_name: 検索対象のコレクション名
    # query: 検索クエリのベクトル
    # limit: 取得する結果の最大数
    # 戻り値のpointsプロパティから検索結果のポイント（データ点）を取得
    search_results = qdrant_client.query_points(
        collection_name="documents", query=query_vector, limit=MAX_SEARCH_RESULTS
    ).points

    # 検索結果の件数をログに記録
    logger.info(f"Search results: {len(search_results)} hits")
    
    # 検索結果を格納するリストを初期化
    outputs = []

    # 検索結果からヒットしたポイント（質問回答ペア）を1つずつ処理
    for point in search_results:
        # カスタムモデルSearchOutputのfrom_pointメソッドを使って、
        # Qdrantのポイントオブジェクトを標準化されたSearchOutputオブジェクトに変換し、リストに追加
        outputs.append(SearchOutput.from_point(point))

    # 検索処理の完了をログに記録
    logger.info("Finished searching XYZ QA by query")

    # 検索結果のリストを返す（最大3件のSearchOutputオブジェクト）
    return outputs
