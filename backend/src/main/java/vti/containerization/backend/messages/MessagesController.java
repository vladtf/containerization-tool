package vti.containerization.backend.messages;

import lombok.AllArgsConstructor;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;

@RestController
@RequestMapping("/messages")
@AllArgsConstructor
public class MessagesController {

    private final MessagesService messagesService;

    @GetMapping("/all")
    public List<MessageModel> getAllMessages() {
        return messagesService.getAllMessages();
    }


    @GetMapping("/clear")
    public void clearMessages() {
        messagesService.clearMessages();
    }
}
