from pydantic import AmqpDsn, Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables or a .env file.
    """

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=False, extra="ignore"
    )

    # General
    environment: str = Field(
        default="development", description="Environment (development, production)"
    )
    log_level: str = Field(default="INFO")

    # MQTT (EMQX) Configuration
    mqtt_host: str = Field(..., description="MQTT broker hostname")
    mqtt_port: int = Field(default=1883, description="MQTT broker port")
    mqtt_username: str | None = Field(default=None, description="MQTT username")
    mqtt_password: str | None = Field(default=None, description="MQTT password")
    mqtt_client_id: str | None = Field(
        default=None,
        description="MQTT Client ID. If not set, a random one is generated.",
    )
    mqtt_keepalive: int = Field(
        default=60, description="MQTT keepalive interval in seconds"
    )
    mqtt_topic: str = Field(default="org/+/#", description="MQTT topic to subscribe to")
    mqtt_qos: int = Field(default=1, description="MQTT Quality of Service (0, 1, 2)")
    mqtt_share_group: str | None = Field(
        default=None,
        description="MQTT5 Shared subscription group name (e.g., worker-group)",
    )

    # RabbitMQ Configuration
    rabbitmq_url: AmqpDsn = Field(
        ...,
        description="RabbitMQ connection string (e.g., amqp://guest:guest@localhost:5672/)",
    )
    rabbitmq_exchange: str = Field(
        default="amq.topic", description="Target exchange in RabbitMQ"
    )
    rabbitmq_exchange_type: str = Field(
        default="topic", description="RabbitMQ exchange type"
    )
    rabbitmq_publish_max_retries: int = Field(
        default=3,
        description="Maximum number of retries when publishing to RabbitMQ fails",
    )
    rabbitmq_publish_retry_delay: float = Field(
        default=2.0, description="Delay in seconds between publish retries"
    )


def get_settings() -> Settings:
    """
    Factory function to get application settings.
    """
    return Settings()
