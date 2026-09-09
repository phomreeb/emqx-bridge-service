import asyncio
from typing import Any

from faststream.rabbit import ExchangeType, RabbitBroker, RabbitExchange

from emqx_bridge.application.ports.amqp_publisher import MessagePublisher
from emqx_bridge.core.config import get_settings
from emqx_bridge.core.logger import get_logger

logger = get_logger(__name__)


class FastStreamRabbitPublisher(MessagePublisher):
    """
    AMQP Publisher adapter using FastStream's RabbitBroker.
    """

    def __init__(self, broker: RabbitBroker) -> None:
        self.broker = broker
        self.settings = get_settings()

        # Pre-configure the target exchange with its specific type
        self.exchange = RabbitExchange(
            name=self.settings.rabbitmq_exchange,
            type=ExchangeType(self.settings.rabbitmq_exchange_type),
        )
        self._exchange_declared = False

    async def publish(
        self, payload: dict[str, Any], routing_key: str, trace_id: str | None = None
    ) -> None:
        """
        Publish message to RabbitMQ exchange with built-in retry logic.
        """
        if not self._exchange_declared:
            await self.broker.declare_exchange(self.exchange)
            self._exchange_declared = True

        max_retries = self.settings.rabbitmq_publish_max_retries
        delay = self.settings.rabbitmq_publish_retry_delay

        headers: dict[str, Any] | None = None
        if trace_id:
            headers = {"x-trace-id": trace_id}

        for attempt in range(max_retries + 1):
            try:
                await self.broker.publish(
                    payload,
                    routing_key=routing_key,
                    exchange=self.exchange,
                    headers=headers,
                )
                return  # Success

            except Exception as e:
                if attempt == max_retries:
                    logger.error(
                        "Failed to publish message after max retries",
                        routing_key=routing_key,
                        error=str(e),
                        max_retries=max_retries,
                        trace_id=trace_id,
                    )
                    raise  # Bubble up the exception after max retries

                logger.warning(
                    f"Publish failed, retrying in {delay} seconds...",
                    attempt=attempt + 1,
                    max_retries=max_retries,
                    routing_key=routing_key,
                    error=str(e),
                    trace_id=trace_id,
                )
                await asyncio.sleep(delay)
