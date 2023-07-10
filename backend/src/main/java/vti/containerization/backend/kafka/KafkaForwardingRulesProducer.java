package vti.containerization.backend.kafka;

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


    private final KafkaProducer kafkaProducer;

    @SneakyThrows
    public void sendForwardingRules(ForwardingController.AddForwardingRuleRequest message) {
        LOGGER.info("Sending forwarding rules to Kafka" + message);

        ObjectMapper objectMapper = new ObjectMapper();
        String messageJson = objectMapper.writeValueAsString(message);
        kafkaProducer.sendMessage("add-forwarding-rules", messageJson);
    }

    @SneakyThrows
    public void sendClearForwardingRules(ForwardingController.ClearForwardingRulesRequest message) {
        LOGGER.info("Sending clear forwarding rules to Kafka" + message);

        ObjectMapper objectMapper = new ObjectMapper();
        String messageJson = objectMapper.writeValueAsString(message);
        kafkaProducer.sendMessage("clear-forwarding-rules", messageJson);
    }
}
