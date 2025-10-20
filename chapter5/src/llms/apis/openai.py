import os

from dotenv import load_dotenv
from openai import AzureOpenAI, OpenAI
from pydantic import BaseModel

from src.llms.models.llm_response import LLMResponse


load_dotenv("/home/ryoyamasuda/Documents/genai-agent-advanced-book/chapter5/.env")

# https://openai.com/api/pricing/ を参照されたい
COST = {
    "o3-mini-2025-01-31": {
        "input": 1.10 / 1_000_000,
        "output": 4.40 / 1_000_000,
    },
    "gpt-4o-2024-11-20": {
        "input": 2.50 / 1_000_000,
        "output": 1.25 / 1_000_000,
    },
    "gpt-4o-mini-2024-07-18": {
        "input": 0.150 / 1_000_000,
        "output": 0.600 / 1_000_000,
    },
}


def _get_client():
    """OpenAIまたはAzure OpenAIクライアントを取得"""
    api_provider = os.getenv("API_PROVIDER", "openai").lower()
    
    if api_provider == "azure":
        # Azure OpenAI設定
        api_key = os.getenv("AZURE_OPENAI_API_KEY")
        endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2024-08-01-preview")
        
        if not api_key or not endpoint:
            raise ValueError("Azure OpenAI設定が不完全です。AZURE_OPENAI_API_KEYとAZURE_OPENAI_ENDPOINTを設定してください。")
        
        return AzureOpenAI(
            api_key=api_key,
            azure_endpoint=endpoint,
            api_version=api_version,
        )
    else:
        # OpenAI設定
        api_key = os.getenv("OPENAI_API_KEY")
        base_url = os.getenv("OPENAI_API_BASE", "https://api.openai.com/v1")
        
        if not api_key:
            raise ValueError("OpenAI API設定が不完全です。OPENAI_API_KEYを設定してください。")
        
        return OpenAI(
            api_key=api_key,
            base_url=base_url,
        )


def generate_response(
    messages: list,
    model: str | None = None,
    response_format: type[BaseModel] | None = None,
) -> LLMResponse:
    client = _get_client()
    
    # モデル名の決定
    api_provider = os.getenv("API_PROVIDER", "openai").lower()
    if api_provider == "azure":
        # Azure OpenAIの場合、デプロイメント名を使用
        if model is None:
            model = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")
            if not model:
                raise ValueError("Azure OpenAI設定が不完全です。AZURE_OPENAI_DEPLOYMENT_NAMEを設定してください。")
    else:
        # OpenAIの場合、環境変数またはデフォルト値を使用
        if model is None:
            model = os.getenv("OPENAI_MODEL", "gpt-4o-2024-08-06")
    
    # LLM呼び出し
    if response_format is None:
        # Chat Completion
        completion = client.chat.completions.create(
            model=model,
            messages=messages
        )
        content = completion.choices[0].message.content or ""
    else:
        # Structured Outputs
        completion = client.beta.chat.completions.parse(
            model=model,
            messages=messages,
            response_format=response_format,
        )
        content = completion.choices[0].message.content or ""
    
    # コスト計算（Azure OpenAIの場合はコスト計算をスキップ）
    usage = completion.usage
    if usage is not None and api_provider != "azure":
        # OpenAIの場合のみコスト計算
        if model in COST:
            input_cost = usage.prompt_tokens * COST[model]["input"]
            output_cost = usage.completion_tokens * COST[model]["output"]
            total_cost = input_cost + output_cost
        else:
            total_cost = 0.0
        input_tokens = usage.prompt_tokens
        output_tokens = usage.completion_tokens
    else:
        total_cost = 0.0
        input_tokens = usage.prompt_tokens if usage else 0
        output_tokens = usage.completion_tokens if usage else 0
    
    response = LLMResponse(
        messages=messages,
        content=content,
        model=completion.model,
        created_at=completion.created,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
    )
    response.cost = total_cost
    return response
