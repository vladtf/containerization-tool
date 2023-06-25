package vti.containerization.backend.kafka;

import org.springframework.kafka.annotation.KafkaListener;
import org.springframework.stereotype.Component;

@Component
public class KafkaMonitoringConsumer {

    @KafkaListener(topics = "monitor-docker-traffic", groupId = "my_group")
    public void listen(String message) {
        System.out.println("Received Messasge in group my_group: " + message);
    }
}
