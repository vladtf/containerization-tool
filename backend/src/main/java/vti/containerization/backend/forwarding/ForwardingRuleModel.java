package vti.containerization.backend.forwarding;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@AllArgsConstructor
@NoArgsConstructor
public class ForwardingRuleModel {
    private String command;
    private String target;
    private String protocol;
    private String options;
    private String source;
    private String destination;
}
