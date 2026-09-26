from typing import Any, Protocol


class MessagePublisher(Protocol):
    """
    Port for publishing messages to a target broker (e.g., RabbitMQ).
    """

    async def publish(
        self, payload: dict[str, Any], routing_key: str, trace_id: str | None = None
    ) -> None:
        """
        Publish the enriched payload using the specified routing key.
        """
        ...
