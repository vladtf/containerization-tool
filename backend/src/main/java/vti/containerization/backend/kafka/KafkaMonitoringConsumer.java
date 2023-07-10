package vti.containerization.backend.kafka;

import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.springframework.kafka.annotation.KafkaListener;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Component;
import vti.containerization.backend.messages.MessageModel;

import java.util.ArrayList;
import java.util.List;
import java.util.logging.Logger;

@Component
public class KafkaMonitoringConsumer {
    private static final Logger LOGGER = Logger.getLogger(KafkaMonitoringConsumer.class.getName());
    private static final int MAX_BUFFER_SIZE = 1000;

    private final List<MessageModel> messageBuffer = new ArrayList<>();

    private MessageModel deserializeMessage(String json) {
        try {
            ObjectMapper mapper = new ObjectMapper();
            return mapper.readValue(json, MessageModel.class);
        } catch (JsonProcessingException e) {
            LOGGER.warning("Failed to deserialize message: " + e.getMessage());
            return null;
        }
    }

    @KafkaListener(topics = "monitor-docker-traffic", groupId = "my_group")
    public synchronized void listen(String message) {
        LOGGER.fine("Received message: " + message);

        // Deserialize the message
        MessageModel messageModel = deserializeMessage(message);

        if (messageModel == null) {
            LOGGER.warning("Failed to deserialize message");
            return;
        }
        messageBuffer.add(messageModel);

        // Remove the oldest message if buffer exceeds the maximum size
        if (messageBuffer.size() > MAX_BUFFER_SIZE) {
            messageBuffer.remove(0);
        }
    }

    @Scheduled(fixedRate = 3000)
    public void logBufferSize() {
        LOGGER.info("Message buffer size: " + messageBuffer.size());
    }

    public List<MessageModel> getMessages() {
        return messageBuffer;
    }

    public void clearMessages() {
        messageBuffer.clear();
    }
}
