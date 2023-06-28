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

    private final List<String> messageBuffer = new ArrayList<>();
    private Timer bufferTimer;
    private Timer logToConsoleTimer;

    @KafkaListener(topics = "monitor-docker-traffic", groupId = "my_group")
    public void listen(String message) {
        LOGGER.fine("Received message: " + message);
        messageBuffer.add(message);

        if (bufferTimer == null) {
            bufferTimer = new Timer();
            bufferTimer.schedule(new TimerTask() {
                @Override
                public void run() {
                    // Process the messages in the buffer
                    LOGGER.info("Buffer flush task running");

                    // Clear the buffer
                    messageBuffer.clear();
                    bufferTimer.cancel();
                    bufferTimer = null;
                }
            }, 10000); // Schedule the task to run after 10 seconds
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