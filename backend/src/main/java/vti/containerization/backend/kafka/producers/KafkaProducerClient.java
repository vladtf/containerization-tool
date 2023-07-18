package vti.containerization.backend.kafka.producers;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.kafka.core.KafkaTemplate;
import org.springframework.stereotype.Component;

import java.util.logging.Logger;

@Component
public class KafkaProducerClient {

    private final Logger LOGGER = Logger.getLogger(KafkaProducerClient.class.getName());

    private final KafkaTemplate<String, String> kafkaTemplate;

    @Autowired
    public KafkaProducerClient(KafkaTemplate<String, String> kafkaTemplate) {
        this.kafkaTemplate = kafkaTemplate;
    }

    public void sendMessage(String topic, String message) {
        kafkaTemplate.send(topic, message);
    }
}
