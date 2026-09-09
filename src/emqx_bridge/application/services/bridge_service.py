import json
import uuid

from emqx_bridge.application.ports.amqp_publisher import MessagePublisher
from emqx_bridge.core.domain import Topic, enrich_payload
from emqx_bridge.core.logger import get_logger

logger = get_logger(__name__)


class BridgeService:
    """
    Application service that orchestrates the logic between MQTT and RabbitMQ.
    """

    def __init__(self, publisher: MessagePublisher) -> None:
        self.publisher = publisher

    async def handle_mqtt_message(self, topic_str: str, payload: bytes) -> None:
        """
        Main use case:
        1. Parse topic
        2. Extract device_id
        3. Convert routing key
        4. Enrich payload
        5. Publish to RabbitMQ
        """
        # Decode payload for readable logging
        try:
            readable_payload = payload.decode("utf-8")
        except Exception:
            readable_payload = str(payload)

        # Attempt to extract trace_id for early logging
        trace_id = None
        try:
            parsed_data = json.loads(readable_payload)
            if isinstance(parsed_data, dict):
                trace_id = parsed_data.get("trace_id")
        except Exception:
            pass

        if not trace_id:
            trace_id = uuid.uuid4().hex

        try:
            # 1. Parse topic
            topic = Topic.parse(topic_str)

            # 2. Extract device_id (already done in parsing)
            device_id = topic.device_id

            # 3. Convert to AMQP routing key
            routing_key = topic.to_amqp_routing_key()

            # 4. Enrich payload
            enriched_payload = enrich_payload(payload, device_id, trace_id)

            # 5. Publish to RabbitMQ
            logger.debug(
                "Publishing message to RabbitMQ",
                routing_key=routing_key,
                device_id=device_id,
                trace_id=trace_id,
            )
            await self.publisher.publish(enriched_payload, routing_key, trace_id=trace_id)

            logger.info(
                "Message bridged successfully",
                # topic=topic_str,
                routing_key=routing_key,
                device_id=device_id,
                trace_id=trace_id,
            )

        except ValueError as e:
            # Malformed topic
            logger.error("Failed to parse topic", topic=topic_str, error=str(e))
        except Exception as e:
            logger.exception(
                "Unexpected error handling MQTT message", topic=topic_str, error=str(e)
            )
