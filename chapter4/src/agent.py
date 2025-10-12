# operator: リストの追加などの演算子を提供（Annotatedで使用）
import operator
# typing: 型ヒントのための型定義をインポート
from typing import Annotated, Literal, Sequence, TypedDict

# LangChainのツール定義をOpenAI形式に変換するユーティリティ
from langchain_core.utils.function_calling import convert_to_openai_tool
# LangGraphの並列処理のためのSend関数
from langgraph.constants import Send
# LangGraphのグラフ構築のための基本コンポーネント
from langgraph.graph import END, START, StateGraph
# LangGraphのコンパイル済みグラフの型
from langgraph.pregel import Pregel
# OpenAI APIクライアント
from openai import OpenAI
# OpenAIのチャット補完メッセージの型定義
from openai.types.chat import ChatCompletionMessageParam

# アプリケーション設定（APIキーなど）
from src.configs import Settings
# カスタムロガーのセットアップ
from src.custom_logger import setup_logger
# データモデル（計画、サブタスク、検索結果など）
from src.models import (
    AgentResult,
    Plan,
    ReflectionResult,
    SearchOutput,
    Subtask,
    ToolResult,
)
# プロンプトテンプレート
from src.prompts import HelpDeskAgentPrompts

# サブタスクの最大リトライ回数（3回まで再試行）
MAX_CHALLENGE_COUNT = 3

# このモジュール用のロガーを初期化
logger = setup_logger(__file__)


# メイングラフの状態を管理するクラス
# エージェント全体の状態（質問、計画、サブタスク結果など）を保持
class AgentState(TypedDict):
    # ユーザーからの質問
    question: str
    # 生成された実行計画（サブタスクのリスト）
    plan: list[str]
    # 現在実行中のサブタスクのステップ番号（0から始まる）
    current_step: int
    # サブタスクの実行結果を蓄積するリスト
    # Annotated[Sequence[Subtask], operator.add]により、
    # 各ノードからの結果が自動的にリストに追加される
    subtask_results: Annotated[Sequence[Subtask], operator.add]
    # 最終的な回答（全サブタスクの結果を統合したもの）
    last_answer: str


# サブグラフの状態を管理するクラス
# 個別のサブタスク実行時の状態（ツール選択、実行、内省のサイクル）を保持
class AgentSubGraphState(TypedDict):
    # ユーザーからの元の質問（コンテキストとして保持）
    question: str
    # 全体の実行計画（コンテキストとして保持）
    plan: list[str]
    # 現在実行中のサブタスク（例: "エラーコードERR-404を検索する"）
    subtask: str
    # サブタスクが完了したかどうかのフラグ
    # Trueになるとサブグラフのループを終了
    is_completed: bool
    # OpenAI APIとのやり取り履歴（会話のコンテキストを保持）
    # システムプロンプト、ユーザープロンプト、AIの応答などが含まれる
    messages: list[ChatCompletionMessageParam]
    # 現在のリトライ回数（最大MAX_CHALLENGE_COUNT回まで再試行）
    challenge_count: int
    # ツール実行結果のリスト（各リトライで取得した検索結果を蓄積）
    # Annotated[Sequence[...], operator.add]により自動的に追加される
    tool_results: Annotated[Sequence[Sequence[SearchOutput]], operator.add]
    # 内省（reflection）の結果のリスト（各リトライでの評価結果を蓄積）
    reflection_results: Annotated[Sequence[ReflectionResult], operator.add]
    # サブタスクに対する回答（検索結果をもとに生成）
    subtask_answer: str


