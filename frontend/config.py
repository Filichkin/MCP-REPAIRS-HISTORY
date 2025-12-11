'''
Frontend configuration module.

Manages all frontend application settings including API connection,
UI parameters, and application behavior.
'''

import os
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class FrontendConfig(BaseSettings):
    '''Frontend application settings loaded from environment variables.'''

    model_config = SettingsConfigDict(
        env_file=os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            '../infra/.env'
        ),
        env_file_encoding='utf-8',
        case_sensitive=False,
        extra='ignore',
    )

    # API Configuration
    api_base_url: str = Field(
        default='http://localhost:8005',
        description='Base URL for backend API'
    )

    # UI Configuration
    ui_server_name: str = Field(
        default='0.0.0.0',
        description='Gradio server name'
    )
    ui_server_port: int = Field(
        default=7860,
        ge=1024,
        le=65535,
        description='Gradio server port'
    )
    ui_share: bool = Field(
        default=False,
        description='Enable Gradio public sharing'
    )

    # Chat Configuration
    chat_timeout: float = Field(
        default=120.0,
        ge=1.0,
        description='HTTP client timeout for agent queries in seconds'
    )
    chat_height: int = Field(
        default=600,
        ge=300,
        description='Chatbot component height in pixels'
    )
    max_message_lines: int = Field(
        default=5,
        ge=1,
        description='Maximum lines for message input'
    )


# Global settings instance
settings = FrontendConfig()
