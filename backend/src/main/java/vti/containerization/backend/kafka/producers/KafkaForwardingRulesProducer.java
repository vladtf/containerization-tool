package vti.containerization.backend.kafka.producers;

import com.fasterxml.jackson.databind.ObjectMapper;
import lombok.AllArgsConstructor;
import lombok.SneakyThrows;
import org.springframework.stereotype.Component;
import vti.containerization.backend.forwarding.ForwardingController;

import java.util.logging.Logger;

@Component
@AllArgsConstructor
public class KafkaForwardingRulesProducer {

    private final Logger LOGGER = Logger.getLogger(KafkaForwardingRulesProducer.class.getName());


    private final KafkaProducerClient kafkaProducerClient;

    private final ObjectMapper objectMapper;

    @SneakyThrows
    public void sendForwardingRules(ForwardingController.AddForwardingRuleRequest message) {
        LOGGER.info("Sending forwarding rules to Kafka" + message);

        String messageJson = objectMapper.writeValueAsString(message);
        kafkaProducerClient.sendMessage("add-forwarding-rules", messageJson);
    }

    @SneakyThrows
    public void sendClearForwardingRules(ForwardingController.ClearForwardingRulesRequest message) {
        LOGGER.info("Sending clear forwarding rules to Kafka" + message);

        String messageJson = objectMapper.writeValueAsString(message);
        kafkaProducerClient.sendMessage("clear-forwarding-rules", messageJson);
    }
}