class HelpDeskAgent:
    """
    ヘルプデスクエージェントのメインクラス
    
    ユーザーの質問に対して、以下の流れで回答を生成する：
    1. 計画作成（Plan）：質問を複数のサブタスクに分解
    2. サブタスク実行（Execute）：各サブタスクを並列実行
       - ツール選択（Select Tools）：適切な検索ツールを選択
       - ツール実行（Execute Tools）：実際に検索を実行
       - 回答作成（Create Answer）：検索結果から回答を生成
       - 内省（Reflect）：回答の品質を評価し、必要なら再試行
    3. 最終回答作成（Create Final Answer）：全サブタスクの結果を統合
    
    このクラスはLangGraphを使用してエージェントのワークフローを管理する。
    """
    
    def __init__(
        self,
        settings: Settings,
        tools: list = [],
        prompts: HelpDeskAgentPrompts = HelpDeskAgentPrompts(),
    ) -> None:
        """
        ヘルプデスクエージェントを初期化する
        
        Args:
            settings (Settings): API キーなどの設定
            tools (list): エージェントが使用できるツールのリスト
                         （例: search_xyz_manual, search_xyz_qa）
            prompts (HelpDeskAgentPrompts): プロンプトテンプレート集
        """
        # 設定を保存
        self.settings = settings
        # 利用可能なツールのリストを保存
        self.tools = tools
        # ツール名からツールオブジェクトへのマッピング（高速アクセス用）
        self.tool_map = {tool.name: tool for tool in tools}
        # プロンプトテンプレートを保存
        self.prompts = prompts
        # OpenAI APIクライアントを初期化
        self.client = OpenAI(api_key=self.settings.openai_api_key)

    def create_plan(self, state: AgentState) -> dict:
        """
        計画を作成する（メイングラフの最初のステップ）
        
        ユーザーの質問を分析し、複数のサブタスクに分解する。
        例：「ERR-404エラーの対処法を教えてください」
        → サブタスク1: "ERR-404エラーコードの意味を調査"
        → サブタスク2: "ERR-404の解決方法を検索"

        Args:
            state (AgentState): 入力の状態（questionを含む）

        Returns:
            dict: 更新された状態（planを含む）
        """

        logger.info("🚀 計画生成処理を開始します...")

        # システムプロンプトを取得
        # エージェントの役割と計画の作成方法を指示
        system_prompt = self.prompts.planner_system_prompt

        # ユーザープロンプトを生成
        # テンプレートにユーザーの質問を埋め込む
        user_prompt = self.prompts.planner_user_prompt.format(
            question=state["question"],
        )
        
        # OpenAI APIに送信するメッセージを構築
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]
        logger.debug(f"最終的なプロンプトメッセージ: {messages}")

        # OpenAI APIにリクエストを送信
        # Structured Outputsを使用してPlanクラスの形式で結果を取得
        # Planの型は以下
        # class Plan(BaseModel):
        #   subtasks: list[str] = Field(..., description="問題を解決するためのサブタスクリスト")
        try:
            logger.info("OpenAIにリクエストを送信中...")
            response = self.client.beta.chat.completions.parse(
                model=self.settings.openai_model,  # 使用するモデル（例: gpt-4o）
                messages=messages,  # プロンプト
                response_format=Plan,  # 出力形式をPlanクラスに指定
                temperature=0,  # 決定的な出力（常に同じ結果）
                seed=0,  # 再現性のためのシード値
            )
            logger.info("✅ OpenAIからのレスポンスを正常に受信しました")
        except Exception as e:
            logger.error(f"OpenAIリクエスト中にエラーが発生しました: {e}")
            raise

        # レスポンスからStructured Outputsを利用してPlanクラスのインスタンスを取得
        # plan.subtasksには生成されたサブタスクのリストが含まれる
        plan = response.choices[0].message.parsed

        logger.info("計画生成が完了しました！")

        # 生成した計画（サブタスクのリスト）を返し、状態を更新する
        return {"plan": plan.subtasks}

    def select_tools(self, state: AgentSubGraphState) -> dict:
        """
        ツールを選択する（サブグラフの最初のステップ）
        
        サブタスクを実行するために適切な検索ツールを選択する。
        例：「ERR-404エラーコードの意味を調査」
        → search_xyz_manual（エラーコードを検索）を選択
        
        内省（reflection）の結果、再試行が必要な場合は、
        過去の対話履歴を参照して別のツールや別のキーワードを選択する。

        Args:
            state (AgentSubGraphState): 入力の状態

        Returns:
            dict: 更新された状態（messagesを含む）
        """

        logger.info("🚀 ツール選択処理を開始します...")

        # LangChainのツール定義をOpenAI Function Calling形式に変換
        # これによりOpenAIのモデルがツールの使い方を理解できる
        logger.debug("ツールをOpenAI形式に変換中...")
        openai_tools = [convert_to_openai_tool(tool) for tool in self.tools]

        # 初回実行かリトライかでプロンプトを切り替える
        if state["challenge_count"] == 0:
            # === 初回実行の場合 ===
            logger.debug("ツール選択用のユーザープロンプトを作成中...")
            
            # サブタスクに適したツール選択を促すプロンプトを生成
            user_prompt = self.prompts.subtask_tool_selection_user_prompt.format(
                question=state["question"],  # 元の質問
                plan=state["plan"],  # 全体の計画
                subtask=state["subtask"],  # 現在のサブタスク
            )

            # 新しい対話を開始
            messages = [
                {"role": "system", "content": self.prompts.subtask_system_prompt},
                {"role": "user", "content": user_prompt},
            ]

        else:
            # === リトライの場合 ===
            logger.debug("リトライ用のユーザープロンプトを作成中...")

            # 過去の対話履歴を取得
            # 前回の試行でのツール選択、検索結果、内省結果などが含まれる
            messages: list = state["messages"]

            # NOTE: トークン数節約のため、過去の検索結果（長文）は除外
            # roleが"tool"のメッセージ（検索結果）と
            # "tool_calls"を含むメッセージ（ツール呼び出し）を除外
            messages = [message for message in messages if message["role"] != "tool" or "tool_calls" not in message]

            # リトライを促すプロンプトを追加
            # 「前回の結果が不十分だったので、別のツールやキーワードで再試行してください」
            user_retry_prompt = self.prompts.subtask_retry_answer_user_prompt
            user_message = {"role": "user", "content": user_retry_prompt}
            messages.append(user_message)

        # OpenAI APIにリクエストを送信
        # Function Callingを使用してツールを選択
        try:
            logger.info("OpenAIにリクエストを送信中...")
            response = self.client.chat.completions.create(
                model=self.settings.openai_model,
                messages=messages,
                tools=openai_tools,  # type: ignore  # 利用可能なツールのリスト
                temperature=0,  # 決定的な出力
                seed=0,  # 再現性のためのシード値
            )
            logger.info("✅ OpenAIからのレスポンスを正常に受信しました")
        except Exception as e:
            logger.error(f"OpenAIリクエスト中にエラーが発生しました: {e}")
            raise

        # ツール呼び出しが含まれているか確認
        if response.choices[0].message.tool_calls is None:
            raise ValueError("ツール呼び出しがNullです")

        # AIの応答（ツール呼び出し情報）をメッセージ履歴に追加
        # tool_callsには、呼び出すツール名と引数が含まれる
        ai_message = {
            "role": "assistant",
            "tool_calls": [tool_call.model_dump() for tool_call in response.choices[0].message.tool_calls],
        }

        logger.info("ツール選択が完了しました！")
        messages.append(ai_message)

        # 更新されたメッセージ履歴を返す
        return {"messages": messages}

    def execute_tools(self, state: AgentSubGraphState) -> dict:
        """
        ツールを実行する（サブグラフの2番目のステップ）
        
        前のステップで選択されたツールを実際に実行する。
        例：search_xyz_manual(keywords="ERR-404")を実行
        → Elasticsearchで検索してドキュメントを取得
        
        複数のツールが選択された場合は、順番に実行する。

        Args:
            state (AgentSubGraphState): 入力の状態（messagesを含む）

        Raises:
            ValueError: ツール呼び出し情報がない場合

        Returns:
            dict: 更新された状態（messagesとtool_resultsを含む）
        """

        logger.info("🚀 ツール実行処理を開始します...")
        messages = state["messages"]

        # 最後のメッセージ（AIの応答）からツール呼び出し情報を取得
        # tool_callsには、呼び出すツール名と引数が含まれる
        tool_calls = messages[-1]["tool_calls"]

        # ツール呼び出し情報が存在するか確認
        if tool_calls is None:
            logger.error("ツール呼び出しがNullです")
            logger.error(f"メッセージ: {messages}")
            raise ValueError("ツール呼び出しがNullです")

        # ツール実行結果を格納するリスト
        tool_results = []

        # 各ツール呼び出しを順番に実行
        for tool_call in tool_calls:
            # ツール名と引数を取得
            tool_name = tool_call["function"]["name"]  # 例: "search_xyz_manual"
            tool_args = tool_call["function"]["arguments"]  # 例: {"keywords": "ERR-404"}

            # ツールマップからツールオブジェクトを取得
            tool = self.tool_map[tool_name]
            
            # ツールを実行して検索結果を取得
            # 例: search_xyz_manual.invoke({"keywords": "ERR-404"})
            # → ElasticsearchまたはQdrantで検索
            tool_result: list[SearchOutput] = tool.invoke(tool_args)

            # 実行結果をToolResultオブジェクトにラップして保存
            tool_results.append(
                ToolResult(
                    tool_name=tool_name,
                    args=tool_args,
                    results=tool_result,  # SearchOutputのリスト
                )
            )

            # ツール実行結果をメッセージ履歴に追加
            # これによりAIが検索結果を参照して回答を生成できる
            messages.append(
                {
                    "role": "tool",  # ツールからの応答
                    "content": str(tool_result),  # 検索結果の文字列表現
                    "tool_call_id": tool_call["id"],  # どのツール呼び出しの結果か紐付け
                }
            )
        logger.info("ツール実行が完了しました！")
        
        # 更新されたメッセージ履歴とツール実行結果を返す
        return {"messages": messages, "tool_results": [tool_results]}

    def create_subtask_answer(self, state: AgentSubGraphState) -> dict:
        """
        サブタスク回答を作成する（サブグラフの3番目のステップ）
        
        ツール実行の結果（検索結果）を参照して、サブタスクに対する回答を生成する。
        例：search_xyz_manualの検索結果から
        → "ERR-404は、リクエストされたリソースが見つからないエラーです。"
        という回答を生成
        
        メッセージ履歴には、システムプロンプト、質問、ツール選択、
        検索結果などが含まれており、これらを全てコンテキストとして使用する。

        Args:
            state (AgentSubGraphState): 入力の状態（messagesを含む）

        Returns:
            dict: 更新された状態（messagesとsubtask_answerを含む）
        """

        logger.info("🚀 サブタスク回答作成処理を開始します...")
        messages = state["messages"]

        # OpenAI APIにリクエストを送信
        # messagesには以下が含まれる：
        # 1. システムプロンプト（役割の指示）
        # 2. ユーザープロンプト（サブタスク）
        # 3. AIの応答（ツール選択）
        # 4. ツール実行結果（検索結果）
        # これらを全てコンテキストとして回答を生成
        try:
            logger.info("OpenAIにリクエストを送信中...")
            response = self.client.chat.completions.create(
                model=self.settings.openai_model,
                messages=messages,  # 全ての対話履歴
                temperature=0,  # 決定的な出力
                seed=0,  # 再現性のためのシード値
            )
            logger.info("✅ OpenAIからのレスポンスを正常に受信しました")
        except Exception as e:
            logger.error(f"OpenAIリクエスト中にエラーが発生しました: {e}")
            raise

        # AIが生成した回答を取得
        subtask_answer = response.choices[0].message.content

        # AIの回答をメッセージ履歴に追加
        ai_message = {"role": "assistant", "content": subtask_answer}
        messages.append(ai_message)

        logger.info("サブタスク回答作成が完了しました！")

        # 更新されたメッセージ履歴とサブタスク回答を返す
        return {
            "messages": messages,
            "subtask_answer": subtask_answer,
        }

    def reflect_subtask(self, state: AgentSubGraphState) -> dict:
        """
        サブタスク回答を内省する（サブグラフの4番目のステップ）
        
        生成したサブタスク回答の品質を評価（自己評価）する。
        - 回答が十分か？（is_completed: True/False）
        - 何が足りないか？（reflection: 文字列）
        
        is_completed=Falseの場合：
        → サブグラフをループして、ツール選択から再実行
        → 内省結果を参考に、別のツールや別のキーワードで再試行
        
        is_completed=Trueの場合、またはMAX_CHALLENGE_COUNT到達時：
        → サブグラフを終了し、次のサブタスクへ進む

        Args:
            state (AgentSubGraphState): 入力の状態（messagesを含む）

        Raises:
            ValueError: 内省結果がNoneの場合

        Returns:
            dict: 更新された状態（reflection_results、is_completed、challenge_countを含む）
        """

        logger.info("🚀 内省処理を開始します...")
        messages = state["messages"]

        # 内省を促すプロンプトを取得
        # 「生成した回答は十分ですか？不足している場合は何が必要ですか？」
        user_prompt = self.prompts.subtask_reflection_user_prompt

        # 内省プロンプトをメッセージ履歴に追加
        messages.append({"role": "user", "content": user_prompt})

        # OpenAI APIにリクエストを送信
        # Structured Outputsを使用してReflectionResultクラスの形式で結果を取得
        try:
            logger.info("OpenAIにリクエストを送信中...")
            response = self.client.beta.chat.completions.parse(
                model=self.settings.openai_model,
                messages=messages,
                response_format=ReflectionResult,  # 内省結果の構造を指定
                temperature=0,
                seed=0,
            )
            logger.info("✅ OpenAIからのレスポンスを正常に受信しました")
        except Exception as e:
            logger.error(f"OpenAIリクエスト中にエラーが発生しました: {e}")
            raise

        # 内省結果を取得
        # reflection_result.is_completed: 回答が十分かどうか（True/False）
        # reflection_result.reflection: 不足している情報や改善点
        reflection_result = response.choices[0].message.parsed
        if reflection_result is None:
            raise ValueError("内省結果がNullです")

        # 内省結果をメッセージ履歴に追加
        messages.append(
            {
                "role": "assistant",
                "content": reflection_result.model_dump_json(),
            }
        )

        # 状態を更新
        update_state = {
            "messages": messages,
            "reflection_results": [reflection_result],  # 内省結果を蓄積
            "challenge_count": state["challenge_count"] + 1,  # リトライ回数を増やす
            "is_completed": reflection_result.is_completed,  # 完了フラグを更新
        }

        # 最大リトライ回数に達し、かつ回答が不完全な場合
        # → これ以上再試行せず、デフォルトの回答を設定
        if update_state["challenge_count"] >= MAX_CHALLENGE_COUNT and not reflection_result.is_completed:
            update_state["subtask_answer"] = f"{state['subtask']}の回答が見つかりませんでした。"

        logger.info("内省が完了しました！")
        return update_state

    def create_answer(self, state: AgentState) -> dict:
        """
        最終回答を作成する（メイングラフの最後のステップ）
        
        全てのサブタスクの実行結果を統合し、ユーザーへの最終的な回答を生成する。
        例：
        - サブタスク1の回答: "ERR-404は、リソースが見つからないエラーです。"
        - サブタスク2の回答: "対処法は、URLを確認するか、管理者に連絡してください。"
        → 最終回答: "ERR-404エラーは...対処法としては...があります。"

        Args:
            state (AgentState): 入力の状態（question、plan、subtask_resultsを含む）

        Returns:
            dict: 更新された状態（last_answerを含む）
        """

        logger.info("🚀 最終回答作成処理を開始します...")
        
        # システムプロンプトを取得
        # 最終回答の生成方法（複数の情報を統合し、わかりやすくまとめる）を指示
        system_prompt = self.prompts.create_last_answer_system_prompt

        # サブタスク結果からタスク内容と回答のみを抽出
        # (ツール実行結果や内省結果などの詳細は除外してトークン数を節約)
        subtask_results = [(result.task_name, result.subtask_answer) for result in state["subtask_results"]]
        
        # ユーザープロンプトを生成
        # 元の質問、計画、各サブタスクの結果を含める
        user_prompt = self.prompts.create_last_answer_user_prompt.format(
            question=state["question"],  # 元の質問
            plan=state["plan"],  # 実行計画
            subtask_results=str(subtask_results),  # 各サブタスクの結果
        )
        
        # OpenAI APIに送信するメッセージを構築
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        # OpenAI APIにリクエストを送信
        try:
            logger.info("OpenAIにリクエストを送信中...")
            response = self.client.chat.completions.create(
                model=self.settings.openai_model,
                messages=messages,
                temperature=0,  # 決定的な出力
                seed=0,  # 再現性のためのシード値
            )
            logger.info("✅ OpenAIからのレスポンスを正常に受信しました")
        except Exception as e:
            logger.error(f"OpenAIリクエスト中にエラーが発生しました: {e}")
            raise

        logger.info("最終回答作成が完了しました！")

        # 最終回答を返し、状態を更新する
        return {"last_answer": response.choices[0].message.content}

    def _execute_subgraph(self, state: AgentState):
        """
        サブグラフを実行する（内部メソッド）
        
        個別のサブタスクを実行するためのサブグラフ（サブワークフロー）を作成し、実行する。
        サブグラフでは以下の処理をループ実行：
        1. ツール選択
        2. ツール実行
        3. 回答作成
        4. 内省（完了判定）
        5. 完了していなければ1に戻る（最大MAX_CHALLENGE_COUNT回）
        
        このメソッドは、各サブタスクに対して並列実行される。
        
        Args:
            state (AgentState): 入力の状態（question、plan、current_stepを含む）
            
        Returns:
            dict: サブタスクの実行結果（subtask_resultsを含む）
        """
        # サブグラフ（サブワークフロー）を作成
        subgraph = self._create_subgraph()

        # サブグラフを実行
        # 初期状態を設定してサブタスクの実行を開始
        result = subgraph.invoke(
            {
                "question": state["question"],  # 元の質問（コンテキスト）
                "plan": state["plan"],  # 全体の計画（コンテキスト）
                "subtask": state["plan"][state["current_step"]],  # 現在のサブタスク
                "current_step": state["current_step"],  # ステップ番号
                "is_completed": False,  # 初期状態は未完了
                "challenge_count": 0,  # リトライ回数は0から開始
            }
        )

        # サブグラフの実行結果をSubtaskオブジェクトにまとめる
        subtask_result = Subtask(
            task_name=result["subtask"],  # サブタスクの内容
            tool_results=result["tool_results"],  # 全ての検索結果
            reflection_results=result["reflection_results"],  # 全ての内省結果
            is_completed=result["is_completed"],  # 最終的な完了状態
            subtask_answer=result["subtask_answer"],  # サブタスクに対する回答
            challenge_count=result["challenge_count"],  # 実行したリトライ回数
        )

        # サブタスクの結果を返す（リストとして返すことで状態に追加される）
        return {"subtask_results": [subtask_result]}

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

    def _should_continue_exec_subtask_flow(self, state: AgentSubGraphState) -> Literal["end", "continue"]:
        """
        サブグラフ内のループを制御する（内部メソッド）
        
        サブタスクの実行を続けるか終了するかを判定する。
        
        終了条件：
        1. is_completed=True（内省で回答が十分と判断された）
        2. challenge_count >= MAX_CHALLENGE_COUNT（最大リトライ回数に到達）
        
        継続条件：
        - 上記以外の場合（回答が不十分で、まだリトライ可能）
        
        Args:
            state (AgentSubGraphState): 現在の状態
            
        Returns:
            Literal["end", "continue"]: "end"で終了、"continue"でループ継続
        """
        # 完了フラグがTrueか、最大リトライ回数に到達した場合は終了
        if state["is_completed"] or state["challenge_count"] >= MAX_CHALLENGE_COUNT:
            return "end"
        else:
            # それ以外は継続（ツール選択に戻る）
            return "continue"

    def _create_subgraph(self) -> Pregel:
        """
        サブグラフ（サブワークフロー）を作成する（内部メソッド）
        
        個別のサブタスク実行用のワークフローを定義する。
        
        ワークフローの構造：
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
        [判定] is_completed? または challenge_count >= MAX?
          Yes → END（サブグラフ終了）
          No → select_toolsに戻る（別のツールや別のキーワードで再試行）
        
        このループにより、AIが自己評価して回答の品質を改善できる。

        Returns:
            Pregel: コンパイル済みのサブグラフ
        """
        # サブグラフの状態管理用のワークフローを作成
        workflow = StateGraph(AgentSubGraphState)

        # === ノードの追加 ===
        # 各ノードは、サブグラフ内の処理ステップを表す
        
        # 1. ツール選択ノード：適切な検索ツールを選択
        workflow.add_node("select_tools", self.select_tools)

        # 2. ツール実行ノード：選択されたツールを実行
        workflow.add_node("execute_tools", self.execute_tools)

        # 3. サブタスク回答作成ノード：検索結果から回答を生成
        workflow.add_node("create_subtask_answer", self.create_subtask_answer)

        # 4. サブタスク内省ノード：回答の品質を評価
        workflow.add_node("reflect_subtask", self.reflect_subtask)

        # === エッジの追加 ===
        # エッジはノード間の遷移を定義する
        
        # スタート地点を設定：最初にツール選択から開始
        workflow.add_edge(START, "select_tools")

        # 固定的なエッジ（必ず次のノードに進む）
        workflow.add_edge("select_tools", "execute_tools")
        workflow.add_edge("execute_tools", "create_subtask_answer")
        workflow.add_edge("create_subtask_answer", "reflect_subtask")

        # 条件分岐エッジ（内省の結果によって次の遷移先が変わる）
        # reflect_subtaskの後の処理を判定関数で決定
        workflow.add_conditional_edges(
            "reflect_subtask",  # 判定元のノード
            self._should_continue_exec_subtask_flow,  # 判定関数
            {
                "continue": "select_tools",  # 継続の場合はツール選択に戻る
                "end": END  # 終了の場合はサブグラフを終了
            },
        )

        # ワークフローをコンパイルして実行可能な形式に変換
        app = workflow.compile()

        return app

    def create_graph(self) -> Pregel:
        """
        エージェントのメイングラフ（全体のワークフロー）を作成する
        
        エージェント全体の処理フローを定義する。
        
        ワークフローの構造：
        START
          ↓
        create_plan（計画作成）
          ↓ （サブタスクごとに並列実行）
        execute_subtasks（サブタスク実行）× N個
          ↓ （全サブタスク完了後）
        create_answer（最終回答作成）
          ↓
        END
        
        例：
        質問「ERR-404エラーの対処法は？」
        → 計画作成：["エラーの意味を調査", "対処法を検索"]
        → サブタスク実行（並列）：
            - サブタスク1：エラーの意味を調査
            - サブタスク2：対処法を検索
        → 最終回答：2つの結果を統合して回答生成

        Returns:
            Pregel: コンパイル済みのメイングラフ
        """
        # メイングラフの状態管理用のワークフローを作成
        workflow = StateGraph(AgentState)

        # === ノードの追加 ===
        
        # 1. 計画作成ノード：質問をサブタスクに分解
        workflow.add_node("create_plan", self.create_plan)

        # 2. サブタスク実行ノード：各サブタスクを実行
        #    このノードは並列実行される（計画のサブタスク数だけ実行）
        workflow.add_node("execute_subtasks", self._execute_subgraph)

        # 3. 最終回答作成ノード：全サブタスクの結果を統合
        workflow.add_node("create_answer", self.create_answer)

        # === エッジの追加 ===
        
        # スタート地点を設定：最初に計画作成から開始
        workflow.add_edge(START, "create_plan")

        # 条件分岐エッジ（計画の結果に基づいて並列実行を制御）
        # 計画に含まれるサブタスクの数だけexecute_subtasksノードを並列実行
        # 例：サブタスクが3つなら、3つのexecute_subtasksが並列実行される
        workflow.add_conditional_edges(
            "create_plan",  # 判定元のノード
            self._should_continue_exec_subtasks,  # 並列実行の命令を生成
        )

        # 固定的なエッジ
        # 全てのサブタスク実行が完了したら最終回答作成へ進む
        workflow.add_edge("execute_subtasks", "create_answer")

        # 終了地点を設定：最終回答作成で終了
        workflow.set_finish_point("create_answer")

        # ワークフローをコンパイルして実行可能な形式に変換
        app = workflow.compile()

        return app

    def run_agent(self, question: str) -> AgentResult:
        """
        エージェントを実行する（エントリーポイント）
        
        ユーザーからの質問を受け取り、エージェントの全処理を実行して回答を返す。
        
        実行フロー：
        1. メイングラフを作成
        2. 初期状態（質問）を設定してグラフを実行
        3. グラフが以下を順番に実行：
           - 計画作成
           - サブタスク実行（並列）
           - 最終回答作成
        4. 結果をAgentResultオブジェクトにまとめて返す
        
        例：
        question = "ERR-404エラーの対処法は？"
        → AgentResult {
            question: "ERR-404エラーの対処法は？",
            plan: ["エラーの意味を調査", "対処法を検索"],
            subtasks: [サブタスク1の結果, サブタスク2の結果],
            answer: "ERR-404エラーは...対処法としては...があります。"
        }

        Args:
            question (str): ユーザーからの質問

        Returns:
            AgentResult: エージェントの実行結果（計画、サブタスク結果、最終回答を含む）
        """

        # メイングラフ（全体のワークフロー）を作成
        app = self.create_graph()
        
        # グラフを実行
        # 初期状態として質問とcurrent_stepを設定
        result = app.invoke(
            {
                "question": question,  # ユーザーの質問
                "current_step": 0,  # 初期ステップは0
            }
        )
        
        # 実行結果をAgentResultオブジェクトにまとめて返す
        return AgentResult(
            question=question,  # 元の質問
            plan=Plan(subtasks=result["plan"]),  # 生成された計画
            subtasks=result["subtask_results"],  # 各サブタスクの実行結果
            answer=result["last_answer"],  # 最終回答
        )
