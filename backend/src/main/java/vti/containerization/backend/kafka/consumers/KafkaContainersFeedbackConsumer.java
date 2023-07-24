package vti.containerization.backend.kafka.consumers;

import java.util.ArrayList;
import java.util.List;
import java.util.Optional;
import java.util.logging.Logger;

import lombok.AllArgsConstructor;
import org.springframework.kafka.annotation.KafkaListener;
import org.springframework.stereotype.Component;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;

import vti.containerization.backend.kafka.entities.KafkaFeedbackMessage;

@Component
@AllArgsConstructor
public class KafkaContainersFeedbackConsumer {
    private static final Logger LOGGER = Logger.getLogger(KafkaContainersFeedbackConsumer.class.getName());

    private final List<KafkaFeedbackMessage> feedbackMessages = new ArrayList<>();

    private final ObjectMapper objectMapper;

    private Optional<KafkaFeedbackMessage> deserializeMessage(String json) {
        try {
            KafkaFeedbackMessage message = objectMapper.readValue(json, KafkaFeedbackMessage.class);
            return Optional.ofNullable(message);
        } catch (JsonProcessingException e) {
            LOGGER.warning("Failed to deserialize message: " + e.getMessage());
            return Optional.empty();
        }
    }

    @KafkaListener(topics = "containers-data-feedback", groupId = "my_group")
    public void listen(String message) {
        LOGGER.info("Received containers errors: " + message);

        Optional<KafkaFeedbackMessage> feedbackMessage = deserializeMessage(message);

        if (feedbackMessage.isPresent()) {
            KafkaFeedbackMessage kafkaFeedbackMessage = feedbackMessage.get();
            this.feedbackMessages.add(kafkaFeedbackMessage);
        }
    }

    public List<KafkaFeedbackMessage> getFeedbackMessages() {
        // get the errors and clear the buffer
        List<KafkaFeedbackMessage> errors = new ArrayList<>(this.feedbackMessages);
        this.feedbackMessages.clear();

        LOGGER.info("Returning containers feedback messages: " + errors);
        return errors;
    }
}
