package vti.containerization.backend.kafka;


import com.fasterxml.jackson.databind.ObjectMapper;
import lombok.AllArgsConstructor;
import org.springframework.stereotype.Component;
import vti.containerization.backend.containers.ContainersController;

import java.util.logging.Logger;

@Component
@AllArgsConstructor
public class KafkaContainersDataProducer {

    private final Logger LOGGER = Logger.getLogger(KafkaContainersDataProducer.class.getName());

    private final KafkaProducer kafkaProducer;

    public void sendCreateContainerRequest(ContainersController.CreateContainerRequest message) {

        ObjectMapper objectMapper = new ObjectMapper();

        try {
            String messageJson = objectMapper.writeValueAsString(message);
            LOGGER.info("Sending create container request: " + messageJson);

            kafkaProducer.sendMessage("create-container", messageJson);
        } catch (Exception e) {
            LOGGER.severe("Failed to serialize message: " + e.getMessage());
        }
    }
}
