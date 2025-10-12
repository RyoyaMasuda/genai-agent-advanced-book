# Sequence、Annotated、operator.addの解説

## 目次

1. [Sequenceとは](#sequenceとは)
2. [Annotatedとは](#annotatedとは)
3. [operator.addとは](#operatoraddとは)
4. [組み合わせ：Annotated[Sequence[T], operator.add]](#組み合わせannotatedsequencet-operatoradd)
5. [agent.pyでの実際の使用例](#agentpyでの実際の使用例)
6. [LangGraphでの動作原理](#langgraphでの動作原理)

---

## Sequenceとは

### 概要

`Sequence`は、Pythonの`typing`モジュールで提供される**型ヒント用の抽象型**です。順序付きコレクション（シーケンス）を表します。

```python
from typing import Sequence
```

### 特徴

- **読み取り専用のシーケンス型**を表す抽象的な型
- インデックスでアクセス可能
- 長さ（len）を持つ
- イテレート可能（for文で回せる）

### Sequenceが受け入れる型

以下のような順序を持つデータ構造が該当します：

- `list`：可変リスト
- `tuple`：不変タプル
- `str`：文字列（文字のシーケンス）
- `range`：範囲オブジェクト
- `bytes`、`bytearray`：バイト列
- その他のシーケンス型

### listとの違い

| 項目 | `list[T]` | `Sequence[T]` |
|------|-----------|---------------|
| **型の具体性** | 具体的な型（listのみ） | 抽象的な型（list、tupleなど） |
| **変更可能性** | 変更可能（mutable） | 一般的に読み取り専用を想定 |
| **柔軟性** | listのみ受け入れる | 様々なシーケンス型を受け入れる |
| **使用場面** | 具体的にlistが必要な場合 | シーケンスであれば何でもOKな場合 |

### コード例

```python
from typing import Sequence

# Sequenceを使った関数
def print_sequence(items: Sequence[str]) -> None:
    """任意のシーケンス型を受け入れる"""
    for i, item in enumerate(items):
        print(f"{i}: {item}")

# どれもOK
print_sequence(["apple", "banana", "cherry"])    # list
print_sequence(("apple", "banana", "cherry"))    # tuple
print_sequence("abc")                             # str（文字のシーケンス）

# listを使った関数
def print_list(items: list[str]) -> None:
    """listのみを受け入れる"""
    for i, item in enumerate(items):
        print(f"{i}: {item}")

# これはOK
print_list(["apple", "banana", "cherry"])        # ✅ list

# これらは型チェックでエラー
print_list(("apple", "banana", "cherry"))        # ❌ tupleはNG
print_list("abc")                                 # ❌ strはNG
```

### なぜSequenceを使うのか？

1. **柔軟性**：関数がlistだけでなくtupleも受け入れられる
2. **意図の明示**：「順序付きデータが必要」という意図を明確にする
3. **読み取り専用の暗示**：変更しないことを暗に示す
4. **抽象化**：実装の詳細（listかtupleか）に依存しない

---

## Annotatedとは

### 概要

`Annotated`は、Python 3.9以降で導入された型ヒント用の特殊な型です。**型にメタデータを付加する**ために使用されます。

```python
from typing import Annotated
```

### 基本構文

```python
Annotated[型, メタデータ1, メタデータ2, ...]
```

- 第1引数：実際の型（例：`int`, `str`, `list[str]`）
- 第2引数以降：メタデータ（任意のオブジェクト）

### メタデータとは？

メタデータは「データについてのデータ」です。型そのものには影響を与えず、追加情報を持たせるために使います。

### 使用例

#### 例1: バリデーション情報を付加

```python
from typing import Annotated

# 1〜100の整数であることを示す
Age = Annotated[int, "age must be between 1 and 100"]

def set_age(age: Age) -> None:
    print(f"Age: {age}")

# 型チェッカーからは普通のintとして扱われる
set_age(25)  # ✅ OK
```

#### 例2: 単位情報を付加

```python
from typing import Annotated

Meters = Annotated[float, "meters"]
Seconds = Annotated[float, "seconds"]

def calculate_speed(distance: Meters, time: Seconds) -> float:
    """速度を計算（メートル/秒）"""
    return distance / time

speed = calculate_speed(100.0, 10.0)  # 10.0 m/s
```

#### 例3: Pydanticでのバリデーション

```python
from typing import Annotated
from pydantic import BaseModel, Field

class User(BaseModel):
    # メタデータとしてFieldを使用（バリデーションルール）
    name: Annotated[str, Field(min_length=1, max_length=50)]
    age: Annotated[int, Field(gt=0, le=120)]

user = User(name="Alice", age=30)  # ✅ OK
# user = User(name="", age=30)      # ❌ nameが空なのでエラー
# user = User(name="Bob", age=150)  # ❌ ageが120を超えているのでエラー
```

### Annotatedの利点

1. **型を拡張できる**：型そのものは変えずに追加情報を持たせられる
2. **ツールが利用可能**：Pydantic、FastAPI、LangGraphなどが活用
3. **可読性向上**：型に意味を付加できる
4. **型チェッカーとの互換性**：mypyなどは第1引数の型だけを見る

---

## operator.addとは

### 概要

`operator.add`は、Pythonの標準ライブラリ`operator`モジュールで提供される関数で、**加算演算子（`+`）と同じ動作**をします。

```python
import operator
```

### 基本的な使い方

```python
import operator

# 数値の加算
result = operator.add(3, 5)
print(result)  # 8

# 文字列の結合
result = operator.add("Hello, ", "World!")
print(result)  # "Hello, World!"

# リストの結合
result = operator.add([1, 2], [3, 4])
print(result)  # [1, 2, 3, 4]

# これらは以下と同じ
3 + 5               # 8
"Hello, " + "World!"  # "Hello, World!"
[1, 2] + [3, 4]     # [1, 2, 3, 4]
```

### なぜoperator.addを使うのか？

#### 理由1: 関数として渡せる

```python
from functools import reduce
import operator

numbers = [1, 2, 3, 4, 5]

# operator.addを関数として渡す
total = reduce(operator.add, numbers)
print(total)  # 15（1+2+3+4+5）

# ラムダ関数を使う場合（同じ意味）
total = reduce(lambda x, y: x + y, numbers)
print(total)  # 15
```

#### 理由2: メタデータとして使用

LangGraphなどのフレームワークでは、`operator.add`を**メタデータ**として使用し、「この値は加算方式で蓄積する」という情報を持たせます。

### operatorモジュールの他の関数

```python
import operator

# 算術演算
operator.add(a, b)       # a + b
operator.sub(a, b)       # a - b
operator.mul(a, b)       # a * b
operator.truediv(a, b)   # a / b

# 比較演算
operator.eq(a, b)        # a == b
operator.lt(a, b)        # a < b
operator.gt(a, b)        # a > b

# 論理演算
operator.and_(a, b)      # a & b
operator.or_(a, b)       # a | b

# 属性アクセス
operator.getitem(obj, key)  # obj[key]
operator.setitem(obj, key, value)  # obj[key] = value
```

---

## 組み合わせ：Annotated[Sequence[T], operator.add]

### この型の意味

```python
from typing import Annotated, Sequence
import operator

Annotated[Sequence[Subtask], operator.add]
```

この型は以下のことを表しています：

1. **型**：`Sequence[Subtask]`
   - Subtaskオブジェクトのシーケンス（list、tupleなど）
   
2. **メタデータ**：`operator.add`
   - この値は加算演算子（`+`）で結合される
   - 新しい値が来たら、既存の値に追加される

### LangGraphでの解釈

LangGraphは、このメタデータを読み取って以下のように動作します：

```python
# 初期状態
state = {
    "subtask_results": []  # 空のシーケンス
}

# ノード1が返す値
return {"subtask_results": [subtask1]}

# LangGraphの内部処理（operator.addを使用）
state["subtask_results"] = operator.add(
    state["subtask_results"],  # 現在の値: []
    [subtask1]                  # 新しい値
)
# 結果: state["subtask_results"] = [subtask1]

# ノード2が返す値
return {"subtask_results": [subtask2]}

# LangGraphの内部処理
state["subtask_results"] = operator.add(
    state["subtask_results"],  # 現在の値: [subtask1]
    [subtask2]                  # 新しい値
)
# 結果: state["subtask_results"] = [subtask1, subtask2]
```

### なぜこの組み合わせが便利か？

#### 1. 自動的な蓄積

通常の状態更新：
```python
# 通常の場合（上書きされる）
state = {"results": []}

def node1(state):
    return {"results": [result1]}  # state["results"] = [result1]

def node2(state):
    return {"results": [result2]}  # state["results"] = [result2]（上書き）
```

Annotatedを使った場合：
```python
# Annotatedの場合（自動的に追加される）
state = {"results": []}  # Annotated[Sequence[Result], operator.add]

def node1(state):
    return {"results": [result1]}  # state["results"] = [result1]

def node2(state):
    return {"results": [result2]}  # state["results"] = [result1, result2]（追加）
```

#### 2. 並列処理での利用

複数のノードが並列実行される場合、各ノードの結果を自動的に集約できます。

```python
# 並列実行される3つのノード
def node_a(state):
    return {"results": [result_a]}

def node_b(state):
    return {"results": [result_b]}

def node_c(state):
    return {"results": [result_c]}

# LangGraphが自動的に結果を集約
# state["results"] = [result_a, result_b, result_c]
```

---

## agent.pyでの実際の使用例

### AgentStateでの定義

```python
from typing import Annotated, Sequence, TypedDict
import operator
from src.models import Subtask

class AgentState(TypedDict):
    question: str
    plan: list[str]
    current_step: int
    # この行に注目
    subtask_results: Annotated[Sequence[Subtask], operator.add]
    last_answer: str
```

### 動作の詳細

#### ステップ1: 初期状態

```python
# エージェント開始時
state = {
    "question": "ERR-404エラーの対処法は？",
    "plan": ["エラーの意味を調査", "対処法を検索"],
    "current_step": 0,
    "subtask_results": [],  # 初期状態は空
    "last_answer": ""
}
```

#### ステップ2: サブタスク1の実行完了

```python
# サブタスク1（並列実行）が結果を返す
def execute_subtasks(state):
    # サブタスク1の処理...
    subtask_result_1 = Subtask(
        task_name="エラーの意味を調査",
        subtask_answer="ERR-404は、リソースが見つからないエラーです。",
        # ... その他のフィールド
    )
    return {"subtask_results": [subtask_result_1]}

# LangGraphの内部処理
# operator.addを使って既存の値と新しい値を結合
state["subtask_results"] = operator.add(
    state["subtask_results"],  # []
    [subtask_result_1]          # [subtask_1]
)
# 結果: state["subtask_results"] = [subtask_1]
```

#### ステップ3: サブタスク2の実行完了（並列実行）

```python
# サブタスク2（並列実行）が結果を返す
def execute_subtasks(state):
    # サブタスク2の処理...
    subtask_result_2 = Subtask(
        task_name="対処法を検索",
        subtask_answer="対処法は、URLを確認するか、管理者に連絡してください。",
        # ... その他のフィールド
    )
    return {"subtask_results": [subtask_result_2]}

# LangGraphの内部処理
state["subtask_results"] = operator.add(
    state["subtask_results"],  # [subtask_1]
    [subtask_result_2]          # [subtask_2]
)
# 結果: state["subtask_results"] = [subtask_1, subtask_2]
```

#### ステップ4: 最終回答作成

```python
# create_answerノードで全サブタスクの結果を使用
def create_answer(state):
    # state["subtask_results"]には全サブタスクの結果が含まれる
    subtask_results = state["subtask_results"]
    # [subtask_1, subtask_2]
    
    # これらを統合して最終回答を生成
    # ...
```

### AgentSubGraphStateでの使用

```python
class AgentSubGraphState(TypedDict):
    question: str
    plan: list[str]
    subtask: str
    is_completed: bool
    messages: list[ChatCompletionMessageParam]
    challenge_count: int
    # 検索結果の蓄積
    tool_results: Annotated[Sequence[Sequence[SearchOutput]], operator.add]
    # 内省結果の蓄積
    reflection_results: Annotated[Sequence[ReflectionResult], operator.add]
    subtask_answer: str
```

#### tool_resultsの動作

```python
# 初回のツール実行
def execute_tools(state):
    tool_results = [
        SearchOutput(...),
        SearchOutput(...),
        SearchOutput(...)
    ]
    return {"tool_results": [tool_results]}  # 2次元リスト

# state["tool_results"] = [[search1, search2, search3]]

# リトライ後のツール実行
def execute_tools(state):
    tool_results = [
        SearchOutput(...),
        SearchOutput(...)
    ]
    return {"tool_results": [tool_results]}

# LangGraphの内部処理
state["tool_results"] = operator.add(
    [[search1, search2, search3]],  # 初回の結果
    [[search4, search5]]             # リトライの結果
)
# 結果: state["tool_results"] = [
#     [search1, search2, search3],
#     [search4, search5]
# ]
```

#### reflection_resultsの動作

```python
# 初回の内省
def reflect_subtask(state):
    reflection = ReflectionResult(
        is_completed=False,
        reflection="検索結果が不十分です。別のツールで再試行してください。"
    )
    return {"reflection_results": [reflection]}

# state["reflection_results"] = [reflection1]

# リトライ後の内省
def reflect_subtask(state):
    reflection = ReflectionResult(
        is_completed=True,
        reflection="十分な情報が得られました。"
    )
    return {"reflection_results": [reflection]}

# LangGraphの内部処理
state["reflection_results"] = operator.add(
    [reflection1],  # 初回の内省
    [reflection2]   # リトライ後の内省
)
# 結果: state["reflection_results"] = [reflection1, reflection2]
```

---

## LangGraphでの動作原理

### 1. 状態の更新メカニズム

LangGraphは、ノードが返す辞書を使って状態を更新します。

#### 通常の更新（上書き）

```python
# 型定義
class State(TypedDict):
    counter: int

# ノード
def node1(state):
    return {"counter": 5}

def node2(state):
    return {"counter": 10}

# 実行結果
# node1実行後: state["counter"] = 5
# node2実行後: state["counter"] = 10（上書き）
```

#### Annotatedを使った更新（蓄積）

```python
# 型定義
class State(TypedDict):
    counter: Annotated[int, operator.add]

# ノード
def node1(state):
    return {"counter": 5}

def node2(state):
    return {"counter": 10}

# 実行結果
# 初期状態: state["counter"] = 0
# node1実行後: state["counter"] = 0 + 5 = 5
# node2実行後: state["counter"] = 5 + 10 = 15（加算）
```

### 2. Annotatedのメタデータの読み取り

LangGraphは内部で以下のような処理をしています：

```python
def update_state(state, updates, state_schema):
    """LangGraphの状態更新処理（簡略版）"""
    for key, value in updates.items():
        # 型定義を確認
        field_type = state_schema[key]
        
        # Annotatedかどうか確認
        if hasattr(field_type, '__metadata__'):
            # メタデータを取得
            metadata = field_type.__metadata__
            
            # operator.addが含まれているか確認
            if operator.add in metadata:
                # 加算方式で更新
                state[key] = operator.add(state[key], value)
            else:
                # 通常の更新（上書き）
                state[key] = value
        else:
            # Annotatedでない場合は上書き
            state[key] = value
    
    return state
```

### 3. 並列処理での集約

複数のノードが並列実行される場合、LangGraphは各ノードの結果を自動的に集約します。

```python
# 3つのサブタスクが並列実行される例
class State(TypedDict):
    results: Annotated[Sequence[str], operator.add]

def subtask1(state):
    return {"results": ["結果1"]}

def subtask2(state):
    return {"results": ["結果2"]}

def subtask3(state):
    return {"results": ["結果3"]}

# LangGraphの処理
# 1. 各ノードを並列実行
# 2. 各ノードの返り値を収集
#    node1 → {"results": ["結果1"]}
#    node2 → {"results": ["結果2"]}
#    node3 → {"results": ["結果3"]}
# 3. operator.addで順次結合
#    [] + ["結果1"] = ["結果1"]
#    ["結果1"] + ["結果2"] = ["結果1", "結果2"]
#    ["結果1", "結果2"] + ["結果3"] = ["結果1", "結果2", "結果3"]
# 4. 最終状態
#    state["results"] = ["結果1", "結果2", "結果3"]
```

---

## まとめ

### Sequence

- **順序付きコレクションの抽象型**
- list、tuple、strなど様々な型を受け入れる
- 読み取り専用的な性質を持つ
- 柔軟で抽象的な型定義に使う

### Annotated

- **型にメタデータを付加する**ための特殊な型
- 型チェッカーは第1引数の型だけを見る
- フレームワーク（Pydantic、LangGraphなど）がメタデータを活用
- 型を拡張しつつ互換性を保つ

### operator.add

- **加算演算子（`+`）と同じ動作**をする関数
- 関数として渡せるため、高階関数で使える
- LangGraphではメタデータとして使用され、「値を加算方式で蓄積する」という意図を表す

### Annotated[Sequence[T], operator.add]

- **Tのシーケンスで、値を加算方式で蓄積する**という型
- LangGraphが自動的に値を追加（上書きではなく追加）
- 並列処理での結果集約に便利
- agent.pyではサブタスク結果や検索結果の蓄積に使用

### agent.pyでの実際の効果

```python
# 定義
subtask_results: Annotated[Sequence[Subtask], operator.add]

# 効果
# - 各サブタスクの結果が自動的にリストに追加される
# - 並列実行されたサブタスクの結果が自動的に集約される
# - 上書きではなく蓄積されるため、全サブタスクの結果が保持される
```

この仕組みにより、LangGraphのエージェントは複数のタスクを並列実行し、その結果を自動的に集約できる強力な機能を実現しています。

