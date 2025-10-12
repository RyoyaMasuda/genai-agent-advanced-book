# LiteralとTypedDictの解説

## 目次

1. [Literalとは](#literalとは)
2. [TypedDictとは](#typeddictとは)
3. [agent.pyでの実際の使用例](#agentpyでの実際の使用例)
4. [組み合わせて使う例](#組み合わせて使う例)
5. [ベストプラクティス](#ベストプラクティス)

---

## Literalとは

### 概要

`Literal`は、Python 3.8以降で導入された型ヒントで、**特定の値だけを受け入れる型**を定義します。

```python
from typing import Literal
```

### 基本的な使い方

```python
from typing import Literal

# "red", "green", "blue"のいずれかのみを受け入れる
Color = Literal["red", "green", "blue"]

def set_color(color: Color) -> None:
    print(f"Color set to: {color}")

# ✅ これらはOK
set_color("red")
set_color("green")
set_color("blue")

# ❌ これは型チェッカーでエラー
set_color("yellow")  # エラー: "yellow"はLiteral["red", "green", "blue"]に含まれない
```

### なぜLiteralを使うのか？

#### 1. **型安全性の向上**

通常の文字列型では、どんな文字列でも受け入れてしまいます：

```python
# strを使った場合
def set_mode(mode: str) -> None:
    if mode == "debug":
        print("Debug mode")
    elif mode == "production":
        print("Production mode")
    else:
        print("Unknown mode")  # タイポしても実行時までエラーがわからない

set_mode("debug")        # ✅ OK
set_mode("production")   # ✅ OK
set_mode("producton")    # ✅ コンパイル通るが、実行時にバグ（タイポ）
```

Literalを使うと、コンパイル時（型チェック時）にエラーを検出できます：

```python
# Literalを使った場合
def set_mode(mode: Literal["debug", "production"]) -> None:
    if mode == "debug":
        print("Debug mode")
    elif mode == "production":
        print("Production mode")

set_mode("debug")        # ✅ OK
set_mode("production")   # ✅ OK
set_mode("producton")    # ❌ 型チェッカーがエラーを検出！
```

#### 2. **ドキュメントとしての役割**

関数の引数に`Literal`を使うことで、どの値が有効かが明確になります：

```python
def move(direction: Literal["up", "down", "left", "right"]) -> None:
    """
    方向に移動する
    
    この関数定義を見るだけで、受け入れられる値が明確！
    """
    pass
```

#### 3. **エディタの補完機能**

IDEやエディタが、Literalで定義された値を自動補完してくれます：

```python
def set_status(status: Literal["pending", "running", "completed", "failed"]) -> None:
    pass

# エディタで set_status( と入力すると、
# "pending", "running", "completed", "failed" が候補として表示される
```

### Literalの様々な使い方

#### 文字列のリテラル

```python
from typing import Literal

Status = Literal["pending", "running", "completed"]

def update_status(status: Status) -> None:
    print(f"Status: {status}")
```

#### 数値のリテラル

```python
from typing import Literal

# 1, 2, 3のいずれかのみ
Priority = Literal[1, 2, 3]

def set_priority(priority: Priority) -> None:
    print(f"Priority: {priority}")

set_priority(1)  # ✅ OK
set_priority(2)  # ✅ OK
set_priority(4)  # ❌ エラー
```

#### 真偽値のリテラル

```python
from typing import Literal

# Trueのみを受け入れる（明示的な同意を要求する場合など）
def accept_terms(agreed: Literal[True]) -> None:
    print("Terms accepted")

accept_terms(True)   # ✅ OK
accept_terms(False)  # ❌ エラー
```

#### 混在型のリテラル

```python
from typing import Literal

# 異なる型の値を混在させることも可能
Mixed = Literal["auto", 0, False]

def set_option(option: Mixed) -> None:
    if option == "auto":
        print("Auto mode")
    elif option == 0:
        print("Disabled (numeric)")
    elif option is False:
        print("Disabled (boolean)")
```

#### 複数のLiteralを結合

```python
from typing import Literal

# 2つのLiteralを組み合わせる
ReadMode = Literal["r", "rb"]
WriteMode = Literal["w", "wb"]
FileMode = Literal[ReadMode, WriteMode]  # "r", "rb", "w", "wb"

# または、Union風に書くこともできる
FileMode2 = Literal["r", "rb", "w", "wb"]
```

### 関数の戻り値としてのLiteral

```python
from typing import Literal

def validate_input(value: str) -> Literal["valid", "invalid"]:
    """
    入力を検証して、"valid"または"invalid"を返す
    """
    if len(value) > 0:
        return "valid"
    else:
        return "invalid"

result = validate_input("test")
# resultの型は Literal["valid", "invalid"] として推論される
```

---

## TypedDictとは

### 概要

`TypedDict`は、Python 3.8以降で導入された型ヒントで、**辞書（dict）の型を詳細に定義**できます。

```python
from typing import TypedDict
```

### 通常のdictとの違い

#### 通常のdict

```python
# 通常のdict型
user: dict = {
    "name": "Alice",
    "age": 30,
    "email": "alice@example.com"
}

# 問題点：
# 1. どんなキーが存在するかわからない
# 2. 各値の型がわからない
# 3. タイポしてもエラーにならない
print(user["emal"])  # ❌ KeyError（実行時エラー）
```

#### TypedDictを使った場合

```python
from typing import TypedDict

class User(TypedDict):
    name: str
    age: int
    email: str

user: User = {
    "name": "Alice",
    "age": 30,
    "email": "alice@example.com"
}

# 利点：
# 1. キーが明確
# 2. 各値の型が明確
# 3. 型チェッカーがタイポを検出
print(user["name"])   # ✅ OK（型チェッカーが確認）
print(user["emal"])   # ❌ 型チェッカーがエラーを検出！
```

### TypedDictの定義方法

#### クラス構文

```python
from typing import TypedDict

class Person(TypedDict):
    name: str
    age: int
    is_active: bool

person: Person = {
    "name": "Bob",
    "age": 25,
    "is_active": True
}
```

#### 関数構文（古い書き方）

```python
from typing import TypedDict

# TypedDict関数を使った定義
Person = TypedDict('Person', {
    'name': str,
    'age': int,
    'is_active': bool
})
```

### オプショナルなキー

#### total=Falseを使う方法

```python
from typing import TypedDict

class Person(TypedDict, total=False):
    name: str
    age: int
    email: str  # すべてのキーがオプショナル

# これもOK
person: Person = {"name": "Alice"}
```

#### Requiredと NotRequiredを使う方法（Python 3.11+）

```python
from typing import TypedDict, Required, NotRequired

class Person(TypedDict):
    name: Required[str]      # 必須
    age: Required[int]       # 必須
    email: NotRequired[str]  # オプショナル

# nameとageは必須、emailはオプショナル
person: Person = {
    "name": "Alice",
    "age": 30
    # emailは省略可能
}
```

#### 一部だけオプショナルにする方法

```python
from typing import TypedDict

# 必須フィールド
class PersonRequired(TypedDict):
    name: str
    age: int

# オプショナルフィールド
class PersonOptional(TypedDict, total=False):
    email: str
    phone: str

# 継承して組み合わせる
class Person(PersonRequired, PersonOptional):
    pass

# nameとageは必須、emailとphoneはオプショナル
person: Person = {
    "name": "Alice",
    "age": 30
    # email, phoneは省略可能
}
```

### TypedDictのネスト

```python
from typing import TypedDict

class Address(TypedDict):
    street: str
    city: str
    zipcode: str

class Person(TypedDict):
    name: str
    age: int
    address: Address  # ネストされたTypedDict

person: Person = {
    "name": "Alice",
    "age": 30,
    "address": {
        "street": "123 Main St",
        "city": "Tokyo",
        "zipcode": "100-0001"
    }
}
```

### TypedDictと通常のクラスの違い

| 項目 | TypedDict | 通常のクラス |
|------|-----------|-------------|
| **実体** | 辞書（dict） | クラスインスタンス |
| **アクセス方法** | `obj["key"]` | `obj.key` |
| **メモリ** | 軽量 | やや重い |
| **メソッド** | 持てない | 持てる |
| **継承** | 型の継承のみ | 実際の継承 |
| **用途** | データ構造の型定義 | オブジェクト指向設計 |

```python
from typing import TypedDict

# TypedDict
class PersonDict(TypedDict):
    name: str
    age: int

person_dict: PersonDict = {"name": "Alice", "age": 30}
print(person_dict["name"])  # 辞書としてアクセス
print(type(person_dict))    # <class 'dict'>

# 通常のクラス
class PersonClass:
    def __init__(self, name: str, age: int):
        self.name = name
        self.age = age
    
    def greet(self):
        return f"Hello, I'm {self.name}"

person_obj = PersonClass("Alice", 30)
print(person_obj.name)      # 属性としてアクセス
print(type(person_obj))     # <class '__main__.PersonClass'>
print(person_obj.greet())   # メソッドを持てる
```

---

## agent.pyでの実際の使用例

### Literalの使用例

#### _should_continue_exec_subtask_flowメソッド

```python
def _should_continue_exec_subtask_flow(
    self, 
    state: AgentSubGraphState
) -> Literal["end", "continue"]:
    """
    サブグラフ内のループを制御する（内部メソッド）
    
    戻り値の型がLiteral["end", "continue"]であることで、
    この関数は必ず"end"または"continue"のいずれかを返すことが保証される。
    """
    # 完了フラグがTrueか、最大リトライ回数に到達した場合は終了
    if state["is_completed"] or state["challenge_count"] >= MAX_CHALLENGE_COUNT:
        return "end"
    else:
        # それ以外は継続（ツール選択に戻る）
        return "continue"
```

**なぜLiteralを使うのか？**

1. **型安全性**：タイポを防ぐ
   ```python
   # もしLiteralを使わず、strを使っていたら...
   def _should_continue_exec_subtask_flow(state) -> str:
       if state["is_completed"]:
           return "ed"  # ❌ タイポ！でも実行時までわからない
       else:
           return "continue"
   ```

2. **条件分岐との連携**：
   ```python
   # LangGraphの条件分岐エッジ
   workflow.add_conditional_edges(
       "reflect_subtask",
       self._should_continue_exec_subtask_flow,
       {
           "continue": "select_tools",  # ✅ "continue"という値と対応
           "end": END                    # ✅ "end"という値と対応
       },
   )
   ```

3. **ドキュメントとしての役割**：関数を見るだけで、どの値を返すかが明確

### TypedDictの使用例

#### AgentState

```python
class AgentState(TypedDict):
    """メイングラフの状態を管理するクラス"""
    question: str
    plan: list[str]
    current_step: int
    subtask_results: Annotated[Sequence[Subtask], operator.add]
    last_answer: str
```

**TypedDictを使う理由：**

1. **LangGraphの要件**
   - LangGraphは状態を辞書として管理する
   - TypedDictを使うことで型安全性を保ちつつ辞書を使える

2. **明確な状態定義**
   - どんなキーがあるか一目でわかる
   - 各値の型が明確

3. **型チェッカーのサポート**
   ```python
   def some_function(state: AgentState) -> dict:
       # 型チェッカーが正しいキー名を確認
       question = state["question"]        # ✅ OK
       answer = state["last_answer"]       # ✅ OK
       result = state["last_answr"]        # ❌ タイポを検出！
       
       return {"last_answer": "新しい回答"}
   ```

#### AgentSubGraphState

```python
class AgentSubGraphState(TypedDict):
    """サブグラフの状態を管理するクラス"""
    question: str
    plan: list[str]
    subtask: str
    is_completed: bool
    messages: list[ChatCompletionMessageParam]
    challenge_count: int
    tool_results: Annotated[Sequence[Sequence[SearchOutput]], operator.add]
    reflection_results: Annotated[Sequence[ReflectionResult], operator.add]
    subtask_answer: str
```

**複雑な型の組み合わせ：**

- `list[ChatCompletionMessageParam]`：OpenAIのメッセージ型のリスト
- `Annotated[Sequence[...], operator.add]`：自動蓄積される型
- 多様な型が混在するが、TypedDictで整理されている

### 実際の使用場面

#### 状態の初期化

```python
def run_agent(self, question: str) -> AgentResult:
    app = self.create_graph()
    
    # TypedDictで定義された型に従って初期状態を作成
    result = app.invoke(
        {
            "question": question,     # str型
            "current_step": 0,        # int型
        }
    )
    
    return AgentResult(
        question=question,
        plan=Plan(subtasks=result["plan"]),
        subtasks=result["subtask_results"],
        answer=result["last_answer"],
    )
```

#### 状態の更新

```python
def create_plan(self, state: AgentState) -> dict:
    # stateの型がAgentStateなので、型チェッカーが確認できる
    question = state["question"]  # ✅ OK
    
    # ...処理...
    
    # 返す辞書のキーも型チェックされる
    return {"plan": plan.subtasks}  # ✅ planキーはlist[str]型
```

---

## 組み合わせて使う例

### Literalを含むTypedDict

```python
from typing import Literal, TypedDict

class TaskState(TypedDict):
    task_id: str
    status: Literal["pending", "running", "completed", "failed"]
    progress: int
    error_message: str | None

# 使用例
task: TaskState = {
    "task_id": "task_001",
    "status": "running",    # ✅ Literalで定義された値のみ
    "progress": 50,
    "error_message": None
}

# ❌ これは型チェックでエラー
bad_task: TaskState = {
    "task_id": "task_002",
    "status": "processing",  # ❌ "processing"はLiteralに含まれない
    "progress": 25,
    "error_message": None
}
```

### 条件分岐とLiteralの組み合わせ

```python
from typing import Literal, TypedDict

Action = Literal["continue", "retry", "abort"]

class WorkflowState(TypedDict):
    current_step: int
    max_steps: int
    errors: list[str]

def decide_next_action(state: WorkflowState) -> Action:
    """次のアクションを決定"""
    if state["current_step"] >= state["max_steps"]:
        return "abort"
    elif len(state["errors"]) > 0:
        return "retry"
    else:
        return "continue"

# 条件分岐での使用
def execute_workflow(state: WorkflowState) -> None:
    action = decide_next_action(state)
    
    # Literalのおかげで、網羅性チェックができる
    if action == "continue":
        print("Continuing workflow")
    elif action == "retry":
        print("Retrying workflow")
    elif action == "abort":
        print("Aborting workflow")
    # else節が不要！すべてのケースをカバーしている
```

### 複雑な状態管理の例

```python
from typing import Literal, TypedDict, Annotated
import operator

Status = Literal["idle", "processing", "completed", "error"]
Priority = Literal["low", "medium", "high"]

class LogEntry(TypedDict):
    timestamp: str
    message: str
    level: Literal["debug", "info", "warning", "error"]

class ProcessState(TypedDict):
    process_id: str
    status: Status
    priority: Priority
    progress: int
    logs: Annotated[list[LogEntry], operator.add]
    retry_count: int
    max_retries: int

def update_process(state: ProcessState, new_log: LogEntry) -> dict:
    """プロセスの状態を更新"""
    # 型チェッカーが全てのキーと型を確認
    return {
        "logs": [new_log],  # operator.addで自動的に追加される
        "progress": state["progress"] + 10
    }
```

---

## ベストプラクティス

### 1. Literalは限定的な選択肢に使う

**✅ 良い例：**
```python
# 選択肢が少なく、明確な場合
def set_log_level(level: Literal["debug", "info", "warning", "error"]) -> None:
    pass
```

**❌ 悪い例：**
```python
# 選択肢が多すぎる場合は別の方法を検討
def select_country(country: Literal["Japan", "USA", "UK", ...]) -> None:  # 200カ国も列挙？
    pass

# 代わりにEnumを使う
from enum import Enum

class Country(Enum):
    JAPAN = "JP"
    USA = "US"
    UK = "GB"
```

### 2. TypedDictは純粋なデータ構造に使う

**✅ 良い例：**
```python
# データの受け渡しに使う
class UserData(TypedDict):
    user_id: str
    name: str
    email: str
```

**❌ 悪い例：**
```python
# メソッドが必要なら通常のクラスを使う
class UserData(TypedDict):  # TypedDictはメソッドを持てない
    user_id: str
    name: str
    email: str

# 代わりにdataclassまたは通常のクラスを使う
from dataclasses import dataclass

@dataclass
class UserData:
    user_id: str
    name: str
    email: str
    
    def get_display_name(self) -> str:
        return f"{self.name} ({self.user_id})"
```

### 3. 明確なネーミング

```python
# ✅ 良い例：名前から意味が明確
Status = Literal["pending", "running", "completed"]
Direction = Literal["north", "south", "east", "west"]

# ❌ 悪い例：意味が不明確
X = Literal["a", "b", "c"]  # a, b, cは何を表す？
```

### 4. ドキュメント化

```python
from typing import Literal, TypedDict

# Literalの選択肢の意味を明確にする
FlowControl = Literal["continue", "retry", "abort"]
"""
ワークフローの制御フラグ:
- "continue": 次のステップに進む
- "retry": 現在のステップを再試行
- "abort": ワークフローを中止
"""

class ProcessState(TypedDict):
    """
    プロセスの状態を表す辞書
    
    Attributes:
        process_id: プロセスの一意な識別子
        status: 現在のステータス
        progress: 進捗率（0-100）
    """
    process_id: str
    status: Literal["idle", "running", "completed"]
    progress: int
```

### 5. TypedDictの継承を活用

```python
from typing import TypedDict

# 共通フィールド
class BaseEntity(TypedDict):
    id: str
    created_at: str
    updated_at: str

# 特化したエンティティ
class User(BaseEntity):
    name: str
    email: str

class Product(BaseEntity):
    name: str
    price: float
    stock: int

# 継承により、id, created_at, updated_atが自動的に含まれる
```

---

## まとめ

### Literal

- **特定の値だけを受け入れる型**
- 型安全性を向上させ、タイポを防ぐ
- エディタの補完機能を活用できる
- 関数の戻り値や引数に使い、選択肢を明確にする
- agent.pyでは条件分岐の戻り値に使用（`"end"`または`"continue"`）

### TypedDict

- **辞書の型を詳細に定義**
- キーと値の型を明確にし、タイポを防ぐ
- LangGraphのような辞書ベースのフレームワークで有用
- メソッドが不要な純粋なデータ構造に適している
- agent.pyではグラフの状態管理に使用（`AgentState`、`AgentSubGraphState`）

### 組み合わせの力

```python
# agent.pyでの実際の使用例
class AgentSubGraphState(TypedDict):
    # ... 他のフィールド
    is_completed: bool
    challenge_count: int

def _should_continue_exec_subtask_flow(
    self, 
    state: AgentSubGraphState
) -> Literal["end", "continue"]:
    if state["is_completed"] or state["challenge_count"] >= MAX_CHALLENGE_COUNT:
        return "end"
    else:
        return "continue"
```

この組み合わせにより：
- 型安全な状態管理（TypedDict）
- 明確な制御フロー（Literal）
- エディタのサポート
- バグの早期発見

が実現されています。

