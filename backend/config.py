import os

from pydantic_settings import BaseSettings, SettingsConfigDict


class Config(BaseSettings):
    mcp_server_url: str = 'http://localhost:8004'
    mcp_transport: str = 'sse'
    mcp_server_port: int = 8004
    mcp_server_host: str = '127.0.0.1'

    # Cloude-RAG Configuration
    key_id: str
    key_secret: str
    auth_url: str
    retrieve_url_template: str
    knowledge_base_id: str
    knowledge_base_version_id: str = 'latest'
    retrieve_limit: int = 10
    evolution_project_id: str

    api_key: str = 'your-api-key'
    api_url: str = 'http://127.0.0.1:8000'

    model_config = SettingsConfigDict(
        env_file=os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            '../infra/.env'
            ),
        extra='ignore'
    )


settings = Config()
