# search_xyz_manual.py

## 概要

`search_xyz_manual.py` は、Elasticsearchを使用してXYZシステムのドキュメントをキーワード検索するツールです。LangChainのtoolデコレーターを使用してエージェントシステムに統合可能な形式で提供されています。

## 主な機能

- XYZシステムのマニュアルやドキュメントからキーワードで全文検索
- エラーコードや固有名詞を含む質問に対応
- 検索結果を最大3件まで取得
- Elasticsearchとの連携
- 構造化された検索結果の返却

## 依存関係

```python
from elasticsearch import Elasticsearch
from langchain.tools import tool
from pydantic import BaseModel, Field
from src.custom_logger import setup_logger
from src.models import SearchOutput
```

- **Elasticsearch**: ローカルのElasticsearchインスタンス（http://localhost:9200）に接続
- **LangChain**: ツール化のためのデコレーター機能を使用
- **Pydantic**: 入力スキーマの定義と検証
- **カスタムモジュール**: ロガーと検索結果モデル

## 設定

### 定数

- `MAX_SEARCH_RESULTS = 3`: 検索結果の最大取得数

### Elasticsearch設定

- **エンドポイント**: `http://localhost:9200`
- **インデックス名**: `documents`
- **検索対象フィールド**: `content`

## クラスとメソッド

### SearchKeywordInput

入力パラメータを定義するPydanticモデル。

```python
class SearchKeywordInput(BaseModel):
    keywords: str = Field(description="全文検索用のキーワード")
```

**フィールド**:
- `keywords`: 検索に使用するキーワード文字列

### search_xyz_manual

メインの検索関数。LangChainのtoolデコレーターでツール化されています。

```python
@tool(args_schema=SearchKeywordInput)
def search_xyz_manual(keywords: str) -> list[SearchOutput]:
```

**引数**:
- `keywords` (str): 全文検索用のキーワード

**戻り値**:
- `list[SearchOutput]`: 検索結果のリスト（最大3件）

**処理フロー**:
1. Elasticsearchクライアントのインスタンス化
2. 検索クエリの作成（matchクエリを使用）
3. Elasticsearchへのクエリ実行
4. ヒット結果の処理とSearchOutputオブジェクトへの変換
5. 結果リストの返却

## 使用例

```python
from src.tools.search_xyz_manual import search_xyz_manual

# キーワードで検索
results = search_xyz_manual.invoke({"keywords": "エラーコード 404"})

# 結果の確認
for result in results:
    print(f"Score: {result.score}")
    print(f"Content: {result.content}")
```

## エージェントシステムでの使用

このツールは、LangChainのエージェントシステム内で自動的に呼び出すことができます。エージェントは以下の場合にこのツールを選択します：

- エラーコードに関する質問を受けた場合
- XYZシステムの固有名詞や機能について調査が必要な場合
- ドキュメントベースの回答が必要な場合

## ログ出力

以下のタイミングでログが出力されます：

1. 検索開始時: 検索キーワードの記録
2. 検索完了時: ヒット件数の記録
3. 処理終了時: 処理完了の記録

## 注意事項

- Elasticsearchが `localhost:9200` で起動している必要があります
- `documents` インデックスが事前に作成されている必要があります
- 検索結果は最大3件に制限されています（`MAX_SEARCH_RESULTS`で変更可能）
- `SearchOutput.from_hit()` メソッドは `src.models` で定義されている必要があります

## 関連ファイル

- `src/models.py`: SearchOutputモデルの定義
- `src/custom_logger.py`: ロガーのセットアップ
- `src/tools/search_xyz_qa.py`: 関連する検索ツール（QA用）

