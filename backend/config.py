import os

from pydantic_settings import BaseSettings, SettingsConfigDict


class Config(BaseSettings):
    mcp_server_url: str = 'http://localhost:8000'
    mcp_transport: str = 'sse'

    api_key: str = 'your-api-key'

    model_config = SettingsConfigDict(
        env_file=os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            '../infra/.env'
            ),
        extra='ignore'
    )


config = Config()
