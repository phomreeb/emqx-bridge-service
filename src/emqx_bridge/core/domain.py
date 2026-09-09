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

        The topic structure can contain any number of prefix segments. For example:
        - 4 segments (No prefix): org/proj/dev-001/telemetry
        - 5 segments (1 prefix): processed/org/proj/dev-001/telemetry
        - N segments (Multiple prefixes): a/b/c/org/proj/dev-001/telemetry

        At least 4 segments are required. The last 4 segments are always extracted.
        """
        parts = topic_str.split("/")
        if len(parts) < 4:
            raise ValueError(
                f"Invalid topic format. Expected at least 4 segments, got {len(parts)}: '{topic_str}'"
            )

        return cls(
            raw_topic=topic_str,
            org=parts[-4],
            project=parts[-3],
            device_id=parts[-2],
            action=parts[-1],
        )

    def to_amqp_routing_key(self) -> str:
        """
        Convert the core MQTT topic segments into an AMQP routing key.
        Prefixes are ignored. Format: [Org].[Project].[Device-ID].[Action]
        """
        return f"{self.org}.{self.project}.{self.device_id}.{self.action}"


def enrich_payload(raw_payload: bytes | str, device_id: str, trace_id: str | None = None) -> dict[str, Any]:
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
            if trace_id and "trace_id" not in data:
                data["trace_id"] = trace_id
            return data
        else:
            # If payload is valid JSON but not an object (e.g., list, string)
            res = {"raw": data, "device_id": device_id}
            if trace_id:
                res["trace_id"] = trace_id
            return res
    except json.JSONDecodeError:
        res = {"raw": payload_str, "device_id": device_id}
        if trace_id:
            res["trace_id"] = trace_id
        return res
