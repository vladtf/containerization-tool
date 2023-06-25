package vti.containerization.backend;

import org.apache.kafka.clients.consumer.ConsumerRecord;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.kafka.annotation.KafkaListener;
import org.springframework.kafka.core.KafkaTemplate;
import org.springframework.kafka.test.context.EmbeddedKafka;
import org.springframework.test.context.junit.jupiter.SpringExtension;

import java.util.concurrent.BlockingQueue;
import java.util.concurrent.LinkedBlockingQueue;
import java.util.concurrent.TimeUnit;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNotNull;

@ExtendWith(SpringExtension.class)
@SpringBootTest
@EmbeddedKafka(partitions = 1, topics = "test-topic")
public class KafkaConsumerTest {

    @Autowired
    private KafkaTemplate<String, String> kafkaTemplate;

    private final BlockingQueue<ConsumerRecord<String, String>> records = new LinkedBlockingQueue<>();

    @Test
    public void testKafkaConsumer() throws InterruptedException {
        // Send a test message to the "test-topic" Kafka topic
        kafkaTemplate.send("test-topic", "Test message");

        // Wait for the consumer to receive the message
        ConsumerRecord<String, String> receivedRecord = records.poll(10, TimeUnit.SECONDS);

        // Assert that the received message is not null
        assertNotNull(receivedRecord);

        // Assert the content of the received message
        assertEquals("Test message", receivedRecord.value());
    }

    @KafkaListener(topics = "test-topic")
    public void listen(ConsumerRecord<String, String> record) {
        records.add(record);
    }
}