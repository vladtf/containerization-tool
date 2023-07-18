package vti.containerization.backend.kafka.entities;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@AllArgsConstructor
@NoArgsConstructor
public class KafkaFeedbackMessage {
    private String message;
    private Level level;

    public static enum Level {
        INFO("INFO"),
        SUCCESS("SUCCESS"),
        ERROR("ERROR"),
        WARNING("WARNING");

        private final String level;

        private Level(String level) {
            this.level = level;
        }

        public String getLevel() {
            return level;
        }
    }

}
