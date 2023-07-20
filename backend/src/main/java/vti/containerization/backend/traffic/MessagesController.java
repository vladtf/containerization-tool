package vti.containerization.backend.traffic;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;
import vti.containerization.backend.containers.ContainerDataModel;

import java.util.List;

@RestController
@RequestMapping("/messages")
@AllArgsConstructor
public class MessagesController {

    private final MessagesService messagesService;

    @GetMapping("/all")
    public List<TrafficMessagesResponse> getAllMessages() {
        return messagesService.getAllMessages();
    }


    @GetMapping("/clear")
    public void clearMessages() {
        messagesService.clearMessages();
    }

    @Data
    @AllArgsConstructor
    @NoArgsConstructor
    public static class TrafficMessagesResponse {
        private String groupId;
        private List<MessageModel> messages;
        private ContainerDataModel container;
    }
}
