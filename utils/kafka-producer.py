from confluent_kafka import Producer

# Kafka broker configuration
bootstrap_servers = 'localhost:29092'
topic = 'my_topic'

# Create Kafka Producer instance
producer = Producer({'bootstrap.servers': bootstrap_servers})

# Produce a message
producer.produce(topic, key='my_key', value='Hello, Kafka!')

# Flush producer buffer
producer.flush()

# Close the producer
# producer.close()
