package vti.containerization.backend.kafka.producers;


import com.fasterxml.jackson.databind.ObjectMapper;
import lombok.AllArgsConstructor;
import org.springframework.stereotype.Component;
import vti.containerization.backend.containers.ContainersController;

import java.util.logging.Logger;

@Component
@AllArgsConstructor
public class KafkaContainersDataProducer {

    private final Logger LOGGER = Logger.getLogger(KafkaContainersDataProducer.class.getName());

    private final KafkaProducerClient kafkaProducerClient;

    private final ObjectMapper objectMapper;

    public void sendCreateContainerRequest(ContainersController.CreateContainerRequest message) {

        try {
            String messageJson = objectMapper.writeValueAsString(message);
            LOGGER.info("Sending create container request: " + messageJson);

            kafkaProducerClient.sendMessage("create-container", messageJson);
        } catch (Exception e) {
            LOGGER.severe("Failed to serialize message: " + e.getMessage());
        }
    }

    public void sendDeleteContainerRequest(String containerId) {
        try {
            LOGGER.info("Sending delete container request: " + containerId);
            kafkaProducerClient.sendMessage("delete-container", containerId);
        } catch (Exception e) {
            LOGGER.severe("Failed to serialize message: " + e.getMessage());
        }
    }
}
