from elasticsearch import Elasticsearch
from qdrant_client import QdrantClient


def delete_es_index(es: Elasticsearch, index_name: str) -> None:
    # インデックスの削除
    if es.indices.exists(index=index_name):
        es.indices.delete(index=index_name)
        print(f"インデックス '{index_name}' を削除しました")
    else:
        print(f"インデックス '{index_name}' は存在しません")


def delete_qdrant_index(qdrant_client: QdrantClient, collection_name: str) -> None:

    if qdrant_client.collection_exists(collection_name=collection_name):
        # qdrantでインデックスを削除
        qdrant_client.delete_collection("documents")
        print(f"コレクション '{collection_name}' を削除しました")
    else:
        print(f"コレクション '{collection_name}' は存在しません")


if __name__ == "__main__":
    es = Elasticsearch("http://localhost:9200")
    qdrant_client = QdrantClient("http://localhost:6333")

    index_name = "documents"

    delete_es_index(es=es, index_name=index_name)

    delete_qdrant_index(qdrant_client=qdrant_client, collection_name=index_name)
