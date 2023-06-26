package vti.containerization.backend.messages;

public class MessageModel {

    private final String message;

    public MessageModel(String message) {
        this.message = message;
    }

    public String getMessage() {
        return message;
    }
}
