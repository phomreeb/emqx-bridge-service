import pytest

from emqx_bridge.core.domain import Topic, enrich_payload


def test_topic_parse_valid_format() -> None:
    """
    Test parsing a valid MQTT topic.
    """
    topic_str = "drr/phangan/device_001/telemetry"
    topic = Topic.parse(topic_str)

    assert topic.raw_topic == topic_str
    assert topic.org == "drr"
    assert topic.project == "phangan"
    assert topic.device_id == "device_001"
    assert topic.action == "telemetry"


def test_topic_parse_invalid_format() -> None:
    """
    Test parsing an invalid MQTT topic (not 4 segments).
    """
    topic_str = "drr/phangan/device_001"  # Only 3 segments

    with pytest.raises(ValueError) as exc_info:
        Topic.parse(topic_str)

    assert "Invalid topic format" in str(exc_info.value)


def test_topic_to_amqp_routing_key() -> None:
    """
    Test converting an MQTT topic to an AMQP routing key.
    """
    topic_str = "drr/phangan/device_001/telemetry"
    topic = Topic.parse(topic_str)

    assert topic.to_amqp_routing_key() == "drr.phangan.device_001.telemetry"


def test_enrich_payload_valid_json() -> None:
    """
    Test enriching a valid JSON payload.
    """
    raw_payload = b'{"temperature": 25.5, "humidity": 60}'
    device_id = "device_001"

    enriched = enrich_payload(raw_payload, device_id)

    assert enriched["temperature"] == 25.5
    assert enriched["humidity"] == 60
    assert enriched["device_id"] == "device_001"


def test_enrich_payload_valid_json_string() -> None:
    """
    Test enriching a valid JSON payload provided as a string instead of bytes.
    """
    raw_payload = '{"status": "ok"}'
    device_id = "device_001"

    enriched = enrich_payload(raw_payload, device_id)

    assert enriched["status"] == "ok"
    assert enriched["device_id"] == "device_001"


def test_enrich_payload_invalid_json() -> None:
    """
    Test enriching an invalid JSON payload (e.g., raw text).
    """
    raw_payload = b"Hello, this is just a string"
    device_id = "device_001"

    enriched = enrich_payload(raw_payload, device_id)

    assert enriched["raw"] == "Hello, this is just a string"
    assert enriched["device_id"] == "device_001"


def test_enrich_payload_json_list() -> None:
    """
    Test enriching a valid JSON payload that is a list, not a dict.
    """
    raw_payload = b"[1, 2, 3]"
    device_id = "device_001"

    enriched = enrich_payload(raw_payload, device_id)

    assert enriched["raw"] == [1, 2, 3]
    assert enriched["device_id"] == "device_001"
