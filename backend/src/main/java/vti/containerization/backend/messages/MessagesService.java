package vti.containerization.backend.messages;


import lombok.AllArgsConstructor;
import org.springframework.stereotype.Service;
import vti.containerization.backend.kafka.KafkaMonitoringConsumer;

import java.util.List;

@Service
@AllArgsConstructor
public class MessagesService {

    private final KafkaMonitoringConsumer kafkaMonitoringConsumer;

    public List<MessageModel> getAllMessages() {
        return kafkaMonitoringConsumer.getMessages().stream()
                .map(MessageModel::new)
                .toList();
    }
}
