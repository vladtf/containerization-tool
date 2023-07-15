package vti.containerization.backend.kafka;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.springframework.kafka.annotation.KafkaListener;
import org.springframework.stereotype.Component;
import vti.containerization.backend.containers.ContainerDataModel;

import java.util.*;
import java.util.logging.Logger;

@Component
public class KafkaContainersErrorConsumer {
    private static final Logger LOGGER = Logger.getLogger(KafkaContainersErrorConsumer.class.getName());

    private final List<String> errors = new ArrayList<>();
    private Timer bufferTimer;
    private Timer logToConsoleTimer;


    @KafkaListener(topics = "containers-data-error", groupId = "my_group")
    public void listen(String message) {
        LOGGER.info("Received containers errors: " + message);
        this.errors.add(message);
    }

    public List<String> getErrors() {
        return errors;
    }
}
