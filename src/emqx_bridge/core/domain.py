import json
from dataclasses import dataclass
from typing import Any


@dataclass
class Topic:
    """
    Domain model representing an MQTT topic.
    """

    raw_topic: str
    org: str
    project: str
    device_id: str
    action: str

    @classmethod
    def parse(cls, topic_str: str) -> "Topic":
        """
        Parse an incoming MQTT topic string.
        Format expected: [Org]/[Project]/[Device-ID]/[Action]
        """
        parts = topic_str.split("/")
        if len(parts) != 4:
            raise ValueError(
                f"Invalid topic format. Expected 4 segments, got {len(parts)}: '{topic_str}'"
            )

        return cls(
            raw_topic=topic_str,
            org=parts[0],
            project=parts[1],
            device_id=parts[2],
            action=parts[3],
        )

    def to_amqp_routing_key(self) -> str:
        """
        Convert the MQTT topic into an AMQP routing key by replacing '/' with '.'.
        """
        return self.raw_topic.replace("/", ".")


def enrich_payload(raw_payload: bytes | str, device_id: str) -> dict[str, Any]:
    """
    Intercept the incoming message payload from MQTT.
    Attempt to parse as JSON.
    If valid: inject device_id.
    If invalid: wrap in {"raw": "<payload>", "device_id": "<device_id>"}.
    """
    if isinstance(raw_payload, bytes):
        payload_str = raw_payload.decode("utf-8")
    else:
        payload_str = raw_payload

    try:
        data = json.loads(payload_str)
        if isinstance(data, dict):
            data["device_id"] = device_id
            return data
        else:
            # If payload is valid JSON but not an object (e.g., list, string)
            return {"raw": data, "device_id": device_id}
    except json.JSONDecodeError:
        return {"raw": payload_str, "device_id": device_id}
