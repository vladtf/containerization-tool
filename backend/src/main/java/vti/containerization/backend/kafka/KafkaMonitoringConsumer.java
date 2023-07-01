package vti.containerization.backend.kafka;

import org.springframework.kafka.annotation.KafkaListener;
import org.springframework.stereotype.Component;

import java.util.ArrayList;
import java.util.List;
import java.util.Timer;
import java.util.TimerTask;
import java.util.logging.Logger;

@Component
public class KafkaMonitoringConsumer {
    private static final Logger LOGGER = Logger.getLogger(KafkaMonitoringConsumer.class.getName());
    private static final int MAX_BUFFER_SIZE = 20;

    private final List<String> messageBuffer = new ArrayList<>();
    private Timer logToConsoleTimer;

    @KafkaListener(topics = "monitor-docker-traffic", groupId = "my_group")
    public synchronized void listen(String message) {
        LOGGER.fine("Received message: " + message);
        messageBuffer.add(message);

        // Remove the oldest message if buffer exceeds the maximum size
        if (messageBuffer.size() > MAX_BUFFER_SIZE) {
            messageBuffer.remove(0);
        }

        if (logToConsoleTimer == null) {
            logToConsoleTimer = new Timer();
            logToConsoleTimer.schedule(new TimerTask() {
                @Override
                public void run() {
                    LOGGER.info("Buffer size: " + messageBuffer.size());
                }
            }, 1000, 1000);
        }
    }

    public List<String> getMessages() {
        return messageBuffer;
    }
}
