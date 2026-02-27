import json
import asyncio
from aiokafka import AIOKafkaProducer, AIOKafkaConsumer
from app.core.config import settings

producer: AIOKafkaProducer | None = None
consumer: AIOKafkaConsumer | None = None
consumer_task: asyncio.Task | None = None


async def start_kafka():
    """
    Start Kafka producer + consumer with retry.
    Prevents FastAPI startup crash if Kafka is still booting.
    """
    global producer, consumer, consumer_task

    retries = 10

    for attempt in range(retries):
        try:
            producer = AIOKafkaProducer(
                bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS
            )

            consumer = AIOKafkaConsumer(
                "messages.created",
                bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
                group_id="messaging-service",
                auto_offset_reset="earliest",
                enable_auto_commit=True,
            )

            await producer.start()
            await consumer.start()

            consumer_task = asyncio.create_task(_consume_loop())

            print("Kafka connected")
            return

        except Exception as e:
            print(f"Kafka not ready ({attempt+1}/{retries}) -> {e}")
            await asyncio.sleep(3)

    print("Kafka failed to start after retries")


async def stop_kafka():
    global producer, consumer, consumer_task

    print("Stopping Kafka...")

    # stop background consumer loop first
    if consumer_task:
        consumer_task.cancel()
        try:
            await consumer_task
        except asyncio.CancelledError:
            pass

    # stop consumer cleanly
    if consumer:
        await consumer.stop()

    # stop producer
    if producer:
        await producer.stop()

    print("Kafka stopped cleanly")


async def publish(topic: str, message: dict):
    if not producer:
        print("Kafka producer not ready, skipping event")
        return

    await producer.send_and_wait(
        topic,
        json.dumps(message).encode()
    )


# consumer loop
async def _consume_loop():
    try:
        async for msg in consumer:
            event = json.loads(msg.value.decode())

            from app.services.websocket_manager import manager
            from app.services.search_service import index_message_from_event

            await manager.broadcast(event["conversation_id"], event)
            index_message_from_event(event)

    except asyncio.CancelledError:
        print("Kafka consumer loop cancelled")
