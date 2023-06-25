from confluent_kafka import Consumer, KafkaException

# Kafka broker configuration
bootstrap_servers = 'localhost:29092'
topic = 'my_topic'
group_id = 'my_group'

# Create Kafka Consumer instance
consumer = Consumer({
    'bootstrap.servers': bootstrap_servers,
    'group.id': group_id
})

# Subscribe to the topic
consumer.subscribe([topic])

# Start consuming messages
while True:
    try:
        msg = consumer.poll(1.0)  # Poll for new messages
        if msg is None:
            continue
        if msg.error():
            raise KafkaException(msg.error())
        print(f"Received message: {msg.value().decode('utf-8')}")
    except KeyboardInterrupt:
        break

# Close the consumer
consumer.close()
