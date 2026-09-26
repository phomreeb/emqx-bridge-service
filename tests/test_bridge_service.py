from typing import Any

import pytest

from emqx_bridge.application.ports.amqp_publisher import MessagePublisher
from emqx_bridge.application.services.bridge_service import BridgeService


class MockPublisher(MessagePublisher):
    """
    Mock implementation of the MessagePublisher port for testing.
    """

    def __init__(self) -> None:
        self.published_messages: list[tuple[dict[str, Any], str, str | None]] = []

    async def publish(
        self, payload: dict[str, Any], routing_key: str, trace_id: str | None = None
    ) -> None:
        self.published_messages.append((payload, routing_key, trace_id))


@pytest.mark.asyncio
async def test_handle_mqtt_message_success() -> None:
    """
    Test the complete successful flow of handling an MQTT message.
    """
    mock_publisher = MockPublisher()
    service = BridgeService(publisher=mock_publisher)

    topic = "org/proj/dev-123/status"
    payload = b'{"state": "online", "trace_id": "00065B0F5CC31A36318C00002CE40000"}'

    await service.handle_mqtt_message(topic, payload)

    assert len(mock_publisher.published_messages) == 1
    published_payload, routing_key, trace_id = mock_publisher.published_messages[0]

    assert routing_key == "org.proj.dev-123.status"
    assert trace_id == "00065B0F5CC31A36318C00002CE40000"
    assert published_payload["state"] == "online"
    assert published_payload["device_id"] == "dev-123"


@pytest.mark.asyncio
async def test_handle_mqtt_message_no_trace_id_generates_one() -> None:
    """
    Test handling an MQTT message without a trace_id.
    The service should generate a UUID trace_id automatically.
    """
    mock_publisher = MockPublisher()
    service = BridgeService(publisher=mock_publisher)

    topic = "org/proj/dev-123/telemetry"
    payload = b'{"temperature": 22.5}'

    await service.handle_mqtt_message(topic, payload)

    assert len(mock_publisher.published_messages) == 1
    published_payload, _routing_key, trace_id = mock_publisher.published_messages[0]

    assert trace_id is not None
    assert "trace_id" in published_payload
    assert published_payload["trace_id"] == trace_id


@pytest.mark.asyncio
async def test_handle_mqtt_message_invalid_topic() -> None:
    """
    Test handling an MQTT message with an invalid topic format.
    The message should not be published.
    """
    mock_publisher = MockPublisher()
    service = BridgeService(publisher=mock_publisher)

    topic = "invalid/topic"
    payload = b'{"state": "online"}'

    await service.handle_mqtt_message(topic, payload)

    # Should catch ValueError and NOT publish
    assert len(mock_publisher.published_messages) == 0
