# SendとPregelの解説

## 目次

1. [Sendとは](#sendとは)
2. [Pregelとは](#pregelとは)
3. [agent.pyでの実際の使用例](#agentpyでの実際の使用例)
4. [LangGraphの実行モデル](#langgraphの実行モデル)
5. [ベストプラクティス](#ベストプラクティス)

---

## Sendとは

### 概要

`Send`は、LangGraphで**並列処理を制御する**ための特殊なオブジェクトです。複数のノードを同時に実行したい場合に使用します。

```python
from langgraph.constants import Send
```

### 基本的な概念

通常のグラフでは、ノードは順番に実行されます。しかし、複数のタスクを同時に実行したい場合（例：3つのサブタスクを並列実行）、`Send`を使用します。

#### 通常のエッジ（逐次実行）

```python
from langgraph.graph import StateGraph, START, END

workflow = StateGraph(State)
workflow.add_node("task1", task1_func)
workflow.add_node("task2", task2_func)
workflow.add_node("task3", task3_func)

# 逐次実行：task1 → task2 → task3
workflow.add_edge(START, "task1")
workflow.add_edge("task1", "task2")
workflow.add_edge("task2", "task3")
workflow.add_edge("task3", END)
```

実行順序：
```
START → task1 → task2 → task3 → END
```

#### Sendを使ったエッジ（並列実行）

```python
from langgraph.graph import StateGraph, START, END
from langgraph.constants import Send

def fan_out(state):
    # 並列実行する命令を返す
    return [
        Send("task1", {"data": state["data"]}),
        Send("task2", {"data": state["data"]}),
        Send("task3", {"data": state["data"]}),
    ]

workflow = StateGraph(State)
workflow.add_node("task1", task1_func)
workflow.add_node("task2", task2_func)
workflow.add_node("task3", task3_func)

# 条件分岐エッジでSendのリストを返す
workflow.add_conditional_edges(START, fan_out)

# すべてのタスクが完了したら次へ
workflow.add_edge("task1", END)
workflow.add_edge("task2", END)
workflow.add_edge("task3", END)
```

実行順序：
```
       ┌─→ task1 ─┐
START ─┼─→ task2 ─┼→ END
       └─→ task3 ─┘
```

### Sendの構文

```python
Send(node_name, state)
```

- **第1引数（node_name）**: 実行するノードの名前（文字列）
- **第2引数（state）**: そのノードに渡す状態（辞書）

### Sendの使用例

#### 例1: 固定数の並列実行

```python
from typing import TypedDict
from langgraph.constants import Send
from langgraph.graph import StateGraph

class State(TypedDict):
    items: list[str]
    results: list[str]

def process_item(state):
    """個別のアイテムを処理"""
    item = state["item"]
    result = f"Processed: {item}"
    return {"results": [result]}

def fan_out_to_tasks(state):
    """各アイテムに対してタスクを並列実行"""
    return [
        Send("process_item", {"item": item})
        for item in state["items"]
    ]

workflow = StateGraph(State)
workflow.add_node("process_item", process_item)
workflow.add_conditional_edges(START, fan_out_to_tasks)

# 実行例
state = {"items": ["apple", "banana", "cherry"], "results": []}
# → 3つのprocess_itemノードが並列実行される
```

#### 例2: 動的な並列実行

```python
def dynamic_fan_out(state):
    """状態に応じて動的にタスクを生成"""
    sends = []
    
    # 条件に応じて異なるノードを実行
    if state["need_search"]:
        sends.append(Send("search_task", state))
    
    if state["need_validation"]:
        sends.append(Send("validation_task", state))
    
    if state["need_processing"]:
        sends.append(Send("processing_task", state))
    
    return sends

workflow = StateGraph(State)
workflow.add_node("search_task", search_func)
workflow.add_node("validation_task", validation_func)
workflow.add_node("processing_task", processing_func)
workflow.add_conditional_edges(START, dynamic_fan_out)
```

### Sendと通常のエッジの違い

| 項目 | 通常のエッジ | Send |
|------|-------------|------|
| **実行方法** | 逐次実行 | 並列実行 |
| **ノード数** | 1つのノードに遷移 | 複数のノードに遷移可能 |
| **状態の渡し方** | 自動的に状態が引き継がれる | 各Sendで個別に状態を指定 |
| **使用場所** | `add_edge()` | `add_conditional_edges()` |
| **用途** | 順番に処理したい場合 | 同時に処理したい場合 |

### Sendのメリット

1. **パフォーマンス向上**
   - 独立したタスクを同時に実行できる
   - 待ち時間を削減

2. **柔軟性**
   - 実行時に並列実行するタスク数を動的に決定できる
   - 条件に応じて異なるノードを実行できる

3. **状態の独立性**
   - 各タスクに異なる状態を渡せる
   - タスク間の干渉を防ぐ

### Sendの注意点

1. **状態の集約**
   - 並列実行されたタスクの結果は、`Annotated[..., operator.add]`などで自動的に集約する必要がある

2. **順序の保証なし**
   - 並列実行されるため、実行順序は保証されない
   - 順序が重要な場合は通常のエッジを使用

3. **依存関係**
   - タスク間に依存関係がある場合は並列実行できない

---

## Pregelとは

### 概要

`Pregel`は、LangGraphで**コンパイル済みのグラフ**を表す型です。グラフを実行可能な状態にしたものです。

```python
from langgraph.pregel import Pregel
```

名前の由来：Googleが開発した大規模グラフ処理システム「Pregel」から来ています。

### Pregelの役割

`Pregel`は、以下の機能を持つ実行可能なグラフオブジェクトです：

1. **グラフの実行**：`invoke()`, `stream()`, `astream()`などのメソッド
2. **状態管理**：ノード間の状態の受け渡し
3. **条件分岐**：条件付きエッジの評価
4. **並列実行**：Sendによる並列タスクの管理
5. **エラーハンドリング**：実行中のエラー処理

### グラフのライフサイクル

```python
from langgraph.graph import StateGraph
from langgraph.pregel import Pregel

# 1. グラフの定義
workflow = StateGraph(State)
workflow.add_node("step1", step1_func)
workflow.add_node("step2", step2_func)
workflow.add_edge("step1", "step2")

# 2. グラフのコンパイル（StateGraph → Pregel）
app: Pregel = workflow.compile()

# 3. グラフの実行
result = app.invoke({"input": "data"})
```

### Pregelオブジェクトの型

```python
from langgraph.pregel import Pregel

def create_workflow() -> Pregel:
    """
    ワークフローを作成してPregelオブジェクトを返す
    
    Returns:
        Pregel: コンパイル済みの実行可能なグラフ
    """
    workflow = StateGraph(State)
    # ... ノードとエッジを追加
    return workflow.compile()
```

### Pregelの主要メソッド

#### 1. invoke() - 同期実行

```python
app = workflow.compile()

# グラフを実行し、最終状態を返す
result = app.invoke({"question": "What is AI?"})
print(result)
# {'question': 'What is AI?', 'answer': '...', ...}
```

#### 2. stream() - ストリーミング実行（同期）

```python
app = workflow.compile()

# グラフの各ステップの結果をストリーム
for step in app.stream({"question": "What is AI?"}):
    print(step)
    # ステップごとに結果が返される
```

#### 3. astream() - ストリーミング実行（非同期）

```python
app = workflow.compile()

# 非同期でストリーミング
async for step in app.astream({"question": "What is AI?"}):
    print(step)
```

#### 4. get_graph() - グラフ構造の取得

```python
app = workflow.compile()

# グラフの構造を可視化用に取得
graph = app.get_graph()
print(graph.nodes)
print(graph.edges)
```

### Pregelの内部動作

Pregelは内部で以下の処理を行います：

```python
# 疑似コード：Pregelの内部動作
class Pregel:
    def __init__(self, nodes, edges, state_schema):
        self.nodes = nodes          # ノードの辞書
        self.edges = edges          # エッジの定義
        self.state_schema = state_schema  # 状態の型
    
    def invoke(self, initial_state):
        """グラフを実行"""
        state = initial_state
        current_node = START
        
        while current_node != END:
            # 現在のノードを実行
            node_func = self.nodes[current_node]
            updates = node_func(state)
            
            # 状態を更新
            state = self._update_state(state, updates)
            
            # 次のノードを決定
            current_node = self._get_next_node(current_node, state)
        
        return state
    
    def _update_state(self, state, updates):
        """状態を更新（Annotatedのメタデータを考慮）"""
        for key, value in updates.items():
            if key in self.state_schema:
                # メタデータをチェック（operator.addなど）
                if self._has_add_operator(key):
                    state[key] = state[key] + value
                else:
                    state[key] = value
        return state
    
    def _get_next_node(self, current_node, state):
        """次のノードを決定（条件分岐を評価）"""
        edge = self.edges[current_node]
        
        if isinstance(edge, ConditionalEdge):
            # 条件分岐を評価
            result = edge.condition(state)
            
            if isinstance(result, list) and all(isinstance(x, Send) for x in result):
                # Sendのリストなら並列実行
                self._execute_parallel(result)
                return edge.then_node
            else:
                # 通常の条件分岐
                return edge.mapping[result]
        else:
            # 固定エッジ
            return edge.to_node
    
    def _execute_parallel(self, sends):
        """並列実行"""
        results = []
        # 並列実行の実装（マルチスレッド/マルチプロセスなど）
        for send in sends:
            node_func = self.nodes[send.node]
            result = node_func(send.state)
            results.append(result)
        
        # 結果を集約
        return self._merge_results(results)
```

---

## agent.pyでの実際の使用例

### Sendの使用例

#### _should_continue_exec_subtasksメソッド

```python
def _should_continue_exec_subtasks(self, state: AgentState) -> list:
    """
    サブタスクの並列実行を制御する（内部メソッド）
    
    計画に含まれる全てのサブタスクを並列実行するための命令を生成する。
    例：計画に3つのサブタスクがある場合
    → 3つのSendオブジェクトを返し、それぞれが並列実行される
    
    LangGraphのSend機能を使用して、各サブタスクを独立したサブグラフとして実行。
    
    Args:
        state (AgentState): 現在の状態（planを含む）
        
    Returns:
        list[Send]: 各サブタスクに対するSendオブジェクトのリスト
    """
    # 計画内の各サブタスクに対してSendオブジェクトを生成
    # これによりLangGraphが各サブタスクを並列実行する
    return [
        Send(
            "execute_subtasks",  # 実行するノード名
            {
                "question": state["question"],  # 元の質問
                "plan": state["plan"],  # 全体の計画
                "current_step": idx,  # サブタスクのインデックス
            },
        )
        for idx, _ in enumerate(state["plan"])  # 各サブタスクに対してループ
    ]
```

**動作の詳細：**

```python
# 例：計画に3つのサブタスクがある場合
state = {
    "question": "ERR-404エラーの対処法は？",
    "plan": [
        "エラーの意味を調査",
        "対処法を検索",
        "関連する質問を検索"
    ]
}

# _should_continue_exec_subtasksが返すSendのリスト
[
    Send("execute_subtasks", {
        "question": "ERR-404エラーの対処法は？",
        "plan": ["エラーの意味を調査", "対処法を検索", "関連する質問を検索"],
        "current_step": 0
    }),
    Send("execute_subtasks", {
        "question": "ERR-404エラーの対処法は？",
        "plan": ["エラーの意味を調査", "対処法を検索", "関連する質問を検索"],
        "current_step": 1
    }),
    Send("execute_subtasks", {
        "question": "ERR-404エラーの対処法は？",
        "plan": ["エラーの意味を調査", "対処法を検索", "関連する質問を検索"],
        "current_step": 2
    })
]

# LangGraphが3つのexecute_subtasksノードを並列実行
# 各ノードは異なるcurrent_stepを持つため、異なるサブタスクを処理
```

**実行フロー：**

```
create_plan
     ↓
  [計画を生成: 3つのサブタスク]
     ↓
_should_continue_exec_subtasks（3つのSendを返す）
     ↓
     ├─→ execute_subtasks (step=0) ─┐
     ├─→ execute_subtasks (step=1) ─┤ 並列実行
     └─→ execute_subtasks (step=2) ─┘
     ↓
  [全サブタスク完了]
     ↓
create_answer
```

### Pregelの使用例

#### _create_subgraphメソッド

```python
def _create_subgraph(self) -> Pregel:
    """
    サブグラフ（サブワークフロー）を作成する（内部メソッド）
    
    個別のサブタスク実行用のワークフローを定義する。
    
    Returns:
        Pregel: コンパイル済みのサブグラフ
    """
    # サブグラフの状態管理用のワークフローを作成
    workflow = StateGraph(AgentSubGraphState)

    # === ノードの追加 ===
    workflow.add_node("select_tools", self.select_tools)
    workflow.add_node("execute_tools", self.execute_tools)
    workflow.add_node("create_subtask_answer", self.create_subtask_answer)
    workflow.add_node("reflect_subtask", self.reflect_subtask)

    # === エッジの追加 ===
    workflow.add_edge(START, "select_tools")
    workflow.add_edge("select_tools", "execute_tools")
    workflow.add_edge("execute_tools", "create_subtask_answer")
    workflow.add_edge("create_subtask_answer", "reflect_subtask")

    # 条件分岐エッジ
    workflow.add_conditional_edges(
        "reflect_subtask",
        self._should_continue_exec_subtask_flow,
        {
            "continue": "select_tools",
            "end": END
        },
    )

    # ワークフローをコンパイルして実行可能な形式（Pregel）に変換
    app: Pregel = workflow.compile()

    return app
```

**Pregelオブジェクトの使用：**

```python
def _execute_subgraph(self, state: AgentState):
    """サブグラフを実行する"""
    # サブグラフ（Pregel）を作成
    subgraph: Pregel = self._create_subgraph()

    # Pregelのinvokeメソッドでサブグラフを実行
    result = subgraph.invoke(
        {
            "question": state["question"],
            "plan": state["plan"],
            "subtask": state["plan"][state["current_step"]],
            "current_step": state["current_step"],
            "is_completed": False,
            "challenge_count": 0,
        }
    )

    # 実行結果を処理
    subtask_result = Subtask(
        task_name=result["subtask"],
        tool_results=result["tool_results"],
        reflection_results=result["reflection_results"],
        is_completed=result["is_completed"],
        subtask_answer=result["subtask_answer"],
        challenge_count=result["challenge_count"],
    )

    return {"subtask_results": [subtask_result]}
```

#### create_graphメソッド

```python
def create_graph(self) -> Pregel:
    """
    エージェントのメイングラフ（全体のワークフロー）を作成する
    
    Returns:
        Pregel: コンパイル済みのメイングラフ
    """
    # メイングラフの状態管理用のワークフローを作成
    workflow = StateGraph(AgentState)

    # === ノードの追加 ===
    workflow.add_node("create_plan", self.create_plan)
    workflow.add_node("execute_subtasks", self._execute_subgraph)
    workflow.add_node("create_answer", self.create_answer)

    # === エッジの追加 ===
    workflow.add_edge(START, "create_plan")

    # 条件分岐エッジ（計画の結果に基づいて並列実行を制御）
    workflow.add_conditional_edges(
        "create_plan",
        self._should_continue_exec_subtasks,  # Sendのリストを返す
    )

    workflow.add_edge("execute_subtasks", "create_answer")
    workflow.set_finish_point("create_answer")

    # ワークフローをコンパイルして実行可能な形式（Pregel）に変換
    app: Pregel = workflow.compile()

    return app
```

#### run_agentメソッド

```python
def run_agent(self, question: str) -> AgentResult:
    """
    エージェントを実行する（エントリーポイント）
    
    Args:
        question (str): ユーザーからの質問

    Returns:
        AgentResult: エージェントの実行結果
    """

    # メイングラフ（Pregel）を作成
    app: Pregel = self.create_graph()
    
    # Pregelのinvokeメソッドでグラフを実行
    result = app.invoke(
        {
            "question": question,
            "current_step": 0,
        }
    )
    
    # 実行結果をAgentResultオブジェクトにまとめて返す
    return AgentResult(
        question=question,
        plan=Plan(subtasks=result["plan"]),
        subtasks=result["subtask_results"],
        answer=result["last_answer"],
    )
```

---

## LangGraphの実行モデル

### グラフの構造

LangGraphのグラフは以下の要素で構成されます：

1. **ノード（Node）**：処理を行う関数
2. **エッジ（Edge）**：ノード間の遷移
3. **状態（State）**：ノード間で共有されるデータ
4. **条件分岐（Conditional Edge）**：状態に応じて次のノードを決定

### 実行フロー

```python
# agent.pyの実行フロー
START
  ↓
create_plan（計画作成）
  ↓
[条件分岐] _should_continue_exec_subtasks
  ↓ [Sendのリストを返す]
  ├─→ execute_subtasks (サブタスク1) ──┐
  ├─→ execute_subtasks (サブタスク2) ──┤ 並列実行
  └─→ execute_subtasks (サブタスク3) ──┘
  ↓ [全サブタスク完了]
create_answer（最終回答）
  ↓
END
```

### サブグラフの実行フロー

各`execute_subtasks`ノード内では、サブグラフ（Pregel）が実行されます：

```python
START
  ↓
select_tools（ツール選択）
  ↓
execute_tools（ツール実行）
  ↓
create_subtask_answer（回答作成）
  ↓
reflect_subtask（内省）
  ↓
[条件分岐] _should_continue_exec_subtask_flow
  ├─→ "continue" → select_tools（ループ）
  └─→ "end" → END
```

### 並列実行のメカニズム

```python
# 疑似コード：LangGraphの並列実行
def execute_conditional_edge(node, condition_func):
    result = condition_func(state)
    
    if isinstance(result, list) and all(isinstance(x, Send) for x in result):
        # Sendのリストが返された場合
        parallel_results = []
        
        # 各Sendを並列実行
        with ThreadPoolExecutor() as executor:
            futures = []
            for send in result:
                # 各ノードを並列実行
                future = executor.submit(
                    execute_node,
                    send.node,
                    send.state
                )
                futures.append(future)
            
            # すべての実行を待つ
            for future in futures:
                parallel_results.append(future.result())
        
        # 結果を集約（operator.addなどを使用）
        merged_state = merge_states(parallel_results)
        return merged_state
    else:
        # 通常の条件分岐
        next_node = result
        return execute_node(next_node, state)
```

---

## ベストプラクティス

### 1. Sendは独立したタスクに使う

**✅ 良い例：独立したサブタスク**

```python
def fan_out_subtasks(state):
    # 各サブタスクは独立しているため並列実行可能
    return [
        Send("search_database", {"query": "error codes"}),
        Send("search_documentation", {"query": "troubleshooting"}),
        Send("search_forum", {"query": "user questions"}),
    ]
```

**❌ 悪い例：依存関係があるタスク**

```python
def bad_fan_out(state):
    # タスク2がタスク1の結果に依存している場合は並列実行不可
    return [
        Send("fetch_data", state),        # データを取得
        Send("process_data", state),      # ❌ fetch_dataの結果が必要
    ]

# 正しくは逐次実行
workflow.add_edge("fetch_data", "process_data")
```

### 2. Pregelは型として使う

**✅ 良い例：戻り値の型として指定**

```python
def create_workflow() -> Pregel:
    """
    ワークフローを作成
    
    Returns:
        Pregel: コンパイル済みグラフ
    """
    workflow = StateGraph(State)
    # ... ノードとエッジを追加
    return workflow.compile()
```

**❌ 悪い例：型を指定しない**

```python
def create_workflow():  # 戻り値の型が不明
    workflow = StateGraph(State)
    return workflow.compile()
```

### 3. 状態の集約を適切に設定

**✅ 良い例：Annotatedで自動集約**

```python
class State(TypedDict):
    # 並列実行の結果を自動的に集約
    results: Annotated[Sequence[Result], operator.add]

def process_task(state):
    result = process(state["data"])
    return {"results": [result]}  # リストで返す

# 並列実行
def fan_out(state):
    return [
        Send("process_task", {"data": item})
        for item in state["items"]
    ]

# すべてのタスクの結果が自動的に集約される
# state["results"] = [result1, result2, result3, ...]
```

**❌ 悪い例：集約の設定なし**

```python
class State(TypedDict):
    results: list[Result]  # operator.addなし

# 並列実行すると、最後の結果だけが残る（上書き）
```

### 4. サブグラフは再利用可能に設計

**✅ 良い例：独立したサブグラフ**

```python
def create_subtask_subgraph() -> Pregel:
    """
    再利用可能なサブタスク用サブグラフ
    """
    workflow = StateGraph(SubtaskState)
    # ... ノードとエッジを追加
    return workflow.compile()

# メイングラフで使用
def execute_subtask(state):
    subgraph = create_subtask_subgraph()
    return subgraph.invoke(state)
```

### 5. エラーハンドリングを考慮

```python
def execute_with_retry(state):
    """リトライ機能付きの実行"""
    max_retries = 3
    for attempt in range(max_retries):
        try:
            # グラフを実行
            app = create_graph()
            result = app.invoke(state)
            return result
        except Exception as e:
            if attempt == max_retries - 1:
                # 最後の試行で失敗したら例外を再送出
                raise
            else:
                # リトライ
                print(f"Retry {attempt + 1}/{max_retries}")
                time.sleep(1)
```

### 6. グラフの可視化

```python
def visualize_graph():
    """グラフ構造を可視化"""
    app = create_graph()
    
    # グラフの構造を取得
    graph = app.get_graph()
    
    # ノード一覧
    print("Nodes:", graph.nodes)
    
    # エッジ一覧
    print("Edges:", graph.edges)
    
    # Mermaid形式で出力（図として可視化可能）
    print(graph.draw_mermaid())
```

---

## まとめ

### Send

- **並列処理を制御**するためのLangGraphの機能
- リストで返すことで、複数のノードを同時に実行
- 各Sendには実行するノード名と状態を指定
- agent.pyでは`_should_continue_exec_subtasks`で使用
- 独立したタスクを並列実行してパフォーマンスを向上

**基本構文：**
```python
Send(node_name, state)

# リストで返す
return [
    Send("task1", state1),
    Send("task2", state2),
    Send("task3", state3),
]
```

### Pregel

- **コンパイル済みのグラフ**を表す型
- `StateGraph.compile()`で生成される
- `invoke()`, `stream()`, `astream()`などで実行
- agent.pyでは`create_graph`と`_create_subgraph`で生成
- 実行可能なワークフローを表現

**基本構文：**
```python
workflow = StateGraph(State)
# ... ノードとエッジを追加
app: Pregel = workflow.compile()
result = app.invoke(initial_state)
```

### agent.pyでの活用

```python
# メイングラフ（Pregel）
def create_graph(self) -> Pregel:
    workflow = StateGraph(AgentState)
    # ...
    return workflow.compile()

# サブグラフ（Pregel）
def _create_subgraph(self) -> Pregel:
    workflow = StateGraph(AgentSubGraphState)
    # ...
    return workflow.compile()

# 並列実行（Send）
def _should_continue_exec_subtasks(self, state: AgentState) -> list:
    return [
        Send("execute_subtasks", {...})
        for idx, _ in enumerate(state["plan"])
    ]
```

これらの機能により、LangGraphは複雑なワークフローを効率的に実行できます。

