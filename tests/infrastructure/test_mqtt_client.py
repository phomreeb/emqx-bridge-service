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
    
    # Mock the context manager behavior of aiomqtt.Client
    mock_client_instance = AsyncMock()
    mock_aiomqtt_client_class.return_value.__aenter__.return_value = mock_client_instance

    # Dummy handler
    async def dummy_handler(topic: str, payload: bytes) -> None:
        pass

    subscriber = MqttSubscriber(handler=dummy_handler)
    
    # We want the subscriber loop to run exactly once and then stop.
    # To do this, we'll set the stop_event INSIDE the async context manager
    # by mocking the `__aenter__` to trigger the stop.
    async def side_effect_aenter(*args: Any, **kwargs: Any) -> AsyncMock:
        subscriber.stop()
        return mock_client_instance
        
    mock_aiomqtt_client_class.return_value.__aenter__.side_effect = side_effect_aenter

    # Run the start method (it will connect, set stop, and then exit the message loop)
    await subscriber.start()

    # 1. Verify Client kwargs (client_id, keepalive)
    mock_aiomqtt_client_class.assert_called_once_with(
        hostname="test_host",
        port=1883,
        keepalive=120,
        identifier="test_client_id"
    )

    # 2. Verify subscription args (Shared subscription format, QoS)
    mock_client_instance.subscribe.assert_called_once_with(
        "$share/test-group/swd/test/#", 
        qos=2
    )
