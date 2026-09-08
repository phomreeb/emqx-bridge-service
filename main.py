import asyncio

from faststream import FastStream
from faststream.rabbit import RabbitBroker

from emqx_bridge.application.services.bridge_service import BridgeService
from emqx_bridge.core.config import get_settings
from emqx_bridge.core.logger import get_logger, setup_logging
from emqx_bridge.infrastructure.amqp.publisher import FastStreamRabbitPublisher
from emqx_bridge.infrastructure.mqtt.client import MqttSubscriber

# Initialize settings and logging
setup_logging()
settings = get_settings()
logger = get_logger(__name__)

# Initialize RabbitBroker
broker = RabbitBroker(str(settings.rabbitmq_url))

# Initialize FastStream app
app = FastStream(broker)

# Global reference for the MQTT subscriber task so we can cancel it cleanly
mqtt_task: asyncio.Task | None = None
mqtt_subscriber: MqttSubscriber | None = None


@app.on_startup
async def startup_event() -> None:
    """
    Hook to run when the FastStream application starts.
    We initialize our services and start the MQTT subscriber here.
    """
    global mqtt_task, mqtt_subscriber
    logger.info("Starting emqx-bridge-service...")

    # Wire up dependencies
    publisher = FastStreamRabbitPublisher(broker=broker)
    bridge_service = BridgeService(publisher=publisher)

    # Initialize MQTT subscriber
    mqtt_subscriber = MqttSubscriber(handler=bridge_service.handle_mqtt_message)

    # Start the MQTT subscriber loop in the background
    mqtt_task = asyncio.create_task(mqtt_subscriber.start())
    logger.info("MQTT subscriber background task started.")


@app.after_shutdown
async def shutdown_event() -> None:
    """
    Hook to run when the FastStream application is shutting down.
    We stop the MQTT subscriber gracefully.
    """
    logger.info("Shutting down emqx-bridge-service...")

    if mqtt_subscriber:
        mqtt_subscriber.stop()

    if mqtt_task:
        await mqtt_task
        logger.info("MQTT subscriber background task stopped.")


if __name__ == "__main__":
    # Normally started via `faststream run main:app`
    # but providing an entry point for testing/local execution.
    asyncio.run(app.run())
