import json
import time
from dataclasses import dataclass, asdict
from enum import Enum

from confluent_kafka import Consumer, Producer
import logging

from confluent_kafka.admin import AdminClient
from confluent_kafka.cimpl import NewTopic

# Configure the logger
logging.basicConfig(level=logging.INFO, format='[%(levelname)s] - %(message)s')
logger = logging.getLogger(__name__)


class Level(Enum):
    INFO = "INFO"
    ERROR = "ERROR"
    WARNING = "WARNING"
    SUCCESS = "SUCCESS"


class DataClassEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Enum):
            return obj.value
        return super().default(obj)


@dataclass
class FeedbackMessage:
    message: str
    level: Level

    def to_dict(self):
        return asdict(self)

    def to_json(self):
        return json.dumps(self.to_dict(), cls=DataClassEncoder)


def create_kafka_producer(bootstrap_servers: str) -> Producer:
    producer = Producer({'bootstrap.servers': bootstrap_servers})
    return producer


def create_missing_topic(admin_client, topic):
    new_topic = NewTopic(topic, num_partitions=1, replication_factor=1)
    admin_client.create_topics([new_topic])
    while topic not in admin_client.list_topics().topics:
        time.sleep(0.1)
    logger.info("Topic '%s' created", topic)


def create_kafka_consumer(topic: str, group_id: str, bootstrap_servers: str):
    consumer = Consumer({
        'bootstrap.servers': bootstrap_servers,
        'group.id': group_id,
        'auto.offset.reset': 'earliest',
        'enable.auto.commit': False
    })

    admin_client = AdminClient({'bootstrap.servers': bootstrap_servers})
    topic_metadata = admin_client.list_topics(timeout=5)

    if topic not in topic_metadata.topics:
        create_missing_topic(admin_client, topic)

    consumer.subscribe([topic])
    logger.info("Subscribed to topic '%s'", topic)

    return consumer


def consume_kafka_message(consumer: Consumer):
    messages = consumer.consume(num_messages=1, timeout=1.0)
    if messages is None or len(messages) == 0:
        return

    if len(messages) > 1:
        logger.warning(
            "More than one message received. Consuming only the first one")

    message = messages[0]

    if message.error():
        logger.error("Consumer error: %s", message.error())
        return

    logger.debug("Consumed message: %s", message.value().decode('utf-8'))
    consumer.commit()

    return message.value().decode('utf-8')
