package vti.containerization.backend.kafka.consumers;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.springframework.kafka.annotation.KafkaListener;
import org.springframework.stereotype.Component;
import vti.containerization.backend.kafka.entities.KafkaFeedbackMessage;

import java.util.ArrayList;
import java.util.List;
import java.util.Optional;
import java.util.logging.Logger;

@Component
public class KafkaForwardingRulesFeedbackConsumer {
    private static final Logger LOGGER = Logger.getLogger(KafkaForwardingRulesFeedbackConsumer.class.getName());

    private final List<KafkaFeedbackMessage> feedbackMessages = new ArrayList<>();

    private Optional<KafkaFeedbackMessage> deserializeMessage(String json) {
        try {
            ObjectMapper mapper = new ObjectMapper();
            KafkaFeedbackMessage message = mapper.readValue(json, KafkaFeedbackMessage.class);

            return Optional.ofNullable(message);
        } catch (JsonProcessingException e) {
            LOGGER.warning("Failed to deserialize message: " + e.getMessage());
            return Optional.empty();
        }
    }

    @KafkaListener(topics = "forwarding-rules-feedback", groupId = "my_group")
    public void listen(String message) {
        LOGGER.info("Received containers errors: " + message);

        ObjectMapper mapper = new ObjectMapper();
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

        LOGGER.info("Returning forwarding rules feedback messages: " + errors);
        return errors;
    }
}
