package vti.containerization.backend.kafka.consumers;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.springframework.kafka.annotation.KafkaListener;
import org.springframework.stereotype.Component;
import vti.containerization.backend.containers.ContainerDataModel;

import java.util.*;
import java.util.logging.Logger;

@Component
public class KafkaContainersDataConsumer {
    private static final Logger LOGGER = Logger.getLogger(KafkaContainersDataConsumer.class.getName());

    private List<ContainerDataModel> containersData;
    private Timer bufferTimer;
    private Timer logToConsoleTimer;

    private List<ContainerDataModel> deserializeMessage(String json) {
        try {
            ObjectMapper mapper = new ObjectMapper();
            ContainerDataModel[] containerDataModels = mapper.readValue(json, ContainerDataModel[].class);

            return Arrays.asList(containerDataModels);
        } catch (JsonProcessingException e) {
            LOGGER.warning("Failed to deserialize message: " + e.getMessage());
            return Collections.emptyList();
        }
    }

    @KafkaListener(topics = "containers-data", groupId = "my_group")
    public void listen(String message) {
        LOGGER.info("Received containers data: " + message);
        this.containersData = deserializeMessage(message);
    }

    public List<ContainerDataModel> getContainersData() {
        return containersData;
    }
}
