package vti.containerization.backend.messages;


import org.springframework.stereotype.Service;
import vti.containerization.backend.kafka.KafkaMonitoringConsumer;

import java.util.List;

@Service
public class MessagesService {

    private final KafkaMonitoringConsumer kafkaMonitoringConsumer;

    public MessagesService(KafkaMonitoringConsumer kafkaMonitoringConsumer) {
        this.kafkaMonitoringConsumer = kafkaMonitoringConsumer;
    }

    public List<MessageModel> getAllMessages() {
        return kafkaMonitoringConsumer.getMessages().stream()
                .map(MessageModel::new)
                .toList();
    }
}
