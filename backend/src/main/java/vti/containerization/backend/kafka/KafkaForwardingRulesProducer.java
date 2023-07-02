package vti.containerization.backend.kafka;

import lombok.AllArgsConstructor;
import org.springframework.stereotype.Component;

import java.util.logging.Logger;

@Component
@AllArgsConstructor
public class KafkaForwardingRulesProducer {

    private final Logger LOGGER = Logger.getLogger(KafkaForwardingRulesProducer.class.getName());


    private final KafkaProducer kafkaProducer;

    public void sendForwardingRules(String topic, String message) {
        LOGGER.info("Sending forwarding rules to Kafka");
        kafkaProducer.sendMessage(topic, message);
    }
}
