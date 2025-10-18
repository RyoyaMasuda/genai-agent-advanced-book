from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    # OpenAI用の設定
    openai_api_key: Optional[str] = None
    openai_api_base: Optional[str] = None
    openai_model: str = "gpt-4o-2024-08-06"
    
    # Azure OpenAI用の設定
    azure_openai_api_key: Optional[str] = None
    azure_openai_endpoint: Optional[str] = None
    azure_openai_deployment_name: Optional[str] = None
    azure_openai_embedding_deployment_name: Optional[str] = None
    azure_openai_api_version: str = "2024-12-01-preview"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
