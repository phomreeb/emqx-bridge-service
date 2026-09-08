import asyncio
from collections.abc import Awaitable, Callable

import aiomqtt
from aiomqtt import MqttError

from emqx_bridge.core.config import get_settings
from emqx_bridge.core.logger import get_logger

logger = get_logger(__name__)

# Type for message handler callback: async func(topic: str, payload: bytes)
MessageHandler = Callable[[str, bytes], Awaitable[None]]


class MqttSubscriber:
    """
    MQTT client adapter to connect to EMQX and subscribe to topics.
    Includes automatic reconnection logic.
    """

    def __init__(self, handler: MessageHandler) -> None:
        self.settings = get_settings()
        self.handler = handler
        self._stop_event = asyncio.Event()
        self._client: aiomqtt.Client | None = None

    async def start(self) -> None:
        """
        Start the MQTT client with automatic reconnection.
        """
        reconnect_interval = 3
        while not self._stop_event.is_set():
            try:
                logger.info(
                    "Connecting to MQTT broker...",
                    host=self.settings.mqtt_host,
                    port=self.settings.mqtt_port,
                )

                # Setup client kwargs
                client_kwargs = {
                    "hostname": self.settings.mqtt_host,
                    "port": self.settings.mqtt_port,
                    "keepalive": self.settings.mqtt_keepalive,
                }

                if self.settings.mqtt_username:
                    client_kwargs["username"] = self.settings.mqtt_username
                if self.settings.mqtt_password:
                    client_kwargs["password"] = self.settings.mqtt_password
                if self.settings.mqtt_client_id:
                    client_kwargs["identifier"] = self.settings.mqtt_client_id

                async with aiomqtt.Client(**client_kwargs) as client:
                    self._client = client
                    logger.info(
                        "Connected to MQTT broker.",
                        client_id=self.settings.mqtt_client_id,
                    )

                    topic = self.settings.mqtt_topic
                    if self.settings.mqtt_share_group:
                        topic = f"$share/{self.settings.mqtt_share_group}/{topic}"

                    qos = self.settings.mqtt_qos
                    await client.subscribe(topic, qos=qos)
                    logger.info("Subscribed to MQTT topic", topic=topic, qos=qos)

                    async for message in client.messages:
                        if self._stop_event.is_set():
                            break

                        # Process message
                        asyncio.create_task(
                            self._safe_handle_message(
                                str(message.topic), message.payload
                            )
                        )

            except MqttError as e:
                logger.error(
                    f"MQTT connection error: {e}. Reconnecting in {reconnect_interval} seconds...",
                    error=str(e),
                )
                await asyncio.sleep(reconnect_interval)
            except Exception as e:
                logger.exception("Unexpected error in MQTT loop", error=str(e))
                await asyncio.sleep(reconnect_interval)

    async def _safe_handle_message(
        self, topic: str, payload: bytes | str | bytearray | float | None
    ) -> None:
        """
        Wrapper to handle message and catch unexpected exceptions from the handler.
        """
        if payload is None:
            raw_payload = b""
        elif isinstance(payload, (str, bytearray)):
            raw_payload = (
                bytes(payload)
                if isinstance(payload, bytearray)
                else payload.encode("utf-8")
            )
        elif isinstance(payload, (int, float)):
            raw_payload = str(payload).encode("utf-8")
        else:
            raw_payload = payload

        try:
            await self.handler(topic, raw_payload)
        except Exception as e:
            logger.exception("Error processing MQTT message", topic=topic, error=str(e))

    def stop(self) -> None:
        """
        Signal the MQTT client to stop.
        """
        self._stop_event.set()
