package vti.containerization.backend.traffic;


import lombok.AllArgsConstructor;
import org.springframework.stereotype.Service;
import vti.containerization.backend.containers.ContainerDataModel;
import vti.containerization.backend.containers.ContainersService;
import vti.containerization.backend.kafka.consumers.KafkaMonitoringConsumer;

import java.text.MessageFormat;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;

@Service
@AllArgsConstructor
public class MessagesService {

    private final KafkaMonitoringConsumer kafkaMonitoringConsumer;

    private final ContainersService containersService;

    public void clearMessages() {
        kafkaMonitoringConsumer.clearMessages();
    }

    public List<MessagesController.TrafficMessagesResponse> getAllMessages() {
        List<MessagesController.TrafficMessagesResponse> response = new ArrayList<>();

        List<MessageModel> messages = kafkaMonitoringConsumer.getMessages();
        response.add(new MessagesController.TrafficMessagesResponse("all", messages, null));

        List<ContainerDataModel> allContainers = containersService.getAllContainers();

        List<MessagesController.TrafficMessagesResponse> messagesGroupedByContainers = allContainers.stream()
                .map(container -> getMessagesRelatedToContainer(container, messages))
                .toList();

        markKnownContainers(messagesGroupedByContainers, allContainers);

        response.addAll(messagesGroupedByContainers);

        return response;
    }

    private MessagesController.TrafficMessagesResponse getMessagesRelatedToContainer(ContainerDataModel container, List<MessageModel> messages) {
        List<MessageModel> filteredMessages = messages.stream()
                .filter(message -> message.getSource().equals(container.getIp()) || message.getDestination().equals(container.getIp()))
                .toList();

        return new MessagesController.TrafficMessagesResponse(container.getName(), filteredMessages, container);
    }

    private void markKnownContainers(
            List<MessagesController.TrafficMessagesResponse> groups,
            List<ContainerDataModel> allContainers) {

        Map<String, ContainerDataModel> knownIpToContainer = allContainers.stream()
                .collect(Collectors.toMap(ContainerDataModel::getIp, container -> container));

        for (MessagesController.TrafficMessagesResponse group : groups) {
            if (group.getGroupId().equals("all")) continue;

            for (MessageModel message : group.getMessages()) {
                if (knownIpToContainer.containsKey(message.getSource())) {
                    message.setSource(MessageFormat.format("{0} ({1})", message.getSource(), knownIpToContainer.get(message.getSource()).getName()));
                }

                if (knownIpToContainer.containsKey(message.getDestination())) {
                    message.setDestination(MessageFormat.format("{0} ({1})", message.getDestination(), knownIpToContainer.get(message.getDestination()).getName()));
                }
            }
        }
    }


}
