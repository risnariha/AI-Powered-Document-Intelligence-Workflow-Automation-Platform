from aiokafka import AIOKafkaProducer, AIOKafkaConsumer
import json
from typing import Optional, Any
from contextlib import asynccontextmanager

from app.config import settings
from app.core.logger import logger


class KafkaProducer:
    """Kafka producer for event streaming"""

    def __init__(self):
        self.producer: Optional[AIOKafkaProducer] = None
        self._started = False

    async def start(self):
        """Start Kafka producer"""
        try:
            self.producer = AIOKafkaProducer(
                bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
                value_serializer=lambda v: json.dumps(v).encode()
            )
            await self.producer.start()
            self._started = True
            logger.info("Kafka producer started")
        except Exception as e:
            logger.error(f"Failed to start Kafka producer: {e}")

    async def stop(self):
        """Stop Kafka producer"""
        if self.producer and self._started:
            await self.producer.stop()
            self._started = False
            logger.info("Kafka producer stopped")

    async def send(self, topic: str, value: Any, key: str = None):
        """Send message to Kafka topic"""
        if not self._started:
            logger.warning(f"Kafka producer not started, skipping message to {topic}")
            return
        try:
            await self.producer.send(topic, value=value, key=key)
            logger.debug(f"Message sent to {topic}: {str(value)[:100]}")
        except Exception as e:
            logger.error(f"Failed to send message to {topic}: {e}")


class KafkaConsumer:
    """Kafka consumer for event processing"""

    def __init__(self, topic: str, group_id: str):
        self.topic = topic
        self.group_id = group_id
        self.consumer: Optional[AIOKafkaConsumer] = None
        self._started = False

    async def start(self):
        """Start Kafka consumer"""
        try:
            self.consumer = AIOKafkaConsumer(
                self.topic,
                bootstrap_servers=settings.KAFKA_BOOTSTRAP_SERVERS,
                group_id=self.group_id,
                value_deserializer=lambda v: json.loads(v.decode()),
                auto_offset_reset="earliest"
            )
            await self.consumer.start()
            self._started = True
            logger.info(f"Kafka consumer started for topic: {self.topic}")
        except Exception as e:
            logger.error(f"Failed to start Kafka consumer: {e}")

    async def stop(self):
        """Stop Kafka consumer"""
        if self.consumer and self._started:
            await self.consumer.stop()
            self._started = False
            logger.info(f"Kafka consumer stopped for topic: {self.topic}")

    async def consume(self):
        """Consume messages from Kafka"""
        if not self._started:
            return
        async for msg in self.consumer:
            yield msg.value


kafka_producer = KafkaProducer()