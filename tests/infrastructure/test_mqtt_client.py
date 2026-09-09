import pytest
from typing import Any
from unittest.mock import patch, AsyncMock, MagicMock
from emqx_bridge.infrastructure.mqtt.client import MqttSubscriber
from emqx_bridge.core.config import Settings


@pytest.fixture
def mock_settings() -> Settings:
    return Settings(
        mqtt_host="test_host",
        mqtt_port=1883,
        mqtt_username="test_user",
        mqtt_password="test_password",
        mqtt_client_id="test_client_id",
        mqtt_keepalive=120,
        mqtt_topic="swd/test/#",
        mqtt_qos=2,
        mqtt_share_group="test-group",
        rabbitmq_url="amqp://guest:guest@localhost:5672/"
    )


@pytest.mark.asyncio
@patch("emqx_bridge.infrastructure.mqtt.client.get_settings")
@patch("emqx_bridge.infrastructure.mqtt.client.aiomqtt.Client")
async def test_mqtt_subscriber_initialization(
    mock_aiomqtt_client_class: MagicMock,
    mock_get_settings: MagicMock,
    mock_settings: Settings
) -> None:
    """
    Test that MqttSubscriber configures the aiomqtt.Client correctly
    using the values from Settings.
    """
    mock_get_settings.return_value = mock_settings
    
    mock_client_instance = AsyncMock()
    
    # 1. Setup the async context manager correctly
    mock_client_instance.__aenter__.return_value = mock_client_instance
    mock_client_instance.__aexit__.return_value = None

    # 2. Setup messages as an empty async generator to prevent TypeError
    async def mock_messages() -> Any:
        if False:
            yield
    mock_client_instance.messages = mock_messages()

    mock_aiomqtt_client_class.return_value = mock_client_instance

    # Dummy handler
    async def dummy_handler(topic: str, payload: bytes) -> None:
        pass

    subscriber = MqttSubscriber(handler=dummy_handler)
    
    # 3. Stop the subscriber immediately after it subscribes
    # so the infinite while-loop breaks cleanly
    async def mock_subscribe(*args: Any, **kwargs: Any) -> None:
        subscriber.stop()
        
    mock_client_instance.subscribe.side_effect = mock_subscribe

    await subscriber.start()

    mock_aiomqtt_client_class.assert_called_once_with(
        hostname="test_host",
        port=1883,
        keepalive=120,
        username="test_user",
        password="test_password",
        identifier="test_client_id"
    )

    # 2. Verify subscription args (Shared subscription format, QoS)
    mock_client_instance.subscribe.assert_called_once_with(
        "$share/test-group/swd/test/#", 
        qos=2
    )
