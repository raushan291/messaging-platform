import json
from aiokafka import AIOKafkaConsumer
from app.services.websocket_manager import manager
from app.core.config import settings
from app.services.search_service import index_message_from_event

async def consume_messages_created():
    consumer = AIOKafkaConsumer(
        "messages.created",
        bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
        group_id="ws-broadcaster"
    )

    await consumer.start()

    try:
        async for msg in consumer:
            data = json.loads(msg.value)

            await manager.broadcast(
                data["conversation_id"],
                data
            )
    finally:
        await consumer.stop()


async def consume_indexing():
    consumer = AIOKafkaConsumer(
        "messages.created",
        bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
        group_id="search-indexer"
    )

    await consumer.start()

    try:
        async for msg in consumer:
            data = json.loads(msg.value)
            index_message_from_event(data)
    finally:
        await consumer.stop()