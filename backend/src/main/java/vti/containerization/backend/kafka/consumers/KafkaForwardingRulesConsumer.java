package vti.containerization.backend.kafka.consumers;

import java.util.Arrays;
import java.util.List;
import java.util.logging.Logger;

import lombok.AllArgsConstructor;
import org.springframework.kafka.annotation.KafkaListener;
import org.springframework.stereotype.Component;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;

import vti.containerization.backend.forwarding.ContainerForwardingRulesModel;

@Component
@AllArgsConstructor
public class KafkaForwardingRulesConsumer {
    private static final Logger LOGGER = Logger.getLogger(KafkaForwardingRulesConsumer.class.getName());

    private List<ContainerForwardingRulesModel> containersNatTables;

    private final ObjectMapper objectMapper;

    private List<ContainerForwardingRulesModel> deserializeMessage(String json) {
        try {
            ContainerForwardingRulesModel[] containersNatTables = objectMapper.readValue(json, ContainerForwardingRulesModel[].class);
            return Arrays.asList(containersNatTables);
        } catch (JsonProcessingException e) {
            LOGGER.warning("Failed to deserialize message: " + e.getMessage());
            return null;
        }
    }

    @KafkaListener(topics = "forwarding-rules", groupId = "my_group")
    public void listen(String message) {
        LOGGER.info("Received forwarding rules from Kafka: " + message);

        this.containersNatTables = deserializeMessage(message);
    }

    public List<ContainerForwardingRulesModel> getForwardingChains() {
        return containersNatTables;
    }
}
