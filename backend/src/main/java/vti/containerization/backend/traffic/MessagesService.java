package vti.containerization.backend.traffic;


import lombok.AllArgsConstructor;
import org.springframework.stereotype.Service;
import vti.containerization.backend.containers.ContainerDataModel;
import vti.containerization.backend.containers.ContainersService;
import vti.containerization.backend.kafka.consumers.KafkaMonitoringConsumer;

import java.util.ArrayList;
import java.util.List;

@Service
@AllArgsConstructor
public class MessagesService {

    private final KafkaMonitoringConsumer kafkaMonitoringConsumer;

    private final ContainersService containersService;

    private MessagesController.TrafficMessagesResponse getMessagesRelatedToContainer(ContainerDataModel container, List<MessageModel> messages) {
        List<MessageModel> filteredMessages = messages.stream().filter(message -> message.getSource().equals(container.getIp())
                || message.getDestination().equals(container.getIp())).toList();

        return new MessagesController.TrafficMessagesResponse(container.getName(), filteredMessages);
    }

    public List<MessagesController.TrafficMessagesResponse> getAllMessages() {
        List<MessagesController.TrafficMessagesResponse> response = new ArrayList<>();

        List<MessageModel> messages = kafkaMonitoringConsumer.getMessages();
        response.add(new MessagesController.TrafficMessagesResponse("all", messages));

        List<ContainerDataModel> allContainers = containersService.getAllContainers();

        List<MessagesController.TrafficMessagesResponse> messagesGroupedByContainers = allContainers.stream()
                .map(container -> getMessagesRelatedToContainer(container, messages))
                .toList();

        response.addAll(messagesGroupedByContainers);

        return response;
    }

    public void clearMessages() {
        kafkaMonitoringConsumer.clearMessages();
    }
}
